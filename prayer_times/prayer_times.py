#!/usr/bin/env python3
"""Prayer Times add-on: publishes prayer times to Home Assistant over MQTT discovery.

One HA device with eight sensors:
  Fajr, Sunrise, Dhuhr, Asr, Maghrib, Isha   (timestamps)
  Next Prayer (name), Next Prayer Time (timestamp)

The day rolls over right after Isha, not at midnight: from Isha (+ a short delay) until the
next Isha the sensors hold tomorrow's times, so Fajr is always the coming Fajr.
"""
import json
import os
import random
import signal
import sys
import threading
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import paho.mqtt.client as mqtt

import prayer_calc as pc

VERSION = "1.00"
OPTIONS_FILE = os.environ.get("PRAYER_OPTIONS", "/data/options.json")   # the env var is for testing
HEARTBEAT_S = 30 * 60          # republish at least this often, in case a message was lost
KEYS = {n: n.lower() for n in pc.PRAYER_NAMES}                        # "Fajr" -> "fajr"
ICONS = {"Fajr": "mdi:weather-sunset-up", "Sunrise": "mdi:white-balance-sunny",
         "Dhuhr": "mdi:weather-sunny", "Asr": "mdi:weather-sunny-alert",
         "Maghrib": "mdi:weather-sunset-down", "Isha": "mdi:weather-night"}


LOG_TZ = None      # set once the time zone option is read, so log times are local times


def log(msg):
    print("%s  %s" % (datetime.now(LOG_TZ).strftime("%Y-%m-%d %H:%M:%S"), msg), flush=True)


# ------------------------------------------------------------------ configuration
class Config:
    def __init__(self, opts):
        self.lat = float(opts["latitude"])
        self.lon = float(opts["longitude"])
        self.tz_name = str(opts["timezone"]).strip()
        try:
            self.tz = ZoneInfo(self.tz_name)
        except (ZoneInfoNotFoundError, ValueError):
            raise SystemExit("Unknown time zone '%s'. Use a name like Asia/Riyadh." % self.tz_name)
        self.method = opts.get("method", "um_alqura")
        self.device_name = (opts.get("device_name") or "Prayer Times").strip()
        self.prefix = (opts.get("topic_prefix") or "prayer_times").strip().strip("/")
        self.delay = int(opts.get("rollover_delay_seconds", 60))
        # MQTT: explicit options win, otherwise what the Supervisor gives us
        self.mqtt_host = opts.get("mqtt_host") or os.environ.get("MQTT_HOST", "core-mosquitto")
        self.mqtt_port = int(opts.get("mqtt_port") or os.environ.get("MQTT_PORT") or 1883)
        self.mqtt_user = opts.get("mqtt_user") or os.environ.get("MQTT_USER") or None
        self.mqtt_pass = opts.get("mqtt_password") or os.environ.get("MQTT_PASSWORD") or None
        self.slug = "".join(c if c.isalnum() else "_" for c in self.prefix.lower())


# ------------------------------------------------------------------ the calculation, as a pure function
def cycle_state(cfg, now):
    """Everything to publish for the moment `now` (an aware datetime). Pure: no I/O.

    Returns dict with: 'cycle_date', 'times' {name: datetime|None},
    'next_name', 'next_time', and 'wake' = the next moment anything changes."""
    today = now.astimezone(cfg.tz).date()
    t_today = pc.day_times(today, cfg.lat, cfg.lon, cfg.tz, cfg.method)
    isha = t_today["Isha"]
    rollover = None if isha is None else isha + timedelta(seconds=cfg.delay)

    cycle = today
    times = t_today
    if rollover is not None and now >= rollover:
        cycle = today + timedelta(days=1)
        times = pc.day_times(cycle, cfg.lat, cfg.lon, cfg.tz, cfg.method)

    # the next prayer is the first time still ahead (sunrise counts, as on the clock)
    upcoming = [(times[n], n) for n in pc.PRAYER_NAMES if times[n] is not None and times[n] > now]
    if upcoming:
        next_time, next_name = upcoming[0]
    else:
        # between Isha and the roll-over: tomorrow's Fajr
        nxt = pc.day_times(today + timedelta(days=1), cfg.lat, cfg.lon, cfg.tz, cfg.method)
        next_time, next_name = nxt["Fajr"], "Fajr"

    wake_points = [t for t, _ in upcoming]
    if rollover is not None and rollover > now:
        wake_points.append(rollover)
    wake_points.append(now + timedelta(seconds=HEARTBEAT_S))
    return {"cycle_date": cycle, "times": times, "next_name": next_name,
            "next_time": next_time, "wake": min(wake_points)}


def state_payload(cfg, st):
    iso = lambda d: d.isoformat(timespec="seconds") if d else None
    out = {KEYS[n]: iso(st["times"][n]) for n in pc.PRAYER_NAMES}
    out["next_prayer"] = st["next_name"]
    out["next_prayer_time"] = iso(st["next_time"])
    out["cycle_date"] = st["cycle_date"].isoformat()
    return out


# ------------------------------------------------------------------ MQTT / discovery
def discovery_messages(cfg):
    """[(topic, payload_dict)] for the eight sensors, all under ONE device."""
    device = {"identifiers": [cfg.slug], "name": cfg.device_name, "model": "Prayer Times add-on",
              "manufacturer": "NETMMS", "sw_version": VERSION}
    base = {"state_topic": "%s/state" % cfg.prefix,
            "availability_topic": "%s/status" % cfg.prefix,
            "payload_available": "Online", "payload_not_available": "Offline",
            "has_entity_name": True, "device": device}
    msgs = []

    def add(key, name, template, icon, **extra):
        uid = "%s_%s" % (cfg.slug, key)
        m = dict(base)
        m.update({"name": name, "unique_id": uid,
                  "default_entity_id": "sensor.%s" % uid,
                  "value_template": "{{ %s if %s is defined else None }}" % (template, template),
                  "icon": icon})
        m.update(extra)
        msgs.append(("homeassistant/sensor/%s/config" % uid, m))

    for n in pc.PRAYER_NAMES:
        add(KEYS[n], n, "value_json.%s" % KEYS[n], ICONS[n], device_class="timestamp")
    add("next_prayer", "Next Prayer", "value_json.next_prayer", "mdi:mosque")
    add("next_prayer_time", "Next Prayer Time", "value_json.next_prayer_time", "mdi:alarm",
        device_class="timestamp")
    return msgs


class Publisher:
    def __init__(self, cfg):
        self.cfg = cfg
        self.wake = threading.Event()
        self.connected = False
        self.need_discovery = True
        self.last_state = None
        try:                                    # paho 2.x
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                                      client_id="%s_addon" % cfg.slug)
        except AttributeError:                  # paho 1.x
            self.client = mqtt.Client(client_id="%s_addon" % cfg.slug)
        if cfg.mqtt_user:
            self.client.username_pw_set(cfg.mqtt_user, cfg.mqtt_pass)
        self.client.will_set("%s/status" % cfg.prefix, "Offline", qos=1, retain=True)
        self.client.reconnect_delay_set(min_delay=1, max_delay=60)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

    def start(self):
        log("MQTT broker %s:%s%s" % (self.cfg.mqtt_host, self.cfg.mqtt_port,
                                     " (user %s)" % self.cfg.mqtt_user if self.cfg.mqtt_user else ""))
        self.client.connect_async(self.cfg.mqtt_host, self.cfg.mqtt_port, keepalive=60)
        self.client.loop_start()

    def stop(self):
        try:
            if self.connected:
                self.client.publish("%s/status" % self.cfg.prefix, "Offline", qos=1, retain=True).wait_for_publish(2)
        except Exception:
            pass
        self.client.loop_stop()
        self.client.disconnect()

    # paho passes (client, userdata, flags, rc[, properties]) depending on version
    def _on_connect(self, client, userdata, flags, rc, *args):
        if rc != 0:
            log("MQTT connect refused: %s" % rc)
            return
        log("MQTT connected")
        self.connected = True
        self.need_discovery = True
        client.subscribe("homeassistant/status", qos=1)    # HA tells us when it (re)starts
        self.wake.set()

    def _on_disconnect(self, client, userdata, *args):
        if self.connected:
            log("MQTT disconnected, will retry")
        self.connected = False

    def _on_message(self, client, userdata, msg):
        if msg.topic == "homeassistant/status" and msg.payload.decode(errors="ignore") == "online":
            log("Home Assistant came online, republishing shortly")
            def again():
                self.need_discovery = True
                self.last_state = None
                self.wake.set()
            # a short random wait lets HA finish starting its MQTT; never sleep in this thread
            threading.Timer(random.uniform(1, 4), again).start()

    def publish(self, payload):
        """Publish discovery (when needed) and the state (when changed). Returns True if sent."""
        if not self.connected:
            return False
        c, cfg = self.client, self.cfg
        if self.need_discovery:
            for topic, m in discovery_messages(cfg):
                c.publish(topic, json.dumps(m), qos=1, retain=True)
            c.publish("%s/status" % cfg.prefix, "Online", qos=1, retain=True)
            self.need_discovery = False
            log("discovery published (%d sensors)" % len(discovery_messages(cfg)))
        text = json.dumps(payload, sort_keys=True)
        if text != self.last_state:
            c.publish("%s/state" % cfg.prefix, text, qos=1, retain=True)
            self.last_state = text
            return True
        return False


# ------------------------------------------------------------------ main loop
def fmt(d):
    return d.strftime("%H:%M:%S") if d else "--:--:--"


def main():
    with open(OPTIONS_FILE, encoding="utf-8") as f:
        cfg = Config(json.load(f))
    global LOG_TZ
    LOG_TZ = cfg.tz
    log("Prayer Times %s: lat %.4f lon %.4f, %s, %s, rollover %ds after Isha" % (
        VERSION, cfg.lat, cfg.lon, cfg.tz_name, cfg.method, cfg.delay))

    pub = Publisher(cfg)
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: (stop.set(), pub.wake.set()))
    pub.start()

    last_logged = None
    while not stop.is_set():
        now = datetime.now(cfg.tz)
        st = cycle_state(cfg, now)
        summary = (st["cycle_date"], st["next_name"])
        if summary != last_logged:
            log("cycle %s: %s | next: %s at %s" % (
                st["cycle_date"], "  ".join("%s %s" % (n, fmt(st["times"][n])) for n in pc.PRAYER_NAMES),
                st["next_name"], fmt(st["next_time"])))
            last_logged = summary
        if pub.publish(state_payload(cfg, st)):
            log("state published")
        # sleep until the next change (a prayer time, the roll-over after Isha, or the heartbeat);
        # a tiny margin so we wake just AFTER the moment, never just before it
        secs = max(0.5, (st["wake"] - datetime.now(cfg.tz)).total_seconds() + 0.5)
        pub.wake.wait(timeout=secs)
        pub.wake.clear()
        if not pub.connected:
            pub.last_state = None      # resend the state when the broker is back
    pub.stop()
    log("stopped")


if __name__ == "__main__":
    sys.exit(main())

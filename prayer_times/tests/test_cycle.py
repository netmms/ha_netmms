#!/usr/bin/env python3
"""Checks the Isha roll-over and next-prayer logic of prayer_times.py. Run: python3 -B tests/test_cycle.py"""
import os
import sys
import types
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
# paho is only needed to publish; a stub lets the logic be tested anywhere
try:
    import paho.mqtt.client  # noqa: F401
except ImportError:
    pkg = types.ModuleType("paho"); sub = types.ModuleType("paho.mqtt"); cl = types.ModuleType("paho.mqtt.client")
    cl.Client = object; sub.client = cl; pkg.mqtt = sub
    sys.modules.update({"paho": pkg, "paho.mqtt": sub, "paho.mqtt.client": cl})
import prayer_calc as pc  # noqa: E402
import prayer_times as app  # noqa: E402

RIYADH = ZoneInfo("Asia/Riyadh")
DELAY = 60
cfg = app.Config({"latitude": 26.2361, "longitude": 50.0393, "timezone": "Asia/Riyadh",
                  "rollover_delay_seconds": DELAY})
fails = 0
SEC = timedelta(seconds=1)


def at(s):
    return datetime.fromisoformat(s).replace(tzinfo=RIYADH)


def check(label, cond, detail=""):
    global fails
    print("%s  %s %s" % ("ok  " if cond else "FAIL", label, detail))
    fails += (not cond)


def hms(d):
    return d.strftime("%m-%d %H:%M:%S")


# the day under test, straight from the calculation (exact to the second, no rounding)
today = at("2026-11-14 00:00:00").date()
T = pc.day_times(today, cfg.lat, cfg.lon, cfg.tz, "um_alqura")
TM = pc.day_times(today + timedelta(days=1), cfg.lat, cfg.lon, cfg.tz, "um_alqura")
check("times carry seconds (not rounded to the minute)", any(t.second for t in T.values()),
      " ".join(hms(T[n])[6:] for n in pc.PRAYER_NAMES))
isha, fajr_tm = T["Isha"], TM["Fajr"]
roll = isha + DELAY * SEC

s = app.cycle_state(cfg, at("2026-11-14 10:00:00"))
check("daytime: cycle is today", s["cycle_date"].isoformat() == "2026-11-14")
check("daytime: next is Dhuhr at its exact time", (s["next_name"], s["next_time"]) == ("Dhuhr", T["Dhuhr"]))

s = app.cycle_state(cfg, isha - SEC)
check("1 s before Isha: next is Isha", (s["next_name"], s["next_time"]) == ("Isha", isha))

s = app.cycle_state(cfg, isha)
check("at Isha: sensors still today's (the Isha trigger must see today's Isha)",
      s["cycle_date"].isoformat() == "2026-11-14" and s["times"]["Isha"] == isha)
check("at Isha: next prayer already tomorrow's Fajr", (s["next_name"], s["next_time"]) == ("Fajr", fajr_tm))
check("at Isha: wakes at Isha + delay", s["wake"] == roll)

s = app.cycle_state(cfg, roll - SEC)
check("1 s before roll-over: still today's", s["cycle_date"].isoformat() == "2026-11-14")
s = app.cycle_state(cfg, roll)
check("at roll-over: sensors switch to tomorrow", s["cycle_date"].isoformat() == "2026-11-15")
check("at roll-over: Fajr sensor is TOMORROW's", s["times"]["Fajr"] == fajr_tm)
check("at roll-over: next is Fajr tomorrow", (s["next_name"], s["next_time"]) == ("Fajr", fajr_tm))

before = app.state_payload(cfg, app.cycle_state(cfg, at("2026-11-14 23:59:30")))
after = app.state_payload(cfg, app.cycle_state(cfg, at("2026-11-15 00:00:30")))
check("midnight changes nothing (no spurious republish)", before == after)

s = app.cycle_state(cfg, fajr_tm - SEC)
check("1 s before Fajr: next is Fajr", s["next_name"] == "Fajr")
s = app.cycle_state(cfg, fajr_tm)
check("at Fajr: next is Sunrise", s["next_name"] == "Sunrise" and s["cycle_date"].isoformat() == "2026-11-15")

a = app.state_payload(cfg, app.cycle_state(cfg, at("2026-11-14 21:00:00")))
b = app.state_payload(cfg, app.cycle_state(cfg, roll))
check("a restart after Isha gives the same answer as running through it", a == b)

p = app.state_payload(cfg, app.cycle_state(cfg, at("2026-11-14 12:00:00")))
check("payload timestamps carry +03:00", all(p[k].endswith("+03:00") for k in
      ("fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha", "next_prayer_time")), str(p))

msgs = app.discovery_messages(cfg)
check("8 discovery messages", len(msgs) == 8)
check("one shared device", len({m["device"]["identifiers"][0] for _, m in msgs}) == 1)
check("entity ids", [m["default_entity_id"] for _, m in msgs][:2] == ["sensor.prayer_times_fajr", "sensor.prayer_times_sunrise"])
check("six timestamps + next time", sum(m.get("device_class") == "timestamp" for _, m in msgs) == 7)

c2 = app.Config({"latitude": 51.5, "longitude": -0.12, "timezone": "Europe/London", "method": "egyptian"})
s2 = app.cycle_state(c2, datetime(2026, 7, 1, 12, tzinfo=ZoneInfo("Europe/London")))
check("London summer: offset +01:00 used", s2["times"]["Dhuhr"].utcoffset().total_seconds() == 3600)
print("\n%d failures" % fails)
sys.exit(1 if fails else 0)

# Prayer Times Add-on for Home Assistant

Publishes the five daily prayer times, and sunrise, to Home Assistant as sensors over MQTT, and tells you which prayer is next. The times are calculated **exactly like the NETMMS clock** (same formulas, same 32-bit arithmetic), so the clock and Home Assistant always agree, to the second.

---

# Features

- One Home Assistant device, **Prayer Times**, with eight sensors, created automatically through MQTT discovery.
- Works offline: no web service, everything is calculated locally.
- **Rolls over right after Isha**, not at midnight, so the Fajr sensor is always the coming Fajr.
- Timestamp sensors, so Home Assistant can trigger an automation at the exact prayer time, to the second.
- Recovers on its own after a broker or Home Assistant restart.

---

# Installation

1. Add the repository `https://github.com/netmms/ha_netmms` under **Add-on Store → Repositories**.
2. Install **Prayer Times**, set your coordinates and time zone, and start it.
3. Needs an MQTT broker (for example the **Mosquitto broker** add-on) with the MQTT integration set up. The broker is found automatically.

---

# Configuration

```yaml
latitude: 26.2361
longitude: 50.0393
timezone: "Asia/Riyadh"
method: "um_alqura"
device_name: "Prayer Times"
topic_prefix: "prayer_times"
rollover_delay_seconds: 60
```

| Option | Meaning |
| --- | --- |
| `latitude`, `longitude` | Your location in decimal degrees. |
| `timezone` | A time zone name such as `Asia/Riyadh` (not an offset). Daylight saving is followed if the zone has it. |
| `method` | `um_alqura`: Umm al-Qura (KSA), Fajr at 18.5°, Isha 90 minutes after Maghrib. `egyptian`: Fajr at 19.5°, Isha at 17.5°. Asr uses shadow factor 1. |
| `device_name` | Name of the device in Home Assistant. The entity ids come from it (`sensor.prayer_times_fajr` and so on). |
| `topic_prefix` | MQTT topic prefix. Change it only to run a second copy for another location. |
| `rollover_delay_seconds` | How long after Isha the sensors switch to tomorrow's times. See below. |
| `mqtt_host`, `mqtt_port`, `mqtt_user`, `mqtt_password` | Optional. Leave empty to use the broker Home Assistant provides. |

---

# Sensors

| Sensor | Value |
| --- | --- |
| `sensor.prayer_times_fajr` | Timestamp |
| `sensor.prayer_times_sunrise` | Timestamp |
| `sensor.prayer_times_dhuhr` | Timestamp |
| `sensor.prayer_times_asr` | Timestamp |
| `sensor.prayer_times_maghrib` | Timestamp |
| `sensor.prayer_times_isha` | Timestamp |
| `sensor.prayer_times_next_prayer` | Name: `Fajr`, `Sunrise`, `Dhuhr`, `Asr`, `Maghrib` or `Isha` |
| `sensor.prayer_times_next_prayer_time` | Timestamp |

The next prayer includes Sunrise, as on the clock.

## How the day rolls over

The sensors hold the times of the **current prayer day**, which runs from one Isha to the next:

- During the day they show today's times.
- `rollover_delay_seconds` after Isha (default 60), all six switch to **tomorrow's** times. Fajr is then tomorrow's Fajr, and nothing happens at midnight.
- The short delay lets an automation triggered by the Isha sensor fire before the sensor changes.
- The next-prayer sensors do not wait: from the moment of Isha they already show tomorrow's Fajr.

---

# Automation: act at each prayer time

`examples/adhan_automation.yaml` is a starting point. One time trigger per prayer, each with the prayer name as its `id`, and the name decides what the actions do: Fajr takes its own branch (its own sound), every other prayer takes the default branch. The actions in the example only post a notification so you can see the triggers work; replace them with whatever plays your sounds.

```yaml
triggers:
  - trigger: time
    at: sensor.prayer_times_fajr
    id: Fajr
  - trigger: time
    at: sensor.prayer_times_dhuhr
    id: Dhuhr
  # ... Asr, Maghrib and Isha the same way
actions:
  - choose:
      - conditions:
          - condition: trigger
            id: Fajr
        sequence: []        # the Fajr sound
    default: []             # the normal sound; {{ trigger.id }} is the prayer's name
```

- A time trigger on a timestamp sensor fires at that exact moment, to the second.
- Sunrise is not a trigger, so nothing plays at sunrise.

---

# How it matches the clock

`prayer_calc.py` is a port of the clock's `prayer.cpp`, including its 32-bit float rounding. `tests/compare_with_clock.py` builds the clock's own math into a native program and compares every day of 2026 and 2027 for eight places and both methods. Run it after changing the clock's calculation:

```
python3 tests/compare_with_clock.py /path/to/clock_esp_400/src/prayer.cpp
python3 -B tests/test_cycle.py
```

The clock's "from the web (aladhan.com)" method is not included.

---

# Troubleshooting

### The sensors do not appear

- Check that the MQTT integration is set up and the broker is running, then restart the add-on. The log shows `MQTT connected` and `discovery published (8 sensors)`.

### A time differs from another app by a minute

- Different authorities round differently. This add-on gives the exact moment calculated by the clock's formulas, to the second (for example 04:34:37), without rounding.

### Wrong times

- Check `latitude`, `longitude` (east is positive) and `timezone` in the add-on log line at start-up.

---

# License

MIT License unless otherwise stated.

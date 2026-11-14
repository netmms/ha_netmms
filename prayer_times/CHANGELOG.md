# Changelog

## 1.00

- First release: six prayer-time sensors (Fajr, Sunrise, Dhuhr, Asr, Maghrib, Isha), Next Prayer and Next Prayer Time, over MQTT discovery as one device.
- Calculation ported from the NETMMS clock firmware (Umm al-Qura and Egyptian), verified against the clock's own code.
- The day rolls over right after Isha, so Fajr is always the coming Fajr.

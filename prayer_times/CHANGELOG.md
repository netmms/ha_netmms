# Changelog

## 1.01

- Fix the build on current Home Assistant: the Dockerfile now has a default base image (the Supervisor no longer passes `BUILD_FROM`).

## 1.00

- First release: six prayer-time sensors (Fajr, Sunrise, Dhuhr, Asr, Maghrib, Isha), Next Prayer and Next Prayer Time, over MQTT discovery as one device.
- Calculation ported from the NETMMS clock firmware (Umm al-Qura and Egyptian), verified against the clock's own code.
- The day rolls over right after Isha, so Fajr is always the coming Fajr.

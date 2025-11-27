# NETMMS Home Assistant Add-ons

A curated collection of advanced, production-quality Home Assistant add-ons designed for local audio, distributed audio, and web-based PA (public address) systems.

This repository contains:

- **Local Audio Player** — play audio files locally or stream them into Snapserver.
- **Snapserver Pipe** — backbone of multi-room audio distribution using a named pipe.
- **Web Megaphone** — an HTTPS, airport-style PA system that records and plays announcements.

---

# Architecture Overview

```
┌───────────────────┐       ┌──────────────────────┐
│ Local Audio Player │──────▶│ Snapserver Pipe FIFO │──────▶ Snapclients
└───────────────────┘       └──────────────────────┘

┌───────────────────┐
│ Web Megaphone     │──────▶ (local speakers OR Snapserver Pipe)
└───────────────────┘
```

### Components

- **Local Audio Player**  
  Plays local audio files from `/config/www`, or streams decoded PCM into the Snapserver pipe.

- **Snapserver Pipe**  
  Provides a named FIFO that Snapserver reads to distribute audio across all connected Snapclients.

- **Web Megaphone**  
  A browser-based HTTPS PA system that plays an alert beep and then your recorded message.

---

# Installation

In Home Assistant:

1. Go to **Add-on Store → Repositories**.
2. Add the repository URL:

```
https://github.com/netmms/ha_netmms
```

3. Install add-ons from the `NETMMS Home Assistant Add-ons` section.

---

# Examples & Automations

## 1. Play a doorbell sound through Snapserver using Local Audio Player

```yaml
script:
  doorbell_chime:
    alias: Doorbell Chime
    sequence:
      - service: hassio.addon_stdin
        data:
          addon: local_audio
          input: "/config/www/doorbell.wav;85"
```

This works when `local_audio` is configured with:

```yaml
use_pipe: true
pipe: "/share/snapserver/stream"
```

---

## 2. Trigger an airport-style announcement using Web Megaphone

This script lets you overwrite the message file and then play it:

```yaml
script:
  pa_announcement:
    alias: PA Announcement
    sequence:
      - service: shell_command.set_pa_message
      - service: hassio.addon_stdin
        data:
          addon: web_megaphone
          input: "play"
```

Example `shell_command`:

```yaml
shell_command:
  set_pa_message: "cp /config/www/announcement.wav /msg.wav"
```

---

## 3. Scheduled announcement example

```yaml
automation:
  - alias: Evening Reminder
    trigger:
      - platform: time
        at: "21:00:00"
    action:
      - service: shell_command.set_pa_message
      - service: hassio.addon_stdin
        data:
          addon: web_megaphone
          input: "play"
```

---

# Troubleshooting

### Audio not playing in Snapserver mode

- Ensure the pipe exists: `ls -l /share/snapserver/stream`
- Ensure the add-on has in its `config.yaml`:

```
map:
  - share:rw
```

### Local Audio Player cannot find files

Files must exist under `/config/www` — upload using File Editor or Samba.

### Web Megaphone “Pipe missing” error

Snapserver Pipe must be running **before** using pipe mode.

---

# License

MIT License unless otherwise stated.


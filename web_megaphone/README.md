# Web Megaphone Add-on for Home Assistant

The **Web Megaphone** add-on provides an HTTPS-based, airport-style public address (PA) system for your Home Assistant installation.  
Record short announcements in your browser, then play them through either:

- The Home Assistant host speakers **(local ALSA)**  
- OR your entire home using **Snapserver Pipe** multiroom audio  

This add-on is part of the **NETMMS Home Assistant Add-ons** collection.

---

# Features

- Browser-based message recorder (no app needed): one big button, tap to talk, tap to send
- Live microphone level, timer (60 s limit), **Cancel**, **Repeat last**, and a status line
  that follows the message: *Sending → Playing in the house → Played ✓*
- **Loud, even voice:** every message is cleaned and leveled before it plays
  (low-cut, speech compressor, normalize, limiter), so it sounds about as loud as an Adhan file
- Messages from several phones play one after another, never on top of each other
- Secure **HTTPS server** on port **8001**
- Airport-style workflow:
  1. Record message  
  2. Chime plays  
  3. Message plays  
- Adjustable volumes:
  - `volume1` → Alert tone (chime)
  - `volume2` → Message
  - `voice_boost` → extra loudness for the voice
- Two output modes:
  - **Local playback** using `aplay`
  - **Multiroom playback** using `sox → Snapserver Pipe`
- The last message is kept in `/share/web_megaphone/last_msg.wav`
- Works on all Home Assistant CPU architectures

---

# Configuration

Add-on options:

```yaml
volume1: 30
volume2: 100
voice_boost: 6
use_pipe: false
pipe: "/share/snapserver/stream"
```

## Options explained

| Option | Description |
|--------|-------------|
| **volume1** | Volume (0–100 %) of the alert chime (`pa_sound.wav`). The chime file is very loud: 30 is plenty |
| **volume2** | Volume (0–100 %) of the recorded message. 100 = the full leveled voice |
| **voice_boost** | Extra loudness on the voice in dB (0–10, default 6). Each +2 is clearly louder; at 10 a limiter keeps it from distorting |
| **use_pipe** | `false` = Play locally via ALSA, `true` = Stream to Snapserver |
| **pipe** | FIFO path for Snapserver (used only if `use_pipe = true`) |

With Snapserver (`use_pipe: true`) the volumes are applied to the sound itself
(before 0.81 they did nothing in this mode). With local playback they set the ALSA
Master volume.

Home Assistant keeps the values you saved before, so after updating from 0.80
set them once in the add-on **Configuration** tab (for example 30 / 100).

## Required Folder Mappings

Your `config.yaml` must include:

```yaml
map:
  - share:rw
  - config:rw
  - certs:rw
```

- `/share` → needed for Snapserver Pipe  
- `/certs` → where HTTPS certificates (`wm.cert.pem` / `wm.key.pem`) reside  

---

# Web UI

Open:

```
https://<homeassistant>:8001/
```

You may need to accept a self-signed certificate warning.

The interface lets you:

- Record a new announcement  
- Preview  
- Submit  
- Trigger the PA playback  

---

# Playback Behavior

## How the voice is processed

`play_msg.sh` runs the recording through sox before it plays:

```
cut the last 0.15 s (the tap on Send) → low-cut 90 Hz → level → speech compressor
→ normalize to -1 dB → + voice_boost dB with a limiter → volume2
```

A normal phone recording comes out near −12 LUFS with the default `voice_boost: 6`.

## Local playback mode (`use_pipe: false`)

```
amixer sset Master volume1 → play pa_sound.wav
amixer sset Master volume2 → play the processed message
```

Plays through Home Assistant host speakers.

---

## Snapserver mode (`use_pipe: true`)

```
sox pa_sound.wav (× volume1) + processed message (× volume2) → /share/snapserver/stream
```

Chime and message go out as one stream. Your PA message is heard in **every room with a Snapclient**.

---

# Creating Certificates

Store certificates in `/ssl` (mapped as `/certs`).  
To generate a 10-year certificate:

```bash
cd /ssl
openssl req -x509 -nodes -newkey rsa:2048   -keyout wm.key.pem   -out wm.cert.pem   -days 3650   -subj "/CN=web-megaphone"
```

Copy them into your add-on or use `/certs` mapping.

---

# Troubleshooting

### “Pipe missing”
- Confirm Snapserver Pipe is installed & running
- FIFO must exist at `/share/snapserver/stream`

### “404 Not Found”
Ensure your front-end files exist in:

```
html/index.html
```

### Browser HTTPS warnings
Self-signed certificates always warn; this is normal on LAN.

---

# License

MIT License unless otherwise specified.

---

# Credits

- Snapcast by badaix  
- Home Assistant community  
- NETMMS contributors  

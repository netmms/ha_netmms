# Web Megaphone Add-on for Home Assistant

The **Web Megaphone** add-on provides an HTTPS-based, airport-style public address (PA) system for your Home Assistant installation.  
Record short announcements in your browser, then play them through either:

- The Home Assistant host speakers **(local ALSA)**  
- OR your entire home using **Snapserver Pipe** multiroom audio  

This add-on is part of the **NETMMS Home Assistant Add-ons** collection.

---

# Features

- Browser-based message recorder (no app needed)
- Secure **HTTPS server** on port **8001**
- Airport-style workflow:
  1. Record message  
  2. Chime plays  
  3. Message plays  
- Adjustable volumes:
  - `volume1` → Alert tone (chime)
  - `volume2` → Message
- Two output modes:
  - **Local playback** using `aplay`
  - **Multiroom playback** using `sox → Snapserver Pipe`
- Supports user-provided or bundled certificates (stored in `/certs`)
- Works on all Home Assistant CPU architectures

---

# Configuration

Add-on options:

```yaml
volume1: 40
volume2: 80
use_pipe: false
pipe: "/share/snapserver/stream"
```

## Options explained

| Option | Description |
|--------|-------------|
| **volume1** | Volume (0–100) for the alert chime (`pa_sound.wav`) |
| **volume2** | Volume (0–100) for recorded message (`msg.wav`) |
| **use_pipe** | `false` = Play locally via ALSA, `true` = Stream to Snapserver |
| **pipe** | FIFO path for Snapserver (used only if `use_pipe = true`) |

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

## Local playback mode (`use_pipe: false`)

```
amixer sset Master volume1 → play pa_sound.wav
amixer sset Master volume2 → play msg.wav
```

Plays through Home Assistant host speakers.

---

## Snapserver mode (`use_pipe: true`)

```
sox pa_sound.wav → /share/snapserver/stream
sox msg.wav → /share/snapserver/stream
```

Your PA message is heard in **every room with a Snapclient**.

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

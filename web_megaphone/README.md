# Web Megaphone Add-on for Home Assistant

The **Web Megaphone** add-on provides an HTTPS-based public-address (PA) system for Home Assistant — similar to a real **airport PA**:

1. You record a short message from your browser or web UI.
2. The add-on stores it as `msg.wav`.
3. It plays an alert chime (`pa_sound.wav`).
4. It plays your recorded message through either:
   - the Home Assistant host speakers (local ALSA), or
   - your whole-home Snapserver system (via pipe mode).

This add-on is part of the **NETMMS Home Assistant Add-ons** collection.

---

## Overview

The Web Megaphone add-on exposes **one HTTPS endpoint** on **port 8001**.
Any device on your network (phone, tablet, PC) can:

- Open the web interface
- Record a short message
- Trigger the PA announcement

The add-on then:

1. Plays an alert tone (`pa_sound.wav`)
2. Plays the recorded message (`msg.wav`)
3. At volumes you control (`volume1` and `volume2`)
4. Either locally or via Snapserver Pipe for distributed audio

---

## Features

- Airport-style PA workflow: record → chime → announce
- HTTPS-enabled server with your own certificate
- Browser-based UI (no client installation)
- Fully local – no cloud voice processing
- Optional Snapserver Pipe mode for whole-home broadcasting
- Adjustable chime and message volumes  
- Works on all Home Assistant CPU architectures

---

## Configuration

### Options

```yaml
volume1: 40
volume2: 80
use_pipe: false
pipe: "/share/snapserver/stream"
```

| Option | Purpose |
|--------|---------|
| `volume1` | Volume (0–100) for **alert tone** |
| `volume2` | Volume (0–100) for **recorded message** |
| `use_pipe` | `false` = play locally, `true` = stream to Snapserver Pipe |
| `pipe` | Named pipe (FIFO) path for Snapserver |

### Required mapping

```yaml
map:
  - share:rw
  - config:rw
  - certs:rw
```

`share` is required for Snapserver Pipe.  
`certs` is required for HTTPS certificates.

---

## Playback Logic

### Local playback (`use_pipe: false`)

```
amixer → set volume1
aplay pa_sound.wav
amixer → set volume2
aplay msg.wav
```

### Pipe playback (`use_pipe: true`)

```
sox pa_sound.wav → raw PCM → pipe
sox msg.wav → raw PCM → pipe
```

This streams audio into Snapserver for multiroom announcements.

---

## Ports

| Port | Purpose |
|------|---------|
| **8001/tcp** | HTTPS PA interface |

There is **no port 8000**.

---

## Using the Web UI

1. Open:  
   ```
   https://<homeassistant>:8001/
   ```
2. Record your message.
3. Submit it.
4. Hear the chime and announcement through your selected audio mode.

---

## Snapserver Integration

Enable this if you want your PA messages to play over all Snapclients.

1. Install **Snapserver Pipe** add-on.
2. Ensure FIFO exists:  
   ```
   /share/snapserver/stream
   ```
3. Configure Web Megaphone:

```yaml
use_pipe: true
pipe: "/share/snapserver/stream"
```

4. Play announcements through Snapcast automatically.

---

## Troubleshooting

### “Pipe missing”
- Ensure Snapserver Pipe is running  
- Make sure `/share/snapserver/stream` exists  
- Confirm `share:rw` is mapped

### “404 Not Found”
Check that your UI assets exist in:
```
html/index.html
```

### HTTPS warnings
Self-signed certificates are normal for internal LAN.

---

## License

MIT License unless specified otherwise.

---

## Credits

- Snapcast by badaix  
- Home Assistant community  
- NETMMS PA System contributors  
- Inspired by real-world airport PA announcements

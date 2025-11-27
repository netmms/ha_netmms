# Snapserver Pipe Add-on for Home Assistant

The **Snapserver Pipe** add-on provides a named FIFO pipe that Snapserver reads from, enabling synchronized multi-room audio distribution via Snapcast.

This add-on is part of the **NETMMS Home Assistant Add-ons** collection.

---

# Overview

Snapserver Pipe acts as the **audio input layer** for Snapserver by exposing a named pipe:

```
/share/snapserver/stream
```

Other add-ons such as:

- **Local Audio Player**
- **Web Megaphone**

can write raw PCM audio into this pipe, and Snapserver distributes it across all Snapclients.

---

# Features

- Creates and manages a FIFO named pipe for Snapserver
- Compatible with Snapclient on all platforms
- Supports:
  - `sox <file> -t raw -b 16 -e signed -r 48000 -c 2 <pipe>`
  - `ffmpeg -f s16le -ar 48000 -ac 2 -i <file> <pipe>`
- Low-latency, multi-room audio transport
- Works with Home Assistant automations and scripts

---

# Pipe Path

Default pipe location:

```
/share/snapserver/stream
```

Ensure your other add-ons map `/share`, e.g.:

```yaml
map:
  - share:rw
```

---

# Usage Examples

## Sending audio to the pipe

### Via SoX

```bash
sox song.mp3 -t raw -b 16 -e signed -r 48000 -c 2 /share/snapserver/stream
```

### Via FFmpeg

```bash
ffmpeg -i song.mp3 -f s16le -ar 48000 -ac 2   /share/snapserver/stream
```

### Home Assistant automation (Local Audio Add-on)

```yaml
service: hassio.addon_stdin
data:
  addon: local_audio
  input: "doorbell.wav;80"
```

---

# Integration

### Works with:

- **Local Audio Player**
- **Web Megaphone**
- **Any audio-producing add-on**

Snapserver Pipe is the core “audio input” that enables synchronous multi-room announcements and playback.

---

# Troubleshooting

### Pipe missing errors
Check that the pipe exists:

```
ls -l /share/snapserver/stream
```

If not present, restart the Snapserver Pipe add-on.

### No audio on Snapclients
Ensure Snapserver is configured to read from the pipe.

---

# License

MIT License.

---

# Credits

- Snapcast by badaix  
- Home Assistant community  
- NETMMS contributors  

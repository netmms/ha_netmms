# Snapserver Pipe Add-on for Home Assistant

The Snapserver Pipe Add-on enables low-latency, synchronized, multi-room audio streaming using Snapcast, with a focus on pipe-based audio input for advanced integrations.

This add-on is part of the NETMMS Home Assistant Add-ons repository.

---

## Overview

Snapserver Pipe is a Home Assistant add-on providing:

- A full Snapserver instance
- Support for pipe:/// input (FIFO named pipe)
- Auto-generated snapserver.conf
- Included Snapweb web interface
- Adjustable sample rate, bit depth, latency and buffer
- Works with MPD, SoX, FFmpeg, AirPlay, and external audio producers
- Suitable for whole-home synchronized audio setups

---

## Features

### Pipe-based audio input
Use a named pipe (FIFO) such as:
```
pipe:///share/snapserver/stream?name=Main&mode=read
```
allowing any program (FFmpeg, SoX, shairport-sync, TTS, etc.) to write raw PCM data into Snapserver.

### Customizable audio format
Configure:
- Sample rate (e.g., 48000, 44100, 16000)
- Bit depth (8/16/24)
- Channels (mono or stereo)
- Buffering and latency

### Snapweb Interface
Used to:
- View clients
- Rename clients
- Adjust volume
- Create groups

Accessible via port 1780.

### Host networking
Ensures low-latency, seamless autodiscovery by Snapclients.

---

## Default FIFO Path

This add-on automatically creates the FIFO at:

```
/share/snapserver/stream
```

Example SoX stream:

```bash
sox input.mp3 -t raw -b 16 -e signed -r 48000 -c 2 /share/snapserver/stream
```

Example FFmpeg stream:

```bash
ffmpeg -i input.mp3 -f s16le -ac 2 -ar 48000 /share/snapserver/stream
```

---

## Configuration

The add-on exposes these options in Home Assistant:

```yaml
stream: "pipe:///share/snapserver/stream?name=Main&mode=read"
sampleformat: "48000:16:2"
buffer_ms: 2000
latency_ms: 0
http_enabled: true
http_bind: "0.0.0.0"
http_port: 1780
rpc_bind: "0.0.0.0"
rpc_port: 1705
stream_port: 1704
extra_args: ""
```

Each option is documented in DOCS.md.

---

## Ports

If using host networking (default), Snapserver uses:

| Port      | Purpose            |
|-----------|--------------------|
| 1704/tcp  | Audio stream       |
| 1705/tcp  | Control (JSON-RPC) |
| 1780/tcp  | Web UI (Snapweb)   |

---

## Testing

After starting the add-on, access:

```
http://homeassistant.local:1780/
```

You should see the Snapweb UI and any connected Snapclients.

---

## Troubleshooting

### Client not appearing?
Run the client with host specified:

```bash
snapclient --host <home_assistant_ip>
```

### Snapweb message: “doc_root = /usr/share/snapserver/snapweb/”
This means Snapweb assets are missing; this add-on includes them automatically.

### Named pipe errors?
Ensure:
```bash
ls -l /share/snapserver/stream
```
It should show "p" for FIFO.

---

## License
MIT License unless otherwise stated.

---

## Credits
- Snapcast by badaix
- Home Assistant community
- NETMMS Add-on contributors

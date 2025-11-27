# Local Audio Player Add-on for Home Assistant

The **Local Audio Player** add-on plays audio files locally on the Home Assistant host, or streams raw PCM into Snapserver for synchronized multi-room playback.

---

# Features

- Plays audio directly via ALSA (`aplay`)
- Streams PCM to Snapserver Pipe using `sox`
- Adjustable volume per playback
- Supports sending only a filename (resolved automatically)
- Fully compatible with Home Assistant automations and scripts

---

# Configuration

```yaml
folder: "/config/www"
volume: 60
use_pipe: false
pipe: "/share/snapserver/stream"
```

### `folder`
Base directory for audio files.  
If you send `"alert.mp3"`, the add-on plays:

```
/config/www/alert.mp3
```

### `volume`
Default volume for playback.

### `use_pipe`
- `false` → Use ALSA (`aplay`)
- `true` → Use Snapserver Pipe (`sox` → FIFO)

### `pipe`
Path to Snapserver FIFO, e.g.:

```
/share/snapserver/stream
```

---

# Usage

## From Developer Tools → Actions

```yaml
service: hassio.addon_stdin
data:
  addon: local_audio
  input: "alert.mp3;80"
```

## From a script

```yaml
script:
  play_alert:
    sequence:
      - service: hassio.addon_stdin
        data:
          addon: local_audio
          input: "alarm.wav;70"
```

## With Snapserver Pipe

Enable in add-on config:

```yaml
use_pipe: true
pipe: "/share/snapserver/stream"
```

Audio will play everywhere Snapclient is connected.

---

# Troubleshooting

### File not found
Make sure the file exists in `/config/www`.

### No audio in pipe mode
Ensure Snapserver Pipe add-on is running and the FIFO exists.

---

# License

MIT License unless otherwise specified.


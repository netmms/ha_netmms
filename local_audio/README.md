# Local Audio Player Add-on for Home Assistant

The **Local Audio Player** add-on allows Home Assistant to play audio files **locally on the Home Assistant host**, or alternatively **send decoded PCM audio into a Snapserver pipe** for synchronized multi-room audio.

This add-on is part of the **NETMMS Home Assistant Add-ons** collection.

---

## Overview

This add-on provides:

- Local audio playback using `play` (SoX)
- Optional **pipe mode**:
  - Decodes audio to raw PCM using `sox`
  - Sends it into a named pipe (FIFO), typically consumed by the **Snapserver Pipe** add-on
- Volume control (per playback and default level)
- Support for playing any audio file readable by SoX
- Works through Home Assistant automations or scripts by writing commands to STDIN  
  (Home Assistant service sends lines like `"file.mp3;60"`)

---

## Features

### Local ALSA Audio
When `use_pipe: false`, audio plays directly on the Home Assistant host speakers:

```
play -q <file> --buffer 32768 -t alsa
```

### Pipe Mode for Snapserver
When `use_pipe: true`, audio is streamed into a FIFO for multi-room audio via Snapserver Pipe:

```
sox <file> -t raw -b 16 -e signed -r 48000 -c 2 <pipe_path>
```

This enables Home Assistant to become a **synchronized audio source** for your Snapcast network.

---

## Configuration

Add-on options:

```yaml
folder: "/config/www"
volume: 60
use_pipe: false
pipe: "/share/snapserver/stream"
```

### `folder`
The default folder from which audio files are played.

### `volume`
System volume (0–100%) set before each playback.

### `use_pipe`
Boolean  
- `false` – play locally via ALSA  
- `true` – output raw PCM audio to the FIFO defined in `pipe`

### `pipe`
A path to a named pipe (FIFO).  
Used only when `use_pipe: true`.

Defaults to:

```
/share/snapserver/stream
```

---

## How Playback Works

Commands are read from STDIN in the format:

```
<file>;<volume>
```

Examples:

```
/config/www/alert.mp3;70
doorbell.wav;90
```

If volume is omitted:

```
alert.mp3
```

then the default volume is used (from `options.volume`).

---

## Pipe Mode Example (with Snapserver Pipe)

1. Install **Snapserver Pipe** add-on  
2. It creates a FIFO at:  
   `/share/snapserver/stream`
3. Configure this add-on:

```yaml
use_pipe: true
pipe: "/share/snapserver/stream"
```

4. Play audio:

```
"/config/www/alert.mp3;80"
```

Audio will now be played in sync across all Snapclients in your home.

---

## Troubleshooting

### No audio in local mode
- Ensure the host’s ALSA device is available
- Try SSHing into HAOS and playing a test tone:
  ```
  play -n synth sine 440
  ```

### Snapserver not receiving audio in pipe mode
- Confirm the FIFO exists:
  ```
  ls -l /share/snapserver/stream
  ```
- Confirm Snapserver Pipe add-on uses `pipe:///share/snapserver/stream`

### “FIFO blocked / no reader”
- Start Snapserver Pipe **first**, then play audio  
  (FIFO waits for a reader before allowing writes)

---

## License

MIT License unless otherwise specified.

---

## Credits

- Snapcast by badaix
- NETMMS Home Assistant Add-ons
- Home Assistant community

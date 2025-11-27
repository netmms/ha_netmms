# Web Megaphone Add-on for Home Assistant

The **Web Megaphone** add-on provides a flexible, browser-accessible public-address (PA) audio system that runs directly on your Home Assistant host.  
It allows any device on your network to open a simple web page and broadcast live audio or trigger audio playback through two independently controlled volume channels.

This add-on is part of the **NETMMS Home Assistant Add-ons** collection.

---

## Overview

The Web Megaphone add-on exposes two HTTP endpoints (ports **8000** and **8001**) that act as audio “zones.”  
Any device (phone, tablet, PC) can connect to either web interface and broadcast audio directly to your Home Assistant host speakers.

Typical use cases include:

- Broadcasting quick voice messages from a phone or laptop  
- Replacing a traditional PA/public announcement system  
- Triggering alerts or sirens from scripts  
- Using with other add-ons such as **Local Audio Player** or **Snapserver Pipe** for distributed audio

---

## Features

- Two independent audio channels (port 8000 and port 8001)
- Each channel has its own configurable volume
- Plays through Home Assistant’s local audio output
- Browser-based interface—no app required
- Works on all architectures supported by Home Assistant
- Optional integration with Snapcast via the Local Audio Player add-on

---

## Configuration

The add-on exposes the following options in *Settings → Add-ons → Web Megaphone → Configuration*:

```yaml
volume1: 40
volume2: 80
```

### `volume1`
Default playback volume (0–100%) for the **8000** interface.

### `volume2`
Default playback volume (0–100%) for the **8001** interface.

---

## Ports

| Port      | Purpose                         |
|-----------|---------------------------------|
| **8000**  | Web Megaphone channel 1         |
| **8001**  | Web Megaphone channel 2         |

Both ports serve an HTTP interface that clients can use to transmit or trigger audio.

Example:

```
http://homeassistant.local:8000
http://homeassistant.local:8001
```

---

## Usage Examples

### Broadcast your voice from a phone
1. Join the same network as Home Assistant.  
2. Open Safari/Chrome:  
   ```
   http://homeassistant.local:8000
   ```  
3. Use the page controls to start broadcasting through HA speakers.

### Trigger a message using Home Assistant
You can POST to the endpoint from an automation to trigger a sound or announcement.

### Combine with Snapserver Pipe
To distribute announcements through multi-room speakers:

1. Install **Snapserver Pipe** add-on  
2. Install **Local Audio Player** add-on  
3. Configure Local Audio Player to output audio to the Snapserver FIFO  
4. Use Web Megaphone for live announcements → Snapserver distributes them everywhere

---

## Troubleshooting

### No sound?
- Confirm Home Assistant audio works (`play -n synth sine 440`)
- Check host volume (amixer)
- Ensure no other add-on is locking ALSA

### Web interface does not load?
- Verify host networking is enabled (it is by default)
- Confirm firewall settings if using HAOS behind a more restrictive router

### Audio stutters?
- Try lowering volume or reducing client CPU load  
- Check Wi-Fi strength on the broadcasting device  

---

## License

MIT License unless otherwise stated.

---

## Credits

- NETMMS Home Assistant Add-ons  
- Home Assistant community  
- Contributors and testers  

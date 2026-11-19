# Quran Stream Server Add-on for Home Assistant

A small HTTP file server for the NETMMS ESP32 stream players (S-Player). It serves the MP3 files in a folder of the
Home Assistant **Media** share, and the players stream them one after the other.

---

# Features

- Serves `/media/quran` (configurable) on port **8099**.
- **Sub-folders**: each player can be given its own list of sub-folders on its web page (e.g. `husari, minshawi`) and
  plays them in turn.
- Files are played in name order (`001_...mp3`, `002_...mp3`, ...). Files can be added, renamed or deleted while the
  players run: a player that asks for a file that is gone re-reads the list and starts that folder again at track 1.
- Read-only access to the Media share.

---

# Installation

1. Add the repository `https://github.com/netmms/ha_netmms` under **Add-on Store → Repositories**.
2. Install **Quran Stream Server** and start it.
3. Create the folder `quran` in the **Media** share (Samba: `\\HA-IP\media\quran`) and copy the MP3 files into it,
   or into sub-folders of it. Until the folder exists the add-on waits and checks again every 30 s.

---

# Configuration

```yaml
folder: "/media/quran"   # the music folder (inside /media)
port: 8099               # also change the port mapping if you change this
```

---

# What the players use

| URL | Returns |
|-----|---------|
| `http://HA-IP:8099/playlist.txt` | the MP3 files of the main folder, one per line |
| `http://HA-IP:8099/f/<name>` | one file of the main folder |
| `http://HA-IP:8099/d/<sub>/playlist.txt` | the MP3 files of a sub-folder |
| `http://HA-IP:8099/d/<sub>/f/<name>` | one file of a sub-folder |

Files are sent with range support, so a player can resume a file after a network drop.

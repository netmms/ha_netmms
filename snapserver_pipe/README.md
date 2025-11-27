# Snapserver (Home Assistant Add-on)

Run the Snapcast server to stream synchronized audio to Snapcast clients.

## Features
- Snapserver on ports 1704 (stream), 1705 (TCP control), 1780 (HTTP API + web)
- Config generated from add-on options
- Host networking by default for easiest discovery

## Installation
1. Copy this folder into your HA add-ons directory (e.g., `/addons/snapserver`).
2. In Home Assistant: **Settings → Add-ons → Add-on Store → ⋮ → Repositories → Local add-ons**.
3. Install **Snapserver**, set options as desired, then **Start**.

## Options
- `stream` (string): e.g., `pipe:///share/snapserver/stream?name=Main&mode=read`, `mpd:///127.0.0.1:6600`, `rtp://…`
- `sampleformat` (string): e.g., `48000:16:2`
- `buffer_ms` (int): stream buffer in ms
- `latency_ms` (int): default latency for clients
- `http_enabled` (bool), `http_bind`, `http_port`
- `rpc_bind`, `rpc_port`
- `stream_port`: audio stream port for clients
- `extra_args`: appended to `snapserver` command

## Paths
- Use `/share/snapserver/` for pipes, playlists, etc.

## Notes
- With `host_network: true`, ports are exposed on the host.
- If you prefer bridged networking, comment `host_network` and set the `ports:` mapping in `config.yaml`.

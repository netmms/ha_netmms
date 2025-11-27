# NETMMS Home Assistant Add-ons

A curated collection of high-quality, purpose-built **Home Assistant add-ons** created and maintained by **NETMMS**.  
This repository provides easy installation and seamless updates through the Home Assistant Add-on Store.

## About This Repository

**NETMMS Home Assistant Addons** is a custom add-on repository designed to extend Home Assistant with useful, reliable, and well-maintained add-ons — starting with the **Snapserver Add-on**, a lightweight audio synchronization server based on Snapcast.

This repository is compatible with:

- **Home Assistant OS**
- **Home Assistant Supervised**
- **Home Assistant Container** (via Add-on support add-ons)
- **Home Assistant Blue / Yellow**

Simply add this repository to Home Assistant and install the add-ons you need.

## Available Add-ons

### Snapserver Add-on
A fully featured Snapcast server packaged for Home Assistant.  
This add-on enables synchronized, low-latency, multi-room audio streaming across your home network.

**Features:**
- Full Snapserver implementation
- Support for pipe, MPD, RTP and other stream inputs
- Auto-generated configuration
- Web UI (Snapweb)
- Host or container networking
- Customizable sample rates, buffers, and stream setups

**Documentation:**  
See the add-on’s own `README.md` and `DOCS.md` inside the `snapserver_pipe/` folder.

## Installation

### 1. Add the repository to Home Assistant

In Home Assistant:

1. Navigate to  
   **Settings → Add-ons → Add-on Store**
2. Click the **⋮ (three dots)** menu in the top-right.
3. Choose **Repositories**.
4. Add this URL:

```
https://github.com/netmms/ha_netmms
```

5. Click **Add**, then close the dialog.

You will now see a new section:

> **NETMMS Home Assistant Add-ons**

### 2. Install any add-on

1. Click the add-on you want (e.g., **Snapserver**).
2. Click **Install**.
3. Configure the options as desired.
4. Click **Start**.

## Updating

Whenever the repository or an add-on updates, Home Assistant will automatically show an **Update Available** button.

Add-ons follow semantic versioning:

```
MAJOR.MINOR.PATCH
```

Always check the add-on `CHANGELOG.md` before upgrading.

## Repository Structure

```
ha_netmms/
│
├── repository.json         # Home Assistant repo manifest
├── README.md               # This file
│
└── snapserver_pipe/             # First add-on
    ├── config.yaml
    ├── Dockerfile
    ├── README.md
    ├── DOCS.md
    ├── CHANGELOG.md
    └── rootfs/
```

Each add-on is fully self-contained.

## Contributing

Contributions, improvements, and issue reports are welcome!  
Feel free to open:

- **Issues** for bugs or feature requests
- **Pull requests** for enhancements

Please follow Home Assistant add-on development conventions.

## License

This project is provided under the **MIT License**, unless otherwise noted inside specific add-ons.

## Acknowledgments

Special thanks to the Home Assistant community, Snapcast developers, and all contributors who make open-source home automation possible.

#!/usr/bin/env python3
"""Add-on start-up: read the add-on options, wait until the music folder exists, then run stream_server.py."""
import json, os, sys, time

try:
    with open(os.environ.get("OPTIONS_FILE", "/data/options.json")) as f:
        opts = json.load(f)
except Exception:
    opts = {}
folder = opts.get("folder") or "/media/quran"
port = int(opts.get("port") or 8099)

while not os.path.isdir(folder):
    print("folder %s does not exist yet: create it (Media share) and copy the MP3 files into it. Checking again in 30 s." % folder, flush=True)
    time.sleep(30)

here = os.path.dirname(os.path.abspath(__file__))
os.execv(sys.executable, [sys.executable, "-u", os.path.join(here, "stream_server.py"), folder, "--port", str(port)])

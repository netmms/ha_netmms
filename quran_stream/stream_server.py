#!/usr/bin/env python3
"""
stream_server.py - file server for the ESP32 stream player. Python 3.8+, no extra packages.

  python stream_server.py "D:\\Music\\box"            (Windows)
  python3 stream_server.py ~/music/box --port 8099    (Mac / Linux)

Serves every *.mp3 in the folder (names starting with "." ignored):
  GET /playlist.txt              URL-encoded file names, one per line, sorted (case-insensitive)
  GET /f/<name>                  the file, with HTTP Range support (the player resumes at the exact byte after a drop)
  GET /d/<sub>/playlist.txt      the same for a sub-folder (one level down only; 404 if there is no such folder)
  GET /d/<sub>/f/<name>          a file in that sub-folder
  GET /                          a small status page
Add, remove or rename files while it runs: the player reads a folder's list each time it enters that folder,
and again when a file it asks for is gone.
The same script runs inside the Home Assistant add-on (quran_stream), where the folder is /media/quran.
"""
import argparse, os, re, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import quote, unquote

FOLDER = "."
LOCK = threading.Lock()
STATS = {"requests": 0, "bytes": 0, "started": time.time()}

def names(folder=None):
    folder = folder or FOLDER
    try:
        n = [f for f in os.listdir(folder)
             if f.lower().endswith(".mp3") and not f.startswith(".") and os.path.isfile(os.path.join(folder, f))]
    except OSError:
        n = []
    return sorted(n, key=str.lower)

def subfolder(enc):
    """The path of a direct sub-folder of FOLDER, or None. Only one level down, no "..", no hidden folders."""
    sub = unquote(enc)
    if not sub or sub.startswith(".") or "/" in sub or "\\" in sub or "\0" in sub or sub != os.path.basename(sub):
        return None
    full = os.path.join(FOLDER, sub)
    if not os.path.isdir(full):
        return None
    if os.path.dirname(os.path.realpath(full)) != os.path.realpath(FOLDER):   # a link that points elsewhere: refused
        return None
    return full

def subfolders():
    try:
        return sorted([d for d in os.listdir(FOLDER) if not d.startswith(".") and os.path.isdir(os.path.join(FOLDER, d))], key=str.lower)
    except OSError:
        return []

class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "stream_server/1.0.1"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s  %s\n" % (time.strftime("%H:%M:%S"), fmt % args))

    def _send(self, code, body, ctype="text/plain; charset=utf-8"):
        b = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        with LOCK:
            STATS["requests"] += 1
        path = self.path.split("?", 1)[0]
        folder = FOLDER
        if path.startswith("/d/"):                                      # /d/<sub>/playlist.txt or /d/<sub>/f/<name>
            enc, _, path = path[3:].partition("/")
            folder = subfolder(enc)
            if folder is None:
                self._send(404, "no such folder"); return
            path = "/" + path
        if path == "/playlist.txt":
            self._send(200, "".join(quote(n) + "\n" for n in names(folder)))
        elif path.startswith("/f/"):
            self._file(unquote(path[3:]), folder)
        elif path == "/" and folder == FOLDER:
            up = int(time.time() - STATS["started"])
            subs = "".join("  %s/  (%d files)\n" % (d, len(names(os.path.join(FOLDER, d)))) for d in subfolders())
            self._send(200, "stream_server: %d files in %s\nrequests %d, %.1f MB sent, up %ds\n\nsub-folders:\n%s\n%s" % (
                len(names()), os.path.abspath(FOLDER), STATS["requests"], STATS["bytes"] / 1e6, up, subs or "  (none)\n", "\n".join(names())))
        else:
            self._send(404, "not found")

    def _file(self, name, folder):
        if name != os.path.basename(name) or name not in names(folder):  # no paths, only files from that folder's list
            self._send(404, "not found"); return
        full = os.path.join(folder, name)
        size = os.path.getsize(full)
        start, end, code = 0, size - 1, 200
        rng = self.headers.get("Range")
        if rng:
            m = re.match(r"bytes=(\d*)-(\d*)$", rng.strip())
            if not m or (m.group(1) == "" and m.group(2) == ""):
                self._send(400, "bad range"); return
            if m.group(1) == "":                                        # suffix: last N bytes
                start = max(0, size - int(m.group(2)))
            else:
                start = int(m.group(1))
                if m.group(2): end = min(int(m.group(2)), size - 1)
            if start >= size:
                self.send_response(416); self.send_header("Content-Range", "bytes */%d" % size)
                self.send_header("Content-Length", "0"); self.send_header("Connection", "close"); self.end_headers(); return
            code = 206
        length = end - start + 1
        self.send_response(code)
        self.send_header("Content-Type", "audio/mpeg")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        if code == 206:
            self.send_header("Content-Range", "bytes %d-%d/%d" % (start, end, size))
        self.send_header("Connection", "close")
        self.end_headers()
        sent = 0
        try:
            with open(full, "rb") as f:
                f.seek(start)
                while sent < length:
                    chunk = f.read(min(8192, length - sent))
                    if not chunk: break
                    self.wfile.write(chunk)
                    sent += len(chunk)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass                                                        # the player closed the connection (reconnect / restart): normal
        finally:
            with LOCK:
                STATS["bytes"] += sent

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="MP3 file server for the ESP32 stream player")
    ap.add_argument("folder", help="folder with the .mp3 files")
    ap.add_argument("--port", type=int, default=8099)
    a = ap.parse_args()
    FOLDER = a.folder
    if not os.path.isdir(FOLDER):
        sys.exit("not a folder: " + FOLDER)
    print("serving %d files from %s on port %d  (Ctrl+C to stop)" % (len(names()), os.path.abspath(FOLDER), a.port))
    ThreadingHTTPServer(("0.0.0.0", a.port), H).serve_forever()

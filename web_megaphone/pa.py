#!/usr/bin/env python3
"""Web Megaphone: the HTTPS server behind the PA Microphone page (port 8001).

  GET  /            the page (files from /html)
  GET  /status      JSON: is a message playing, how many are waiting, the last one done
  POST /            a recording (multipart field "audio_data", a WAV file) -> JSON {"ok", "id"}
  POST /repeat      play the last message again                          -> JSON {"ok", "id"}

The server answers right away and plays the messages one after another in a
background thread (play_msg.sh), so two phones never talk over each other and
the page can show "Playing" -> "Played". Every message played is kept in
/share/web_megaphone/last_msg.wav (for "Repeat last" and for checking the level).
"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json
import os
import queue
import shutil
import ssl
import subprocess
import sys
import threading
import time

PORT = 8001
HTML_DIR = os.path.realpath("/html")
PLAYER = "/play_msg.sh"
SHARE_DIR = "/share/web_megaphone"
LAST_MSG = os.path.join(SHARE_DIR, "last_msg.wav")
MAX_UPLOAD = 20 * 1024 * 1024        # about 3.5 minutes of 48 kHz mono
CERT = "/certs/wm.cert.pem"
KEY = "/certs/wm.key.pem"

TYPES = {
    "html": "text/html; charset=utf-8", "css": "text/css", "js": "application/javascript",
    "json": "application/json", "ico": "image/x-icon", "png": "image/png", "apng": "image/png",
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "svg": "image/svg+xml",
    "wav": "audio/wav", "xml": "application/xml", "webmanifest": "application/manifest+json",
}


def log(msg):
    print(time.strftime("%H:%M:%S ") + msg, file=sys.stderr, flush=True)


def keep_last(path):
    """Copy the message just played to /share/web_megaphone/last_msg.wav."""
    try:
        os.makedirs(SHARE_DIR, exist_ok=True)
        tmp = LAST_MSG + ".tmp"
        shutil.copyfile(path, tmp)
        os.replace(tmp, LAST_MSG)
    except OSError as e:
        log(f"cannot keep the last message: {e}")


class Player:
    """Plays the messages one at a time, in the order they arrived."""

    def __init__(self):
        self.q = queue.Queue()
        self.lock = threading.Lock()
        self.seq = 0          # id of the last message queued
        self.done = 0         # id of the last message finished
        self.playing = False
        self.error = ""
        self.counter = 0
        threading.Thread(target=self._run, daemon=True).start()

    def tmp_name(self):
        with self.lock:
            self.counter += 1
            return f"/tmp/wm_msg_{os.getpid()}_{self.counter}.wav"

    def add(self, path, keep):
        with self.lock:
            self.seq += 1
            n = self.seq
        self.q.put((n, path, keep))
        return n

    def status(self):
        with self.lock:
            return {"playing": self.playing, "waiting": self.q.qsize(), "seq": self.seq,
                    "done": self.done, "error": self.error,
                    "has_last": os.path.isfile(LAST_MSG)}

    def _run(self):
        while True:
            n, path, keep = self.q.get()
            with self.lock:
                self.playing = True
                self.error = ""
            err = ""
            try:
                r = subprocess.run([PLAYER, path], timeout=900)
                if r.returncode != 0:
                    err = "Playback failed (see the add-on log)"
                elif keep:
                    keep_last(path)
            except Exception as e:          # never let the player thread die
                err = f"Playback failed: {e}"
            try:
                os.remove(path)
            except OSError:
                pass
            if err:
                log(f"message {n}: {err}")
            with self.lock:
                self.playing = False
                self.done = n
                self.error = err


player = Player()


def multipart_field(body, content_type, field):
    """The bytes of one field of a multipart/form-data body, or None."""
    if "boundary=" not in content_type:
        return None
    boundary = content_type.split("boundary=", 1)[1].split(";", 1)[0].strip().strip('"')
    marker = b'name="' + field.encode() + b'"'
    for part in body.split(b"--" + boundary.encode()):
        head, sep, data = part.partition(b"\r\n\r\n")
        if sep and marker in head:
            # the part ends with exactly one CRLF before the next boundary;
            # strip only that, the audio itself may end in 0x0d / 0x0a bytes
            return data[:-2] if data.endswith(b"\r\n") else data
    return None


class Handler(BaseHTTPRequestHandler):
    timeout = 60                      # seconds per connection read

    def log_message(self, fmt, *args):
        # the page asks /status twice a second while a message plays: keep the log clean
        if "/status" not in self.requestline:
            log("%s %s" % (self.address_string(), fmt % args))

    def handle(self):
        try:
            super().handle()
        except (ssl.SSLError, ConnectionError, TimeoutError, OSError):
            pass                      # bad handshake (certificate warning) or client gone

    def send_body(self, code, ctype, data):
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(data)
        except (ConnectionError, ssl.SSLError):
            pass

    def send_json(self, obj, code=200):
        self.send_body(code, "application/json", json.dumps(obj).encode())

    def do_GET(self):
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        if path == "/status":
            return self.send_json(player.status())
        if path == "/":
            path = "/index.html"
        full = os.path.realpath(os.path.join(HTML_DIR, path.lstrip("/")))
        # only files inside /html (no "../" tricks to read the certificate key)
        if not full.startswith(HTML_DIR + os.sep) or not os.path.isfile(full):
            return self.send_body(404, "text/html", b"<h1>404 Not Found</h1>")
        with open(full, "rb") as f:
            data = f.read()
        ext = os.path.splitext(full)[1][1:].lower()
        self.send_body(200, TYPES.get(ext, "application/octet-stream"), data)

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length < 0 or length > MAX_UPLOAD:
            return self.send_json({"ok": False, "error": "Recording too long"}, 413)
        body = self.rfile.read(length) if length else b""

        if path == "/repeat":
            if not os.path.isfile(LAST_MSG):
                return self.send_json({"ok": False, "error": "No message yet"}, 404)
            tmp = player.tmp_name()
            try:
                shutil.copyfile(LAST_MSG, tmp)
            except OSError:
                return self.send_json({"ok": False, "error": "Cannot read the last message"}, 500)
            n = player.add(tmp, keep=False)
            log(f"message {n}: repeat last")
            return self.send_json({"ok": True, "id": n})

        if path not in ("/", "/upload"):
            return self.send_json({"ok": False, "error": "Not found"}, 404)

        audio = multipart_field(body, self.headers.get("Content-Type", ""), "audio_data")
        if not audio or len(audio) <= 44 or audio[:4] != b"RIFF":
            return self.send_json({"ok": False, "error": "No recording in the request"}, 400)
        tmp = player.tmp_name()
        try:
            with open(tmp, "wb") as f:
                f.write(audio)
        except OSError as e:
            log(f"cannot write {tmp}: {e}")
            return self.send_json({"ok": False, "error": "Cannot save the recording"}, 500)
        n = player.add(tmp, keep=True)
        log(f"message {n}: {len(audio) // 1024} KB received")
        self.send_json({"ok": True, "id": n})


def main():
    if not os.path.isfile(CERT) or not os.path.isfile(KEY):
        log(f"ERROR: certificate or key not found at {CERT} / {KEY}")
        sys.exit(1)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=CERT, keyfile=KEY)

    httpd = ThreadingHTTPServer(("", PORT), Handler)
    httpd.daemon_threads = True
    # the TLS handshake happens in each connection's own thread, so a slow or
    # refused handshake (the certificate warning) never holds up other phones
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True,
                                       do_handshake_on_connect=False)
    log(f">>> Web Megaphone listening on https port {PORT}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()

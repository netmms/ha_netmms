#!/usr/bin/env python3
"""Web Megaphone: the HTTPS server behind the PA Microphone page (port 8001).

  GET  /            the page (files from /html)
  GET  /status      JSON: is a message playing, how many are waiting, the last one done
  POST /            a recording (multipart field "audio_data", a WAV file) -> JSON {"ok", "id"}
  POST /repeat      play the last message again                          -> JSON {"ok", "id"}
  GET  /ca.crt      the home CA certificate, for installing on phones (if present)

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
# HTTPS certificate: the one made by tools/make_certs.sh and copied to
# Home Assistant's /ssl/web_megaphone/ (trusted by your devices, no warning);
# otherwise the self-signed one run.sh makes in /data (browser warning).
SSL_DIR = "/ssl/web_megaphone"
CERTS = [(os.path.join(SSL_DIR, "wm.cert.pem"), os.path.join(SSL_DIR, "wm.key.pem")),
         ("/data/wm.cert.pem", "/data/wm.key.pem")]
CA_CERT = os.path.join(SSL_DIR, "ca.crt")

TYPES = {
    "html": "text/html; charset=utf-8", "css": "text/css", "js": "application/javascript",
    "json": "application/json", "ico": "image/x-icon", "png": "image/png", "apng": "image/png",
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif", "svg": "image/svg+xml",
    "wav": "audio/wav", "xml": "application/xml", "webmanifest": "application/manifest+json",
}


def cert_end(path):
    """The certificate's 'valid until' text, or '' (uses Python's own decoder)."""
    try:
        return ssl._ssl._test_decode_cert(path).get("notAfter", "")
    except Exception:
        return ""


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
        if "/status" not in getattr(self, "requestline", ""):
            log("%s %s" % (self.address_string(), fmt % args))

    def log_error(self, fmt, *args):
        # a browser closing an idle connection (keep-alive) is normal: not an error
        if "timed out" in fmt:
            return
        self.log_message(fmt, *args)

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
        if path == "/ca.crt":
            # iPhone Safari offers to install it as a profile; Android saves it
            if not os.path.isfile(CA_CERT):
                return self.send_body(404, "text/html", b"<h1>No home certificate installed</h1>")
            with open(CA_CERT, "rb") as f:
                return self.send_body(200, "application/x-x509-ca-cert", f.read())
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
    found = [(c, k) for c, k in CERTS if os.path.isfile(c) and os.path.isfile(k)]
    if not found:
        log("ERROR: no certificate found (" + ", ".join(c for c, _ in CERTS) + ")")
        sys.exit(1)
    cert, key = found[0]
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=cert, keyfile=key)
    end = cert_end(cert)
    if cert.startswith(SSL_DIR):
        log(f"certificate {cert}, valid until {end or '?'}")
        try:
            left = (ssl.cert_time_to_seconds(end) - time.time()) / 86400 if end else 999
            if left < 30:
                log(f"WARNING: the certificate ends in {left:.0f} days: run tools/make_certs.sh "
                    f"and copy the new wm.cert.pem / wm.key.pem to {SSL_DIR}")
        except ValueError:
            pass
    else:
        log(f"certificate {cert} (self-signed: browsers will warn). "
            f"For no warning see 'Certificates' in the add-on README.")

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

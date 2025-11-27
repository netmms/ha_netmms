from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl
import os
import sys


def get_ip_address():
    # Do not assume order of hostname -i output
    ip_list = os.popen("hostname -i").read().split()
    for ip in ip_list:
        if ":" in ip:
            continue
        return ip.strip()
    return "0.0.0.0"


def read_file(fname):
    if not os.path.isfile(fname):
        return b""
    with open(fname, "rb") as f:
        return f.read()


def content_type(path):
    ext = os.path.splitext(path)[1][1:].lower()
    if ext == "css":
        type_ = "text/css"
    elif ext == "ico":
        type_ = "image/x-icon"
    elif ext == "png":
        type_ = "image/png"
    elif ext == "jpg" or ext == "jpeg":
        type_ = "image/jpeg"
    elif ext == "gif":
        type_ = "image/gif"
    elif ext == "wav":
        type_ = "audio/wav"
    elif ext == "js":
        type_ = "application/javascript"
    elif ext == "zip":
        type_ = "application/x-zip"
    elif ext == "gz":
        type_ = "application/x-gzip"
    else:
        type_ = "text/html"
    return type_


# Bind on all interfaces
host_name = ""  # 0.0.0.0


class MyServer(SimpleHTTPRequestHandler):
    def do_HEAD(self, type_):
        self.send_response(200)
        self.send_header("Content-type", type_)
        self.end_headers()

    def _redirect(self, path):
        self.send_response(303)
        self.send_header("Content-type", "text/html")
        self.send_header("Location", path)
        self.end_headers()

    def do_GET(self):
        path = self.path
        if path == "/":
            path = "/index.html"

        # Serve from /html directory inside container
        full_path = "html" + path

        html = read_file(full_path)
        if not html:
            self.send_error(404, "Not Found")
        else:
            self.do_HEAD(content_type(full_path))
            self.wfile.write(html)

    def do_POST(self):
        # Read Content-Length
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0

        if length <= 0:
            self.send_error(400, "Bad Request: missing or invalid Content-Length")
            return

        body = self.rfile.read(length)

        # Expect multipart
        content_type_header = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type_header or "boundary=" not in content_type_header:
            self.send_error(400, "Bad Request: expected multipart/form-data")
            return

        # Extract boundary
        boundary = content_type_header.split("boundary=", 1)[1].strip()
        if boundary.startswith('"') and boundary.endswith('"'):
            boundary = boundary[1:-1]
        boundary = boundary.encode()

        # Parse multipart parts
        parts = body.split(b"--" + boundary)
        audio_data = None

        for part in parts:
            if b"Content-Disposition" in part and b'name="audio_data"' in part:
                if b"\r\n\r\n" in part:
                    _, data = part.split(b"\r\n\r\n", 1)
                    audio_data = data.rstrip(b"\r\n")
                    break

        if audio_data is None:
            self.send_error(400, "Bad Request: audio_data field not found")
            return

        # Save WAV
        try:
            with open("/msg.wav", "wb") as f:
                f.write(audio_data)
        except Exception as e:
            print(f"Error writing /msg.wav: {e}", file=sys.stderr)
            self.send_error(500, "Internal Server Error: cannot write file")
            return

        # Trigger playback
        os.system("/play_msg.sh")

        # Redirect back to page
        self._redirect("/")


def init_server(flag, port):
    certfile = "/ssl/wm.cert.pem"
    keyfile = "/ssl/wm.key.pem"

    # Certificate check
    if not os.path.isfile(certfile) or not os.path.isfile(keyfile):
        print(
            f"ERROR: Certificate or key not found at {certfile} / {keyfile}",
            file=sys.stderr,
        )
        sys.exit(1)

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=certfile, keyfile=keyfile)
    context.check_hostname = False

    with HTTPServer((host_name, port), MyServer) as httpd:
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        ip = get_ip_address()
        print(
            f">>> Server {ip} started on port {port} (https)",
            file=sys.stderr,
        )
        httpd.serve_forever()
        httpd.server_close()


if __name__ == "__main__":
    init_server(2, 8001)


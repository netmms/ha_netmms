from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl, cgi
import os, sys, time


def get_ip_address():
    # do not make any assumptions about the order of the output!
    ip_list = os.popen("hostname -i").read().split()
    for ip in ip_list:
        if ":" in ip:
            continue
        else:
            return ip.strip()


def read_file(fname):
    if not os.path.isfile(fname):
        return b""
    with open(fname, "rb") as f:
        return f.read()


def content_type(path):
    ext = os.path.splitext(path)[1][1:]
    if ext == "css":
        type_ = "text/css"
    elif ext == "ico":
        type_ = "image/x-icon"
    elif ext == "png":
        type_ = "image/png"
    elif ext == "jpg":
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


# empty string = all interfaces (0.0.0.0)
host_name = ""


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

        # serve from /html directory inside the container
        path = "html" + path

        html = read_file(path)
        if not html:
            self.send_error(404)
        else:
            self.do_HEAD(content_type(path))
            self.wfile.write(html)

    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers["Content-Type"],
            },
        )

        # save incoming audio data to /msg.wav
        with open("/msg.wav", "wb") as f:
            data = form.getfirst("audio_data")
            # FieldStorage may return str or bytes; normalise to bytes
            if isinstance(data, str):
                data = data.encode("latin1")
            f.write(data)

        # play the recorded message
        os.system("/play_msg.sh")

        # redirect back to web UI
        self._redirect("/")


def init_server(flag, port):
    # HTTPS server using certs from /ssl
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(
        certfile="/certs/wm.cert.pem",
        keyfile="/certs/wm.key.pem"
    )
    context.check_hostname = False

    with HTTPServer((host_name, port), MyServer) as httpd:
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
        print(
            ">>> Server %s started on port %s (https)" % (host_name or "0.0.0.0", port),
            file=sys.stderr,
        )
        httpd.serve_forever()
        httpd.server_close()


if __name__ == "__main__":
    # start HTTPS server on port 8001
    init_server(2, 8001)

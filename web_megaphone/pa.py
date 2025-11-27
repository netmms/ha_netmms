from http.server import HTTPServer, SimpleHTTPRequestHandler
import ssl, cgi
import os, sys, time

def get_ip_address():
    # do not make any assumptions about the order of the output!
    ip_list = os.popen("hostname -i").read().split()
    for ip in (ip_list):
        if ":" in ip: continue
        else: return ip.strip()

def read_file(fname):
    if not os.path.isfile(fname):
        return ''
    file = open(fname, 'rb')
    content = file.read()
    file.close()
    return content
    
def content_type(path): 
    ext = os.path.splitext(path)[1][1:]
    if   ext == 'css':  type = 'text/css'
    elif ext == 'ico':  type = 'image/x-icon'
    elif ext == 'png':  type = 'image/png'
    elif ext == 'jpg':  type = 'image/jpeg'
    elif ext == 'gif':  type = 'image/gif'
    elif ext == 'wav':  type = 'audio/wav'
    elif ext == 'js':   type = 'application/javascript'
    elif ext == 'zip':  type = 'application/x-zip'
    elif ext == 'gz':   type = 'application/x-gzip'
    else:               type = 'text/html'
    return type

host_name = ""
# host_name = get_ip_address()

class MyServer(SimpleHTTPRequestHandler):
    def do_HEAD(self, type):
        self.send_response(200)
        self.send_header('Content-type', type)
        self.end_headers()

    def _redirect(self, path):
        self.send_response(303)
        self.send_header('Content-type', 'text/html')
        self.send_header('Location', path)
        self.end_headers()

    def do_GET(self):
        path = self.path
        if path == '/': path = '/index.html'

        path = 'html' + path

        html = read_file(path)
        if html == '':
            self.send_error(404)
        else:
            self.do_HEAD(content_type(path))
            self.wfile.write(html)

    def do_POST(self):
        form = cgi.FieldStorage(fp=self.rfile, headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                'CONTENT_TYPE':self.headers['Content-Type'],
                })

        file = open('/msg.wav', 'wb')
        file.write(form.getfirst('audio_data'))
        file.close()

        # the forward slash is required
        os.system("/play_msg.sh")
            
        self._redirect('/') # Redirect back to the root url

def init_server(flag, port):
  context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
  context.load_cert_chain(certfile='pzpray.local.cert.pem', keyfile='pzpray.local.key.pem')
  context.check_hostname = False

  with HTTPServer((host_name, port), MyServer) as httpd:
      httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
       
      print(">>> Server %s started on port %s" %(host_name, port), file=sys.stderr)

      httpd.serve_forever()
      httpd.server_close()

      VERBOSE = "True"

if __name__ == '__main__':

    init_server(2,8001)
    # os.system("python3 -m http.server 8001")

    # try:
        # while 1:
            # time.sleep(5000)
    # except KeyboardInterrupt:
        # print("Received keyboard interrupt")
        # sys.exit()

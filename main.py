from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import socket
from threading import Thread
from pathlib import Path
from datetime import datetime
import json
import logging
from time import sleep, ctime

HTTP_IP = '0.0.0.0'
HTTP_PORT = 3000
SOCKET_IP = '127.0.0.1'
SOCKET_PORT = 5000
STORAGE_DIR = Path('storage')
FILE_STORAGE = STORAGE_DIR / 'data.json'


class HttpHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if Path(pr_url.path[:1]).exists():
                self.send_static(pr_url.path)
            else:
                self.send_html_file('error.html', 404)
  
       
    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())
    
    
    def send_static(self, path):
        self.send_response(200)
        mt = mimetypes.guess_type(path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{path}', 'rb') as file:
            self.wfile.write(file.read())


    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        send_data_to_socket(data)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()      
    

def send_data_to_socket(data):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(data, (SOCKET_IP, SOCKET_PORT))
    sock.close()


def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = (HTTP_IP, HTTP_PORT)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def run_socket_server(ip=SOCKET_IP, port=SOCKET_PORT):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((ip, port))
    try:
        while True:
            data, address = s.recvfrom(1024)
            save_data_to_json(data)
    except KeyboardInterrupt:
        s.close()


def save_data_to_json(data):
    data_parse = urllib.parse.unquote_plus(data.decode())
    data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
    try:
        with open(FILE_STORAGE, 'r') as f:
            storage = json.load(f)
    except ValueError:
        storage = {}
    storage.update({str(datetime.now()): data_dict})
    with open(FILE_STORAGE, 'w') as f:
        json.dump(storage, f)    


def main():
    STORAGE_DIR.mkdir(exist_ok=True)
    if not FILE_STORAGE.exists():
        with open(FILE_STORAGE, 'w') as f:
            json.dump({}, f)
    http_server = Thread(target=run_http_server)
    socket_server = Thread(target=run_socket_server)
    http_server.start()
    socket_server.start()
    http_server.join()
    socket_server.join()
    print('Done!')


if __name__ == '__main__':
   
    main()

       
# http://localhost:3000/    
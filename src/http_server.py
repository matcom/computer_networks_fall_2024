import http.server
import socketserver
from threading import Thread
from src.request_handler import HTTPRequestHandler

class HTTPServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.server = socketserver.TCPServer((host, port), HTTPRequestHandler)
    
    def start(self):
        print(f"Servidor HTTP iniciado en http://{self.host}:{self.port}")
        self.server.serve_forever()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Servidor HTTP Personalizado')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    
    server = HTTPServer(host=args.host, port=args.port)
    server.start()
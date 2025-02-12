#import http.server
#import socketserver 

from request_handler import HTTPRequestHandler
from http.server import HTTPServer as BaseHTTPServer
from socketserver import ThreadingMixIn
import logging

from utils.logger import configure_logging, RequestLogger
from utils.rate_limiter import RateLimiter

class ThreadedHTTPServer(ThreadingMixIn, BaseHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.logger = logging.getLogger("HTTP.Server")  # Inicializar aquí
        self.rate_limiter = RateLimiter()  # Añadir rate limiter
  # Reutilizar dirección para reinicios rápidos

class HTTPServer:
    def __init__(self, host='0.0.0.0', port=8080):
        configure_logging()
        self.rate_limiter = RateLimiter()
        self.server = ThreadedHTTPServer((host, port), HTTPRequestHandler)
        self.host = host
        self.port = port
        self.server.rate_limiter =RateLimiter()
       
    
    def start(self):
        #self.logger = logging.getLogger("HTTP Server")
        #self.logger.info(f"Starting server on {self.host}:{self.port}")
        #self.server.serve_forever()
        self.server.logger.info(
            f"Servidor iniciado en {self.server.server_address[0]}:{self.server.server_address[1]}"
        )
        try:
            self.server.serve_forever()  # Bucle principal de servicio
        except KeyboardInterrupt:
            self.server.logger.info("Deteniendo servidor...")

if __name__ == "__main__":
    #import argparse
    #parser = argparse.ArgumentParser(description='Servidor HTTP Personalizado')
    #parser.add_argument('--host', default='0.0.0.0')
    #parser.add_argument('--port', type=int, default=8080)
    #args = parser.parse_args()
    #
    #server = HTTPServer(host=args.host, port=args.port)
    server = HTTPServer()
    server.start()


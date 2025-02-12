#from utils.types import HTTPResponse
#from typing import Dict, Any

from util import validate_auth
from http.server import BaseHTTPRequestHandler
from routes import router

import json
import logging

class HTTPRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def _get_client_ip(self) -> str:
        """Obtiene IP real considerando proxies"""
        return self.headers.get('X-Forwarded-For', self.client_address[0])

    def _set_response(self, status_code=200, headers=None, body=None) -> None:
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        
        self.end_headers()
        
        if body:
            response = {
                "status": status_code,
                "body": body
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_GET(self):
        #client_ip = self._get_client_ip()
        #logger = logging.getLogger("HTTP.Handler")
#
        ## Verificar rate limiting
        #if not self.server.rate_limiter.check_limit(client_ip):
        #    self.server.logger.warning(f"Rate limit exceeded for {client_ip}")
        #    self._set_response(429, body="Too many requests")
        #    return
        
        # Acceder al logger del servidor
        logger = self.server.logger 
        client_ip = client_ip = self._get_client_ip()
        
        if not self.server.rate_limiter.check_limit(client_ip):
            logger.warning(f"Rate limit excedido: {client_ip}")
            self._set_response(429, body="Too many requests")
            return

        logger.info(f"{self.command} {self.path} from {self.client_address[0]}")

        # Validar autenticación para rutas seguras
        if self.path.startswith('/secure'):
            if not validate_auth(self.headers.get('Authorization')):
                logger.warning(f"Intento de acceso no autorizado a {self.path} desde {client_ip}")
                self._set_response(401, body="Authorization header missing")
                return

        # Delegar a router        
        response = router.handle_request(self)
        self._set_response(**response)

    # Implementar métodos similares para POST, PUT, DELETE, etc.
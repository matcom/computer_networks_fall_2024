from http.server import BaseHTTPRequestHandler
import json
from src.routes import router
from src.utils import parse_headers, validate_auth

class HTTPRequestHandler(BaseHTTPRequestHandler):
    def _set_response(self, status_code=200, headers=None, body=None):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        
        if headers:
            for key, value in headers.items():
                self.send_header(key, value)
        
        self.end_headers()
        
        if body:
            self.wfile.write(json.dumps({
                "status": status_code,
                "body": body
            }).encode('utf-8'))

    def do_GET(self):
        if self.path == '/secure':
            if not validate_auth(self.headers.get('Authorization')):
                self._set_response(401, body="Authorization header missing")
                return
                
        response = router.handle_request(self)
        self._set_response(**response)

    # Implementar métodos similares para POST, PUT, DELETE, etc.
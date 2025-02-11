import socket
from threading import Thread
import gzip
import datetime
import zlib
from logger import logger
from status import HTTP_STATUS_CODES

# Configuración del servidor
HOST = '0.0.0.0'  # Escucha en todas las interfaces
PORT = 8000        # Puerto del servidor
VERSION = 'HTTP/1.1'  #Version


class HTTPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def start(self):
        """Inicia el servidor y acepta conexiones entrantes en hilos separados."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Permite reutilizar el puerto
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        
        logger.info(f"Servidor HTTP en {self.host}:{self.port}")

        while True:
            client_socket, client_address = server_socket.accept()
            logger.info(f"Conexión entrante desde {client_address}")
            thread = Thread(target=self.handle_client, args=(client_socket,))
            thread.start()

    def handle_client(self, client_socket):
        """Maneja una conexión entrante procesando la solicitud HTTP y enviando una respuesta."""
        try:
            request_data = client_socket.recv(1024).decode()
            if not request_data:
                client_socket.close()
                return

            response = self.handle_request(request_data)
            client_socket.sendall(response.encode())

        except Exception as e:
            logger.error(f"Error al procesar la solicitud: {e}")
            client_socket.sendall(self.http_response(500, "Internal Server Error", "An unexpected error occurred.").encode())

        finally:
            client_socket.close()

    def handle_request(self, request):
        """Procesa la solicitud HTTP y genera la respuesta adecuada."""
        try:
            lines = request.split("\r\n")
            request_line = lines[0].split(" ")
            method, path, _ = request_line

            headers = self.parse_headers(lines[1:])
            body = ""

            if "Content-Length" in headers:
                body_length = int(headers["Content-Length"])
                body = request[-body_length:]  # Extraer el cuerpo del mensaje si existe

            return self.build_response(method, path, headers, body)

        except Exception:
            return self.http_response(400, "Bad Request", "Invalid request format.")

    def parse_headers(self, header_lines):
        """Convierte líneas de encabezados HTTP en un diccionario."""
        headers = {}
        for line in header_lines:
            if ": " in line:
                key, value = line.split(": ", 1)
                headers[key] = value
        return headers

    def build_response(self, method, path, headers, body):
        """Genera respuestas HTTP según el método y la ruta solicitada."""

        logger.info(f"Method : {method} - Path: {path}")
        
        # 414 - URI Too Long
        if len(path) > 2048:
            return self.http_response(414)

        # Verificar si el cliente tiene una versión válida del recurso (usando If-Modified-Since o If-None-Match)
        last_modified = self.get_last_modified(path)  # Esta función puede devolver la última fecha de modificación del recurso
        if last_modified:
            if "If-Modified-Since" in headers:
                if_modified_since = headers["If-Modified-Since"]
                if if_modified_since >= last_modified:
                    return self.http_response(304, headers=headers)  # No se ha modificado, devolver 304

            if "If-None-Match" in headers:
                if_none_match = headers["If-None-Match"]
                if if_none_match == self.get_etag(path):  # Comparar con el ETag
                    return self.http_response(304, headers=headers)  # ETag coincide, devolver 304

        # Redirecciones
        if path == "/old-page":
            return self.http_response(301, location="/new-page")
        
        if path == "/temp-move":
            return self.http_response(302, location="/temporary-page")  # 302 Found

        
         # Si la ruta no existe
        if path != "/":
            return self.http_response(404)
        
        # 411 - Length Required
        if method in ["POST", "PUT"] and "Content-Length" not in headers:
            return self.http_response(411)

        # 415 - Unsupported Media Type
        if method in ["POST", "PUT"]:
            supported_types = ["application/json", "application/x-www-form-urlencoded", "text/plain"]
            if "Content-Type" in headers and headers["Content-Type"] not in supported_types:
                return self.http_response(415)

        if method == "GET":
            return self.http_response(200, "Hello, GET!")

        elif method == "POST":
            return self.http_response(200, f"Received POST: {body}")

        elif method == "HEAD":
            return self.http_response(200, "", include_body=False)

        elif method == "PUT":
            return self.http_response(200, "PUT request successful!")

        elif method == "DELETE":
            return self.http_response(200, "DELETE request successful!")

        elif method == "OPTIONS":
            return self.http_response(200, "", headers={"Allow": "OPTIONS, GET, POST, HEAD, PUT, DELETE, TRACE, CONNECT"})

        elif method == "TRACE":
            return self.http_response(200, f"TRACE received:\n{headers}")

        else:
            return self.http_response(405)

    def http_response(self, status_code, reason, body, headers=None,location=None, include_body=True):
        """Construye una respuesta HTTP válida con headers y cuerpo."""
        headers = headers or {}
        headers["Server"] = "CustomHTTPServer/1.0"
        headers["Date"] = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

        
         # Obtener el mensaje de estado y la descripción
        reason, default_body = HTTP_STATUS_CODES.get(status_code, ("Unknown", "Unknown error"))

        # Manejo de redirecciones (301, 302, etc.)
        if status_code in [301, 302, 304] and location:
            headers["Location"] = location
            body = f"Redirecting to {location}"

        # Si no se especifica un body, usar el mensaje por defecto
        if not body and include_body:
            body = default_body
            
        # Verificar si el cliente acepta gzip
        accept_encoding = headers.get("Accept-Encoding","").lower()
        accepts_gzip = "gzip" in accept_encoding
        accepts_deflate = "deflate" in accept_encoding
        
        if include_body:
            body_bytes = body.encode()
            
            if accepts_gzip:  # Si el cliente acepta gzip, comprimir la respuesta
                body_bytes = gzip.compress(body_bytes)
                headers["Content-Encoding"] = "gzip"  # Informar que está comprimido

            elif accepts_deflate:
                body_bytes = zlib.compress(body_bytes)
                headers["Content-Encoding"] = "deflate"
                
            headers["Content-Length"] = str(len(body_bytes))
        else:
            body_bytes = b""

        response = f"{VERSION} {status_code} {reason}\r\n"
        for key, value in headers.items():
            response += f"{key}: {value}\r\n"
        response += "\r\n"

        logger.debug(f"Respuesta generada: {status_code} {reason} {'-> ' + location if location else ''}")
        return response + body_bytes.decode()

    
    def stop(self):
        """Cerrar el servidor de manera ordenada."""
        if self.server_socket:
            self.server_socket.close()
            logger.info("Servidor detenido.")

# Ejecutar el servidor
if __name__ == "__main__":
    
    server = HTTPServer(HOST, PORT)
    server.start()



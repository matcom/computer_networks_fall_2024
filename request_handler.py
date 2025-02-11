import os
import mimetypes
import logging
import io

# Logger setup for the class to log events and errors.
logger = logging.getLogger(__name__)

class PicoHTTPRequestHandler:
    '''
    A simple HTTP request handler that serves static files as-is.
    Only supports GET and HEAD requests.
    - POST requests return a 403 FORBIDDEN response.
    - Other HTTP methods return a 405 METHOD NOT ALLOWED response.
    Supports HTTP/1.1 protocol.
    '''

    def __init__(
        self, 
        request_stream: io.BufferedIOBase, 
        response_stream: io.BufferedIOBase
    ):
        # Initialize the request and response streams.
        self.request_stream = request_stream
        self.response_stream = response_stream
        
        # Default headers for the HTTP response.
        self.headers = {
            'Content-Type': 'text/html',
            'Content-Length': '0',
            'Connection': 'close'
        }
        
        # Command (HTTP method) and path of the request.
        self.command = ''
        self.path = ''
        
        # Start handling the incoming request.
        self.handle()

    def handle(self) -> None:
        '''
        Handles the incoming HTTP request.
        This method should parse the request, determine the HTTP method,
        and call the appropriate handler (e.g., handle_GET, handle_HEAD).
        '''
        # Parse the incoming HTTP request.
        self._parse_request()
        
        # Determine the HTTP method and call the corresponding handler.
        method = self.command.upper()
        if method == 'GET':
            self.handle_GET()
        elif method == 'HEAD':
            self.handle_HEAD()
        elif method == 'POST':
           self.handle_POST()
        elif method == 'PUT':
           self.handle_PUT()
        elif method == 'PATCH':
           self.handle_PATCH()
        elif method == 'DELETE':
           self.handle_DELETE()
        else:
            self.send_error(405, "Method Not Allowed")

    def _parse_request(self) -> None:
        '''
        Parses the incoming HTTP request line and headers.
        The request line is expected to be in the format:
        <METHOD> <PATH> HTTP/1.1
        '''
        content_length = self.headers.get('Content-Length')
        if content_length:
            try:
                content_length = int(content_length)
            except ValueError:
                self.send_error(400, "Bad Request: Invalid Content-Length")
                return
        
        # Read the exact number of bytes specified by Content-Length.
            body = self.request_stream.read(content_length)
            if len(body) != content_length:
                self.send_error(400, "Bad Request: Incomplete Body")
                return

        logger.info('Parsing request line')
        
        # Read the first line of the request (the request line).
        requestline = self.request_stream.readline().decode()
        requestline = requestline.rstrip('\r\n')
        
        # Split the request line into its components: method, path, and HTTP version.
        parts = requestline.split(' ')
        if len(parts) != 3:
            self.send_error(400, "Bad Request")
            return
        # Extract the HTTP method, path, and version.
        self.command, self.path, _ = parts
        
        # Parse the headers.
        headers = {}
        line = self.request_stream.readline().decode()
        while line not in ('\r\n', '\n', '\r', ''):
            header_line = line.rstrip('\r\n')
            
            # Ensure the header line contains a colon separating key and value.
            if ': ' not in header_line:
                self.send_error(400, "Bad Request")
                return
            
            # Split the header into key-value pairs.
            key, value = header_line.split(': ', 1)
            headers[key] = value
            
            # Read the next line of headers.
            line = self.request_stream.readline().decode()
        
        # Update the default headers with the parsed headers.
        self.headers.update(headers)

    def handle_GET(self) -> None:
        '''
        Handles an HTTP GET request.
        This method should:
        - Locate the requested file or resource.
        - Read the file content.
        - Send the file content as the response body.
        - Include appropriate HTTP headers (e.g., Content-Type, Content-Length).
        '''
    # Predefined content for the response.
        content = b"Hola Amigo bienvenido al servidor\n"
        
        # Update the headers with the content type and length.
        self.headers.update({
            'Content-Type': 'text/html',
            'Content-Length': str(len(content)),
            'Connection': 'close'
        })
        
        # Send the HTTP response status line and headers.
        self.send_response(200, "OK")
        self.send_headers()
        
        # Write the predefined content as the response body.
        self.response_stream.write(content)
        self.response_stream.flush()

    def handle_HEAD(self) -> None:
        '''
        Handles an HTTP HEAD request.
        This method should:
        - Send the same headers as a GET request but without the response body.
        '''
        # Predefined content for the response (same as in handle_GET).
        content = b"Hola Amigo bienvenido al servidor\n"
        
        # Update the headers with the content type and length.
        self.headers.update({
            'Content-Type': 'text/html',
            'Content-Length': str(len(content)),
            'Connection': 'close'
        })
        
        # Send the HTTP response status line and headers (no body for HEAD requests).
        self.send_response(200, "OK")
        self.send_headers()

    def handle_POST(self) -> None:
        '''
        Handles an HTTP POST request.
        This method should:
        - Read the request body.
        - Process the request body (e.g., parse JSON, extract parameters).
        - Send a response back to the client.
        '''
        # Leer el cuerpo de la solicitud.
        content_length = self.headers.get('Content-Length')
        body = ""
        if content_length:
            try:
                content_length = int(content_length)
            except ValueError:
                self.send_error(400, "Bad Request: Invalid Content-Length")
                return
            
            # Leer el número exacto de bytes especificado por Content-Length.
            body = self.request_stream.read(content_length).decode()
            if len(body) != content_length:
                self.send_error(400, "Bad Request: Incomplete Body")
                return
            
            # Procesar el cuerpo de la solicitud (por ejemplo, parsear JSON o extraer parámetros).
            logger.info(f"Received POST data: {body}")

        # Crear contenido de respuesta que incluya los datos recibidos.
        response_content = f"Ha creado un post satisfactoriamente. Datos recibidos: {body}\n".encode()

        self.headers.update({
            'Content-Type': 'text/html',
            'Content-Length': str(len(response_content)),
            'Connection': 'close'
        })

        # Send the HTTP response status line and headers.
        self.send_response(200, "OK")
        self.send_headers()

        # Write the response content as the response body.
        self.response_stream.write(response_content)
        self.response_stream.flush()

    def handle_PUT(self) -> None:
        '''
        Handles an HTTP PUT request.
        This method should:
        - Read the request body.
        - Process the request body (e.g., save data to a file).
        - Send a response back to the client.
        '''
        content_length = self.headers.get('Content-Length')
        body = ""
        if content_length:
            try:
                content_length = int(content_length)
            except ValueError:
                self.send_error(400, "Bad Request: Invalid Content-Length")
                return
            
            body = self.request_stream.read(content_length).decode()
            if len(body) != content_length:
                self.send_error(400, "Bad Request: Incomplete Body")
                return
            
            logger.info(f"Received PUT data: {body}")

        response_content = f"PUT request processed successfully. Data received: {body}\n".encode()

        self.headers.update({
            'Content-Type': 'text/html',
            'Content-Length': str(len(response_content)),
            'Connection': 'close'
        })

        self.send_response(200, "OK")
        self.send_headers()
        self.response_stream.write(response_content)
        self.response_stream.flush()

    def handle_PATCH(self) -> None:
        '''
        Handles an HTTP PATCH request.
        This method should:
        - Read the request body.
        - Process the request body (e.g., update data).
        - Send a response back to the client.
        '''
        content_length = self.headers.get('Content-Length')
        body = ""
        if content_length:
            try:
                content_length = int(content_length)
            except ValueError:
                self.send_error(400, "Bad Request: Invalid Content-Length")
                return
            
            body = self.request_stream.read(content_length).decode()
            if len(body) != content_length:
                self.send_error(400, "Bad Request: Incomplete Body")
                return
            
            logger.info(f"Received PATCH data: {body}")

        response_content = f"PATCH request processed successfully. Data received: {body}\n".encode()

        self.headers.update({
            'Content-Type': 'text/html',
            'Content-Length': str(len(response_content)),
            'Connection': 'close'
        })

        self.send_response(200, "OK")
        self.send_headers()
        self.response_stream.write(response_content)
        self.response_stream.flush()

    def handle_DELETE(self) -> None:
        '''
        Handles an HTTP DELETE request.
        This method should:
        - Process the request (e.g., delete a resource).
        - Send a response back to the client.
        '''
        logger.info(f"Received DELETE request for path: {self.path}")

        response_content = f"DELETE request processed successfully for path: {self.path}\n".encode()

        self.headers.update({
            'Content-Type': 'text/html',
            'Content-Length': str(len(response_content)),
            'Connection': 'close'
        })

        self.send_response(200, "OK")
        self.send_headers()
        self.response_stream.write(response_content)
        self.response_stream.flush()

    def send_response(self, status_code: int, status_message: str) -> None:
        '''
        Sends the HTTP response status line.
        '''
        response_line = f"HTTP/1.1 {status_code} {status_message}\r\n"
        self.response_stream.write(response_line.encode())

    def send_headers(self) -> None:
        '''
        Sends the HTTP response headers.
        '''
        headers = "\r\n".join([f"{k}: {v}" for k, v in self.headers.items()]) + "\r\n\r\n"
        self.response_stream.write(headers.encode())
        self.response_stream.flush()

    def send_error(self, status_code: int, message: str) -> None:
        '''
        Sends an error response with the specified status code and message.
        '''
        self.send_response(status_code, message)
        
        # Generate a simple HTML error page.
        content = f"<html><body><h1>{status_code} {message}</h1></body></html>".encode()
        self.headers.update({
            'Content-Type': 'text/html',
            'Content-Length': str(len(content)),
            'Connection': 'close'
        })
        
        # Send the headers.
        self.send_headers()
        
        # If the request method was GET, include the error page content in the response.
        if self.command.upper() == 'GET':
            self.response_stream.write(content)
        
        # Flush the response stream to ensure all data is sent.
        self.response_stream.flush()
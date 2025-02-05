import os
import mimetypes
import logging
import io

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
        self.request_stream = request_stream
        self.response_stream = response_stream
        self.command = ''
        self.path = ''
        self.headers = {
            'Content-Type': 'text/html',
            'Content-Length': '0',
            'Connection': 'close'
        }
        self.handle()

    def handle(self) -> None:
        '''
        Handles the incoming HTTP request.
        This method should parse the request, determine the HTTP method,
        and call the appropriate handler (e.g., handle_GET, handle_HEAD).
        '''
        self._parse_request()
        method = self.command.upper()
        if method == 'GET':
            self.handle_GET()
        elif method == 'HEAD':
            self.handle_HEAD()
        elif method == 'POST':
            self.send_error(403, "Forbidden")
        else:
            self.send_error(405, "Method Not Allowed")

    def _parse_request(self) -> None:
        logger.info('Parsing request line')
        requestline = self.request_stream.readline().decode()
        requestline = requestline.rstrip('\r\n')
        logger.info(requestline)

        parts = requestline.split(' ')
        if len(parts) != 3:
            self.send_error(400, "Bad Request")
            return
        self.command, self.path, _ = parts

        headers = {}
        line = self.request_stream.readline().decode()
        while line not in ('\r\n', '\n', '\r', ''):
            header_line = line.rstrip('\r\n')
            if ': ' not in header_line:
                self.send_error(400, "Bad Request")
                return
            key, value = header_line.split(': ', 1)
            headers[key] = value
            line = self.request_stream.readline().decode()
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
        doc_root = os.getcwd()
        requested_path = os.path.join(doc_root, self.path.lstrip('/'))
        requested_path = os.path.normpath(requested_path)

        if not requested_path.startswith(doc_root):
            self.send_error(403, "Forbidden")
            return

        if not os.path.exists(requested_path) or not os.path.isfile(requested_path):
            self.send_error(404, "Not Found")
            return

        try:
            file_size = os.path.getsize(requested_path)
            mime_type, _ = mimetypes.guess_type(requested_path)
            content_type = mime_type if mime_type else 'application/octet-stream'

            self.headers.update({
                'Content-Type': content_type,
                'Content-Length': str(file_size),
                'Connection': 'close'
            })

            self.send_response(200, "OK")
            self.send_headers()

            with open(requested_path, 'rb') as file:
                while True:
                    data = file.read(4096)
                    if not data:
                        break
                    self.response_stream.write(data)
            self.response_stream.flush()

        except Exception as e:
            logger.error(f"Error handling GET request: {e}")
            self.send_error(500, "Internal Server Error")

    def handle_HEAD(self) -> None:
        '''
        Handles an HTTP HEAD request.
        This method should:
        - Locate the requested file or resource.
        - Send the same headers as a GET request but without the response body.
        '''
        doc_root = os.getcwd()
        requested_path = os.path.join(doc_root, self.path.lstrip('/'))
        requested_path = os.path.normpath(requested_path)

        if not requested_path.startswith(doc_root):
            self.send_error(403, "Forbidden")
            return

        if not os.path.exists(requested_path) or not os.path.isfile(requested_path):
            self.send_error(404, "Not Found")
            return

        try:
            file_size = os.path.getsize(requested_path)
            mime_type, _ = mimetypes.guess_type(requested_path)
            content_type = mime_type if mime_type else 'application/octet-stream'

            self.headers.update({
                'Content-Type': content_type,
                'Content-Length': str(file_size),
                'Connection': 'close'
            })

            self.send_response(200, "OK")
            self.send_headers()

        except Exception as e:
            logger.error(f"Error handling HEAD request: {e}")
            self.send_error(500, "Internal Server Error")

    def send_response(self, status_code: int, status_message: str) -> None:
        response_line = f"HTTP/1.1 {status_code} {status_message}\r\n"
        self.response_stream.write(response_line.encode())

    def send_headers(self) -> None:
        headers = "\r\n".join([f"{k}: {v}" for k, v in self.headers.items()]) + "\r\n\r\n"
        self.response_stream.write(headers.encode())
        self.response_stream.flush()

    def send_error(self, status_code: int, message: str) -> None:
        self.send_response(status_code, message)
        content = f"<html><body><h1>{status_code} {message}</h1></body></html>".encode()
        self.headers.update({
            'Content-Type': 'text/html',
            'Content-Length': str(len(content)),
            'Connection': 'close'
        })
        self.send_headers()
        if self.command.upper() == 'GET':
            self.response_stream.write(content)
        self.response_stream.flush()
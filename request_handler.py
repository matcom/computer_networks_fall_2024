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
            self.send_error(403, "Forbidden")
        else:
            self.send_error(405, "Method Not Allowed")

    def _parse_request(self) -> None:
        '''
        Parses the incoming HTTP request line and headers.
        The request line is expected to be in the format:
        <METHOD> <PATH> HTTP/1.1
        '''
        logger.info('Parsing request line')
        
        # Read the first line of the request (the request line).
        requestline = self.request_stream.readline().decode()
        requestline = requestline.rstrip('\r\n')
        logger.info(requestline)
        
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
        # Get the document root directory (current working directory).
        doc_root = os.getcwd()
        
        # Construct the full path to the requested file.
        requested_path = os.path.join(doc_root, self.path.lstrip('/'))
        requested_path = os.path.normpath(requested_path)
        
        # Ensure the requested path is within the document root to prevent directory traversal attacks.
        if not requested_path.startswith(doc_root):
            self.send_error(403, "Forbidden")
            return
        
        # Check if the requested file exists and is a file (not a directory).
        if not os.path.exists(requested_path) or not os.path.isfile(requested_path):
            self.send_error(404, "Not Found")
            return
        
        try:
            # Get the size of the file and determine its MIME type.
            file_size = os.path.getsize(requested_path)
            mime_type, _ = mimetypes.guess_type(requested_path)
            content_type = mime_type if mime_type else 'application/octet-stream'
            
            # Update the headers with the content type and length.
            self.headers.update({
                'Content-Type': content_type,
                'Content-Length': str(file_size),
                'Connection': 'close'
            })
            
            # Send the HTTP response status line and headers.
            self.send_response(200, "OK")
            self.send_headers()
            
            # Read and send the file content in chunks to avoid loading the entire file into memory.
            with open(requested_path, 'rb') as file:
                while True:
                    data = file.read(4096)
                    if not data:
                        break
                    self.response_stream.write(data)
            
            # Flush the response stream to ensure all data is sent.
            self.response_stream.flush()
        except Exception as e:
            # Log any errors that occur during the GET request handling.
            logger.error(f"Error handling GET request: {e}")
            self.send_error(500, "Internal Server Error")

    def handle_HEAD(self) -> None:
        '''
        Handles an HTTP HEAD request.
        This method should:
        - Locate the requested file or resource.
        - Send the same headers as a GET request but without the response body.
        '''
        # Get the document root directory (current working directory).
        doc_root = os.getcwd()
        
        # Construct the full path to the requested file.
        requested_path = os.path.join(doc_root, self.path.lstrip('/'))
        requested_path = os.path.normpath(requested_path)
        
        # Ensure the requested path is within the document root to prevent directory traversal attacks.
        if not requested_path.startswith(doc_root):
            self.send_error(403, "Forbidden")
            return
        
        # Check if the requested file exists and is a file (not a directory).
        if not os.path.exists(requested_path) or not os.path.isfile(requested_path):
            self.send_error(404, "Not Found")
            return
        
        try:
            # Get the size of the file and determine its MIME type.
            file_size = os.path.getsize(requested_path)
            mime_type, _ = mimetypes.guess_type(requested_path)
            content_type = mime_type if mime_type else 'application/octet-stream'
            
            # Update the headers with the content type and length.
            self.headers.update({
                'Content-Type': content_type,
                'Content-Length': str(file_size),
                'Connection': 'close'
            })
            
            # Send the HTTP response status line and headers (no body for HEAD requests).
            self.send_response(200, "OK")
            self.send_headers()
        except Exception as e:
            # Log any errors that occur during the HEAD request handling.
            logger.error(f"Error handling HEAD request: {e}")
            self.send_error(500, "Internal Server Error")

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
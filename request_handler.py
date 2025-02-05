import io  # Import the io module for handling input/output streams.
import socket 
import logging  # Import the socket module for network communication.

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
        self.client = client #pending to define client.py
        self.command = ''
        self.path = ''
        self.headers = {
            'Content-Type': 'text/html',
            'Content-Length': '0',
            'Connection': 'close'
        }
        self.data = ''
        self.handle()

    def handle(self) -> None:
        '''
        Handles the incoming HTTP request.
        This method should parse the request, determine the HTTP method,
        and call the appropriate handler (e.g., handle_GET, handle_HEAD).
        '''
        self._parse_request()

    def _parse_request(self) -> None:
        logger.info('Parsing request line')
        requestline = self.request_stream.readline().decode()
        requestline = requestline.rstrip('\r\n')
        logger.info(requestline)

        self.command = requestline.split(' ')[0]
        self.path = requestline.split(' ')[1]

        # parse the headers
        headers = {} 
        line = self.request_stream.readline().decode()
        while line not in ('\r\n', '\n', '\r', ''):
            header = line.rstrip('\r\n').split(': ')
            headers[header[0]] = header[1]
            line = self.request_stream.readline().decode()

        logger.info(headers)

    def handle_GET(self) -> None:
        '''
        Handles an HTTP GET request.
        This method should:
        - Locate the requested file or resource.
        - Read the file content.
        - Send the file content as the response body.
        - Include appropriate HTTP headers (e.g., Content-Type, Content-Length).
        '''
        pass  # Placeholder for GET request handling logic.

    def handle_HEAD(self) -> None:
        '''
        Handles an HTTP HEAD request.
        This method should:
        - Locate the requested file or resource.
        - Send the same headers as a GET request but without the response body.
        '''
        pass  # Placeholder for HEAD request handling logic.
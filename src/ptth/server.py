import socket
import threading
import logging

from http import HTTPStatus

from utils import CaseInsensitiveDict, readline

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class CloseConnection(Exception):
    pass

class HTTPRequest:

    def __init__(self, /, **kwargs):
        self.version = kwargs.get("version")
        self.verb = kwargs.get("verb")
        self.location = kwargs.get("location")
        self.headers = kwargs.get("headers")
        self.body = kwargs.get("body")

    def get_body_raw(self):
        return self.body

    def get_headers(self):
        return self.headers

    def __str__(self):
        return f"<{self.__class__.__name__} [{self.verb} @ {self.location}]>"

# stolen from http.server
DEFAULT_ERROR_MESSAGE = """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
        "http://www.w3.org/TR/html4/strict.dtd">
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
        <title>Error response</title>
    </head>
    <body>
        <h1>Error response</h1>
        <p>Error code: %(code)d</p>
        <p>Message: %(message)s.</p>
        <p>Error code explanation: %(code)s - %(explain)s.</p>
    </body>
</html>
"""

def parse_request(conn):
    buffer, index = readline(conn)
    verb, location, version = map(str.strip, buffer.decode().split(" ", 2))
    # ignore \n
    index += 1

    buffer, index = readline(conn, index)
    headers = CaseInsensitiveDict()
    while buffer != b'\r':
        header, value = map(str.strip, buffer.decode().split(":", 1))
        headers[header] = value
        index += 1
        buffer, index = readline(conn, index)
    # ignore \r
    index += 1

    body = b''
    cl = int(headers.get("Content-Length", 0))
    # sometimes it sends an incomplete response
    # it will hang if c-l is wrong
    # NOTE HEAD request returns c-l as if it were a
    # GET so it will hang as well
    # https://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.13
    while len(body) < cl:
        body += conn.recv(cl - len(body))

    return HTTPRequest(
        version=version,
        verb=verb,
        location=location,
        headers=headers,
        body=body
    )


class ClientHandler:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr

    def send(self, data):
        logging.info("INFO - sending\n%s" , data)

        self.conn.sendall(data)
        
    def _handle(self, data):
        return NotImplemented

    def handle(self):
        print(f"Connected by {self.addr}")
        
        while True:
            try:
                # Echo back the received message
                self._handle(parse_request(self.conn))
            except CloseConnection:
                print("hello")
                break
            except (Exception, KeyboardInterrupt) as e:
                print(f"Error handling client: {e}")
                break
        
        self.conn.close()
        print(f"Connection closed for {self.addr}")


class HTTPHandler(ClientHandler):

    _version = 11
    _version_str = 'HTTP/1.1'

    SUPPORTED_METHODS = (
        "GET",
    )

    def response(self, code, headers=None, body=None):
        status = HTTPStatus(code)

        headers = headers or {}
        # SHOULD
        headers["Last-Modified"] = "Thu, 06 Feb 2015 22:03:00 GMT"
        # MUST
        headers["Content-Length"] = str(len(body))
        headers["Content-Type"] = headers.get("Content-Type", "text/html")
        headers["Connection"] = headers.get("Connection", "keep-alive")

        req = f"{self._version_str} {code} {status.name}\r\n"

        for header, value in headers.items():
            req += f"{header}: {value}\r\n"

        if body:
            req += f"\r\n{body}\r\n"
        req += "\r\n"

        self.send(req.encode())

    def send_error(self, code: int):
        body = DEFAULT_ERROR_MESSAGE % dict(code=code, message=HTTPStatus(code).name, explain="Something happened")

        self.response(code, {}, body=body)

    def _handle(self, request: HTTPRequest):
        headers = {}
        headers["Connection"] = request.headers.get("Connection", "keep-alive")

        if request.verb not in self.SUPPORTED_METHODS:
            return self.send_error(405)

        self.response(200, {}, "<html>Hello, world!</html>")

        if headers["Connection"] == "close":
            # response was sent
            raise CloseConnection("As per the client's request")

        return None

def start_server(host='127.0.0.1', port=50000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen(5)
        
        print(f"Serving TCP on {host}:{port}...")

        while True:
            conn, addr = s.accept()
            
            # Create a new thread for each incoming connection
            handler = HTTPHandler(conn, addr)
            t = threading.Thread(target=handler.handle)
            
            t.start()

if __name__ == "__main__":
    start_server()

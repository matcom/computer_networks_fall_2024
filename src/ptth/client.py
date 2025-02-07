import os
import socket
import time
import logging
import gzip

from collections.abc import Callable, Mapping, MutableMapping

from parse_http_url import parse_http_url, BadUrlError
from utils import CaseInsensitiveDict, readline

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class NotConnected(Exception):
    pass

HTTP_PORT = 80

class HTTPResponse:
    
    def __init__(self, /, **kwargs):
        self.version = kwargs.get("version")
        self.code = int(kwargs.get("code"))
        self.reason = kwargs.get("reason")
        self.headers = kwargs.get("headers")
        self.body = kwargs.get("body")

    def get_body_raw(self):
        return self.body
    
    def get_headers(self):
        return self.headers

    def visualise(self):
        with open("/tmp/tmp.html", "wb") as file:
            file.write(self.body)
        os.system("xdg-open /tmp/tmp.html")

    def __str__(self):
        return f"<{self.__class__.__name__} [{self.code}]>"

def parse_response(method, conn):
    buffer, index = readline(conn)
    version, code, reason = map(str.strip, buffer.decode().split(" ", 2))
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
    if "Content-Length" in headers:
        cl = int(headers.get("Content-Length", 0))
        # sometimes it sends an incomplete response
        # it will hang if c-l is wrong
        # NOTE HEAD request returns c-l as if it were a
        # GET so it will hang as well
        # https://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.13
        while len(body) < cl and method != "HEAD":
            body += conn.recv(cl - len(body))
    elif headers.get("Transfer-Encoding") == "chunked":
        size, index = readline(conn, index)
        size = int(size, base=16) + 2 # size in hex + carrier return + \n
        body += conn.recv(size)
        index += size
        while size - 2:
            size, index = readline(conn, index)
            size = int(size, base=16) + 2 # size in hex + carrier return
            body += conn.recv(size)
            index += size

    # decode if needed
    # only gzip and identity are supported
    if headers.get("Content-Encoding") == "gzip":
        body = gzip.decompress(body)

    return HTTPResponse(
        version=version,
        code=code,
        reason=reason,
        headers=headers,
        body=body
    )

class HTTPConnection:
    _version = 11
    _version_str = 'HTTP/1.1'
    default_port = HTTP_PORT

    def __init__(self, host: "IP", port: int, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, blocksize=8192):
        self.host = host
        self.port = port
        self.timeout = timeout

        # sock
        self.sock = None
        self.blocksize = blocksize

    def connect(self):
        logging.info("INFO - connecting to %s:%s" , self.host, self.port)
        self.sock = socket.create_connection((self.host, self.port), self.timeout)

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def send(self, data):
        if not self.sock:
            raise NotConnected()
        logging.info("INFO - sending\n%s" , data)

        self.sock.sendall(data)

    def receive(self, count=1024):
        return self.sock.recv(count)

    def request(self, method, url, body="", headers=None):
        headers = headers or {}
        # https://httpwg.org/specs/rfc9110.html#field.host
        headers["Host"] = headers.get("Host", self.host)
        # https://httpwg.org/specs/rfc9110.html#field.content-length
        headers["Content-Length"] = str(len(body))
        # https://httpwg.org/specs/rfc9110.html#field.accept-encoding
        # no encoding
        headers["Accept-Encoding"] = headers.get("Accept-Encoding", "identity")
        # https://www.rfc-editor.org/rfc/rfc2616#section-14.10
        # we do not support persistent connections
        headers["Connection"] = "close"

        req = f"{method.upper()} {url} {self._version_str}\r\n"
        for header, value in headers.items():
            req += f"{header}: {value}\r\n"

        if body:
            req += f"\r\n{body}\r\n"
        req += "\r\n"

        self.send(req.encode())

    def __str__(self):
        return f"<({self.__class__.__name__}) [{self.host=}, {self.port=}]>"

    __repr__ = __str__


def request(method="GET", url="/", headers=None, body=""):
    host, port, abs_path, query = parse_http_url(url) # Can launch a BadUrlError
    conn = HTTPConnection(host, port)
    res = None
    data = None

    try:
        conn.connect()
        conn.request(method, abs_path + query, headers=headers, body=body)
        data = parse_response(method, conn.sock)
    finally:
        conn.close()

    logging.debug("%s %s %s", data, data.body, data.headers)

    return data

if __name__ == "__main__":
    #URL = "http://httpbin.org/"
    URL = "http://www.cubadebate.cu/"
    #URL = "http://127.0.0.1:8000"
    #URL = "http://anglesharp.azurewebsites.net/Chunked" # chunk
    #URL = "http://www.whatsmyip.org/

    # r
    res = request("GET", URL, headers={"Accept-Encoding": "gzip"})
    print(res)
    res.visualise()

    URL = "http://anglesharp.azurewebsites.net/Chunked" # chunk
    res = request("GET", URL)
    print(res)
    res.visualise()

    URL = "http://httpbin.org/"
    res = request("GET", URL, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"})
    print(res)
    res.visualise()

    res = request("HEAD", URL)
    print(res, res.headers)
    res = request("OPTIONS", URL)
    print(res, res.headers)

    URL = "http://httpbin.org/status/100"
    res = request("DELETE", URL)
    print(res, res.headers, res.reason, res.body)

    URL = "http://httpbin.org/anything"
    res = request("POST", URL, body="blob doko")
    print(res, res.headers, res.reason, res.body)
    res = request("PATCH", URL, body="skipped all the text")
    print(res, res.headers, res.reason, res.body)
    res = request("PUT", URL, body="dodo")
    print(res, res.headers, res.reason, res.body)
    URL = "http://47.251.122.81:8888"
    res = request("CONNECT", URL, body="dodo")
    print(res, res.headers, res.reason, res.body)

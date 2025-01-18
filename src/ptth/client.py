import os
import socket
import time

from requests.structures import CaseInsensitiveDict

class NotConnected(Exception):
    pass

HTTP_PORT = 80

class HTTPResponse:
    
    def __init__(self, /, **kwargs):
        self.version = kwargs.get("version")
        self.code = kwargs.get("code")
        self.reason = kwargs.get("reason")
        self.headers = kwargs.get("headers")
        self.body = kwargs.get("body")

    def visualise(self):
        with open("/tmp/tmp.html", "wb") as file:
            file.write(self.body)
        os.system("xdg-open /tmp/tmp.html")

    def __str__(self):
        return f"<{self.__class__.__name__} [{self.code}]>"

def readline(connection, index=0):
    buffer = b''
    while (c := connection.receive(1)) != b'\n':
        buffer += c
        index += 1

    return buffer, index

def parse_response(conn):
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
    cl = int(headers.get("Content-Length", 0))
    # sometimes it sends an incomplete response
    # it will hang if c-l is wrong
    while len(body) < cl:
        body += conn.receive(cl - len(body))

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
        print(f"INFO - connecting to %s:%s" % (self.host, self.port))
        self.sock = socket.create_connection((self.host, self.port), self.timeout)

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def send(self, data):
        if not self.sock:
            raise NotConnected()
        print(f"INFO - sending\n%s" % (data,))

        self.sock.sendall(data)

    def receive(self, count=1024):
        return self.sock.recv(count)

    def request(self, method, url, body="", headers=None):
        headers = headers or {}
        headers["Content-Length"] = str(len(body))
        headers["Accept-Encoding"] = headers.get("Accept", "identity")
        headers["Host"] = headers.get("Host", self.host)

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
    url_split = url.split("/")

    url = "/" + "/".join(url_split[3:])
    host_port = url_split[2].split(":")
    if len(host_port) < 2:
        host = host_port[0]
        port = 80
    else:
        host, port = host_port
        port = int(port)
    conn = HTTPConnection(host, port)
    res = None
    data = None
    try:
        conn.connect()
        conn.request(method, url, headers=headers, body=body)
        data = parse_response(conn)
    finally:
        conn.close()

    return data

if __name__ == "__main__":
    URL = "http://httpbin.org/"
    #URL = "http://www.cubadebate.cu/"
    #URL = "http://127.0.0.1:8000"

    res = request("GET", URL, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"})
    print(res)
    res.visualise()
    """

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
    """

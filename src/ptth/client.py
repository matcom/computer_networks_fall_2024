import os
import socket

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

def readline(data, index=0):
    buffer = b''
    while (c := chr(data[index])) != '\n':
        buffer += c.encode()
        index += 1

    return buffer, index

def parse_response(res: bytes):
    buffer, index = readline(res)
    version, code, reason = map(str.strip, buffer.decode().split(" ", 2))
    # ignore \n
    index += 1
    
    buffer, index = readline(res, index)
    headers = {}
    while buffer != b'\r':
        header, value = map(str.strip, buffer.decode().split(":", 1))
        headers[header] = value
        index += 1
        buffer, index = readline(res, index)
    # ignore \r
    index += 1

    body = res[index: index+int(headers.get("Content-Length", 0))]

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

    def receive(self):
        return self.sock.recv(1024)

    def request(self, method, url, body="", headers=None):
        headers = headers or {}
        headers["Content-Length"] = str(len(body))
        headers["User-Agent"] = headers.get("User-Agent", "blob")

        req = f"{method.upper()} {url} {self._version_str}\r\n"
        for header, value in headers.items():
            req += f"{header}: {value}\r\n"

        req += f"\r\n{body}\r\n"

        self.send(req.encode())

    def __str__(self):
        return f"<({self.__class__.__name__}) [{self.host=}, {self.port=}]>"

    __repr__ = __str__


def request(method="GET", url="/", headers=None):
    url_split = url.split("/")

    url = "/".join(url_split[3:]) or "/"
    host_port = url_split[2].split(":")
    if len(host_port) < 2:
        host = host_port[0]
        port = 80
    else:
        host, port = host_port
        port = int(port)
    conn = HTTPConnection(host, port)
    res = None
    try:
        conn.connect()
        conn.request(method, url, headers=headers)
        res = conn.receive()
    finally:
        conn.close()

    return parse_response(res)

if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8000

    res = request("GET", "http://127.0.0.1:8000/")
    res.visualise()

import socket

class NotConnected(Exception):
    pass

HTTP_PORT = 80

class HTTPConnection:
    _http_vsn = 11
    _http_vsn_str = 'HTTP/1.1'
    default_port = HTTP_PORT

    def __init__(self, host: "IP", port: int, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, blocksize=8192):
        self.host = host
        self.port = port
        self.timeout = timeout

        # sock
        self.sock = None
        self.blocksize = blocksize

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), self.timeout)

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def send(self, data):
        if not self.sock:
            raise NotConnected()
        print(f"INFO - sending %s" % (data,))

        self.sock.sendall(data)

    def receive(self):
        return self.sock.recv(1024)

    def __str__(self):
        return f"<({self.__class__.__name__}) [{self.host=}, {self.port=}]>"

    __repr__ = __str__


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 8000

    data = "hello world"
    request = (
        "GET / HTTP/1.1 \r\n"
        "Host: localhost\r\n"
        "User-Agent: blob\r\n"
        f"Content-Length: {len(data)}\r\n"
        f"\r\n{data}\r\n"
    )

    conn = HTTPConnection(host, port)
    try:
        print(conn)

        conn.connect()
        conn.send(bytes(request, "utf8"))
        print(conn.receive())
    finally:
        conn.close()

import os
import socket
import time

from collections.abc import Callable, Mapping, MutableMapping

from parse_http_url import parse_http_url, BadUrlError

# stolen from requests
class CaseInsensitiveDict(MutableMapping):
    """A case-insensitive ``dict``-like object.

    Implements all methods and operations of
    ``MutableMapping`` as well as dict's ``copy``. Also
    provides ``lower_items``.

    All keys are expected to be strings. The structure remembers the
    case of the last key to be set, and ``iter(instance)``,
    ``keys()``, ``items()``, ``iterkeys()``, and ``iteritems()``
    will contain case-sensitive keys. However, querying and contains
    testing is case insensitive::

        cid = CaseInsensitiveDict()
        cid['Accept'] = 'application/json'
        cid['aCCEPT'] == 'application/json'  # True
        list(cid) == ['Accept']  # True

    For example, ``headers['content-encoding']`` will return the
    value of a ``'Content-Encoding'`` response header, regardless
    of how the header name was originally stored.

    If the constructor, ``.update``, or equality comparison
    operations are given keys that have equal ``.lower()``s, the
    behavior is undefined.
    """

    def __init__(self, data=None, **kwargs):
        self._store = {}
        if data is None:
            data = {}
        self.update(data, **kwargs)

    def __setitem__(self, key, value):
        # Use the lowercased key for lookups, but store the actual
        # key alongside the value.
        self._store[key.lower()] = (key, value)

    def __getitem__(self, key):
        return self._store[key.lower()][1]

    def __delitem__(self, key):
        del self._store[key.lower()]

    def __iter__(self):
        return (casedkey for casedkey, mappedvalue in self._store.values())

    def __len__(self):
        return len(self._store)

    def lower_items(self):
        """Like iteritems(), but with all lowercase keys."""
        return ((lowerkey, keyval[1]) for (lowerkey, keyval) in self._store.items())

    def __eq__(self, other):
        if isinstance(other, Mapping):
            other = CaseInsensitiveDict(other)
        else:
            return NotImplemented
        # Compare insensitively
        return dict(self.lower_items()) == dict(other.lower_items())

    # Copy is required
    def copy(self):
        return CaseInsensitiveDict(self._store.values())

    def __repr__(self):
        return str(dict(self.items()))


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

def readline(connection, index=0):
    buffer = b''
    while (c := connection.receive(1)) != b'\n':
        buffer += c
        index += 1

    return buffer, index

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
    cl = int(headers.get("Content-Length", 0))
    # sometimes it sends an incomplete response
    # it will hang if c-l is wrong
    # NOTE HEAD request returns c-l as if it were a
    # GET so it will hang as well
    # https://www.w3.org/Protocols/rfc2616/rfc2616-sec14.html#sec14.13
    while len(body) < cl and method != "HEAD":
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
        # https://httpwg.org/specs/rfc9110.html#field.host
        headers["Host"] = headers.get("Host", self.host)
        # https://httpwg.org/specs/rfc9110.html#field.content-length
        headers["Content-Length"] = str(len(body))
        # https://httpwg.org/specs/rfc9110.html#field.accept-encoding
        # no encoding
        headers["Accept-Encoding"] = headers.get("Accept", "identity")

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
    host,port,_,_ = parse_http_url(url) # Can launch a BadUrlError
    conn = HTTPConnection(host, port)
    res = None
    data = None
    try:
        conn.connect()
        conn.request(method, url, headers=headers, body=body)
        data = parse_response(method, conn)
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

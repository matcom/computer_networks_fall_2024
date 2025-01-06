import socket

class SMTPConnection:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        self._receive()

    def send(self, data):
        self.sock.sendall(data.encode())

    def _receive(self):
        return self.sock.recv(1024).decode()

    def close(self):
        self.sock.close()

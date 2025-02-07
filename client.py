import socket
import grammar

class httpClient :
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
    
    def send_request(self, method: str, header: str, data: str):
        request = grammar.httpRequest.build(method=method, headers=header, body=data)
        self.socket.send(request.encode())
        response = self.socket.recv(1024)
        return response
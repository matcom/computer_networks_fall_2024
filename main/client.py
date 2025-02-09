import socket
import sys


class FTPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.control_socket.connect((self.host, self.port))
        self.receive_response()  # Recibir mensaje de bienvenida

    def receive_response(self):
        response = self.control_socket.recv(4096).decode('utf-8')
        print(response, end='')
        return response

    def send_command(self, command):
        self.control_socket.send((command + '\r\n').encode('utf-8'))
        return self.receive_response()

    def login(self, username, password):
        self.send_command(f'USER {username}')
        self.send_command(f'PASS {password}')




if __name__ == "__main__":
    main()
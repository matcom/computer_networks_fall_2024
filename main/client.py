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




def main():
    if len(sys.argv) < 8:
        print("Uso: python client.py -p PORT -h HOST -u USER -w PASS -c COMMAND -a ARG1 -b ARG2")
        return

    args = {}
    for i in range(1, len(sys.argv), 2):
        args[sys.argv[i]] = sys.argv[i + 1]

    host = args['-h']
    port = int(args['-p'])
    user = args['-u']
    password = args['-w']
    command = args['-c']
    arg1 = args.get('-a', '')
    arg2 = args.get('-b', '')

    client = FTPClient(host, port)
    client.login(user, password)

    if command == "LIST":
        client.list_files()
    elif command == "RETR":
        client.retr(arg1)
    elif command == "STOR":
        client.stor(arg1)
    else:
        print(f"Comando '{command}' no reconocido.")

    client.quit()


if __name__ == "__main__":
    main()
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

    def list_files(self):
        response = self.send_command('LIST')
        if "150" in response:
            return self.receive_response()

    def quit(self):
        self.send_command('QUIT')
        self.control_socket.close()
        print("Conexión cerrada.")


def main():
    if len(sys.argv) != 3:
        print("Uso: python client.py <servidor> <puerto>")
        return

    host = sys.argv[1]
    port = int(sys.argv[2])

    client = FTPClient(host, port)

    while True:
        try:
            command = input("ftp> ").strip()
            if not command:
                continue

            if command.startswith("login"):
                _, username, password = command.split()
                client.login(username, password)
            elif command == "list":
                client.list_files()

            elif command == "quit":
                client.quit()
                break
            else:
                print("Comando no reconocido. Comandos disponibles: login, list, download, upload, quit")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()

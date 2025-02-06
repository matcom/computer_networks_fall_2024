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

    def acct(self, account):
        return self.send_command(f'ACCT {account}')

    def cwd(self, path):
        return self.send_command(f'CWD {path}')

    def cdup(self):
        return self.send_command('CDUP')

    def smnt(self, path):
        return self.send_command(f'SMNT {path}')

    def rein(self):
        return self.send_command('REIN')

    def port(self, host_port):
        return self.send_command(f'PORT {host_port}')

    def pasv(self):
        return self.send_command('PASV')

    def type(self, type_code):
        return self.send_command(f'TYPE {type_code}')

    def stru(self, structure):
        return self.send_command(f'STRU {structure}')

    def mode(self, mode_code):
        return self.send_command(f'MODE {mode_code}')

    def retr(self, filename):
        return self.send_command(f'RETR {filename}')

    def stor(self, filename):
        return self.send_command(f'STOR {filename}')

    def stou(self):
        return self.send_command('STOU')

    def appe(self, filename):
        return self.send_command(f'APPE {filename}')

    def allo(self, size, record_size=None):
        if record_size:
            return self.send_command(f'ALLO {size} R {record_size}')
        return self.send_command(f'ALLO {size}')

    def rest(self, marker):
        return self.send_command(f'REST {marker}')

    def rnfr(self, old_path):
        return self.send_command(f'RNFR {old_path}')

    def rnto(self, new_path):
        return self.send_command(f'RNTO {new_path}')

    def abor(self):
        return self.send_command('ABOR')

    def dele(self, path):
        return self.send_command(f'DELE {path}')

    def rmd(self, path):
        return self.send_command(f'RMD {path}')

    def mkd(self, path):
        return self.send_command(f'MKD {path}')

    def pwd(self):
        return self.send_command('PWD')

    def nlst(self, path=None):
        if path:
            return self.send_command(f'NLST {path}')
        return self.send_command('NLST')

    def site(self, parameters):
        return self.send_command(f'SITE {parameters}')

    def syst(self):
        return self.send_command('SYST')

    def stat(self, path=None):
        if path:
            return self.send_command(f'STAT {path}')
        return self.send_command('STAT')

    def help(self, command=None):
        if command:
            return self.send_command(f'HELP {command}')
        return self.send_command('HELP')

    def noop(self):
        return self.send_command('NOOP')


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

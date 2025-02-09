import socket
import sys
import re


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

    def pasv(self):
        response = self.send_command('PASV')
        if "227" in response:  # Respuesta de modo pasivo
            # Extraer la dirección IP y el puerto de la respuesta
            ip_port = re.search(r'\((\d+,\d+,\d+,\d+,\d+,\d+)\)', response).group(1)
            ip_parts = list(map(int, ip_port.split(',')))
            ip = '.'.join(map(str, ip_parts[:4]))
            port = (ip_parts[4] << 8) + ip_parts[5]
            return ip, port
        else:
            raise Exception("Error al entrar en modo PASV.")

    def list_files(self):
        ip, port = self.pasv()
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.connect((ip, port))
        self.send_command('LIST')
        data = data_socket.recv(4096).decode('utf-8')
        data_socket.close()
        print(data)
        return data

    def retr(self, filename):
        ip, port = self.pasv()
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.connect((ip, port))
        self.send_command(f'RETR {filename}')
        with open(filename, 'wb') as file:
            while True:
                data = data_socket.recv(4096)
                if not data:
                    break
                file.write(data)
        data_socket.close()
        print(f"Archivo '{filename}' descargado correctamente.")

    def stor(self, filename):
        ip, port = self.pasv()
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.connect((ip, port))
        self.send_command(f'STOR {filename}')
        with open(filename, 'rb') as file:
            data_socket.sendfile(file)
        data_socket.close()
        print(f"Archivo '{filename}' subido correctamente.")

    def print_working_directory(self):
        response = self.send_command('PWD')
        if "257" in response:  # Respuesta exitosa de PWD
            print(response)
            return response
        else:
            raise Exception("Error al obtener el directorio actual.")

    def change_working_directory(self, directory):
        response = self.send_command(f'CWD {directory}')
        if "250" in response:  # Respuesta exitosa de CWD
            print(f"Directorio cambiado a '{directory}'.")
            return response
        else:
            raise Exception(f"Error al cambiar al directorio '{directory}'.")

    def quit(self):
        self.send_command('QUIT')
        self.control_socket.close()
        print("Conexión cerrada.")


def main():
    if len(sys.argv) < 8:
        print("Uso: python client.py -p PORT -h HOST -u USER -w PASS -c COMMAND -a ARG1 -b ARG2")
        return

    # Parsear argumentos
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
    elif command == "PWD":
        client.print_working_directory()
    elif command == "CWD":
        client.change_working_directory(arg1)
    else:
        print(f"Comando '{command}' no reconocido.")

    client.quit()


if __name__ == "__main__":
    main()
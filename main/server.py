import socket
import threading
import os
import re

class FTPServer:
    def __init__(self, host='', port=21):
        self.host = host
        self.port = port
        self.server_socket = None
        self.working_directory = os.getcwd()
        self.users = {'usuario': 'contraseña'}  # Diccionario de usuarios para autenticación

    def start(self):
        # Crear el socket del servidor
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Servidor FTP iniciado en {self.host}:{self.port}")

        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Conexión entrante de {client_address}")
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.start()

    def handle_client(self, client_socket):
        client_socket.sendall('220 Bienvenido al servidor FTP\r\n'.encode('utf-8'))
        authenticated = False
        username = ''
        current_directory = self.working_directory
        data_socket = None

        while True:
            data = client_socket.recv(1024).decode('utf-8').strip()
            if not data:
                break
            print(f"Comando recibido: {data}")
            command, _, params = data.partition(' ')
            command = command.upper()

            if command == 'USER':
                username = params
                client_socket.sendall('331 Nombre de usuario OK, necesita contraseña\r\n'.encode('utf-8'))

            elif command == 'PASS':
                if username in self.users and self.users[username] == params:
                    authenticated = True
                    client_socket.sendall('230 Usuario autenticado exitosamente\r\n'.encode('utf-8'))
                else:
                    client_socket.sendall('530 Error de autenticación\r\n'.encode('utf-8'))

            elif not authenticated:
                client_socket.sendall('530 Debe autenticarse primero\r\n'.encode('utf-8'))

            elif command == 'SYST':
                client_socket.sendall('215 UNIX Type: L8\r\n'.encode('utf-8'))

            elif command == 'PWD':
                relative_path = os.path.relpath(current_directory, self.working_directory)
                if relative_path == '.':
                    relative_path = '/'
                else:
                    relative_path = '/' + relative_path.replace(os.sep, '/')
                response = f'257 "{relative_path}"\r\n'
                client_socket.sendall(response.encode('utf-8'))

            elif command == 'CWD':
                new_dir = params
                if new_dir.startswith('/'):
                    target_directory = os.path.join(self.working_directory, new_dir.strip('/'))
                else:
                    target_directory = os.path.join(current_directory, new_dir)
                if os.path.isdir(target_directory):
                    current_directory = os.path.abspath(target_directory)
                    client_socket.sendall('250 Directorio cambiado correctamente\r\n'.encode('utf-8'))
                else:
                    client_socket.sendall('550 Directorio no encontrado\r\n'.encode('utf-8'))

            elif command == 'PASV':
                if data_socket:
                    data_socket.close()
                data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                data_socket.bind((self.host, 0))
                data_socket.listen(1)
                ip_address = self.get_ip_address()
                port_number = data_socket.getsockname()[1]
                p1 = port_number >> 8
                p2 = port_number & 0xFF
                ip_parts = ip_address.split('.')
                response = f'227 Entering Passive Mode ({",".join(ip_parts)},{p1},{p2})\r\n'
                client_socket.sendall(response.encode('utf-8'))

            elif command == 'LIST':
                if data_socket:
                    client_socket.sendall('150 Aquí viene la lista de directorios\r\n'.encode('utf-8'))
                    conn, _ = data_socket.accept()
                    files = os.listdir(current_directory)
                    listing = ''
                    for name in files:
                        path = os.path.join(current_directory, name)
                        if os.path.isdir(path):
                            listing += f"drwxr-xr-x 1 user group      0 Jan 1 00:00 {name}\r\n"
                        else:
                            size = os.path.getsize(path)
                            listing += f"-rw-r--r-- 1 user group {size:>6} Jan 1 00:00 {name}\r\n"
                    conn.sendall(listing.encode('utf-8'))
                    conn.close()
                    data_socket.close()
                    data_socket = None
                    client_socket.sendall('226 Listado enviado correctamente\r\n'.encode('utf-8'))
                else:
                    client_socket.sendall('425 Use PASV primero\r\n'.encode('utf-8'))

            elif command == 'RETR':
                if data_socket:
                    filepath = os.path.join(current_directory, params)
                    if os.path.isfile(filepath):
                        client_socket.sendall('150 Iniciando transferencia de datos\r\n'.encode('utf-8'))
                        conn, _ = data_socket.accept()
                        with open(filepath, 'rb') as f:
                            while True:
                                chunk = f.read(1024)
                                if not chunk:
                                    break
                                conn.sendall(chunk)
                        conn.close()
                        data_socket.close()
                        data_socket = None
                        client_socket.sendall('226 Transferencia completada\r\n'.encode('utf-8'))
                    else:
                        client_socket.sendall('550 Archivo no encontrado\r\n'.encode('utf-8'))
                else:
                    client_socket.sendall('425 Use PASV primero\r\n'.encode('utf-8'))

            elif command == 'STOR':
                if data_socket:
                    filepath = os.path.join(current_directory, params)
                    client_socket.sendall('150 Iniciando transferencia de datos\r\n'.encode('utf-8'))
                    conn, _ = data_socket.accept()
                    with open(filepath, 'wb') as f:
                        while True:
                            chunk = conn.recv(1024)
                            if not chunk:
                                break
                            f.write(chunk)
                    conn.close()
                    data_socket.close()
                    data_socket = None
                    client_socket.sendall('226 Transferencia completada\r\n'.encode('utf-8'))
                else:
                    client_socket.sendall('425 Use PASV primero\r\n'.encode('utf-8'))

            elif command == 'DELE':
                filepath = os.path.join(current_directory, params)
                if os.path.isfile(filepath):
                    os.remove(filepath)
                    client_socket.sendall('250 Archivo eliminado correctamente\r\n'.encode('utf-8'))
                else:
                    client_socket.sendall('550 Archivo no encontrado\r\n'.encode('utf-8'))

            elif command == 'MKD':
                dirpath = os.path.join(current_directory, params)
                try:
                    os.makedirs(dirpath)
                    response = f'257 "{params}" creado\r\n'
                    client_socket.sendall(response.encode('utf-8'))
                except OSError:
                    client_socket.sendall('550 No se pudo crear el directorio\r\n'.encode('utf-8'))

            elif command == 'RMD':
                dirpath = os.path.join(current_directory, params)
                try:
                    os.rmdir(dirpath)
                    client_socket.sendall('250 Directorio eliminado correctamente\r\n'.encode('utf-8'))
                except OSError:
                    client_socket.sendall('550 No se pudo eliminar el directorio\r\n'.encode('utf-8'))

            elif command == 'RNFR':
                filepath = os.path.join(current_directory, params)
                if os.path.exists(filepath):
                    client_socket.sendall('350 Archivo/directorio existe, listo para RNTO\r\n'.encode('utf-8'))
                    data = client_socket.recv(1024).decode('utf-8').strip()
                    cmd, _, new_name = data.partition(' ')
                    if cmd.upper() == 'RNTO':
                        new_filepath = os.path.join(current_directory, new_name)
                        os.rename(filepath, new_filepath)
                        client_socket.sendall('250 Renombrado correctamente\r\n'.encode('utf-8'))
                    else:
                        client_socket.sendall('503 Se esperaba RNTO\r\n'.encode('utf-8'))
                else:
                    client_socket.sendall('550 Archivo/directorio no encontrado\r\n'.encode('utf-8'))

            elif command == 'QUIT':
                client_socket.sendall('221 Adiós\r\n'.encode('utf-8'))
                break

            else:
                client_socket.sendall('502 Comando no implementado\r\n'.encode('utf-8'))

        client_socket.close()
        if data_socket:
            data_socket.close()
        print("Conexión cerrada")

    def get_ip_address(self):
        # Obtener la dirección IP local
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Conectar a un host remoto para obtener la IP local
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

def main():
    server = FTPServer()
    server.start()

if __name__ == '__main__':
    main()

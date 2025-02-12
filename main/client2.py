import socket
import sys
import re

class FTPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.control_socket.connect((self.host, self.port))
        self.receive_response()

    def receive_response(self):
        response = ''
        while True:
            data = self.control_socket.recv(4096).decode('utf-8')
            response += data
            if self.is_response_complete(response):
                break
            if not data:
                break
        print(response, end='')
        return response

    def is_response_complete(self, response):
        lines = response.split('\r\n')
        lines = [line for line in lines if line]
        if not lines:
            return False
        last_line = lines[-1]

        if re.match(r'^\d{3} ', last_line):
            return True
        else:
            return False

    def send_command(self, command):
        self.control_socket.sendall((command + '\r\n').encode('utf-8'))
        return self.receive_response()

    def login(self, username, password):
        user_response = self.send_command(f'USER {username}')
        pass_response = self.send_command(f'PASS {password}')
        return user_response, pass_response

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
        list_response = self.send_command('LIST')
        data = ''
        while True:
            chunk = data_socket.recv(4096).decode('utf-8')
            if not chunk:
                break
            data += chunk
        data_socket.close()
        print(data)
        return list_response, data

    def retr(self, filename):
        ip, port = self.pasv()
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.connect((ip, port))
        retr_response = self.send_command(f'RETR {filename}')
        with open(filename, 'wb') as file:
            while True:
                data = data_socket.recv(4096)
                if not data:
                    break
                file.write(data)
        data_socket.close()
        print(f"Archivo '{filename}' descargado correctamente.")
        return retr_response

    def print_working_directory(self):
        response = self.send_command('PWD')
        if "257" in response:
            print(response)
            return response
        else:
            raise Exception("Error al obtener el directorio actual.")

    def change_working_directory(self, directory):
        response = self.send_command(f'CWD {directory}')
        if "250" in response:
            print(f"Directorio cambiado a '{directory}'.")
            return response
        else:
            raise Exception(f"Error al cambiar al directorio '{directory}'.")

    def rename(self, from_name, to_name):
        rnfr_response = self.send_command(f'RNFR {from_name}')
        if "350" in rnfr_response:  # Respuesta exitosa de RNFR
            rnto_response = self.send_command(f'RNTO {to_name}')
            if "250" in rnto_response:  # Respuesta exitosa de RNTO
                print(f"Archivo renombrado de '{from_name}' a '{to_name}'.")
            else:
                raise Exception(f"Error al renombrar el archivo a '{to_name}'.")
        else:
            raise Exception(f"Error al renombrar el archivo desde '{from_name}'.")
        return rnfr_response, rnto_response

    def make_directory(self, directory):
        response = self.send_command(f'MKD {directory}')
        if "257" in response:
            print(f"Directorio '{directory}' creado correctamente.")
        else:
            raise Exception(f"Error al crear el directorio '{directory}'.")
        return response

    def delete_file(self, filename):
        response = self.send_command(f'DELE {filename}')
        if "250" in response:
            print(f"Archivo '{filename}' eliminado correctamente.")
        else:
            raise Exception(f"Error al eliminar el archivo '{filename}'.")
        return response

    def remove_directory(self, directory):
        response = self.send_command(f'RMD {directory}')
        if "250" in response:
            print(f"Directorio '{directory}' eliminado correctamente.")
        else:
            raise Exception(f"Error al eliminar el directorio '{directory}'.")
        return response

    def stor(self, local_filepath, remote_filename):
        ip, port = self.pasv()
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.connect((ip, port))
        stor_response = self.send_command(f'STOR {remote_filename}')
        with open(local_filepath, 'rb') as file:
            while True:
                data = file.read(4096)
                if not data:
                    break
                data_socket.sendall(data)
        data_socket.close()
        final_response = self.receive_response()
        if "226" in final_response or "250" in final_response:
            print(f"Archivo '{local_filepath}' subido como '{remote_filename}' correctamente.")
        else:
            raise Exception(f"Error al subir el archivo '{local_filepath}'.")
        return stor_response, final_response

    def quit(self):
        response = self.send_command('QUIT')
        self.control_socket.close()
        print("Conexión cerrada.")
        return response

def main():
    host = input("Ingrese el host: ")
    port = int(input("Ingrese el puerto: "))
    user = input("Ingrese el usuario: ")
    password = input("Ingrese la contraseña: ")

    client = FTPClient(host, port)
    client.login(user, password)

    while True:
        try:
            command_input = input("ftp> ").strip()
            if not command_input:
                continue
            command_parts = command_input.split()
            command = command_parts[0].upper()

            if command == "LIST":
                client.list_files()
            elif command == "DELE":
                if len(command_parts) < 2:
                    print("Uso: DELE <archivo>")
                    continue
                client.delete_file(command_parts[1])
            elif command == "STOR":
                if len(command_parts) < 3:
                    print("Uso: STOR <archivo_local> <nombre_remoto>")
                    continue
                client.stor(command_parts[1], command_parts[2])
            elif command == "RETR":
                if len(command_parts) < 2:
                    print("Uso: RETR <archivo>")
                    continue
                client.retr(command_parts[1])
            elif command == "PWD":
                client.print_working_directory()
            elif command == "CWD":
                if len(command_parts) < 2:
                    print("Uso: CWD <directorio>")
                    continue
                client.change_working_directory(command_parts[1])
            elif command == "RNFR":
                if len(command_parts) < 3:
                    print("Uso: RNFR <nombre_actual> <nuevo_nombre>")
                    continue
                client.rename(command_parts[1], command_parts[2])
            elif command == "MKD":
                if len(command_parts) < 2:
                    print("Uso: MKD <directorio>")
                    continue
                client.make_directory(command_parts[1])
            elif command == "RMD":
                if len(command_parts) < 2:
                    print("Uso: RMD <directorio>")
                    continue
                client.remove_directory(command_parts[1])
            elif command == "QUIT" or command == "EXIT":
                client.quit()
                break
            else:
                print(f"Comando '{command}' no reconocido.")
        except Exception as e:
            print(f"Error durante la ejecución del comando '{command}': {str(e)}")

if __name__ == "__main__":
    main()

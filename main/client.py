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

    def rename(self, from_name, to_name):
        response = self.send_command(f'RNFR {from_name}')
        if "350" in response:  # Respuesta exitosa de RNFR
            response = self.send_command(f'RNTO {to_name}')
            if "250" in response:  # Respuesta exitosa de RNTO
                print(f"Archivo renombrado de '{from_name}' a '{to_name}'.")
            else:
                raise Exception(f"Error al renombrar el archivo a '{to_name}'.")
        else:
            raise Exception(f"Error al renombrar el archivo desde '{from_name}'.")

    def stor(self, filename):
        try:
            ip, port = self.pasv()
            data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_socket.connect((ip, port))
            response = self.send_command(f'STOR {filename}')
            if "150" not in response:
                raise Exception(f"Error al iniciar la subida del archivo '{filename}': {response}")
            with open(filename, 'rb') as file:
                data_socket.sendfile(file)
            data_socket.close()
            response = self.receive_response()
            if "226" in response:
                print(f"Archivo '{filename}' subido correctamente.")
            else:
                raise Exception(f"Error al completar la subida del archivo '{filename}': {response}")
        except FileNotFoundError:
            raise Exception(f"Archivo '{filename}' no encontrado.")
        except PermissionError:
            raise Exception(f"Permiso denegado para leer el archivo '{filename}'.")
        except Exception as e:
            raise Exception(f"Error al subir el archivo '{filename}': {str(e)}")

    def delete(self, filename):
        try:
            response = self.send_command(f'DELE {filename}')
            if "250" in response:  # Respuesta exitosa de DELE
                print(f"Archivo '{filename}' eliminado correctamente.")
            else:
                raise Exception(f"Error al eliminar el archivo '{filename}': {response}")
        except FileNotFoundError:
            raise Exception(f"Archivo '{filename}' no encontrado.")
        except PermissionError:
            raise Exception(f"Permiso denegado para eliminar el archivo '{filename}'.")
        except Exception as e:
            raise Exception(f"Error al eliminar el archivo '{filename}': {str(e)}")

    def make_directory(self, directory):
        response = self.send_command(f'MKD {directory}')
        if "257" in response:  # Respuesta exitosa de MKD
            print(f"Directorio '{directory}' creado correctamente.")
        else:
            raise Exception(f"Error al crear el directorio '{directory}'.")

    def remove_directory(self, directory):
        response = self.send_command(f'RMD {directory}')
        if "250" in response:  # Respuesta exitosa de RMD
            print(f"Directorio '{directory}' eliminado correctamente.")
        else:
            raise Exception(f"Error al eliminar el directorio '{directory}'.")

    def quit(self):
        self.send_command('QUIT')
        self.control_socket.close()
        print("Conexión cerrada.")


def main():
    # Parsear argumentos
    args = {}
    for i in range(1, len(sys.argv), 2):
        args[sys.argv[i]] = sys.argv[i + 1]

    # Validar argumentos requeridos
    required_args = ['-p', '-h', '-u', '-w']
    for arg in required_args:
        if arg not in args:
            print(f"Falta el argumento requerido: {arg}")
            print("Uso: python client.py -p PORT -h HOST -u USER -w PASS -c COMMAND [-a ARG1] [-b ARG2]")
            return

    host = args['-h']
    port = int(args['-p'])
    user = args['-u']
    password = args['-w']
    command = args.get('-c', '')
    arg1 = args.get('-a', '')
    arg2 = args.get('-b', '')

    client = FTPClient(host, port)
    client.login(user, password)

    try:
        if command == "LIST":
            client.list_files()
        elif command == "RETR":
            if not arg1:
                print("Falta el argumento requerido: -a para el comando RETR")
                return
            client.retr(arg1)
        elif command == "STOR":
            if not arg1:
                print("Falta el argumento requerido: -a para el comando STOR")
                return
            client.stor(arg1)
        elif command == "PWD":
            client.print_working_directory()
        elif command == "CWD":
            if not arg1:
                print("Falta el argumento requerido: -a para el comando CWD")
                return
            client.change_working_directory(arg1)
        elif command == "RNFR":
            if not arg1 or not arg2:
                print("Faltan los argumentos requeridos: -a y -b para el comando RNFR")
                return
            client.rename(arg1, arg2)
        elif command == "DELE":
            if not arg1:
                print("Falta el argumento requerido: -a para el comando DELE")
                return
            client.delete(arg1)
        elif command == "MKD":
            if not arg1:
                print("Falta el argumento requerido: -a para el comando MKD")
                return
            client.make_directory(arg1)
        elif command == "RMD":
            if not arg1:
                print("Falta el argumento requerido: -a para el comando RMD")
                return
            client.remove_directory(arg1)
        elif command:
            print(f"Comando '{command}' no reconocido.")
        else:
            print("No se proporcionó ningún comando.")
    except Exception as e:
        print(f"Error durante la ejecución del comando '{command}': {str(e)}")

    client.quit()


if __name__ == "__main__":
    main()
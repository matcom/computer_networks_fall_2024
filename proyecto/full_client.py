import socket
import os
import re
from pathlib import Path

class FTPClient:
    def __init__(self, host='127.0.0.1', port=21):
        self.host = host
        self.port = port
        self.commands_help = {
            "USER": "Especifica el usuario",
            "PASS": "Especifica la contraseña",
            "PWD" : "Muestra el directorio actual",
            "CWD" : "Cambia el directorio de trabajo",
            "CDUP": "Cambia el directorio de trabajo al directorio padre",
            "LIST": "Lista archivos y directorios",
            "MKD" : "Crea un directorio",
            "RMD" : "Elimina un directorio",
            "DELE": "Elimina un archivo",
            "RNFR": "Especifica el archivo a renombrar",
            "RNTO": "Especifica el nuevo nombre",
            "QUIT": "Cierra la conexión",
            "HELP": "Muestra la ayuda",
            "SYST": "Muestra información del sistema",
            "NOOP": "No realiza ninguna operación",
            "ACCT": "Especifica la cuenta del usuario",
            "SMNT": "Monta una estructura de sistema de archivos",
            "REIN": "Reinicia la conexión",
            "PORT": "Especifica dirección y puerto para conexión",
            "PASV": "Entra en modo pasivo",
            "TYPE": "Establece el tipo de transferencia",
            "STRU": "Establece la estructura de archivo",
            "MODE": "Establece el modo de transferencia",
            "RETR": "Recupera un archivo",
            "STOR": "Almacena un archivo",
            "STOU": "Almacena un archivo con nombre único",
            "APPE": "Añade datos a un archivo",
            "ALLO": "Reserva espacio",
            "REST": "Reinicia transferencia desde punto",
            "ABOR": "Aborta operación en progreso",
            "SITE": "Comandos específicos del sitio",
            "STAT": "Retorna estado actual",
            "NLST": "Lista nombres de archivos"
        }
        self.downloads_folder = str(Path.cwd() / "Downloads")  # Carpeta local Downloads
        # Crear la carpeta si no existe
        os.makedirs(self.downloads_folder, exist_ok=True)
        print(f"Carpeta de descargas: {self.downloads_folder}")

    def send_command(self, sock, command, *args):
        full_command = f"{command} {' '.join(args)}".strip()
        sock.send(f"{full_command}\r\n".encode())
        
        response = ""
        while True:
            data = sock.recv(8192).decode()
            if not data:  # Si no hay más datos, salir del bucle
                break
            response += data
            # Verificar si la respuesta termina con un código de estado (por ejemplo, "226")
            if re.search(r"\d{3} .*\r\n", response):
                break
        
        return response
    
    def send_stor_command(self, sock, data_sock, command, *args):
        full_command = f"{command} {' '.join(args)}".strip()
        sock.send(f"{full_command}\r\n".encode())
        
        response = ""
        while True:
            data = sock.recv(8192).decode()
            if not data:  # Si no hay más datos, salir del bucle
                break
            if "150" in data:
                if self.send_file(data_sock, args[0]):
                    print("Archivo enviado exitosamente")
                else:
                    print("Error al enviar archivo")
            response += data
            
            # Verificar si la respuesta termina con un código de estado (por ejemplo, "226")
            if re.search(r"226 .*\r\n", response) or data.startswith("5"):
                break
        
        return response
    
    def send_command_multiresponse(self, sock, command, *args):
        full_command = f"{command} {' '.join(args)}".strip()
        sock.send(f"{full_command}\r\n".encode())
        
        response = ""
        while True:
            data = sock.recv(8192).decode()
            if not data:  # Si no hay más datos, salir del bucle
                break
            response += data
            # Verificar si la respuesta termina con un código de estado (por ejemplo, "226")
            if re.search(r"226 .*\r\n", response) or data.startswith("5"):
                break
        
        return response

    def send_file(self, sock, filename):
        """Envía un archivo al servidor"""
        try:
            print(filename)
            with open(filename, 'rb') as f:
                while True:
                    data = f.read()
                    print(data)
                    if not data:
                        break
                    sock.send(data)
            sock.send(b'EOF')
            return True
        except Exception as e:
            print(f"Error al enviar archivo: {e}")
            return False

    def receive_file(self, sock, filename):
        """Recibe un archivo del servidor en la carpeta Downloads local"""
        try:
            # Construir la ruta completa en la carpeta Downloads local
            download_path = os.path.join(self.downloads_folder, filename)
            with open(download_path, 'wb') as f:
                while True:
                    data = sock.recv(8192)
                    if not data:  # Detectar fin de transferencia
                        break
                    f.write(data)
            print(f"Archivo guardado en: {download_path}")
            return True
        except Exception as e:
            print(f"Error al recibir archivo: {e}")
            return False
        
    def enter_passive_mode(self, control_sock):
        """Entra en modo pasivo y devuelve el socket de datos"""
        response = self.send_command(control_sock, "PASV")
        print(response)

        # Extraer la dirección IP y el puerto de la respuesta
        match = re.search(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', response)
        if not match:
            print("No se pudo entrar en modo pasivo")
            return None

        # Construir la dirección IP y el puerto
        ip = ".".join(match.groups()[:4])
        port = (int(match.group(5)) << 8) + int(match.group(6))
        
        # Si la dirección IP es 0.0.0.0, usar la dirección IP del servidor
        if ip == "0.0.0.0":
            ip = self.host

        # Crear un nuevo socket para la conexión de datos
        data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_sock.connect((ip, port))

        return data_sock

    def start(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((self.host, self.port))
            print(client_socket.recv(8192).decode())

            while True:
                try:
                    command = input("FTP> ").strip().split()
                    if not command:
                        continue

                    cmd = command[0].upper()
                    args = command[1:] if len(command) > 1 else []

                    if cmd == "HELP":
                        if args:
                            cmd_help = args[0].upper()
                            if cmd_help in self.commands_help:
                                print(f"{cmd_help}: {self.commands_help[cmd_help]}")
                            else:
                                print(f"Comando '{cmd_help}' no reconocido")
                        else:
                            print("\nComandos disponibles:")
                            for cmd_name, desc in sorted(self.commands_help.items()):
                                print(f"{cmd_name}: {desc}")
                        continue

                    if cmd in self.commands_help:
                        # Manejo especial para comandos que requieren modo pasivo
                        if cmd in ["LIST", "RETR", "STOR", "APPE", "NLST"]:
                            # Enviar el comando PASV y obtener la respuesta
                            response = self.send_command(client_socket, "PASV")
                            print(response)

                            if not response.startswith("227"):
                                print("Error: No se pudo entrar en modo pasivo")
                                continue

                            # Extraer la dirección IP y el puerto de la respuesta
                            match = re.search(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', response)
                            if not match:
                                print("Error: No se pudo extraer la dirección IP y el puerto")
                                continue

                            # Construir la dirección IP y el puerto
                            ip = ".".join(match.groups()[:4])
                            port = (int(match.group(5)) << 8) + int(match.group(6))

                            # Crear un nuevo socket para la conexión de datos
                            data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            data_sock.connect((ip, port))

                            try:
                                if cmd == "LIST" or cmd == "NLST":
                                    path = args[0] if args else '.'
                                    response = self.send_command_multiresponse(client_socket, cmd, path)
                                    print(response)
                                    if "150" in response:
                                        data = data_sock.recv(8192).decode()
                                        print(data)
                                    data_sock.close()  # Cerrar el socket de datos

                                elif cmd in ["RETR", "STOR", "APPE"]:
                                    if len(args) < 1:
                                        print(f"Uso: {cmd} <filename>")
                                        continue

                                    filename = args[0]
                                    if cmd == "STOR":
                                        if os.path.exists(filename):
                                            response = self.send_stor_command(client_socket, data_sock, "STOR", filename)
                                            print(response)
                                        else:
                                            print("Archivo no encontrado")

                                    elif cmd == "RETR":
                                        response = self.send_command_multiresponse(client_socket, "RETR", filename)
                                        print(response)
                                        if "150" in response:
                                            if self.receive_file(data_sock, filename):
                                                print("Archivo recibido exitosamente")
                                            else:
                                                print("Error al recibir archivo")

                                    elif cmd == "APPE":
                                        if os.path.exists(filename):
                                            response = self.send_stor_command(client_socket, data_sock, "APPE", filename)
                                            print(response)
                                        else:
                                            print("Archivo no encontrado")
                            finally:
                                data_sock.close()  # Cerrar el socket de datos    
                        else:
                            # Comandos que no requieren modo pasivo
                            response = self.send_command(client_socket, cmd, *args)
                            print(response)
                            if cmd == "QUIT":
                                break
                    else:
                        print("Comando no reconocido")

                except Exception as e:
                    print(f"Error: {e}")

        except Exception as e:
            print(f"Error de conexión: {e}")
        finally:
            client_socket.close()
    
if __name__ == "__main__":
    client = FTPClient()
    client.start()
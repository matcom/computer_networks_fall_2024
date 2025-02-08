import socket
import ssl
import argparse
import re

commands = [
    "USER", "PASS", "ACCT", "CWD", "CDUP", "SMNT", "REIN", "QUIT", "PORT", "PASV", "TYPE", "STRU", "MODE", "RETR", 
    "STOR", "STOU", "APPE", "ALLO", "REST", "RNFR", "RNTO", "ABOR", "DELE", "RMD", "MKD", "PWD", "LIST", "NLST", 
    "SITE", "SYST", "STAT", "HELP", "NOOP"
]

def connect_to_server(server, port, use_tls=False):
    """
    Conecta al servidor FTP.
    Si use_tls es True, establece una conexión segura (TLS/SSL).
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server, port))

    if use_tls:
        # Enviar el comando AUTH TLS
        client_socket.sendall(b"AUTH TLS\r\n")
        response = client_socket.recv(1024).decode().strip()
        print(f"auth: {response}")
        
        if "234" in response:  # Código 234 indica que el servidor acepta TLS
            # Configura el contexto SSL
            context = ssl.create_default_context()
            tls_socket = context.wrap_socket(client_socket, server_hostname=server)
            return tls_socket
        else:
            print("Error: El servidor no acepta AUTH TLS.")
            client_socket.close()
            return None
    else:
        return client_socket

def send_command(client_socket, command):
    """
    Envía un comando al servidor FTP y devuelve la respuesta.
    """
    client_socket.sendall(command.encode() + b"\r\n")
    response = client_socket.recv(1024).decode().strip()
    return response

def parse_pasv_response(response):
    """
    Extrae la dirección IP y el puerto de la respuesta PASV.
    """
    match = re.search(r"(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)", response)
    if match:
        ip = ".".join(match.groups()[:4])
        port = int(match.groups()[4]) * 256 + int(match.groups()[5])
        return ip, port
    return None, None  # Si no se puede parsear la respuesta

def handle_data_transfer(command, pasv_response, server, client_socket, argument1, argument2=None):
    if "227" in pasv_response:  # Código 227: Entrando en modo pasivo
        ip, port = parse_pasv_response(pasv_response)
        if ip and port:
            # Establece la conexión de datos
            data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_socket.connect((ip, port))

            if command == "RETR":
                # Ejecuta el comando RETR
                retr_response = send_command(client_socket, f"RETR {argument1}")
                print(retr_response)

                if "150" in retr_response:  # Código 150: Preparándose para la transferencia
                    # Recibe los datos del archivo
                    with open(argument1, "wb") as f:
                        while True:
                            file_data = data_socket.recv(1024)
                            if not file_data:
                                break
                            f.write(file_data)

                    # Cierra la conexión de datos
                    data_socket.close()

                    # Recibe la confirmación de finalización
                    completion_response = client_socket.recv(1024).decode().strip()
                    print(completion_response)
                else:
                    print("Error en la transferencia del archivo.")

            elif command == "STOR":
                # Ejecuta el comando STOR
                stor_response = send_command(client_socket, f"STOR {argument2}")
                print(stor_response)

                if "150" in stor_response:  # Código 150: Preparándose para la transferencia
                    # Envía el archivo al servidor
                    with open(argument1, "rb") as f:
                        while True:
                            file_data = f.read(1024)
                            if not file_data:
                                break
                            data_socket.sendall(file_data)

                    # Cierra la conexión de datos
                    data_socket.close()

                    # Recibe la confirmación de finalización
                    completion_response = client_socket.recv(1024).decode().strip()
                    print(completion_response)
                else:
                    print("Error en la transferencia del archivo.")
        else:
            print("Error al procesar la respuesta PASV")
    else:
        print("Error al entrar en modo PASV")

def ftp_client(argvs):
    """
    Función principal del cliente FTP.
    """
    server = argvs.host
    port = argvs.port
    username = argvs.username
    password = argvs.password
    use_tls = argvs.use_tls  # Usar o no TLS

    try:
        # Conecta al servidor
        client_socket = connect_to_server(server, port, use_tls)
        if not client_socket:
            return

        # Recibe el mensaje de bienvenida del servidor
        welcome_message = client_socket.recv(1024).decode().strip()
        print(welcome_message)

        # Autenticación con USER y PASS
        user_response = send_command(client_socket, f"USER {username}")
        print(user_response)
        
        pass_response = send_command(client_socket, f"PASS {password}")
        print(pass_response)

        # Verifica si la autenticación fue exitosa
        if "230" in pass_response:  # Código 230: Usuario autenticado
            print("Autenticación exitosa. Puedes comenzar a enviar comandos.")
            while True:
                # Solicita un comando al usuario
                command = input("ftp> ").strip()
                if command.upper() == "QUIT":
                    send_command(client_socket, "QUIT")
                    print("Cerrando conexión...")
                    break

                # Manejo especial para comandos que requieren transferencia de datos
                if command.upper().startswith("RETR") or command.upper().startswith("STOR"):
                    pasv_response = send_command(client_socket, "PASV")
                    print(pasv_response)
                    args = command.split()
                    handle_data_transfer(args[0], pasv_response, server, client_socket, args[1], args[1] if len(args) > 1 else None)
                else:
                    # Ejecuta otros comandos
                    if command.upper() in commands:
                        response = send_command(client_socket, command)
                        print(response)
                    else:
                        print("Comando no soportado.")
        else:
            print("Error de autenticación. Verifica las credenciales.")

    except Exception as e:
        print(f"Error durante la ejecución: {e}")
    finally:
        # Cierra la conexión
        if client_socket:
            client_socket.close()

if __name__ == "__main__":
    # Configura el parser de argumentos
    parser = argparse.ArgumentParser(description="Cliente FTP en Python", add_help=False)
    parser.add_argument("-h", "--host", required=True, help="Dirección del servidor FTP")
    parser.add_argument("-p", "--port", type=int, default=21, help="Puerto del servidor FTP")
    parser.add_argument("-u", "--username", required=True, help="Nombre de usuario")
    parser.add_argument("-w", "--password", required=True, help="Contraseña")
    parser.add_argument("--use_tls", action="store_true", help="Usar TLS/SSL para la conexión")

    # Parsea los argumentos
    argvs = parser.parse_args()

    # Llama a la función principal del cliente FTP
    ftp_client(argvs)
import socket
import ssl
import argparse
import json
import re

def connect_to_server(server, port, use_tls=False):
    """
    Conecta al servidor FTP.
    Si use_tls es True, establece una conexión segura (TLS/SSL).
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server, port))

    if use_tls:
        # Configura el contexto SSL
        context = ssl.create_default_context()
        tls_socket = context.wrap_socket(client_socket, server_hostname=server)
        return tls_socket
    else:
        return client_socket

def send_command(client_socket, command):
    """
    Envía un comando al servidor FTP y devuelve la respuesta en formato JSON.
    """
    client_socket.sendall(command.encode())
    response = client_socket.recv(1024).decode().strip()
    status_code = response.split(" ")[0]  # Extrae el código de estado
    return json.dumps({"status": status_code, "message": response}, indent=4)

def parse_pasv_response(response, server_ip):
    """
    Extrae la dirección IP y el puerto de la respuesta PASV.
    Si la respuesta no es válida, usa la dirección IP del servidor.
    """
    match = re.search(r"(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)", response)
    if match:
        ip = ".".join(match.groups()[:4])
        port = int(match.groups()[4]) * 256 + int(match.groups()[5])
        return ip, port
    return server_ip, None  # Usa la dirección IP del servidor si la respuesta no es válida

def ftp_client(argvs):
    """
    Función principal del cliente FTP.
    """
    server = argvs.host
    port = argvs.port
    username = argvs.username
    password = argvs.password
    command = argvs.command
    argument1 = argvs.argument1
    argument2 = argvs.argument2
    use_tls = argvs.use_tls  # Nuevo argumento para usar o no TLS

    # Diccionario de delegados para los comandos FTP
    command_delegates = {
        "USER": lambda: f"USER {argument1}\r\n",
        "PASS": lambda: f"PASS {argument1}\r\n",
        "ACCT": lambda: f"ACCT {argument1}\r\n",
        "CWD": lambda: f"CWD {argument1}\r\n",
        "CDUP": lambda: f"CDUP\r\n",
        "SMNT": lambda: f"SMNT {argument1}\r\n",
        "REIN": lambda: f"REIN\r\n",
        "QUIT": lambda: f"QUIT\r\n",
        "PORT": lambda: f"PORT {argument1}\r\n",
        "PASV": lambda: f"PASV\r\n",
        "TYPE": lambda: f"TYPE {argument1}\r\n",
        "STRU": lambda: f"STRU {argument1}\r\n",
        "MODE": lambda: f"MODE {argument1}\r\n",
        "RETR": lambda: f"RETR {argument1}\r\n",
        "STOR": lambda: f"STOR {argument1}\r\n",
        "STOU": lambda: f"STOU\r\n",
        "APPE": lambda: f"APPE {argument1}\r\n",
        "ALLO": lambda: f"ALLO {argument1}\r\n",
        "REST": lambda: f"REST {argument1}\r\n",
        "RNFR": lambda: f"RNFR {argument1}\r\n",
        "RNTO": lambda: f"RNTO {argument2}\r\n",
        "ABOR": lambda: f"ABOR\r\n",
        "DELE": lambda: f"DELE {argument1}\r\n",
        "RMD": lambda: f"RMD {argument1}\r\n",
        "MKD": lambda: f"MKD {argument1}\r\n",
        "PWD": lambda: f"PWD\r\n",
        "LIST": lambda: f"LIST {argument1}\r\n",
        "NLST": lambda: f"NLST {argument1}\r\n",
        "SITE": lambda: f"SITE {argument1}\r\n",
        "SYST": lambda: f"SYST\r\n",
        "STAT": lambda: f"STAT {argument1}\r\n",
        "HELP": lambda: f"HELP {argument1}\r\n",
        "NOOP": lambda: f"NOOP\r\n",
    }

    try:
        # Conecta al servidor
        client_socket = connect_to_server(server, port, use_tls)

        # Recibe el mensaje de bienvenida del servidor
        welcome_message = client_socket.recv(1024).decode().strip()
        welcome_status = welcome_message.split(" ")[0]
        print(json.dumps({"status": welcome_status, "message": welcome_message}, indent=4))

        # Autenticación con USER y PASS
        user_response = send_command(client_socket, f"USER {username}\r\n")
        print(user_response)

        pass_response = send_command(client_socket, f"PASS {password}\r\n")
        print(pass_response)

        # Verifica si la autenticación fue exitosa
        if "230" in pass_response:  # Código 230: Usuario autenticado
            # Si el comando es RETR, envía PASV primero
            if command == "RETR" or command == "STOR":
                pasv_response = send_command(client_socket, "PASV\r\n")
                print(pasv_response)

                if "227" in pasv_response:  # Código 227: Entrando en modo pasivo
                    ip, port = parse_pasv_response(pasv_response, server)  # Pasa la dirección IP del servidor
                    if ip and port:
                        # Establece la conexión de datos
                        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        data_socket.connect((ip, port))

                        # Ejecuta el comando RETR
                        retr_response = send_command(client_socket, f"RETR {argument1}\r\n")
                        print(retr_response)

                        # Recibe los datos del archivo
                        file_data = data_socket.recv(1024)
                        while file_data:
                            print(file_data.decode(), end="")
                            file_data = data_socket.recv(1024)

                        # Cierra la conexión de datos
                        data_socket.close()

                        # Agrega verificación del mensaje 226
                        completion_response = client_socket.recv(1024).decode().strip()
                        print(json.dumps({"status": completion_response.split(" ")[0], "message": completion_response}, indent=4))
                    else:
                        print(json.dumps({"status": "500", "message": "Error al procesar la respuesta PASV"}, indent=4))
                else:
                    print(json.dumps({"status": "500", "message": "Error al entrar en modo PASV"}, indent=4))
            else:
                # Ejecuta otros comandos
                if command in command_delegates:
                    command_response = send_command(client_socket, command_delegates[command]())
                else:
                    command_response = json.dumps({"status": "500", "message": "Comando no soportado"}, indent=4)

                print(command_response)
        else:
            print(json.dumps({"status": "530", "message": "Error de autenticación. Verifica las credenciales."}, indent=4))

    except Exception as e:
        print(json.dumps({"status": "500", "message": f"Error durante la ejecución: {e}"}, indent=4))
    finally:
        # Cierra la conexión
        client_socket.close()

if __name__ == "__main__":
    # Configura el parser de argumentos
    parser = argparse.ArgumentParser(description="Cliente FTP en Python", add_help=False)
    parser.add_argument("-h", "--host", required=True, help="Dirección del servidor FTP")
    parser.add_argument("-p", "--port", type=int, default=21, help="Puerto del servidor FTP")
    parser.add_argument("-u", "--username", required=True, help="Nombre de usuario")
    parser.add_argument("-w", "--password", required=True, help="Contraseña")
    parser.add_argument("-c", "--command", required=False, help="Comando a ejecutar")
    parser.add_argument("-a", "--argument1", required=False, help="Primer argumento del comando")
    parser.add_argument("-b", "--argument2", required=False, help="Segundo argumento del comando")
    parser.add_argument("--use_tls", action="store_true", help="Usar TLS/SSL para la conexión")

    # Parsea los argumentos
    argvs = parser.parse_args()

    # Llama a la función principal del cliente FTP
    ftp_client(argvs)

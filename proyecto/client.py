import socket
import ssl
import argparse
import json

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

def ftp_client(argvs):
    """
    Función principal del cliente FTP.
    """
    server = argvs.host
    port = argvs.port
    username = argvs.username
    password = argvs.password
    command = argvs.command
    argument = argvs.argument
    use_tls = argvs.use_tls  # Nuevo argumento para usar o no TLS

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
            # Ejecuta el comando solicitado
            if command == "DELE":
                command_response = send_command(client_socket, f"DELE {argument}\r\n")
            elif command == "MKD":
                command_response = send_command(client_socket, f"MKD {argument}\r\n")
            elif command == "RMD":
                command_response = send_command(client_socket, f"RMD {argument}\r\n")
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
    parser = argparse.ArgumentParser(description="Cliente FTP en Python")
    parser.add_argument("-H", "--host", required=True, help="Dirección del servidor FTP")
    parser.add_argument("-P", "--port", type=int, default=21, help="Puerto del servidor FTP")
    parser.add_argument("-u", "--username", required=True, help="Nombre de usuario")
    parser.add_argument("-w", "--password", required=True, help="Contraseña")
    parser.add_argument("-c", "--command", required=True, help="Comando a ejecutar (DELE, MKD, RMD)")
    parser.add_argument("-a", "--argument", required=True, help="Argumento del comando")
    parser.add_argument("--use_tls", action="store_true", help="Usar TLS/SSL para la conexión")

    # Parsea los argumentos
    argvs = parser.parse_args()

    # Llama a la función principal del cliente FTP
    ftp_client(argvs)

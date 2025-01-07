import socket
import ssl

# Configuración del cliente FTP
FTP_SERVER = '127.0.0.1'
FTP_PORT = 21
BUFFER_SIZE = 1024
TIMEOUT = 30  # Ajustar tiempo de espera a 30 segundos


def connect_to_server(server, port):
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(TIMEOUT)
    client_socket.connect((server, port))
    print(client_socket.recv(BUFFER_SIZE).decode())

    client_socket.send("AUTH TLS\r\n".encode())
    response = client_socket.recv(BUFFER_SIZE).decode()
    print(response)

    tls_socket = context.wrap_socket(client_socket, server_hostname=server)
    tls_socket.settimeout(TIMEOUT)

    try:
        tls_socket.do_handshake()
    except ssl.SSLError as e:
        print(f"Error durante el handshake TLS: {e}")
        client_socket.close()
        return None

    # Establecer protección privada para la conexión de datos
    send_command(tls_socket, "PBSZ 0")
    send_command(tls_socket, "PROT P")

    return tls_socket


def send_command(client_socket, command):
    client_socket.send((command + "\r\n").encode())
    try:
        response = client_socket.recv(BUFFER_SIZE).decode()
        print(response)
        return response
    except socket.timeout:
        print("Tiempo de espera agotado para la respuesta del servidor.")
        return None

# Cliente interactivo FTP
def ftp_client():
    client_socket = connect_to_server(FTP_SERVER, FTP_PORT)
    if not client_socket:
        print("No se pudo establecer una conexión segura.")
        return

    try:
        user = input("User: ")
        user_response = send_command(client_socket, f"USER {user}")

        if user_response and "331" in user_response:
            password = input("Password: ")
            send_command(client_socket, f"PASS {password}")

        while True:
            command = input("ftp> ")
            if not command:
                continue

            command_name = command.split()[0].upper()

            if command_name == 'QUIT':
                send_command(client_socket, command)
                break

            elif command_name in ['USER', 'PASS', 'CWD', 'TYPE', 'STRU', 'MODE', 'APPE', 'DELE', 'RMD', 'MKD', 'PORT',
                                  'RNFR', 'RNTO']:
                send_command(client_socket, command)

            elif command_name in ['CDUP', 'PWD', 'PASV', 'SYST', 'HELP', 'NOOP', 'REIN']:
                send_command(client_socket, command)

            else:
                print("Comando no implementado o no reconocido.")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        client_socket.close()
        print("Conexión cerrada.")


if __name__ == "__main__":
    ftp_client()

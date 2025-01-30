import socket
import ssl
import sys

# Configuración del cliente FTP
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

def list_files(tls_socket):
    response = send_command(tls_socket, 'PASV')
    start = response.find('(') + 1
    end = response.find(')')
    pasv_data = response[start:end].split(',')
    ip = '.'.join(pasv_data[:4])
    port = (int(pasv_data[4]) << 8) + int(pasv_data[5])

    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.connect((ip, port))
    send_command(tls_socket, 'LIST')

    data = b""
    while True:
        chunk = data_socket.recv(BUFFER_SIZE)
        if not chunk:
            break
        data += chunk

    data_socket.close()
    print(data.decode())

def stor_file(tls_socket, local_file, remote_file):
    send_command(tls_socket, 'TYPE I')
    response = send_command(tls_socket, 'PASV')
    start = response.find('(') + 1
    end = response.find(')')
    pasv_data = response[start:end].split(',')
    ip = '.'.join(pasv_data[:4])
    port = (int(pasv_data[4]) << 8) + int(pasv_data[5])

    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.connect((ip, port))
    send_command(tls_socket, f'STOR {remote_file}')

    with open(local_file, 'rb') as file:
        while True:
            data = file.read(BUFFER_SIZE)
            if not data:
                break
            data_socket.send(data)

    data_socket.close()
    print(tls_socket.recv(BUFFER_SIZE).decode())

def retr_file(tls_socket, remote_file, local_file):
    send_command(tls_socket, f'TYPE I')
    response = send_command(tls_socket, 'PASV')
    start = response.find('(') + 1
    end = response.find(')')
    pasv_data = response[start:end].split(',')
    ip = '.'.join(pasv_data[:4])
    port = (int(pasv_data[4]) << 8) + int(pasv_data[5])

    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.connect((ip, port))
    send_command(tls_socket, f'RETR {remote_file}')

    with open(local_file, 'wb') as file:
        while True:
            data = data_socket.recv(BUFFER_SIZE)
            if not data:
                break
            file.write(data)

    data_socket.close()
    print(tls_socket.recv(BUFFER_SIZE).decode())

def ftp_client(args):
    # Inicializar variables para argumentos
    server = None
    port = None
    user = None
    password = None
    command = None
    arg1 = None
    arg2 = None

    # Procesar argumentos de sys.argv
    i = 1  # iniciar en 1 para saltar el nombre del script
    while i < len(args):
        if args[i] == '-h':
            server = args[i + 1]
            i += 2
        elif args[i] == '-p' and port is None:
            port = int(args[i + 1])
            i += 2
        elif args[i] == '-u':
            user = args[i + 1]
            i += 2
        elif args[i] == '-p' and password is None:
            password = args[i + 1]
            i += 2
        elif args[i] == '-c':
            command = args[i + 1]
            i += 2
        elif args[i] == '-a':
            arg1 = args[i + 1]
            i += 2
        elif args[i] == '-b':
            arg2 = args[i + 1]
            i += 2
        else:
            i += 1

    client_socket = connect_to_server(server, port)
    if not client_socket:
        print("No se pudo establecer una conexión segura.")
        return

    try:
        user_response = send_command(client_socket, f"USER {user}")

        if user_response and "331" in user_response:
            send_command(client_socket, f"PASS {password}")

        if command:
            command_name = command.upper()

            if command_name == 'QUIT':
                send_command(client_socket, command)
            elif command_name == 'STOR':
                stor_file(client_socket, arg1, arg2)
            elif command_name == 'RETR':
                retr_file(client_socket, arg1, arg2)
            elif command_name == 'LIST':
                list_files(client_socket)
            elif command_name in ['USER', 'PASS', 'CWD', 'TYPE', 'STRU', 'MODE', 'APPE', 'DELE', 'RMD', 'MKD', 'PORT',
                                  'RNFR', 'RNTO']:
                full_command = f"{command} {arg1}" if arg1 else command
                send_command(client_socket, full_command)
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
    ftp_client(sys.argv)

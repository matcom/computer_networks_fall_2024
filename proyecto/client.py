import socket
import ssl
import sys

BUFFER_SIZE = 1024
TIMEOUT = 30

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

    # Extraer la dirección IP y el puerto del modo pasivo
    start = response.find('(') + 1
    end = response.find(')')
    pasv_data = response[start:end].split(',')
    ip = '.'.join(pasv_data[:4])
    port = (int(pasv_data[4]) << 8) + int(pasv_data[5])

    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.connect((ip, port))

    send_command(tls_socket, 'LIST')

    # Leer la lista de archivos
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
    # Extraer servidor y puerto de los argumentos
    server = args[args.index('-h') + 1]
    port = int(args[args.index('-p') + 1])

    client_socket = connect_to_server(server, port)
    if not client_socket:
        print("No se pudo establecer una conexión segura.")
        return

    try:
        user = args[args.index('-u') + 1]
        password = args[args.index('-w') + 1]

        user_response = send_command(client_socket, f"USER {user}")

        if user_response and "331" in user_response:
            send_command(client_socket, f"PASS {password}")

        if '-c' in args:
            command = args[args.index('-c') + 1].upper()
            if command == 'QUIT':
                send_command(client_socket, 'QUIT')
            elif command == 'PWD':
                send_command(client_socket, 'PWD')
            elif command == 'CWD':
                directory = args[args.index('-a') + 1]
                send_command(client_socket, f'CWD {directory}')
            elif command == 'RETR':
                remote_file = args[args.index('-a') + 1]
                local_file = args[args.index('-b') + 1]
                retr_file(client_socket, remote_file, local_file)
            elif command == 'STOR':
                local_file = args[args.index('-a') + 1]
                remote_file = args[args.index('-b') + 1]
                stor_file(client_socket, local_file, remote_file)
            elif command == 'LIST':
                list_files(client_socket)
            elif command == 'DELE':
                file_to_delete = args[args.index('-a') + 1]
                send_command(client_socket, f'DELE {file_to_delete}')
            elif command == 'MKD':
                directory_to_create = args[args.index('-a') + 1]
                send_command(client_socket, f'MKD {directory_to_create}')
            elif command == 'RMD':
                directory_to_remove = args[args.index('-a') + 1]
                send_command(client_socket, f'RMD {directory_to_remove}')
            elif command == 'RNFR':
                old_name = args[args.index('-a') + 1]
                new_name = args[args.index('-b') + 1]
                send_command(client_socket, f'RNFR {old_name}')
                send_command(client_socket, f'RNTO {new_name}')
            else:
                print("Comando no implementado o no reconocido.")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        client_socket.close()
        print("Conexión cerrada.")

if __name__ == "__main__":
    argvs = sys.argv[1:]
    ftp_client(argvs)
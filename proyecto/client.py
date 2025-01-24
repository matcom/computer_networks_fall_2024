import socket
import ssl

FTP_SERVER = '127.0.0.1'
FTP_PORT = 21
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
            
            elif command_name == 'STOR':
                local_file = command.split()[1]
                remote_file = command.split()[2]
                stor_file(client_socket, local_file, remote_file)

            elif command_name == 'RETR':
                remote_file = command.split()[1]
                local_file = command.split()[2]
                retr_file(client_socket, remote_file, local_file)

            elif command_name == 'LIST':
                list_files(client_socket)

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
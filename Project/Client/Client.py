import Utils
from socket import *

server_name = 'localhost'
server_port = 12000
timeout = 35
buffer_size = 1024

def connect_server():
    client_socket = socket(AF_INET, SOCK_STREAM)
    client_socket.settimeout(timeout)
    client_socket.connect((server_name,server_port))


def send_command(client_socket, command):
    client_socket.send((command + "\r\n").encode())
    try:
        response = client_socket.recv(buffer_size).decode()
        print(response)
        return response
    except socket.timeout:
        print("Tiempo de espera agotado para la respuesta del servidor.")
        return None

def list_files(tls_socket):
    response = send_command(tls_socket, 'PASV')
    start = response.find('(') + 1
    end = response.find(')')
    pasv_info = response[start:end].split()
    ip = '.'.join(pasv_info[:4])
    port = (int(pasv_info[4]) << 8) + int(pasv_info[5])
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.connect((ip, port))
    send_command(data_socket, 'LIST')

    files = ''
    while True:
        chunk = data_socket.recv(buffer_size).decode()
        if not chunk:
            break
        files += chunk
    
    data_socket.close()
    print(tls_socket.recv(buffer_size).decode())

def stor_file(tls_socket, file_name, file_path):
    response = send_command(tls_socket, 'PASV')
    start = response.find('(') + 1
    end = response.find(')')
    pasv_info = response[start:end].split()
    ip = '.'.join(pasv_info[:4])
    port = (int(pasv_info[4]) << 8) + int(pasv_info[5])
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.connect((ip, port))
    send_command(data_socket, 'STOR ' + file_name)

    with open(file_path, 'rb') as file:
        file_content = file.read()
        data_socket.sendall(file_content)
    
    data_socket.close()
    print(tls_socket.recv(buffer_size).decode())

def retr_file(tls_socket, file_name, destiny_path):
    response = send_command(tls_socket, 'PASV')
    start = response.find('(') + 1
    end = response.find(')')
    pasv_info = response[start:end].split()
    ip = '.'.join(pasv_info[:4])
    port = (int(pasv_info[4]) << 8) + int(pasv_info[5])
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.connect((ip, port))
    send_command(data_socket, 'RETR ' + file_name)

    with open(destiny_path, 'wb') as destiny:
        while True:
            data = socket.recv(4096)
            if not data:
                break
            destiny.write(data)
    
    data_socket.close()
    print(tls_socket.recv(buffer_size).decode())

def ftp_client():
    client_socket = connect_server()
    if not client_socket:
        print("No se pudo establecer una conexión segura.")
        return
    
    while True:
        command = input(">>")
        if not command:
            continue

        command_name = command.split()[0].upper()
        if command_name in Utils.commands:
            if  command_name == 'QUIT':
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

            else: send_command(client_socket, command_name)
        
        else:
            lev = 1000000000000
            sug = ""
            for command in Utils.commands:
                newlev = Utils.levenshtein_distance(command, command_name)
                if newlev < sug:
                    sug = command
            print(f"Command {command_name} not found, prove with {sug}")

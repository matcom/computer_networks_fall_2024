import socket
import os
import hashlib

# Configuración del servidor
HOST = '127.0.0.1'  # Dirección IP del servidor
PORT = 21         # Puerto FTP
BUFFER_SIZE = 1024
FILE_ROOT = './files'
# KEY = 'key.pem'
# CERT = 'cert.pem'

def hash_password(password: str, salt: bytes = None) -> tuple:
    if salt is None:
        salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt, key

def verify_password(stored_password: tuple, provided_password: str) -> bool:
    salt, key = stored_password
    new_key = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return new_key == key

# Usuarios y contraseñas válidos con contraseñas hasheadas
users = {
    "user": hash_password("pass")
}

state: dict = {}

def handle_user_command(client_socket: socket, args): 
    user = args[0] if args else ""
    if user in users:
        client_socket.send(b'331 Please specify the password.')
    else:
        client_socket.send(b'530 Login incorrect.')
    return user

def handle_pass_command(client_socket: socket, args, user):
    password = args[0] if args else ""
    if user in users and verify_password(users[user], password):
        client_socket.send(b'230 Login successful.')
        return True
    else:
        client_socket.send(b'530 Login incorrect.')   
        return False
    
def handle_list_command(client_socket: socket, user: str):
    files = os.listdir(f'{FILE_ROOT}/{state[user]}')
    files = ' '.join(files)
    client_socket.send(f'150 Here comes the directory listing. {files} '.encode())
    
def handle_pwd_command(client_socket: socket, user: str):
    path = '/' if state[user] == '' else state[user]    
    client_socket.send(f'257 {path} is the current directory.'.encode())
    
def handle_cwd_command(client_socket: socket, args, user: str):
    dirname = args[0] if args else ""
    try:
        path = f'{FILE_ROOT}/{dirname}'
        if not os.path.isdir(path):
            raise FileNotFoundError
        
        if(dirname == '/' or dirname == '.'):
            state[user] = ''
        else:
            state[user] = f'{dirname}/'
        
        client_socket.send('250 Directory successfully changed.'.encode())
    except FileNotFoundError:
        client_socket.send('550 Requested action not taken. Directory does not exist.'.encode())
        
def handle_pasv_command(client_socket: socket, user: str):    
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.bind((HOST, 0))
    data_socket.listen(1)
    
    port = data_socket.getsockname()[1]
    port_bytes = [str(port >> 8), str(port & 0xff)]
    
    # print(port)
    
    client_socket.send(f'227 Entering Passive Mode ({",".join(HOST.split("."))},{",".join(port_bytes)})'.encode())
    # print(f'227 Entering Passive Mode ({",".join(HOST.split("."))},{",".join(port_bytes)}')
    
    data_client_socket, host = data_socket.accept()
    
    return data_client_socket
    
def handle_retr_command(client_socket: socket, data_socket: socket, args, user: str):
    filename = args[0] if args else ""
    try:
        pointer = open(f'{FILE_ROOT}/{state[user]}{filename}', 'rb')
        
        client_socket.send('150 Opening data connection.'.encode())
        
        data_socket.sendfile(pointer)
        pointer.close()
        
        data_socket.close()
        
        client_socket.send('226 Transfer complete.'.encode())
    except FileNotFoundError:
        client_socket.send('550 Requested action not taken. File unavailable.'.encode())

def handle_stor_command(client_socket: socket, data_socket: socket, args, user: str):
    filename = args[0] if args else ""
    try:
        pointer = open(f'{FILE_ROOT}/{state[user]}{filename}', 'wb')
        
        client_socket.send('150 Opening data connection.'.encode())
        
        pointer.write(data_socket.recv(BUFFER_SIZE))
        pointer.close()
        
        data_socket.close()
        
        client_socket.send('226 Transfer complete.'.encode())
    except Exception:
        client_socket.send('550 Requested action not taken. File unavailable.'.encode())
        
def handle_rnfr_command(client_socket: socket, args, user: str):
    filename = args[0] if args else ""
    try:
        os.stat(f'{FILE_ROOT}/{state[user]}{filename}')
        
        client_socket.send('350 Ready to RNTO.'.encode())
        return filename
    except Exception:
        client_socket.send('550 Requested action not taken. File unavailable.'.encode())
        return None
        
def handle_rnto_command(client_socket: socket, old_filename: str, args, user: str):
    new_filename = args[0] if args else ""
    try:
        os.rename(f'{FILE_ROOT}/{state[user]}{old_filename}', f'{FILE_ROOT}/{state[user]}{new_filename}')
        
        client_socket.send('250 Rename successful.'.encode())
    except FileNotFoundError:
        client_socket.send('550 Requested action not taken. File unavailable.'.encode())

def handle_dele_command(client_socket: socket, args, user: str):
    filename = args[0] if args else ""
    try:
        os.remove(f'{FILE_ROOT}/{state[user]}{filename}')
        client_socket.send('250 File deleted successfully.'.encode())
    except FileNotFoundError:
        client_socket.send('550 Requested action not taken. File unavailable.'.encode())

def handle_mkd_command(client_socket: socket, args, user: str):
    dirname = args[0] if args else ""
    try:
        os.mkdir(f'{FILE_ROOT}/{state[user]}{dirname}')
        client_socket.send('257 Directory created successfully.'.encode())
    except FileExistsError:
        client_socket.send('550 Requested action not taken. Directory already exists.'.encode())
        
def handle_rmd_command(client_socket: socket, args, user: str):
    dirname = args[0] if args else ""
    try:
        os.rmdir(f'{FILE_ROOT}/{state[user]}{dirname}')
        client_socket.send('250 Directory removed successfully.'.encode())
    except FileNotFoundError:
        client_socket.send('550 Requested action not taken. Directory does not exist.'.encode())

def handle_quit_command(client_socket: socket):
    client_socket.send(b'221 Goodbye.')

def handle_client(client_socket: socket):
    client_socket.sendall(b'220 Welcome to the FTP server.')
    
    while True:
        data = client_socket.recv(BUFFER_SIZE).decode().strip()
        data = {
            'command': data.split(' ')[0],
            'args': data.split(' ')[1:]
        }
        
        if not data:
            client_socket.close()
            return
            
        command = data['command']
        args = data['args']
        
        if command == "USER":
            user = handle_user_command(client_socket, args)
            if state.get(user) is None:
                state[user] = ''
        elif command == "PASS":
            authenticated = handle_pass_command(client_socket, args, user)
        elif command == "LIST" and authenticated:
            handle_list_command(client_socket, user)
        elif command == "PWD" and authenticated:
            handle_pwd_command(client_socket, user)
        elif command == "CWD" and authenticated:
            handle_cwd_command(client_socket, args, user)
        elif command == "PASV":
            data_socket = handle_pasv_command(client_socket, user)
        elif command == "RETR" and authenticated:
            handle_retr_command(client_socket, data_socket, args, user)
        elif command == "STOR" and authenticated:
            handle_stor_command(client_socket, data_socket, args, user)
        elif command == "RNFR" and authenticated:
            filename = handle_rnfr_command(client_socket, args, user)
        elif command == "RNTO" and authenticated and filename:
            handle_rnto_command(client_socket, filename, args, user)
        elif command == "DELE" and authenticated:
            handle_dele_command(client_socket, args, user)
        elif command == "MKD" and authenticated:
            handle_mkd_command(client_socket, args, user)
        elif command == "RMD" and authenticated:
            handle_rmd_command(client_socket, args, user)
        elif command == "QUIT":
            handle_quit_command(client_socket)
            break
        else:
            client_socket.send(b'500 Unknown command.')
    
    client_socket.close()

def main():
    # Crear un socket TCP/IP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
    
    print(f"FTP Server listening on {HOST}:{PORT}")

    while True:
        client_socket, host = server_socket.accept()
        print(f"Connection from {host}")
        handle_client(client_socket)
        client_socket.close()

if __name__ == '__main__':
    main()
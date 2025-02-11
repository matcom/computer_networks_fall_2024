import socket
import os
import ssl
import hashlib

from utils import from_json, to_json, log

# Configuración del servidor
HOST = '127.0.0.1'  # Dirección IP del servidor
PORT = 21         # Puerto FTP
BUFFER_SIZE = 1024
FILE_ROOT = '.'
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
        client_socket.send(to_json({"status_code" : "331", "message": "User name okay, need password."}))
    else:
        client_socket.send(to_json({"status_code" : "530", "message": "Login Failed."}))
    return user

def handle_pass_command(client_socket: socket, args, user):
    password = args[0] if args else ""
    if user in users and verify_password(users[user], password):
        client_socket.send(to_json({"status_code" : "230", "message": "User logged in, proceed."}))
        return True
    else:
        client_socket.send(to_json({"status_code" : "530", "message": "Login Failed."}))   
        return False
    
def handle_list_command(client_socket: socket, user: str):
    files = os.listdir(f'{FILE_ROOT}/{state[user]}')
    client_socket.send(to_json({"status_code" : "150", "message": "Here comes the directory listing.", "data": files}))
    
def handle_pwd_command(client_socket: socket, user: str):
    client_socket.send(to_json({"status_code" : "257", "message": "Directory created.", "data": '/' if state[user] == '' else f'{state[user]}'}))
    
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
        
        client_socket.send(to_json({"status_code" : "250", "message": "Directory changed."}))
    except FileNotFoundError:
        client_socket.send(to_json({"status_code" : "550", "message": "Requested action not taken. Directory does not exist."}))
    
def handle_retr_command(client_socket: socket, args, user: str):
    filename = args[0] if args else ""
    try:
        pointer = open(f'{FILE_ROOT}/{state[user]}{filename}', 'rb')
        
        client_socket.send(to_json({"status_code" : "150", "message": "Opening data connection."}))
        
        client_socket.sendfile(pointer)
        pointer.close()
        
        client_socket.send(to_json({"status_code" : "226", "message": "Transfer complete."}))
    except FileNotFoundError:
        client_socket.send(to_json({"status_code" : "550", "message": "Requested action not taken. File unavailable."}))

def handle_stor_command(client_socket: socket, args, user: str):
    filename = args[0] if args else ""
    try:
        client_socket.send(to_json({"status_code" : "150", "message": "Opening data connection."}))
        
        pointer = open(f'{FILE_ROOT}/{state[user]}{filename}', 'wb')
        pointer.write(client_socket.recv(BUFFER_SIZE))
        pointer.close()
        
        client_socket.send(to_json({"status_code" : "226", "message": "Transfer complete."}))
    except FileNotFoundError:
        client_socket.send(to_json({"status_code" : "550", "message": "Requested action not taken. File unavailable."}))
        
def handle_rnfr_command(client_socket: socket, args, user: str):
    filename = args[0] if args else ""
    try:
        pointer = open(f'{FILE_ROOT}/{state[user]}{filename}', 'rb')
        pointer.close()
        
        client_socket.send(to_json({"status_code" : "350", "message": "Ready for RNTO."}))
        return filename
    except FileNotFoundError:
        client_socket.send(to_json({"status_code" : "550", "message": "Requested action not taken. File unavailable."}))
        return None
        
def handle_rnto_command(client_socket: socket, old_filename: str, args, user: str):
    new_filename = args[0] if args else ""
    try:
        os.rename(f'{FILE_ROOT}/{state[user]}{old_filename}', f'{FILE_ROOT}/{state[user]}{new_filename}')
        
        client_socket.send(to_json({"status_code" : "250", "message": "Rename successful."}))
    except FileNotFoundError:
        client_socket.send(to_json({"status_code" : "550", "message": "Requested action not taken. File unavailable."}))

def handle_dele_command(client_socket: socket, args, user: str):
    filename = args[0] if args else ""
    try:
        os.remove(f'{FILE_ROOT}/{state[user]}{filename}')
        client_socket.send(to_json({"status_code" : "250", "message": "Requested file action okay, completed."}))
    except FileNotFoundError:
        client_socket.send(to_json({"status_code" : "550", "message": "Requested action not taken. File unavailable."}))

def handle_mkd_command(client_socket: socket, args, user: str):
    dirname = args[0] if args else ""
    try:
        os.mkdir(f'{FILE_ROOT}/{state[user]}{dirname}')
        client_socket.send(to_json({"status_code" : "257", "message": "Directory created."}))
    except FileExistsError:
        client_socket.send(to_json({"status_code" : "550", "message": "Requested action not taken. Directory already exists."}))
        
def handle_rmd_command(client_socket: socket, args, user: str):
    dirname = args[0] if args else ""
    try:
        os.rmdir(f'{FILE_ROOT}/{state[user]}{dirname}')
        client_socket.send(to_json({"status_code" : "250", "message": "Directory removed."}))
    except FileNotFoundError:
        client_socket.send(to_json({"status_code" : "550", "message": "Requested action not taken. Directory does not exist."}))

def handle_quit_command(client_socket: socket):
    client_socket.send(to_json({"status_code" : "221", "message": "Goodbye."}))

def handle_client(client_socket: socket):
    client_socket.sendall(to_json({"status_code" : "220", "message": "Welcome to the FTP server"}))
    
    while True:
        data = from_json(client_socket.recv(BUFFER_SIZE))
        
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
        elif command == "RETR" and authenticated:
            handle_retr_command(client_socket, args, user)
        elif command == "STOR" and authenticated:
            handle_stor_command(client_socket, args, user)
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
            client_socket.send(to_json({"status_code" : "502", "message": "Command not recognized."}))
    
    client_socket.close()

def main():
    # Crear un socket TCP/IP
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)
    
    print(f"Servidor FTP escuchando en {HOST}:{PORT}...")

    while True:
        client_socket, host = server_socket.accept()
        print(f"Nueva conexión desde {host}")
        handle_client(client_socket)
        client_socket.close()

if __name__ == '__main__':
    main()
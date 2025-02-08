import socket
import os

from utils import from_json, to_json, log

# Configuración del servidor
HOST = '127.0.0.1'  # Dirección IP del servidor
PORT = 21         # Puerto FTP
BUFFER_SIZE = 1024
USERS = {"user": "pass"}  # Usuario y contraseña válidos

def handle_user_command(client_socket: socket, args): 
    user = args[0] if args else ""
    if user in USERS:
        client_socket.send(to_json({"status_code" : "331", "message": "User name okay, need password."}))
    else:
        client_socket.send(to_json({"status_code" : "530", "message": "Login Failed."}))
    return user

def handle_pass_command(client_socket: socket, args, user):
    password = args[0] if args else ""
    if user in USERS and USERS[user] == password:
        client_socket.send(to_json({"status_code" : "230", "message": "User logged in, proceed."}))
        return True
    else:
        client_socket.send(to_json({"status_code" : "530", "message": "Login Failed."}))   
        return False
    
def handle_list_command(client_socket: socket):
    files = os.listdir('files')
    client_socket.send(to_json({"status_code" : "150", "message": "Here comes the directory listing.", "data": files}))
    
def handle_retr_command(client_socket: socket, args):
    filename = args[0] if args else ""
    try:
        client_socket.send(to_json({"status_code" : "150", "message": "Opening data connection."}))
        
        pointer = open(f'files/{filename}', 'rb')
        client_socket.sendfile(pointer)
        pointer.close()
        
        client_socket.send(to_json({"status_code" : "226", "message": "Transfer complete."}))
    except FileNotFoundError:
        client_socket.send(to_json({"status_code" : "550", "message": "Requested action not taken. File unavailable."}))

def handle_stor_command(client_socket: socket, args):
    filename = args[0] if args else ""
    try:
        client_socket.send(to_json({"status_code" : "150", "message": "Opening data connection."}))
        
        pointer = open(f'files/{filename}', 'wb')
        pointer.write(client_socket.recv(BUFFER_SIZE))
        pointer.close()
        
        client_socket.send(to_json({"status_code" : "226", "message": "Transfer complete."}))
    except FileNotFoundError:
        client_socket.send(to_json({"status_code" : "550", "message": "Requested action not taken. File unavailable."}))
        
def handle_rnfr_command(client_socket: socket, args):
    filename = args[0] if args else ""
    try:
        pointer = open(f'files/{filename}', 'rb')
        pointer.close()
        
        client_socket.send(to_json({"status_code" : "350", "message": "Ready for RNTO."}))
        return filename
    except FileNotFoundError:
        client_socket.send(to_json({"status_code" : "550", "message": "Requested action not taken. File unavailable."}))
        return None
        
def handle_rnto_command(client_socket: socket, old_filename: str, args):
    new_filename = args[0] if args else ""
    try:
        os.rename(f'files/{old_filename}', f'files/{new_filename}')
        
        client_socket.send(to_json({"status_code" : "250", "message": "Rename successful."}))
    except FileNotFoundError:
        client_socket.send(to_json({"status_code" : "550", "message": "Requested action not taken. File unavailable."}))

def handle_dele_command(client_socket: socket, args):
    filename = args[0] if args else ""
    try:
        os.remove(f'files/{filename}')
        client_socket.send(to_json({"status_code" : "250", "message": "Requested file action okay, completed."}))
    except FileNotFoundError:
        client_socket.send(to_json({"status_code" : "550", "message": "Requested action not taken. File unavailable."}))
        
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
        
        print(command)
        
        if command == "USER":
            user = handle_user_command(client_socket, args)
        elif command == "PASS":
            authenticated = handle_pass_command(client_socket, args, user)
        elif command == "LIST" and authenticated:
            handle_list_command(client_socket)
        elif command == "RETR" and authenticated:
            handle_retr_command(client_socket, args)
        elif command == "STOR" and authenticated:
            handle_stor_command(client_socket, args)
        elif command == "RNFR" and authenticated:
            filename = handle_rnfr_command(client_socket, args)
        elif command == "RNTO" and authenticated and filename:
            handle_rnto_command(client_socket, filename, args)
        elif command == "DELE" and authenticated:
            handle_dele_command(client_socket, args)
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
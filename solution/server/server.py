import socket
import os

from utils import from_json, to_json, log

# Configuración del servidor
HOST = '127.0.0.1'  # Dirección IP del servidor
PORT = 21         # Puerto FTP (por defecto es 21, pero usamos 2121 para evitar conflictos)
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
            files = os.listdir('.')
            client_socket.send(to_json({"status_code" : "150", "message": "Here comes the directory listing.", "data": files}))
        elif command == "QUIT":
            client_socket.send(to_json({"status_code" : "221", "message": "Goodbye."}))
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
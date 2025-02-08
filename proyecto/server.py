import socket
import os
import threading

# Configuración del servidor
HOST = '0.0.0.0'  # Escucha en todas las interfaces
PORT = 21         # Puerto FTP estándar
FTP_ROOT = os.getcwd()  # Directorio raíz del servidor FTP

# Diccionario para almacenar la información de los usuarios (simulado)
USERS = {
    'joel': 'joel'
}

# Función para manejar la conexión con un cliente
def handle_client(client_socket, client_address):
    print(f"Conexión establecida con {client_address}")
    current_dir = FTP_ROOT
    authenticated = False
    pasv_mode = False
    pasv_socket = None
    username = None

    # Envía el mensaje de bienvenida
    client_socket.send(b"220 Welcome to Python FTP Server\r\n")

    while True:
        try:
            # Recibe el comando del cliente
            command = client_socket.recv(1024).decode().strip()
            if not command:
                break

            print(f"Comando recibido: {command}")

            # Procesa el comando
            if command.startswith("USER"):
                username = command.split()[1]
                client_socket.send(b"331 User name okay, need password\r\n")
            elif command.startswith("PASS"):
                if username in USERS and USERS[username] == command.split()[1]:
                    authenticated = True
                    client_socket.send(b"230 User logged in, proceed\r\n")
                else:
                    client_socket.send(b"530 Not logged in\r\n")
            elif command.startswith("QUIT"):
                client_socket.send(b"221 Goodbye\r\n")
                break
            elif command.startswith("PWD"):
                client_socket.send(f"257 \"{current_dir}\"\r\n".encode())
            elif command.startswith("CWD"):
                new_dir = command.split()[1]
                new_path = os.path.join(current_dir, new_dir)
                if os.path.isdir(new_path):
                    current_dir = new_path
                    client_socket.send(f"250 Directory changed to {current_dir}\r\n".encode())
                else:
                    client_socket.send(b"550 Failed to change directory\r\n")
            elif command.startswith("PASV"):
                if pasv_socket:
                    pasv_socket.close()
                pasv_socket, pasv_port = start_pasv_mode()
                client_socket.send(f"227 Entering Passive Mode (127,0,0,1,{pasv_port // 256},{pasv_port % 256})\r\n".encode())
                pasv_mode = True
            elif command.startswith("LIST"):
                if pasv_mode and pasv_socket:
                    data_socket = pasv_socket.accept()[0]
                    pasv_mode = False
                else:
                    client_socket.send(b"425 Use PASV first.\r\n")
                    continue
                try:
                    files = os.listdir(current_dir)
                    client_socket.send(b"150 Here comes the directory listing\r\n")
                    listing = "\r\n".join(files) + "\r\n"
                    data_socket.send(listing.encode())
                    data_socket.close()
                    client_socket.send(b"226 Directory send OK\r\n")
                except Exception as e:
                    client_socket.send(b"550 Failed to list directory\r\n")
            elif command.startswith("RETR"):
                if pasv_mode and pasv_socket:
                    data_socket = pasv_socket.accept()[0]
                    pasv_mode = False
                else:
                    client_socket.send(b"425 Use PASV first.\r\n")
                    continue
                filename = command.split()[1]
                filepath = os.path.join(current_dir, filename)
                if os.path.isfile(filepath):
                    client_socket.send(b"150 Opening data connection\r\n")
                    with open(filepath, 'rb') as f:
                        data_socket.sendfile(f)
                    data_socket.close()
                    client_socket.send(b"226 Transfer complete\r\n")
                else:
                    client_socket.send(b"550 File not found\r\n")
            elif command.startswith("STOR"):
                if pasv_mode and pasv_socket:
                    data_socket = pasv_socket.accept()[0]
                    pasv_mode = False
                else:
                    client_socket.send(b"425 Use PASV first.\r\n")
                    continue
                filename = command.split()[1]
                filepath = os.path.join(current_dir, filename)
                client_socket.send(b"150 Ok to send data\r\n")
                with open(filepath, 'wb') as f:
                    while True:
                        data = data_socket.recv(1024)
                        if not data:
                            break
                        f.write(data)
                data_socket.close()
                client_socket.send(b"226 Transfer complete\r\n")
            else:
                client_socket.send(b"500 Command not recognized\r\n")
        except Exception as e:
            print(f"Error: {e}")
            break

    print(f"Conexión cerrada con {client_address}")
    if pasv_socket:
        pasv_socket.close()
    client_socket.close()

# Función para iniciar el modo PASV
def start_pasv_mode():
    pasv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pasv_socket.bind((HOST, 0))
    pasv_socket.listen(1)
    pasv_port = pasv_socket.getsockname()[1]
    return pasv_socket, pasv_port

# Función principal del servidor
def start_ftp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Servidor FTP escuchando en {HOST}:{PORT}")

    while True:
        client_socket, client_address = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()

if __name__ == "__main__":
    start_ftp_server()

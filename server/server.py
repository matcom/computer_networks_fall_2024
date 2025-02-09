import socket
import threading
import os
import time
import platform
import random
import struct
import string

BUFFER_SIZE = 1024
# Límite de intentos fallidos y tiempo de bloqueo
MAX_FAILED_ATTEMPTS = 3
BLOCK_TIME = 300  # Tiempo de bloqueo en segundos (5 minutos)
INACTIVITY_TIMEOUT = 180  # 3 minuto de inactividad

# Diccionario de intentos fallidos por IP: {'ip_address': {'attempts': int, 'block_time': float}}
failed_attempts = {}

HOST = "0.0.0.0"  # Escuchar en todas las interfaces
PORT = 21         # Puerto FTP por defecto

USERS = {
    "user": "pass",
    "user1": "pass1",
    "user2": "pass2",
    "user3": "pass3",
    "user4": "pass4",
    "user5": "pass5"
}

def check_failed_attempts(client_ip):
    current_time = time.time()
    if client_ip in failed_attempts:
        attempts = failed_attempts[client_ip]
        # Si la IP ha sido bloqueada y no ha pasado el tiempo de bloqueo
        if attempts['block_time'] > current_time:
            return True  # IP bloqueada
        # Si el tiempo de bloqueo ha pasado, resetear los intentos fallidos
        elif attempts['block_time'] <= current_time:
            failed_attempts[client_ip] = {'attempts': 0, 'block_time': 0}
    return False

def increment_failed_attempts(client_ip):
    current_time = time.time()
    if client_ip in failed_attempts:
        failed_attempts[client_ip]['attempts'] += 1
    else:
        failed_attempts[client_ip] = {'attempts': 1, 'block_time': 0}
    
    if failed_attempts[client_ip]['attempts'] >= MAX_FAILED_ATTEMPTS:
        # Bloqueamos la IP por un tiempo determinado (por ejemplo, 5 minutos)
        failed_attempts[client_ip]['block_time'] = current_time + BLOCK_TIME
        return True  # La IP ha sido bloqueada

    return False

def generate_unique_filename(directory, original_filename):
    # Generar un nombre único basado en el nombre del archivo original y un sufijo aleatorio
    name, ext = os.path.splitext(original_filename)
    while True:
        unique_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        unique_name = f"{name}_{unique_suffix}{ext}"
        if not os.path.exists(os.path.join(directory, unique_name)):
            return unique_name


#-------------------------------------------------------------------------------------------------------------------------


def cmd_USER(arg, client_socket, client_ip):
    if not arg:
        client_socket.send(b"501 Syntax error in parameters or arguments.\r\n")
    elif arg == "anonymous":
        client_socket.send(b"230 User logged in, proceed.\r\n")
    elif arg in USERS:
        client_socket.send(b"331 User name okay, need password.\r\n")
        return arg  # Devuelve el nombre de usuario para su posterior autenticación
    else:
        client_socket.send(b"530 User not found.\r\n")
        if increment_failed_attempts(client_ip):
            client_socket.send(b"421 Too many failed login attempts. Try again later.\r\n")
            return None
    return None

def cmd_PASS(arg, client_socket, authenticated, username, current_dir, client_ip):
    if username is None:
        client_socket.send(b"503 Bad sequence of commands.\r\n")
    elif not arg:
        client_socket.send(b"501 Syntax error in parameters or arguments.\r\n")
    elif authenticated:
        client_socket.send(b"202 User already logged in.\r\n")
    elif username in USERS and USERS[username] == arg:
        user_dir = os.path.join(current_dir, "server\\root", username)
        os.makedirs(user_dir, exist_ok=True)
        client_socket.send(b"230 Login successful.\r\n")
        return user_dir, True
    else:
        client_socket.send(b"530 Login incorrect.\r\n")
        if increment_failed_attempts(client_ip):
            client_socket.send(b"421 Too many failed login attempts. Try again later.\r\n")
            return None, False
    return current_dir, False





#-------------------------------------------------------------------------------------------------------------------------


def handle_command(command, client_socket, current_dir, username, authenticated, client_ip, Type, Mode, rename_from_path, DATA_SOCKET):
    parts = command.strip().split(" ", 1)
    cmd = parts[0].upper()
    arg = parts[1] if len(parts) > 1 else None

    if cmd == "USER":
        username = cmd_USER(arg, client_socket, client_ip)
    elif cmd == "PASS":
        current_dir, authenticated = cmd_PASS(arg, client_socket, authenticated, username, current_dir, client_ip)
    elif cmd == "ACCT":
        cmd_ACCT(arg, client_socket, authenticated, username)
    elif cmd == "SMNT":
        current_dir = cmd_SMNT(arg, client_socket, authenticated, current_dir)
    elif cmd == "REIN":
        username, authenticated, current_dir = cmd_REIN(client_socket, current_dir)
    elif cmd == "QUIT":
        client_socket.send(b"221 Goodbye.\r\n")
        return None, None, None  # Indica que el cliente debe terminar
    elif cmd == "PWD":
        cmd_PWD(client_socket, current_dir, authenticated)
    elif cmd == "CWD":
        current_dir = cmd_CWD(arg, client_socket, current_dir, authenticated)
    elif cmd == "CDUP":
        current_dir = cmd_CDUP(client_socket, current_dir, root_dir, authenticated)
    elif cmd == "MKD":
        cmd_MKD(arg, client_socket, current_dir, authenticated)
    elif cmd == "RMD":
        cmd_RMD(arg, client_socket, current_dir, authenticated)
    elif cmd == "DELE":
        current_dir = cmd_DELE(arg, client_socket, authenticated, current_dir)
    elif cmd == "TYPE":
        newtype = cmd_TYPE(arg, client_socket)
        if newtype is not None:
            Type = newtype
    elif cmd == "MODE":
        newmode = cmd_MODE(arg, client_socket)
        if newmode is not None:
            Mode = newmode
    elif cmd == "SYST":
        cmd_SYST(client_socket)
    elif cmd == "STAT":
        cmd_STAT(arg, client_socket, current_dir)
    elif cmd == "HELP":
        cmd_HELP(arg, client_socket)
    elif cmd == "RNFR":
        rename_from_path = cmd_RNFR(arg, client_socket, current_dir)
    elif cmd == "RNTO":
        cmd_RNTO(arg, client_socket, rename_from_path, current_dir)
        rename_from_path = None
    elif cmd == "NOOP":
        cmd_NOOP(client_socket)
    elif cmd == "PASV":
        DATA_SOCKET = cmd_PASV(client_socket)
    elif cmd == "RETR":
        cmd_RETR(client_socket, DATA_SOCKET, arg, Type, Mode, current_dir)
        DATA_SOCKET = None
    elif cmd == "STOR":
        cmd_STOR(client_socket, DATA_SOCKET, arg, Type, Mode, current_dir)
        DATA_SOCKET = None
    elif cmd == "APPE":
        cmd_APPE(client_socket, DATA_SOCKET, arg, Type, Mode, current_dir)
        DATA_SOCKET = None
    elif cmd == "STOU":
        cmd_STOU(client_socket, DATA_SOCKET, arg, Type, Mode, current_dir)
        DATA_SOCKET = None
    elif cmd == "LIST":
        cmd_LIST(client_socket, DATA_SOCKET, current_dir)
        DATA_SOCKET = None
    elif cmd == "NLST":
        cmd_NLST(client_socket, DATA_SOCKET, current_dir)
        DATA_SOCKET = None
    elif cmd == "ABOR":
        cmd_ABOR(client_socket, DATA_SOCKET)
        DATA_SOCKET = None
    elif cmd == "PORT":
        DATA_SOCKET = cmd_PORT(client_socket, arg, current_dir, DATA_SOCKET)
    else:
        client_socket.send(b"502 Command not implemented.\r\n")

    return username, authenticated, current_dir, Type, Mode, rename_from_path, DATA_SOCKET

def handle_client(client_socket, address):
    client_ip = address[0]  # Obtener la IP del cliente
    if check_failed_attempts(client_ip):
        client_socket.send(b"421 Too many failed login attempts. Try again later.\r\n")
        client_socket.close()
        return

    print(f"Conexión establecida desde {address}")
    client_socket.send(b"220 FTP Server Ready\r\n")
    
    last_activity_time = time.time()  # Registro de la última actividad
    current_dir = os.getcwd()
    username = None
    authenticated = False
    Type = 'A'
    Mode = 'S'
    rename_from_path = None
    DATA_SOCKET = None
    
    while True:
        try:
            data = client_socket.recv(BUFFER_SIZE).decode()
            if not data:
                break

            # Verifica si ha pasado mucho tiempo desde la última actividad
            current_time = time.time()
            if current_time - last_activity_time > INACTIVITY_TIMEOUT:
                client_socket.send(b"421 Service timeout.\r\n")
                break

            print(f"Comando recibido de {address}: {data.strip()}")
            username, authenticated, current_dir, Type, Mode, rename_from_path, DATA_SOCKET = handle_command(data, client_socket, current_dir, username, authenticated, address, Type, Mode, rename_from_path, DATA_SOCKET)

            # Actualizamos el tiempo de actividad
            last_activity_time = current_time

            if username is None and authenticated is None and current_dir is None:
                break  # Sale del bucle cuando el cliente cierra sesión con QUIT
        except ConnectionResetError:
            break
    
    print(f"Conexión cerrada con {address}")
    client_socket.close()

def start_ftp_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Servidor FTP escuchando en {HOST}:{PORT}")

    while True:
        client_socket, address = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket, address))
        client_thread.start()

if __name__ == "__main__":
    start_ftp_server()

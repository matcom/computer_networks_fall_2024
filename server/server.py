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

def cmd_ACCT(arg, client_socket, authenticated, username):
    if authenticated:
        client_socket.send(b"202 No hay necesidad de esta informacion adicional.\r\n")
    elif username is None:
        client_socket.send(b"503 Bad sequence of commands.\r\n")
    elif not arg:
        client_socket.send(b"501 Syntax error in parameters or arguments.\r\n")
    else:
        client_socket.send(b"230 User logged in, proceed.\r\n")  # En este caso, ACCT no es obligatorio

def cmd_SMNT(arg, client_socket, authenticated, current_dir):
    if not authenticated:
        client_socket.send(b"530 Not logged in.\r\n")
    elif arg is None or not arg.strip():
        client_socket.send(b"501 Syntax error in parameters or arguments.\r\n")
    elif not os.path.isdir(arg):
        client_socket.send(b"550 Failed to mount directory structure.\r\n")
    else:
        try:
            os.chdir(arg)  # Cambia la estructura de trabajo
            client_socket.send(b"250 Directory structure mounted successfully.\r\n")
            return os.getcwd()  # Devuelve la nueva ruta actual
        except Exception:
            client_socket.send(b"550 Failed to mount directory structure.\r\n")

    return current_dir  # Si no se cambia, devuelve el directorio actual

def cmd_REIN(client_socket, current_dir):
    """Restablece la conexión del usuario sin cerrar la sesión."""
    client_socket.send(b"220 Service ready for new user.\r\n")
    return None, False, os.getcwd()  # Restablece el usuario y autenticación, y vuelve a la raíz del servidor

def cmd_PWD(client_socket, current_dir, authenticated):
    if not authenticated:
        client_socket.send(b"530 Not logged in.\r\n")  # Usuario no autenticado
    else:
        try:
            client_socket.send(f'257 "{current_dir}" is the current directory.\r\n'.encode())
        except Exception:
            client_socket.send(b"550 Failed to retrieve current directory.\r\n")  # Error inesperado

def cmd_CWD(arg, client_socket, current_dir, authenticated):
    if not authenticated:
        client_socket.send(b"530 Not logged in.\r\n")  # Usuario no autenticado
        return current_dir
    if not arg:
        client_socket.send(b"501 Syntax error in parameters or arguments.\r\n")  # Falta argumento
        return current_dir
    new_path = os.path.join(current_dir, arg)
    if os.path.isdir(new_path):
        current_dir = new_path
        client_socket.send(b"250 Directory successfully changed.\r\n")
    else:
        client_socket.send(b"550 Failed to change directory.\r\n")  # Directorio inválido
    return current_dir

def cmd_CDUP(client_socket, current_dir, root_dir, authenticated):
    if not authenticated:
        client_socket.send(b"530 Not logged in.\r\n")
        return current_dir

    # Intentar moverse al directorio padre
    new_dir = os.path.dirname(current_dir)

    # Verificar que no se salga de la raíz del usuario
    if os.path.commonpath([new_dir, root_dir]) != root_dir:
        client_socket.send(b"550 Access denied.\r\n")
        return current_dir

    client_socket.send(b"250 Directory successfully changed.\r\n")
    return new_dir

def cmd_MKD(arg, client_socket, current_dir, authenticated):
    if not authenticated:
        client_socket.send(b"530 Not logged in.\r\n")
        return

    if not arg:
        client_socket.send(b"501 Syntax error in parameters or arguments.\r\n")
        return

    new_dir = os.path.join(current_dir, arg)

    if os.path.exists(new_dir):
        client_socket.send(b"550 Directory already exists.\r\n")
        return

    try:
        os.makedirs(new_dir)
        client_socket.send(f'257 "{arg}" directory created successfully.\r\n'.encode())
    except Exception:
        client_socket.send(b"550 Failed to create directory.\r\n")

def cmd_RMD(arg, client_socket, current_dir, authenticated):
    if not authenticated:
        client_socket.send(b"530 Not logged in.\r\n")
        return

    if not arg:
        client_socket.send(b"501 Syntax error in parameters or arguments.\r\n")
        return

    target_dir = os.path.join(current_dir, arg)

    if not os.path.exists(target_dir):
        client_socket.send(b"550 Directory not found.\r\n")
        return

    if not os.path.isdir(target_dir):
        client_socket.send(b"550 Not a directory.\r\n")
        return

    if os.listdir(target_dir):  # Si el directorio no está vacío
        client_socket.send(b"550 Directory not empty.\r\n")
        return

    try:
        os.rmdir(target_dir)
        client_socket.send(b"250 Directory deleted successfully.\r\n")
    except Exception:
        client_socket.send(b"550 Failed to remove directory.\r\n")

def cmd_DELE(arg, client_socket, authenticated, current_dir):
    """Comando DELE: Elimina un archivo del servidor."""
    if not authenticated:
        client_socket.send(b"530 Not logged in.\r\n")
        return current_dir

    if not arg:
        client_socket.send(b"501 Syntax error in parameters or arguments.\r\n")
        return current_dir

    # Obtener la ruta completa del archivo
    file_path = os.path.join(current_dir, arg)

    # Comprobar si el archivo existe
    if os.path.exists(file_path) and os.path.isfile(file_path):
        try:
            os.remove(file_path)  # Eliminar el archivo
            client_socket.send(f"250 Deleted {arg}.\r\n".encode())
        except Exception as e:
            client_socket.send(f"550 Failed to delete {arg}: {str(e)}.\r\n".encode())
    else:
        client_socket.send(f"550 {arg}: No such file.\r\n".encode())
    
    return current_dir

def cmd_TYPE(arg, client_socket):
    """Maneja el comando TYPE, que establece el tipo de transferencia de datos (ASCII o Binario)."""
    if not arg:
        client_socket.send(b"501 Syntax error in parameters or arguments.\r\n")
        return None
    if arg.upper() == 'A':
        client_socket.send(b"200 Type set to ASCII.\r\n")
        # Aquí podrías agregar la lógica para manejar la transferencia de archivos en modo ASCII.
        return 'A'
    elif arg.upper() == 'I':
        client_socket.send(b"200 Type set to Binary.\r\n")
        # Aquí podrías agregar la lógica para manejar la transferencia de archivos en modo binario.
        return 'I'
    else:
        client_socket.send(b"501 Syntax error in parameters or arguments.\r\n")

def cmd_MODE(arg, client_socket):
    """Maneja el comando MODE, que establece el modo de transferencia de datos."""
    if not arg:
        client_socket.send(b"501 Syntax error in parameters or arguments.\r\n")
        return
    
    if arg.upper() == 'S':
        client_socket.send(b"200 Mode set to Stream.\r\n")
        # Aquí podrías agregar lógica adicional para manejar el modo Stream si fuera necesario.
        return 'S'
    elif arg.upper() == 'B':
        client_socket.send(b"200 Mode set to Block.\r\n")
        # Aquí podrías agregar lógica para el modo Block si fuera necesario.
        return 'B'
    else:
        client_socket.send(b"501 Syntax error in parameters or arguments.\r\n")

def cmd_STRU(arg, client_socket):
    """Maneja el comando STRU, que establece la estructura del archivo a transferir."""
    if not arg:
        client_socket.send(b"501 Syntax error in parameters or arguments.\r\n")
        return

    arg = arg.upper()

    if arg == "F":
        client_socket.send(b"200 Structure set to File (F).\r\n")
    elif arg == "R":
        client_socket.send(b"504 Record structure not implemented.\r\n")
    elif arg == "P":
        client_socket.send(b"504 Page structure not implemented.\r\n")
    else:
        client_socket.send(b"501 Syntax error in parameters or arguments.\r\n")

def cmd_SYST(client_socket):
    """Maneja el comando SYST, que devuelve información sobre el sistema operativo del servidor."""
    system_name = platform.system()
    if system_name == "Windows":
        response = "215 Windows Type: L8\r\n"
    elif system_name == "Linux":
        response = "215 UNIX Type: L8\r\n"
    else:
        response = f"215 {system_name} Type: L8\r\n"

    client_socket.send(response.encode())

def cmd_STAT(arg, client_socket, current_dir):
    if not arg:
        # Si no se recibe argumento, se devuelve información del sistema
        system_info = "FTP Server: Windows Type: L8\r\n"
        client_socket.send(f"211- {system_info}".encode())
        client_socket.send(b"211 End of status.\r\n")
    else:
        # Si se recibe un argumento, se devuelve información sobre el archivo o directorio
        target_path = os.path.join(current_dir, arg)
        
        if not os.path.exists(target_path):
            client_socket.send(b"550 File or directory not found.\r\n")
            return
        
        # Si es un archivo
        if os.path.isfile(target_path):
            file_info = os.stat(target_path)
            last_modified = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(file_info.st_mtime))
            file_size = file_info.st_size
            response = f"213 {last_modified} {file_size} {target_path}\r\n"
            client_socket.send(response.encode())
        # Si es un directorio
        elif os.path.isdir(target_path):
            response = f"213 Directory: {target_path} exists.\r\n"
            client_socket.send(response.encode())
        else:
            client_socket.send(b"550 Not a valid file or directory.\r\n")


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

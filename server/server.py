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

def cmd_HELP(arg, client_socket):
    # Descripciones de los comandos según el RFC 959
    commands = {
        "USER": "USER <username> - Identifies the user to the server.",
        "PASS": "PASS <password> - Authenticates the user.",
        "ACCT": "ACCT <account> - Provides additional information to the server.",
        "CWD": "CWD <directory> - Changes the current working directory on the server.",
        "CDUP": "CDUP - Changes to the parent directory.",
        "SMNT": "SMNT <pathname> - Mounts a file system on the server.",
        "QUIT": "QUIT - Closes the connection with the server.",
        "REIN": "REIN - Reinitializes the connection without closing it.",
        "PORT": "PORT <address> - Specifies the IP address and port for data transfer.",
        "PASV": "PASV - Enables passive mode for data transfer.",
        "TYPE": "TYPE <type> - Sets the data transfer mode (ASCII or binary).",
        "STRU": "STRU <structure> - Specifies the file structure (F for file, R for record).",
        "MODE": "MODE <mode> - Sets the transfer mode (Stream, Block, or Compressed).",
        "RETR": "RETR <file> - Retrieves a file from the server.",
        "STOR": "STOR <file> - Stores a file on the server.",
        "APPE": "APPE <file> - Appends data to a file on the server.",
        "LIST": "LIST [path] - Lists files and directories.",
        "NLST": "NLST [path] - Lists only file names.",
        "STAT": "STAT [path] - Displays the status of the server or a file/directory.",
        "HELP": "HELP [command] - Provides help for FTP commands. If no command is given, lists available commands.",
        "NOOP": "NOOP - Performs a no-operation (no action).",
        "MDTM": "MDTM <file> - Displays the last modification time of a file.",
        "DELE": "DELE <file> - Deletes a file from the server.",
        "RMD": "RMD <directory> - Removes an empty directory from the server.",
        "MKD": "MKD <directory> - Creates a directory on the server.",
        "PWD": "PWD - Displays the current working directory."
    }

    if arg:
        # Si se pasa un argumento, muestra la ayuda de ese comando específico
        if arg.upper() in commands:
            client_socket.send(f"214 {commands[arg.upper()]}\r\n".encode())
        else:
            client_socket.send(b"500 Command not recognized.\r\n")
    else:
        # Si no se pasa un argumento, muestra la lista completa de comandos
        help_message = "214 The following commands are recognized:\r\n"
        for command in commands:
            help_message += f"{command}\r\n"
        help_message += "214 End of help message.\r\n"
        client_socket.send(help_message.encode())

def cmd_RNFR(arg, client_socket, current_dir):

    # Verificar si se ha proporcionado un argumento (nombre del archivo a renombrar)
    if not arg:
        client_socket.send(b"550 No file name specified.\r\n")  # Si no se pasa un archivo
        return
    
    try:
        target_path = os.path.join(current_dir, arg)
        # Verificar si el archivo existe
        if not os.path.exists(target_path):
            client_socket.send(b"550 Requested action not taken. File unavailable.\r\n")
            return
        
        # Verificamos si el nombre del archivo es válido
        if not os.path.isfile(target_path):
            client_socket.send(b"553 Requested action not taken. File name not allowed.\r\n")
            return
        
        # Guardar la ruta del archivo
        rename_from_path = target_path
        client_socket.send(b"350 Ready for RNTO.\r\n")  # Confirmación de que RNFR fue recibido
        return rename_from_path

    except Exception as e:
        client_socket.send(f"550 Error: {str(e)}\r\n".encode())  # Error genérico si ocurre algún problema inesperado

def cmd_RNTO(arg, client_socket, rename_from_path, current_dir):

    # Verificar que RNFR fue llamado previamente y que el nombre de archivo de destino es válido
    if not rename_from_path:
        client_socket.send(b"550 RNFR not received or new name missing.\r\n")  # Error si RNFR no fue ejecutado
        return
    
    if not arg:
        client_socket.send(b"550 No new file name specified.\r\n")  # Si no se proporciona un nuevo nombre
        return

    try:
        target_path = os.path.join(current_dir, arg)
        # Verificar si el archivo destino ya existe
        if os.path.exists(target_path):
            client_socket.send(b"550 File already exists.\r\n")  # Error si el archivo de destino ya existe

        # Verificar si el nuevo nombre es válido
        if not os.path.isabs(target_path):
            client_socket.send(b"553 Requested action not taken. File name not allowed.\r\n")
            return

        # Intentar realizar el renombrado
        os.rename(rename_from_path, target_path)  # Renombramos el archivo
        client_socket.send(b"250 Rename successful.\r\n")  # Confirmación de éxito

    except FileNotFoundError:
        client_socket.send(b"550 Requested action not taken. File unavailable.\r\n")  # Si el archivo no se encuentra
    except PermissionError:
        client_socket.send(b"550 Permission denied.\r\n")  # Si no se tiene permiso para renombrar
    except OSError as e:
        # Manejo de casos generales o errores relacionados con el sistema de archivos
        client_socket.send(f"550 Error: {str(e)}\r\n".encode())
    except Exception as e:
        client_socket.send(f"550 Error: {str(e)}\r\n".encode())

def cmd_NOOP(client_socket):
    try:
        # Responder con un código de éxito 200, indicando que la operación no ha hecho nada
        client_socket.send(b"200 NOOP command successful.\r\n")
    except Exception as e:
        # Manejo de errores en caso de que la respuesta no pueda enviarse
        client_socket.send(b"450 Requested file action not taken.\r\n")
        print(f"Error handling NOOP command: {e}")

def cmd_PASV(client_socket, data_port_range=(1024, 65535)):
    global DATA_SOCKET
    try:
        # Obtener la IP local del servidor
        server_ip = socket.gethostbyname(socket.gethostname())  # Obtiene la IP real
        pasv_port = random.randint(data_port_range[0], data_port_range[1])

        # Crear socket de datos
        data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_socket.bind((server_ip, pasv_port))
        data_socket.listen(1)

        # Convertir la IP y puerto a formato PASV
        ip_parts = server_ip.split('.')
        pasv_ip = ','.join(ip_parts)
        p1, p2 = pasv_port // 256, pasv_port % 256

        # Enviar respuesta al cliente
        pasv_response = f"227 Entering Passive Mode ({pasv_ip},{p1},{p2})\r\n"
        client_socket.sendall(pasv_response.encode())

        # Esperar a que el cliente se conecte al socket de datos
        client_conn, client_addr = data_socket.accept()

        print(f"[PASV] Servidor en modo pasivo en {server_ip}:{pasv_port}")
        return client_conn 


    except Exception as e:
        client_socket.sendall("500 PASV command failed.\r\n".encode())
        print(f"Error en PASV: {e}")
        return None, None, None

def cmd_RETR(client_socket, data_socket, filename, TYPE, MODE, current_dir):
    try:
        if not data_socket:
            client_socket.sendall(b"425 Use PASV or PORT first.\r\n")
            return

        # Verificar si el archivo existe
        target_path = filename
        if not os.path.isfile(filename):
            target_path = os.path.join(current_dir, filename)
            if not os.path.isfile(target_path):
                client_socket.sendall(b"550 File not found.\r\n")
                return
        
        # Verificar tipo de archivo para configurar permisos de lectura
        r_mode = 'rb'
        if TYPE == 'A':
            r_mode = 'r'

        if TYPE == 'A':
            client_socket.sendall(b"150 Opening ASCII mode data connection for file transfer.\r\n")
        else:
            client_socket.sendall(b"150 Opening binary mode data connection for file transfer.\r\n")

        if MODE == 'S':
            with open(target_path, r_mode) as file:
                while True:
                    data = file.read(BUFFER_SIZE)
                    if not data:
                        break  # Fin del archivo
                    if TYPE == 'A':
                        data_socket.sendall(data.encode())  # Enviar los datos
                    else:
                        data_socket.sendall(data)
        else:
            with open(target_path, r_mode) as file:
                while True:
                    data = file.read(BUFFER_SIZE)
                    if not data:
                        break  # Fin del archivo

                    # Crear encabezado del bloque (DATA)
                    block_header = struct.pack(">BH", 0x00, len(data))  # (Tipo, Tamaño)
                    if TYPE == 'A':
                        data_socket.sendall(block_header + data.encode())  # Enviar bloque
                    else:
                        data_socket.sendall(block_header + data)  # Enviar bloque

                # Enviar bloque EOF al final
                eof_header = struct.pack(">BH", 0x80, 0)  # Tipo EOF, Tamaño 0
                data_socket.sendall(eof_header)

        # Cerrar el socket de datos
        data_socket.close()
        
        # Confirmar la transferencia
        client_socket.sendall(b"226 Transfer complete.\r\n")
    
    except Exception as e:
        client_socket.sendall(b"451 Requested action aborted: local error in processing.\r\n")
        print(f"Error en RETR: {e}")

def cmd_STOR(client_socket, data_socket, filename, TYPE, MODE, current_dir):
    try:
        # Verificar si el cliente está enviando datos para un archivo
        if not data_socket:
            client_socket.sendall(b"425 Use PASV or PORT first.\r\n")
            data_socket.close()
            return

        # Preparar el path completo del archivo en el servidor
        target_path = os.path.join(current_dir, filename)

        # Verificar si el archivo ya existe y si se permite sobrescribirlo (según el protocolo)
        if os.path.exists(target_path):
            client_socket.sendall(b"550 File already exists.\r\n")
            data_socket.close()
            return
        
        # Enviar un mensaje de inicio de recepción de datos
        if TYPE == 'A':
            client_socket.sendall(b"150 Opening ASCII mode data connection for file transfer.\r\n")
        else:
            client_socket.sendall(b"150 Opening binary mode data connection for file transfer.\r\n")

        # Configurar el modo de escritura (binario o texto)
        write_mode = 'wb'  # Por defecto en modo binario
        if TYPE == 'A':
            write_mode = 'w'  # Si es tipo ASCII, abrir en modo texto

        # Abrir el archivo en modo de escritura
        with open(target_path, write_mode) as file:
            if MODE == 'S':
                while True:
                    chunk = data_socket.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    if TYPE == 'A':
                        file.write(chunk.decode())
                    else:
                        file.write(chunk)
            else:
                while True:
                    # Recibir el encabezado del bloque (1 byte de tipo + 2 bytes de longitud)
                    header = data_socket.recv(3)
                    if not header:
                        break  # Fin de la transferencia

                    block_type, block_size = struct.unpack(">BH", header)

                    # Si es un bloque EOF (0x80), finaliza la transferencia
                    if block_type == 0x80:
                        print("Fin de archivo alcanzado (EOF).")
                        break

                    # Recibir los datos del bloque
                    data = data_socket.recv(block_size)
                    if not data:
                        break  # Fin de la transferencia

                    # Escribir los datos en el archivo
                    if TYPE == 'A':
                        file.write(data.decode())
                    else:
                        file.write(data)

        # Confirmar la transferencia
        client_socket.sendall(b"226 Transfer complete.\r\n")

        # Cerrar el socket de datos
        data_socket.close()

    except Exception as e:
        # En caso de cualquier error, enviar un código de error
        client_socket.sendall(b"451 Requested action aborted: local error in processing.\r\n")
        print(f"Error en STOR: {e}")

def cmd_APPE(client_socket, data_socket, filename, TYPE, MODE, current_dir):
    try:
        # Verificar si el cliente está enviando datos para un archivo
        if not data_socket:
            client_socket.sendall(b"425 Use PASV or PORT first.\r\n")
            data_socket.close()
            return

        # Preparar el path completo del archivo en el servidor
        target_path = os.path.join(current_dir, filename)

        # Verificar si el archivo existe, ya que en APPE se debe agregar al final
        file_exists = os.path.exists(target_path)
        if not file_exists:
            client_socket.sendall(b"550 File does not exist.\r\n")
            data_socket.close()
            return
        
        # Enviar un mensaje de inicio de recepción de datos
        if TYPE == 'A':
            client_socket.sendall(b"150 Opening ASCII mode data connection for file transfer.\r\n")
        else:
            client_socket.sendall(b"150 Opening binary mode data connection for file transfer.\r\n")

        # Configurar el modo de escritura (binario o texto), en este caso append
        write_mode = 'ab'  # Modo append (agregar) en binario
        if TYPE == 'A':
            write_mode = 'a'  # Si es tipo ASCII, abrir en modo texto

        # Abrir el archivo en modo de append (agregar)
        with open(target_path, write_mode) as file:
            if MODE == 'S':
                while True:
                    chunk = data_socket.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    if TYPE == 'A':
                        file.write(chunk.decode())
                    else:
                        file.write(chunk)
            else:
                while True:
                    # Recibir el encabezado del bloque (1 byte de tipo + 2 bytes de longitud)
                    header = data_socket.recv(3)
                    if not header:
                        break  # Fin de la transferencia

                    block_type, block_size = struct.unpack(">BH", header)

                    # Si es un bloque EOF (0x80), finaliza la transferencia
                    if block_type == 0x80:
                        print("Fin de archivo alcanzado (EOF).")
                        break

                    # Recibir los datos del bloque
                    data = data_socket.recv(block_size)
                    if not data:
                        break  # Fin de la transferencia

                    # Escribir los datos en el archivo
                    if TYPE == 'A':
                        file.write(data.decode())
                    else:
                        file.write(data)

        # Confirmar la transferencia
        client_socket.sendall(b"226 Transfer complete.\r\n")

        # Cerrar el socket de datos
        data_socket.close()

    except Exception as e:
        # En caso de cualquier error, enviar un código de error
        client_socket.sendall(b"451 Requested action aborted: local error in processing.\r\n")
        print(f"Error en APPE: {e}")

def cmd_STOU(client_socket, data_socket, filename, TYPE, MODE, current_dir):
    try:
        # Verificar si el cliente está enviando datos para un archivo
        if not data_socket:
            client_socket.sendall(b"425 Use PASV or PORT first.\r\n")
            data_socket.close()
            return

        # Preparar el path completo del archivo en el servidor
        target_path = os.path.join(current_dir, filename)

        # Generar un nombre único para el archivo
        unique_filename = generate_unique_filename(current_dir, filename)
        target_path = os.path.join(current_dir, unique_filename)

        # Enviar un mensaje de inicio de recepción de datos
        if TYPE == 'A':
            client_socket.sendall(b"150 Opening ASCII mode data connection for file transfer.\r\n")
        else:
            client_socket.sendall(b"150 Opening binary mode data connection for file transfer.\r\n")

        # Configurar el modo de escritura (binario o texto)
        write_mode = 'wb'  # Por defecto en modo binario
        if TYPE == 'A':
            write_mode = 'w'  # Si es tipo ASCII, abrir en modo texto

        # Abrir el archivo en modo de escritura
        with open(target_path, write_mode) as file:
            if MODE == 'S':
                while True:
                    chunk = data_socket.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    if TYPE == 'A':
                        file.write(chunk.decode())
                    else:
                        file.write(chunk)
            else:
                while True:
                    # Recibir el encabezado del bloque (1 byte de tipo + 2 bytes de longitud)
                    header = data_socket.recv(3)
                    if not header:
                        break  # Fin de la transferencia

                    block_type, block_size = struct.unpack(">BH", header)

                    # Si es un bloque EOF (0x80), finaliza la transferencia
                    if block_type == 0x80:
                        print("Fin de archivo alcanzado (EOF).")
                        break

                    # Recibir los datos del bloque
                    data = data_socket.recv(block_size)
                    if not data:
                        break  # Fin de la transferencia

                    # Escribir los datos en el archivo
                    if TYPE == 'A':
                        file.write(data.decode())
                    else:
                        file.write(data)

        # Confirmar la transferencia
        client_socket.sendall(f"226 Transfer complete. Stored as {unique_filename}\r\n".encode())

        # Cerrar el socket de datos
        data_socket.close()

    except Exception as e:
        # En caso de cualquier error, enviar un código de error
        client_socket.sendall(b"451 Requested action aborted: local error in processing.\r\n")
        print(f"Error en STOU: {e}")

def cmd_LIST(client_socket, data_socket, current_dir):
    try:
        # Verificar si se está usando PASV o PORT
        if not data_socket:
            client_socket.sendall(b"425 Use PASV or PORT first.\r\n")
            return

        # Enviar respuesta indicando que se está abriendo una conexión de datos
        client_socket.sendall(b"150 Opening data connection for file list.\r\n")

        # Obtener lista de archivos y directorios en el directorio actual
        files = os.listdir(current_dir)

        # Recorrer los archivos y directorios y enviar detalles reales
        for filename in files:
            file_path = os.path.join(current_dir, filename)
            file_stat = os.stat(file_path)

            # Obtener los permisos del archivo (modo)
            file_permissions = oct(file_stat.st_mode)[-3:]
            
            # Obtener el tamaño del archivo
            file_size = file_stat.st_size

            # Obtener la fecha de última modificación
            last_modified_time = time.strftime("%b %d %H:%M", time.localtime(file_stat.st_mtime))

            # Preparar la línea de detalles del archivo
            if os.path.isdir(file_path):
                # Directorio
                file_details = f"drwxr-xr-x   1 user group {file_size} {last_modified_time} {filename}\r\n"
            else:
                # Archivo regular
                file_details = f"-rw-r--r--   1 user group {file_size} {last_modified_time} {filename}\r\n"
            
            # Enviar los detalles del archivo
            data_socket.sendall(file_details.encode())

        # Finalizar la transferencia
        client_socket.sendall(b"226 Transfer complete.\r\n")
        data_socket.close()

    except Exception as e:
        # En caso de error, enviar código de error
        client_socket.sendall(b"451 Requested action aborted: local error in processing.\r\n")
        print(f"Error en LIST: {e}")

def cmd_NLST(client_socket, data_socket, current_dir):
    try:
        # Verificar si se está usando PASV o PORT
        if not data_socket:
            client_socket.sendall(b"425 Use PASV or PORT first.\r\n")
            return

        # Enviar respuesta indicando que se está abriendo una conexión de datos
        client_socket.sendall(b"150 Opening data connection for file list.\r\n")

        # Obtener lista de archivos en el directorio actual
        files = os.listdir(current_dir)

        # Enviar los nombres de los archivos y directorios
        for filename in files:
            data_socket.sendall(f"{filename}\r\n".encode())

        # Finalizar la transferencia
        client_socket.sendall(b"226 Transfer complete.\r\n")
        data_socket.close()

    except Exception as e:
        # En caso de error, enviar código de error
        client_socket.sendall(b"451 Requested action aborted: local error in processing.\r\n")
        print(f"Error en NLST: {e}")


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

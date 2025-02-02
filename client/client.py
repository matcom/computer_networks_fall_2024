import socket
import os
import re
import sys

BUFFER_SIZE = 1024
TYPE = 'A'
DATA_SOCKET = None                  # Socket de transferencia utilizado para transferencia de datos

# Funciones -------------------------------------------------------------------------------------------------------------------

# Obtener una respuesta del servidor
def get_response(socket):
    response = ''
    while True:
        data = socket.recv(BUFFER_SIZE).decode()
        response += data
        if data.endswith('\r\n') or len(data) < BUFFER_SIZE:
            break
    return response

# Iniciar la conexión con el servidor
def client_connects_to_server(sock, server_addr, port):
    sock.connect((server_addr, port))
    return sock.recv(BUFFER_SIZE).decode()

# Enviar mensaje al servidor
def send(socket, message):
    socket.sendall(f"{message}\r\n".encode())
    response = get_response(socket)
    return response

# Loguearse como usuario anónimo
def default_login(socket):
    send(socket, f"USER anonymous")
    response = send(socket, "PASS anonymous")
    print("Autenticado como usuario anónimo.")
    return response

# Loguearse (USER and PASS)
def client_login(sock, username, password):
    sock.sendall(f"USER {username}\r\n".encode())
    response = sock.recv(BUFFER_SIZE).decode()

    if "331" in response:
        sock.sendall(f"PASS {password}\r\n".encode())
        response = sock.recv(BUFFER_SIZE).decode()
    
    return response

# Validar argumentos recibidos por el comando
def argument_handler(min_required_args, max_required_args, given_args):
    if min_required_args>given_args:
        if min_required_args==max_required_args:
            return f"Este comando requiere {min_required_args} argumentos, sin embargo {given_args} fueron recibidos."
        else:
            return f"Este comando requiere al menos {min_required_args} argumentos, sin embargo {given_args} fueron recibidos."
    elif max_required_args<given_args:
        return f"Este comando recibió {given_args-max_required_args} argumentos innecesarios."
    else:
        return "Argumentos recibidos correctamente"

# Obtener argumentos manualmente
def get_arg(flag):
    try:
        index = sys.argv.index(flag)
        return sys.argv[index + 1]
    except (ValueError, IndexError):
        return None

# Obtener un socket de conexión (Configurado con PORT o PASV)
def get_socket():
    if DATA_SOCKET is None:
        print("No existe una conexión abierta en este momento, intentando conectar en modo pasivo")
        response = cmd_PASV(socket, [])
        if response is None:
            print("La conexión no se ha podido establecer")
        return response
    else: 
        return DATA_SOCKET

# Funciones para manejar comandos ---------------------------------------------------------------------------------------------

def generic_command_by_type(socket, *args, command, command_type):
    args_len = len(args)

    # Verificando validez de argumentos
    response = 'Undefined command type'

    if command_type == 'A':
        response = argument_handler(1,1,args_len)
        print(response)
        response = send(socket, f'{command} {args[0]}')
    if command_type == 'B':
        response = argument_handler(0,0,args_len)
        print(response)
        response = send(socket, f'{command}')
    if command_type == 'C':
        response = argument_handler(0,1,args_len)
        print(response)
        if args_len == 1:
            response = send(socket, f'{command} {args[0]}')
        else:
            response = send(socket, f'{command}')
    if command == 'RNFR':
        response = argument_handler(0,1,args_len)
        print(response)
        if args_len == 1:
            response = send(socket, f'{command} {args[0]}')
        else:
            print(send(socket, f'RNFR {args[0]}'))
            return send(socket, f'RNTO {args[1]}')

    if command == 'QUIT':
        if not socket is None:
            socket.close()

    return response

def cmd_STOR_APPE_STOU(socket, *args, command):
    args_len = len(args)
    response = argument_handler(1,2,args_len)
    print(response)

    # Verificar si el archivo existe
    if not os.path.exists(args[0]):
        print(f"La ruta {args[0]} no es una ruta válida.")
        return
    # Verificar tipo de archivo para configurar permisos de lectura
    if TYPE == 'A':
        r_mode = 'r'
    else:
        r_mode = 'rb'

    # Conectar para recibir el archivo
    data_socket = get_socket()

    try:
        # Enviar el comando STOR o APPE
        response = send(socket, f'{command} {os.path.basename(args[0])}')
        print(response)

        # Abrir el archivo en modo binario para leer y enviar su contenido
        with open(args[0], r_mode) as file:
            while True:
                chunk = file.read(BUFFER_SIZE)
                if not chunk:
                    break # Se sale del bucle cuando no hay más datos para enviar
                data_socket.sendall(chunk.encode())
    finally:
        # Asegurarse de que el socket de datos se cierre correctamente
        data_socket.close()

    # Leer y retornar la respuesta del servidor
    return get_response(socket)

def cmd_RETR(socket, *args):  
    # Crear la carpeta Downloads si no existe
    if not os.path.exists('Downloads'):
        os.makedirs('Downloads')
    # Verificar tipo de archivo para configurar permisos de escritura
    if TYPE == 'A':
        w_mode = 'w'
    else:
        w_mode = 'wb'
    # Conectar pasivamente para recibir el archivo
    data_socket = get_socket()

    # Descargar archivo
    try:
        # Enviar el comando RETR
        response = send(socket, f'RETR {args[0]}')
        print(response)

        # Recibir el archivo y guardarlo en la carpeta Downloads
        with open(f'Downloads/{args[0]}', w_mode) as file:
            while True:
                try:
                    chunk = data_socket.recv(BUFFER_SIZE)
                    if not chunk:
                        break
                    if TYPE == 'A':
                        file.write(chunk.decode())
                    else:
                        file.write(chunk)
                except socket.timeout:
                    break
    finally:
        # Asegurarse de que el socket de datos se cierre correctamente
        data_socket.close()
    return get_response(socket)

def cmd_LIST_NLST(socket, *args, command):
    args_len = len(args)
    response = argument_handler(0,1,args_len)
    print(response)

    # Conectar para recibir el archivo
    data_socket = get_socket()
    try:
        if args_len == 0:
            send(socket, command)
        else:
            send(socket, f'{command} {args[0]}')
        data = b''
        while True:
            try:
                chunk = data_socket.recv(BUFFER_SIZE)
                if not chunk:
                    break # Se sale del bucle cuando no hay más datos para recibir
                data += chunk
            except socket.timeout:
                break
        print(response(socket))
    finally:
        # Asegurarse de que el socket de datos se cierre correctamente
        data_socket.close()
    decoded_data = data.decode()
    return decoded_data

# Control de conexión:

def cmd_PORT(comm_socket, *args):
    """Envía el comando PORT al servidor FTP para especificar el puerto de datos del cliente."""
    args_len = len(args)
    response = argument_handler(2,2,args_len)
    print(response)
    
    if not isinstance(args[1], int):
        raise TypeError("El argumento 'PORT' debe ser un entero.")
    if not isinstance(ip, str):
        raise TypeError("El argumento 'IP' debe ser una cadena.")
    # Validando puerto
    if args[1] < 1 or args[1] > 65535:
        raise ValueError("El puerto debe estar en el rango de 1 a 65535.")
    # Validando IP
    ip_parts = args[0].split('.')
    if len(ip_parts) != 4:
        raise ValueError("La dirección IP debe tener exactamente cuatro partes.")

    # Iniciando socket de datos local
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.bind((args[0], int(args[1])))
    data_socket.listen(1)

    # Obtener la dirección IP y el puerto del socket de datos para enviar al servidor
    data_ip, data_port = data_socket.getsockname()
    ip_parts = data_ip.split('.')
    
    # Convertir la dirección IP y el puerto a formato de cadena para el comando PORT
    port_high, port_low = divmod(data_port, 256)
    port_str = f"{port_high},{port_low}"
    command = f"PORT {','.join(ip_parts)},{port_str}"

    # Verificando respuesta esperada
    response = send(comm_socket, command)
    if response.startswith('2'):
    # Cerrar el socket pasivo si está abierto
        if DATA_SOCKET is not None:
            DATA_SOCKET.close()
            DATA_SOCKET = None
    # Si el servidor responde con un código de éxito, proceder con la transferencia de datos
    print("Conexión activa establecida.")
    DATA_SOCKET = data_socket
    return response

def cmd_PASV(comm_socket, *args):
    """Envía el comando PASV al servidor FTP para establecer el modo pasivo (el servidor escucha conexiones y el cliente la inicia)."""
    try:
        response = send(comm_socket, 'PASV')
        # Extraer la dirección IP y el puerto del servidor
        print(response)
        match = re.search(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', response)
        if match:
            ip_parts = [int(x) for x in match.groups()[:4]]
            port = int(match.group(5)) * 256 + int(match.group(6))
            data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_socket.connect((socket.inet_ntoa(bytes(ip_parts)), port))
            return data_socket
        else:
            print('No se ha podido establecer una conexión de transferencia de datos con el Host: ')
            print(match)
            return None
    except Exception as e:
        print(f'No se pudo establecer el modo pasivo: {e}')
    return None

# Ejecución principal del cliente ---------------------------------------------------------------------------------------------

# Obteniendo variabes de parámetros pasados al programa
host = get_arg("-h")
port = int(get_arg("-p"))
user = get_arg("-u")
password = get_arg("-w")
command = get_arg("-c")
a_arg = get_arg("-a")
b_arg = get_arg("-b")

if not all([host, port, user, password]):
    print("Error: Host, puerto, usuario y contraseña son obligatorios.")
    exit()

# Conexión al servidor
ftp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    print(client_connects_to_server(ftp_socket, host, port))
except Exception as e:
    print(f"Error al conectar con el servidor: {e}")
    exit()

Response = "Intento de inicio de sesión"
# Autenticación
if user and password:
    Response = client_login(ftp_socket, user, password)
else:
    Response = default_login(ftp_socket)
print(Response)

# Ejecutar comando
cmd_args = [arg for arg in [a_arg, b_arg] if arg is not None]

# Llevando a mayúsculas
if command:
    command = command.upper

try:
    if command == 'USER':   # Comando usado para autenticarse en el servidor
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='A'))
    elif command == 'PASS': # Comando usado para introducir la contraseña en el servidor
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='A'))
    elif command == 'ACCT': # Comando usado para pasar al servidor información adicional de la cuenta
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='A'))
    elif command == 'SMNT': # Monta un sistema de archivos remoto en el servidor FTP
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='A'))
    elif command == 'REIN': # Reinicia la sesión FTP actual
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='B'))
    elif command == 'QUIT': # Cierra la sesión y termina la ejecución del cliente
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='B'))
        ftp_socket.close()
    elif command == 'PWD':  # Muestra el directorio de trabajo actual
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='B'))
    elif command == 'CWD':  # Cambia el directorio actual al especificado
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='A'))
    elif command == 'CDUP': # Cambia al directorio padre del directorio de trabajo actual
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='B'))
    elif command == 'MKD':  # Crea un nuevo directorio con el nombre especificado
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='A'))
    elif command == 'RMD':  # Elimina el directorio especificado
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='A'))
    elif command == 'RETR':
        print(cmd_RETR(ftp_socket, *cmd_args))
    elif command == 'STOR': # Almacena un archivo en el servidor
        print(cmd_STOR_APPE_STOU(ftp_socket, *cmd_args, command=command))
    elif command == 'APPE': # Agrega información al final de un archivo en el servidor
        print(cmd_STOR_APPE_STOU(ftp_socket, *cmd_args, command=command))
    elif command == 'DELE': # Elimina el directorio especificado
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='A'))
    elif command == 'LIST': # Recibe una lista de archivos en un directorio especificado
        print(cmd_LIST_NLST(ftp_socket, *cmd_args, command=command))
    elif command == 'NLST': # Recibe una lista de nombres de archivos en un directorio especificado
        print(cmd_LIST_NLST(ftp_socket, *cmd_args, command=command))
    elif command == 'ABOR': # Cancela el comando actual en el servidor FTP
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='B'))
    elif command == 'TYPE': # Establece el tipo de transferencia de datos ('ASCII' o 'BINARY')
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='A'))
    elif command == 'MODE': # Establece el modo de transferencia de datos ('STREAM' o 'BLOCK')
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='A'))
    elif command == 'STRU': # Establece la estructura de datos para la transferencia ('FILE' o 'RECORD')
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='A'))
    elif command == 'PORT':
        print(cmd_PORT(ftp_socket, *cmd_args))
    elif command == 'PASV':
        PASV_SOCKET = cmd_PASV(ftp_socket, *cmd_args)
    elif command == 'SYST': # Solicita información del sistema operativo del servidor FTP
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='B'))
    elif command == 'STAT': # Solicita el estado del servidor FTP o de un archivo específico
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='C'))
    elif command == 'HELP': # Solicita ayuda sobre un comando específico o sobre el servicio FTP en general
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='C'))
    elif command == 'RNFR': # Inicia el proceso de renombrar un archivo en el servidor FTP
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='None'))
    elif command == 'RNTO': # Completa el proceso de renombrar un archivo en el servidor FT
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='A'))
    elif command == 'NOOP': # Envía un comando NOOP al servidor FTP, no es muy útil excepto si quieres mantener la conexión activa
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='B'))
    elif command == 'STOU': # Envía un archivo al servidor y solicita que se le genere un nombre único
        print(cmd_STOR_APPE_STOU(ftp_socket, *cmd_args, command=command))
    elif command == 'ALLO': # Indica al servidor FTP que el cliente está listo para recibir datos
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='A'))
    elif command == 'REST': # Especifica un punto de inicio para la transferencia de datos
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='A'))
    elif command == 'SITE': # Envía un comando específico del sitio al servidor FTP
        print(generic_command_by_type(ftp_socket, *cmd_args, command=command, command_type='A'))
    else:
        print("Comando no reconocido, por favor intente de nuevo.")
except Exception as e:
    print(f"Error al ejecutar el comando: {e}")
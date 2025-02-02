import socket
import os
import re
import sys

BUFFER_SIZE = 1024
TYPE = 'A'
PASV_MODE = 0                       # Indicador de modo pasivo (0=inactivo   1=activo)
PASV_SOCKET = None                  # Socket de transferencia utilizado en modo pasivo
DATA_SOCKET = None                  # Socket de transferencia utilizado para transferencia de datos

# Funciones -------------------------------------------------------------------------------------------------------------------

def get_response(socket):
    response = ''
    while True:
        data = socket.recv(BUFFER_SIZE).decode()
        response += data
        if data.endswith('\r\n') or len(data) < BUFFER_SIZE:
            break
    return response

def client_connects_to_server(sock, server_addr, port):
    sock.connect((server_addr, port))
    return sock.recv(BUFFER_SIZE).decode()

def send(socket, message):
    socket.sendall(f"{message}\r\n".encode())
    response = get_response(socket)
    return response

def default_login(socket):
    send(socket, f"USER anonymous")
    response = send(socket, "PASS anonymous")
    print("Autenticado como usuario anónimo.")
    return response

def client_login(sock, username, password):
    sock.sendall(f"USER {username}\r\n".encode())
    response = sock.recv(BUFFER_SIZE).decode()

    if "331" in response:
        sock.sendall(f"PASS {password}\r\n".encode())
        response = sock.recv(BUFFER_SIZE).decode()
    
    return response

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

def start_pasv_socket():
    global PASV_SOCKET

    socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Funciones para manejar comandos ---------------------------------------------------------------------------------------------

# Control de acceso:
def cmd_USER(socket, *args):
    """Comando usado para autenticarse en el servidor"""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    print(response)
    return send(socket, f'USER {args[0]}')

def cmd_PASS(socket, *args):
    """Comando usado para introducir la contraseña en el servidor"""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    print(response)
    return send(socket, f'PASS {args[0]}')

def cmd_ACCT(socket, *args):
    """Comando usado para pasar al servidor información adicional de la cuenta"""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    print(response)
    return send(socket, f'ACCT {args[0]}')

def cmd_SMNT(socket, *args):
    """Monta un sistema de archivos remoto en el servidor FTP."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    print(response)
    return send(socket, f'SMNT {args[0]}')

def cmd_REIN(socket, *args):
    """Reinicia la sesión FTP actual."""
    args_len = len(args)
    response = argument_handler(0,0,args_len)
    print(response)
    return send(socket, f'REIN')

def cmd_QUIT(socket, *args):
    """Cierra la sesión y termina la ejecución del cliente"""
    args_len = len(args)
    response = argument_handler(0,0,args_len)
    print(response)
    response = send(socket, f'QUIT')
    if not socket is None:
        socket.close()
    return response

# Navegación:
def cmd_PWD(sock, *args):
    """Muestra el directorio de trabajo actual."""
    
    # Verifica que no se envían argumentos adicionales
    if args:
        print("El comando PWD no acepta argumentos.")
    
    # Envía el comando PWD al servidor FTP
    return send(sock, 'PWD')

def cmd_CWD(socket, *args):
    """Cambia el directorio actual al especificado."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    print(response)
    return send(socket, f'CWD {args[0]}')

def cmd_CDUP(socket, *args):
    """Cambia al directorio padre del directorio de trabajo actual."""
    args_len = len(args)
    response = argument_handler(0,0,args_len)
    print(response)
    return send(socket, f'CDUP')

def cmd_MKD(socket, *args):
    """Crea un nuevo directorio con el nombre especificado."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    print(response)
    return send(socket, f'MKD {args[0]}')

def cmd_RMD(socket, *args):
    """Elimina el directorio especificado."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    print(response)
    return send(socket, f'RMD {args[0]}')

# Transferencia de archivos:
def cmd_DELE(socket, *args):
    """Elimina el directorio especificado."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    print(response)
    return send(socket, f'DELE {args[0]}')

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
    data_socket = DATA_SOCKET
    if data_socket is None:
        print("No existe una conexión abierta en este momento, intentando iniciar en modo pasivo")
        response = cmd_PASV(socket, [])
        if response is None:
            return f"La conexión no se ha podido establecer"
        data_socket = response
    filename = args[0]
    # Descargar archivo
    try:
        # Enviar el comando RETR
        response = send(socket, f'RETR {filename}')
        if response.split()[0] == '550':
            return '550: Archivo no encontrado'
        
        # Recibir el archivo y guardarlo en la carpeta Downloads
        with open(f'Downloads/{filename}', w_mode) as file:
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
        print(response(socket))
    finally:
        # Asegurarse de que el socket de datos se cierre correctamente
        data_socket.close()
    return f"226: Archivo {filename} descargado en la carpeta Downloads. Cerrando conexión."

def cmd_STOR(socket, *args):
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
    # Extraer el nombre del archivo de la ruta completa
    filename = os.path.basename(args[0])

    # Conectar para recibir el archivo
    data_socket = DATA_SOCKET
    if data_socket is None:
        print("No existe una conexión abierta en este momento, intentando conectar en modo pasivo")
        response = cmd_PASV(socket, [])
        if response is None:
            return f"La conexión no se ha podido establecer: {response}"
        data_socket = response

    try:
        # Enviar el comando STOR
        send(socket, f'STOR {filename}')

        # Abrir el archivo en modo binario para leer y enviar su contenido
        with open(filepath, r_mode) as file:
            while True:
                chunk = file.read(BUFFER_SIZE)
                if not chunk:
                    break # Se sale del bucle cuando no hay más datos para enviar
                data_socket.sendall(chunk)
    finally:
        # Asegurarse de que el socket de datos se cierre correctamente
        data_socket.close()

    # Leer y retornar la respuesta del servidor
    return response(socket)

def cmd_APPE(socket, *args):
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    print(response)

    # Conectar para recibir el archivo
    data_socket = DATA_SOCKET
    if data_socket is None:
        print("421: No existe una conexión abierta en este momento, intentando conectar en modo pasivo")
        response = cmd_PASV(socket, [])
        if response is None:
            return "550: La conexión no se ha podido establecer"
        data_socket = response
    try:
        ans = send(socket, f'APPE {args[0]}')
        print(ans)
        if ans.startswith('150'):
            # Enviar los datos especificados
            data_socket.sendall(data.encode())
            data_socket.close()
            return response(socket)
        else:
            print("Permisos insuficientes o error en la operación")
    finally:
        # Asegurarse de que el socket de datos se cierre correctamente
        data_socket.close()

def cmd_LIST(socket, *args):
    args_len = len(args)
    response = argument_handler(0,1,args_len)
    print(response)

    # Conectar para recibir el archivo
    data_socket = DATA_SOCKET
    if data_socket is None:
        print("No existe una conexión abierta en este momento, intentando conectar en modo pasivo")
        response = cmd_PASV(socket, [])
        if response is None:
            return "La conexión no se ha podido establecer"
        data_socket = response
    try:
        if args_len == 0:
            send(socket, 'LIST')
        else:
            send(socket, f'LIST {args[0]}')
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

def cmd_NLST(socket, *args):
    args_len = len(args)
    response = argument_handler(0,1,args_len)
    print(response)

    # Conectar para recibir el archivo
    data_socket = DATA_SOCKET
    if data_socket is None:
        print("No existe una conexión abierta en este momento, intentando conectar en modo pasivo")
        response = cmd_PASV(socket, [])
        if response is None:
            return "La conexión no se ha podido establecer"
        data_socket = response
    try:
        if args_len == 0:
            send(socket, 'NLST')
        else:
            send(socket, f'NLST {args[0]}')
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

def cmd_ABOR(socket, *args):
    """Cancela el comando actual en el servidor FTP."""
    args_len = len(args)
    response = argument_handler(0,0,args_len)
    print(response)
    return send(socket, f'ABOR')

# Configuración de transferencia:
def cmd_TYPE(socket, *args):
    """Establece el tipo de transferencia de datos ('ASCII' o 'BINARY')."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    print(response)

    if args[0].upper() not in ['A', 'I']:
        raise ValueError("El modo debe ser A-ASCII o I-BINARY")
    response = send(socket, f'TYPE {args[0]}')
    TYPE = args[0].upper()
    return response
    
def cmd_MODE(socket, *args):
    """Establece el modo de transferencia de datos ('STREAM' o 'BLOCK')."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    print(response)

    if args[0].upper() not in ['S', 'B']:
        raise ValueError("504: El modo debe ser STREAM o BLOCK")
    return send(socket, f'MODE {args[0]}')

def cmd_STRU(socket, *args):
    """Establece la estructura de datos para la transferencia ('FILE' o 'RECORD')."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    print(response)
    
    if args[0].upper() not in ['F', 'R']:
        raise ValueError("504: El modo debe ser FILE o RECORD")
    return send(socket, f'STRU {args[0]}')

# Control de conexión:
def cmd_PORT(comm_socket, *args):
    """Envía el comando PORT al servidor FTP para especificar el puerto de datos del cliente."""
    args_len = len(args)
    response = argument_handler(2,2,args_len)
    print(response)
    
    if not isinstance(args[1], int):
        raise TypeError("504: El argumento 'PORT' debe ser un entero.")
    if not isinstance(ip, str):
        raise TypeError("El argumento 'IP' debe ser una cadena.")
    # Validando puerto
    if args[1] < 1 or args[1] > 65535:
        raise ValueError("504: El puerto debe estar en el rango de 1 a 65535.")
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
    if response.startswith('227'):
    # Cerrar el socket pasivo si está abierto
        if DATA_SOCKET is not None:
            DATA_SOCKET.close()
            DATA_SOCKET = None
            PASV_MODE = 0
    # Si el servidor responde con un código de éxito, proceder con la transferencia de datos
    print("Conexión activa establecida.")
    DATA_SOCKET = data_socket
    return response

def cmd_PASV(comm_socket, *args):
    """Envía el comando PASV al servidor FTP para establecer el modo pasivo (el servidor escucha conexiones y el cliente la inicia)."""
    try:
        print("1- Intentando obtener response de enviar el comando PASV\n")
        response = send(comm_socket, 'PASV')
        print("2- Response obtenida de enviar el comando PASV, proximo paso imprimir response\n")
        # Extraer la dirección IP y el puerto del servidor
        print(response)
        print("3- Response impresa, proximo paso buscar match\n")
        match = re.search(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', response)
        if match:
            print(f"4- Encontré match: {match}")
            ip_parts = [int(x) for x in match.groups()[:4]]
            port = int(match.group(5)) * 256 + int(match.group(6))
            data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_socket.connect((socket.inet_ntoa(bytes(ip_parts)), port))
            print('225: Conexión establecida, sin transferencia en proceso.')
            PASV_MODE = 1
            return data_socket
        else:
            print('425: No se ha podido establecer una conexión de transferencia de datos con el Host.')
            print(match)
            return None
    except Exception as e:
        print(f'No se pudo establecer el modo pasivo: {e}')
    return None

# Información del sistema:
def cmd_SYST(socket, *args):
    """Solicita información del sistema operativo del servidor FTP."""
    args_len = len(args)
    response = argument_handler(0,0,args_len)
    print(response)
    return send(socket, f'SYST')

def cmd_STAT(socket, *args):
    """Solicita el estado del servidor FTP o de un archivo específico."""
    args_len = len(args)
    response = argument_handler(0,1,args_len)
    print(response)
    if args_len==0:
        return send(socket, f'STAT')
    else:
        return send(socket, f'STAT {args[0]}')

def cmd_HELP(socket, *args):
    """Solicita ayuda sobre un comando específico o sobre el servicio FTP en general."""
    args_len = len(args)
    response = argument_handler(0,1,args_len)
    print(response)
    if args_len==0:
        print(send(socket, f'HELP'))
    else:
        print(send(socket, f'HELP {args[0]}'))
    return response(socket)

# Control de archivos:
def cmd_RNFR(socket, *args):
    """Inicia el proceso de renombrar un archivo en el servidor FTP."""
    args_len = len(args)
    response = argument_handler(1,2,args_len)
    print(response)

    if args_len == 1:
        return send(socket, f'RNFR {args[0]}')
    else:
        print(send(socket, f'RNFR {args[0]}'))
        return cmd_RNTO(socket, {args[1]})

def cmd_RNTO(socket, *args):
    """Completa el proceso de renombrar un archivo en el servidor FTP."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    print(response)
    return send(socket, f'RNTO {args[0]}')

# Otros comandos:
def cmd_NOOP(socket, *args):
    """Envía un comando NOOP al servidor FTP, no es muy útil excepto si quieres mantener la conexión activa."""
    args_len = len(args)
    response = argument_handler(0,0,args_len)
    print(response)
    return send(socket, f'NOOP')

def cmd_STOU(socket, *args):
    """Envía un archivo al servidor FTP y solicita que el servidor genere un nombre de archivo único."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
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
    # Extraer el nombre del archivo de la ruta completa
    filename = os.path.basename(args[0])

    # Conectar para recibir el archivo
    data_socket = DATA_SOCKET
    if data_socket is None:
        print("421: No existe una conexión abierta en este momento, intentando conectar en modo pasivo")
        response = cmd_PASV(socket, [])
        if response is None:
            return "550: La conexión no se ha podido establecer"
        data_socket = response

    try:
        # Enviar el comando STOU
        send(socket, f'STOU {filename}')

        # Abrir el archivo en modo binario para leer y enviar su contenido
        with open(filepath, r_mode) as file:
            while True:
                chunk = file.read(BUFFER_SIZE)
                if not chunk:
                    break # Se sale del bucle cuando no hay más datos para enviar
                data_socket.sendall(chunk)
    finally:
        # Asegurarse de que el socket de datos se cierre correctamente
        data_socket.close()

    # Leer y retornar la respuesta del servidor
    return response(socket)

def cmd_ALLO(socket, *args):
    """Indica al servidor FTP que el cliente está listo para recibir datos."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    print(response)
    return send(socket, f'ALLO {args[0]}')

def cmd_REST(socket, *args):
    """Especifica un punto de inicio para la transferencia de datos."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    print(response)
    return send(socket, f'REST {args[0]}')

def cmd_SITE(socket, *args):
    """Envía un comando específico del sitio al servidor FTP."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    print(response)
    return send(socket, f'SITE {args[0]}')

# Obtener argumentos manualmente
def get_arg(flag):
    try:
        index = sys.argv.index(flag)
        return sys.argv[index + 1]
    except (ValueError, IndexError):
        return None

# Ejecución principal del cliente ---------------------------------------------------------------------------------------------

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

# Autenticación
Response = client_login(ftp_socket, user, password)
print(Response)

# Ejecutar comando
cmd_args = [arg for arg in [a_arg, b_arg] if arg is not None]

try:
    if command == 'USER':
        print(cmd_USER(ftp_socket, *cmd_args))
    elif command == 'PASS':
        print(cmd_PASS(ftp_socket, *cmd_args))
    elif command == 'ACCT':
        print(cmd_ACCT(ftp_socket, *cmd_args))
    elif command == 'SMNT':
        print(cmd_SMNT(ftp_socket, *cmd_args))
    elif command == 'REIN':
        print(cmd_REIN(ftp_socket, *cmd_args))
    elif command == 'QUIT':
        print(cmd_QUIT(ftp_socket, *cmd_args))
        ftp_socket.close()
    elif command == 'PWD':
        print(cmd_PWD(ftp_socket, *cmd_args))
    elif command == 'CWD':
        print(cmd_CWD(ftp_socket, *cmd_args))
    elif command == 'CDUP':
        print(cmd_CDUP(ftp_socket, *cmd_args))
    elif command == 'MKD':
        print(cmd_MKD(ftp_socket, *cmd_args))
    elif command == 'RMD':
        print(cmd_RMD(ftp_socket, *cmd_args))
    elif command == 'RETR':
        print(cmd_RETR(ftp_socket, *cmd_args))
    elif command == 'STOR':
        print(cmd_STOR(ftp_socket, *cmd_args))
    elif command == 'APPE':
        print(cmd_APPE(ftp_socket, *cmd_args))
    elif command == 'DELE':
        print(cmd_DELE(ftp_socket, *cmd_args))
    elif command == 'LIST':
        print(cmd_LIST(ftp_socket, *cmd_args))
    elif command == 'NLST':
        print(cmd_NLST(ftp_socket, *cmd_args))
    elif command == 'ABOR':
        print(cmd_ABOR(ftp_socket, *cmd_args))
    elif command == 'TYPE':
        print(cmd_TYPE(ftp_socket, *cmd_args))
    elif command == 'MODE':
        print(cmd_MODE(ftp_socket, *cmd_args))
    elif command == 'STRU':
        print(cmd_STRU(ftp_socket, *cmd_args))
    elif command == 'PORT':
        print(cmd_PORT(ftp_socket, *cmd_args))
    elif command == 'PASV':
        PASV_SOCKET = cmd_PASV(ftp_socket, *cmd_args)
    elif command == 'SYST':
        print(cmd_SYST(ftp_socket, *cmd_args))
    elif command == 'STAT':
        print(cmd_STAT(ftp_socket, *cmd_args))
    elif command == 'HELP':
        print(cmd_HELP(ftp_socket, *cmd_args))
    elif command == 'RNFR':
        print(cmd_RNFR(ftp_socket, *cmd_args))
    elif command == 'RNTO':
        print(cmd_RNTO(ftp_socket, *cmd_args))
    elif command == 'NOOP':
        print(cmd_NOOP(ftp_socket, *cmd_args))
    elif command == 'STOU':
        print(cmd_STOU(ftp_socket, *cmd_args))
    elif command == 'ALLO':
        print(cmd_ALLO(ftp_socket, *cmd_args))
    elif command == 'REST':
        print(cmd_REST(ftp_socket, *cmd_args))
    elif command == 'SITE':
        print(cmd_SITE(ftp_socket, *cmd_args))
    else:
        print("Comando no reconocido, por favor intente de nuevo.")
except Exception as e:
    print(f"Error al ejecutar el comando: {e}")
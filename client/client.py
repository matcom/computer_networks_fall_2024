import socket
import os

# Configuración inicial
FTP_SERVER_ADDR = '127.0.0.1'       # Dirección del servidor
FTP_CONTROL_PORT = 21               # Puerto del servidor FTP para manejar sesiones. Este valor no cambia
FTP_DATA_PORT = 20                  # Puerto del servidor FTP para enviar y recibir datos
BUFFER_SIZE = 1024
TYPE = None

# Funciones -------------------------------------------------------------------------------------------------------------------

def response(socket):
    response = ''
    while True:
        data = socket.recv(BUFFER_SIZE).decode
        response += data
        if data.endswith('\r\n'):
            break
    return response

def client_connects_to_server(socket):
    socket.connect((FTP_SERVER_ADDR, FTP_CONTROL_PORT))
    return response()

def send(socket, message):
    socket.sendall(f"{message}\r\n".encode())
    return response()

def default_login(socket):
    send(socket, f"USER anonymous")
    response = send(socket, "PASS anonymous")

    if "230" in response: 
        print("Autenticado como usuario anónimo.")
        return response
    else:
        return (f"Error de autenticación: {response}")

def client_login(socket):
    username = input("Ingrese el nombre de usuario: ")
    if username == "":
        return default_login()
    
    send(socket, f"USER {username}")
    password = getpass.getpass("Ingrese la contraseña: ")
    response = send(socket, f"PASS {password}")

    req = input("Requiere una cuenta específica?   s -> SI    [otra tecla] -> NO: ")
    if req == "s" or req == "S":
        account = input("Ingrese su cuenta: ")
        acct_response = send(socket, f"ACCT {account}") 
        return acct_response

    elif "230" in response: 
        return response
    else:
        return (f"Error de autenticación: {response}")

# Funciones para manejar comandos ---------------------------------------------------------------------------------------------

# Control de acceso:
def cmd_USER(username):
    pass

def cmd_PASS(password):
    pass

def cmd_ACCT(account_info):
    pass

def cmd_SMNT(pathname):
    pass

def cmd_REIN():
    pass

def cmd_QUIT():
    pass

# Navegación:
def cmd_PWD():
    pass

def cmd_CWD(pathname):
    pass

def cmd_CDUP():
    pass

def cmd_MKD(pathname):
    pass

def cmd_RMD(pathname):
    pass

# Transferencia de archivos:
def cmd_RETR(pathname):
    pass

def cmd_STOR(pathname):
    pass

def cmd_APPE(pathname):
    pass

def cmd_DELE(pathname):
    pass

def cmd_LIST(pathname):
    pass

def cmd_NLST(pathname):
    pass

def cmd_ABOR():
    pass

# Configuración de transferencia:
def cmd_TYPE(type_code):
    pass

def cmd_MODE(mode_code):
    pass

def cmd_STRU(structure_code):
    pass

# Control de conexión:
def cmd_PORT(host_port):
    pass

def cmd_PASV():
    pass

# Información del sistema:
def cmd_SYST():
    pass

def cmd_STAT(pathname=None):
    pass

def cmd_HELP(command=None):
    pass

# Control de archivos:
def cmd_RNFR(pathname):
    pass

def cmd_RNTO(pathname):
    pass

# Otros comandos:
def cmd_NOOP():
    pass

def cmd_STOU():
    pass

def cmd_ALLO(size):
    pass

def cmd_REST(marker):
    pass

def cmd_SITE(command):
    pass

# Ejecución principal del cliente ---------------------------------------------------------------------------------------------

# Conexión inicial
FTP_SERVER_ADDR = input("Ingrese la dirección IP del servidor FTP: ")
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    print(client_connects_to_server(socket))
except Exception as e:
    print(f"Error al conectar con el servidor: {e}")
    exit()

# Autenticación de usuario
while True:
    response = client_login(socket)
    print(response)
    if "230" in response:
        break
    else:
        print("Inténtelo de nuevo.")

# Ejecución de comandos del cliente
while True:
    try:
        user_input = input("=> ")

    except Exception as e:
        print(f"Error: {e}")
    
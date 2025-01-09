import socket
import os

# Configuración inicial
FTP_SERVER_ADDR = '127.0.0.1'       # Dirección del servidor
FTP_CONTROL_PORT = 21               # Puerto del servidor FTP para manejar sesiones. Este valor no cambia
FTP_DATA_PORT = 20                  # Puerto del servidor FTP para enviar y recibir datos
BUFFER_SIZE = 1024
TYPE = None

# Funciones

def client_connects_to_server(socket):
    socket.connect((FTP_SERVER_ADDR, FTP_CONTROL_PORT))
    response = b''
    while True:
        data = socket.recv(BUFFER_SIZE)
        response += data
        if data.endswith(b'\r\n'):
            break
    return response.decode('utf-8')

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
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.settimeout(10)
print(client_connects_to_server(socket))

# Realizar conexión al servidor


# Ejecución de comandos del cliente
while True:
    try:
        user_input = input("=> ")

    except Exception as e:
        print(f"Error: {e}")
    
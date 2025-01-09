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
    
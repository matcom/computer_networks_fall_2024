from socket import *

# Nombre del servidor y puerto para establecer la conexion
server_name = 'localhost'
server_port = 12000

# crea el socket para establecer la comunicacion(ip4 y TCP)
client_socket = socket(AF_INET, SOCK_STREAM)

#handshake inicial entre cliente y servidor
client_socket.connect((server_name,server_port))

# -- Implementar protocolo FTP --
# Esto de momento es una prueba mandando tu nombre para que el server te salude
name = input('Ingrese su nombre: ')
client_socket.send(name.encode())

response = client_socket.recv(1024).decode()
print(response)

# cierra la conexion
client_socket.close()


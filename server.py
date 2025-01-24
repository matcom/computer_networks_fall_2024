from socket import *

# levantando el servidor
server_port = 12000
server_socket = socket(AF_INET, SOCK_STREAM)
server_socket.bind(('' , server_port))
server_socket.listen(1)

print("Server Ready...")

# escuchando conexiones de clientes
while True:
    connection_socket , addr = server_socket.accept() #conexion establecida
    
    # -- Implementar protocolo FTP -- 
    # -- de momento como prueba, recibe un nombre y manda un saludo
    name = connection_socket.recv(1024).decode()
    response = "Server says: hello, " + name
    connection_socket.send(response.encode())
    connection_socket.close()
    
    


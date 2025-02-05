import socket
import os
import threading


class FTPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Servidor FTP escuchando en {self.host}:{self.port}")

    def handle_client(self, client_socket):
        client_socket.send("220 Bienvenido al Servidor FTP\r\n".encode('utf-8'))
        while True:
            data = client_socket.recv(1024).decode('utf-8').strip()
            if not data:
                break

            command = data.split(' ')[0].upper()
            if command == 'USER':
                client_socket.send("331 Nombre de usuario correcto, se requiere contraseña\r\n".encode('utf-8'))
            elif command == 'PASS':
                client_socket.send("230 Usuario autenticado, proceda\r\n".encode('utf-8'))
            elif command == 'LIST':
                files = os.listdir('.')
                client_socket.send("150 Listado de directorio en proceso\r\n".encode('utf-8'))
                client_socket.send(('\r\n'.join(files) + '\r\n').encode('utf-8'))
                client_socket.send("226 Listado de directorio completado\r\n".encode('utf-8'))
            elif command == 'QUIT':
                client_socket.send("221 Adios\r\n".encode('utf-8'))
                break
            else:
                client_socket.send("500 Comando desconocido\r\n".encode('utf-8'))

        client_socket.close()

    def run(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Conexión aceptada de {addr}")
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_thread.start()


if __name__ == "__main__":
    server = FTPServer('0.0.0.0', 21)
    server.run()

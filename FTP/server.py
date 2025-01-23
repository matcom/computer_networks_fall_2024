import socket
import os


def start_ftp_server(host='0.0.0.0', port=21):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Servidor FTP iniciado en {host}:{port}")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"Cliente conectado: {client_address}")
        handle_client(client_socket)


def handle_client(client_socket):
    client_socket.send(b"220 Bienvenido al servidor FTP\r\n")
    while True:
        try:
            command = client_socket.recv(1024).decode().strip()
            if not command:
                break

            print(f"Comando recibido: {command}")

            # Procesar comandos FTP básicos
            if command.upper().startswith("USER"):
                client_socket.send(b"331 Usuario aceptado, se requiere contraseña.\r\n")
            elif command.upper().startswith("PASS"):
                client_socket.send(b"230 Usuario autenticado con éxito.\r\n")
            elif command.upper() == "QUIT":
                client_socket.send(b"221 Cerrando conexión.\r\n")
                break
            elif command.upper() == "LIST":
                # Respuesta de ejemplo para LIST
                files = "\r\n".join(os.listdir(".")).encode()
                client_socket.send(b"150 Listado de directorio:\r\n")
                client_socket.send(files + b"\r\n")
                client_socket.send(b"226 Listado completado.\r\n")
            else:
                client_socket.send(b"502 Comando no implementado.\r\n")
        except ConnectionResetError:
            break
    client_socket.close()


if __name__ == "__main__":
    start_ftp_server()
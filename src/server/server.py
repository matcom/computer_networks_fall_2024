import socket
import threading

def handle_client(client_socket):
    request = client_socket.recv(1024).decode('utf-8')
    print(f"Solicitud recibida:\n{request}")
    response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nHola, mundo!"
    client_socket.send(response.encode('utf-8'))
    client_socket.close()

def start_server(host='127.0.0.1', port=8080):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Servidor escuchando en {host}:{port}...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Conexión aceptada de {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()
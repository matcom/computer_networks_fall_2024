import socket

def start_ftp_client(host='127.0.0.1', port=21):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # Recibir saludo del servidor
    print(client_socket.recv(1024).decode())

    while True:
        command = input("FTP> ")
        if command.lower() == 'quit':
            client_socket.send(b"QUIT\r\n")
            break
        client_socket.send((command + "\r\n").encode())
        response = client_socket.recv(1024).decode()
        print(response)

    client_socket.close()

if __name__ == "__main__":
    start_ftp_client()
import socket
import ssl
import argparse
import json
import re

def connect_to_server(server, port, use_tls=False):
    """
    Conecta al servidor FTP.
    Si use_tls es True, establece una conexión segura (TLS/SSL).
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server, port))

    if use_tls:
        # Configura el contexto SSL
        context = ssl.create_default_context()
        tls_socket = context.wrap_socket(client_socket, server_hostname=server)
        return tls_socket
    else:
        return client_socket

def send_command(client_socket, command):
    """
    Envía un comando al servidor FTP y devuelve la respuesta en formato JSON.
    """
    client_socket.sendall(command.encode())
    response = client_socket.recv(1024).decode().strip()
    status_code = response.split(" ")[0]  # Extrae el código de estado
    return json.dumps({"status": status_code, "message": response}, indent=4)

def parse_pasv_response(response, server_ip):
    """
    Extrae la dirección IP y el puerto de la respuesta PASV.
    Si la respuesta no es válida, usa la dirección IP del servidor.
    """
    match = re.search(r"(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)", response)
    if match:
        ip = ".".join(match.groups()[:4])
        port = int(match.groups()[4]) * 256 + int(match.groups()[5])
        return ip, port
    return server_ip, None  # Usa la dirección IP del servidor si la respuesta no es válida

def stor_retr_files(command, pasv_response, server, client_socket, argument1,argument2):
    if "227" in pasv_response:  # Código 227: Entrando en modo pasivo
        ip, port = parse_pasv_response(pasv_response, server)  # Pasa la dirección IP del servidor
        if ip and port:
            # Establece la conexión de datos
            data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_socket.connect((ip, port))

            if command == "RETR":
                # Ejecuta e
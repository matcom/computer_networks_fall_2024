import os
import re
import socket
import streamlit as st
from clientFTP import FTPClient

def execute_command():
    command = st.session_state.command_input.strip()
    if not command:
        return

    cmd_parts = command.split()
    cmd = cmd_parts[0].upper()
    args = cmd_parts[1:] if len(cmd_parts) > 1 else []

    try:
        if cmd in ["LIST", "RETR", "STOR", "APPE", "NLST"]:
            handle_passive_commands(cmd, args)
        else:
            handle_non_passive_commands(cmd, args)
    except Exception as e:
        st.session_state.client_responses.insert(0, f"Error: {e}")

def handle_passive_commands(cmd, args):
    response = st.session_state.ftp_client.sendCommand("PASV")
    st.session_state.client_responses.insert(0, response)

    if not response.startswith("227"):
        st.session_state.client_responses.insert(0, "Error: No se pudo entrar en modo pasivo")
        return

    match = re.search(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', response)
    if not match:
        st.session_state.client_responses.insert(0, "Error: No se pudo extraer la dirección IP y el puerto")
        return

    ip = ".".join(match.groups()[:4])
    port = (int(match.group(5)) << 8) + int(match.group(6))

    data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_sock.connect((ip, port))

    try:
        if cmd in ["LIST", "NLST"]:
            handle_list_commands(cmd, args, data_sock)
        elif cmd in ["RETR", "STOR", "APPE"]:
            handle_file_transfer_commands(cmd, args, data_sock)
    finally:
        data_sock.close()

def handle_list_commands(cmd, args, data_sock):
    path = args[0] if args else '.'
    response = st.session_state.ftp_client.send_command_multiresponse(cmd, path)
    st.session_state.client_responses.insert(0, response)
    if "150" in response:
        data = data_sock.recv(8192).decode()
        st.session_state.client_responses.insert(0, data)

def handle_file_transfer_commands(cmd, args, data_sock):
    if len(args) < 1:
        st.session_state.client_responses.insert(0, f"Uso: {cmd} <filename>")
        return

    filename = args[0]
    if cmd == "STOR":
        if os.path.exists(filename):
            response = st.session_state.ftp_client.send_stor_command(data_sock, "STOR", filename)
            st.session_state.client_responses.insert(0, response)
        else:
            st.session_state.client_responses.insert(0, "Archivo no encontrado")
    elif cmd == "RETR":
        response = st.session_state.ftp_client.send_command_multiresponse("RETR", filename)
        st.session_state.client_responses.insert(0, response)
        if "150" in response:
            if st.session_state.ftp_client.receive_file(data_sock, filename):
                st.session_state.client_responses.insert(0, "Archivo recibido exitosamente")
            else:
                st.session_state.client_responses.insert(0, "Error al recibir archivo")
    elif cmd == "APPE":
        if os.path.exists(filename):
            response = st.session_state.ftp_client.send_stor_command(data_sock, "APPE", filename)
            st.session_state.client_responses.insert(0, response)
        else:
            st.session_state.client_responses.insert(0, "Archivo no encontrado")

def handle_non_passive_commands(cmd, args):
    response = st.session_state.ftp_client.sendCommand(cmd, *args)
    st.session_state.client_responses.insert(0, response)
    if cmd == "QUIT":
        st.session_state.client_responses.insert(0, "Conexión cerrada.")
        st.session_state.ftp_client.close()

def main():
    st.title("Cliente FTP")

    if 'ftp_client' not in st.session_state:
        st.session_state.ftp_client = FTPClient("0.0.0.0",21)  # Crea una instancia del cliente FTP
        st.session_state.ftp_client.initialize()  # Inicia la conexión FTP

    # Inicializar el valor del campo de texto si no existe
    if 'command_input' not in st.session_state:
        st.session_state.command_input = ""
        
    # Inicializar la lista de respuestas si no existe
    if 'client_responses' not in st.session_state:
        st.session_state.client_responses = []


    # Crear dos columnas
    col1, col2 = st.columns(2)

    with col1:
        # Entrada de comandos
        st.text_input(
            "Ingrese un comando FTP:",
            key="command_input",
            on_change=execute_command,  # Ejecutar el comando al presionar Enter
        )
        if st.button("Borrar comando"):
            st.session_state.command_input = ""


    with col2:
        # Mostrar respuestas
        if 'client_responses' in st.session_state:
            st.text_area("Respuestas:", value="\n".join(st.session_state.client_responses), height=300)

        if st.button("Resetear respuestas"):
            st.session_state.client_responses = []
            
if __name__ == "__main__":
    main()

baseDirectoryForDownloads = "/Users/mauriciosundejimenez/ProyectoFinalFTP/computer_networks_fall_2024/Solution"

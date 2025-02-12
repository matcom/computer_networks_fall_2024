import os
import re
import socket
import streamlit as st
from clientFTP import FTPClient

def execute_command():
    command = st.session_state.command_input.strip()
    if command:
        # Procesar el comando
        cmd_parts = command.split()
        cmd = cmd_parts[0].upper()
        args = cmd_parts[1:] if len(cmd_parts) > 1 else []

        try:
            if cmd in ["LIST", "RETR", "STOR", "APPE", "NLST"]:
                # Enviar el comando PASV y obtener la respuesta
                response = st.session_state.ftp_client.send_command("PASV")
                st.session_state.client_responses.insert(0, response)

                if not response.startswith("227"):
                    st.session_state.client_responses.insert(0, "Error: No se pudo entrar en modo pasivo")
                else:
                    # Extraer la dirección IP y el puerto de la respuesta
                    match = re.search(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', response)
                    if not match:
                        st.session_state.client_responses.insert(0, "Error: No se pudo extraer la dirección IP y el puerto")
                    else:
                        # Construir la dirección IP y el puerto
                        ip = ".".join(match.groups()[:4])
                        port = (int(match.group(5)) << 8) + int(match.group(6))

                        # Crear un nuevo socket para la conexión de datos
                        data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        data_sock.connect((ip, port))

                        try:
                            if cmd == "LIST" or cmd == "NLST":
                                path = args[0] if args else '.'
                                response = st.session_state.ftp_client.send_command_multiresponse(cmd, path)
                                st.session_state.client_responses.insert(0, response)
                                if "150" in response:
                                    data = data_sock.recv(8192).decode()
                                    st.session_state.client_responses.insert(0, data)
                                data_sock.close()  # Cerrar el socket de datos

                            elif cmd in ["RETR", "STOR", "APPE"]:
                                if len(args) < 1:
                                    st.session_state.client_responses.insert(0, f"Uso: {cmd} <filename>")
                                else:
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
                        finally:
                            data_sock.close()  # Cerrar el socket de datos

            # Manejo de comandos que no requieren modo pasivo
            else:
                response = st.session_state.ftp_client.send_command(cmd, *args)
                st.session_state.client_responses.insert(0, response)
                if cmd == "QUIT":
                    st.session_state.client_responses.insert(0, "Conexión cerrada.")
                    st.session_state.ftp_client.close()

        except Exception as e:
            st.session_state.client_responses.insert(0, f"Error: {e}")


def main():
    st.title("FTP Client Interface")
    
    host = st.text_input("FTP Server Host", "0.0.0.0")
    port = st.number_input("FTP Server Port", 21)
    
    if st.button("Connect"):
        client = FTPClient(host, port)
        try:
            client.initialize()
            st.success("Connected to FTP server")
        except Exception as e:
            st.error(f"Connection failed: {e}")
            return
        
        command = st.text_input("Enter FTP Command")
        if st.button("Send Command"):
            try:
                # response = client.sendCommand(command)
                execute_command
                # st.text_area("Response", response)
                # if 'client_responses' in st.session_state:
                st.text_area("Respuestas:", value="\n".join(st.session_state.client_responses))
            except Exception as e:
                st.error(f"Error sending command: {e}")
            
        
        if st.button("Disconnect"):
            client.finish()
            st.success("Disconnected from FTP server")

if __name__ == "__main__":
    main()

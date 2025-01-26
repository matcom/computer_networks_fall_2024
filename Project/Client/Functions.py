from socket import *
import Client as cl
def list_files(tls_socket):
    response = cl.send_command(tls_socket, 'PASV')
    start = response.find('')
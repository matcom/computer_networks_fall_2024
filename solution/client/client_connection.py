import socket
import ssl
from utils import log, from_json, to_json

class connection:
    host: str
    port: int
    client_socket: socket
    ssl_socket: ssl.SSLSocket
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        
    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Envolver el socket con SSL
            context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            context.load_verify_locations(cafile='cert.pem')  # Usar el certificado del servidor
            
            self.ssl_socket = context.wrap_socket(self.client_socket, server_hostname=self.host)
            self.ssl_socket.connect((self.host, self.port))
            
            # Recibir la respuesta del servidor
            data = from_json(self.ssl_socket.recv(1024))
            
            if(data['status_code'] != '220'):
                return False
            
            return True
        except Exception as e:
            log(f'Error connecting to server: {e}')
            return False
        
    def send(self, data: bytes):
        self.ssl_socket.sendall(data)
        return self.ssl_socket.recv(1024)
    
    def send_file(self, filepath: str):
        pointer = open(filepath, 'rb')
        self.ssl_socket.sendfile(pointer)
        pointer.close()
            
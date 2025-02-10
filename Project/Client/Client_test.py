import Utils
import os
import time
import argparse
from socket import *

class Client_test:

    # Constructor de la clase
    def __init__(self, ip_server, port, user, password):
        self.ip_server = ip_server
        self.port = port
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.user = user 
        self.password = password
        self.data_socket = None
        
        # Diccionario de comandos y sus funciones correspondientes
        self.command_handlers = {
            "LIST": self.list_file,
            "STOR": lambda cmd, args: self.store_file(cmd, args),
            "STOU": lambda cmd, args: self.store_file(cmd, args),
            "RETR": lambda cmd, args: self.retrieve_file(cmd, args),
            "APPE": lambda cmd, args: self.store_file(cmd, args),
        }

    # Enviar comando al servidor
    def send_command(self, command, args=None):
        if args:
            command = f"{command} {args}"  # Concatenar el comando con los argumentos
        self.client_socket.sendall(f"{command}".encode())
    
    # Recibir una respuesta del servidor
    def receive_response(self):
        response = self.client_socket.recv(1024)
        return response.decode().strip()
    
    # Conectar con el servidor
    def connect(self):
        self.client_socket.connect((self.ip_server, self.port))
        response = self.receive_response()
        print(f"{response}")
    
    # Autenticarse mediante usuario y contrasena
    def auth(self):
        user_response = send_command(client_socket, f"USER {self.user}")
        print(user_response)

        password_response = send_command(client_socket, f"PASS {self.password}")
        print(password_response)

        if "230" in password_response:
            print("530 Authentication error. Please verify your credentials.")
            return False

        return True
    
    # Ejecuta un comando
    def execute_command(self, command, args=None):
        if command in ["LIST", "STOR", "RETR", "STOU", "APPE"]:
            return self.handle_data_connection(command, args)
        else:
            self.send_command(command, args)  # Pasar args a send_command
            return self.receive_response()
    
    # Ejecuta los comandos que requieren establecer conexion de datos
    def handle_data_connection(self, command, args):
        try:
            self.connect_data_socket()
            
            # Ejecutar el comando
            response = self.command_handlers[command](command, args)
            
            # Asegura cerrar el socket de datos
            if(self.data_socket):
                self.data_socket.close()
            
            return response
            
        except Exception as e:
            if self.data_socket:
                self.data_socket.close()
                                    
            return f"Error in {command}: {e}"

    # Conecta el socket de datos para transferencia de informacion
    def connect_data_socket(self):
        ip, port = self.enter_passive_mode()
        self.data_socket = socket(AF_INET, SOCK_STREAM)
        self.data_socket.settimeout(5)
        self.data_socket.connect((ip, port))
    
    # Entrar en modo pasivo
    def enter_passive_mode(self):
        try:
            self.send_command("PASV")
            response = self.receive_response()
            
            # Extraer la información de IP y puerto
            start = response.find('(') + 1
            end = response.find(')')
                
            data = response[start:end].split(',')
                
            ip = '.'.join(data[:4])
            port = int(data[4]) * 256 + int(data[5])
            return ip, port
            
        except Exception as e:
            print(f"Error in enter_passive_mode: {e}")
    
    # ------------------- Comandos Especificos  ---------------------------------------------------
    
    # Comando para listar archivos
    def list_file(self, command, args=None):
        self.send_command(command)
        
        all_data = b""
        while True:
            data = self.data_socket.recv(1024)
            if not data:
                break
            all_data += data

        print("Files \n--------------------------")
        print(f"{all_data.decode()}\n")
        
        self.data_socket.close()
        
        return self.receive_response()
          
    # Comando para recibir un archivo
    def retrieve_file(self, command, filename):
        Utils.validate_args(command, filename)
        
        #Agregar la carpeta fuente donde se descargara el archivo
        path = os.path.join(".local" , filename)
        
        # Enviar comando y recibir respuesta
        self.send_command(f"{command} {filename}")
        response = self.receive_response()
            
        # Verificar si se encontro el archivo
        if not response.startswith('550'):
            
            #Proceder a descargarlo
            with open(path, 'wb') as f:
                while True:
                    data = self.data_socket.recv(1024)
                    if not data:
                        break
                    f.write(data)

        self.data_socket.close()            
        return response    

    # Comando para guardar un archivo    
    def store_file(self, command, filename):
        # Maneja los comandos STOR, STOU Y APPEND
        Utils.validate_args(command, filename)
        
        # Agregar la carpeta fuente desde donde se enviara el archivo
        path = os.path.join(".local" , filename)
        
        # Chequear si el archivo existe localmente
        if not os.path.exists(path):
            return f"Error: File '{filename}' does not exist"
        
        if command == "STOU":
            filename = f"{int(time.time())}_{filename}" # le agrega timestamp para hacer el nombre unico
            
        # Enviar comando
        self.send_command(f"{command} {filename}")
        
        # Enviar archivo            
        with open(path, 'rb') as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                self.data_socket.sendall(data)
        
        self.data_socket.close()
        
        # Recibir confirmacion de transferencia completa            
        return self.receive_response()
    
def start_client(argvs):    
    server = argvs.host
    port = argvs.port
    username = argvs.username
    password = argvs.password
    command = argvs.command
    argument1 = argvs.argument1
    argument2 = argvs.argument2
    ftp_client = Client_test(server, port, username, password )
    ftp_client.execute_command(command, argument1) # esto hay que modificarlo para ajustarse a la entrada de los tests

if __name__ == "__main__":
    # Configura el parser de argumentos
    parser = argparse.ArgumentParser(description="Cliente FTP en Python", add_help=False)
    parser.add_argument("-h", "--host", required=True, help="Dirección del servidor FTP")
    parser.add_argument("-p", "--port", type=int, default=21, help="Puerto del servidor FTP")
    parser.add_argument("-u", "--username", required=True, help="Nombre de usuario")
    parser.add_argument("-w", "--password", required=True, help="Contraseña")
    parser.add_argument("-c", "--command", required=False, help="Comando a ejecutar")
    parser.add_argument("-a", "--argument1", required=False, help="Primer argumento del comando")
    parser.add_argument("-b", "--argument2", required=False, help="Segundo argumento del comando")

    # Parsea los argumentos
    argvs = parser.parse_args()

    # Llama a la función principal del cliente FTP
    start_client(argvs)
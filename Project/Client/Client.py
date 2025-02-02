import Utils
import os
import time
from socket import *

class Client:

    #Constructor de la clase
    def __init__(self, ip_server, port):
        self.ip_server = ip_server
        self.port = port
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.data_socket = None
        
        # Diccionario de comandos y sus funciones correspondientes
        self.command_handlers = {
            "LIST": self.list_file,
            "STOR": lambda cmd, args: self.store_file(cmd, args),
            "STOU": lambda cmd, args: self.store_file(cmd, args),
            "RETR": lambda cmd, args: self.retrieve_file(cmd, args),
            "APPE": lambda cmd, args: self.store_file(cmd, args),
        }
    
    #Conectar con el servidor
    def connect(self):
        self.client_socket.connect((self.ip_server, self.port))
        response = self.receive_response()
        print(f"{response}")
    
    #Enviar comando al servidor
    def send_command(self, command, args=None):
        if args:
            command = f"{command} {args}"  # Concatenar el comando con los argumentos
        self.client_socket.sendall(f"{command}".encode())
    
    #Recibir una respuesta del servidor
    def receive_response(self):
        response = self.client_socket.recv(1024)
        return response.decode()
    
    #Conecta el socket de datos para transferencia de informacion
    def connect_data_socket(self):
        ip, port = self.enter_passive_mode()
        self.data_socket = socket(AF_INET, SOCK_STREAM)
        self.data_socket.settimeout(5)
        self.data_socket.connect((ip, port))
    
    #Entrar en modo pasivo
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
    
    def execute_command(self, command, args=None):
        if command in ["LIST", "STOR", "RETR", "STOU", "APPE"]:
            return self.handle_data_connection(command, args)
        else:
            self.send_command(command, args)  # Pasar args a send_command
            return self.receive_response()
    
    # Manejar la conexión de datos para comandos que lo requieren
    def handle_data_connection(self, command, args):
        try:
            self.connect_data_socket()
            
            #Ejecutar el comando
            response = self.command_handlers[command](command, args)
            
            self.data_socket.close()
            return response
            
        except Exception as e:
            if self.data_socket:
                self.data_socket.close()
                    
            return f"Error in {command}: {e}"
            
    #Comando para listar archivos
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
        
        return self.receive_response()
        
        
    #Comando para recibir archivos
    def retrieve_file(self, command, filename):
        Utils.validate_args(command, filename)
        
        #Agregar la carpeta fuente donde se descargara el archivo
        path = f".local/{filename}"
        
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
                    
        return response    
        
    def store_file(self, command, filename):
        # Maneja los comandos STOR, STOU Y APPEND
        Utils.validate_args(command, filename)
        
        #Agregar la carpeta fuente desde donde se enviara el archivo
        path = f".local/{filename}"
        
        #Chequear si el archivo existe localmente
        if not os.path.exists(path):
            return f"Error: File '{filename}' does not exist"
        
        if command == "STOU":
            filename = f"{int(time.time())}_{filename}" #le agrega timestamp para hacer el nombre unico
            
        #Enviar comando
        self.send_command(f"{command} {filename}")
        
        #Enviar archivo            
        with open(path, 'rb') as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                self.data_socket.sendall(data)
        
        self.data_socket.close()
                    
        return self.receive_response()

    #Metodo que llamara a todas las funcionalidades del cliente
    def ftp_client(self):
        while True:
            user_input = input("ftp>> ").strip().split()
            cmd , args = Utils.recv_cmd(user_input)
            
            #print(f"Debug: cmd:{cmd}, args:{args}")
            
            if not cmd:
                continue
            
            response = self.execute_command(cmd, args)
            print(f"{response}")
            
            #Verificar si la respuesta es de cierre de conexión
            if response.startswith("221"):
                print("Cerrando la conexión...")
                self.client_socket.close()  
                break
            #Verificar si la respuesta es de comando desconocido
            if response.startswith("500"):  
                sug = Utils.Get_suggestion(cmd)
                print(f"Command {cmd} not found, try with {sug}")
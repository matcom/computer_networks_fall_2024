import Utils
import os
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
            "STOR": lambda args: self.store_file(args[0]) if args else print("Error: Filename required"),
            "RETR": lambda args: self.retrieve_file(args[0]) if args else print("Error: Filename required"),
            "QUIT": self.quit,
        }
    
    #Conectar con el servidor
    def connect(self):
        self.client_socket.connect((self.ip_server, self.port))
        response = self.receive_response()
        print(f"{response}")
    
    #Recibir una respuesta del servidor
    def receive_response(self):
        response = self.client_socket.recv(1024)
        return response.decode()
    
    #Enviar comando al servidor
    def send_command(self, command):
        self.client_socket.sendall(f"{command}".encode())
        return self.receive_response()
    
    #Entrar en modo pasivo
    def enter_passive_mode(self):
        #try:
            response = self.send_command("PASV")
            # Extraer la información de IP y puerto
            start = response.find('(') + 1
            end = response.find(')')
                
            data = response[start:end].split(',')
                
            ip = '.'.join(data[:4])
            port = int(data[4]) * 256 + int(data[5])
            return ip, port
            
        # except Exception as e:
        #     print(f"Error in enter_passive_mode: {e}")
        #     raise
    
    #Salir y cerrar la concexion
    def quit(self, args=None):
        self.send_command("QUIT")
        self.client_socket.close()
        print("Close Connection...")

    #Comando para listar archivos
    def list_file(self, args=None):
        try:
            # Obtener IP y puerto del modo pasivo
            ip, port = self.enter_passive_mode()
            # Crear nuevo socket de datos
            self.data_socket = socket(AF_INET, SOCK_STREAM)
            
            # Configurar timeout para la conexión
            self.data_socket.settimeout(5)
            
            # Intentar conectar
            try:
                self.data_socket.connect((ip, port))
            except Exception as e:
                return
            
            # Enviar comando LIST después de establecer la conexión de datos
            response = self.send_command("LIST")
            print(f"{response}")
            
            # Recibir datos
            data = self.data_socket.recv(1024)
            print(f"Files: \n{data.decode()}")
            
            # Cerrar socket de datos
            self.data_socket.close()
            
        except Exception as e:
            print(f"Error in list_file: {e}")
            if self.data_socket:
                self.data_socket.close()

    #Comando para recibir archivos
    def retrieve_file(self, filename):
        #los archios se guardaran en ./local/
        path = f"./.local/{filename}"
        
        try:
            # Obtener IP y puerto del modo pasivo
            ip, port = self.enter_passive_mode()
            
            # Crear nuevo socket de datos
            self.data_socket = socket(AF_INET, SOCK_STREAM)
            
            # Configurar timeout para la conexión
            self.data_socket.settimeout(5)
            
            # Intentar conectar
            try:
                self.data_socket.connect((ip, port))
                
            except Exception as e:
                print(f"Error connecting to data socket: {e}")
                return
            
            # Enviar comando RETR y verificar la respuesta
            response = self.send_command(f"RETR {filename}")
            
            # Verificar si el archivo no se encuentra
            if response.startswith('550'):
                print(f"Error: {response.strip()}")
                self.data_socket.close()
                return
            
            # Si el archivo existe, proceder a descargarlo
            with open(path, 'wb') as f:
                while True:
                    data = self.data_socket.recv(1024)
                    if not data:
                        break
                    f.write(data)
            
            self.data_socket.close()
            print(f"{response}")
            print(f"The file {filename} downloaded successfully")
            
        except Exception as e:
            print(f"Error in retrieve_file: {e}")
            if self.data_socket:
                self.data_socket.close()

    #Comando para Updatear un archivo
    def store_file(self, filename):
        # los archivos se guardaran en ./local/
        path = f"./.local/{filename}"
        
        try:
            # Chequear si el archivo existe localmente
            if not os.path.exists(path):
                print(f"Error: File '{filename}' does not exist")
                self.data_socket.close()
                return
            
            # Obtener IP y puerto del modo pasivo
            ip, port = self.enter_passive_mode()
            
            # Crear nuevo socket de datos
            self.data_socket = socket(AF_INET, SOCK_STREAM)
            
            # Configurar timeout para la conexión
            self.data_socket.settimeout(5)
            
            # Intentar conectar
            try:
                self.data_socket.connect((ip, port))
                
            except Exception as e:
                print(f"Error connecting to data socket: {e}")
                return
            
            # Enviar comando STOR 
            self.client_socket.sendall(f"STOR {filename}".encode())
                    
            with open(path, 'rb') as f:
                while True:
                    data = f.read(4096)
                    if not data:
                        break
                    self.data_socket.sendall(data)
                    
            self.data_socket.close()
            print(self.receive_response())
            print(f"The file {filename} uploaded successfully")
        
        except Exception as e:
            print(f"Error in store_file: {e}")
            if self.data_socket:
                self.data_socket.close()
        
    #Metodo que llamara a todas las funcionalidades del cliente
    def ftp_client(self):
        while True:
            # Obtener y parsear el comando
            user_input = input("ftp>> ").strip().split()
            if not user_input:
                continue

            cmd = user_input[0].upper()
            args = user_input[1:]

            if cmd in self.command_handlers:
                # Ejecutar el comando
                self.command_handlers[cmd](args)
                # Verificar si el comando es QUIT para salir del bucle
                if cmd == "QUIT":
                    break
            else:
                sug = Utils.Calculate_Lev(cmd)
                print(f"Command {cmd} not found, try with {sug}")
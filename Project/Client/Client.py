import Utils
import os
import time
from socket import *

class Client:
    user_db = 'user_database.json'
    # Constructor de la clase
    def __init__(self, ip_server, port):
        self.ip_server = ip_server
        self.port = port
        self.source_file = ".local"
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.data_socket = None
        self.logged_in = False
        # Diccionario de comandos y sus funciones correspondientes
        self.command_handlers = {
            "LIST": self.list_file,
            "STOR": lambda cmd, args: self.store_file(cmd, args),
            "STOU": lambda cmd, args: self.store_file(cmd, args),
            "APPE": lambda cmd, args: self.store_file(cmd, args),
            "RETR": lambda cmd, args: self.retrieve_file(cmd, args),
            "CWD": lambda cmd, args: self.change_directory(cmd, args),
            "PORT": lambda cmd, args: self.set_port(cmd, args),
        }
    
    # Conectar con el servidor
    def connect(self):
        self.client_socket.connect((self.ip_server, self.port))
        response = self.receive_response()
        print(f"{response}")
    
    # Enviar comando al servidor
    def send_command(self, command, args=None):
        if args:
            command = f"{command} {args}"  # Concatenar el comando con los argumentos
        self.client_socket.sendall(f"{command}".encode())
    
    # Recibir una respuesta del servidor
    def receive_response(self):
        response = self.client_socket.recv(1024)
        return response.decode()
    
    # Conectar el socket de datos para transferencia de informacion
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
    
    # Ejecutar comandos
    def execute_command(self, command, args=None):
        if command in ["LIST", "STOR", "RETR", "STOU", "APPE"]:
            return self.handle_data_connection(command, args)
        if command == "USER":
            return self.exec_user(command, args)
        else:
            self.send_command(command, args)  
            return self.receive_response()
    
    # Manejar la conexión de datos para comandos que lo requieren
    def handle_data_connection(self, command, args):
        try:
            self.connect_data_socket()
            
            # Ejecutar el comando
            response = self.command_handlers[command](command, args)
            
            # Se asegura que el socket de datos se cierre correctamente
            if self.data_socket:
                self.data_socket.close()
            
            return response
            
        except Exception as e:
            if self.data_socket:
                self.data_socket.close()
                    
            return f"Error in {command}: {e}"
            
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
          
    # Comando para recibir archivos
    def retrieve_file(self, command, filename):
        Utils.validate_args(command, filename)
        
        # Agregar la carpeta fuente donde se descargara el archivo
        path = os.path.join(self.source_file , filename)
        
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
        
        # Agregar la carpeta fuente desde donde se enviara el archivo
        path = os.path.join(self.source_file , filename)
        
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
                    
        return self.receive_response()
    
    def change_directory(self, command ,path):
        Utils.validate_args(command, path)

        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist"
        
        self.send_command(f"{command}{path}")
        with open(path, 'rb') as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                self.data_socket.sendall(data)

    def set_port(self, command, args):
        Utils.validate_args(command, args)
        if not args.isdigit():
            return f"Error: Invalid port number"
        
        if self.ip_server is not None and self.port is not None:
            ip_parts = self.ip_server.split('.')
            ip_formatted = ','.join(ip_parts)

            p1 = self.port // 256
            p2 = self.port % 256

            self.send_command(f"{command}{ip_formatted},{p1},{p2}")
            print(self.receive_response())
        else:
            print("La dirección IP y el puerto del cliente no están configurados.")
    
    def exec_user(self, cmd, args):
        while True:
            # Enviar comando USER
            self.send_command(cmd , args)
            user_response = self.receive_response()
            
            # Si el usuario no es valido
            if "530" in user_response:
                return user_response
            
            print(user_response)

            pass_input = input("ftp>> ").strip().split()
            pass_cmd , pass_args = Utils.recv_cmd(pass_input)

            # Enviar comando PASS
            self.send_command(pass_cmd, pass_args)
            password_response = self.receive_response()
            break
        
        self.logged_in = "230" in password_response
        return password_response
            
    def log_in(self):
        while True: 
            username = input("Username : ")
            
            # Enviar comando USER
            self.send_command("USER" , username)
            user_response = self.receive_response()
            
            # Si el usuario no es valido
            if "530" in user_response:
                return user_response
            
            print(user_response)
            password = input("Password : ")
            
            # Enviar comando PASS
            self.send_command("PASS", password)
            password_response = self.receive_response()
            print(password_response)
            
            self.logged_in = "230" in password_response  # Autenticacion exitosa
            
            if not self.logged_in:
                print("530 You are not authenticated in the system. Do you want to continue? (y/n) ")
                stay = input().upper().startswith("N")
                if stay:
                    continue
            break
        
    def exec(self):
        if not self.logged_in:
            print("530 You are not authenticated in the system. Available commands are: 'HELP', 'USER','SYST','QUIT'.")

        while True:
            user_input = input("ftp>> ").strip().split()
            cmd , args = Utils.recv_cmd(user_input)
            
            #print(f"Debug: cmd:{cmd}, args:{args}")
            
            if not cmd:
                continue
            
            if not self.logged_in and cmd not in ["HELP" , "USER", "QUIT","SYST"]:
                continue
            
            response = self.execute_command(cmd, args)
            print(f"{response}")
            
            # Verificar si la respuesta es de cierre de conexión
            if response.startswith("221"):
                print("Cerrando la conexión...")
                self.client_socket.close()  
                break
            
            # Verificar si la respuesta es de comando desconocido
            if response.startswith("500"):  
                sug = Utils.Get_suggestion(cmd)
                print(f"Command {cmd} not found, try with {sug}")

    # Metodo para iniciar el cliente
    def ftp_client(self):
        self.connect()    
        self.log_in()
        self.exec()
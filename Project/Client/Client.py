import Utils
import os
import time
from socket import *

class Client:

    user_db = 'user_database.json'
    #Constructor de la clase
    def __init__(self, ip_server, port):
        self.ip_server = ip_server
        self.port = port
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.data_socket = None
        self.logged_in = False
        # Diccionario de comandos y sus funciones correspondientes
        self.command_handlers = {
            "LIST": self.list_file,
            "QUIT": lambda cmd: self.send_command(cmd),
            "RNFR": lambda cmd: self.send_command(cmd),
            "ABOR": lambda cmd: self.send_command(cmd),
            "DELE": lambda cmd: self.send_command(cmd),
            "RMD": lambda cmd: self.send_command(cmd),
            "MKD": lambda cmd: self.send_command(cmd),
            "PWD": lambda cmd: self.send_command(cmd),
            "SITE": lambda cmd: self.send_command(cmd),
            "SYST": lambda cmd: self.send_command(cmd),
            "STAT": lambda cmd: self.send_command(cmd), #Puede o no recibir argumentos, tacto en el server
            "HELP": lambda cmd: self.send_command(cmd), #La misma pincha que Stat, puede o no recibir argumentos
            "NOOP": lambda cmd: self.send_command(cmd),
            "STOR": lambda cmd, args: self.store_file(cmd, args),
            "STOU": lambda cmd, args: self.store_file(cmd, args),
            "RETR": lambda cmd, args: self.retrieve_file(cmd, args),
            "APPE": lambda cmd, args: self.store_file(cmd, args),
            "CWD": lambda cmd, args: self.change_directory(cmd, args),
            "PORT": lambda cmd, args: self.set_port(cmd, args),
            "TYPE": lambda cmd, args: self.set_type(cmd, args),
            "STRU": lambda cmd, args: self.set_stru(cmd, args),
            "MODE": lambda cmd, args: self.set_mode(cmd, args),
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

    def set_type(self, command, type):
        Utils.validate_type(type)
        self.send_command(f"{command}{type}")
        print(self.receive_response())
    
    def set_stru(self, command, stru):
        Utils.validate_stru(stru)
        self.send_command(f"{command}{stru}")
        print(self.receive_response())
    
    def set_mode(self, command, mode):
        Utils.validate_mode(mode)
        self.send_command(f"{command}{mode}")
        print(self.receive_response())
    
    def log_in(self):
        user_db = Utils.load_db()
        while not self.logged_in:
            print("You are not authenticated/registered in the system. Available commands are 'USER', 'HELP', 'LOG'.")
            cmd = input("ftp>> ")
            if cmd == 'HELP':
                self.send_command("HELP")
            else:
                spliter_cmd = cmd.split()
                if len(spliter_cmd) == 2 and spliter_cmd[0] == 'USER':
                    password = input("ftp>> PASS: ")
                    if Utils.authenticate_user(user_db, spliter_cmd[1], password):
                        self.logged_in = True
                        self.send_command(f"USER {spliter_cmd[1]}")
                        self.send_command(f"PASS {password}")
                    else:
                        print("Error: Invalid Username or Password")
                # El comando LOG es una cosa interna nuestra, no hay que llamar al servidor ni nada
                if len(spliter_cmd) == 1 and spliter_cmd[0] == 'LOG':
                    username = input("ftp>> USER: ")
                    userpass = input("ftp>> PASS: ")
                    Utils.add_user(user_db, username, userpass)
                    self.logged_in = True
                else:
                    print("Error: Invalid command")

    #Metodo que llamara a todas las funcionalidades del cliente
    def ftp_client(self):    
        self.logged_in()
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
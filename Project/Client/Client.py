import Utils
import os
import time
from socket import *

class Client:
    unlogged_commands = ["HELP" , "USER", "QUIT","SYST"]

    def __init__(self, ip_server, port, source_file):
        
        self.ip_server = ip_server
        self.port = port
        self.source_file = source_file
        self.logged_in = False

        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.data_socket = None
        
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
    
    # --------------------------   Methods   --------------------------------------------------
    def execute_command(self, command, args=None):
        """
        takes:
            [command]: command to be executed
            [args]   : arguments

        actions:
            .if the command requires to stablish a data connection it calls that method
            .if the command requires any extra actions calls the correspondent method
            .every other command is just sent with it's arguments

        return:
            [string]: the correspondent FTP Server response
        """

        if command in ["LIST", "STOR", "RETR", "STOU", "APPE"]:
            return self.handle_data_connection(command, args)
        
        if command == "USER":
            return self.exec_user(command, args)
        else:
            self.send_command(command, args)  
            return self.receive_response()

    def send_command(self, command, args=None):
        """
        takes:
            [command] : command to be send
            [args]    : string with the arguments
        
        actions:
            .sends the command to the server via client socket
        """
        if args:
            command = f"{command} {args}"  # concat the command with the arguments

        self.client_socket.sendall(f"{command}\r\n".encode())

    def receive_response(self):
        """
        returns a response from the server
        """
        response = self.client_socket.recv(1024)
        return response.decode()

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
    
    def unauthorized_command(self, command):
        return not self.logged_in and cmd not in unlogged_commands
    
    # Conectar el socket de datos para transferencia de informacion
    def connect_data_socket(self):
        """
        actions: 
            .gets the ip and port where the server has started the passive mode
            .connects the data_socket to that ip and port to send/receive data.    
        """
        ip, port = self.enter_passive_mode()
        self.data_socket = socket(AF_INET, SOCK_STREAM)
        self.data_socket.settimeout(5)
        self.data_socket.connect((ip, port))
    
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
                
    #----------------------------  Comandos Especificos   -----------------------------------------
    def exec_user(self, cmd, args):
        """
        takes:
            [cmd] : 'USER' command
            [args]:  the username introduced by the client
        
        actions:
            .sends the 'USER' command
            .if there is any error aborts the login operation
            .if not asks for PASS command, sends it and returns the response
        """
        
        # Sending 'USER' command
        self.send_command(cmd , args)
        user_response = self.receive_response()
            
        # if operation was unsuccesfull
        if not user_response.startswith("331"):
            return user_response
            
        print(user_response)

        while True:
            # Keeps asking for PASS if other command is introduced
            pass_input = input("ftp>> ").strip().split()
            pass_cmd , pass_args = Utils.recv_cmd(pass_input)

            if pass_cmd == "PASS":
                break

        # Sending PASS command
        self.send_command(pass_cmd, pass_args)
        password_response = self.receive_response()
        
        self.logged_in = password_response.startswith("230")
        return password_response

    def list_file(self, command, args=None):
        
        # Sends 'LIST' command
        self.send_command(command)
        ready_response = self.receive_response()

        # if bad response abort the listing operation
        if not ready_response.startswith('150'):
            return ready_response

        print(ready_response)
        
        # receive file's list
        all_data = b""
        while True:
            data = self.data_socket.recv(1024)
            if not data:
                break
            all_data += data

        # print list
        print("Files \n--------------------------")
        print(all_data.decode())

        self.data_socket.close()
        
        return self.receive_response()
          
    def retrieve_file(self, command, filename):
        Utils.validate_args(command, filename)
        
        # Add the source file to the path where the file will be downloaded
        path = os.path.join(self.source_file , filename)
        
        # Sends the command
        self.send_command(f"{command} {filename}")
        ready_response = self.receive_response()

        # if bad response aborts the store operation
        if not ready_response.startswith("150"):
            return ready_response
        
        print(ready_response)
            
        # Downloads the file
        with open(path, 'wb') as f:
            while True:
                data = self.data_socket.recv(1024)
                if not data:
                    break
                f.write(data)
                    
        return self.receive_response()    
        
    def store_file(self, command, filename):
        # Handle 'STOR', 'STOU' and 'APPEND' commands
        Utils.validate_args(command, filename)
        
        # Adds the source folder to the file path
        path = os.path.join(self.source_file , filename)
        
        # Check if the file exists locally
        if not os.path.exists(path):
            return f"Error: File '{filename}' does not exist"
        
        # Send command and wait for response
        self.send_command(f"{command} {filename}")
        ready_response = self.receive_response()

        # if bad response aborts the store operation
        if not ready_response.startswith("150"):
            return ready_response
        
        print(ready_response)

        # Sends file            
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
    
    #-----------------------------   Actions   -----------------------------------------------
    def connect(self):
        """
        actions:
            .uses the client_socket to connect to the FTP server ip and port
            .receives the welcome message and prints it
        """
        self.client_socket.connect((self.ip_server, self.port))
        welcome_msg = self.receive_response()
        print(welcome_msg)
                
    def log_in(self):
        """
        Executes the log_in in a user-friendly way, without needing to use the USER and PASS command
        """
        while True: 

            # Asks for username
            username = input("Username : ")
            
            # Sends 'USER' command
            self.send_command("USER" , username)
            user_response = self.receive_response()
            
            # if operation was unsuccesfull
            if not user_response.startswith("331"):
                return user_response
            
            print(user_response)
            
            # Asks for password
            password = input("Password : ")
            
            # Sends 'PASS' command
            self.send_command("PASS", password)
            password_response = self.receive_response()

            print(password_response)
            
            # Stores login result
            self.logged_in = password_response.startswith("230")
            
            if not self.logged_in:
                # Asks the client if they want to continue without authenticating
                print("530 You are not authenticated in the system. Do you want to continue? (y/n) ")
                stay = input().upper().startswith("N")
                if stay:
                    continue
            break
        
    def exec(self):
        """
        Lets the user send commands to the Server
          .if the user isn't logged in, it can only send a group of commands
          .executes the command and prints the response
          .keeps asking for commands until 'QUIT' is received
          .if the command is unknown uses Levenstein Distance to find the most similar command and suggest it
        """

        if not self.logged_in:
            print("You are not authenticated in the system. Avaiable commands are: 'HELP', 'USER','SYST','QUIT'.")

        while True:
            user_input = input("ftp>> ").strip().split()
            cmd , args = Utils.recv_cmd(user_input)
            
            #print(f"Debug: cmd:{cmd}, args:{args}")
            
            if not cmd:
                continue
            
            if self.unauthorized_command(cmd):
                print("530 You are not authenticated in the system. Avaiable commands are: 'HELP', 'USER','SYST','QUIT'.")
                continue
            
            response = self.execute_command(cmd, args)
            print(f"{response}")
            
            if response.startswith("221"):      # 'QUIT' command response
                print("Shutting down connection...")
                self.client_socket.close()  
                break
            
            if response.startswith("500"):      # Unknown command
                sug = Utils.Get_suggestion(cmd)
                print(f"Command {cmd} not found, try with {sug}")

    def ftp_client(self):
        self.connect()    
        self.log_in()
        self.exec()
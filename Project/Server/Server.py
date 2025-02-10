from socket import *
import os
import platform
import shutil
import time
import Utils

class FTPServer:
    def __init__(self, port):
        self.server_port = port
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.bind(('', self.server_port))
        self.server_socket.listen(1)
        self.conection_socket = None
        self.data_socket = None
        self.username = None
        self.rename_from = None  
        print("Server Ready...")
        
        # Diccionario de comandos y sus funciones correspondientes
        self.command_handlers = {
            "QUIT": self.handle_quit,
            "PASV": self.enter_passive_mode,
            "LIST": self.handle_list,
            "RETR": self.handle_retr,
            "STOR": self.handle_store,
            "NOOP": self.handle_noop,
            "SYST": self.handle_syst,
            "PWD": self.handle_pwd,
            "DELE": self.handle_dele,
            "RNFR": self.handle_rnfr,  
            "RNTO": self.handle_rnto,
            "RMD" : self.handle_rmd,
            "MKD" : self.handle_mkd,   
            "STOU": self.handle_stou,
            "APPE": self.handle_appe,
            "USER": self.handle_user,
        }

    def send_response(self, connection, code, message):
        response = f"{code} {message}\r"
        connection.send(response.encode())
    
    def recv_cmd(self, entry):    
        if not entry:
            return None, None
        
        cmd = entry[0].upper()
        args = ' '.join(entry[1:])  # Unir los argumentos en un solo string
        
        return cmd , args
    def user_file_name(self):
        return "." + self.username
    # ------------ Comandos ------------------------------------------------------
    def handle_quit(self, connection, *args):
        self.send_response(connection, 221, "Goodbye")
    
    def handle_noop(self, connection, *args):
        self.send_response(connection, 200, "No operation performed")
        
    def handle_syst(self, connection, *args):
        os_name = platform.system()  # Obtener el nombre del sistema operativo
        self.send_response(connection, 215, f"{os_name}")
        
    def handle_pwd(self, connection, *args):
        current_directory = os.getcwd()  # Obtener el directorio de trabajo actual
        self.send_response(connection, 257, f'"{current_directory}"')
    
    def handle_dele(self, connection, filename):
        file_path = os.path.join(self.user_file_name(), filename)  # Ruta del archivo a eliminar
        
        try:
            os.remove(file_path)  # Intentar eliminar el archivo
            self.send_response(connection, 250, "File deleted successfully")  
        except FileNotFoundError:
            self.send_response(connection, 550, "File not found")  
        except Exception as e:
            self.send_response(connection, 550, f"Error deleting file: {str(e)}")  
    
    def handle_rmd(self, connection, dir_name):
        file_path = os.path.join(self.user_file_name() , dir_name) # ruta del directorio a eliminar
        try:
            shutil.rmtree(file_path)
            self.send_response(connection, 250, "Directory deleted successfully")
        except FileNotFoundError:
            self.send_response(connection, 550, "File not found")  
        except Exception as e:
            self.send_response(connection, 550, f"Error deleting directory: {str(e)}")
    
    def handle_mkd(self, connection, dir_name):
        file_path = os.path.join(self.user_file_name() , dir_name) # ruta del directorio a crear
        try:
            os.makedirs(file_path, exist_ok=True)
            self.send_response(connection, 250, "Directory created successfully")
        except Exception as e:
            self.send_response(connection, 550, f"Error creating directory: {str(e)}")
    
    
    def handle_rnfr(self, connection, filename):
        self.rename_from = filename     # Almacenar el nombre del archivo a renombrar
        self.send_response(connection, 350, "Ready for RNTO") 

    def handle_rnto(self, connection, new_filename):
        if self.rename_from is None:
            self.send_response(connection, 503, "RNFR required first")  # Error si RNFR no fue llamado
            return
        
        old_file_path = os.path.join(self.user_file_name(), self.rename_from)
        new_file_path = os.path.join(self.user_file_name(), new_filename)
        
        try:
            os.rename(old_file_path, new_file_path) # Renombrar el archivo
            self.send_response(connection, 250, "File renamed successfully")  
        except FileNotFoundError:
            self.send_response(connection, 550, "File not found")  
        except Exception as e:
            self.send_response(connection, 550, f"Error renaming file: {str(e)}")
        finally:
            self.rename_from = None  # Reiniciar la variable de estado
    
    def enter_passive_mode(self, connection, *args):
        self.data_socket = socket(AF_INET, SOCK_STREAM)
        self.data_socket.bind(('', 0))
        self.data_socket.listen(1)
        
        addr = self.data_socket.getsockname()
        ip = addr[0]  
                
        ip_parts = ip.split('.')
        p1 = addr[1] // 256
        p2 = addr[1] % 256
        passive_str = f"({','.join(ip_parts)},{p1},{p2})"
        
        self.send_response(connection, 227, f"Entering Passive Mode {passive_str}")
        
    def handle_list(self, connection, *args):
        client_data, _ = self.data_socket.accept()
            
        files = '\n'.join(os.listdir(self.user_file_name()))
        
        client_data.send(files.encode())
        
        client_data.close()
        self.data_socket.close()
        
        self.send_response(connection, 226, "Transfer complete (File's List)")

    def handle_retr(self, connection, filename):
        file_path = os.path.join(self.user_file_name(), filename)
        
        if not os.path.exists(file_path):
            self.send_response(connection, 550, "File not found")
            return
        
        client_data, _ = self.data_socket.accept()
        
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                client_data.send(data)
            
        client_data.close()
        self.data_socket.close()
        
        self.send_response(connection, 226, "Transfer complete")

    def handle_store(self, connection, filename, mode='wb'):
        file_path = os.path.join(self.user_file_name(), filename)
        
        client_data, _ = self.data_socket.accept()
        with open(file_path, mode) as f:
            while True:
                data = client_data.recv(1024)
                if not data:
                    break
                f.write(data)
                
        client_data.close()
        self.data_socket.close()
        
        self.send_response(connection, 226, f"Transfer complete. File created on server : {filename}")
        
    def handle_stou(self, connection, filename):
        unique_filename = f"{int(time.time())}_{filename}"  # Generar un nombre único para el archivo
        return self.handle_store(connection, unique_filename)   
    
    def handle_appe(self, connection, filename):
        return self.handle_store(connection, filename, mode='ab')
    
    def handle_user(self, connection, username):
        user_db = Utils.load_db()
        if Utils.user_exists(user_db, username):
            self.send_response(connection, 331, "Username is correct, password required to log in.")
            
            command = self.connection_socket.recv(1024).decode().strip().split()
            pass_cmd , password = self.recv_cmd(command)

            if not pass_cmd or pass_cmd != "PASS":
                self.send_response(connection, 503, "Unexpected command: 'PASS' was expected.")
                return

            if not Utils.authenticate_user(user_db, username, password):
                self.send_response(connection, 530, "Login failed, incorrect password.")
                return
            
            self.username = username
            os.makedirs(f".{username}", exist_ok=True)
            self.send_response(connection, 230, "User succesfully logged in.")
        
        else:
            self.send_response(connection, 530, "Login failed, incorrect user.")

        
    def accept_conection(self):
        while True:
            self.connection_socket, _ = self.server_socket.accept()
            self.send_response(self.connection_socket, 220, "Welcome to FTP server")
            self.listen_commands()
            self.connection_socket.close()
    
    def listen_commands(self):
        while True:
            try:
                command = self.connection_socket.recv(1024).decode().strip().split()
                cmd , args = self.recv_cmd(command)
                
                #print(f"Debug: cmd:{cmd}, args:{args}")

                if not self.username and cmd not in ["HELP" , "QUIT" , "USER", "SYST"]:
                    self.send_response(self.conection_socket, 530, "Please log in using USER/PASS commands")
                    continue
                
                if cmd in self.command_handlers:
                    self.command_handlers[cmd](self.connection_socket,args)
                    
                    if(cmd == "QUIT"):
                        break
                else:
                    self.send_response(self.connection_socket, 500, "Unknown command")
            
            except Exception as e:
                print(f"Error: {e}")
                break
                     
if __name__ == "__main__":
    server = FTPServer(12001)
    server.accept_conection()
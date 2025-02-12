from socket import *
import os
import platform
import shutil
import time
import Utils

class FTPServer:
    
    unlogged_commands = ["HELP" , "QUIT" , "USER", "SYST"]
    
    def __init__(self, port):
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.connection_socket = None
        self.data_socket = None
        
        self.server_port = port
        self.username = None
        self.rename_from = None

        self.server_socket.bind(('', self.server_port))
        self.server_socket.listen(1)
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
        """ 
        takes: 
            [connection] : socket used to send the response
            [code]       : response's code (ex. 220)
            [message]    : complementary message for the response (ex. Welcome to FTP Server)

        action:
            .Sends the response via the given socket
        
        returns:
            void
        """
        response = f"{code} {message}\r"
        connection.send(response.encode())
    
    def process_cmd(self, msg):
        """
        takes:
            [msg] : string where the first word is the command and the rest is the argument
        
        returns:
            cmd , args
            [cmd] : command
            [arg] : argument
        """

        if not msg:                     # if there is not message, returns None
            return None, None
        
        msg_parts = msg.split()         # split the message into a list of it's words
        
        cmd = msg_parts[0].upper()      # takes the command
        args = ' '.join(msg_parts[1:])  # takes the rest as argument
        
        return cmd , args

    def unauthorized_command(self, cmd):
        """ 
        takes:
            [cmd] : an FTP command
        
        returns:
            [bool] : if the client is authorized to run the command
            * if the client is not logged in, it can only run a few commands
        """
        return not self.username and cmd not in self.unlogged_commands

    def user_file_name(self):
        return "." + self.username
    # -----------------------------   Commands   ---------------------------------------------
    def handle_quit(self, *args):
        self.send_response(self.connection_socket, 221, "Goodbye")
    
    def handle_noop(self, *args):
        self.send_response(self.connection_socket, 200, "No operation performed")
        
    def handle_syst(self, *args):
        os_name = platform.system()
        self.send_response(self.connection_socket, 215, f"Server OS: {os_name}")
        
    def handle_pwd(self, *args):
        """
        actions:
            . Sends the current working directory
        """
        current_directory = os.getcwd()
        self.send_response(self.connection_socket, 257, f'"{current_directory}{self.user_file_name()}"')
    
    def handle_dele(self, filename):
        """
        takes:
            [filename] : name of the file to delete

        actions:
            . Finds the file in the user's directory and deletes it 
        """
        file_path = os.path.join(self.user_file_name(), filename)  
        
        try:
            os.remove(file_path)
            self.send_response(self.connection_socket, 250, "File deleted successfully")  
        except FileNotFoundError:
            self.send_response(self.connection_socket, 550, "File not found")  
        except Exception as e:
            self.send_response(self.connection_socket, 550, f"Error deleting file: {str(e)}")  
    
    def handle_rmd(self, dir_name):
        """
        takes:
            [dir_name]: name of the directory to delete
        actions:
            . Finds the directory and deletes it
        """
        file_path = os.path.join(self.user_file_name() , dir_name)
        
        try:
            shutil.rmtree(file_path)
            self.send_response(self.connection_socket, 250, "Directory deleted successfully")
        except FileNotFoundError:
            self.send_response(self.connection_socket, 550, "File not found")  
        except Exception as e:
            self.send_response(self.connection_socket, 550, f"Error deleting directory: {str(e)}")
    
    def handle_mkd(self, dir_name):
        """
        takes:
            [dir_name]: name of the directory to create
        
        actions:
            . Creates a directory with the given name
        """
        file_path = os.path.join(self.user_file_name() , dir_name)
        
        try:
            os.makedirs(file_path, exist_ok=True)
            self.send_response(self.connection_socket, 250, "Directory created successfully")
        except Exception as e:
            self.send_response(self.connection_socket, 550, f"Error creating directory: {str(e)}")

    def handle_rnfr(self, filename):
        """
        takes:
            [filename]: name of the file to rename
        
        actions:
            . Sets the name of the file to be rename it
        """
        self.rename_from = filename     
        self.send_response(self.connection_socket, 350, "Ready for RNTO") 

    def handle_rnto(self, new_filename):
        """
        takes:
            [new_filename]: new name of the file to be renamed
        
        actions:
            . RNFR must hae been called first
            . changes the old name for the new one
        """
        if self.rename_from is None:
            self.send_response(self.connection_socket, 503, "RNFR required first")
            return
        
        old_file_path = os.path.join(self.user_file_name(), self.rename_from)
        new_file_path = os.path.join(self.user_file_name(), new_filename)
        
        try:
            os.rename(old_file_path, new_file_path)
            self.send_response(self.connection_socket, 250, "File renamed successfully")  
        except FileNotFoundError:
            self.send_response(self.connection_socket, 550, "File not found")  
        except Exception as e:
            self.send_response(self.connection_socket, 550, f"Error renaming file: {str(e)}")
        finally:
            self.rename_from = None  # Restarts the status variable
    
    def enter_passive_mode(self, *args):
        """
        actions:
            . initializates the data socket
            . binds it to a random port
            . returns the ip an port in an 227 response
        """
        self.data_socket = socket(AF_INET, SOCK_STREAM)
        self.data_socket.bind(('', 0))
        self.data_socket.listen(1)
        
        addr = self.data_socket.getsockname()
        ip = addr[0]  
                
        ip_parts = ip.split('.')
        p1 = addr[1] // 256
        p2 = addr[1] % 256
        passive_str = f"({','.join(ip_parts)},{p1},{p2})"
        
        self.send_response(self.connection_socket, 227, f"Entering Passive Mode {passive_str}")
        
    def handle_list(self, *args):
        """
        actions:
            . List all files on the root directory
            . After the transference sends an 226 response
        """
        client_data, _ = self.data_socket.accept()
        self.send_response(self.connection_socket, 150 ,f"Opening data connection for LIST")
            
        files = '\n'.join(os.listdir(self.user_file_name()))
        
        client_data.send(files.encode())
        
        client_data.close()
        self.data_socket.close()
        
        self.send_response(self.connection_socket, 226, "Transfer complete (File's List)")

    def handle_retr(self, filename):
        """
        takes:
            [filename]
        
        actions:
            . Search for a file and sends it to client
            . If the file is not found sends an 550 response
            . After the transference it sends an 226 response
        """
        file_path = os.path.join(self.user_file_name(), filename)
        
        if not os.path.exists(file_path):
            self.send_response(self.connection_socket, 550, "File not found")
            return
        
        client_data, _ = self.data_socket.accept()
        self.send_response(self.connection_socket, 150 ,f"Opening data connection for {filename}")
        
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                client_data.send(data)
            
        client_data.close()
        self.data_socket.close()
        
        self.send_response(self.connection_socket, 226, "Transfer complete")
    
    def handle_stou(self, filename):
        """Stores the file with a unique name adding a timestamp to it"""
        unique_filename = f"{int(time.time())}_{filename}"  
        return self.handle_store(unique_filename)   
    
    def handle_appe(self, filename):
        """ Stores the file, if it already exists appends the data to the file. """
        return self.handle_store(filename, mode='ab')

    def handle_store(self, filename, mode='wb'):
        """
        takes:
            [filename]: name of the file where data will be stored
            [mode]    : open mode of the file
        
        actions:
            . Handles the STOR, STOU and APPEND commands
            . STOR and STOU use (wb), APPEND uses (ab)
            . Stablishes a data connection and sends an 150 response waiting for the file
            . Receives the file and sends back an 226 response
        """
        file_path = os.path.join(self.user_file_name(), filename)
        
        client_data, _ = self.data_socket.accept()
        self.send_response(self.connection_socket, 150 ,f"Opening data connection for {filename}")
        
        # receives the file      
        with open(file_path, mode) as f:
            while True:
                data = client_data.recv(1024)
                if not data:
                    break
                f.write(data)
                
        client_data.close()
        self.data_socket.close()
        
        self.send_response(self.connection_socket, 226, f"Transfer complete. File created on server : {filename}")
    
    def handle_user(self, username):
        """
        Method to process the "USER" command
        takes:
            [username]
        
        actions:
            .searches the username on the User's Database
        
        actions:
            .if username is found sends an 331 response requesting the PASS command
                .if other command is sent, sends an 503 response
                .if the password is incorrect sends an 530 response
                .if the password is right, sets the username, creates a directory for the user and sends a 230 response
            .if username is not found sends an 530 response 
        """
        
        user_db = Utils.load_db()   # loads the database
        
        if Utils.user_exists(user_db, username): # searches for the user
            
            # User OK, request PASS command
            self.send_response(self.connection_socket, 331, "Username is correct, password required to log in.")
            
            # receives command
            command = self.connection_socket.recv(1024).decode().strip()
            pass_cmd , password = self.process_cmd(command)

            # checks if the command is 'PASS'
            if not pass_cmd or pass_cmd != "PASS":
                self.send_response(self.connection_socket, 503, "Unexpected command: 'PASS' was expected.")
                return
            
            # checks if the password is correct
            if not Utils.authenticate_user(user_db, username, password):
                self.send_response(self.connection_socket, 530, "Login failed, incorrect password.")
                return
            
            # logs in the user and creates a directory(if it does not exist already)
            self.username = username
            os.makedirs(f".{username}", exist_ok=True)
            self.send_response(self.connection_socket, 230, "User succesfully logged in.")
        
        else:
            self.send_response(self.connection_socket, 530, "Login failed, incorrect user.")

    #----------------------------------   Actions   ------------------------------------------------
    def ftp_server(self):
        """
        actions:
            . Waits for incoming client's connection requests
            . Accepts the connection( via connection_socket)
            . Starts listening for commands from the client
            . When the client stops sending commands, closes the connection_socket
        """
        while True:
            self.accept_connection()
            self.listen_commands()
            self.connection_socket.close()
    
    def accept_connection(self):
        """
        actions:
            . Accepts an incoming connection from a client
            . Sends the client a confirmation response
        """
        self.connection_socket, _ = self.server_socket.accept()
        self.send_response(self.connection_socket, 220, "Welcome to FTP server")

    def listen_commands(self):
        """
        actions:
            . Receives commands from the client
            . Executes the commands
            . Each command sends it's responses to the client 
        """
        while True:
            try:
                # Receiving and proccessing the command
                command = self.connection_socket.recv(1024).decode().strip()
                cmd , args = self.process_cmd(command)
                
                #print(f"Debug: cmd:{cmd}, args:{args}")

                # checks if the client is authorized to run the command
                if self.unauthorized_command(cmd) :
                    self.send_response(self.connection_socket, 530, "Please log in using USER/PASS commands")
                    continue
                
                # executes the corresponding method
                if cmd in self.command_handlers: 
                    self.command_handlers[cmd](args)
                    
                    # stops when 'QUIT' command is received
                    if(cmd == "QUIT"):
                        break
                else:
                    self.send_response(self.connection_socket, 500, "Unknown command")
            
            except Exception as e:
                print(f"550 Error: {e}")
                break
                     
if __name__ == "__main__":
    server = FTPServer(12001)
    server.ftp_server()
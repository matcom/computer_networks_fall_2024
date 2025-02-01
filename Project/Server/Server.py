from socket import *
import os

class FTPServer:
    def __init__(self, port):
        self.server_port = port
        self.server_socket = socket(AF_INET, SOCK_STREAM)
        self.server_socket.bind(('', self.server_port))
        self.server_socket.listen(1)
        self.conection_socket = None
        self.data_socket = None
        print("Server Ready...")
        
        # Diccionario de comandos y sus funciones correspondientes
        self.command_handlers = {
            "QUIT": self.handle_quit,
            "PASV": self.enter_passive_mode,
            "LIST": self.handle_list,
            "RETR": self.handle_retr,
            "STOR": self.handle_stor
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
    
    def handle_quit(self, connection, *args):
        self.send_response(connection, 221, "Goodbye")
    
    def enter_passive_mode(self, connection, *args):
        self.data_socket = socket(AF_INET, SOCK_STREAM)
        self.data_socket.bind(('127.0.0.1', 0))  # Bind explicitly to localhost
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
            
        files = '\n'.join(os.listdir('./.home'))
        
        client_data.send(files.encode())
        
        client_data.close()
        self.data_socket.close()
        
        self.send_response(connection, 226, "Transfer complete (File's List)")

    def handle_retr(self, connection, filename):
        file_path = os.path.join('./.home', filename)
        
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

    def handle_stor(self, connection, filename):
        path = "./.home/" + filename
        
        client_data, _ = self.data_socket.accept()
        
        with open(path, 'wb') as f:
            while True:
                data = client_data.recv(1024)
                if not data:
                    break
                f.write(data)
                
        client_data.close()
        self.data_socket.close()
        
        self.send_response(connection, 226, "Transfer complete")
        
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
    server = FTPServer(12000)
    server.accept_conection()
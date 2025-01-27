import Utils
from socket import *

class Client:

    #Constructor de la clase
    def __init__(self, ip_server, port):
        self.ip_server = ip_server
        self.port = port
        self.client_socket = socket(AF_INET, SOCK_STREAM)
        self.data_socket = None
    
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
        self.client_socket.sendall(f"{command}\r\n".encode())
        return self.receive_response()
    
    #Entrar en modo pasivo
    def enter_passive_mode(self):
        response = self.send_command("PASV")
        start = response.find('(') + 1
        end = response.find(')')
        data = response[start:end].split(',')
        ip = '.'.join(data[:4])
        port = int(data[4]) * 256 + int(data[5])
        return ip, port
    
    #Salir y cerrar la concexion
    def quit(self, command):
        self.send_command("QUIT")
        self.client_socket.close()
        print("Close Conection...")

    #Comando para listar archivos
    def list_file(self, command):
        ip, port = self.enter_passive_mode()
        self.data_socket = socket(AF_INET, SOCK_STREAM)
        self.data_socket.connect((ip, port))
        self.send_command("LIST")
        data = self.data_socket.recv(1024)
        self.data_socket.close()
        return data.decode()
    
    #Comando para recibir archivos
    def retrieve_file(self, command):
        filename = command.split()[1]
        ip, port = self.enter_passive_mode()
        self.data_socket = socket(AF_INET, SOCK_STREAM)
        self.data_socket.connect((ip, port))
        self.send_command(f"RETR {filename}")

        with open(filename, 'wb') as f:
            while True:
                data = self.data_socket.recv(1024)
                if not data:
                    break
                f.write(data)
        self.data_socket.close()
        print(f"The file {filename} downloaded succesfully")

    #Comando para Updatear un archivo
    def store_file(self, command):
        filename = command.split()[1]
        ip, port = self.enter_passive_mode()
        self.data_socket = socket(AF_INET, SOCK_STREAM)
        self.data_socket.connect((ip, port))
        self.send_command(f"STOR {filename}")

        with open(filename, 'rb') as f:
            while True:
                data = f.read(4096)
                if not data:
                    break
                self.data_socket.sendall(data)
        self.data_socket.close()
        print(f"The file {filename} uploaded succesfully")
    
    Commands_Methods= {
        "LIST": list_file,
        "STOR": store_file,
        "RETR": retrieve_file,
        "QUIT": quit,
    }

    #Metodo que llamara a todas las funcionalidades del cliente
    def ftp_client(self):
        while True:
            _input = input("ftp>> ").strip()
            command = _input.split()[0].upper()
            if command in self.Commands_Methods.keys():
                self.Commands_Methods[command](_input)
                self.send_command(command)
            else:
                sug = Utils.Calculate_Lev(command)
                print(f"Command {command} not found, prove with {sug}")
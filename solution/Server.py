import socket
import threading

class IRCServer:
    def __init__(self, host='0.0.0.0', port=6667):
        self.host = host
        self.port = port
        self.clients= {}
        self.channels = {'General': []}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Servidor IRC escuchando en {self.host}:{self.port}")

    def start(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Nueva conexion desde {client_address}")
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.daemon = True
            client_handler.start()


    def handle_client(self, client_socket):
        client_socket.sendall("Bienvenido al servidor IRC local\r\n".encode())
        self.channels["General"].append(client_socket)
        client_socket.sendall(f"Te has unido al canal General \r\n".encode())

        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            data = data.decode().strip()
            print(f"Recibido: {data}")
            response = self.process_command(client_socket, data)
            if response:
                client_socket.sendall((response + "\r\n").encode())

        client_socket.close()
        del self.clients[client_socket]
        self.remove_client_from_channels(client_socket)
        print("Cliente desconectado")        


    def process_command(self, client_socket, data):
        parts = data.split(" ", 1)
        command = parts[0]
        argument = parts[1] if len(parts) > 1 else ""

        if command == "NICK":
            return self.change_nick(client_socket, argument)
        elif command == "USER":
            return "Usuario registrado."
        elif command == "JOIN":
            return self.join_channel(client_socket, argument)
        elif command == "PART":
            return self.part_channel(client_socket, argument)
        elif command == "PRIVMSG":
            return self.send_private_message(client_socket, argument)
        elif command == "NOTICE":
            return self.send_notice(client_socket, argument)
        elif command == "LIST":
            return self.list_channels()
        elif command == "NAMES":
            return self.list_users(argument)
        elif command == "WHOIS":
            return self.whois_user(argument)
        elif command == "TOPIC":
            return self.show_topic(argument)
        elif command == "QUIT":
            return "Desconectado del servidor."
        else:
            return self.send_private_message(client_socket, f'General {command} {argument}')


    def change_nick(self, client_socket, new_nick):
        for sock, nick in self.clients.items():
            if nick == new_nick and sock != client_socket:
                return "Error, por favor seleccione otro nickname"
        self.clients[client_socket]= new_nick
        return f"Tu nuevo nick es {new_nick}"


    def join_channel(self, client_socket, channel):
        if channel not in self.channels:
            self.channels[channel]= []
        if client_socket in self.channels[channel]:
            return "El cliente ya está en el canal."
        self.channels[channel].append(client_socket)
        return f"Unido al canal {channel}."

    def part_channel(self, client_socket, channel):
        if channel in self.channels and client_socket in self.channels[channel]:
            self.channels[channel].remove(client_socket)
            return f"Saliste de {channel}."
        return "Error: No estás en ese canal."

    def send_private_message(self, client_socket, argument):
        parts = argument.split(" ", 1)
        if len(parts) < 2:
            return "Error: Formato incorrecto"
        target, message = parts
        sender = self.clients[client_socket]
        c= [client for _ , client in self.clients.items()]
        # Mensaje a un usuario
        if target in c:
            destination_sock= None
            for sock, client in self.clients.items():
                if client== target: destination_sock= sock
            destination_sock.sendall((f"[Mensaje privado de {sender}] {message}\r\n").encode())
            return "Mensaje enviado"

        # Mensaje a un canal
        elif target in self.channels:
            if client_socket not in self.channels[target]:
                return "Error: No estás en este canal"
            
            for member in self.channels[target]:
                if member != client_socket:  # No reenviar el mensaje al emisor
                    member.sendall((f"[{target}] Mensaje de {sender}: {message}\r\n").encode())
            return f"Mensaje enviado a {target}"

        return "Error: Usuario o canal no encontrado"

    def send_notice(self, client_socket, argument):
        parts = argument.split(" ", 1)
        if len(parts) < 2:
            return "Error: Formato incorrecto"
        target, message = parts
        sender = self.clients[client_socket]
        # Mensaje a un canal
        if target in self.channels:
            if client_socket not in self.channels[target]:
                return "Error: No estás en este canal"
            
            for member in self.channels[target]:
                if member != client_socket:  # No reenviar el mensaje al emisor
                    member.sendall((f"[{target}] Notificación de {sender}: {message}\r\n").encode())
            return f"Mensaje enviado a {target}"

        return "Error: Usuario o canal no encontrado"


    def list_channels(self):
        channels= ", ".join(self.channels.keys())
        return f"Lista de Canales: {channels}" 

    def list_users(self, channel):
        if channel in self.channels:
            list_users = ", ".join(str(self.clients[key]) for key in self.channels[channel] if key in self.clients)
            return f"Usuarios en {channel}: {list_users}"
        return "Error: Canal no encontrado"

    def whois_user(self, user):
        if user in [client for sock, client in self.clients.items()]:         
            for channel in self.channels:
                for user_socket in self.channels[channel]:
                    if self.clients[user_socket] == user:
                        user_socket.sendall((f"Usuario {user} en el canal {channel}\r\n").encode())

            return "Lista Completada"                        
        else: return 'Usuario no encontrado'                


    def show_topic(self, argument):
        parts = argument.split(" ", 1)
        if len(parts) < 1:
            return "Error: Debes proporcionar un canal"
        channel= parts[0]
        if channel in self.channels:
            return f"El Topic del canal channels es {self.channels[channel]}"
        
        return "Canal no encontrado"
        

    def remove_client_from_channels(self, client_socket):
        for channel in self.channels:
            if client_socket in self.channels[channel]:
                self.channels[channel].remove(client_socket)

if __name__ == "__main__":
    server = IRCServer()
    server.start()

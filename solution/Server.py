import socket
import threading
from User import User
from Channel import Channel

class IRCServer:
    def __init__(self, host='0.0.0.0', port=6667):
        self.host = host
        self.port = port
        self.clients= []
        self.channels= {'General': Channel('General')}
        self.channel_modes = {
            'o': 'operator privileges (op/deop)',
            't': 'topic settable by channel operator only',
            'm': 'moderated channel',
        }
        
        self.user_modes = {
            'i': 'invisible',
        }
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
        elif command == "MODE":
            return self.handle_mode(client_socket, argument)
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
            return self.whois_user(client_socket, argument)
        elif command == "KICK":
            return self.kick_user(client_socket, argument)
        elif command == "TOPIC":
            return self.handle_topic(client_socket, argument)
        elif command == "QUIT":
            return "Desconectado del servidor."
        else:
            return self.send_private_message(client_socket, f'General {command} {argument}')


    def change_nick(self, client_socket, new_nick):
        new_cli = User(client_socket, new_nick)
        cli = None
        for client in self.clients:
            if client.nick == new_nick and client.socket != client_socket:
                return "Error, por favor seleccione otro nickname"
            if client.socket == client_socket:
                cli = client
                
        if cli: 
            self.clients.remove(cli);
            self.clients.append(new_cli)
            for _, channel in self.channels.items():
                if channel.is_on_channel(cli):
                    if channel.is_operator(cli):
                        channel.add_operator(new_cli)
                    channel.remove_user(cli)
                    channel.add_user(new_cli)    
        else: 
            self.clients.append(new_cli)  
            self.channels['General'].add_user(new_cli)    

        return f"Tu nuevo nick es {new_nick}"


    def join_channel(self, client_socket, channel):
        client = next((item for item in self.clients if item.socket== client_socket), None)
        if channel not in self.channels:
            self.channels[channel]= Channel(channel)
            self.channels[channel].add_operator(client)
            return f"Unido al canal {channel}."
        if self.channels[channel].is_on_channel(client):
            return "El cliente ya está en el canal."
        self.channels[channel].add_user(client)
        self.channels[channel].broadcast(f"El usuario {client.nick} se ha unido al canal {channel}", client)
        return f"Unido al canal {channel}."


    def part_channel(self, client_socket, channel):
        client = next((item for item in self.clients if item.socket== client_socket), None)
        if channel in self.channels and self.channels[channel].is_on_channel(client):
            self.channels[channel].remove_user(client)
            self.channels[channel].broadcast(f"El usuario {client.nick} ha salido del canal {channel}")
            return f"Saliste de {channel}."
        return "Error: No estás en ese canal."

    # Envia un mensaje ya sea a un usuario o a un canal
    def send_private_message(self, client_socket, argument):
        parts = argument.split(" ", 1)
        if len(parts) < 2:
            return "Error: Formato incorrecto"
        target, message = parts
        sender = next((item for item in self.clients if item.socket== client_socket), None)
        c = [client.nick for client in self.clients]
        
        # Mensaje a un usuario
        if target in c:
            destination_sock = None
            for client in self.clients:
                if client.nick == target: 
                    destination_sock = client.socket
            destination_sock.sendall((f"[Mensaje privado de {sender.nick}] {message}\r\n").encode())
            return "Mensaje enviado"
        
        # Mensaje a un canal
        elif target in self.channels:
            if not self.channels[target].is_on_channel(sender):
                return "Error: No estás en este canal"
            
            self.channels[target].broadcast(f"[{target}] Mensaje de {sender.nick}: {message}", sender)
            return f"Mensaje enviado a {target}"

        # Si no es ni usuario ni canal, devolver mensaje de error
        return "Error: No hay ningún usuario con ese nombre" if target not in self.channels else "Error: Usuario o canal no encontrado"

    # Envía un notice a un canal específico
    def send_notice(self, client_socket, argument):
        parts = argument.split(" ", 1)
        if len(parts) < 2:
            return "Error: Formato incorrecto"
        target, message = parts
        sender = next((item for item in self.clients if item.socket == client_socket), None)
        # Mensaje a un canal
        if target in self.channels:
            if not self.channels[target].is_on_channel(sender):
                return "Error: No estás en este canal"
            
            self.channels[target].broadcast(f"[{target}] Notificación de {sender.nick}: {message}", sender)
            return f"Mensaje enviado a {target}"

        return "Error: Usuario o canal no encontrado"


    def list_channels(self):
        channels= ", ".join(self.channels.keys())
        return f"Lista de Canales: {channels}" 

    def list_users(self, channel):
        if channel in self.channels:
            list_users = ", ".join(str(client.nick) for client in self.channels[channel].users if client in self.clients)
            return f"Usuarios en {channel}: {list_users}"
        return "Error: Canal no encontrado"

    def whois_user(self,client_socket, user):
        client = next((item for item in self.clients if item.socket == client_socket), None)
        if client and client.visibility:         
            for _, channel in self.channels.items():
                if channel.is_on_channel(client):
                    client.send_message(f"Usuario {user} en el canal {channel.name}")
            return "Lista Completada"              
        else: return 'Error: Usuario no visible o encontrado'                

    def handle_topic(self, client_socket, argument):
        try:
            parts= argument.split(" ")
            channel= parts[0]
            if len(parts)>1:
                new_topic = " ".join(parts[1:])
                return self.change_topic(client_socket, channel, new_topic)
            return self.show_topic(channel)
        except IndexError:
            return 'Error: Uso correcto /topic <channel> [new_topic]'


    def change_topic(self, client_socket, channel, new_topic):
        if not channel in self.channels:
            return 'Error: Canal no encontrado'
        
        client = next((item for item in self.clients if item.socket == client_socket), None)

        if not self.channels[channel].is_on_channel(client):
            return f'Error: No perteneces al canal {channel}'
        
        if self.channels[channel].t and not self.channels[channel].is_operator(client):
            return f'Error: No tienes permiso para cambiar el topic del canal {channel}'
        
        self.channels[channel].topic = new_topic
        self.channels[channel].broadcast(f'El usuario {client.nick} ha cambiado el topic del canal {channel} a {new_topic}', client)
        return f'Topic del canal {channel} cambiado a {new_topic}'


    def show_topic(self, channel):
        if channel in self.channels:
            return f"El Topic del canal {channel} es: {self.channels[channel].topic}"
        
        return "Error: Canal no encontrado"
        
    def kick_user(self, client_socket, argument):
        try:    
            parts = argument.split(" ", 2)
            channel = parts[0]
            user = parts[1]
            reason = parts[2] if len(parts) > 2 else "No reason given"    
            sender = next((item for item in self.clients if item.socket == client_socket), None)
            addressee= next((item for item in self.clients if item.nick == user), None)
            if channel in self.channels:
                if self.channels[channel].is_on_channel(sender):
                    if self.channels[channel].is_on_channel(addressee):
                        if self.channels[channel].is_operator(sender):
                            self.channels[channel].remove_user(addressee)
                            addressee.send_message(f'Has sido expulsado del canal {channel} por {reason}')
                            self.channels[channel].broadcast(f'El usuario {user} ha sido expulsado de {channel} por {reason}', sender)
                            return f'Usuario {user} expulsado del canal {channel}'
                        return 'Error: No tienes permiso'
                    return f'Error: El usuario {user} no está en el canal {channel}'  
                return f'Error: No perteneces al canal {channel}' 
            return f'Error: Canal no encontrado'
        except IndexError:
            return "Error: Uso correcto: /kick <canal> <usuario> [motivo]"


    def remove_client_from_channels(self, client_socket):
        client = next((item for item in self.clients if item.socket == client_socket), None)
        for _, channel in self.channels.items():
            channel.remove_user(client)


    def handle_mode(self, client_socket, argument):
        """Maneja el comando MODE"""
        try:
            parts = argument.split()
            target = parts[1]
            modes = parts[2] if len(parts) > 2 else ""
            params = parts[3:] if len(parts) > 3 else []

            if target.startswith('#'):
                self.handle_channel_mode(client_socket, target, modes, params)
            else:
                self.handle_user_mode(client_socket, target, modes)
        except Exception as e:
            return "Error: Comando MODE incorrecto"


    def handle_channel_mode(self, client_socket, channel, modes, params):
        """Maneja modos de canal"""
        if channel not in self.channels:
            return "Error :Canal no encontrado"

        client = next((item for item in self.clients if item.socket == client_socket), None)
        # Verificar si el usuario es operador del canal
        if not self.channels[channel].is_operator(client):
            return f"Error: No eres operador del canal {channel}"

        param_index = 0
        for i, mode in enumerate(modes[1:]):  # Skip the +/- character
            if mode == 'o': 
                if param_index >= len(params):
                    return 'Error: No hay suficientes parametros'
                param = params[param_index]
                param_index += 1
                
                if modes[0] == '+':
                    if mode == 'o':
                        self.channels[channel].add_operator(param)
                else:  # modes[0] == '-'
                    if mode == 'o':
                        self.channels[channel].remove_operator(param)
            elif mode == 't':
                if modes[0] == '+':
                    self.channels[channel].t= True
                else:
                    self.channels[channel].t= False  

            elif mode == 'm':  
                if modes[0] == '+':
                    self.channels[channel].m= True
                else:
                    self.channels[channel].m= True

            else: return f'Error: Comando {mode} no soportado'    

        return 'Operación Exitosa'    



    def handle_user_mode(self, client_socket, target, modes):
        """Maneja modos de usuario"""
        if target not in [client.nick for client in self.clients]:
            return 'Error: Usuario no encontrado'

        client = next((item for item in self.clients if item.socket == client_socket), None)
        # Un usuario solo puede cambiar sus propios modos
        if client.nick != target:
            return 'Error: Un usuario solo puede cambiar sus propios modos'
        
        self.clients.remove(client)

        for i, mode in enumerate(modes[1:]):  # Skip the +/- character
            if mode == 'i':
                if modes[0] == '+':
                    client.visibility = True
                else:
                    client.visibility = False
            else: return f'Error: Comando {mode} no soportado'   

        self.clients.append(client)
        return 'Operación Exitosa'


if __name__ == "__main__":
    server = IRCServer()
    server.start()

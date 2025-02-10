import socket
import threading
from User import User
from Channel import Channel

class IRCServer:
    def __init__(self, host='0.0.0.0', port=6667):
        self.host = host
        self.port = port
        self.clients= []
        self.channels= {'#General': Channel('General')}
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

        self.NUMERIC_REPLIES = {
            '001': 'Bienvenido al servidor IRC',
            '331': 'No hay topic establecido',
            '332': 'El topic es: %s',
            '353': 'Lista de usuarios en el canal',
            '366': 'Fin de la lista de usuarios',
            '401': 'Usuario/Canal no encontrado',
            '403': 'Canal no encontrado',
            '404': 'No puedes enviar mensajes a este canal',
            '421': 'Comando desconocido',
            '433': 'Nickname ya está en uso',
            '441': 'Usuario no está en el canal',
            '442': 'No estás en ese canal',
            '461': 'Faltan parámetros',
            '472': 'Modo desconocido',
            '482': 'No eres operador del canal',
            '502': "Un usuario solo puede cambiar sus propios modos"
        }

    def start(self):
        while True:
            client_socket, client_address = self.server_socket.accept()
            print(f"Nueva conexion desde {client_address}")
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket,))
            client_handler.daemon = True
            client_handler.start()


    def handle_client(self, client_socket):
        """Maneja la conexión de un cliente."""
        # Mensaje de bienvenida con código 001
        client_socket.sendall(":001 :Bienvenido al servidor IRC local\r\n".encode())
        # Notificación de unión al canal General
        client_socket.sendall("Te has unido al canal #General\r\n".encode())

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
        client = next((item for item in self.clients if item.socket == client_socket), None)
        self.clients.remove(client)
        self.remove_client_from_channels(client_socket)
        print("Cliente desconectado")        


    def process_command(self, client_socket, data):
        parts = data.split(" ", 1)
        command = parts[0]
        argument = parts[1] if len(parts) > 1 else ""
        
        sender = next((item for item in self.clients if item.socket == client_socket), None)
        
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
            return f":{sender.nick} QUIT :Leaving"
        else:
            return f":421 {sender.nick} {command} :Unknown command"


    def change_nick(self, client_socket, new_nick):
        new_cli = User(client_socket, new_nick)
        cli = None
        for client in self.clients:
            if client.nick == new_nick and client.socket != client_socket:
                return f':433 {client.nick} :{self.NUMERIC_REPLIES['433']}'
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
            return f":{cli.nick} NICK {new_nick}"         
        else: 
            self.clients.append(new_cli)  
            self.channels['#General'].add_user(new_cli)    
            return f":Usuario NICK {new_nick}"


    def join_channel(self, client_socket, channel):
        client = next((item for item in self.clients if item.socket== client_socket), None)
        if channel not in self.channels:
            self.channels[channel]= Channel(channel)
            self.channels[channel].add_operator(client)
            return f"Te has unido al canal {channel}."
        if self.channels[channel].is_on_channel(client):
            return "El cliente ya está en el canal."
        self.channels[channel].add_user(client)
        self.channels[channel].broadcast(f":{client.nick}! JOIN {channel}", client)
        return f"Te has unido al canal {channel}."


    def part_channel(self, client_socket, channel):
        client = next((item for item in self.clients if item.socket== client_socket), None)
        if channel in self.channels and self.channels[channel].is_on_channel(client):
            self.channels[channel].remove_user(client)
            self.channels[channel].broadcast(f":{client.nick}! PART #{channel}")
            return f"Saliste de {channel}."
        return f':442 :{self.NUMERIC_REPLIES['442']}'

    # Envia un mensaje ya sea a un usuario o a un canal
    def send_private_message(self, client_socket, argument):
        parts = argument.split(" ", 1)
        if len(parts) < 2:
            return f':sever 461 :{self.NUMERIC_REPLIES['461']}'
        target, message = parts
        sender = next((item for item in self.clients if item.socket== client_socket), None)
        c = [client.nick for client in self.clients]
        
        # Mensaje a un usuario
        if target in c:
            destination_sock = None
            for client in self.clients:
                if client.nick == target: 
                    destination_sock = client.socket
            destination_sock.sendall((f":{sender.nick}! PRIVMSG {target} {message}\r\n").encode())
            return "Mensaje enviado"
        
        # Mensaje a un canal
        elif target in self.channels:
            if not self.channels[target].is_on_channel(sender):
                return f":442 :{self.NUMERIC_REPLIES['442']}"
            
            self.channels[target].broadcast(f":{sender.nick}! PRIVMSG {target} {message}", sender)
            return f"Mensaje enviado a {target}"

        # Si no es ni usuario ni canal, devolver mensaje de error
        return f':401 :{self.NUMERIC_REPLIES['401']}'

    # Envía un notice a un canal específico
    def send_notice(self, client_socket, argument):
        parts = argument.split(" ", 1)
        if len(parts) < 2:
            return f':461 :{self.NUMERIC_REPLIES['461']}'
        target, message = parts
        sender = next((item for item in self.clients if item.socket == client_socket), None)
        # Mensaje a un canal
        if target in self.channels:
            if not self.channels[target].is_on_channel(sender):
                return f':442 :{self.NUMERIC_REPLIES['442']}'
            
            self.channels[target].broadcast(f":{sender.nick} NOTICE {target} {message}", sender)
            return f"Mensaje enviado a {target}"

        return  f':401 :{self.NUMERIC_REPLIES['401']}'


    def list_channels(self):
        channels= " ".join(self.channels.keys())
        return f"Lista de Canales: {channels}" 

    def list_users(self, channel):
        if channel in self.channels:
            list_users = " ".join(str(client.nick) for client in self.channels[channel].users if client in self.clients)
            return f":353 {channel} :{list_users}"
        return f':401 :{self.NUMERIC_REPLIES['401']}'

    def whois_user(self,client_socket, user):
        client = next((item for item in self.clients if item.nick == user), None)
        if client and client.visibility:         
            return f':312 host:{client_socket.getpeername()[0]} nick:{client.nick}'
        else: return f':401 :{self.NUMERIC_REPLIES['401']}'              

    def handle_topic(self, client_socket, argument):
        try:
            parts= argument.split(" ")
            channel= parts[0]
            if len(parts)>1:
                new_topic = " ".join(parts[1:])
                return self.change_topic(client_socket, channel, new_topic)
            return self.show_topic(client_socket, channel)
        except IndexError:
            return 'Error: Uso correcto /topic <channel> [new_topic]'


    def change_topic(self, client_socket, channel, new_topic):
        if not channel in self.channels:
            return  f':401 :{self.NUMERIC_REPLIES['401']}'
        
        client = next((item for item in self.clients if item.socket == client_socket), None)

        if not self.channels[channel].is_on_channel(client):
            return f':442 {channel} :{self.NUMERIC_REPLIES['442']}'
        
        if self.channels[channel].t and not self.channels[channel].is_operator(client):
            return f":482 {channel} :{self.NUMERIC_REPLIES['482']}"
        
        self.channels[channel].topic = new_topic
        self.channels[channel].broadcast(f':{client.nick}! TOPIC #{channel} :{new_topic}', client)
        return f':{client.nick}! TOPIC #{channel} :{new_topic}'


    def show_topic(self, client_socket, channel):
        client = next((item for item in self.clients if item.socket == client_socket), None)      
        if channel in self.channels:
            return f'332 {channel}: {self.channels[channel].topic}'
        return f':401 :{self.NUMERIC_REPLIES['401']}'
        

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
                            self.channels[channel].broadcast(f":{sender.nick}! KICK {channel} {addressee.nick} :{reason}", sender)
                            return f":{sender.nick}! KICK {channel} {addressee.nick} :{reason}"
                        return f":482 #{channel} :{self.NUMERIC_REPLIES['482']}"
                    return f':441 #{channel}: {self.NUMERIC_REPLIES['441']}'  
                return f':442 #{channel} :{self.NUMERIC_REPLIES['442']}' 
            return  f':401 :{self.NUMERIC_REPLIES['401']}'
        except IndexError:
            return f":461 :{self.NUMERIC_REPLIES['461']}"


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
            return f":421 COMANDO_INVALIDO :{self.NUMERIC_REPLIES['421']}"


    def handle_channel_mode(self, client_socket, channel, modes, params):
        """Maneja modos de canal"""
        if channel not in self.channels:
            return f':401 :{self.NUMERIC_REPLIES['401']}'

        client = next((item for item in self.clients if item.socket == client_socket), None)
        # Verificar si el usuario es operador del canal
        if not self.channels[channel].is_operator(client):
            return f":482 {channel} :{self.NUMERIC_REPLIES['482']}"

        param_index = 0
        for i, mode in enumerate(modes[1:]):  # Skip the +/- character
            if mode == 'o': 
                if param_index >= len(params):
                    return f":461 :{self.NUMERIC_REPLIES['461']}"
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

            else: return f":472 :{self.NUMERIC_REPLIES['472']}"    

        return 'Operación Exitosa'    



    def handle_user_mode(self, client_socket, target, modes):
        """Maneja modos de usuario"""
        if target not in [client.nick for client in self.clients]:
            return f':401 :{self.NUMERIC_REPLIES['401']}'

        client = next((item for item in self.clients if item.socket == client_socket), None)
        # Un usuario solo puede cambiar sus propios modos
        if client.nick != target:
            return f":502 usuario :{self.NUMERIC_REPLIES['502']}"
        
        self.clients.remove(client)

        for i, mode in enumerate(modes[1:]):  # Skip the +/- character
            if mode == 'i':
                if modes[0] == '+':
                    client.visibility = True
                else:
                    client.visibility = False
            else: return f":472 :{self.NUMERIC_REPLIES['472']}"   

        self.clients.append(client)
        return 'Operación Exitosa'


if __name__ == "__main__":
    server = IRCServer()
    server.start()

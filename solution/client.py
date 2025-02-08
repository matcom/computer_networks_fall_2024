import socket
import threading


class Client:
    def __init__(self, host, port, nick, name):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.nick = nick
        self.name = name
        self.connected = False

    # Intenta establecer la conexión y envía mensajes de nick/name si tiene éxito
    def connect_to_irc_server(self):
        try:
            # Conectarse al servidor IRC
            self.socket.connect((self.host, self.port))
            self.connected = True
            # Enviar comandos de usuario y nickname
            self.socket.sendall(f"NICK {self.nick}\r\n".encode())
            self.socket.sendall(f"USER {self.name} 0 * :Real name\r\n".encode())

        except Exception as e:
            print("Error de conexión", e)
            self.connected = False

    def send_message(self, msg):
        try:
            self.socket.sendall(f"{msg}\r\n".encode())
        except Exception as e:
            print("Error al enviar mensaje:", e)

    # Permite recibir mensajes del recibir, mostrarlos en consola y manejarlos
    def rcv_messages(self):
        buffer = ""
        while self.connected:
            try:
                info = self.socket.recv(4096)  # 4096 bytes recibidos
                if not info:
                    continue

                buffer += info.decode('utf-8', errors='replace')

                while "\r\n" in buffer:
                    message, buffer = buffer.split("\r\n", 1)

                    sections = message.split(" ")

                    if sections[0] == "PING":
                        self.socket.sendall(f"PONG {sections[1]}\r\n".encode())
                    elif sections[0].startswith(":") and sections[1] == "NICK":
                        self.change_nick(sections)
                    elif sections[1] == "PRIVMSG":
                        self.handle_privmsg(sections)
                    elif sections[1] == "NOTICE":
                        self.handle_notice(sections)
                    elif sections[1] == "JOIN":
                        self.join_channel(sections)
                    elif sections[1] == "PART":
                        self.leave_channel(sections)
                    elif sections[1] == "KICK":#no
                        self.handle_kick(sections)
                    elif sections[1] == "MODE":#no
                        self.handle_mode(sections)
                    elif sections[1] in ["311", "319", "322", "323", "324", "353", "366", "431", "432", "433"]:
                        self.num_handler(sections)

                    print(message)

            except UnicodeDecodeError as e:
                print(f"Error de decodificación en la recepción de mensajes: {e}.")
            except Exception as e:
                print(f"Error al recibir mensaje: {e}.")

    ######################
    ######################
    ###    Handlers    ###  
    ######################
    ######################  

    # Cambia el nickname del cliente
    def change_nick(self, sections):
        old = sections[0][1:].split('!')[0]
        new = sections[2].lstrip(':')
        if old == new:
            self.nick = new
            print(f"Nuevo nickname: {self.nick}.")
        else:
            print("Los nicks no coinciden")

    def handle_privmsg(self, msg):
        full_msg = " ".join(msg)
        # Extrae el remitente del mensaje
        prefix_end = full_msg.find('!')
        sender = full_msg[1:prefix_end]

        # Extrae el texto del mensaje
        # Busca el primer carácter ':' que indica el inicio del mensaje real
        message_start = full_msg.find(':', 1)
        message = full_msg[message_start + 1:]

        # Determina si el mensaje es para un canal o es un mensaje directo
        if msg[2].startswith('#'):
            # Mensaje de canal
            print(f"Mensaje de {sender} en {msg[2]}: {message}")
        else:
            # Mensaje directo
            print(f"Mensaje directo de {sender}: {message}")

    def handle_notice(self, sections):
        # Join the sections into a full message
        full_msg = " ".join(sections)
        # Extract the sender's nickname from the full message
        sender = full_msg[1:full_msg.find('!')]
        # Find the start of the message content
        message_start = full_msg.find(':', 1)
        # Extract the message content from the full message
        message = full_msg[message_start + 1:]
        # Print the sender's nickname and their message
        print(f"Notice de {sender}: {message}")

    def handle_kick(self, sections):
        # Extract the channel name from the sections
        channel = sections[2]
        # Extract the nickname of the user who was kicked
        user_kicked = sections[3]
        # Extract the reason for the kick, if any, from the sections
        reason = " ".join(sections[4:]).lstrip(':')
        # Print a message indicating that the user was kicked from the channel and the reason
        print(f"{user_kicked} ha sido expulsado de {channel} por la razón: {reason}")

    def handle_mode(self, sections):
        source = sections[0][1:]
        channel_or_user = sections[2]
        mode_changes = sections[3:]

        # Imprime o procesa el cambio de modo
        print(f"{source} cambió el modo de {channel_or_user} a {' '.join(mode_changes)}")

    def num_handler(self, sections):
        code = sections[1]

        # Código 311: WHOIS - otorga información del usuario
        if code == "311":
            nickname = sections[3]
            username = sections[4]
            hostname = sections[5]
            realname = ' '.join(sections[7:])[1:]
            print(f"El usuario {nickname} ({realname}) está en: {hostname}")

        # Código 319: Muestra los canales a los que pertenece el usuario
        elif code == "319":
            nickname = sections[3]
            channels = ' '.join(sections[4:])[1:]
            print(f"{nickname} pertenece a los canales: {channels}")

        # Código 322: LIST
        elif code == "322":
            channel = sections[3]
            user_count = sections[4]
            topic = ' '.join(sections[5:])[1:]
            print(f"Canal: {channel}. Cantidad de usuarios: {user_count}. Tema: {topic}")

        # Código 323: Fin de la lista LIST
        elif code == "323":
            print("Fin de la lista de canales.")

        # Código 324: Respuesta de modo de canal
        elif code == "324":
            channel = sections[3]
            modes = ' '.join(sections[4:])
            print(f"Modos actuales para {channel}: {modes}")

        # Código 353: Respuesta a NAMES
        elif code == "353":
            channel = sections[4]
            names = ' '.join(sections[5:])[1:]
            print(f"Usuarios en {channel}: {names}")

        # Código 366: Fin de la lista NAMES
        elif code == "366":
            channel = sections[3]
            print(f"Fin de la lista de usuarios en {channel}.")

        # Código 431: Sin nickname dado
        elif code == "431":
            print("No se ha proporcionado un nickname.")

        # Código 432: Nickname erróneo
        elif code == "432":
            print("El nickname es inválido.")

        # Código 433: Nickname en uso/inválido
        elif code == "433":
            print("El nickname deseado está en uso o es inválido.")

    ######################
    ######################
    ###      CMD       ###
    ######################
    ######################  

    def process_command(self, command):
        sections = command.split(' ', 1)
        cmd = sections[0].lower()

        if cmd == "/join" and len(sections) > 1:
            self.socket.sendall(f"JOIN {sections[1]}\r\n".encode())

        elif cmd == "/part" and len(sections) > 1:
            self.socket.sendall(f"PART {sections[1]}\r\n".encode())

        elif cmd == "/msg" and len(sections) > 1:
            target_msg = sections[1].split(' ', 1)
            if len(target_msg) > 1:
                self.socket.sendall(f"PRIVMSG {target_msg[0]} :{target_msg[1]}\r\n".encode())

        elif cmd == "/notice" and len(sections) > 1:
            target_msg = sections[1].split(' ', 1)
            if len(target_msg) > 1:
                self.socket.sendall(f"NOTICE {target_msg[0]} :{target_msg[1]}\r\n".encode())

        elif cmd == "/mode" and len(sections) > 1:
            mode_args = sections[1].split(' ', 1)
            if len(mode_args) > 1:
                self.socket.sendall(f"MODE {mode_args[0]} {mode_args[1]}\r\n".encode())

        elif cmd == "/list":
            self.socket.sendall("LIST\r\n".encode())

        elif cmd == "/names":
            if len(sections) > 1:
                self.get_channel_users(sections[1])
            else:
                self.get_channel_users()

        elif cmd == "/nick" and len(sections) > 1:
            self.socket.sendall(f"NICK {sections[1]}\r\n".encode())

        elif cmd == "/whois" and len(sections) > 1:
            self.socket.sendall(f"WHOIS {sections[1]}\r\n".encode())
            
        elif cmd == "/topic" and len(sections) > 1:
            self.socket.sendall(f"TOPIC {sections[1]}\r\n".encode())
        else:
            print("No se reconoce el comando o faltan argumentos.")

    def join_channel(self, sections):
        user_info = sections[0][1:]
        channel = sections[2].strip() if sections[2].startswith(':') else sections[2]
        print(f"El usuario {user_info} se ha unido al canal {channel}")

    def leave_channel(self, sections):
        user_info = sections[0][1:]
        channel = sections[2].strip() if sections[2].startswith(':') else sections[2]
        print(f"El usuario {user_info} ha salido del canal {channel}")

    def get_channel_users(self, channel=""):
        if channel:
            self.socket.sendall(f"NAMES {channel}\r\n".encode())
        else:
            self.socket.sendall("NAMES\r\n".encode())


# def main():
#     host = input("Ingrese la dirección del host: ")
#     port = int(input("Ingrese la dirección del puerto: "))
#     nick = input("Ingrese su nick: ")
#     user = input("Ingrese su nombre real: ")

#     client = Client(host, port, nick, user)

#     client.connect_to_irc_server()

#     if client.connected:
#         print(f"Conexión exitosa. Bienvenido {client.nick}!")

#         # Iniciar un nuevo hilo para manejar la entrada de la consola
#         threading.Thread(target=client.rcv_messages, daemon=True).start()

#         while True:
#             user_input = input()
#             if user_input.startswith('/'):
#                 client.process_command(user_input)
#             else:
#                 client.send_message(user_input)

#     else:
#         print("No se pudo conectar al servidor. Por favor, vuelva a intentarlo más tarde.")


# main()
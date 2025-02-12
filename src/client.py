import socket
import ssl
import threading
import sys
import getopt
import time


class IRCClient:
    def __init__(self, host, port, nickname, use_ssl):
        self.host = host
        self.port = port
        self.nickname = nickname
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.use_ssl = use_ssl
        
        
        if self.use_ssl:
            # Crear una instancia de SSLContext para autenticación del servidor (conexión cliente)
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ssl_context.check_hostname = True  # Verifica que el nombre de host en el certificado coincide con el objetivo
            ssl_context.verify_mode = ssl.CERT_REQUIRED  # Requiere un certificado válido
            # ssl_context.check_hostname = False
            # ssl_context.verify_mode = ssl.CERT_NONE  #Deshabilita la verificación del certificado
            # Envolver el socket existente en un contexto SSL
            self.socket = ssl_context.wrap_socket(self.socket, server_hostname=self.host)
            
    
    def connect(self):
       
         try:   
            time.sleep(5)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # # echo message
            # self.socket.sendall("CAP REQ :echo-message\r\n".encode())
            
            # Enviar comandos NICK y USER según el protocolo IRC
            self.socket.sendall(f"NICK {self.nickname}\r\n".encode())
            self.socket.sendall(f"USER {self.nickname} 0 * :Real name\r\n".encode())
         except Exception as e:
           print("Error al conectar al servidor:", e)
           self.connected = False
    
    def disconnect(self, message=""):
        if self.connected:
            if message:
                self.socket.sendall(f"QUIT :{message}\r\n".encode())
            else:
                self.socket.sendall("QUIT\r\n".encode())
            self.socket.close()
            self.connected = False
            print("Desconectado del servidor.")


    def send_message(self, message):
        try:
            self.socket.sendall(f"{message}\r\n".encode())
            print(f"Tú: {message}")
        except Exception as e:
            print("Error al enviar mensaje:", e)
            
    
    def send_pong(self, server):
        self.socket.sendall(f"PONG {server}\r\n".encode())
            
            
    def handle_privmsg(self, parts):
        """
        Maneja mensajes PRIVMSG.

        Args:
        parts: Lista de componentes del mensaje PRIVMSG.
        """
        # Concatena de nuevo las partes para manejar fácilmente los mensajes que contienen espacios
        # print(parts)
        full_msg = " ".join(parts)

        # Extrae el remitente del mensaje
        prefix_end = full_msg.find('!')
        sender = full_msg[1:prefix_end]

        # Extrae el texto del mensaje
        # Busca el primer carácter ':' que indica el inicio del mensaje real
        message_start = full_msg.find(':', 1)
        message = full_msg[message_start + 1:]

        # Determina si el mensaje es para un canal o es un mensaje directo
        if parts[2].startswith('#'):
            # Mensaje de canal
            print(f"Mensaje de {sender} en {parts[2]}: {message}")
        else:
            # Mensaje directo
            print(f"Mensaje directo de {sender}: {message}")

    def handle_notice(self, parts):
        sender = parts[0][1:].split('!')[0]
        target = parts[2]
        message = ' '.join(parts[3:])[1:]
        print(f"Notificación de {sender}: {target} {message}")

    def handle_join(self, parts):
        user_info = parts[0].split('!')[0][1:]
        channel = parts[2].strip() if parts[2].startswith(':') else parts[2]
        print(f"{user_info} se ha unido a {channel}")

    def handle_part(self, parts):
        user_info = parts[0].split('!')[0][1:]
        channel = parts[2].strip() if parts[2].startswith(':') else parts[2]
        print(f"{user_info} ha dejado {channel}")

    def handle_kick(self, parts):
        channel = parts[2]
        user_kicked = parts[3]
        reason = " ".join(parts[4:]).lstrip(':')
        print(f"{user_kicked} ha sido expulsado de {channel} por la razón: {reason}")
        
    
    def handle_mode(self, parts):
        source = parts[0][1:]
        channel_or_user = parts[2]
        mode_changes = parts[3:]

        # Imprime o procesa el cambio de modo
        print(f"{source} cambió el modo de {channel_or_user} a {' '.join(mode_changes)}")


    def handle_nick_change(self, parts):
        old_nick = parts[0][1:].split('!')[0]
        new_nick = parts[2].lstrip(':')
        if old_nick == self.nickname:
            self.nickname = new_nick  # Actualiza el nickname almacenado
            print(f"Tu nuevo apodo es {new_nick}.")
        else:
            print(f"{old_nick} ahora es conocido como {new_nick}.")
            
            
    def handle_whois_response(self, parts):
        code = parts[1]
        if code == "311":  # Respuesta WHOIS con información del usuario
            nickname = parts[3]
            username = parts[4]
            hostname = parts[5]
            realname = ' '.join(parts[7:])[1:]
            print(f"Usuario {nickname} ({realname}) está en {hostname}")
        elif code == "319":  # Canales en los que el usuario está
            nickname = parts[3]
            channels = ' '.join(parts[4:])[1:]
            print(f"{nickname} está en los canales {channels}")
    
    
    def handle_numeric_response(self, parts):
        code = parts[1]
        if code == "322":  # Respuesta a LIST
            channel = parts[3]
            user_count = parts[4]
            topic = ' '.join(parts[5:])[1:]
            print(f"Canal: {channel} ({user_count} usuarios) - Tema: {topic}")
        elif code == "323":  # Fin de la lista LIST
            print("Fin de la lista de canales.")
        elif code == "353":  # Respuesta a NAMES
            channel = parts[4]
            names = ' '.join(parts[5:])[1:]
            print(f"Usuarios en {channel}: {names}")
        elif code == "366":  # Fin de la lista NAMES
            channel = parts[3]
            print(f"Fin de la lista de usuarios en {channel}.")
        elif code == "433":
            print("El nickname deseado está en uso o es inválido.")
        elif code == "482":
            print("No tienes permiso para cambiar el modo del canal.")
        elif code == "431":  # Sin nickname dado
            print("No se ha proporcionado un nickname.")
        elif code == "432":  # Erroneous Nickname
            print("El nickname es inválido.")
        elif code == "324":  # Respuesta de modo de canal
            channel = parts[3]
            modes = ' '.join(parts[4:])
            print(f"Modos actuales para {channel}: {modes}")
        elif code == "311":  # Respuesta WHOIS con información del usuario
            nickname = parts[3]
            username = parts[4]
            hostname = parts[5]
            realname = ' '.join(parts[7:])[1:]
            print(f"Usuario {nickname} ({realname}) está en {hostname}")
        elif code == "319":  # Canales en los que el usuario está
            nickname = parts[3]
            channels = ' '.join(parts[4:])[1:]
            print(f"{nickname} está en los canales {channels}")
        elif code == "332": # Respuesta de tema de canal
            channel = parts[3]
            topic = ' '.join(parts[4:])[1:]
            print(f"Tema de {channel}: {topic}")
        elif code == "352":  # Respuesta a WHO
            channel = parts[3]
            user = parts[7]
            host = parts[4]
            server = parts[5]
            nick = parts[7]
            realname = ' '.join(parts[10:])[1:]
            print(f"Usuario en {channel}: {nick} ({realname}) - Host: {host} - Servidor: {server}")
        elif code == "315":  # Fin de la lista WHO
            channel = parts[3]
            print(f"Fin de la lista WHO para {channel}.")
        elif code == "314":  # Respuesta a WHOWAS
            nickname = parts[3]
            username = parts[4]
            host = parts[5]
            realname = ' '.join(parts[7:])[1:]
            print(f"WHOWAS {nickname}: {username}@{host} ({realname})")
        elif code == "369":  # Fin de la lista WHOWAS
            nickname = parts[3]
            print(f"Fin de la lista WHOWAS para {nickname}.")
        
    
    
    def handle_quit(self, parts):
     user_info = parts[0].split('!')[0][1:]
     channel = parts[2].strip() if parts[2].startswith(':') else parts[2]
     print(f"{user_info} se ha desconectado. Mensaje: {channel}")
    
    
    def handle_topic(self, parts):
        channel = parts[2]
        topic = ' '.join(parts[3:])[1:]
        print(f"El tema del canal {channel} ha sido cambiado a: {topic}")
    

    def send_privmsg(self, target, message):
        self.socket.sendall(f"PRIVMSG {target} {message}\r\n".encode())
        print(f"Mensaje privado de {self.nickname}: {target} {message}")  # Muestra el mensaje que envías
    def join_channel(self, channel):
        self.socket.sendall(f"JOIN {channel}\r\n".encode())
        print(f"Te has unido al canal {channel}")
    def leave_channel(self, channel):
        self.socket.sendall(f"PART {channel}\r\n".encode())
        print(f"Has salido del canal {channel}")
    def set_channel_mode(self, channel, mode):
        self.socket.sendall(f"MODE {channel} {mode}\r\n".encode())
        print(f"Has cambiado el modo de {channel} a {mode}")
    def send_notice(self, target, message):
        self.socket.sendall(f"NOTICE {target} :{message}\r\n".encode())
        print(f"Notificacion de {self.nickname}: {target} {message}")  # Muestra el mensaje que envías
    def list_channels(self):
        self.socket.sendall("LIST\r\n".encode())
    def list_users_in_channel(self, channel=""):
        if channel:
            self.socket.sendall(f"NAMES {channel}\r\n".encode())
        else:
            self.socket.sendall("NAMES\r\n".encode())
    def change_nickname(self, new_nickname):
        self.socket.sendall(f"NICK {new_nickname}\r\n".encode())
        print(f"Tu nuevo apodo es {new_nickname}.")

    def change_user_mode(self, nickname, mode):
        self.socket.sendall(f"MODE {nickname} {mode}\r\n".encode())
    def whois_query(self, nickname):
        self.socket.sendall(f"WHOIS {nickname}\r\n".encode())
    
    def send_topic(self, channel, topic=None):
        if topic:
            self.socket.sendall(f"TOPIC {channel} :{topic}\r\n".encode())
        else:
            self.socket.sendall(f"TOPIC {channel}\r\n".encode())
    
    def send_who(self, channel):
        self.socket.sendall(f"WHO {channel}\r\n".encode())
    
    def send_whowas(self, nickname):
        self.socket.sendall(f"WHOWAS {nickname}\r\n".encode())
    
    def send_ping(self, server):
        self.socket.sendall(f"PING {server}\r\n".encode())
    
    def send_kick(self, channel, user, reason=""):
        if reason:
            self.socket.sendall(f"KICK {channel} {user} :{reason}\r\n".encode())
        else:
            self.socket.sendall(f"KICK {channel} {user}\r\n".encode())
        print(f"Has expulsado a {user} del canal {channel}. Razón: {reason}")
    
    def send_invite(self, user, channel):
        self.socket.sendall(f"INVITE {user} {channel}\r\n".encode())
        print(f"Has invitado a {user} al canal {channel}")
    
    
    def process_command(self, command):
        print("COMANDO" + command)
        parts = command.split(' ', 1)
        print(parts)
        cmd = parts[0].lower()
        #/notice #General Hello, World!
        if cmd == "/join" and len(parts) > 1:
            self.join_channel(parts[1])
        elif cmd == "/part" and len(parts) > 1:
            self.leave_channel(parts[1])
        elif cmd == "/privmsg" and len(parts) > 1:
            target_message = parts[1].split(' ', 1)
            if len(target_message) > 1:
                self.send_privmsg(target_message[0], target_message[1])
        elif cmd == "/notice" and len(parts) > 1:
            target_message = parts[1].split(' ', 1)
            if len(target_message) > 1:
                self.send_notice(target_message[0], target_message[1])
        elif cmd == "/mode" and len(parts) > 1:
            mode_args = parts[1].split(' ', 1)
            if len(mode_args) > 1:
                self.set_channel_mode(mode_args[0], mode_args[1])
        elif cmd == "/list":
            self.list_channels()
        elif cmd == "/names":
            if len(parts) > 1:
                self.list_users_in_channel(parts[1])
            else:
                self.list_users_in_channel()
        elif cmd == "/nick" and len(parts) > 1:
            new_nickname = parts[1]
            self.change_nickname(new_nickname)
        elif cmd == "/whois" and len(parts) > 1:
            nickname = parts[1]
            self.whois_query(nickname)
        elif cmd == "/who" and len(parts) > 1:
            channel = parts[1]
            self.send_who(channel)
        elif cmd == "/whowas" and len(parts) > 1:
            nickname = parts[1]
            self.send_whowas(nickname)
        elif cmd == "/topic" and len(parts) > 1:
            topic_args = parts[1].split(' ', 1)
            if len(topic_args) > 1:
                self.send_topic(topic_args[0], topic_args[1])
            else:
                self.send_topic(topic_args[0])
        elif cmd == "/ping" and len(parts) > 1:
            server = parts[1]
            self.send_ping(server)
        elif cmd == "/pong" and len(parts) > 1:
            server = parts[1]
            self.send_pong(server)
        elif cmd == "/kick" and len(parts) > 1:
            kick_args = parts[1].split(' ', 2)
            if len(kick_args) > 2:
                self.send_kick(kick_args[0], kick_args[1], kick_args[2])
            elif len(kick_args) > 1:
                self.send_kick(kick_args[0], kick_args[1])
        elif cmd == "/invite" and len(parts) > 1:
            invite_args = parts[1].split(' ', 1)
            if len(invite_args) > 1:
                self.send_invite(invite_args[0], invite_args[1])
        elif cmd == "/quit":
            message = parts[1] if len(parts) > 1 else ""
            self.disconnect(message)
        else:
            print("Comando desconocido o faltan argumentos.")



    def receive_messages(self):
        buffer = ""  # Búfer para acumular datos recibidos
        while self.connected:
            try:
                data = self.socket.recv(4096)  # Recibe bytes del socket
                if not data:
                    continue  # Si no hay datos, continúa el bucle

                # Decodifica y añade al búfer, manejando errores de decodificación
                buffer += data.decode('utf-8', errors='replace')

                # Procesa todos los mensajes completos que hay en el búfer
                while "\r\n" in buffer:
                    message, buffer = buffer.split("\r\n", 1)  # Separa el primer mensaje completo del buffer
                    parts = message.split(" ")

                    # Lógica para manejar diferentes tipos de mensajes basada en 'parts'
                    if parts[0] == "PING":
                        self.send_pong(parts[1])
                    elif parts[1] in ["322","482", "323","352","315","314","369","332", "353", "366", "433", "431", "432", "311", "319", "324"]:
                        self.handle_numeric_response(parts)
                    elif parts[0].startswith(":") and parts[1] == "NICK":
                        self.handle_nick_change(parts)
                    elif parts[1] == "PRIVMSG":
                        self.handle_privmsg(parts)
                    elif parts[1] == "NOTICE":
                        self.handle_notice(parts)
                    elif parts[1] == "JOIN":
                        self.handle_join(parts)
                    elif parts[1] == "PART":
                        self.handle_part(parts)
                    elif parts[1] == "KICK":
                        self.handle_kick(parts)
                    elif parts[1] == "MODE":
                        self.handle_mode(parts)
                    elif parts[1] == "QUIT":
                        self.handle_quit(parts)
                    elif parts[1] == "TOPIC":
                        self.handle_topic(parts)
                    


                #    print(message)  # Imprime todos los mensajes para depuración.

            except UnicodeDecodeError as e:
                print(f"Error de decodificación en la recepción de mensajes: {e}.")
            except Exception as e:
                print(f"Error al recibir mensaje: {e}.")
                self.connected = False
                break
    
    
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "H:p:n:c:a:", ["port=", "host=", "nick=", "command=", "argument="])
    except getopt.GetoptError as err:
        print(str(err))
        sys.exit(2)
    
    test_input = sys.argv[1:]
    print(test_input)
    server_ip,port,nickname,command,argument = test_input[1],int(test_input[3]),test_input[5],'/'+test_input[7].split('/').pop(),test_input[9:]
    argument = ' '.join(argument)
    # print(server_ip)
    # print(nickname)
    # print(command)
    # print(argument)
    # server_ip = None
    # port = None
    # nickname = None
    # command = None
    # argument = None
    use_ssl = False

    # print(opts)
    # for opt, arg in opts:
    #     if opt in ("-p", "--port"):
    #         port = int(arg)
    #     elif opt in ("-H", "--host"):
    #         server_ip = arg
    #     elif opt in ("-n", "--nick"):
    #         nickname = arg
    #     elif opt in ("-c", "--command"):
    #         command = arg
    #     elif opt in ("-a", "--argument"):
    #         argument = arg
            
    
    if not server_ip or not port or not nickname:
       # Modo interactivo
        server_ip = input("Ingrese la dirección IP del servidor: ")
        port = int(input("Ingrese el puerto: "))
        nickname = input("Ingrese su apodo: ")
        usarssl = input("Ingrese 1 para usar conexión segura. Ingrese 2 para el caso contrario: ")

        tmp = True
        while tmp:
           if usarssl == '1':
            use_ssl = True
            tmp = False
           elif usarssl == '2':
            use_ssl = False
            tmp = False
           else:
            usarssl = input ("Ingrese 1 para usar conexión segura. Ingrese 2 para el caso contrario ")


    irc_client = IRCClient(server_ip, port, nickname, use_ssl)
    irc_client.connect()
    
    if irc_client.connected:
        # print(f"Bienvenido, {nickname}!\n")
        threading.Thread(target=irc_client.receive_messages, daemon=True).start()
        
        if command and argument:
            # print(f"ARGUMENTO {argument}")
            user_input = f"{command} {argument}"
            if user_input.startswith('/'):
                # print(user_input)
                # print(argument)
                irc_client.process_command(user_input)
            else:
                irc_client.send_message(user_input)
        else:        
            while irc_client.connected:
             user_input = input() 
             if user_input.startswith('/'):
                irc_client.process_command(user_input)
             else:
                irc_client.send_message(user_input)

    else:
        print("No se pudo conectar al servidor. Por favor, vuelva a intentarlo más tarde.")

if __name__ == "__main__":
    main()
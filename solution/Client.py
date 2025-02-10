import argparse
import socket
from time import sleep
import threading

class IRCClient:
    def __init__(self, host, port, nick):
        self.host = host
        self.port = port
        self.nick = nick
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected= False
        self.buffer=""

    def connect(self):
        """Se conecta al servidor IRC y envía el NICK y USER inicial."""
        self.sock.connect((self.host, self.port))
        self.connected = True
        sleep(0.2)
        # Enviar comandos iniciales al servidor
        self.send_command(f"NICK {self.nick}")
        sleep(0.2)
        self.send_command(f"USER {self.nick}")
        # Esperar respuesta del servidor después de conectarse
        

    def send_command(self, command):
        """Envía un mensaje al servidor IRC."""
        self.sock.sendall((command + "\r\n").encode("utf-8"))

    def receive_response(self):
        """Recibe y almacena todas las respuestas del servidor hasta que no haya más datos en el buffer."""
        try:
            response = ""
            self.sock.settimeout(0.5)  # Evita bloqueos infinitos si no llegan más mensajes
            while True:
                try:
                    chunk = self.sock.recv(4096).decode("utf-8")
                    if not chunk:
                        break
                    response += chunk
                except socket.timeout:
                    break  # Salimos cuando no hay más datos disponibles

            return response.strip()  # Eliminamos espacios en blanco sobrantes
        except Exception as e:
            return f"Error al recibir respuesta: {e}"


    def start_receiving(self):
        """Inicia un hilo para recibir mensajes del servidor."""
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def receive_messages(self):
        """Escucha continuamente los mensajes del servidor."""
        while self.connected:
            try:
                info = self.sock.recv(4096)  # 4096 bytes recibidos
                if not info:
                    continue

                self.buffer += info.decode('utf-8', errors='replace')
                self.process_buffer()

            except UnicodeDecodeError as e:
                print(f"Error de decodificación en la recepción de mensajes: {e}.")
            except Exception as e:
                print(f"Error al recibir mensaje: {e}.")

    def process_buffer(self):
        """Procesa los mensajes completos en el buffer."""
        while "\r\n" in self.buffer:
            message, self.buffer = self.buffer.split("\r\n", 1)  # Separar un mensaje completo
            self.handle_message(message)

    def handle_message(self, message):
        """Maneja el mensaje recibido del servidor y procesa los comandos."""
        try:
            # Si el mensaje está vacío, ignorarlo
            if not message:
                return
            
            # Dividir el mensaje en sus componentes
            parts = message.split(' ', 1)
            first_part = parts[0]
            content = parts[1] if len(parts) > 1 else ""
            
            # Manejar códigos numéricos
            if first_part.startswith(':') and first_part[1:].isdigit():
                code = str(first_part[1:])
                self.handle_numeric_response(code, content)
                return
            
            # Manejar comandos específicos
            if first_part == "PING":
                # Responder inmediatamente al PING para mantener la conexión
                self.send_command(f"PONG {content}")
                return
            
            # Manejar mensajes que comienzan con ':'
            if message.startswith(':'):
                # Extraer el origen y el comando
                try:
                    source, cmd, *params = message[1:].split(' ')
                    nick = source.split('!')[0] if '!' in source else source
                    
                    if cmd == "PRIVMSG":
                        target = params[0]
                        msg_content = ' '.join(params[1:])[1:] # Eliminar el ':' inicial
                        if target.startswith('#'):
                            print(f"[{target}] {nick}: {msg_content}")
                        else:
                            print(f"Mensaje privado de {nick}: {msg_content}")
                        
                    elif cmd == "JOIN":
                        channel = params[0]
                        print(f"{nick} se ha unido al canal {channel}")
                        
                    elif cmd == "PART":
                        channel = params[0]
                        print(f"{nick} ha abandonado el canal {channel}")
                        
                    elif cmd == "QUIT":
                        reason = ' '.join(params)[1:] if params else "No reason given"
                        print(f"{nick} se ha desconectado: {reason}")
                        
                    elif cmd == "NICK":
                        new_nick = params[0]
                        print(f"{nick} ahora se conoce como {new_nick}")

                    elif cmd == "KICK":
                        channel = params[0]  # Canal de donde se expulsó al usuario
                        kicked_user = params[1]  # Usuario expulsado
                        reason = ' '.join(params[2:])[1:] if len(params) > 2 else "Sin razón especificada"
                        print(f"{kicked_user} ha sido expulsado de {channel} por {nick}: {reason}")    
                        
                    elif cmd == "MODE":
                        target = params[0]
                        modes = ' '.join(params[1:])
                        print(f"{nick} estableció modo {modes} en {target}")
                        
                    elif cmd == "TOPIC":
                        channel = params[0]
                        topic = ' '.join(params[1:])[1:] if len(params) > 1 else ""
                        print(f"{nick} cambió el topic en {channel} a: {topic}")
                        
                    elif cmd == "NOTICE":
                        target = params[0]
                        notice_content = ' '.join(params[1:])[1:]
                        print(f"NOTICE de {nick}: {notice_content}")
                        
                    else:
                        print(f"Mensaje del servidor: {message}")
                    
                except Exception as e:
                    print(f"Error al procesar mensaje con prefijo: {e}")
                    print(f"Mensaje original: {message}")
            
            else:
                print(f"Mensaje del servidor: {message}")
            
        except Exception as e:
            print(f"Error al procesar mensaje: {e}")

    def handle_numeric_response(self, code, content):
        """Procesa los códigos numéricos del servidor IRC."""
        responses = {
            '001': "Bienvenido al servidor IRC",
            '331': "No hay topic establecido",
            '332': f"Topic del canal: {content}",
            '353': f"Lista de usuarios: {content}",
            '366': "Fin de la lista de usuarios",
            '401': "Usuario/Canal no encontrado",
            '403': "Canal no encontrado",
            '404': "No puedes enviar mensajes a este canal",
            '421': "Comando desconocido",
            '431': "No se ha especificado nickname",
            '432': "Nickname inválido",
            '433': "Nickname ya está en uso",
            '441': "Usuario no está en el canal",
            '442': "No estás en ese canal",
            '461': "Faltan parámetros",
            '472': "Modo desconocido",
            '482': "No eres operador del canal",
            '502': "Un usuario solo puede cambiar sus propios modos"
            
        }
        
        if code in responses:
            print(f"[{code}] {responses[code]}")
        else:
            print(f"Código {code}: {content}")

    def handle_command(self, command, argument):
        """Maneja el comando que llega desde los tests."""
        if command == "/nick":
            return self.change_nick(argument)
        elif command == "/join":
            return self.join_channel(argument)
        elif command == "/part":
            return self.part_channel(argument)
        elif command == "/privmsg":
            return self.send_private_message(argument)
        elif command == "/notice":
            return self.send_notice(argument)
        elif command == "/list":
            return self.list_channels()
        elif command == "/names":
            return self.list_users(argument)
        elif command == "/whois":
            return self.whois_user(argument)
        elif command == '/kick':
            return self.kick_user(argument)
        elif command == '/mode':
            return self.handle_mode(argument)
        elif command == "/topic":
            return self.change_topic(argument)
        elif command == "/quit":
            return self.quit_server()
        else:
            return f"Error: Comando '{command}' no soportado"

    def change_nick(self, new_nick):
        """Cambia el nickname enviando el comando al servidor."""
        if new_nick:
            self.send_command(f"NICK {new_nick}")
        else: print('Error: Debes proporcionar un nickname')   

    def join_channel(self, channel):
        """Se une a un canal enviando el comando JOIN."""
        if channel:
            self.send_command(f"JOIN {channel}")
        else: print('Error: Debes proporcionar un canal')    

    def part_channel(self, channel):
        """Sale de un canal enviando el comando PART."""
        if channel:
            self.send_command(f"PART {channel}")
        else: print('Error: Debe proporcionar un canal')    

    def send_private_message(self, argument):
        try:
            """Envía un mensaje privado a un usuario o canal."""
            parts = argument.split(" ", 1)
            if len(parts) < 2:
                print ("Error: Debes proporcionar un destinatario y un mensaje")
            target, message = parts
            self.send_command(f"PRIVMSG {target} :{message}")
        except IndexError:
            print("Formato invalido")    

    def send_notice(self, argument):
        """Envía un mensaje NOTICE a un usuario o canal."""
        try:
            parts = argument.split(" ", 1)
            if len(parts) < 2:
                print ("Error: Debes proporcionar un destinatario y un mensaje")
            target, message = parts
            self.send_command(f"NOTICE {target} {argument}") 
        except IndexError:
            print("Formato invalido")    
    
    def list_channels(self):
        """Solicita la lista de canales al servidor."""
        self.send_command("LIST")
    
    def list_users(self, channel):
        """Lista los usuarios de un canal específico."""
        if channel:
            self.send_command(f"NAMES {channel}")
        else: print('Error: Debe proporcionar un canal')    

    def whois_user(self, user):
        """Obtiene información sobre un usuario."""
        if user:
            self.send_command(f"WHOIS {user}")
        else: print('Error: Debe proporcionar un nickname')    

    def kick_user(self, argument):
        try:
            parts = argument.split(" ", 2)
            channel = parts[0]
            user = parts[1]
            reason = parts[2] if len(parts) > 2 else "No reason given"
            self.send_command(f'KICK {channel} {user} {reason}')
        except IndexError:
            print ("Error: Uso correcto: /kick <canal> <usuario> [motivo]")
    
    def change_topic(self, argument):
        """Cambia o consulta el tema de un canal."""
        try:
            parts = argument.split(" ", 1)
            if len(parts) < 1:
                return "Error: Debes proporcionar un canal"
            channel = parts[0]
            topic = parts[1] if len(parts) > 1 else ""
            if topic:
                self.send_command(f"TOPIC {channel} :{topic}")
            else:
                self.send_command(f"TOPIC {channel}")
        except IndexError:
            print('Formato Invalido')        

    def handle_mode(self, argument):
        print("Falta")        
    
    def quit_server(self):
        """Sale del servidor IRC enviando el comando QUIT."""
        self.send_command("QUIT :Saliendo del servidor")
        self.sock.close()
        self.connected= False
        print('Desconectado del servidor')

def parse_arguments():
    parser = argparse.ArgumentParser(description="Parser de pruebas para cliente IRC")
    parser.add_argument("-p", type=int, help="Puerto del servidor IRC", required=True)
    parser.add_argument("-H", type=str, help="Host del servidor IRC", required=True)
    parser.add_argument("-n", type=str, help="Nickname del usuario", required=True)
    parser.add_argument("-c", type=str, help="Comando de IRC a ejecutar", required=True)
    parser.add_argument("-a", type=str, help="Argumento del comando", required=False, default="", nargs="+")

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    sleep(1)
    argument = " ".join(args.a) if isinstance(args.a, list) else args.a
    # Crear el cliente y conectar al servidor
    client = IRCClient(args.H, args.p, args.n)
    client.connect()
    client.receive_response()
    # Ejecutar el comando desde el test
    client.handle_command(args.c, argument)
    if args.c != "/quit":
        response = client.receive_response()  
        # Mostrar la respuesta del servidor
        print(response)    
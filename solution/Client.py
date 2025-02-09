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
            return f"❌ Error al recibir respuesta: {e}"


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
        """Maneja el mensaje recibido."""
        print(f"Mensaje del servidor: {message}")


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
        elif command == "/topic":
            return self.change_topic(argument)
        elif command == "/quit":
            return self.quit_server()
        else:
            return f"Error: Comando '{command}' no soportado"

    def change_nick(self, new_nick):
        """Cambia el nickname enviando el comando al servidor."""
        self.send_command(f"NICK {new_nick}")

    def join_channel(self, channel):
        """Se une a un canal enviando el comando JOIN."""
        self.send_command(f"JOIN {channel}")

    def part_channel(self, channel):
        """Sale de un canal enviando el comando PART."""
        self.send_command(f"PART {channel}")

    def send_private_message(self, argument):
        """Envía un mensaje privado a un usuario o canal."""
        parts = argument.split(" ", 1)
        if len(parts) < 2:
            return "Error: Debes proporcionar un destinatario y un mensaje"
        target, message = parts
        self.send_command(f"PRIVMSG {target} :{message}")

    def send_notice(self, argument):
        """Envía un mensaje NOTICE a un usuario o canal."""
        parts = argument.split(" ", 1)
        if len(parts) < 2:
            return "Error: Debes proporcionar un destinatario y un mensaje"
        target, message = parts
        self.send_command(f"NOTICE {target} {argument}") 
    
    def list_channels(self):
        """Solicita la lista de canales al servidor."""
        self.send_command("LIST")
    
    def list_users(self, channel):
        """Lista los usuarios de un canal específico."""
        self.send_command(f"NAMES {channel}")

    def whois_user(self, user):
        """Obtiene información sobre un usuario."""
        self.send_command(f"WHOIS {user}")
    
    def change_topic(self, argument):
        """Cambia o consulta el tema de un canal."""
        parts = argument.split(" ", 1)
        if len(parts) < 1:
            return "Error: Debes proporcionar un canal"
        channel = parts[0]
        topic = parts[1] if len(parts) > 1 else ""
        if topic:
            self.send_command(f"TOPIC {channel} :{topic}")
        else:
            self.send_command(f"TOPIC {channel}")
    
    def quit_server(self):
        """Sale del servidor IRC enviando el comando QUIT."""
        self.send_command("QUIT :Saliendo del servidor")
        self.sock.close()
        self.connected= False

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
    response = client.receive_response()
    # Mostrar la respuesta del servidor
    print(response)
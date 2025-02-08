import argparse
import socket

class IRCClient:
    def __init__(self, host, port, nick):
        self.host = host
        self.port = port
        self.nick = nick
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        """Se conecta al servidor IRC y envía el NICK y USER inicial."""
        self.sock.connect((self.host, self.port))

        # Enviar comandos iniciales al servidor
        self.send_command(f"NICK {self.nick}")
        self.send_command(f"USER {self.nick} 0 * :Test User")

    def send_command(self, command):
        """Envía un comando al servidor IRC en formato correcto."""
        self.sock.sendall((command + "\r\n").encode("utf-8"))

    def receive_response(self):
        """Recibe datos del servidor hasta encontrar una línea completa."""
        buffer = ""
        while True:
            data = self.sock.recv(4096).decode("utf-8")
            if not data:
                break  # Conexión cerrada
            buffer += data
            if "\r\n" in buffer:  # Mensaje IRC completo recibido
                break
        return buffer.strip()


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
            return f"⚠️ Error: Comando '{command}' no soportado"

    def change_nick(self, new_nick):
        """Cambia el nickname enviando el comando al servidor."""
        self.send_command(f"NICK {new_nick}")
        return self.receive_response()

    def join_channel(self, channel):
        """Se une a un canal enviando el comando JOIN."""
        if not channel.startswith("#"):
            return "⚠️ Error: Los canales IRC deben comenzar con '#'"
        self.send_command(f"JOIN {channel}")
        return self.receive_response()

    def part_channel(self, channel):
        """Sale de un canal enviando el comando PART."""
        if not channel.startswith("#"):
            return "⚠️ Error: Los canales IRC deben comenzar con '#'"
        self.send_command(f"PART {channel}")
        return self.receive_response()

    def send_private_message(self, argument):
        """Envía un mensaje privado a un usuario o canal."""
        parts = argument.split(" ", 1)
        if len(parts) < 2:
            return "⚠️ Error: Debes proporcionar un destinatario y un mensaje"
        target, message = parts
        self.send_command(f"PRIVMSG {target} :{message}")
        return self.receive_response()

    def send_notice(self, argument):
        """Envía un mensaje NOTICE a un usuario o canal."""
        parts = argument.split(" ", 1)
        if len(parts) < 2:
            return "⚠️ Error: Debes proporcionar un destinatario y un mensaje"
        target, message = parts
        self.send_command(f"NOTICE {target} :{message}")
        return self.receive_response()
    
    def list_channels(self):
        """Solicita la lista de canales al servidor."""
        self.send_command("LIST")
        return self.receive_response()
    
    def list_users(self, channel):
        """Lista los usuarios de un canal específico."""
        if not channel.startswith("#"):
            return "⚠️ Error: Los canales IRC deben comenzar con '#'"
        self.send_command(f"NAMES {channel}")
        return self.receive_response()
    
    def whois_user(self, user):
        """Obtiene información sobre un usuario."""
        self.send_command(f"WHOIS {user}")
        return self.receive_response()
    
    def change_topic(self, argument):
        """Cambia o consulta el tema de un canal."""
        parts = argument.split(" ", 1)
        if len(parts) < 1:
            return "⚠️ Error: Debes proporcionar un canal"
        channel = parts[0]
        topic = parts[1] if len(parts) > 1 else ""
        if topic:
            self.send_command(f"TOPIC {channel} :{topic}")
        else:
            self.send_command(f"TOPIC {channel}")
        return self.receive_response()
    
    def quit_server(self):
        """Sale del servidor IRC enviando el comando QUIT."""
        self.send_command("QUIT :Saliendo del servidor")
        self.sock.close()
        return "🔌 Desconectado del servidor IRC"

def parse_arguments():
    parser = argparse.ArgumentParser(description="Parser de pruebas para cliente IRC")
    parser.add_argument("-p", type=int, help="Puerto del servidor IRC", required=True)
    parser.add_argument("-H", type=str, help="Host del servidor IRC", required=True)
    parser.add_argument("-n", type=str, help="Nickname del usuario", required=True)
    parser.add_argument("-c", type=str, help="Comando de IRC a ejecutar", required=True)
    parser.add_argument("-a", type=str, help="Argumento del comando", required=False, default="")

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()

    # Crear el cliente y conectar al servidor
    client = IRCClient(args.H, args.p, args.n)
    client.connect()

    # Ejecutar el comando desde el test
    response = client.handle_command(args.c, args.a)

    # Mostrar la respuesta del servidor
    print(response)
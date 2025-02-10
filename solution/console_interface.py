import cmd
from Client import IRCClient

class IRCInterface(cmd.Cmd):
    prompt = '> '
    intro = 'Bienvenido al cliente IRC. Escribe "help" para ver los comandos disponibles.'

    def __init__(self):
        super().__init__()
        self.client = None
        self.connected = False

    def do_connect(self, arg):
        """Conectarse al servidor IRC: connect <host> <puerto> <nick>"""
        try:
            host, port, nick = arg.split()
            self.client = IRCClient(host, int(port), nick)
            self.client.connect()
            self.client.start_receiving()
            self.connected = True
            self.prompt = f'{nick}> '
            print(f"Conectado al servidor {host}:{port} como {nick}")
        except ValueError:
            print("Error: Uso correcto: connect <host> <puerto> <nick>")
        except Exception as e:
            print(f"Error al conectar: {e}")

    def do_nick(self, arg):
        """Cambiar nickname: nick <nuevo_nick>"""
        if not self.check_connection():
            return
        if not arg:
            print("Error: Debes especificar un nuevo nickname")
            return
        self.client.handle_command("/nick", arg)
        self.prompt = f'{arg}> '

    def do_join(self, arg):
        """Unirse a un canal: join <canal>"""
        if not self.check_connection() or not arg:
            return
        self.client.handle_command("/join", arg)

    def do_msg(self, arg):
        """Enviar mensaje privado: msg <destinatario> <mensaje>"""
        if not self.check_connection():
            return
        self.client.handle_command("/privmsg", arg)

    def do_notice(self, arg):
        """Enviar notificación: notice <destinatario> <mensaje>"""
        if not self.check_connection():
            return
        self.client.handle_command("/notice", arg)

    def do_part(self, arg):
        """Salir de un canal: part <canal>"""
        if not self.check_connection():
            return
        self.client.handle_command("/part", arg)

    def do_list(self, arg):
        """Listar canales disponibles"""
        if not self.check_connection():
            return
        self.client.handle_command("/list", "")

    def do_names(self, arg):
        """Listar usuarios en un canal: names <canal>"""
        if not self.check_connection():
            return
        self.client.handle_command("/names", arg)

    def do_topic(self, arg):
        """Ver o cambiar el tema de un canal: topic <canal> [nuevo_tema]"""
        if not self.check_connection():
            return
        self.client.handle_command("/topic", arg)

    def do_quit(self, arg):
        """Salir del cliente IRC"""
        if self.connected:
            self.client.handle_command("/quit", "")
        print("¡Hasta luego!")
        return True

    def check_connection(self):
        """Verifica si el cliente está conectado"""
        if not self.connected:
            print("Error: No estás conectado. Usa el comando 'connect' primero.")
            return False
        return True

    def default(self, line):
        """Maneja mensajes que no son comandos"""
        if self.connected and line:
            self.client.send_command(line)

def main():
    interface = IRCInterface()
    try:
        interface.cmdloop()
    except KeyboardInterrupt:
        if interface.connected:
            interface.do_quit("")
        print("\n¡Hasta luego!")

if __name__ == "__main__":
    main() 
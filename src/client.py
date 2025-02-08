import socket
import threading
import time

class IRCClient:
    def __init__(self, server, port, nickname, realname, password=None):
        self.server = server
        self.port = port
        self.nickname = nickname
        self.realname = realname
        self.password = password  # Contraseña de NickServ (si aplica)
        self.irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True

    def connect(self):
        """Conecta al servidor IRC y se registra con el NICK y USER"""
        self.irc.connect((self.server, self.port))
        self.send_raw(f'NICK {self.nickname}')
        self.send_raw(f'USER {self.nickname} 0 * :{self.realname}')

        # Si se proporcionó una contraseña, intentamos autenticar la cuenta
        if self.password:
            self.authenticate()

    def send_raw(self, message):
        """Envía un mensaje raw al servidor IRC"""
        self.irc.send(bytes(f"{message}\r\n", "UTF-8"))
    
    def authenticate(self):
        """Envía un comando IDENTIFY a NickServ si hay contraseña"""
        self.send_raw(f'MSG NickServ IDENTIFY {self.password}')

    def listen(self):
        """Escucha los mensajes del servidor y maneja eventos"""
        while self.running:
            try:
                response = self.irc.recv(2048).decode("UTF-8")
                print(response)  # Muestra el mensaje recibido

                if response.startswith("PING"):
                    self.pong(response)
                
                # Respuesta de bienvenida, unirse al canal
                if "001" in response:  # RPL_WELCOME
                    self.join_channel()

                # Aquí puedes agregar más respuestas de servidor para manejar
                # otros eventos como errores, etc.
            
            except UnicodeDecodeError as e:
                print(f"Error de codificación: {e}. Respuesta no válida.")
                
    def pong(self, message):
        """Responder al PING del servidor con un PONG"""
        server = message.split()[1]
        self.send_raw(f'PONG {server}')

    def join_channel(self):
        """Se une a un canal IRC"""
        self.send_raw(f'JOIN #miCanal')  # Reemplaza con el canal que quieras unirte

    def send_message(self, target, message):
        """Envía un mensaje PRIVMSG a un canal o usuario"""
        self.send_raw(f'PRIVMSG {target} :{message}')

    def quit(self, message="Adiós!"):
        """Cierra la conexión con el servidor IRC"""
        self.send_raw(f'QUIT :{message}')
        self.irc.close()

    def interactive_mode(self):
        """Modo interactivo para ingresar comandos manualmente"""
        while self.running:
            user_input = input("Comando IRC: ")
            if user_input.lower() == 'quit':
                self.quit("Usuario se desconecta.")
                self.running = False
                break
            elif user_input.startswith("msg"):
                parts = user_input.split(" ", 2)
                if len(parts) >= 3:
                    self.send_message(parts[1], parts[2])
                else:
                    print("Uso incorrecto. Usa: msg <destino> <mensaje>")
            elif user_input.startswith("join"):
                parts = user_input.split(" ", 1)
                if len(parts) >= 2:
                    self.send_raw(f'JOIN {parts[1]}')
                else:
                    print("Uso incorrecto. Usa: join <canal>")
            else:
                self.send_raw(user_input)
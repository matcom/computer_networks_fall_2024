import socket
import threading

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
        """Conecta al servidor IRC y se registra con NICK y USER"""
        self.irc.connect((self.server, self.port))

        if self.password:
            self.send_raw(f'PASS {self.password}')
        
        self.send_raw(f'NICK {self.nickname}')
        self.send_raw(f'USER {self.nickname} 0 * :{self.realname}')

    def send_raw(self, message):
        """Envía un mensaje en formato RAW al servidor"""
        self.irc.send(bytes(f"{message}\r\n", "UTF-8"))

    def listen(self):
        """Escucha los mensajes del servidor y maneja eventos"""
        while self.running:
            try:
                response = self.irc.recv(2048).decode("UTF-8")
                print(response)

                if response.startswith("PING"):
                    self.pong(response)

            except UnicodeDecodeError as e:
                print(f"Error de codificación: {e}")

    def pong(self, message):
        """Responde a PING con PONG"""
        server = message.split()[1]
        self.send_raw(f'PONG {server}')

    ## ---- FUNCIONES NICKSERV ---- ##
    
    def nickserv_register(self, email, password):
        """Registra un nuevo nick con NickServ"""
        self.send_raw(f'PRIVMSG NickServ :REGISTER {password} {email}')
    
    def nickserv_identify(self, password):
        """Identifica el usuario con NickServ"""
        self.send_raw(f'PRIVMSG NickServ :IDENTIFY {password}')

    def nickserv_set_password(self, old_password, new_password):
        """Cambia la contraseña del nick"""
        self.send_raw(f'PRIVMSG NickServ :SET PASSWORD {old_password} {new_password}')

    def nickserv_recover(self, nickname, password):
        """Recupera el control de un nick en caso de desconexión abrupta"""
        self.send_raw(f'PRIVMSG NickServ :RECOVER {nickname} {password}')

    def nickserv_release(self, nickname, password):
        """Libera un nick bloqueado"""
        self.send_raw(f'PRIVMSG NickServ :RELEASE {nickname} {password}')

    def nickserv_confirm(self, code):
        """Confirma el registro del nick (usando un código enviado por email)"""
        self.send_raw(f'PRIVMSG NickServ :CONFIRM {code}')

    def nickserv_info(self, nickname):
        """Obtiene información sobre un nick"""
        self.send_raw(f'PRIVMSG NickServ :INFO {nickname}')

    ## ---- FUNCIONES GENERALES ---- ##
    
    def quit(self, message="Adiós!"):
        """Cierra la conexión con el servidor IRC"""
        self.send_raw(f'QUIT :{message}')
        self.irc.close()
        self.running = False

    def interactive_mode(self):
        """Modo interactivo para ingresar comandos manualmente"""
        while self.running:
            user_input = input("IRC Command> ").strip()

            if user_input.lower() == 'quit':
                self.quit("Desconectando...")
                break

            elif user_input.startswith("register "):
                parts = user_input.split(" ", 2)
                if len(parts) == 3:
                    self.nickserv_register(parts[1], parts[2])
                else:
                    print("Uso: register <email> <contraseña>")

            elif user_input.startswith("identify "):
                parts = user_input.split(" ", 1)
                if len(parts) == 2:
                    self.nickserv_identify(parts[1])
                else:
                    print("Uso: identify <contraseña>")

            elif user_input.startswith("setpass "):
                parts = user_input.split(" ", 2)
                if len(parts) == 3:
                    self.nickserv_set_password(parts[1], parts[2])
                else:
                    print("Uso: setpass <contraseña_actual> <nueva_contraseña>")

            elif user_input.startswith("recover "):
                parts = user_input.split(" ", 2)
                if len(parts) == 3:
                    self.nickserv_recover(parts[1], parts[2])
                else:
                    print("Uso: recover <nick> <contraseña>")

            elif user_input.startswith("release "):
                parts = user_input.split(" ", 2)
                if len(parts) == 3:
                    self.nickserv_release(parts[1], parts[2])
                else:
                    print("Uso: release <nick> <contraseña>")

            elif user_input.startswith("confirm "):
                parts = user_input.split(" ", 1)
                if len(parts) == 2:
                    self.nickserv_confirm(parts[1])
                else:
                    print("Uso: confirm <código>")

            elif user_input.startswith("info "):
                parts = user_input.split(" ", 1)
                if len(parts) == 2:
                    self.nickserv_info(parts[1])
                else:
                    print("Uso: info <nick>")

            else:
                self.send_raw(user_input)

import socket
import threading
import ssl
from .session import Session
from .commands import CommandHandler
from .parser import CommandParser

class SMTPServer:
    def __init__(self, host="localhost", port=1025):
        self.host = host
        self.port = port
        self.certfile = "src/server/certs/cert.pem"
        self.keyfile = "src/server/certs/key.pem"
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        print(f"Server listening on {self.host}:{self.port}")
        
        while True:
            client_socket, addr = self.socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        session = Session()
        client_socket.send(b"220 smtp.server.com ESMTP Ready\r\n")
        
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                command, arg = CommandParser.parse(data)
                
                # Procesar comando y obtener posible socket seguro
                result = self.process_command(client_socket, session, command, arg)
                
                if command == "STARTTLS":
                    # Reemplazar el socket por el seguro
                    client_socket = result  # result es el socket seguro
                    continue  # Saltar al siguiente ciclo del bucle
                
                # Enviar respuesta para otros comandos
                client_socket.send(result.encode())
                
                if command == "AUTH" and "334" in result:
                    # Manejar el flujo de autenticación para AUTH LOGIN
                    while True:
                        data = client_socket.recv(1024)
                        if not data:
                            break
                        credential = data.decode().strip()
                        result = CommandHandler.auth_login_password(session, credential)
                        client_socket.send(result.encode())
                        if "235" in result or "535" in result:
                            break
                
                if command == "QUIT":
                    break
        finally:
            client_socket.close()

    def process_command(self, client_socket, session, command, arg):
        if command == "STARTTLS":
            return self.upgrade_tls(client_socket, session)  # Retorna el socket seguro
        
        handler = {
            "EHLO": lambda: CommandHandler.ehlo(session, arg),
            "MAIL": lambda: CommandHandler.mail_from(session, arg.split(":")[1].strip()),
            "RCPT": lambda: CommandHandler.rcpt_to(session, arg.split(":")[1].strip()),
            "DATA": lambda: CommandHandler.data(client_socket),
            "QUIT": CommandHandler.quit,
            "AUTH": lambda: CommandHandler.auth(session, arg.split()[0], arg.split()[1] if len(arg.split()) > 1 else None),
        }.get(command, lambda: "500 Unknown command\r\n")
        
        return handler()

    def upgrade_tls(self, client_socket, session):
        response = CommandHandler.starttls(session)
        client_socket.send(response.encode())  # Envía "220 Ready to start TLS"
        
        # Crear contexto TLS
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)
        
        # Envolver el socket en TLS (sin cerrar el original)
        secure_socket = context.wrap_socket(client_socket, server_side=True)
        secure_socket.do_handshake()  # Realizar handshake TLS
        
        session.tls_active = True
                
        return secure_socket  # Retornar el socket seguro
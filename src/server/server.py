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
                response = self.process_command(client_socket, session, command, arg)
                client_socket.send(response.encode())
                
                if command == "QUIT":
                    break
        finally:
            client_socket.close()

    def process_command(self, client_socket, session, command, arg):
        handler = {
            "EHLO": lambda: CommandHandler.ehlo(session, arg),
            "STARTTLS": lambda: self.upgrade_tls(client_socket, session),
            "MAIL": lambda: CommandHandler.mail_from(session, arg.split(":")[1].strip()),
            "RCPT": lambda: CommandHandler.rcpt_to(session, arg.split(":")[1].strip()),
            "DATA": lambda: CommandHandler.data(client_socket),
            "QUIT": CommandHandler.quit,
        }.get(command, lambda: "500 Unknown command\r\n")
        
        return handler()

    def upgrade_tls(self, client_socket, session):
        response = CommandHandler.starttls(session)
        client_socket.send(response.encode())
        
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=self.certfile, keyfile=self.keyfile)
        
        secure_socket = context.wrap_socket(client_socket, server_side=True)
        session.tls_active = True
        
        # Reemplazar el socket original
        client_socket.close()
        return "250 TLS negotiation successful\r\n"
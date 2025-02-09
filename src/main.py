import threading
from client import IRCClient as ircc

server = input("Enter the server url\n>")
port = int(input("Enter server port\n>"))
nickname = input("Enter your nickname\n>")
realname = input("Enter real name\n>")

client = ircc(server, port, nickname, realname)

# Conectar al servidor
client.connect()

# Iniciar hilo para escuchar mensajes del servidor
listen_thread = threading.Thread(target=client.listen)
listen_thread.daemon = True
listen_thread.start()

# Iniciar modo interactivo
client.interactive_mode()
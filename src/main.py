import threading
from client import IRCClient as ircc

server = "irc.libera.chat"
port = 6667
nickname = "jotica0602"
realname = "Alex Brunet"
password = "Poseidon123*"  # La contraseña que elegiste al registrar la cuenta IRC

client = ircc(server, port, nickname, realname, password)

# Conectar al servidor
client.connect()

# Iniciar hilo para escuchar mensajes del servidor
listen_thread = threading.Thread(target=client.listen)
listen_thread.daemon = True
listen_thread.start()

# Iniciar modo interactivo
client.interactive_mode()
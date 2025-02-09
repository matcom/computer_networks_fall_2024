class User:
    def __init__(self, socket, nick=None):
        self.socket = socket
        self.nick = nick
        self.visibility = True  # Por defecto el usuario es visible
        
    def send_message(self, message):
        """Envía un mensaje al usuario"""
        self.socket.sendall(f"{message}\r\n".encode())
        
    def set_visibility(self, visible):
        """Cambia la visibilidad del usuario"""
        self.visibility = visible
        
    def __eq__(self, other):
        """Dos usuarios son iguales si tienen el mismo nick"""
        if isinstance(other, User):
            return self.nick == other.nick
        return False
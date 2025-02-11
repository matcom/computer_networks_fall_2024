from cryptography.fernet import Fernet
from secret_key import SECRET_KEY
class User:
    def __init__(self, socket, nick=None):
        self.socket = socket
        self.nick = nick
        self.visibility = True  # Por defecto el usuario es visible
        self.cipher = Fernet(SECRET_KEY)
    def send_message(self, message):
        """Envía un mensaje al usuario"""
        encrypted_response = self.cipher.encrypt((message + "\r\n").encode())
        self.socket.sendall(encrypted_response)
        
    def set_visibility(self, visible):
        """Cambia la visibilidad del usuario"""
        self.visibility = visible
        
    def __eq__(self, other):
        """Dos usuarios son iguales si tienen el mismo nick"""
        if isinstance(other, User):
            return self.nick == other.nick
        return False
# src/response.py

from .exceptions import SMTPException, TemporarySMTPException, PermanentSMTPException
from .response import SMTPResponse
import base64
import random
import string

def generate_boundary():
    chars = string.ascii_letters + string.digits
    return "BOUNDARY_" + "".join(random.choice(chars) for _ in range(16))

def validate_email(email):
    import re
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def credentials_for_plain_authentication( username: str, password: str) -> str:
    """
    Credenciales encriptadas del cliente utilizando PLAIN.

    :param username: Nombre de usuario.
    :param password: Contraseña del usuario.
    :return: Respuesta del servidor después de la autenticación.
    """
    credentials = f"\0{username}\0{password}"
    encoded_credentials = base64.b64encode(credentials.encode(encoding='us-ascii')).decode()
    return encoded_credentials

def credentials_for_login_authentication( username: str, password: str):
    """
    Credenciales encriptadas del cliente utilizando LOGIN.
    
    :param username: Nombre de usuario.
    :param password: Contraseña del usuario.
    :return: Respuesta del servidor después de la autenticación.
    """
    username_b64 = base64.b64encode(username.encode('us-ascii')).decode()
    password_b64 = base64.b64encode(password.encode('us-ascii')).decode()
    return username_b64, password_b64

def encode_attachment(filepath: str):
    import base64
    
    try:
        with open(filepath, "rb") as f:
            file_data = f.read()
        
        encoded = base64.b64encode(file_data).decode("us-ascii")
        
        # Dividir en líneas de 76 caracteres (requerido por el estándar)
        chunked = "\r\n".join(
            [encoded[i:i+76] for i in range(0, len(encoded), 76)]
        )
        
        return chunked
        
    except Exception as e:
        raise SMTPException(f"Error al adjuntar archivo: {e}")
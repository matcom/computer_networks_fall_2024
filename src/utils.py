# src/response.py

from .exceptions import SMTPException, TemporarySMTPException, PermanentSMTPException
from .response import SMTPResponse
import base64
import base64
import hmac
from hashlib import md5

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

def credentials_for_cram_md5_authentication(response: SMTPResponse, username: str, password: str) -> str:
    """
    Credenciales encriptadas del cliente utilizando CRAM-MD5.
    
    :param response: Respuesta del servidor después de la autenticación.
    :param username: Nombre de usuario.
    :param password: Contraseña del usuario.
    :return: Respuesta del servidor después de la autenticación.
    """

    challenge = base64.b64decode(response.message.strip())
    digest = hmac.new(password.encode(), challenge, md5).hexdigest()
    credentials = f"{username} {digest}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    return encoded_credentials

def credentials_for_xoauth2_authentication(username: str, token: str) -> str:
    """
    Credenciales encriptadas del cliente utilizando XOAUTH2.

    :param username: Dirección de correo del usuario.
    :param token: Token de acceso OAuth2.
    :return: Respuesta del servidor después de la autenticación.
    """

    # Formato del token XOAUTH2
    credentials = f"user={username}\x01auth=Bearer {token}\x01\x01"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    return encoded_credentials
 
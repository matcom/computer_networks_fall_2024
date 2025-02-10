import base64
import re

class CommandHandler:
    @staticmethod
    def ehlo(session, domain: str):
        # Reiniciar solo los campos relacionados con el correo electrónico
        session.mail_from = None
        session.recipients = []
        session.data = []
        
        # Actualizar el host del cliente
        session.client_host = domain
        
        # Construir la respuesta EHLO
        response = "250-smtp.server.com Hello\r\n"
        
        # Agregar capacidades basadas en el estado de la sesión
        if not session.tls_active:
            response += "250-STARTTLS\r\n"  # Ofrecer STARTTLS si no está activo
        
        if session.tls_active:
            response += "250-AUTH PLAIN LOGIN\r\n"  # Ofrecer AUTH si TLS está activo
        
        response += "250 OK\r\n"
        
        return response

    @staticmethod
    def starttls(session):
        if session.tls_active:
            return "454 TLS already active\r\n"
        return "220 Ready to start TLS\r\n"

    # Expresión regular para validación básica de emails (RFC 5322 simplificado)
    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

    @staticmethod
    def _validate_email_format(address: str) -> bool:
        """Valida el formato básico de una dirección de correo"""
        return CommandHandler.EMAIL_REGEX.match(address) is not None

    @staticmethod
    def _parse_address(arg: str) -> str:
        """Extrae la dirección del formato MAIL FROM:<address> o RCPT TO:<address>"""
        if arg.startswith("<") and arg.endswith(">"):
            return arg[1:-1]
        return arg

    @staticmethod
    def mail_from(session, arg: str):
        if not session.tls_active:
            return "530 Must issue STARTTLS first\r\n"
        if not session.authenticated:
            return "530 Authentication required\r\n"
        
        address = CommandHandler._parse_address(arg)
        
        if not CommandHandler._validate_email_format(address):
            return "501 Invalid email format\r\n"
        
        session.mail_from = address
        return "250 OK\r\n"

    @staticmethod
    def rcpt_to(session, arg: str):
        if not session.tls_active:
            return "530 Must issue STARTTLS first\r\n"
        if not session.authenticated:
            return "530 Authentication required\r\n"
        if not session.mail_from:
            return "503 Need MAIL command before RCPT\r\n"
        
        address = CommandHandler._parse_address(arg)
        
        if not CommandHandler._validate_email_format(address):
            return "501 Invalid email format\r\n"
        
        # # Límite máximo de destinatarios (ej: 100)
        # if len(session.recipients) >= 100:
        #     return "452 Too many recipients\r\n"
        
        session.recipients.append(address)
        return "250 OK\r\n"

    @staticmethod
    def data(session, client_socket):
        if not session.mail_from:
            return "503 Need MAIL command\r\n"
        if not session.recipients:
            return "503 Need RCPT command\r\n"
        
        client_socket.send(b"354 End data with <CR><LF>.<CR><LF>\r\n")
        buffer = bytearray()
        
        while True:
            data = client_socket.recv(1024)
            if not data:
                return "421 Connection timed out\r\n"
            
            buffer.extend(data)
            
            if b"\r\n.\r\n" in buffer:
                end_index = buffer.index(b"\r\n.\r\n")
                message = buffer[:end_index]
                
                # Guardar mensaje en la sesión
                session.data = message.decode('us-ascii', errors='replace')
                
                # Reset de transacción
                session.mail_from = None
                session.recipients = []
                
                return "250 Message accepted\r\n"
            
            if len(buffer) > 10_485_760:  # 10MB límite
                return "552 Message size exceeds limit\r\n"
    
    @staticmethod
    def quit():
        return "221 Bye\r\n"

    @staticmethod
    def auth(session, mechanism: str, credential: str = None):
        if not session.tls_active:
            return "530 Must issue STARTTLS first\r\n"
        
        if mechanism.upper() == "PLAIN":
            return CommandHandler.auth_plain(session, credential)
        elif mechanism.upper() == "LOGIN":
            return CommandHandler.auth_login(session, credential)
        else:
            return "504 Unrecognized authentication type\r\n"

    @staticmethod
    def auth_plain(session, credential: str):
        try:
            decoded_credential = base64.b64decode(credential).decode('us-ascii')
            parts = decoded_credential.split('\0')
            if len(parts) == 3:
                username, password = parts[1], parts[2]
                # Verificar credenciales (ejemplo simple)
                if username == "user" and password == "pass":
                    session.authenticated = True
                    return "235 Authentication successful\r\n"
                else:
                    return "535 Authentication failed\r\n"
            else:
                return "535 Invalid credential format\r\n"
        except Exception as e:
            return f"535 Authentication error: {str(e)}\r\n"

    @staticmethod
    def auth_login(session, credential: str = None):
        if not credential:
            # Solicitar el username
            return "334 VXNlcm5hbWU6\r\n"  # "Username:" en base64
        else:
            # Decodificar el username
            try:
                username = base64.b64decode(credential).decode('us-ascii')
                session.auth_username = username
                # Solicitar la contraseña
                return "334 UGFzc3dvcmQ6\r\n"  # "Password:" en base64
            except Exception as e:
                return f"535 Authentication error: {str(e)}\r\n"

    @staticmethod
    def auth_login_password(session, password_credential: str):
        try:
            password = base64.b64decode(password_credential).decode('us-ascii')
            # Verificar credenciales (ejemplo simple)
            if session.auth_username == "user" and password == "pass":
                session.authenticated = True
                return "235 Authentication successful\r\n"
            else:
                return "535 Authentication failed\r\n"
        except Exception as e:
            return f"535 Authentication error: {str(e)}\r\n"
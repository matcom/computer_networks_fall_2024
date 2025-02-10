import base64

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

    @staticmethod
    def mail_from(session, address: str):
        if not session.tls_active:
            return "530 Must issue STARTTLS first\r\n"
        if not session.authenticated:
            return "530 Authentication required\r\n"
        session.mail_from = address
        return "250 OK\r\n"

    @staticmethod
    def rcpt_to(session, address: str):
        if not session.tls_active:
            return "530 Must issue STARTTLS first\r\n"
        if not session.authenticated:
            return "530 Authentication required\r\n"
        session.recipients.append(address)
        return "250 OK\r\n"

    @staticmethod
    def data(client_socket):
        client_socket.send(b"354 End data with <CR><LF>.<CR><LF>\r\n")
        message = []
        while True:
            data = client_socket.recv(1024).decode()
            if data.strip() == ".":
                break
            message.append(data)
        return "250 Message accepted\r\n"

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
            decoded_credential = base64.b64decode(credential).decode('utf-8')
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
                username = base64.b64decode(credential).decode('utf-8')
                session.auth_username = username
                # Solicitar la contraseña
                return "334 UGFzc3dvcmQ6\r\n"  # "Password:" en base64
            except Exception as e:
                return f"535 Authentication error: {str(e)}\r\n"

    @staticmethod
    def auth_login_password(session, password_credential: str):
        try:
            password = base64.b64decode(password_credential).decode('utf-8')
            # Verificar credenciales (ejemplo simple)
            if session.auth_username == "user" and password == "pass":
                session.authenticated = True
                return "235 Authentication successful\r\n"
            else:
                return "535 Authentication failed\r\n"
        except Exception as e:
            return f"535 Authentication error: {str(e)}\r\n"
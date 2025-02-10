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
        session.mail_from = address
        return "250 OK\r\n"

    @staticmethod
    def rcpt_to(session, address: str):
        if not session.tls_active:
            return "530 Must issue STARTTLS first\r\n"
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
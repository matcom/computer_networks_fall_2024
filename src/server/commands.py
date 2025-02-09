class CommandHandler:
    @staticmethod
    def ehlo(session, domain: str):
        session.reset()
        session.client_host = domain
        return (
            "250-smtp.server.com Hello\r\n"
            "250-STARTTLS\r\n"
            "250-AUTH PLAIN LOGIN\r\n"
            "250 OK\r\n"
        )

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
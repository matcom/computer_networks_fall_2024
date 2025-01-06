class SMTPCommands:
    def __init__(self, connection):
        self.connection = connection

    def ehlo(self, domain):
        self.connection.send(f"EHLO {domain}\r\n")
        return self.connection._receive()

    def mail_from(self, sender):
        self.connection.send(f"MAIL FROM:<{sender}>\r\n")
        return self.connection._receive()

    def rcpt_to(self, recipient):
        self.connection.send(f"RCPT TO:<{recipient}>\r\n")
        return self.connection._receive()

    def data(self, message):
        self.connection.send("DATA\r\n")
        self.connection._receive()
        self.connection.send(f"{message}\r\n.\r\n")
        return self.connection._receive()

    def quit(self):
        self.connection.send("QUIT\r\n")
        return self.connection._receive()

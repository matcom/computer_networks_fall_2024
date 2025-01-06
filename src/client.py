from .connection import SMTPConnection
from .commands import SMTPCommands
from .response import SMTPResponse
from .exceptions import SMTPException, TemporarySMTPException, PermanentSMTPException
from .utils import validate_email

class SMTPClient:
    def __init__(self, host, port):
        self.connection = SMTPConnection(host, port)
        self.commands = SMTPCommands(self.connection)

    def send_mail(self, sender, recipient, message):
        if not validate_email(sender) or not validate_email(recipient):
            raise SMTPException("Invalid email address")

        self.connection.connect()
        try:
            response = self.commands.ehlo("localhost")
            print(SMTPResponse.parse(response).message)

            response = self.commands.mail_from(sender)
            print(SMTPResponse.parse(response).message)

            response = self.commands.rcpt_to(recipient)
            print(SMTPResponse.parse(response).message)

            response = self.commands.data(message)
            print(SMTPResponse.parse(response).message)
            
        except TemporarySMTPException as e:
            print(f"Temporary error: {e}")
        except PermanentSMTPException as e:
            print(f"Permanent error: {e}")
        finally:
            response = self.commands.quit()
            print(SMTPResponse.parse(response).message)
            self.connection.close()

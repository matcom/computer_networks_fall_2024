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
            print(response)

            response = self.commands.mail_from(sender)
            print(response)

            response = self.commands.rcpt_to(recipient)
            print(response)

            response = self.commands.data(message)
            print(response)
            
        except TemporarySMTPException as e:
            print(f"Error temporal: {e}. Puedes reintentar más tarde.")
        except PermanentSMTPException as e:
            print(f"Error permanente: {e}. No puedes continuar con esta operación.")
        except SMTPException as e:
            print(f"Error general de SMTP: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")
        finally:
            response = self.commands.quit()
            print(response)
            self.connection.close()
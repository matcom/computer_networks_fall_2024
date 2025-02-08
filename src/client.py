# src/client.py

from .connection import SMTPConnection
from .commands import SMTPCommands
from .response import SMTPResponse
from .exceptions import SMTPException, TemporarySMTPException, PermanentSMTPException
from .utils import validate_email

          
class SMTPClient:
    """
    Cliente SMTP que maneja conexión, autenticación y envío de correos.
    """

    def __init__(self, host, port):
        """
        Inicializa el cliente SMTP.

        :param connection: Instancia de SMTPConnection.
        """
        self.connection = SMTPConnection(host, port)
        self.commands = SMTPCommands(self.connection)
        self.auth_methods = None
        self.supports_tls = False

    def connect(self):
        """
        Establece la conexión con el servidor SMTP y realiza el handshake inicial (EHLO).
        """
        try:
            self.connection.connect()
            response = self.commands.ehlo(self.connection.host)
            
            if not response.is_success():
                raise SMTPException(f"Error en EHLO: {response}")
                      
            # Parsear capacidades del servidor si EHLO tiene éxito
            self.auth_methods = None
            for line in response.message.splitlines():
                if "AUTH" in line:
                    self.auth_methods = line.split("AUTH")[1].strip().split(' ')
                elif "STARTTLS" in line:
                    self.supports_tls = True
            
            print(response)
            
        except Exception as e:
            raise SMTPException(f"Error al conectar: {e}")

    def tls_conncection(self):
        """
        Establece la conexión segura con el servidor SMTP a traves de TLS y realiza el handshake inicial (EHLO).
        """
        if not self.tls_conncection:
            raise SMTPException(f"El servidor no soporta TLS")
        
        self.connection.start_tls()
        
        # Reenviar EHLO después de iniciar TLS
        response = self.commands.ehlo(self.connection.host)
        if not response.is_success():
            raise SMTPException(f"Error en EHLO tras STARTTLS: {response}")

    
        # Parsear capacidades del servidor si EHLO tiene éxito
        self.auth_methods = None
        for line in response.message.splitlines():
            if "AUTH" in line:
                self.auth_methods = line.split("AUTH")[1].strip().split(' ')

    
    def disconnect(self):
        """
        Cierra la conexión SMTP de manera ordenada.
        """
        try:
            print(self.commands.quit())
            print(self.connection.close())
        except Exception as e:
            raise SMTPException(f"Error al desconectar: {e}")
            
    def authenticate(self, mechanism: str, username: str, password: str):
        """
        Autentica al cliente con el servidor SMTP utilizando el mecanismo especificado.
        """
        
        if not self.auth_methods:
            raise SMTPException(f"Autentificación no implementada en el servidor")
        
        if mechanism.upper() not in self.auth_methods:
            raise SMTPException(f"Mecanismo no soportado por el servidor: {mechanism}")
        
        try:
            response = self.commands.authenticate(mechanism, username, password)
            if not response.is_success():
                raise SMTPException(f"Autenticación fallida: {response}")
            
            print(response)
            
        except Exception as e:
            raise SMTPException(f"Error durante la autenticación: {e}")

    def does_server_supports_authentication(self, auth_type=None) -> bool:
        """
        Se verifica si el servidor SMTP soporta autenticación.
        """
        
        if not self.auth_methods:
            return False
        if not auth_type:
            return True
        
        return self.auth_methods.__contains__(auth_type)
    
    def does_server_supprorts_tls(self):
        """
        Se verifica si el servidor SMTP soporta TLS.
        """
        return self.tls_conncection
    
    def send_mail(self, sender: str, recipients: list, subject: str, body: str):
        """
        Envía un correo electrónico utilizando la conexión SMTP establecida.

        :param sender: Dirección del remitente.
        :param recipients: Lista de direcciones de los destinatarios.
        :param subject: Asunto del correo.
        :param body: Cuerpo del correo.
        """
        
        if not validate_email(sender) or not all(validate_email(recipient) for recipient in recipients):
            raise SMTPException("Invalid email address")
        
        try:
            print(self.commands.mail_from(sender))
            
            for recipient in recipients:
                print(self.commands.rcpt_to(recipient))
            
            message = f"Subject: {subject}\r\n\r\n{body}"
            
            print(self.commands.data(message))
            
        except TemporarySMTPException as e:
            print(f"Error temporal: {e}. Puedes reintentar más tarde.")
        except PermanentSMTPException as e:
            print(f"Error permanente: {e}. No puedes continuar con esta operación.")
        except SMTPException as e:
            print(f"Error general de SMTP: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")
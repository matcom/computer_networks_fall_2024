# src/client.py

from .connection import SMTPConnection
from .commands import SMTPCommands
from .response import SMTPResponse
from .exceptions import SMTPException, TemporarySMTPException, PermanentSMTPException
from .utils import validate_email
import json
          
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

    def connect_by_tls(self):
        """
        Establece la conexión segura con el servidor SMTP a traves de TLS y realiza el handshake inicial (EHLO).
        """
        if not self.connect_by_tls:
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
            self.connection.close()
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
        return self.connect_by_tls
    
    def send_mail(self, sender: str, recipients: list, subject: str, body: str, headers: str | dict = None):
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
            
            #
            headers_string = self.format_headers(headers, sender, recipients)

            # Incluir Subject manualmente
            formatted_message = f"{headers_string}\r\nSubject: {subject}\r\n\r\n{body}"
                
            print(self.commands.data(formatted_message))
            
        except TemporarySMTPException as e:
            print(f"Error temporal: {e}. Puedes reintentar más tarde.")
        except PermanentSMTPException as e:
            print(f"Error permanente: {e}. No puedes continuar con esta operación.")
        except SMTPException as e:
            print(f"Error general de SMTP: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")
            
    def format_headers(self, headers, sender, recipients):
        """
        Formatea y valida los headers para asegurar que cumplan con RFC 5322.

        :param headers: Headers en formato string (saltos de línea), JSON (dict) o string con formato JSON.
        :param sender: Dirección de correo del remitente.
        :param recipients: Lista de direcciones de los destinatarios.
        :return: String con los headers formateados.
        :raises SMTPException: Si los headers no son válidos.
        """

        # Si los headers están en formato JSON (dict), los usamos directamente
        if not headers:
            headers_dict = {}
        
        elif isinstance(headers, dict):
            headers_dict = headers

        # Si es un string con formato JSON, lo convertimos a diccionario
        elif isinstance(headers, str) and headers.strip().startswith("{"):
            try:
                #headers = headers.replace('\\', '')  # Eliminar las comillas escapadas
                headers_dict = json.loads(headers)
            except json.JSONDecodeError:
                raise SMTPException("Formato JSON inválido en los headers.")

        # Si es un string con saltos de línea, lo convertimos a diccionario
        elif isinstance(headers, str):
            headers_dict = {}
            for line in headers.split("\n"):
                if ": " in line:
                    key, value = line.split(": ", 1)
                    headers_dict[key.strip()] = value.strip()

        else:
            raise SMTPException("Formato de headers no válido. Use un string, JSON o diccionario.")

        # Validar y construir los headers
        validated_headers = {}

        # Validar que "From" y "To" coincidan con los valores de sender y recipients
        if "From" in headers_dict:
            if headers_dict["From"] != sender:
                raise SMTPException("El header 'From' no coincide con el remitente proporcionado.")
            validated_headers["From"] = headers_dict["From"]
        else:
            validated_headers["From"] = sender  # Si no está en headers, lo agregamos.

        if "To" in headers_dict:
            if set(headers_dict["To"].split(", ")) != set(recipients):
                raise SMTPException("El header 'To' no coincide con los destinatarios proporcionados.")
            validated_headers["To"] = headers_dict["To"]
        else:
            validated_headers["To"] = ", ".join(recipients)

        # Validar otros headers opcionales según RFC 5322
        allowed_headers = [
            "Reply-To", "CC", "BCC", "Message-ID", "Date",
            "MIME-Version", "Content-Type", "Content-Transfer-Encoding"
        ]

        for key, value in headers_dict.items():
            if key in allowed_headers:
                validated_headers[key] = value
            else:
                raise SMTPException(f"El header '{key}' no esta permitido.")

        # Agregar valores por defecto si no están presentes
        if "MIME-Version" not in validated_headers:
            validated_headers["MIME-Version"] = "1.0"
        
        if "Content-Type" not in validated_headers:
            validated_headers["Content-Type"] = "text/plain; charset=us-ascii"

        # Convertir a formato string con `\r\n`
        formatted_headers = "\r\n".join([f"{k}: {v}" for k, v in validated_headers.items()])
        
        return formatted_headers

from .response import SMTPResponse
from .connection import SMTPConnection
from .exceptions import SMTPException, TemporarySMTPException, PermanentSMTPException
from .utils import credentials_for_login_authentication, credentials_for_plain_authentication
class SMTPCommands:
    """
    Clase para gestionar y enviar comandos SMTP específicos a través de una conexión.
    """

    def __init__(self, connection: SMTPConnection):
        """
        Inicializa el gestor de comandos SMTP con una conexión existente.

        :param connection: Instancia de SMTPConnection para enviar y recibir datos.
        """
        self.connection = connection

    def _send_command(self, command: str) -> SMTPResponse:
        """
        Envía un comando al servidor SMTP y analiza la respuesta.

        :param command: Comando SMTP en formato de texto.
        :return: Instancia de SMTPResponse con la respuesta del servido.
        """
        self.connection.send(command)
        raw_response = self.connection.receive()
        return SMTPResponse(raw_response)

    def ehlo(self, domain: str) -> SMTPResponse:
        """
        Envía el comando EHLO al servidor SMTP. Si no es soportado, intenta con HELO.

        :param domain: Dominio que identifica al cliente.
        :return: Respuesta del servidor al comando EHLO o HELO.
        """

        response = self._send_command(f"EHLO {domain}\r\n")
        if response.is_permanent_error():  # EHLO no soportado, intentar HELO
            response = self._send_command(f"HELO {domain}\r\n")
            
        return response
    
    def authenticate(self, mechanism: str, username: str, password: str) -> SMTPResponse:
        """
        Autentica al cliente con el servidor SMTP utilizando el mecanismo especificado.

        :param mechanism: Mecanismo de autenticación (PLAIN, LOGIN, etc.).
        :param username: Nombre de usuario.
        :param password: Contraseña del usuario.
        :return: Respuesta del servidor después de la autenticación.
        :raises SMTPException: Si la autenticación falla o el mecanismo no es soportado.
        """

        if mechanism.upper() == "PLAIN":
            encoded_credentials = credentials_for_plain_authentication(username, password)
            response = self._send_command(f"AUTH PLAIN {encoded_credentials}\r\n")
                         
            return response

        if mechanism.upper() == "LOGIN":
            # Enviar AUTH LOGIN
            response = self._send_command("AUTH LOGIN\r\n")
            if not response.is_provisional():  # Esperar 334
                return response
            
            # Enviar nombre de usuario en Base64
            username_b64, password_b64 = credentials_for_login_authentication(username, password)
            response = self._send_command(f"{username_b64}\r\n")
            if not response.is_provisional():  # Esperar 334
                return response
            
            # Enviar contraseña en Base64
            return self._send_command(f"{password_b64}\r\n")
                                          
    def mail_from(self, sender: str, size: int = None) -> SMTPResponse:
        """
        Envía el comando MAIL FROM al servidor SMTP.

        :param sender: Dirección de correo del remitente.
        :param size: Tamaño del mensaje en bytes (opcional).
        :return: Respuesta del servidor al comando MAIL FROM.
        """

        parameters = f" SIZE={size}" if size else ""
        
        return self._send_command(f"MAIL FROM:{sender}\r\n")
        return self._send_command(f"MAIL FROM:<{sender}>{parameters}\r\n")

    def rcpt_to(self, recipient: str, notify: str = None) -> SMTPResponse:
        """
        Envía el comando RCPT TO al servidor SMTP.

        :param recipient: Dirección de correo del destinatario.
        :param notify: Parámetro opcional NOTIFY (por ejemplo, SUCCESS,FAILURE).
        :return: Respuesta del servidor al comando RCPT TO.
        """
        
        parameters = f" NOTIFY={notify}" if notify else ""
        
        return self._send_command(f"RCPT TO:{recipient}\r\n")
        return self._send_command(f"RCPT TO:<{recipient}>{parameters}\r\n")

    def data(self, message: str) -> SMTPResponse:
        """
        Envía el comando DATA y el cuerpo del mensaje al servidor SMTP.

        :param message: Cuerpo del mensaje que se enviará.
        :return: Respuesta del servidor tras enviar el mensaje.
        """
        
        # Enviar DATA y esperar la respuesta 354
        initial_response = self._send_command("DATA\r\n")
        if not initial_response.is_provisional():  # `354` es provisional (3xx)
            return initial_response

        # Formatear el mensaje correctamente
        lines = message.splitlines()  # Dividir en líneas
        formatted_lines = []

        for line in lines:
            if line.startswith("."):  # apar líneas que comienzan con `.`
                formatted_lines.append(f".{line}")
            else:
                formatted_lines.append(line)

        formatted_message = "\r\n".join(formatted_lines)  # Unir con `<CRLF>`
        formatted_message = formatted_message if formatted_message.endswith("\r\n") else formatted_message + "\r\n" 
        
        # Agregar la secuencia final `<CRLF>.<CRLF>`
        final_message = f"{formatted_message}.\r\n"

        # Enviar el mensaje y recibir la respuesta final
        return self._send_command(final_message)
        

    def rset(self) -> SMTPResponse:
        """
        Envía el comando RSET para reiniciar el estado de la transacción SMTP.

        :return: Respuesta del servidor al comando RSET.
        """
        return self._send_command("RSET\r\n")

    def vrfy(self, address: str) -> SMTPResponse:
        """
        Envía el comando VRFY para verificar una dirección de correo.

        :param address: Dirección de correo a verificar.
        :return: Respuesta del servidor al comando VRFY.
        """
        
        return self._send_command(f"VRFY {address}\r\n")

    def expn(self, alias: str) -> SMTPResponse:
        """
        Envía el comando EXPN para expandir un alias o lista de correo.

        :param alias: Alias o lista de correo a expandir.
        :return: Respuesta del servidor al comando EXPN.
        """
        
        return self._send_command(f"EXPN {alias}\r\n")

    def help(self, command: str = None) -> SMTPResponse:
        """
        Envía el comando HELP para obtener información sobre los comandos SMTP.

        :param command: Comando específico para obtener ayuda (opcional).
        :return: Respuesta del servidor al comando HELP.
        """
        cmd = f" {command}" if command else ""
        return self._send_command(f"HELP{cmd}\r\n")

    def noop(self) -> SMTPResponse:
        """
        Envía el comando NOOP para verificar que la conexión sigue activa.

        :return: Respuesta del servidor al comando NOOP.
        """
        return self._send_command("NOOP\r\n")

    def quit(self) -> SMTPResponse:
        """
        Envía el comando QUIT para cerrar la sesión SMTP.

        :return: Respuesta del servidor al comando QUIT.
        """
        return self._send_command("QUIT\r\n")

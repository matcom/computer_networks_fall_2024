from .response import SMTPResponse
from .connection import SMTPConnection
from .exceptions import SMTPException, TemporarySMTPException, PermanentSMTPException

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
        :return: Instancia deSMTPResponse con la respuesta del servido.
        """
        self.connection.send(command)
        raw_response = self.connection.receive()
        return SMTPResponse(raw_response)

    # def _send_command(self, command: str) -> SMTPResponse:
    #     """
    #     Envía un comando al servidor SMTP y analiza la respuesta.
        
    #     :param command: Comando SMTP en formato de texto.
    #     :return: Instancia deSMTPResponse con la respuesta del servido.
    #     """
    #     try:
    #         self.connection.send(command)
    #         raw_response = self.connection.receive()
    #         response = SMTPResponse(raw_response)
    #         response.raise_for_status()  # Lanza excepción si hay un error
    #         return response
    #     except SMTPException as e:
    #         # Repropagar errores específicos de SMTP
    #         raise e
    #     except Exception as e:
    #         # Manejar errores inesperados
    #         raise SMTPException(f"Error inesperado al enviar el comando '{command}': {e}")
        
    def ehlo(self, domain: str) -> SMTPResponse:
        """
        Envía el comando EHLO al servidor SMTP. Si no es soportado, intenta con HELO.

        :param domain: Dominio que identifica al cliente.
        :return: Respuesta del servidor al comando EHLO o HELO.
        """
        if not domain or not isinstance(domain, str):
            raise ValueError("El dominio debe ser una cadena válida.")

        response = self._send_command(f"EHLO {domain}\r\n")
        if response.is_permanent_error():  # EHLO no soportado, intentar HELO
            response = self._send_command(f"HELO {domain}\r\n")
        return response

    def mail_from(self, sender: str, size: int = None) -> SMTPResponse:
        """
        Envía el comando MAIL FROM al servidor SMTP.

        :param sender: Dirección de correo del remitente.
        :param size: Tamaño del mensaje en bytes (opcional).
        :return: Respuesta del servidor al comando MAIL FROM.
        """
        if not sender or not isinstance(sender, str):
            raise ValueError("El remitente debe ser una dirección de correo válida.")

        parameters = f" SIZE={size}" if size else ""
        return self._send_command(f"MAIL FROM:<{sender}>{parameters}\r\n")

    def rcpt_to(self, recipient: str, notify: str = None) -> SMTPResponse:
        """
        Envía el comando RCPT TO al servidor SMTP.

        :param recipient: Dirección de correo del destinatario.
        :param notify: Parámetro opcional NOTIFY (por ejemplo, SUCCESS,FAILURE).
        :return: Respuesta del servidor al comando RCPT TO.
        """
        if not recipient or not isinstance(recipient, str):
            raise ValueError("El destinatario debe ser una dirección de correo válida.")

        parameters = f" NOTIFY={notify}" if notify else ""
        return self._send_command(f"RCPT TO:<{recipient}>{parameters}\r\n")

    def data(self, message: str) -> SMTPResponse:
        """
        Envía el comando DATA y el cuerpo del mensaje al servidor SMTP.

        :param message: Cuerpo del mensaje que se enviará.
        :return: Respuesta del servidor tras enviar el mensaje.
        """
        if not message or not isinstance(message, str):
            raise ValueError("El mensaje debe ser una cadena válida.")

        initial_response = self._send_command("DATA\r\n")
        if not (initial_response.is_provisional() or initial_response.is_success()):
            raise ConnectionError(f"Error al iniciar el envío de datos: {initial_response}")

        # Escapar líneas que comiencen con un punto
        escaped_message = "\r\n".join([f".{line}" if line.startswith(".") else line for line in message.splitlines()])
        final_response = self._send_command(f"{escaped_message}\r\n.\r\n")
        return final_response

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
        if not address or not isinstance(address, str):
            raise ValueError("La dirección debe ser una cadena válida.")
        return self._send_command(f"VRFY {address}\r\n")

    def expn(self, alias: str) -> SMTPResponse:
        """
        Envía el comando EXPN para expandir un alias o lista de correo.

        :param alias: Alias o lista de correo a expandir.
        :return: Respuesta del servidor al comando EXPN.
        """
        if not alias or not isinstance(alias, str):
            raise ValueError("El alias debe ser una cadena válida.")
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

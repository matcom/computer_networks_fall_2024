# src/response.py

from .exceptions import SMTPException, TemporarySMTPException, PermanentSMTPException
class SMTPResponse:
    """
    Clase para analizar y clasificar las respuestas del servidor SMTP.
    """

    def __init__(self, raw_response: str):
        """
        Inicializa la clase con la respuesta en bruto del servidor.

        :param raw_response: Respuesta completa del servidor en formato de texto.
        """
        if not raw_response or not isinstance(raw_response, str):
            #raise ValueError("La respuesta no debe ser una cadena no vacía.")
            self.raw_response = None
            self.code = None
            self.message = None
        else:
            self.raw_response = raw_response
            self.code = self._extract_code()
            self.message = self._extract_message()

    def _extract_code(self) -> int:
        """
        Extrae el código de estado de la respuesta.

        :return: Código de respuesta como un entero.
        """
        try:
            return int(self.raw_response[:3])
        except (ValueError, IndexError):
            raise ValueError(f"No se pudo extraer un código válido de la respuesta: {self.raw_response}")

    def _extract_message(self) -> str:
        """
        Extrae el mensaje de la respuesta, excluyendo el código de estado.

        :return: Mensaje de la respuesta como una cadena.
        """
        return self.raw_response[4:].strip() if len(self.raw_response) > 4 else ""

    def is_success(self) -> bool:
        """
        Verifica si la respuesta indica éxito (códigos 2xx).

        :return: True si el código es 2xx, False en caso contrario.
        """
        return 200 <= self.code < 300
    
    def is_provisional(self) -> bool:
        """
        Verifica si la respuesta indica éxito (códigos 2xx).

        :return: True si el código es 2xx, False en caso contrario.
        """
        return 300 <= self.code < 400

    def is_temporary_error(self) -> bool:
        """
        Verifica si la respuesta indica un error temporal (códigos 4xx).

        :return: True si el código es 4xx, False en caso contrario.
        """
        return 400 <= self.code < 500

    def is_permanent_error(self) -> bool:
        """
        Verifica si la respuesta indica un error permanente (códigos 5xx).

        :return: True si el código es 5xx, False en caso contrario.
        """
        return 500 <= self.code < 600

    def raise_for_status(self):
        """
        Lanza excepciones específicas según el código de la respuesta.
        """
        if self.is_temporary_error():
            raise TemporarySMTPException(f"Error temporal: {self}")
        elif self.is_permanent_error():
            raise PermanentSMTPException(f"Error permanente: {self}")
    
    def to_json(self):
        """
        Devuelve una representación legible de la respuesta en formato json.

        :return: Cadena con el código y el mensaje en formato json.
        """
        return {
            "status_code": self.code,
            "message": self.message
        }
        
    def __str__(self):
        """
        Devuelve una representación legible de la respuesta.

        :return: Cadena con el código y el mensaje.
        """
        return f"{self.code} {self.message}"

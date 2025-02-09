
class UrlIncorrect (Exception):
    pass

class NotConnection(Exception):
    pass

class InvalidHeaderFormat(Exception):
    """Excepción para indicar que el formato del encabezado no es un JSON válido."""
    pass
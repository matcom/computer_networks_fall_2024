import logging

# crear un logger

logger = logging.getLogger('HTTPServer')
logger.setLevel(logging.DEBUG)

# Definir un formato de color para los logs
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[94m',  # Azul
        'INFO': '\033[92m',   # Verde
        'WARNING': '\033[93m',  # Amarillo
        'ERROR': '\033[91m',   # Rojo
        'CRITICAL': '\033[95m',  # Magenta
        'RESET': '\033[0m',    # Restablecer color
    }

    def format(self, record):
        log_message = super().format(record)
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        return f"{color}{log_message}{self.COLORS['RESET']}"

# Configurar un stream handler para los logs (en consola)
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter('%(levelname)s: %(message)s'))

# Añadir el handler al logger
logger.addHandler(console_handler)

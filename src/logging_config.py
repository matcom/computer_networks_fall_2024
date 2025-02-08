import logging
import logging.config

LOG_FILE = "app.log"  # Nombre del archivo donde se guardarán los logs

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "simple": {
            "format": "%(levelname)s - %(message)s"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": LOG_FILE,
            "mode": "a",  # "a" para añadir logs al archivo, "w" para sobrescribir
        },
    },
    "loggers": {
        "app_logger": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False,
        }
    },
}

def setup_logging():
    """ Configura el sistema de logs en toda la aplicación. """
    logging.config.dictConfig(LOGGING_CONFIG)
    return logging.getLogger("app_logger")

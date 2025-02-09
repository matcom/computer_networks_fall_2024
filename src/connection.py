# src/connection.py

import socket
import logging
import ssl
import time 

class SMTPConnection:
    """
    Clase para gestionar la conexión TCP subyacente con un servidor SMTP.
    """

    def __init__(self, host: str, port: int = 25, timeout: float = 50.0):
        """
        Inicializa la conexión SMTP y establece la conexión automáticamente.

        :param host: Dirección del servidor SMTP.
        :param port: Puerto del servidor SMTP (por defecto, 25).
        :param timeout: Tiempo de espera para la conexión en segundos (por defecto, 10).
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = None
        self.server_address = None

        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s', filename="connection_log.txt")

    def connect(self):
        """
        Establece una conexión TCP con el servidor SMTP.
        """
        try:
            self.socket = socket.create_connection((self.host, self.port), timeout=self.timeout)
            self.server_address = (self.host, self.port)
            logging.info(f"Conexión establecida con {self.host}:{self.port}")
            self.receive()
        except Exception as e:
            raise ConnectionError(f"Error al conectar con {self.host}:{self.port}: {e}")

    def send(self, data: str):
        """
        Envía datos al servidor SMTP.

        :param data: Comando o mensaje en formato de texto.
        """
        if not self.socket:
            raise ConnectionError("La conexión no está abierta.")

        try:
            data += "" if data.endswith('\r\n') else '\r\n'
            self.socket.sendall(data.encode('us-ascii'))
            logging.info(f"Enviado: {data}")
        except Exception as e:
            raise ConnectionError(f"Error al enviar datos: {e}")

    def receive(self) -> str:
        """
        Recibe datos del servidor SMTP.

        :return: Respuesta del servidor en formato de texto.
        """
        if not self.socket:
            raise ConnectionError("La conexión no está abierta.")

        try:
            response = self.socket.recv(1024).decode('us-ascii')
            logging.info(f"Recibido: {response.strip()}")
            return response.strip()
            
        except Exception as e:
            raise ConnectionError(f"Error al recibir datos: {e}")

    def is_connected(self) -> bool:
        """
        Verifica si la conexión TCP está activa.

        :return: True si la conexión está abierta, False en caso contrario.
        """
        return self.socket is not None

    def close(self):
        """
        Cierra la conexión TCP.
        """
        if self.socket:
            try:
                self.socket.close()
                logging.info("Conexión cerrada.")
            except Exception as e:
                raise ConnectionError(f"Error al cerrar la conexión: {e}")
            finally:
                self.socket = None
        else:
            logging.warning("No hay conexión activa para cerrar.")

    def start_tls(self):
        """
        Inicia una conexión TLS segura con el servidor SMTP.
        """
        try:
            # Solicitar al servidor que inicie una conexión cifrada
            self.send("STARTTLS\r\n")
            response = self.receive()
                        
            if not response.startswith("2"):
                raise ConnectionError(f"El servidor rechazó STARTTLS: {response}")

            # Cerrar el socket antes de aplicar TLS (necesario en algunos servidores)
            self.socket.shutdown(socket.SHUT_RDWR)
            
            # Encapsular el socket en un contexto TLS
            context = ssl.create_default_context()
            self.socket = context.wrap_socket(self.socket, server_hostname=self.server_address[0])
            
            # Agregar una pausa para evitar "Broken pipe"
            time.sleep(0.5)

            # Recibir cualquier mensaje pendiente antes de enviar EHLO
            leftover_data = self.receive()
            logging.info("Datos después de STARTTLS: " + leftover_data)
            logging.info("Conexión TLS establecida con éxito.")
        except Exception as e:
            raise ConnectionError(f"Error al iniciar TLS: {e}")

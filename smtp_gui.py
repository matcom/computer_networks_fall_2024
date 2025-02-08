import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QMessageBox
)
from src.client import SMTPClient  # Importa tu clase SMTPClient

class SMTPClientGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cliente SMTP")
        self.setGeometry(100, 100, 600, 400)

        # Widgets principales
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Campos de entrada
        self.host_input = QLineEdit(self)
        self.host_input.setPlaceholderText("Servidor SMTP (ej: localhost)")
        self.layout.addWidget(QLabel("Servidor SMTP:"))
        self.layout.addWidget(self.host_input)

        self.port_input = QLineEdit(self)
        self.port_input.setPlaceholderText("Puerto (ej: 1025)")
        self.layout.addWidget(QLabel("Puerto:"))
        self.layout.addWidget(self.port_input)

        self.sender_input = QLineEdit(self)
        self.sender_input.setPlaceholderText("Remitente (ej: remitente@dominio.com)")
        self.layout.addWidget(QLabel("Remitente:"))
        self.layout.addWidget(self.sender_input)

        self.recipient_input = QLineEdit(self)
        self.recipient_input.setPlaceholderText("Destinatario (ej: destinatario@dominio.com)")
        self.layout.addWidget(QLabel("Destinatario:"))
        self.layout.addWidget(self.recipient_input)

        self.subject_input = QLineEdit(self)
        self.subject_input.setPlaceholderText("Asunto")
        self.layout.addWidget(QLabel("Asunto:"))
        self.layout.addWidget(self.subject_input)

        self.message_input = QTextEdit(self)
        self.message_input.setPlaceholderText("Mensaje")
        self.layout.addWidget(QLabel("Mensaje:"))
        self.layout.addWidget(self.message_input)

        # Botón de envío
        self.send_button = QPushButton("Enviar Correo", self)
        self.send_button.clicked.connect(self.send_email)
        self.layout.addWidget(self.send_button)

    def send_email(self):
        """Envía el correo usando SMTPClient."""
        try:
            # Obtener los valores de los campos
            host = self.host_input.text()
            port = int(self.port_input.text())
            sender = self.sender_input.text()
            recipient = self.recipient_input.text()
            subject = self.subject_input.text()
            message = self.message_input.toPlainText()

            # Construir el mensaje completo
            full_message = f"Subject: {subject}\r\n\r\n{message}"

            # Crear el cliente SMTP y enviar el correo
            client = SMTPClient(host, port)
            client.send_mail(sender, recipient, full_message)

            # Mostrar mensaje de éxito
            QMessageBox.information(self, "Éxito", "El correo se envió correctamente.")
        except Exception as e:
            # Mostrar mensaje de error
            QMessageBox.critical(self, "Error", f"Error al enviar el correo: {str(e)}")

def main():
    app = QApplication(sys.argv)
    window = SMTPClientGUI()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
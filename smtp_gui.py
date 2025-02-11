import sys
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QFileDialog,
    QLabel, QLineEdit, QTextEdit, QPushButton, QMessageBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtCore import Qt
from src.client import SMTPClient
from src.exceptions import SMTPException


class SMTPClientGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cliente SMTP")
        self.setGeometry(100, 100, 800, 400)
        self.loading_dialog = None
        self.thread = None
        self.init_ui()
        

    def init_ui(self):
        # Widget principal
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Campos de conexión
        self.init_connection_fields()
        self.layout.addSpacing(20)

        # Campos de autenticación
        self.init_auth_fields()
        self.layout.addSpacing(20)

        # Campos de correo
        self.init_email_fields()
        self.layout.addSpacing(20)

        # Botón de envío
        self.send_button = QPushButton("Enviar Correo", self)
        self.send_button.clicked.connect(self.send_email)
        self.layout.addWidget(self.send_button)

    def init_connection_fields(self):
        """Inicializa los campos de conexión."""
               
        # Crear el layout horizontal
        self.layout_horizontal = QHBoxLayout()
        
        connection_layout = QHBoxLayout()

        self.host_input = QLineEdit(self)
        self.host_input.setPlaceholderText("Servidor SMTP (ej: localhost)")
        connection_layout.addWidget(QLabel("Servidor:"))
        connection_layout.addWidget(self.host_input)

        self.port_input = QLineEdit(self)
        self.port_input.setPlaceholderText("Puerto (ej: 1025)")
        connection_layout.addWidget(QLabel("Puerto:"))
        connection_layout.addWidget(self.port_input)

        self.layout.addLayout(connection_layout)

    def init_auth_fields(self):
        """Inicializa los campos de autenticación."""
        auth_layout = QHBoxLayout()

        self.sender_input = QLineEdit(self)
        self.sender_input.setPlaceholderText("Remitente (ej: remitente@dominio.com)")
        auth_layout.addWidget(QLabel("Remitente:"))
        auth_layout.addWidget(self.sender_input)

        self.password_input = QLineEdit(self)
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.Password)
        auth_layout.addWidget(QLabel("Contraseña:"))
        auth_layout.addWidget(self.password_input)

        self.layout.addLayout(auth_layout)

    def init_email_fields(self):
        """Inicializa los campos de correo."""
        # Destinatarios
        recipient_layout = QHBoxLayout()
        self.recipient_input = QLineEdit(self)
        self.recipient_input.setPlaceholderText("Destinatario (ej: destinatario@dominio.com)")
        recipient_layout.addWidget(QLabel("Destinatario:"))
        recipient_layout.addWidget(self.recipient_input)

        self.add_recipient_button = QPushButton("Agregar", self)
        self.add_recipient_button.clicked.connect(self.add_recipient)
        recipient_layout.addWidget(self.add_recipient_button)

        self.layout.addLayout(recipient_layout)

        # Lista de destinatarios
        self.recipient_list = QListWidget(self)
        self.layout.addWidget(self.recipient_list)
        
        # Añadir botón de eliminar
        recipient_buttons_layout = QHBoxLayout()
        recipient_buttons_layout.addWidget(self.add_recipient_button)
        
        self.remove_recipient_button = QPushButton("Eliminar Seleccionado", self)
        self.remove_recipient_button.clicked.connect(self.remove_recipient)
        recipient_buttons_layout.addWidget(self.remove_recipient_button)
        
        self.layout.addLayout(recipient_buttons_layout)

        # Asunto y mensaje
        self.subject_input = QLineEdit(self)
        self.subject_input.setPlaceholderText("Asunto")
        self.layout.addWidget(QLabel("Asunto:"))
        self.layout.addWidget(self.subject_input)

        self.message_input = QTextEdit(self)
        self.message_input.setPlaceholderText("Mensaje")
        self.layout.addWidget(QLabel("Mensaje:"))
        self.layout.addWidget(self.message_input)
        
        
    def seleccionar_archivo(self):
            # Abrir diálogo para seleccionar archivo
            nombre_archivo, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar Archivo",
                "",
                "Todos los archivos (*.*)"
            )
            
            # Si se seleccionó un archivo, actualizar el texto del label
            if nombre_archivo:
                self.label_archivo.setText(nombre_archivo)
    def remove_recipient(self):
        selected = self.recipient_list.currentRow()
        if selected >= 0:
            self.recipient_list.takeItem(selected)
    
    def add_recipient(self):
        """Agrega un destinatario a la lista."""
        recipient = self.recipient_input.text().strip()
        if recipient and recipient not in [
            self.recipient_list.item(i).text() for i in range(self.recipient_list.count())
        ]:
            self.recipient_list.addItem(QListWidgetItem(recipient))
            self.recipient_input.clear()
        else:
            QMessageBox.warning(self, "Advertencia", "El destinatario ya existe o está vacío.")

    def validate_fields(self):
        """Valida que todos los campos requeridos estén completos."""
        fields = [
            (self.host_input, "Servidor SMTP"),
            (self.port_input, "Puerto"),
            (self.sender_input, "Remitente"),
            (self.password_input, "Contraseña"),
            (self.subject_input, "Asunto"),
            #(self.message_input, "Mensaje"),
        ]

        for field, name in fields:
            if not field.text().strip():
                QMessageBox.warning(self, "Campo Requerido", f"El campo '{name}' es obligatorio.")
                return False

        if self.recipient_list.count() == 0:
            QMessageBox.warning(self, "Destinatario Requerido", "Debe agregar al menos un destinatario.")
            return False

        return True
    
    def send_email(self):
        if not self.validate_fields():
            return
        
        # Configurar y lanzar hilo
        client = SMTPClient(
            self.host_input.text().strip(),
            int(self.port_input.text().strip())
        )
        
        self.thread = EmailSenderThread(
            client=client,
            user=(
                self.sender_input.text().strip(),
                self.password_input.text().strip()
            ),
            recipients=[self.recipient_list.item(i).text() for i in range(self.recipient_list.count())],
            subject=self.subject_input.text().strip(),
            body=self.message_input.toPlainText().strip()
        )
        
        self.thread.finished.connect(self.handle_send_result)
        self.thread.start()
        
        # Mostrar diálogo de carga
        self.show_loading_dialog()

    def show_loading_dialog(self):
        time.sleep(0.5)
        
        self.loading_dialog = QMessageBox(self)
        self.loading_dialog.setWindowTitle("Enviando correo")
        self.loading_dialog.setText("Por favor espere...")
        #self.loading_dialog.setStandardButtons(QMessageBox.NoButton)
        self.loading_dialog.show()

    def handle_send_result(self, success, message):
        # Cerrar el diálogo de carga
        if self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None 
        
        if success:
            QMessageBox.information(self, "Éxito", message)
            #self.clear_fields()
        else:
            QMessageBox.critical(self, "Error", message)
        
    def clear_fields(self):
        """Opcional: Limpiar campos después de enviar"""
        self.message_input.clear()
        self.recipient_list.clear()
        self.subject_input.clear()

class EmailSenderThread(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int)

    def __init__(self, client: SMTPClient, user, recipients, subject, body):
        super().__init__()
        self.client = client
        self.user = user
        self.recipients = recipients
        self.subject = subject
        self.body = body

    def run(self):
        try:
            self.client.connect().raise_for_status("Connection error")
            
            if self.client.does_server_supports_tls():
                self.client.connect_by_tls().raise_for_status("TLS connection error")
            
            if self.client.does_server_supports_authentication():
                self.client.authenticate(mechanism='PLAIN', username=self.user[0], password=self.user[1]).raise_for_status("Authentication error")
            
            self.client.send_mail(self.user[0], self.recipients, self.subject, self.body).raise_for_status("Email error")
            self.client.disconnect()
            
            self.finished.emit(True, "Correo enviado exitosamente")
        except Exception as e:
            self.finished.emit(False, str(e))

def main():
    app = QApplication(sys.argv)
    window = SMTPClientGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

# class SMTPClientGUI(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.setWindowTitle("Cliente SMTP")
#         self.setGeometry(100, 100, 600, 500)

#         # Widgets principales
#         self.central_widget = QWidget()
#         self.setCentralWidget(self.central_widget)
#         self.layout = QVBoxLayout(self.central_widget)

#         # Campos de entrada
#         self.host_input = QLineEdit(self)
#         self.host_input.setPlaceholderText("Servidor SMTP (ej: localhost)")
#         self.layout.addWidget(QLabel("Servidor SMTP:"))
#         self.layout.addWidget(self.host_input)

#         self.port_input = QLineEdit(self)
#         self.port_input.setPlaceholderText("Puerto (ej: 1025)")
#         self.layout.addWidget(QLabel("Puerto:"))
#         self.layout.addWidget(self.port_input)

#         self.sender_input = QLineEdit(self)
#         self.sender_input.setPlaceholderText("Remitente (ej: remitente@dominio.com)")
#         self.layout.addWidget(QLabel("Remitente:"))
#         self.layout.addWidget(self.sender_input)

#         self.password_input = QLineEdit(self)
#         self.password_input.setPlaceholderText("Contraseña")
#         self.password_input.setEchoMode(QLineEdit.Password)
#         self.layout.addWidget(QLabel("Contraseña:"))
#         self.layout.addWidget(self.password_input)

#         self.recipient_input = QLineEdit(self)
#         self.recipient_input.setPlaceholderText("Destinatario (ej: destinatario@dominio.com)")
#         self.layout.addWidget(QLabel("Destinatario:"))
#         self.layout.addWidget(self.recipient_input)

#         self.recipient_list = QListWidget(self)
#         self.layout.addWidget(QLabel("Destinatarios:"))
#         self.layout.addWidget(self.recipient_list)

#         self.add_recipient_button = QPushButton("Agregar Destinatario", self)
#         self.add_recipient_button.clicked.connect(self.add_recipient)
#         self.layout.addWidget(self.add_recipient_button)

#         self.subject_input = QLineEdit(self)
#         self.subject_input.setPlaceholderText("Asunto")
#         self.layout.addWidget(QLabel("Asunto:"))
#         self.layout.addWidget(self.subject_input)

#         self.message_input = QTextEdit(self)
#         self.message_input.setPlaceholderText("Mensaje")
#         self.layout.addWidget(QLabel("Mensaje:"))
#         self.layout.addWidget(self.message_input)

#         # Botón de envío
#         self.send_button = QPushButton("Enviar Correo", self)
#         self.send_button.clicked.connect(self.send_email)
#         self.layout.addWidget(self.send_button)

#     def add_recipient(self):
#         """Agrega un destinatario a la lista."""
#         recipient = self.recipient_input.text()
#         if recipient:
#             self.recipient_list.addItem(QListWidgetItem(recipient))
#             self.recipient_input.clear()
        
#     def send_email(self):
#         """Envía el correo usando SMTPClient."""
#         try:
#             # Obtener los valores de los campos
#             host = self.host_input.text()
#             port = int(self.port_input.text())
#             sender = self.sender_input.text()
#             password = self.password_input.text()
#             subject = self.subject_input.text()
#             body = self.message_input.toPlainText()

#             # Obtener la lista de destinatarios
#             recipients = [self.recipient_list.item(i).text() for i in range(self.recipient_list.count())]
#             if not recipients:
#                 raise ValueError("At least one recipient must be defined")

#             # Crear el cliente SMTP
#             client = SMTPClient(host, port)
#             response = client.connect()
            
#             response.raise_for_status("Connection error")
            
#             # Verificar si el servidor soporta TLS
#             if client.does_server_supports_tls():
#                 response = client.connect_by_tls()    
#                 response.raise_for_status("TLS connection error")
            
#             # Verificar si el servidor soporta autenticación
#             if client.does_server_supports_authentication():
#                 response = client.authenticate(mechanism='PLAIN', username=sender, password=password)
#                 response.raise_for_status("Authentication error")

#             # Enviar el correo
#             response = client.send_mail(sender, recipients, subject, body)
#             response.raise_for_status("Email error")
            
#             # Desconectar
#             client.disconnect()

#             # Mostrar mensaje de éxito
#             QMessageBox.information(self, "Success", "The email has been send successfully")
        
#         except Exception as e:
#             # Mostrar mensaje de error
#             QMessageBox.critical(self, "Error", f"{str(e)}")

# def main():
#     app = QApplication(sys.argv)
#     window = SMTPClientGUI()
#     window.show()
#     sys.exit(app.exec_())

# if __name__ == "__main__":
#     main()
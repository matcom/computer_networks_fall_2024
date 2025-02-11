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

        # Campos de adjuntos
        self.init_attachment_fields()
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
        
    def init_attachment_fields(self):
        """Inicializa los campos de adjuntos."""
        attachment_layout = QHBoxLayout()

        self.attachment_input = QLineEdit(self)
        self.attachment_input.setPlaceholderText("Ruta del archivo")
        attachment_layout.addWidget(QLabel("Adjunto:"))
        attachment_layout.addWidget(self.attachment_input)

        self.browse_button = QPushButton("Buscar", self)
        self.browse_button.clicked.connect(self.browse_file)
        attachment_layout.addWidget(self.browse_button)

        self.add_attachment_button = QPushButton("Agregar Adjunto", self)
        self.add_attachment_button.clicked.connect(self.add_attachment)
        attachment_layout.addWidget(self.add_attachment_button)

        self.layout.addLayout(attachment_layout)

        # Lista de adjuntos
        self.attachment_list = QListWidget(self)
        self.layout.addWidget(self.attachment_list)

        # Botón para eliminar adjuntos
        self.remove_attachment_button = QPushButton("Eliminar Adjunto Seleccionado", self)
        self.remove_attachment_button.clicked.connect(self.remove_attachment)
        self.layout.addWidget(self.remove_attachment_button)

    def browse_file(self):
        """Abre un diálogo para seleccionar un archivo."""
        file_name, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo", "", "Todos los archivos (*.*)")
        if file_name:
            self.attachment_input.setText(file_name)

    def add_attachment(self):
        """Agrega un archivo a la lista de adjuntos."""
        file_path = self.attachment_input.text().strip()
        if file_path:
            self.attachment_list.addItem(QListWidgetItem(file_path))
            self.attachment_input.clear()
        else:
            QMessageBox.warning(self, "Advertencia", "Por favor, selecciona un archivo.")

    def remove_attachment(self):
        """Elimina el archivo seleccionado de la lista de adjuntos."""
        selected = self.attachment_list.currentRow()
        if selected >= 0:
            self.attachment_list.takeItem(selected)

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
            int(self.port_input.text().strip()))
        
        attachments = [self.attachment_list.item(i).text() for i in range(self.attachment_list.count())]
        
        self.thread = EmailSenderThread(
            client=client,
            user=(
                self.sender_input.text().strip(),
                self.password_input.text().strip()
            ),
            recipients=[self.recipient_list.item(i).text() for i in range(self.recipient_list.count())],
            subject=self.subject_input.text().strip(),
            body=self.message_input.toPlainText().strip(),
            attachments=attachments
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
        self.attachment_list.clear()

class EmailSenderThread(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int)

    def __init__(self, client: SMTPClient, user, recipients, subject, body, attachments=None):
        super().__init__()
        self.client = client
        self.user = user
        self.recipients = recipients
        self.subject = subject
        self.body = body
        self.attachments = attachments if attachments else []

    def run(self):
        try:
            self.client.connect().raise_for_status("Connection error")
            
            if self.client.does_server_supports_tls():
                self.client.connect_by_tls().raise_for_status("TLS connection error")
            
            if self.client.does_server_supports_authentication():
                self.client.authenticate(mechanism='PLAIN', username=self.user[0], password=self.user[1]).raise_for_status("Authentication error")
            
            if self.attachments:
                self.client.send_mail_with_attachments(
                    sender=self.user[0],
                    recipients=self.recipients,
                    subject=self.subject,
                    body=self.body,
                    attachments=self.attachments
                ).raise_for_status("Email with attachments error")
            else:
                self.client.send_mail(
                    self.user[0],
                    self.recipients,
                    self.subject,
                    self.body
                ).raise_for_status("Email error")
            
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
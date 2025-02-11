# test_smtp_client.py

from src.client import SMTPClient

def main():
    
    google = ("smtp.gmail.com", 587,'gabrielplalasa@gmail.com', 'andres28lasa')
    mailhog = ("localhost", 1025)
    matcom = ("0.0.0.0", 2525)
    server = ('localhost', 2025, 'user@admin.com', 'pass')
    python = ('localhost', 3025)
    ethereal = ('smtp.ethereal.email', 587, 'harvey.schumm@ethereal.email', 'bXQvWeuv5mqsaUXuxt')
    
    sender = 'user1@uh.cu'
    recipients = ["user2@uh.cu", "user3@uh.cu"]
    subject = 'Test Email'
    body = 'This is a test email.'
    headers1="Reply-To: support@example.com\nCC: charlie@example.com"
    headers2={"CC": "charlie@example.com"}
    headers3='{"Reply-To": "support@example.com", "CC": "charliePan@example.com"}'

    
    generic = server
    
    client = SMTPClient(generic[0], generic[1])
    client.connect()
    
    if client.does_server_supports_tls():
        client.connect_by_tls()
    
    if client.does_server_supports_authentication():
        client.authenticate(mechanism=client.auth_methods[0], username=generic[2], password=generic[3])
    
    client.send_mail(sender, recipients, subject, body)
    client.disconnect()

    # Enviar correo con adjuntos
    # client.send_mail_with_attachments(
    #     sender="user@example.com",
    #     recipients=["dest@example.com"],
    #     subject="Prueba con adjuntos",
    #     body="Mira estos archivos!",
    #     attachments=["tc.pdf", "README.md"]
    # )
    
    
if __name__ == '__main__':
    main()

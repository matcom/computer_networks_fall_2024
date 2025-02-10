# test_smtp_client.py

from src.client import SMTPClient

def main():
    
    google = ("smtp.gmail.com", 587,'gabrielplalasa@gmail.com', 'andres28lasa')
    mailhog = ("localhost", 1025)
    matcom = ("0.0.0.0", 2525)
    server = ('localhost', 2025)
    python = ('localhost', 3025)
    ethereal = ('smtp.ethereal.email', 587, 'user', 'pass')
    
    sender = 'user1@uh.cu'
    recipients = ["user2@uh.cu", "user3@uh.cu"]
    subject = 'Test Email'
    body = 'This is a test email.'
    headers1="Reply-To: support@example.com\nCC: charlie@example.com"
    headers2={"CC": "charlie@example.com"}
    headers3='{"Reply-To": "support@example.com", "CC": "charliePan@example.com"}'

    client = SMTPClient(mailhog[0], mailhog[1])
    client.connect()
    
    if client.does_server_supports_tls():
        client.connect_by_tls()
    
    if client.does_server_supports_authentication():
        client.authenticate(mechanism=client.auth_methods[0], username=ethereal[2], password=ethereal[3])
    
    client.send_mail(sender, recipients, subject, body)
    client.disconnect()

if __name__ == '__main__':
    main()

# test_smtp_client.py

from src.client import SMTPClient

def main():
    
    host = "smtp.gmail.com" #'localhost'  # Host de MailHog
    port = 587         # Puerto de MailHog
    sender = 'example@domain.com'
    recipients = ['andras.pla@google.com']
    subject = 'Subject: Test Email'
    body = 'This is a test email.'

    client = SMTPClient(host, port)
    client.connect()
    
    if client.does_server_supprorts_tls():
        client.tls_conncection()
    
    mechanism='PLAIN'
    if client.does_server_supports_authentication(mechanism):
        client.authenticate(mechanism=mechanism, username=sender, password='123456')
    
    client.send_mail(sender, recipients, subject, body)
    client.disconnect()

if __name__ == '__main__':
    main()

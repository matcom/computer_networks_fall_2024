# test_smtp_client.py

from src.client import SMTPClient

def main():
    
    host = 'localhost'  # Host de MailHog
    port = 1025         # Puerto de MailHog
    sender = 'example@domain.com'
    recipients = ['recipient@domain.com']
    subject = 'Subject: Test Email'
    body = 'This is a test email.'

    client = SMTPClient(host, port)
    client.connect()
    
    if client.does_server_supports_authentication():
        client.authenticate(mechanism='PLAIN', username=sender, password='123456')
    
    client.send_mail(sender, recipients, subject, body)
    client.disconnect()

if __name__ == '__main__':
    main()

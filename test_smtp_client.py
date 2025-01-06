# test_smtp_client.py

from src.client import SMTPClient

def main():
    host = 'localhost'  # Host de MailHog
    port = 1025         # Puerto de MailHog
    sender = 'example@domain.com'
    recipient = 'recipient@domain.com'
    message = 'Subject: Test Email\r\n\r\nThis is a test email.'

    client = SMTPClient(host, port)
    client.send_mail(sender, recipient, message)

if __name__ == '__main__':
    main()

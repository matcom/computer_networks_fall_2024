# test_smtp_client.py

from src.client import SMTPClient

def main():
    
    google = ("smtp.gmail.com", 587)
    mailhog = ("localhost", 1025)
    
    
    sender = 'example@domain.com'
    recipients = ['andras.pla@google.com']
    subject = 'Test Email'
    body = 'This is a test email.'
    headers1="Reply-To: support@example.com\nCC: charlie@example.com"
    headers2={
        "Reply-To": "support@example.com",
        "CC": "charlie@example.com",
    }
    headers3='{"Reply-To": "support@example.com", "CC": "charliePan@example.com"}'
    headers4='{\\"CC\\":\\ \\"cc@example.com\\"}'

    client = SMTPClient(mailhog[0], mailhog[1])
    client.connect()
    
    # if client.does_server_supprorts_tls():
    #     client.tls_conncection()
    
    # mechanism='PLAIN'
    # if client.does_server_supports_authentication(mechanism):
    #     client.authenticate(mechanism=mechanism, username=sender, password='123456')
    
    client.send_mail(sender, recipients, subject, body, headers4)
    client.disconnect()

if __name__ == '__main__':
    main()

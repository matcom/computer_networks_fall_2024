# test_smtp_client.py

from src.client import SMTPClient

def main():
    
    google = ("smtp.gmail.com", 587)
    mailhog = ("localhost", 1025)
    matcom = ("0.0.0.0", 2525)
    
    
    sender = 'user1@uh.cu'
    recipients = ["user2@uh.cu", "user3@uh.cu"]
    subject = 'Test Email'
    body = 'This is a test email.'
    headers1="Reply-To: support@example.com\nCC: charlie@example.com"
    headers2={"CC": "charlie@example.com"}
    headers3='{"Reply-To": "support@example.com", "CC": "charliePan@example.com"}'

    client = SMTPClient(mailhog[0], mailhog[1])
    client.connect()
    client.send_mail(sender, recipients, subject, body)
    client.disconnect()

if __name__ == '__main__':
    main()

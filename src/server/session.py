class Session:
    def __init__(self):
        self.client_host = None
        self.mail_from = None
        self.recipients = []
        self.data = []
        self.tls_active = False
        self.authenticated = False
        self.auth_username = None 
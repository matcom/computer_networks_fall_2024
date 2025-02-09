class Session:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.mail_from = None
        self.recipients = []
        self.data = []
        self.tls_active = False
        self.authenticated = False
        self.client_host = ""
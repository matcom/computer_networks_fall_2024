class response:
    status_code: str
    message: str
    data: str
    
    def __init__(self, status, message, data = None):
        self.status_code = status
        self.message = message
        self.data = data
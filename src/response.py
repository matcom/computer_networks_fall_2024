class SMTPResponse:
    def __init__(self, response_code, message):
        self.response_code = response_code
        self.message = message

    @classmethod
    def parse(cls, response):
        lines = response.split('\r\n')
        response_code = int(lines[0][:3])
        message = '\n'.join(lines)
        return cls(response_code, message)

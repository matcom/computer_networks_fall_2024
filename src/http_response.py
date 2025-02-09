
""" representa una respuesta HTTP contienendo 
    la informacion clave que se obtiene despues 
    de realizar una solicitud a un servidor

"""
class HTTPResponse:
    def __init__(self, version, code, reason, headers, body):
        self.version = version # "HTTP/1.1"
        self.code = int(code)  # 200,400
        self.reason = reason   # OK,Not Found
        self.headers = headers 
        self.body = body

    def get_body_bytes(self):
        return self.body

    def get_headers(self):
        return self.headers

    def __str__(self):
        return f"<{self.__class__.__name__} [{self.code}]>"

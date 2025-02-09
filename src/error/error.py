class HTTPClientError(Exception):
    """Base class for HTTP client errors."""
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details

class ConnectionError(HTTPClientError):
    """Raised when a connection error occurs."""
    def __init__(self, message, host, port):
        super().__init__(message)
        self.host = host
        self.port = port

class InvalidURLError(HTTPClientError):
    """Raised when the URL is invalid."""
    def __init__(self, message, url):
        super().__init__(message)
        self.url = url

class RequestBuildError(HTTPClientError):
    """Raised when there is an error building the request."""
    def __init__(self, message, method, uri, headers, body):
        super().__init__(message)
        self.method = method
        self.uri = uri
        self.headers = headers
        self.body = body

class RequestSendError(HTTPClientError):
    """Raised when there is an error sending the request."""
    def __init__(self, message, request):
        super().__init__(message)
        self.request = request

class ResponseReceiveError(HTTPClientError):
    """Raised when there is an error receiving the response."""
    def __init__(self, message):
        super().__init__(message)

class ResponseParseError(HTTPClientError):
    """Raised when there is an error parsing the response."""
    def __init__(self, message, response_header):
        super().__init__(message)
        self.response_header = response_header

class ResponseBodyError(HTTPClientError):
    """Raised when there is an error with the response body."""
    def __init__(self, message, content_length):
        super().__init__(message)
        self.content_length = content_length
HTTP_STATUS_CODES = {
    # Informativos
    100: ("Continue", "The server has received the request headers and the client should proceed to send the body."),
    101: ("Switching Protocols", "The server is switching protocols as requested."),
    
    # Éxito
    200: ("OK", "Request processed successfully."),
    201: ("Created", "The resource was successfully created."),
    204: ("No Content", "The server successfully processed the request, but is not returning any content."),
    
    # Redirección
    301: ("Moved Permanently", "The requested resource has been permanently moved."),
    302: ("Found", "The requested resource is temporarily at a different location."),
    304: ("Not Modified", "The resource has not changed since the last request."),
    
    # Errores del cliente
    400: ("Bad Request", "Invalid request format."),
    401: ("Unauthorized", "Authentication is required to access this resource."),
    403: ("Forbidden", "You do not have permission to access this resource."),
    404: ("Not Found", "The requested resource was not found."),
    405: ("Method Not Allowed", "This method is not supported."),
    411: ("Length Required", "Content-Length header is required for POST and PUT."),
    414: ("URI Too Long", "Requested URL is too long."),
    415: ("Unsupported Media Type", "This content type is not supported."),
    
    # Errores del servidor
    500: ("Internal Server Error", "An unexpected error occurred."),
    501: ("Not Implemented", "This method is not supported by the server."),
    503: ("Service Unavailable", "The server is currently unable to handle the request."),
}

class Router:
    def __init__(self):
        self.routes = {}
    
    def add_route(self, path, methods=['GET']):
        def decorator(handler):
            for method in methods:
                self.routes[(path, method.upper())] = handler
            return handler
        return decorator
    
    def handle_request(self, handler):
        path = handler.path
        method = handler.command
        return self.routes.get((path, method), self.default_handler)(handler)
    
    def default_handler(self, handler):
        return {
            "status_code": 404,
            "body": "Endpoint no encontrado"
        }

router = Router()

@router.add_route('/', methods=['GET', 'HEAD'])
def root_handler(handler):
    return {
        "status_code": 200,
        "body": "Welcome to the server!" if handler.command == 'GET' else None
    }

@router.add_route('/secure', methods=['GET'])
def secure_handler(handler):
    return {
        "status_code": 200,
        "body": "You accessed a protected resource"
    }
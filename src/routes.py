from typing import Dict, Tuple, Callable, Any
from utils.types import HTTPResponse

class Router:
    def __init__(self) -> None:
        self.routes: Dict[Tuple[str, str], Callable] = {}
    
    def add_route(self, path:str, methods:list[str] = ['GET']) -> Callable:
        def decorator(handler:Callable) -> Callable:
            for method in methods:
                self.routes[(path, method.upper())] = handler
            return handler
        return decorator
    
    def handle_request(self, handler) -> HTTPResponse:
        #method = handler.command
        route_key = (handler.path, handler.command.upper())
        handler_func = self.routes.get(route_key, self._default_handler)
        return handler_func(handler)
    
    def default_handler(self, handler) -> HTTPResponse:
        return {
            "status_code": 404,
            "body": {"error": f"Ruta {handler.path} no encontrada"}
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
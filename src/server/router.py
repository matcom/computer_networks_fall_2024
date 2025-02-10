from typing import Callable, List, Tuple
from src.status import HTTPStatus

class Method:
    def __init__(self, method: str, function: Callable[[object], Tuple[int, str, dict]]):
        self.method = method
        self.function = function

    def handle(self, request):
        return self.function(request)

class Endpoint:
    def __init__(self, uri: str, methods: List[Method], router=None):
        self.uri = uri
        self.methods = methods

class Router:
    def __init__(self, routes: List[Endpoint]):
        self.routes = routes

    def handle(self, resource: str, method: str, request):
        for route in self.routes:
            if route.uri != resource:
                continue

            allowed_methods = [m.method for m in route.methods]

            if method == "OPTIONS":
                return HTTPStatus.OK.value, "", {"Allow": ", ".join(allowed_methods)}

            for m in route.methods:
                if m.method == method:
                    return m.handle(request)

            return HTTPStatus.METHOD_NOT_ALLOWED.value, "Method Not Allowed", {"Allow": ", ".join(allowed_methods)}

        return HTTPStatus.NOT_FOUND.value, "Not Found", {}

router = Router([
    Endpoint("/", [
        Method("GET", lambda request: (HTTPStatus.OK.value, "bienvenidos al himalaya", {})),
        Method("POST", lambda request: (HTTPStatus.CREATED.value, "Resource created", {})),
        Method("PUT", lambda request: (HTTPStatus.OK.value, "Resource updated", {})),
        Method("DELETE", lambda request: (HTTPStatus.NO_CONTENT.value, "", {})),
        Method("HEAD", lambda request: (HTTPStatus.OK.value, "", {})),
        Method("OPTIONS", lambda request: (HTTPStatus.OK.value, "", {})),
        Method("TRACE", lambda request: (HTTPStatus.OK.value, "TRACE response", {})),
        Method("CONNECT", lambda request: (HTTPStatus.OK.value, "CONNECT response", {}))
    ]),
    Endpoint("/redirect", [
        Method("GET", lambda request: (HTTPStatus.MOVED_PERMANENTLY.value, "", { "Location": "localhost:8080/"}))  
    ]),
    Endpoint("/hello", [
        Method("GET", lambda request: (HTTPStatus.OK.value, "Hello, world!", {}))
    ]),
    Endpoint("/goodbye", [
        Method("GET", lambda request: (HTTPStatus.OK.value, "Goodbye, world!", {}))
    ])
])
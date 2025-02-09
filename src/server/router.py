from typing import Callable, List, Tuple
from src.status import HTTPStatus

class Method:
    def __init__(self, method: str, function: Callable[[object], Tuple[int, str]]):
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
                return HTTPStatus.OK, "", {"Allow": ", ".join(allowed_methods)}

            for m in route.methods:
                if m.method == method:
                    return m.handle(request)

            return HTTPStatus.METHOD_NOT_ALLOWED, "Method Not Allowed", {"Allow": ", ".join(allowed_methods)}

        return HTTPStatus.NOT_FOUND, "Not Found", {}

router = Router([
    Endpoint("/", [
        Method("GET", lambda request: (HTTPStatus.OK, "bienvenidos al himalaya")),
        Method("POST", lambda request: (HTTPStatus.CREATED, "Resource created")),
        Method("PUT", lambda request: (HTTPStatus.OK, "Resource updated")),
        Method("DELETE", lambda request: (HTTPStatus.NO_CONTENT, "")),
        Method("HEAD", lambda request: (HTTPStatus.OK, "")),
        Method("OPTIONS", lambda request: (HTTPStatus.OK, "")),
        Method("TRACE", lambda request: (HTTPStatus.OK, "TRACE response")),
        Method("CONNECT", lambda request: (HTTPStatus.OK, "CONNECT response"))
    ]),
    Endpoint("/hello", [
        Method("GET", lambda request: (HTTPStatus.OK, "Hello, world!"))
    ]),
    Endpoint("/goodbye", [
        Method("GET", lambda request: (HTTPStatus.OK, "Goodbye, world!"))
    ])
])
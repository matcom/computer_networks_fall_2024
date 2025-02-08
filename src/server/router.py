from typing import Callable, List, Tuple

#some type definitions

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
  
  def handle(self, resource: str, method: str,  request):
    for route in self.routes:
      if route.uri != resource:
        continue
      for m in route.methods:
        if m.method == method:
          return m.handle(request)
      return 405, "Method Not Allowed"
    return 404, "Not Found"
  
router = Router([
  Endpoint("/", [
    Method("GET", lambda request: (200, "bienvenidos al himalaya"))
  ]),
  Endpoint("/hello", [
    Method("GET", lambda request: (200, "Hello, world!"))
  ]),
  Endpoint("/goodbye", [
    Method("GET", lambda request: (200, "Goodbye, world!"))
  ])
])
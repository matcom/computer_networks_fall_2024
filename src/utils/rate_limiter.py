
#from collections import defaultdict
#from time import time
#
#class RateLimiter:
#   def __init__(self, max_requests=100, window=60):
#       self.requests = defaultdict(list)
#       self.max_requests = max_requests
#       self.window = window
#
#   def is_allowed(self, client_ip: str) -> bool:
#       now = time()
#       self.requests[client_ip] = [t for t in self.requests[client_ip] if t > now - self.window]
#       if len(self.requests[client_ip]) < self.max_requests:
#           self.requests[client_ip].append(now)
#           return True
#       return False

from collections import defaultdict
from time import time
from typing import Dict, List

class RateLimiter:
    def __init__(self, max_requests: int = 100, period: int = 60):
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.max_requests = max_requests
        self.period = period

    def check_limit(self, client_ip: str) -> bool:
        now = time()
        self.requests[client_ip] = [
            t for t in self.requests[client_ip]
            if t > now - self.period
        ]
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        self.requests[client_ip].append(now)
        return True
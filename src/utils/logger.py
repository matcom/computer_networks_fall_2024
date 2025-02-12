import logging
from typing import Dict, Any
from pathlib import Path

def configure_logging(level: int = logging.INFO) -> None:
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(logs_dir/"server.log"),
            logging.StreamHandler()
        ]
    )

class RequestLogger:
    def __init__(self, handler):
        self.logger = logging.getLogger("HTTP")
        self.handler = handler
    
    def log_request(self, method: str, path: str) -> None:
        client_ip = self.handler.client_address[0]
        self.logger.info(f"{method} {path} from {client_ip}")
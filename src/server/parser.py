class CommandParser:
    @staticmethod
    def parse(data: bytes):
        decoded = data.decode().strip()
        parts = decoded.split()
        
        if not parts:
            return "UNKNOWN", None
            
        command = parts[0].upper()
        arg = " ".join(parts[1:]) if len(parts) > 1 else None
        
        return command, arg
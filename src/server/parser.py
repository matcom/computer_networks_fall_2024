class CommandParser:
    @staticmethod
    def parse(data: bytes):
        try:
            decoded_data = data.decode().strip()
            parts = decoded_data.split(maxsplit=1)
            command = parts[0].upper()
            arg = parts[1] if len(parts) > 1 else None
            return command, arg
        except Exception:
            return None, None
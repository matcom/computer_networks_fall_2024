import json

def from_json(data: bytes):
    return json.loads(data.decode("utf-8"))

def to_json(data: dict):
    return json.dumps(data).encode("utf-8")

def log(message):
    print('Info: ' + message)
    return
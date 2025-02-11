import json

def from_json(data):
    return json.loads(data.decode())

def to_json(data: dict):
    return json.dumps(data).encode("utf-8")

def log(message: str):
    # print('Info: ' + message)
    return
import json

def parse_headers(raw_headers):
    return {k: v for k, v in (line.split(': ', 1) for line in raw_headers)}

def validate_auth(auth_header):
    return auth_header == "Bearer 12345"

def validate_json(body):
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None
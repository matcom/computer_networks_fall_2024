import sys
import json
import argparse
from http_client import HttpClient  # Importamos la clase

def json_response(status, body, headers=None):
    return json.dumps({
        "status": status,
        "body": body,
        "headers": headers or {}
    })

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cliente HTTP en Python")
    parser.add_argument("-m", "--method", required=True, help="Método HTTP (GET, POST, PUT, DELETE, etc.)")
    parser.add_argument("-u", "--url", required=True, help="URL de la solicitud")
    parser.add_argument("-h", "--headers", default="{}", help="Encabezados en formato JSON")
    parser.add_argument("-d", "--data", default=None, help="Datos del cuerpo de la solicitud")

    args = parser.parse_args()

    try:
        headers = json.loads(args.headers)
    except json.JSONDecodeError:
        headers = {}

    client = HttpClient("")  # No ponemos base_url porque recibimos la URL completa
    response = client.request(args.method, args.url, data=args.data, headers=headers)

    if response is None:
        print(json_response(500, "Error en la solicitud"))
        sys.exit(1)

    print(json_response(200, response))

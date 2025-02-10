import argparse
import json
import sys
from http_client import final_request
from http_response import HTTPResponse
from http_parser import categorize_args
from exceptions import InvalidHeaderFormat

def run_client(method, url, headers=None, body=""):
    """
    Función que ejecuta una solicitud HTTP y devuelve la respuesta formateada.

    :param method: Método HTTP (GET, POST, etc.)
    :param url: URL de la solicitud
    :param headers: Diccionario de encabezados HTTP
    :param body: Cuerpo de la solicitud (opcional)
    :return: Respuesta HTTP formateada como string
    """
    headers = headers or {}

    try:
        response: HTTPResponse = final_request(method=method, url=url, headers=headers, body=body)

        # Construcción de la respuesta en formato HTTP
        response_text = f"HTTP/1.1 {response.code} {response.reason}\n"

        # Agregar encabezados al formato
        for key, value in response.headers.items():
            response_text += f"{key}: {value}\n"

        response_text += "\n"  # Línea vacía entre encabezados y cuerpo
        response_text += response.get_body_bytes().decode("utf-8")  # Cuerpo de la respuesta

        return response_text
    except Exception as e:
        return f"HTTP/1.1 500 Internal Server Error\nError: {str(e)}"


def main(sys_args):
    parser = argparse.ArgumentParser(description="HTTP Client CLI", add_help=False)
    parser.add_argument("-m", "--method", required=True, help="HTTP Method (GET, POST, DELETE, etc.)")
    parser.add_argument("-u", "--url", required=True, help="Request URL")
    parser.add_argument("-h", "--header", type=str, default="{}", help="Headers in JSON format (e.g., '{\"User-Agent\": \"device\"}')")
    parser.add_argument("-d", "--data", type=str, default="", help="Request body")

    # Parse command-line arguments
    args = parser.parse_args(categorize_args(sys_args))

    try:
        headers = json.loads(args.header)
    except json.JSONDecodeError:
        raise InvalidHeaderFormat("❌ Error: Invalid header format. Please provide valid JSON.")

    response: HTTPResponse = final_request(method=args.method, url=args.url, headers=headers, body=args.data)

    # Prepare output JSON format
    final_response = {
        "status": response.code,
        "body": response.get_body_bytes().decode('utf-8')  # Assuming body is in bytes and needs to be decoded
    }

    # Print output as JSON
    print(json.dumps(final_response, indent=2))

if __name__ == "__main__":
    main(sys.argv[1:])

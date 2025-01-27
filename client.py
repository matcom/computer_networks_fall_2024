# http_request.py
import sys
import json
import requests

def main():
    # Obtener los parámetros de la línea de comandos
    method = sys.argv[1]
    url = sys.argv[2]
    headers = json.loads(sys.argv[3])  # Encabezados en formato JSON
    body = sys.argv[4]  # El cuerpo de la solicitud (como string)

    # Realizar la solicitud HTTP

    # Formateamos la respuesta para que sea legible y fácil de procesar
    response_data = {
        'status': '500',
        'body': 'Error',
        'headers': '\{\}'
    }

    # Imprimimos la respuesta en formato JSON
    print(json.dumps(response_data))

if __name__ == "__main__":
    main()

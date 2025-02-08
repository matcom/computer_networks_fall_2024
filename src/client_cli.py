import argparse
import json
import sys
from http_client import HttpClient


if __name__ == "__main__":
    
    # crear un analizador de argumentos
    parser = argparse.ArgumentParser(description="Cliente HTTP en Python", add_help= False)  # deshabilitar argumento de ayuda (-h)
    
    # definimos que argumentos puedes ser pasados al script
    parser.add_argument("-m", "--method", required=True, help="Método HTTP (GET, POST, PUT, DELETE,)")
    parser.add_argument("-u", "--url", required=True, help="URL de la solicitud")
    parser.add_argument("-h", "--headers",type=str, default="{}", help="Encabezados en formato JSON")
    parser.add_argument("-d", "--data",type=str, default="", help="Datos del cuerpo de la solicitud")

    args = parser.parse_args()

    try:
        headers = json.loads(args.headers)
    except json.JSONDecodeError:
        print("Invalid header format. Please provide valid JSON.")
        sys.exit(1)
    
    # creando un cliente
    client = HttpClient("")  
    response = client.request(args.method, args.url, data=args.data, headers=headers)

    # respuesta final
    response_data = {
        "status" : response.code,
        "body": response.get_body_raw().decode('utf-8') # decodifica la respuesta del srvidor si viene en formato bytes
    }
    
    print(json.dump(response_data,indent=2))

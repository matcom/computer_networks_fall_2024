
# import requests

# # Permitir hacer solicitudes HTTP (GET,POST)
# # RFC 9110 para clientes HTTP

# class HttpClient:
#     def __init__(self,base_url):
#         self.base_url = base_url     # la url del servidor al que se haran las solicitudes
#         self.session = requests.Session()  # se usa una sesion para mantener conexiones persistentes y mejorar el rendimiento
#         self.session.headers.update({
#             "User-Agent": "MyHttpClient/1.0",     # indica que cliente esta haciendo la peticion
#             "Accept": "application/json",         # especifica lo que se espera recibir respuesta en formato JSON
#             "Connection": "keep-alive"            # mantiene la conexion abierta para mejorar la eficiencia
#         })
        
#     def request(self, method, endpoint, params=None, data=None, json=None, headers=None):
#         url = f"{self.base_url}{endpoint}"
#         try:
#             response = self.session.request(
#                 method=method.upper(),
#                 url=url,
#                 params=params,
#                 data=data,
#                 json=json,
#                 headers=headers,
#                 timeout=10
#             )
#             response.raise_for_status()
#             return response.json() if "application/json" in response.headers.get("Content-Type", "") else response.text
        
#         except requests.exceptions.RequestException as e:
#             print(f"Error en {method.upper()} {url}: {e}")
#             return None

#     def get(self,endpoint,params=None, headers= None):
#         return self.request("GET",endpoint,params=params, headers=headers)
    
#     def post(self,endpoint,data = None, json=None,headers = None):
#         return self.request("POST",endpoint,data=data, json=json, headers=headers)
    
#     def close(self):
#         self.session.close()


# if __name__== "__main__":

#     client= HttpClient("https://jsonplaceholder.typicode.com")

#     # Realizar una solicitud POST
#     nueva_data = {"title": "foo", "body": "bar", "userId": 1}
#     respuesta_post = client.post("/posts", json=nueva_data)
#     print("Respuesta POST:", respuesta_post)

#      # Realizar una solicitud GET
#     respuesta = client.get("/posts/1")
#     print("Respuesta GET:", respuesta)

#     client.close()
    
import sys
import json
import argparse
import requests

# Definir la clase HttpClient
class HttpClient:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MyHttpClient/1.0",
            "Accept": "application/json",
            "Connection": "keep-alive"
        })

    def request(self, method, url, params=None, data=None, json=None, headers=None):
        try:
            response = self.session.request(
                method=method.upper(),
                url=url,
                params=params,
                data=data,
                json=json,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return {
                "status": response.status_code,
                "body": response.text,
                "headers": dict(response.headers)
            }
        except requests.exceptions.RequestException as e:
            return {
                "status": 500,
                "body": f"Error en la solicitud: {str(e)}",
                "headers": {}
            }

# Función para generar respuestas en JSON
def json_response(response):
    return json.dumps(response)

# Punto de entrada del script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cliente HTTP en Python")
    parser.add_argument("-m", "--method", required=True, help="Método HTTP (GET, POST, PUT, DELETE, etc.)")
    parser.add_argument("-u", "--url", required=True, help="URL de la solicitud")
    parser.add_argument("-hdr", "--headers", default="{}", help="Encabezados en formato JSON")
    parser.add_argument("-d", "--data", default=None, help="Datos del cuerpo de la solicitud")

    args = parser.parse_args()

    # Convertir encabezados de string a diccionario
    try:
        headers = json.loads(args.headers)
    except json.JSONDecodeError:
        headers = {}

    # Crear cliente y realizar la solicitud
    client = HttpClient()
    response = client.request(args.method, args.url, data=args.data, headers=headers)

    # Imprimir la respuesta en formato JSON para que `tests.py` la procese correctamente
    print(json_response(response))

    # Si hay error, salir con código 1
    if response["status"] >= 400:
        sys.exit(1)

import socket
import json
import ssl
from http_parser import parse_http_url,parse_http_response
from exceptions import NotConnection

# GLOBAL VARIABLES
_versionHttp = 'HTTP/1.1'
default_http_port = 80
default_https_port = 443

class HttpClient:
    
    def __init__(self,host, port :int,use_https,timeout=socket._GLOBAL_DEFAULT_TIMEOUT, blocksize = 8192):
        
        self.host = host
        self.port = port
        self.use_https = use_https
        self.timeout = timeout
        self.mySocket = None
        self.blocksize = blocksize
    
    # se hace uso del protocolo TCP/IP
    def connect (self):
        # se establece una conexion TCP con el servidor
       raw_mySocket = socket.create_connection((self.host,self.port),self.timeout)
       
       if self.use_https:
           # si es https se envuelve el socket en una conexion TLS/SSL
           context = ssl.create_default_context()
           self.mySocket = context.wrap_socket(raw_mySocket,server_hostname=self.host)
           
       else: # si es HTTP
           self.mySocket = raw_mySocket
       
    def request(self,method,url,body="", headers= None):
        # construye y envia una solicitud HTTP
        headers = headers or {}
        headers["Host"]= headers.get("Host",self.host)
        headers["Content-Length"] = str(len(body))
        headers["Accept-Encodding"] =headers.get("Accept-Encoding", "identity") # sin compresion
        headers["Connection"] = "close" # se cierra la conexion despues de recibir la respuesta

        # construir la solicitud HTTP
        
        request= f"{method.upper()} {url} {_versionHttp}\r\n"
        
        # agregar los encabezados
        
        for header, value in headers.items():
            request += f"{header}: {value}\r\n"
        
        if body:
            request+= f"\r\n{body}\r\n"
        
        request += "\r\n"
        
        # converite la solicitud a bytes porque socket trabaja con binarios
        self.send(request.encode())
        
    
    def send(self,data):
        # verfica que la conexion este abierta 
        if not self.mySocket:
            raise NotConnection("La conexión no está abierta")

        #enviar los datos al servidor 
        self.mySocket.sendall(data)
    
    def close(self):
        if self.mySocket: # si el socket esta abierto
            self.mySocket.close()
            self.mySocket = None

    def receive(self,count= 1024):
        # recibir hasta count bytes del servidor
        return self.mySocket.recv(count)

  
def final_request (method="GET",url="/",headers = None,body =""):
    # extraer la informacion de la URL
    host,port,path,query = parse_http_url(url)
    
    use_https = (port == default_https_port) or url.startswith("https://")
    # crear una instancia de HttpClient para establecer una conexion
    conn = HttpClient(host,port,use_https)

    data = None
    
    try:
        # conectar al servidor y enviar la solicitud
        conn.connect()
        conn.request(method,path+query, headers=headers,body=body)
        
        #parsear la respuesta del servidor pendiente en el socket
        data= parse_http_response (method,conn.mySocket)
    
    finally:
        # cierra la conexion
        conn.close()
    
    # devuelve la respuesta parseada
    return data
    

if __name__ == "__main__":
    
    # Case 1 : My API - DownTrack
    host = "http://localhost:5217"
    endpoint = "/api/Authentication/register"
    
    body = json.dumps({
        "id":33590,
        "name": "User_335",
        "userName": "username_33590",
        "email": "example3@gmail.com",
        "password": "Password_333!",
        "userRole": "Technician",
        "specialty": "mechanic",
        "salary": 19090,
        "expYears": 10,
        "departamentId": 1,
        "sectionId": 1
    })
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = final_request("POST", f"{host}{endpoint}", headers=headers, body=body)

    print("Código de estado:", response.code)
    print("Encabezados:", response.headers)
    print("Cuerpo:", response.body[:500])

    # Case 2: HTTPS 
    
    response = final_request("GET","https://reqres.in/api/users?page=2", headers={}, body="")
    
    print("Código de estado:", response.code)
    print("Encabezados:", response.headers)
    print("Cuerpo:", response.body[:500])

    # Case 3: HTTPS
    response = final_request("GET","https://jsonplaceholder.typicode.com", headers={}, body="")
    
    print("Código de estado:", response.code)
    print("Encabezados:", response.headers)
    print("Cuerpo:", response.body[:500])


import socket
import re
import gzip
from logging_config import setup_logging
from collections import defaultdict

# GLOBAL VARIABLES
_versionHttp = 'HTTP/1.1'
default_port = 80
logger = setup_logging()

class BadUrlError(Exception):
    pass

def parse_http_url(url):
    # Expresión regular para parsear la URL
    regex = r'^(http://)?([^:/\s]+)(?::(\d+))?(/[^?\s]*)?(\?[^#\s]*)?$'
    match = re.match(regex, url)
    
    if not match:
        raise BadUrlError(f"Invalid URL: {url}")
    
    scheme = match.group(1) or "http://"  # Si no tiene esquema, asignamos "http://"
    host = match.group(2)
    port = match.group(3) or 80  # Si no tiene puerto, asignamos el puerto por defecto 80
    path = match.group(4) or "/"  # Si no tiene path, asignamos "/"
    query = match.group(5) or ""  # Si no tiene query, dejamos como cadena vacía
    
    #Convertir el puerto a entero
    
    port = int(port)
    
    return (host,port,path,query)


class HTTPResponse:
    def __init__(self, version, code, reason, headers, body):
        self.version = version
        self.code = int(code)
        self.reason = reason
        self.headers = headers
        self.body = body

    def get_body_raw(self):
        return self.body

    def get_headers(self):
        return self.headers

    def __str__(self):
        return f"<{self.__class__.__name__} [{self.code} {self.reason}]>"

def read_line(conn):
    """ Lee una línea completa desde el socket. """
    line = b""
    while True:
        chunk = conn.recv(1)
        if not chunk or chunk == b"\n":
            break
        line += chunk
    return line.strip()  # Eliminamos espacios y retornos de línea

def read_headers(conn):
    """ Lee los encabezados HTTP y los devuelve en un diccionario. """
    headers = defaultdict(str)
    while True:
        line = read_line(conn)
        if not line:
            break  # Fin de los encabezados
        try:
            key, value = line.decode().split(":", 1)
            headers[key.strip()] = value.strip()
        except ValueError:
            logger.warning("Encabezado HTTP mal formado: %s", line)
    return headers

def read_body(conn, headers, method):
    """ Lee el cuerpo de la respuesta según Content-Length o Transfer-Encoding. """
    body = b""

    # Leer cuerpo basado en Content-Length
    if "Content-Length" in headers:
        length = int(headers["Content-Length"])
        while len(body) < length:
            body += conn.recv(length - len(body))
    
    # Leer cuerpo basado en Transfer-Encoding: chunked
    elif headers.get("Transfer-Encoding") == "chunked":
        while True:
            size_line = read_line(conn)
            if not size_line:
                break
            try:
                chunk_size = int(size_line, 16)  # Convertir de hexadecimal a entero
            except ValueError:
                logger.warning("Error al leer chunk size: %s", size_line)
                break
            
            if chunk_size == 0:
                break  # Fin de los chunks
            
            chunk_data = conn.recv(chunk_size)
            body += chunk_data
            read_line(conn)  # Consumir la línea vacía después del chunk

    # Descomprimir si está en gzip
    if headers.get("Content-Encoding") == "gzip":
        try:
            body = gzip.decompress(body)
        except gzip.BadGzipFile:
            logger.warning("Error al descomprimir GZIP")

    return body

def parse_response(method, conn):
    """ Parsea la respuesta HTTP del servidor. """
    # Leer línea de estado HTTP
    status_line = read_line(conn).decode()
    try:
        version, code, reason = status_line.split(" ", 2)
    except ValueError:
        logger.error("Línea de estado mal formada: %s", status_line)
        return None

    headers = read_headers(conn)
    body = read_body(conn, headers, method) if method != "HEAD" else b""

    return HTTPResponse(version, code, reason, headers, body)

class HttpClient:
    
    def __init__(self,host: "IP", port :int, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, blocksize = 8192):
        
        self.host = host
        self.port = port
        self.timeout = timeout
        
        self.mySocket = None
        self.blocksize = blocksize
    
    # se hace uso del protocolo TCP/IP
    def connect (self):
       self.mySocket = socket.create_connection((self.host,self.port),self.timeout)
       logger.info("INFO - conexión a %s:%s ha sido exitosa" , self.host, self.port) 
    
    def request(self,method,url,body="", headers= None):
        
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
        
        if len(body)!=0:
            request+= f"\r\n{body}\r\n"
        
        request += "\r\n"
        
        # converite la solicitud a bytes porque socket trabaja con binarios
        self.send(request.encode())
        
    
    def send(self,data):
        if not self.mySocket:
            raise Exception()

        logger.info("INFO - sending\n%s", data)
        
        self.mySocket.sendall(data)
    
    def close(self):
        if self.mySocket: # si el socket esta abierto
            self.mySocket.close()
            self.mySocket = None

    def receive(self,count= 1024):
        # recibir hasta count bytes del servidor
        return self.mySocket.recv(count)
  
  
def request (method="GET",url="/",headers = None,body =""):
    host,port,path,query = parse_http_url(url)
    
    conn = HttpClient(host,port)
    
    res= None
    data = None
    
    try:
        conn.connect()
        conn.request(method,path+query, headers=headers,body=body)
        data= parse_response (method,conn.mySocket)
    
    finally:
        conn.close()
    
    logger.debug("%s %s %s", data, data.body, data.headers)
    
    return data
    

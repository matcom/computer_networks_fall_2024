import os
import socket
import json
import logging
import sys
import re


class BadUrlError(Exception):
    pass

def parse_http_url(url: str):
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
    
    
url = "http://www.example.com:8080/path/to/resource?key=value"

print(parse_http_url(url))
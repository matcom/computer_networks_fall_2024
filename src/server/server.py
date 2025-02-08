import socket
import threading
from src.grammar import httpMessage, basic_rules, httpRequest, httpResponse
import router as r

def handle_client(client_socket: socket.socket):
  try:
    request_info, body = receive_request(client_socket)
    print(f"Solicitud recibida")
    status, body = r.router.handle(request_info["uri"], request_info["method"], body)
    headers = httpResponse.build_headers(status, body)
    headers = httpResponse.stringify_headers(headers)
    response = httpResponse.build_res(status, "OK", headers, body=body)
    client_socket.send(response.encode())
  except:
    response = httpResponse.build_res(500, "Error")
    client_socket.send()
  finally:
    client_socket.close()
    
def receive_request(client_socket):
  head = ""
  while True:
    data = client_socket.recv(1)
    if not data:
      break
    head += data.decode()
    if head.endswith(basic_rules.crlf * 2):
      break
  head_info = httpRequest.get_head_info(head)
  body = ""
  if "Content-Length" in head_info["headers"]:
    body = client_socket.recv(int(head_info["headers"]["Content-Length"])).decode()
  return head_info, body

def start_server(host='127.0.0.1', port=8080):
  try:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print(f"Servidor escuchando en {host}:{port}...")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Conexión aceptada de {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()
  except:
    print('Hubo un error fatal')

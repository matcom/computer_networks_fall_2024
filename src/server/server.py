import socket
import threading
from src.status import HTTPStatus
from src.grammar import httpMessage, basic_rules, httpRequest, httpResponse
import router as r

def handle_client(client_socket: socket.socket):
  try:
    while True:
      request_info, body = receive_request(client_socket)
      if not request_info:
        break
      print("Request received")
      status, body = r.router.handle(request_info["uri"], request_info["method"], body)
      headers = httpResponse.build_headers(status, body)
      headers = httpResponse.stringify_headers(headers)
      response = httpResponse.build_res(status, "OK", headers, body=body)
      client_socket.send(response.encode())
      if "Connection" in request_info["headers"] and request_info["headers"]["Connection"] == 'close':
        break
  except Exception as e:
    print(f"Error: {e}")
    response = httpResponse.build_res(HTTPStatus.INTERNAL_SERVER_ERROR, "Error")
    client_socket.send(response.encode())
  finally:
    client_socket.close()
    print("Connection closed")
    
def receive_request(client_socket):
  head = ""
  try:
    while True:
      data = client_socket.recv(1)
      if not data:
        return None, None
      head += data.decode()
      if head.endswith(basic_rules.crlf * 2):
        break
  except TimeoutError:
    print("Connection closed due to timeout")
    return None, None
  except Exception as e:
    print(f"Error: {e}")
    return None, None
  
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
    print(f"Server listening on {host}:{port}...")

    while True:
        client_socket, addr = server_socket.accept()
        client_socket.settimeout(10)
        print(f"Connection accepted from {addr}")
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()
  except:
    print('Fatal Error')

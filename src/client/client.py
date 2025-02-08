import socket
from src.grammar import httpMessage, basic_rules, httpRequest, httpResponse

class httpClient :
    def __init__(self, url):
        host, port, path = httpMessage.get_url_info(url)
        self.host = host
        self.port = port
        self.url = url
        self.path = path
    
    def send_request(self, method: str, header: str, data: str):
        req_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        req_socket.connect((self.host, self.port))        
        request = httpRequest.build_req(method=method, uri=self.path,  headers=header, body=data)
        req_socket.send(request.encode())
        response = self.receive_response(req_socket)
        req_socket.close()
        return response
        
        
    def receive_response(self, req_socket: socket.socket):
        head = ""
        while True:
            data = req_socket.recv(1)
            if not data:
                break
            head += data.decode()
            if head.endswith(basic_rules.crlf * 2):
                break
        head_info = httpResponse.extract_head_info(head)
        if "Content-Length" in head_info["headers"]:
            body = req_socket.recv(int(head_info["headers"]["Content-Length"])).decode()
        return {
            "status": head_info["status_code"],
            "body": body
        }

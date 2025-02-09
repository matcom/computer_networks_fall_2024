import socket
from src.grammar import httpMessage, basic_rules, httpRequest, httpResponse
from src.error.error import (
    InvalidURLError, ConnectionError, RequestBuildError, 
    RequestSendError, ResponseReceiveError, ResponseParseError, ResponseBodyError
)

class httpClient:
    def __init__(self, url):
        try:
            host, port, path = httpMessage.get_url_info(url)
        except Exception as e:
            raise InvalidURLError(f"Invalid URL: {url}", url) from e
        self.host = host
        self.port = port
        self.url = url
        self.path = path
    
    def send_request(self, method: str, header: str, data: str):
        try:
            req_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            req_socket.connect((self.host, self.port))
        except socket.error as e:
            raise ConnectionError(f"Failed to connect to {self.host}:{self.port}", self.host, self.port) from e
        
        try:
            request = httpRequest.build_req(method=method, uri=self.path, headers=header, body=data)
        except Exception as e:
            raise RequestBuildError("Failed to build request", method, self.path, header, data) from e
        
        try:
            req_socket.send(request.encode())
        except Exception as e:
            req_socket.close()
            raise RequestSendError("Failed to send request", request) from e
        
        try:
            response = self.receive_response(req_socket)
        except Exception as e:
            raise ResponseReceiveError("Failed to receive response") from e
        finally:
            req_socket.close()
        
        return response
        
    def receive_response(self, req_socket: socket.socket):
        head = ""
        try:
            while True:
                data = req_socket.recv(1)
                if not data:
                    break
                head += data.decode()
                if head.endswith(basic_rules.crlf * 2):
                    break
        except socket.error as e:
            raise ResponseReceiveError("Error receiving response header") from e
        
        try:
            head_info = httpResponse.extract_head_info(head)
        except Exception as e:
            raise ResponseParseError("Error parsing response header", head) from e
        
        body = ""
        if "Transfer-Encoding" in head_info["headers"] and head_info["headers"]["Transfer-Encoding"] == "chunked":
            try:
                body = self.receive_chunked_body(req_socket)
            except ResponseBodyError as e:
                raise ResponseBodyError("Error receiving chunked response body", e.details) from e
        elif "Content-Length" in head_info["headers"]:
            try:
                body = req_socket.recv(int(head_info["headers"]["Content-Length"])).decode()
            except socket.error as e:
                raise ResponseBodyError("Error receiving response body", head_info["headers"]["Content-Length"]) from e
        
        return {
            "status": head_info["status_code"],
            "body": body
        }

    def receive_chunked_body(self, req_socket: socket.socket):
        body = ""
        while True:
            chunk_size_str = ""
            while True:
                try:
                    data = req_socket.recv(1)
                    if not data:
                        raise ResponseBodyError("Error receiving chunk size", "No data received")
                    chunk_size_str += data.decode()
                    if chunk_size_str.endswith(basic_rules.crlf):
                        break
                except socket.error as e:
                    raise ResponseBodyError("Error receiving chunk size", str(e)) from e
            try:
                chunk_size = int(chunk_size_str.strip(), 16)
            except ValueError as e:
                raise ResponseBodyError("Invalid chunk size", chunk_size_str.strip()) from e
            if chunk_size == 0:
                break
            try:
                chunk_data = req_socket.recv(chunk_size).decode()
                body += chunk_data
                req_socket.recv(2)
            except socket.error as e:
                raise ResponseBodyError("Error receiving chunk data", str(e)) from e
        return body
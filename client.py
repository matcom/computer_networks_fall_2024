import socket
import grammar
import argparse
import json

class httpClient :
    def __init__(self, url):
        host, port, path = grammar.httpMessage.get_url_info(url)
        self.host = host
        self.port = port
        self.url = url
        self.path = path
    
    def send_request(self, method: str, header: str, data: str):
        req_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        req_socket.connect((self.host, self.port))        
        request = grammar.httpRequest.build_req(method=method, uri=self.path,  headers=header, body=data)
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
            if head.endswith(grammar.basic_rules.crlf * 2):
                break
        head_info = grammar.httpResponse.extract_head_info(head)
        if "Content-Length" in head_info["headers"]:
            body = req_socket.recv(int(head_info["headers"]["Content-Length"])).decode()
        return {
            "status": head_info["status_code"],
            "body": body
        }


def parse_arguments():
    parser = argparse.ArgumentParser(description='Make an http request')
    parser.add_argument("-m", "--method", type=str, required=True, help="http method of the request")
    parser.add_argument("-u", "--url", type=str, required=True, help="Resource url")
    parser.add_argument("-H", "--headers", type=str, default="{}", help='headers of the request')
    parser.add_argument("-d", "--data", type=str, default="", help="Body of the request")
    
    args = parser.parse_args()
    return {
        "method": args.method.upper(),
        "url": args.url,
        "headers": args.headers,
        "data": args.data,
    }

def main():
    args = parse_arguments()
    
    client = httpClient(args["url"])
    response = client.send_request(method=args["method"], header=args["headers"], data=args["data"])
    print(json.dumps(response, indent=4))
    
if __name__=="__main__":
    main()

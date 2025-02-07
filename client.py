import socket
import grammar
import argparse

class httpClient :
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
    
    def send_request(self, method: str, header: str, data: str):
        request = grammar.httpRequest.build(method=method, headers=header, body=data)
        self.socket.send(request.encode())
        response = self.socket.recv(1024)
        return response


def parse_arguments():
    parser = argparse.ArgumentParser(description='Make an http request')
    parser.add_argument("-m", "--method", type=str, required=True, help="http method of the request")
    parser.add_argument("-u", "--url", type=str, required=True, help="Resource url")
    parser.add_argument("-H", "--header", type=str, default="{}", help='headers of the request')
    parser.add_argument("-d", "--data", type=str, default="", help="Body of the request")
    
    args = parser.parse_args()
    return {
        "method": args.method.upper(),
        "url": args.url,
        "headers": args.headers,
        "data": args.data,
    }

def __main__():
    args = parse_arguments()
    host, port = grammar.httpMessage.get_host_port(args["url"])
    client = httpClient(host, port)
    client.send_request(args["method", args["headers"], args["data"]])
    
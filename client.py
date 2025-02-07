import socket
import grammar
import argparse

class httpClient :
    def __init__(self, url):
        host, port = grammar.httpMessage.get_host_port(url)
        self.host = host
        self.port = port
        self.url = url
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
    
    def send_request(self, method: str, header: str, data: str):
        request = grammar.httpRequest.build_req(method=method, uri=self.url,  headers=header, body=data)
        self.socket.send(request.encode())
        response = self.socket.recv(1024).decode()
        return response


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
    print(response)
    client.socket.close
    
if __name__=="__main__":
    main()
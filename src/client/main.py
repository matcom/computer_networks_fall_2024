import argparse
from client import httpClient
import json

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

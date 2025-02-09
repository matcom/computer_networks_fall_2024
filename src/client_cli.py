import argparse
import json
import sys
from http_client import  final_request
from http_response import HTTPResponse
from http_parser import categorize_args

def main(sys_args):
    
    parser = argparse.ArgumentParser(description="HTTP Client CLI", add_help=False)
    parser.add_argument("-m", "--method", required=True, help="HTTP method (e.g., GET, POST)")
    parser.add_argument("-u", "--url", required=True, help="Request URL")
    parser.add_argument("-h", "--header", type=str, default="{}", help="Request headers in JSON format (e.g., '{\"User-Agent\": \"device\"}')")
    parser.add_argument("-d", "--data", type=str, default="", help="Request body data")

    # Parse arguments
    args = parser.parse_args(categorize_args(sys_args))

    # Prepare headers from JSON string
    try:
        headers = json.loads(args.header)
    except json.JSONDecodeError:
        print("Invalid header format. Please provide valid JSON.")
        sys.exit(1)

    # Make the HTTP request
    response: HTTPResponse = final_request(method=args.method, url=args.url, headers=headers, body=args.data)

    # Prepare output JSON format
    final_response = {
        "status": response.code,
        "body": response.get_body_bytes().decode('utf-8')  # Assuming body is in bytes and needs to be decoded
    }

     # Print output as JSON
    print(json.dumps(final_response, indent=2))

if __name__ == "__main__":
    main(sys.argv[1:])


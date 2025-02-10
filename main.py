import argparse
import json
from client import HTTPClient

def parse_headers(header_string):
    """Parse headers from a JSON string into a dictionary."""
    if not header_string:
        return {}
    try:
        headers = json.loads(header_string)
        if not isinstance(headers, dict):
            raise ValueError("Headers must be a JSON object.")
        return headers
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format for headers.")

def main():
    # Create the HTTP client
    client = HTTPClient()

    # Set up the argument parser
    parser = argparse.ArgumentParser(description="HTTP Client for making requests from the command line.", add_help=False)
    
    # Add arguments for HTTP method, URL, headers, and data
    parser.add_argument("-m", "--method", type=str, required=True, help="HTTP method (GET, POST, HEAD, DELETE, PATCH, PUT)")
    parser.add_argument("-u", "--url", type=str, required=True, help="URL to make the request to")
    parser.add_argument("-h", "--headers", type=str, help="Request headers as a JSON string (e.g., '{\"User-Agent\": \"device\"}')", default="{}")
    parser.add_argument("-d", "--data", type=str, help="Request body data", default=None)

    # Parse the arguments
    args = parser.parse_args()

    # Parse headers from JSON string
    try:
        headers = parse_headers(args.headers)
    except ValueError as e:
        print(f"Error parsing headers: {e}")
        return

    # Perform the HTTP request
    try:
        # Handle HEAD request
        if args.method.upper() == "HEAD":
            if args.data:
                print("Error: HEAD requests cannot include a body.")
                return
            status_code, response_body = client.head(args.url, headers=headers)
        
        # Handle DELETE request
        elif args.method.upper() == "DELETE":
            return client.delete(args.url, body=args.data, headers=headers)
        
        # Handle PATCH request
        elif args.method.upper() == "PATCH":
            return client.patch(args.url, body=args.data, headers=headers)
        
        # Handle PUT request
        elif args.method.upper() == "PUT":
            return client.put(args.url, body=args.data, headers=headers)
        
        # Handle other HTTP methods (e.g., GET, POST)
        else:
            return client.http_request(
                method=args.method.upper(),
                url=args.url,
                body=args.data,
                headers=headers
            )

        # Display the response
        print(f"Status Code: {status_code}")
        print("Response Body:")
        print(response_body)

    except Exception as e:
        # Handle any exceptions that occur during the request
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
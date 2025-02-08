import argparse
from urllib.parse import urlencode
from client import HTTPClient

def main():
    # Create the HTTP client
    client = HTTPClient()

    # Set up the argument parser
    parser = argparse.ArgumentParser(description="HTTP Client for making requests from the command line.")
    
    # Add arguments for HTTP method and URL
    parser.add_argument("method", type=str, help="HTTP method (GET, POST, HEAD, DELETE, PATCH, PUT)")
    parser.add_argument("url", type=str, help="URL to make the request to")
    
    # Optional arguments for request body, headers, and query parameters
    parser.add_argument("--body", type=str, help="Request body (for POST, PUT, PATCH, DELETE)", default=None)
    parser.add_argument("--headers", type=str, help="Request headers (format: 'Key: Value, Key2: Value2')", default=None)
    parser.add_argument("--query", type=str, help="Query parameters (format: 'key1=value1&key2=value2')", default=None)

    # Parse the arguments
    args = parser.parse_args()

    # Add query parameters to the URL if provided
    if args.query:
        # Check if the URL already contains query parameters
        separator = "&" if "?" in args.url else "?"
        args.url += separator + args.query

    # Convert headers from string to dictionary
    headers = {}
    if args.headers:
        for header in args.headers.split(","):
            if ":" in header:
                key, value = header.split(":", 1)
                headers[key.strip()] = value.strip()

    # Perform the HTTP request
    try:
        # Handle HEAD request
        if args.method.upper() == "HEAD":
            status_code, response_body = client.head(args.url, headers=headers)
        
        # Handle DELETE request
        elif args.method.upper() == "DELETE":
            status_code, response_body = client.delete(args.url, body=args.body, headers=headers)
        
        # Handle PATCH request
        elif args.method.upper() == "PATCH":
            status_code, response_body = client.patch(args.url, body=args.body, headers=headers)
        
        # Handle PUT request
        elif args.method.upper() == "PUT":
            status_code, response_body = client.put(args.url, body=args.body, headers=headers)
        
        # Handle other HTTP methods (e.g., GET, POST)
        else:
            status_code, response_body = client.http_request(
                method=args.method.upper(),
                url=args.url,
                body=args.body,
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
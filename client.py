import socket

def parse_url(url):
    """Parses the URL and returns (host, port, path)."""
    # Remove the scheme (http:// or https://)
    if url.startswith("http://"):
        url = url[7:]  # Remove "http://"
    elif url.startswith("https://"):
        raise ValueError("HTTPS is not supported in this implementation.")
    
    # Separate host:port from the path
    parts = url.split("/", 1)  # Split at the first "/"
    host_port = parts[0]  # The first part contains host:port
    path = "/" + parts[1] if len(parts) > 1 else "/"  # Path is the rest or "/" if none
    
    # Separate port if specified
    if ":" in host_port:
        host, port = host_port.split(":", 1)  # Split host and port
        port = int(port)  # Convert port to integer
    else:
        host = host_port  # No port specified, use default
        port = 80  # Default HTTP port
    
    return host, port, path  # Return parsed components


def http_get(url):
    """Performs a GET request and returns (status_code, body)."""
    # Parse the URL to extract host, port, and path
    host, port, path = parse_url(url)
    
    # Create a TCP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))  # Connect to the server
    
    # Build the HTTP GET request
    request = (
        f"GET {path} HTTP/1.1\r\n"  # Specify the method, path, and protocol
        f"Host: {host}\r\n"  # Add the Host header
        "Connection: close\r\n"  # Indicate that the connection should be closed after the response
        "\r\n"  # End of headers
    )
    sock.send(request.encode())  # Send the request as bytes
    
    # Receive the response
    response = b""  # Initialize an empty byte string to store the response
    while True:
        data = sock.recv(4096)  # Receive data in chunks of 4KB
        if not data:  # If no more data is received, break out of the loop
            break
        response += data  # Append received data to the response buffer
    
    sock.close()  # Close the socket after receiving the full response
    
    # Separate headers and body
    headers_body = response.split(b"\r\n\r\n", 1)  # Split headers from body using the blank line separator
    headers = headers_body[0].decode("utf-8", errors="ignore")  # Decode headers to string
    body = headers_body[1] if len(headers_body) > 1 else b""  # Extract body if it exists
    
    # Extract status code from the status line
    status_line = headers.split("\r\n")[0]  # Get the first line (e.g., "HTTP/1.1 200 OK")
    status_code = int(status_line.split(" ")[1])  # Extract the status code (e.g., "200")
    
    return status_code, body.decode("utf-8", errors="ignore")  # Return status code and decoded body


# Example usage
if __name__ == "__main__":
    url = "http://example.com"  # Use HTTP (not HTTPS)
    status_code, body = http_get(url)  # Perform the GET request
    print(f"Status Code: {status_code}")  # Print the status code
    print("\nResponse Body:")  # Print the body of the response
    print(body)
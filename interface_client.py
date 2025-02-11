import socket
import ssl
import hmac
import hashlib
class HTTPClient:
    def hmac_generator(self, key, msg):
        return hmac.new(key.encode(), msg.encode(), hashlib.sha256).hexdigest()

    def parse_url(self, url):
        """Parses the URL and returns (host, port, path, use_ssl)."""
        use_ssl = False
        # Remove the scheme (http:// or https://)
        if url.startswith("http://"):
            url = url[7:]  # Remove "http://"
        elif url.startswith("https://"):
            url = url[8:]  # Remove "https://"
            use_ssl = True
        
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
            port = 443 if use_ssl else 80  # Default HTTPS or HTTP port
        
        return host, port, path, use_ssl  # Return parsed components

    def http_request(self, method, url, body=None, headers=None):
        """Performs an HTTP request and returns (status_code, body)."""
        
        if method.upper() == "HEAD" and body is not None:
            raise ValueError("Las solicitudes HEAD no pueden incluir un cuerpo.")

        # Parse the URL to get the host, port, path, and SSL usage
        host, port, path, use_ssl = self.parse_url(url)
        
        # Create a socket for the connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Wrap the socket with SSL if needed
        if use_ssl:
            context = ssl.create_default_context()
            sock = context.wrap_socket(sock, server_hostname=host)
        
        sock.connect((host, port))
        
        # Build basic headers
        default_headers = {
            "Host": host,
            "Connection": "close"
        }
        
        # Add custom headers if provided
        if headers:
            default_headers.update(headers)
        
        # Add Content-Length header if there is a body
        if body:
            default_headers["Content-Length"] = str(len(body))
        
        # Construct the request lines
        request_lines = [f"{method} {path} HTTP/1.1"]
        for key, value in default_headers.items():
            request_lines.append(f"{key}: {value}")
        request = "\r\n".join(request_lines) + "\r\n\r\n"
        
        # Add the body to the request if it exists
        if body:
            request += body
        
        # Send the request through the socket
        sock.send(request.encode())
        
        # Receive the response
        response = b""
        while True:
            data = sock.recv(4096)
            if not data:
                break
            response += data
        
        # Close the socket connection
        sock.close()
        
        # Process the response
        headers_body = response.split(b"\r\n\r\n", 1)
        headers = headers_body[0].decode("utf-8", errors="ignore")
        body = headers_body[1] if len(headers_body) > 1 else b""
        
        # Extract the status code from the response
        status_line = headers.split("\r\n")[0]
        status_code = int(status_line.split(" ")[1])
        
        # Return the status code and the body of the response
        return status_code, headers, body.decode("utf-8", errors="ignore")
    
    def head(self, url, headers=None):
        """Carry out a HEAD request and returns status_code and empty body."""
        return self.http_request("HEAD", url, headers=headers)
    
    def delete(self, url, body=None, headers=None):
        """Carry out a DELETE request and returns status_code and body."""
        return self.http_request("DELETE", url, body=body, headers=headers)
    
    def patch(self, url, body=None, headers=None):
        """Carry out a PATCH request and returns status_code and body."""
        return self.http_request("PATCH", url, body=body, headers=headers)
    
    def put(self, url, body=None, headers=None):
        """Carry out a PUT request and returns status_code and body."""
        return self.http_request("PUT", url, body=body, headers=headers)
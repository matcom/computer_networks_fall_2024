# Import necessary modules for handling HTTP requests and networking
from .request_handler import PicoHTTPRequestHandler  # Custom request handler module
import socket  # Module for working with sockets
import logging  # Module for logging messages

# Configure the logger to capture information about server operations
logger = logging.getLogger(__name__)

# Define the PicoTCPServer class to handle TCP connections and serve HTTP requests
class PicoTCPServer:
    # Constructor method to initialize the server with a socket address and request handler
    def __init__(
        self, 
        socket_address: tuple[str, int],  # Tuple containing the IP address and port number
        request_handler: PicoHTTPRequestHandler  # Instance of the request handler class
    ) -> None:
        # Assign the request handler to the instance variable
        self.request_handler = request_handler
        # Create a TCP/IP socket
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Set the socket option to reuse the address, avoiding "address already in use" errors
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the socket to the specified address and port
        self.sock.bind(socket_address)
        # Start listening for incoming connections
        self.sock.listen()

    # Method to continuously serve incoming connections
    def serve_forever(self) -> None:
        # Infinite loop to handle client connections
        while True:
            # Accept an incoming connection, returning a new socket object and the client's address
            conn, addr = self.sock.accept()
            # Use a context manager to ensure the connection is properly closed after handling
            with conn:
                # Log the acceptance of the connection
                logger.info(f'Accepted connection from {addr}')
                # Create file-like objects for reading the request and writing the response
                request_stream = conn.makefile('rb')  # Binary read mode for the request
                response_stream = conn.makefile('wb')  # Binary write mode for the response
                # Pass the request and response streams to the request handler
                self.request_handler(
                    request_stream=request_stream,
                    response_stream=response_stream
                )
            # Log the closure of the connection
            logger.info(f'Closed connection from {addr}')

    # Method to support the use of the server in a "with" statement (context manager entry)
    def __enter__(self):
        return self

    # Method to close the socket when exiting a "with" statement (context manager exit)
    def __exit__(self, *args) -> None:
        # Close the server socket to release resources
        self.sock.close()
import argparse
import logging
from request_handler import PicoHTTPRequestHandler  # Ensure this module is in the same directory or in the PYTHONPATH
from tcp_server import PicoTCPServer  # Ensure this file is in the same directory or in the PYTHONPATH

# Configure the logger to display messages on the console
logging.basicConfig(level=logging.INFO)

def main():
    # Set up the argument parser
    parser = argparse.ArgumentParser(description='Start the PicoTCPServer.')
    parser.add_argument('--host', type=str, default='127.0.0.1' , help='The IP address the server will listen on (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8080, help='The port the server will listen on (default: 8080)')

    # Parse the command line arguments
    args = parser.parse_args()

    # Define the IP address and port for the server to listen on
    socket_address = (args.host, args.port)

    logging.info(f'Server is starting and listening on {args.host}:{args.port}')

    # Create an instance of the server
    with PicoTCPServer(socket_address, PicoHTTPRequestHandler) as server:
        # Start the server to listen for incoming connections
        server.serve_forever()

if __name__ == '__main__':
    main()
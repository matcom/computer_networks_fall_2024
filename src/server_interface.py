import socket
import threading 
import ssl

class ServerInterface:
    def __init__(self, server, port, nickname, message_callback, use_ssl=False):
        self.server = server
        self.port = port
        self.nickname = nickname
        self.connected = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receiving_thread = None
        self.message_callback = message_callback 
        self.use_ssl = use_ssl 

    def connect(self, nickname, username, realname):
        # Connect to the server
        self.socket.connect((self.server, self.port))
        if self.use_ssl:
            # Create a new SSL context with a specific SSL/TLS version and cipher suites
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)  # Use the highest protocol version that both client and server support
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE  # Disable certificate verification
            self.socket = context.wrap_socket(self.socket, server_hostname=self.server)
        self.connected = True

        # Send the NICK and USER commands
        self.send_message("NICK {}".format(nickname))
        self.send_message("USER {} 0 * :{}".format(username, realname))
        
        # Start the receiving thread
        self.receiving_thread = threading.Thread(target=self.fetch_server_messages)
        self.receiving_thread.start()

    def send_message(self, message):
        # Send a message to the server
        self.socket.send((message + "\r\n").encode('utf-8'))

    def fetch_server_messages(self):
        buffer = ""
        while self.connected:
            try:
                raw_data = self.socket.recv(2048)
                start = 0
                while start < len(raw_data):
                    try:
                        # Try to decode a chunk of data
                        chunk = raw_data[start:start+1024].decode('utf-8')
                        buffer += chunk
                        start += 1024
                    except UnicodeDecodeError:
                        # If a UnicodeDecodeError occurs, skip to the next chunk
                        start += 1024

                while "\r\n" in buffer:
                    line, buffer = buffer.split("\r\n", 1)
                    self.message_callback(line)
                    print(line) #debug
            except Exception as e:
                print(f"Connection was aborted due to error: {e}")
                break 

    def stop(self):
        # Set connected to False
        self.connected = False
        if self.socket.fileno() != -1:
            # Send a message to the server
            self.send_message("QUIT")   
            self.socket.close()
        else:
            print("Error: Attempted to send a message on a closed socket.")
        
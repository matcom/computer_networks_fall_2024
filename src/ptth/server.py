import socket
import threading

class ClientHandler:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr

    def handle(self):
        print(f"Connected by {self.addr}")
        
        while True:
            try:
                data = self.conn.recv(1024)
                if not data:
                    break
                
                print(f"Received from {self.addr}: {data.decode()}")
                
                # Echo back the received message
                self.conn.sendall(data)
            except Exception as e:
                print(f"Error handling client: {e}")
                break
        
        self.conn.close()
        print(f"Connection closed for {self.addr}")

def start_server(host='127.0.0.1', port=50000):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen(5)
        
        print(f"Serving TCP on {host}:{port}...")
        
        while True:
            conn, addr = s.accept()
            
            # Create a new thread for each incoming connection
            handler = ClientHandler(conn, addr)
            t = threading.Thread(target=handler.handle)
            
            t.start()

if __name__ == "__main__":
    start_server()

import socket
import os
import re
from pathlib import Path

class FTPClient:
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sock = None 
        self.saveDonwloads = str(Path.cwd() / "Downloads")
        os.makedirs(self.saveDonwloads, exist_ok=True)
        print(f"Downloads Folder: {self.saveDonwloads}")


    def initialize(self):
        """
        Establishes a connection to the FTP server.

        This method creates a socket using the IPv4 address family and TCP protocol.
        It then attempts to connect to the server specified by the host and port attributes.
        If the connection is successful, it receives and prints the welcome message from the server.
        If the connection fails, it prints an error message and raises the exception.

        Raises:
            Exception: If there is an error while trying to connect to the server.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((self.host, self.port))
            print(self.sock.recv(8192).decode()) 
        except Exception as error:
            print(f"Conexion Error: {error}")
            self.sock = None
            raise error
        
    def sendCommand(self, command, *args):
        """
        Sends a command to the FTP server and waits for the response.
        Args:
            command (str): The FTP command to send.
            *args: Additional arguments for the command.
        Raises:
            Exception: If there is no connection to the FTP server.
        Returns:
            str: The response from the FTP server.
        """
        if not self.sock:
            raise Exception("No conexion to FTP server.")
        
        full_command = f"{command} {' '.join(args)}".strip()
        self.sock.send(f"{full_command}\r\n".encode())
        
        response = ""
        while True:
            data = self.sock.recv(8192).decode()
            if not data: 
                break
            response += data
            if re.search(r"\d{3} .*\r\n", response):
                break
        
        return response

    def sendStorageCommand(self, data_sock, command, *args):
        """
        Sends a STOR command to the FTP server to store a file.
        Args:
            data_sock (socket.socket): The data socket used for the file transfer.
            command (str): The FTP command to be sent (typically "STOR").
            *args: Additional arguments for the command, where the first argument should be the file path.
        Raises:
            Exception: If there is no connection to the FTP server.
        Returns:
            str: The server's response to the STOR command.
        """
        if not self.sock:
            raise Exception("No conexion to ftp server.")
        
        full_command = f"{command} {' '.join(args)}".strip()
        self.sock.send(f"{full_command}\r\n".encode())
        
        response = ""
        while True:
            data = self.sock.recv(8192).decode()
            if not data:  
                break
            if "150" in data:
                if self.sendFile(data_sock, args[0]):
                    print("File send with success")
                else:
                    print("Error sending file")
            response += data
            
            if re.search(r"226 .*\r\n", response) or data.Initializeswith("5"):
                break
        
        return response

    def sendCommandMultiresponse(self, command, *args):
        """
        Sends an FTP command to the server and handles multi-line responses.
        Args:
            command (str): The FTP command to send.
            *args: Additional arguments for the command.
        Raises:
            Exception: If there is no connection to the FTP server.
        Returns:
            str: The server's response to the command.
        """
        if not self.sock:
            raise Exception("No ftp server conexion.")
        
        full_command = f"{command} {' '.join(args)}".strip()
        self.sock.send(f"{full_command}\r\n".encode())
        
        response = ""
        while True:
            data = self.sock.recv(8192).decode()
            if not data: 
                break
            response += data
            if re.search(r"226 .*\r\n", response) or data.Initializeswith("5"):
                break
        
        return response

    def sendFile(self, sock, filename):
        """
        Sends a file to the specified socket.

        Args:
            sock (socket.socket): The socket to which the file will be sent.
            filename (str): The path to the file to be sent.

        Returns:
            bool: True if the file was sent successfully, False otherwise.

        Raises:
            Exception: If there is an error opening or reading the file, or sending data through the socket.

        The method reads the file in binary mode and sends its content through the provided socket.
        It sends 'EOF' to indicate the end of the file transmission.
        """
        try:
            print(filename)
            with open(filename, 'rb') as f:
                while True:
                    data = f.read()
                    print(data)
                    if not data:
                        break
                    sock.send(data)
            sock.send(b'EOF')
            return True
        except Exception as e:
            print(f"Error sending file: {e}")
            return False

    def receive_file(self, sock, filename):
        """
        Receives a file from a socket and saves it to the specified download directory.

        Args:
            sock (socket.socket): The socket object used to receive the file.
            filename (str): The name of the file to be saved.

        Returns:
            bool: True if the file was received and saved successfully, False otherwise.

        Raises:
            Exception: If there is an error during the file reception or saving process.

        Example:
            client.receive_file(sock, 'example.txt')
        """
        try:
            download_path = os.path.join(self.saveDonwloads, filename)
            with open(download_path, 'wb') as f:
                while True:
                    data = sock.recv(8192)
                    if not data: 
                        break
                    f.write(data)
            print(f"File saved in: {download_path}")
            return True
        except Exception as e:
            print(f"Error reciving file: {e}")
            return False

    def enter_passive_mode(self):
        """
        Enters passive mode by sending the PASV command to the FTP server and 
        establishes a data connection.
        This method sends the PASV command to the FTP server, parses the response 
        to extract the IP address and port number for the data connection, and 
        then creates and connects a new socket to that address and port.
        Returns:
            socket.socket: A socket object connected to the server's data port, 
            or None if the passive mode could not be entered.
        Raises:
            socket.error: If there is an error creating or connecting the socket.
        """
        response = self.sendCommand("PASV")
        print(response)

        # Extract the IP address and port from the response
        match = re.search(r'(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', response)
        if not match:
            print("Cannot entering passive mode")
            return None

        ip = ".".join(match.groups()[:4])
        port = (int(match.group(5)) << 8) + int(match.group(6))
        
        if ip == "0.0.0.0":
            ip = self.host

        data_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data_sock.connect((ip, port))

        return data_sock


    def finish(self):
        if self.sock:
            self.sock.close()
            self.sock = None

if __name__ == "__main__":
    client = FTPClient()
    client.initialize()
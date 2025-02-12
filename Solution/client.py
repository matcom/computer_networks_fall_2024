import socket
import ssl
import argparse
import json
import re

def ftpClient(args):
    """
    Main function of the FTP client.
    
    Args:
        args: Parsed command-line arguments containing the following attributes:
            - host: FTP server address.
            - port: FTP server port.
            - username: Username for authentication.
            - password: Password for authentication.
            - command: FTP command to execute.
            - argument1: First argument for the command.
            - argument2: Second argument for the command.
            - use_tls: Boolean indicating whether to use TLS/SSL for the connection.
    """
    server = args.host
    port = args.port
    username = args.username
    password = args.password
    command = args.command
    argument1 = args.argument1
    argument2 = args.argument2
    use_tls = args.use_tls  

    command_templates = {
        "USER": f"USER {argument1}\r\n",
        "PASS": f"PASS {argument1}\r\n",
        "ACCT": f"ACCT {argument1}\r\n",
        "CWD" : f"CWD {argument1}\r\n",
        "CDUP": "CDUP\r\n",
        "SMNT": f"SMNT {argument1}\r\n",
        "REIN": "REIN\r\n",
        "QUIT": "QUIT\r\n",
        "PORT": f"PORT {argument1}\r\n",
        "PASV": "PASV\r\n",
        "TYPE": f"TYPE {argument1}\r\n",
        "STRU": f"STRU {argument1}\r\n",
        "MODE": f"MODE {argument1}\r\n",
        "RETR": f"RETR {argument1}\r\n",
        "STOR": f"STOR {argument1}\r\n",
        "STOU": "STOU\r\n",
        "APPE": f"APPE {argument1}\r\n",
        "ALLO": f"ALLO {argument1}\r\n",
        "REST": f"REST {argument1}\r\n",
        "RNFR": f"RNFR {argument1}\r\n",
        "RNTO": f"RNTO {argument2}\r\n",
        "ABOR": "ABOR\r\n",
        "DELE": f"DELE {argument1}\r\n",
        "RMD" : f"RMD {argument1}\r\n",
        "MKD" : f"MKD {argument1}\r\n",
        "PWD" : "PWD\r\n",
        "LIST": f"LIST {argument1}\r\n",
        "NLST": f"NLST {argument1}\r\n",
        "SITE": f"SITE {argument1}\r\n",
        "SYST": "SYST\r\n",
        "STAT": f"STAT {argument1}\r\n",
        "HELP": f"HELP {argument1}\r\n",
        "NOOP": "NOOP\r\n",
    }

    try:
        client_socket = connectToServer(server, port, use_tls)

        welcome_message = client_socket.recv(1024).decode().strip()
        welcome_status = welcome_message.split(" ")[0]
        print(json.dumps({"status": welcome_status, "message": welcome_message}, indent=4))

        user_response = sendCommand(client_socket, f"USER {username}\r\n")
        print(user_response)

        pass_response = sendCommand(client_socket, f"PASS {password}\r\n")
        print(pass_response)

        if "230" in pass_response:  
            if command == "RETR" or command == "STOR":
                pasv_response = sendCommand(client_socket, "PASV\r\n")
                print(pasv_response)
                storageRetrievalFiles(command, pasv_response, server, client_socket, argument1, argument2);
                
            elif command == "RNFR":
                rnfr_response = sendCommand(client_socket, f"RNFR {argument1}\r\n")
                print(rnfr_response)
                renameFile(rnfr_response, client_socket, argument2)
                
            else:
                if command in command_templates:
                    command_response = sendCommand(client_socket, command_templates[command])
                else:
                    command_response = json.dumps({"status": "500", "message": "Unsupported command"}, indent=4)

                print(command_response)
        else:
            print(json.dumps({"status": "530", "message": "Authentication error. Please check your credentials."}, indent=4))

    except Exception as e:
        print(json.dumps({"status": "500", "message": f"Error during execution: {e}"}, indent=4))
    finally:
        client_socket.close()

def sendCommand(client_socket, command):
    """
    Sends a command to the server via the provided client socket and returns the server's response.
    Args:
        client_socket (socket.socket): The socket object used to communicate with the server.
        command (str): The command to be sent to the server.
    Returns:
        str: A JSON-formatted string containing the status code and the server's response message.
    Example:
        response = sendCommand(client_socket, "LIST")
        print(response)
    """
    
    client_socket.sendall(command.encode())
    response = client_socket.recv(1024).decode().strip()
    status_code = response.split(" ")[0] 
    return json.dumps({"status": status_code, "message": response}, indent=4)

def connectToServer(server, port, tls=False):
    """
    Establishes a connection to the specified server and port.

    Args:
        server (str): The server address to connect to.
        port (int): The port number to connect to.
        tls (bool, optional): If True, establishes a TLS/SSL connection. Defaults to False.

    Returns:
        socket.socket: The connected socket object. If use_tls is True, returns an SSL-wrapped socket.
    """

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server, port))

    if tls:
        context = ssl.create_default_context()
        tls_socket = context.wrap_socket(client_socket, server_hostname=server)
        return tls_socket
    else:
        return client_socket
    
def renameFile(rnfr_response, client_socket, argument):
    """
    Renames a file on the FTP server if the initial rename request was successful.

    Parameters:
    rnfr_response (str): The response from the server after sending the RNFR (rename from) command.
    client_socket (socket.socket): The socket object used to communicate with the FTP server.
    argument (str): The new name for the file.

    Returns:
    None
    """
    if "350" in rnfr_response:
        rnto_response = sendCommand(client_socket, f"RNTO {argument}\r\n")
        print(rnto_response)

def parsePasiveResponse(response, server_ip):
    """
    Parses the response of the PASV command from the FTP protocol.

    Args:
        response (str): The server's response to the PASV command.
        server_ip (str): The FTP server's IP address.

    Returns:
        tuple: A tuple containing the IP address and port where the server is waiting for a data connection.
               If the response is invalid, returns the server's IP address and None.
    """
    match = re.search(r"(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)", response)
    if match:
        ip = ".".join(match.groups()[:4])
        port = int(match.groups()[4]) * 256 + int(match.groups()[5])
        return ip, port
    
    return server_ip, None  

def storageRetrievalFiles(command, pasv_response, server, client_socket, argument1,argument2):
    """
        Handles the storage (STOR) and retrieval (RETR) of files in an FTP client.
        Parameters:
        command (str): The FTP command to execute, either "RETR" for retrieving a file or "STOR" for storing a file.
        pasv_response (str): The server's response to the PASV command, containing the IP address and port for the data connection.
        server (str): The server address.
        client_socket (socket.socket): The control connection socket to the FTP server.
        argument1 (str): The first argument for the command, typically the filename to retrieve or the local file path to store.
        argument2 (str): The second argument for the command, typically the remote filename to store.
        Returns:
        None
        Raises:
        None
        Notes:
        - For the "RETR" command, the function retrieves the specified file from the server and prints its contents.
        - For the "STOR" command, the function uploads the specified local file to the server.
        - The function handles the establishment of a data connection in passive mode (PASV).
        - The function verifies the completion of the command by checking for the 226 response code from the server.
        - Error messages are printed in JSON format if there are issues with the PASV response or data connection.
        """    
         
    if "227" in pasv_response: 
        ip, port = parsePasiveResponse(pasv_response, server)  
        if ip and port:
            data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            data_socket.connect((ip, port))

            if command == "RETR":
                handleRETR(client_socket, data_socket, argument1)
                
            elif command == "STOR":
                handleSTOR(client_socket, data_socket, argument1, argument2)
        else:
            print(json.dumps({"status": "500", "message": "Error processing PASV response"}, indent=4))
    else:
        print(json.dumps({"status": "500", "message": "Error entering PASV mode"}, indent=4))
        
def handleRETR(client_socket, data_socket, argument1):
    """
    Executes the RETR command to retrieve a file from the FTP server and handles data reception.

    Args:
        client_socket (socket.socket): The client's control socket.
        data_socket (socket.socket): The data socket for file transfer.
        argument1 (str): The name of the file to retrieve.

    Returns:
        None

    Process:
        1. Sends the RETR command to the FTP server.
        2. Receives and displays the server's response to the RETR command.
        3. Receives the file data in 1024-byte chunks and prints it.
        4. Closes the data connection.
        5. Receives and displays the server's completion message, verifying the 226 status code.
    """
    retr_response = sendCommand(client_socket, f"RETR {argument1}\r\n")
    print(retr_response)

    file_data = data_socket.recv(1024)
    while file_data:
        print(file_data.decode(), end="")
        file_data = data_socket.recv(1024)

    data_socket.close()

    completion_response = client_socket.recv(1024).decode().strip()
    print(json.dumps({"status": completion_response.split(" ")[0], "message": completion_response}, indent=4))
          
def handleSTOR(client_socket, data_socket, argument1, argument2):
    """
    Handles the STOR command to upload a file to the server.
    Args:
        client_socket (socket.socket): The control connection socket to the FTP server.
        data_socket (socket.socket): The data connection socket for transferring the file.
        argument1 (str): The local file path to be uploaded.
        argument2 (str): The remote file name to be stored on the server.
    Returns:
        None
    The function performs the following steps:
    1. Sends the STOR command to the server with the specified remote file name.
    2. Checks the server's response for a positive preliminary reply (code 150).
    3. If the response is positive, reads the local file in chunks and sends it through the data connection.
    4. Closes the data connection after the file is completely sent.
    5. Waits for the server's completion reply (code 226) and prints the response status and message.
    """
    stor_response = sendCommand(client_socket, f"STOR {argument2}\r\n")
    print(stor_response)

    if "150" in stor_response:
        print("Sending file...")
                    
        with open(argument1, "rb") as f:
            file_data = f.read(1024)
            while file_data:
                data_socket.sendall(file_data)
                file_data = f.read(1024)
                print("Sending data chunk...")

            data_socket.shutdown(socket.SHUT_WR)
            data_socket.close()

            completion_response = client_socket.recv(1024).decode().strip()
            print(json.dumps({"status": completion_response.split(" ")[0], "message": completion_response}, indent=4))
    
    

def create_arg_parser():
    """
    Creates and configures the argument parser for the FTP client.

    Returns:
        argparse.ArgumentParser: The configured argument parser.
    """
    parser = argparse.ArgumentParser(description="FTP Client in Python", add_help=False)
    parser.add_argument("-h", "--host", required=True, help="FTP server address")
    parser.add_argument("-p", "--port", type=int, default=21, help="FTP server port")
    parser.add_argument("-u", "--username", required=True, help="Username")
    parser.add_argument("-w", "--password", required=True, help="Password")
    parser.add_argument("-c", "--command", required=False, help="Command to execute")
    parser.add_argument("-a", "--argument1", required=False, help="First argument for the command")
    parser.add_argument("-b", "--argument2", required=False, help="Second argument for the command")
    parser.add_argument("--use_tls", action="store_true", help="Use TLS/SSL for the connection")
    return parser

if __name__ == "__main__":
    # Create and configure the argument parser
    parser = create_arg_parser()

    # Parse the arguments
    argvs = parser.parse_args()

    # Call the main FTP client function
    ftpClient(argvs)
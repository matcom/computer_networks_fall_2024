import os
import shutil
import tempfile
import socket
from pathlib import Path

def handle_user(ftp_server, client_socket,state, args):
    """
    Handles the USER command from the FTP client.
    This function processes the USER command sent by the client to the FTP server.
    It checks if the provided username is valid and sends the appropriate response
    to the client.
    Args:
        ftp_server (FTPServer): The FTP server instance handling the connection.
        client_socket (socket.socket): The socket representing the client connection.
        args (list): A list containing the arguments passed with the USER command.
    Returns:
        None: This function sends a response to the client and does not return a value.
    Responses:
        - If no arguments are provided or more than one argument is provided:
            Sends "501 Syntax error in parameters or arguments\r\n"
        - If the username is valid:
            Sends "331 User name okay, need password\r\n"
        - If the username is invalid:
            Sends "530 Not logged in\r\n"
    """
    if not args or len(args) > 1:
        client_socket.send(b"501 Syntax error in parameters or arguments\r\n")
        return
    
    state.current_user = args[0]
    if state.current_user in ftp_server.users:
        client_socket.send(b"331 Username okay, need password\r\n")
    else:
        state.current_user = None
        client_socket.send(b"530 Invalid username\r\n")

def handle_pass(ftp_server, client_socket,state ,args):
    """
    Handles the PASS command for the FTP server.
    This function processes the password provided by the client and 
    authenticates the user if the password matches the stored password 
    for the current user.
    Args:
        ftp_server (FTPServer): The instance of the FTP server.
        client_socket (socket.socket): The socket connected to the client.
        args (list): A list containing the password provided by the client.
    Returns:
        None
    Behavior:
        - If no password is provided or more than one argument is provided,
          sends "501 Syntax error in parameters or arguments\r\n".
        - If a password is provided:
            - If the current user is set:
                - If the password matches the stored password for the current user,
                  sets the user as authenticated and sends "230 User logged in successfully\r\n".
                - If the password does not match, sends "530 Incorrect password\r\n".
            - If no user is set, sends "503 Login with USER first\r\n".
    """
    if not args or len(args) > 1:
        client_socket.send(b"501 Syntax error in parameters or arguments\r\n")
        return
    
    password = args[0]
    if state.current_user:
        if password == ftp_server.users[state.current_user]:
            state.authenticated = True  # Cliente autenticado
            client_socket.send(b"230 User logged in successfully\r\n")
        else:
            client_socket.send(b"530 Incorrect password\r\n")
    else:
        client_socket.send(b"503 Login with USER first\r\n")

def handle_pwd(ftp_server, client_socket,state ,args):
    """
    Handle the PWD (Print Working Directory) command for the FTP server.
    This function sends the current working directory of the FTP server to the client.
    If any arguments are provided with the PWD command, it sends a syntax error response.
    Args:
        ftp_server (FTPServer): The FTP server instance.
        client_socket (socket.socket): The client socket to send responses to.
        args (list): The list of arguments provided with the PWD command.
    Responses:
        501: Syntax error if arguments are provided.
        257: The current working directory of the FTP server.
    """
    if args:
        client_socket.send(b"501 Syntax error in parameters or arguments\r\n")
        return
    
    response = f"257 \"{state.current_dir.relative_to(state.base_dir)}\"\r\n"
    client_socket.send(response.encode())

def handle_cwd(ftp_server, client_socket,state,args):
    """
    Handles the 'CWD' (Change Working Directory) command for the FTP server.

    Parameters:
    ftp_server (FTPServer): The instance of the FTP server handling the request.
    client_socket (socket): The socket connected to the client.
    args (list): A list containing the arguments passed with the 'CWD' command.

    Returns:
    None: Sends a response to the client based on the result of the command.
        - "501 Invalid syntax\r\n" if no arguments are provided or more than one argument is provided.
        - "250 Directory successfully changed\r\n" if the directory change is successful.
        - "550 Directory does not exist\r\n" if the specified directory does not exist.
        - "550 Error changing directory\r\n" if there is an error while changing the directory.
    """
    if not args or len(args) > 1:
        client_socket.send(b"501 Invalid syntax\r\n")
        return
    try:
        if args[0] == "..":
            print('Entering in CDUP from CWD')
            handle_cdup(ftp_server,client_socket, state, [])
            return
        new_path = (state.current_dir / args[0]).resolve()
        if new_path.exists() and new_path.is_dir():
            state.current_dir = new_path
            client_socket.send(b"250 Directory successfully changed\r\n")
        else:
            client_socket.send(b"550 Directory does not exist\r\n")
    except:
        client_socket.send(b"550 Error changing directory\r\n")

def handle_cdup(ftp_server, client_socket,state,args):
    """
    Handle the CDUP (Change to Parent Directory) FTP command.

    This function changes the current directory of the FTP server to its parent directory.
    It sends appropriate responses to the client based on the success or failure of the operation.

    Args:
        ftp_server (FTPServer): The FTP server instance.
        client_socket (socket.socket): The client socket to send responses to.
        args (str): The arguments passed with the CDUP command.

    Returns:
        None: Sends responses to the client socket:
            - "501 Syntax error in parameters or arguments\r\n" if arguments are provided.
            - "550 Cannot go up. You are already in the root directory.\r\n" if already in the base directory.
            - "250 Directory successfully changed\r\n" if the directory change is successful.
            - "550 Directory does not exist\r\n" if the new directory does not exist.
            - "550 Error changing directory\r\n" if an exception occurs during the directory change.
    """
    if args:
        client_socket.send(b"501 Syntax error in parameters or arguments\r\n")
        return
    try:
        if state.current_dir == state.base_dir:
            client_socket.send(b"550 Cannot go up. You are already in the root directory.\r\n")
        else:
            new_path = state.current_dir.parent.resolve()
            if new_path.exists() and new_path.is_dir():
                state.current_dir = new_path
                client_socket.send(b"250 Directory successfully changed\r\n")
            else:
                client_socket.send(b"550 Directory does not exist\r\n")
    except:
        client_socket.send(b"550 Error changing directory\r\n")

def handle_list(ftp_server, client_socket,state ,args):
    """
    Handles the LIST command for the FTP server, which lists the files in the current directory or a specified directory.
    Args:
        ftp_server (FTPServer): The FTP server instance.
        client_socket (socket.socket): The client socket to send responses to.
        args (list): A list of arguments provided with the LIST command.
    Returns:
        None: Sends appropriate FTP response codes to the client socket.
    FTP Response Codes:
        501: Syntax error in parameters or arguments.
        150: File status okay; about to open data connection.
        226: Closing data connection. Requested file action successful.
        550: Requested action not taken. File unavailable.
    """
    if args and len(args) > 1:
        client_socket.send(b"501: Syntax error in parameters or arguments\r\n")
        return
    
    try:
        path = state.current_dir / args[0] if args else state.current_dir
        client_socket.send(b"150: File status okay; about to open data connection.\r\n")
        print(path)
        
        state.data_socket, _ = state.pasv_socket.accept()
        
        files = "\r\n".join(str(f.name) for f in path.iterdir())
        state.data_socket.send(files.encode())
        
        client_socket.send(b"226: Closing data connection. Requested file action successful.\r\n")
        state.data_socket.close()
        state.data_socket = None
    except Exception as e:
        print(f"Error en LIST: {e}")
        client_socket.send(b"550: Requested action not taken. File unavailable.\r\n")

def handle_mkd(ftp_server, client_socket,state, args):
    """
    Handle the MKD (Make Directory) command from the FTP client.

    This function creates a new directory in the current directory of the FTP server.
    It sends appropriate responses to the client based on the success or failure of the operation.

    Args:
        ftp_server (FTPServer): The FTP server instance handling the request.
        client_socket (socket.socket): The socket connected to the FTP client.
        args (list): A list containing the name of the directory to be created.

    Returns:
        None: This function sends responses directly to the client socket.

    Responses:
        501: Syntax error in parameters or arguments (if no directory name is provided or too many arguments are given).
        257: Directory created successfully (if the directory is created).
        550: Requested action not taken (if there is an error creating the directory).
    """
    if not args or len(args) > 1:
        client_socket.send(b"501: Syntax error in parameters or arguments\r\n")
        return
    try:
        new_dir = (state.current_dir / args[0])
        new_dir.mkdir(parents=True, exist_ok=True)
        client_socket.send(f"257: \"{new_dir}\" Directory created successfully.\r\n".encode())
    except:
        client_socket.send(b"550: Requested action not taken\r\n")

def handle_rmd(ftp_server, client_socket,state ,args):
    """
    Handle the RMD (Remove Directory) command from the FTP client.

    Parameters:
    ftp_server (FTPServer): The FTP server instance.
    client_socket (socket): The socket connected to the client.
    args (list): List of arguments passed with the RMD command.

    Returns:
    None: Sends a response to the client based on the result of the command.
        - "501 Syntax error in parameters or arguments\r\n": If the arguments are invalid.
        - "250 Directory removed\r\n": If the directory is successfully removed.
        - "550 Not a directory\r\n": If the specified path is not a directory.
        - "550 Error removing directory\r\n": If there is an error while removing the directory.
    """
    if not args or len(args) > 1:
        client_socket.send(b"501 Syntax error in parameters or arguments\r\n")
        return
    try:
        dir_to_remove = (state.current_dir / args[0])
        if dir_to_remove.is_dir():
            shutil.rmtree(dir_to_remove)
            client_socket.send(b"250 Directory removed\r\n")
        else:
            client_socket.send(b"550 Not a directory\r\n")
    except:
        client_socket.send(b"550 Error removing directory\r\n")

def handle_dele(ftp_server, client_socket,state,args):
    """
    Handle the DELE command from the FTP client to delete a file.

    Parameters:
    ftp_server (FTPServer): The instance of the FTP server handling the request.
    client_socket (socket): The socket connected to the FTP client.
    args (list): The arguments provided with the DELE command. Should contain the filename to delete.

    Returns:
    None: Sends a response to the client based on the result of the delete operation.
        - "501 Syntax error in parameters or arguments\r\n": If the arguments are invalid (either none or more than one).
        - "250 File deleted successfully\r\n": If the file was successfully deleted.
        - "550 Not a file\r\n": If the specified path is not a file.
        - "550 Error deleting file\r\n": If there was an error deleting the file.
    """
    if not args or len(args) > 1:
        client_socket.send(b"501 Syntax error in parameters or arguments\r\n")
        return
    try:
        file_to_delete = (state.current_dir / args[0])
        if file_to_delete.is_file():
            file_to_delete.unlink()
            client_socket.send(b"250 File deleted successfully\r\n")
        else:
            client_socket.send(b"550 Not a file\r\n")
    except:
        client_socket.send(b"550 Error deleting file\r\n")

def handle_rnfr(ftp_server, client_socket,state, args):
    """
    Handles the RNFR (Rename From) FTP command.

    This function processes the RNFR command which specifies the old pathname of the file which is to be renamed.
    It checks if the provided arguments are valid and if the specified file exists. If the file exists, it sets the
    rename_from attribute of the ftp_server to the specified file path and sends a response indicating readiness for
    the RNTO (Rename To) command. If the file does not exist or the arguments are invalid, it sends an appropriate
    error response.

    Args:
        ftp_server (FTPServer): The FTP server instance handling the request.
        client_socket (socket): The socket connected to the client.
        args (list): A list of arguments provided with the RNFR command.

    Returns:
        None: Sends a response to the client indicating the result of the RNFR command.
        - "501 Syntax error in parameters or arguments\r\n" if the arguments are invalid.
        - "350 Ready for RNTO\r\n" if the file exists and the server is ready for the RNTO command.
        - "550 File not found\r\n" if the specified file does not exist.
    """
    if not args or len(args) > 1:
        client_socket.send(b"501 Syntax error in parameters or arguments\r\n")
        return
    file_path = (state.current_dir / args[0])
    if file_path.exists():
        state.rename_from = file_path
        client_socket.send(b"350 Ready for RNTO\r\n")
    else:
        client_socket.send(b"550 File not found\r\n")

def handle_rnto(ftp_server, client_socket,state, args):
    """
    Handles the RNTO (rename to) FTP command. This command is used to rename a file on the server.

    Parameters:
    ftp_server (FTPServer): The instance of the FTP server handling the request.
    client_socket (socket): The socket connected to the client.
    args (list): A list containing the new name for the file.

    Returns:
    None: Sends appropriate response messages to the client based on the outcome of the rename operation.

    Responses:
    - 503: Sent if the RNFR (rename from) command was not issued first.
    - 501: Sent if the syntax of the RNTO command is invalid.
    - 250: Sent if the file was successfully renamed.
    - 553: Sent if there was an error renaming the file.
    """
    if not state.rename_from:
        client_socket.send(b"503 RNFR command required first\r\n")
        return
    if not args or len(args) > 1:
        client_socket.send(b"501 Syntax error in parameters or arguments\r\n")
        return
    try:
        new_path = (ftp_server.current_dir / args[0])
        state.rename_from.rename(new_path)
        client_socket.send(b"250 File renamed successfully\r\n")
    except:
        client_socket.send(b"553 Error renaming file\r\n")
    finally:
        state.rename_from = None

def handle_syst(ftp_server, client_socket,state, args):
    """
    Handle the SYST command for the FTP server.

    The SYST command is used to return the type of operating system
    running on the server. This implementation responds with a UNIX
    type.

    Parameters:
    ftp_server (object): The FTP server instance.
    client_socket (socket): The socket connected to the client.
    args (str): The arguments passed with the SYST command.

    Returns:
    None

    Response Codes:
    215 - UNIX Type: L8 (if no arguments are provided)
    501 - Syntax error in parameters or arguments (if arguments are provided)
    """
    if args:
        client_socket.send(b"501 Syntax error in parameters or arguments\r\n")
        return
    client_socket.send(b"215 UNIX Type: L8\r\n")

def handle_help(ftp_server, client_socket, state,args):
    """
    Handles the HELP command for the FTP server.

    This function generates a list of available commands supported by the FTP server
    and sends it to the client in a formatted response.

    Args:
        ftp_server (FTPServer): The instance of the FTP server containing the commands.
        client_socket (socket): The socket connected to the client.
        args (list): Additional arguments for the HELP command (not used in this function).

    Response Codes:
        214: Help message.
    """
    if args and len(args) > 1:
        client_socket.send(b"501 Sintaxis: HELP [command]\r\n")
        return
    
    if args:
        helpCommand = args[0].upper()
        if helpCommand in ftp_server.commands_help:
            print(ftp_server.commands_help[helpCommand])
            response = f"214 {helpCommand}: {ftp_server.commands_help[helpCommand]}.\r\n"
        else:
            response = f"501 Comando \'{helpCommand}\' no reconocido\r\n"
    
    else:
        commands = ", ".join(sorted(ftp_server.commands.keys()))
        response = f"214-The following commands are available:\r\n{commands}\r\n214 End of help.\r\n"
    client_socket.send(response.encode())

def handle_noop(ftp_server, client_socket,state, args):
    """
    Handle the NOOP (no operation) command for the FTP server.

    This command does nothing except return a response to the client.
    It is used to keep the connection alive.

    Parameters:
    ftp_server (FTPServer): The instance of the FTP server.
    client_socket (socket): The socket connected to the client.
    args (str): The arguments passed with the NOOP command.

    Returns:
    None

    Sends:
    - "501 Syntax error in parameters or arguments\r\n" if arguments are provided.
    - "200 Command okay\r\n" if no arguments are provided.
    """
    if args:
        client_socket.send(b"501 Syntax error in parameters or arguments\r\n")
        return
    client_socket.send(b"200 Command okay\r\n")

def handle_quit(ftp_server, client_socket,state, args):
    """
    Handles the QUIT command from an FTP client.

    This function processes the QUIT command sent by the client. If the command
    includes any arguments, it responds with a "501 Syntax error in parameters or arguments"
    message. If the command is correctly formatted without arguments, it responds with a 
    "221 Service closing control connection" message and indicates that the connection 
    should be closed.

    Args:
        ftp_server: The FTP server instance handling the connection.
        client_socket: The socket object representing the client's connection.
        args: The arguments passed with the QUIT command.

    Returns:
        bool: True if the connection should be closed, otherwise None.
    """
    if args:
        client_socket.send(b"501 Syntax error in parameters or arguments\r\n")
        return
    client_socket.send(b"221 Goodbye: Service closing control connection\r\n")
    return True

def handle_acct(ftp_server, client_socket,state, args):
    """
    Handle the ACCT (account) command for the FTP server.

    This function processes the ACCT command sent by the client. The ACCT command
    is used to specify the account information for the client. However, in this
    implementation, no account information is required.

    Parameters:
    ftp_server (object): The FTP server instance.
    client_socket (socket): The socket connected to the client.
    args (list): The arguments provided with the ACCT command.

    Behavior:
    - If no arguments are provided or more than one argument is provided, it sends
      a "501 Syntax error" response to the client.
    - If the correct number of arguments is provided, it sends a "230 No account
      required" response to the client.

    Response Codes:
    - 501: Syntax error in parameters or arguments.
    - 230: User logged in, proceed. No account required.
    """
    if not args or len(args) > 1:
        client_socket.send(b"501: Syntax error in parameters or arguments.\r\n")
        return
    client_socket.send(b"230: User logged in, proceed. No account required.\r\n")

def handle_smnt(ftp_server, client_socket,state, args):
    """
    Handle the SMNT (Structure Mount) command for the FTP server.

    This function allows the user to mount a different file system structure without altering
    their login or accounting information. The transfer parameters also remain unchanged.
    The argument is a path that specifies a directory or a system-dependent file group designator.

    Args:
        ftp_server (FTPServer): The FTP server instance handling the request.
        client_socket (socket.socket): The socket connected to the FTP client.
        args (list): A list containing the path to be mounted.

    Returns:
        None: Sends appropriate response messages to the client based on the outcome of the mount operation.

    Responses:
        - "501 Syntax error in parameters or arguments\r\n": If the arguments are invalid.
        - "250 Directory successfully mounted\r\n": If the directory is successfully mounted.
        - "550 Directory does not exist\r\n": If the specified directory does not exist.
        - "550 Error mounting directory\r\n": If there is an error while mounting the directory.
    """
    if not args or len(args) > 1:
        client_socket.send(b"501 Syntax error in parameters or arguments\r\n")
        return
    try:
        new_path = (ftp_server.base_dir / args[0]).resolve()
        if new_path.exists() and new_path.is_dir():
            state.current_dir = new_path
            client_socket.send(b"250 Directory successfully mounted\r\n")
        else:
            client_socket.send(b"550 Directory does not exist\r\n")
    except Exception as e:
        print(f"Error in SMNT: {e}")
        client_socket.send(b"550 Error mounting directory\r\n")

def handle_rein(ftp_server, client_socket,state, args):
    """
    Handle the REIN (REINITIALIZE) command.

    This command terminates a USER session, clearing all I/O and account information,
    except to allow any transfer in progress to complete. All parameters are reset to 
    their default settings, and the control connection remains open. This is identical 
    to the state in which a user is immediately after the control connection is opened. 
    A USER command is expected to follow.

    Args:
        ftp_server (FTPServer): The instance of the FTP server handling the request.
        client_socket (socket): The socket connected to the client.
        args (str): The arguments provided with the REIN command.

    Returns:
        None

    Response Codes:
        220: Service ready for new user.
        501: Syntax error in parameters or arguments.
    """
    if args:
        client_socket.send(b"501: Syntax error in parameters or arguments.\r\n")
        return
    state.current_user = None
    state.authenticated = False
    state.current_dir = ftp_server.base_dir
    client_socket.send(b"220: Service ready for new user.\r\n")

def handle_port(ftp_server, client_socket,state, args):
    """
    Handles the PORT command for the FTP server.
    The PORT command specifies the data port to be used in the data connection.
    The argument is a HOST-PORT specification for the data port. Normally, there
    are default data ports for both the user and server, and under normal
    circumstances, this command and its response are not needed. If this command
    is used, the argument is the concatenation of a 32-bit internet host address
    and a 16-bit TCP port address. This address information is broken into 8-bit
    fields and the value of each field is transmitted as a decimal number (in
    character string representation). The fields are separated by commas. A port
    command would be: PORT h1,h2,h3,h4,p1,p2 where h1 is the high order 8 bits of
    the internet host address.
    Args:
        ftp_server: The FTP server instance.
        client_socket: The client socket to send responses to.
        args: A list of arguments where the first element is the HOST-PORT specification.
    Returns:
        None
    Sends:
        200 Command okay if the PORT command is successful.
        500 Syntax error, command unrecognized if there is an error in the command.
        501 Syntax error in parameters or arguments if the arguments are invalid.
    """
    if not args:
        client_socket.send(b"501 Syntax: PORT h1,h2,h3,h4,p1,p2\r\n")
        return

    try:
        port_parts = args[0].split(',')
        if len(port_parts) != 6:
            client_socket.send(b"501 Syntax error in parameters or arguments\r\n")
            return

        ip = ".".join(port_parts[:4])
        port = (int(port_parts[4]) << 8) + int(port_parts[5])

        state.data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        state.data_socket.connect((ip, port))

        client_socket.send(b"200 Command okay\r\n")
    except Exception as e:
        print(f"Error en PORT: {e}")
        client_socket.send(b"500 Error in command PORT\r\n")

def handle_pasv(ftp_server, client_socket,state, args):
    """
    Handles the PASV (Passive Mode) command for the FTP server.
    This command requests the server-DTP to "listen" on a data port (which is not its default data port) 
    and wait for a connection instead of initiating one upon receiving a transfer command. 
    The response to this command includes the host address and port on which the server is listening.
    Args:
        ftp_server: The FTP server instance.
        client_socket: The client socket connected to the FTP server.
        args: Additional arguments for the command (not used in this function).
    Returns:
        None
    Response Codes:
        227: Entering Passive Mode (success).
        500: Error in passive mode (failure).
    """
    try:
        if hasattr(ftp_server, 'pasv_socket'):
            state.pasv_socket.close()
        
        state.pasv_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        state.pasv_socket.bind((ftp_server.host, 0))
        state.pasv_socket.listen(1)
        _, port = state.pasv_socket.getsockname()

        ip = socket.gethostbyname(socket.gethostname())
        port_bytes = [str(port >> 8), str(port & 0xff)]
        response = f"227 Entering Passive Mode ({','.join(ip.split('.'))},{','.join(port_bytes)})\r\n"
        client_socket.send(response.encode())
    except Exception as e:
        print(f"Error en PASV: {e}")
        client_socket.send(b"500: Error in passive mode\r\n")

def handle_type(ftp_server, client_socket,state, args):
    """
    Handle the FTP TYPE command to specify the data representation type.

    The argument specifies the type of representation as described in the 
    Data Representation and Storage section. Several types require a second 
    parameter. The first parameter is denoted by a single Telnet character, 
    as is the second parameter for Format for ASCII and EBCDIC; the second 
    parameter for local byte is a decimal integer to indicate byte size. 
    Parameters are separated by a <SP> (Space, ASCII code 32).

    The following codes are assigned for type:
                             
               A - ASCII |    | N - Non-print
                         |    | T - Telnet format effectors
               E - EBCDIC|    | C - Carriage control (ASA)
               I - Image

               L <byte size> - Local byte Byte size

    The default representation type is ASCII Non-print. If the Format parameter 
    is changed, and then only the first argument is changed, the Format reverts 
    to the default value of Non-print.

    Args:
        ftp_server (FTPServer): The FTP server instance.
        client_socket (socket): The client socket to send responses.
        args (list): The list of arguments provided with the TYPE command.

    Returns:
        None

    Response Codes:
        200 - Type set to {type_code}
        501 - Syntax: TYPE {A,E,I,L}
        504 - Type not supported
    """
    if not args or len(args) > 1:
        client_socket.send(b"501 Syntax: TYPE {A,E,I,L}\r\n")
        return
    type_code = args[0].upper()
    if type_code in ['A', 'E', 'I', 'L']:
        state.transfer_type = type_code
        client_socket.send(f"200 Type set to {type_code}\r\n".encode())
    else:
        client_socket.send(b"504 Type not supported\r\n")

def handle_stru(ftp_server, client_socket,state, args):
    """
    Handle the STRU (File Structure) command for the FTP server.
    The argument is a single Telnet character code that specifies the file structure as described in the Data Representation and Storage section.
    The following codes are assigned for structure:
        F - File (no record structure)
        R - Record structure
        P - Page structure
    Args:
        ftp_server: The FTP server instance.
        client_socket: The socket connected to the client.
        args: List of arguments passed with the STRU command.
    Returns:
        None
    Response Codes:
        200: Structure set successfully.
        501: Syntax error in parameters or arguments.
        504: Command not implemented for that parameter.
    """
    if not args or len(args) > 1:
        client_socket.send(b"501 Syntax: STRU {F,R,P}\r\n")
        return

    stru_code = args[0].upper()
    if stru_code in ['F', 'R', 'P']:
        state.structure = stru_code
        client_socket.send(f"200 Structure set to {ftp_server.structs[stru_code]}\r\n".encode())
    else:
        client_socket.send(b"504 Structure not supported\r\n")

def handle_mode(ftp_server, client_socket,state, args):
    """
    Handles the MODE command for the FTP server.
    The MODE command specifies the data transfer modes as described in the Transmission Modes section.
    The following codes are assigned for transfer modes:
        S - Stream
        B - Block
        C - Compressed
    Args:
        ftp_server: The FTP server instance.
        client_socket: The client socket to send responses to.
        args: A list of arguments provided with the MODE command.
    Returns:
        None. Sends a response to the client socket.
    Response Codes:
        200: Mode set successfully.
        501: Syntax error in parameters or arguments.
        504: Command not implemented for that parameter.
    """
    if not args or len(args) > 1:
        client_socket.send(b"501 Syntax: MODE {S,B,C}\r\n")
        return
    
    mode_code = args[0].upper()
    if mode_code in ['S', 'B', 'C']:
        state.mode = mode_code
        client_socket.send(f"200 Mode set to {ftp_server.modes[mode_code]}\r\n".encode())
    else:
        client_socket.send(b"504 Mode not supported\r\n")

def handle_retr(ftp_server, client_socket,state, args):
    """
    Handles the RETR (retrieve) command from the FTP client.
    This function retrieves a file from the server and sends it to the client
    over a data connection. It expects a single argument which is the filename
    to be retrieved.
    Args:
        ftp_server (FTPServer): The FTP server instance handling the request.
        client_socket (socket.socket): The control connection socket to the client.
        args (list): A list of arguments passed with the RETR command. Should contain one element, the filename.
    Returns:
        None
    Sends:
        - "501 Syntax: RETR filename\r\n" if the syntax is incorrect.
        - "150 Starting transfer\r\n" when the file transfer is about to start.
        - "226 Transfer complete\r\n" when the file transfer is successfully completed.
        - "550 File not found\r\n" if the requested file does not exist.
        - "550 Error reading file\r\n" if there is an error reading the file.
    """
    if not args or len(args) > 1:
        client_socket.send(b"501 Syntax: RETR filename\r\n")
        return
    try:
        file_path = state.current_dir / args[0]
        if file_path.is_file():
            client_socket.send(b"150 Starting transfer\r\n")
            
            state.data_socket, _ = state.pasv_socket.accept()
            
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read()
                    if not data:
                        break
                    state.data_socket.send(data)
            
            client_socket.send(b"226 Transfer completed\r\n")
            state.data_socket.close()
            state.data_socket = None
        else:
            client_socket.send(b"550 File not found\r\n")
    except Exception as e:
        print(f"Error en RETR: {e}")
        client_socket.send(b"550 Error reading file\r\n")

def handle_stor(ftp_server, client_socket,state, args):
    """
    Handles the STOR command from the FTP client to store a file on the server.
    Parameters:
    ftp_server (FTPServer): The FTP server instance handling the request.
    client_socket (socket.socket): The socket connected to the FTP client.
    args (list): A list of arguments provided with the STOR command. Should contain the filename.
    Returns:
    None
    Sends the following response codes to the client:
    - 150: Ready to receive data.
    - 226: Transfer complete.
    - 501: Syntax error in parameters or arguments.
    - 550: Requested action not taken. File unavailable or error storing file.
    """
    if not args or len(args) > 1:
        client_socket.send(b"501 Syntax: STOR filename\r\n")
        return

    try:
        file_path = state.current_dir / Path(args[0]).name

        client_socket.send(b"150 Ready to receive data\r\n")

        state.data_socket, _ = state.pasv_socket.accept()

        with open(file_path, 'wb') as f:
            while True:
                data = state.data_socket.recv(8192)
                print("Data received")
                if b'EOF' in data:
                    f.write(data.split(b'EOF')[0])
                    break
                f.write(data)

        client_socket.send(b"226 Transfer complete\r\n")

    except Exception as e:
        print(f"Error in STOR: {e}")
        client_socket.send(b"550 Error storing file\r\n")

    finally:
        if state.data_socket:
            state.data_socket.close()

def handle_stou(ftp_server, client_socket,state, args):
    """
    Handle the STOU (Store Unique) FTP command.

    This command is used to store a file on the server with a unique name.
    If arguments are provided, it sends a syntax error response to the client.
    Otherwise, it creates a temporary file in the current directory of the FTP server
    and sends the unique name of the file to the client.

    Args:
        ftp_server (FTPServer): The FTP server instance handling the request.
        client_socket (socket): The socket connected to the client.
        args (str): The arguments provided with the STOU command.

    Responses:
        250: File will be stored with a unique name.
        501: Syntax error in parameters or arguments.
        550: Requested action not taken. File storage error.
    """
    if args:
        client_socket.send(b"501: Syntax error in parameters or arguments\r\n")
        return
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, dir=state.current_dir)
        temp_name = Path(temp_file.name).name
        client_socket.send(f"250 File will be stored as {temp_name}\r\n".encode())
        temp_file.close()
    except:
        client_socket.send(b"550 Error storing file\r\n")

def handle_appe(ftp_server, client_socket,state, args):
    """
    Handles the FTP APPE (append) command from the client.
    This function allows the client to append data to an existing file on the server.
    If the file does not exist, it creates a new file and writes the data to it.
    Args:
        ftp_server (FTPServer): The FTP server instance handling the connection.
        client_socket (socket.socket): The socket connected to the client.
        args (list): A list of arguments passed with the APPE command. It should contain the filename.
    Returns:
        None
    Sends appropriate FTP response codes to the client based on the success or failure of the operation:
        - 501 if the syntax of the command is incorrect.
        - 150 if the server is ready to receive data.
        - 226 if the file transfer is complete.
        - 550 if there is an error appending to the file.
    """
    if not args or len(args) > 1:
        client_socket.send(b"501 Syntax: APPE filename\r\n")
        return
    try:
        file_path = state.current_dir / Path(args[0]).name
        mode = 'ab' if file_path.exists() else 'wb'
        
        client_socket.send(b"150 Ready to receive data\r\n")
        
        state.data_socket, _ = state.pasv_socket.accept()

        with open(file_path, mode) as f:
            while True:
                data = state.data_socket.recv(8192)
                if b'EOF' in data:
                    f.write(data.split(b'EOF')[0])
                    break
                f.write(data)
        
        client_socket.send(b"226 Transfer complete\r\n")
    except:
        client_socket.send(b"550 Error appending to file\r\n")

def handle_allo(ftp_server, client_socket,state, args):
    """
    Handle the ALLO (Allocate) command for the FTP server.

    This command may be required by some servers to reserve sufficient storage to accommodate the new file to be transferred.
    The argument will be a decimal integer representing the number of bytes (using the logical byte size) of storage to be reserved for the file.
    For files sent with record or page structure, a maximum record or page size (in logical bytes) may also be needed; this is indicated by a decimal integer in a second argument field of the command.
    This second argument is optional, but when present, it must be separated from the first by the three Telnet characters <SP> R <SP>.
    This command should be followed by a STORe or APPEnd command.
    The ALLO command should be treated as a NOOP (no operation) by those servers that do not require the maximum file size to be declared in advance, and those servers interested only in the maximum record or page size should accept a dummy value in the first argument and ignore it.

    Args:
        ftp_server (FTPServer): The FTP server instance handling the request.
        client_socket (socket.socket): The socket connected to the FTP client.
        args (list): A list of arguments provided with the ALLO command.

    Returns:
        None: Sends a response to the client indicating the result of the ALLO command.
        - "200 ALLO command okay\r\n" if the command is successfully processed.
        - "501 Syntax error in parameters or arguments\r\n" if the arguments are invalid.
    """
    if not args or len(args) > 2:
        client_socket.send(b"501 Syntax error in parameters or arguments\r\n")
        return

    # Treat ALLO as NOOP since pre-allocation is not required
    client_socket.send(b"200 ALLO command okay\r\n")

def handle_rest(ftp_server, client_socket,state, args):
    """
    Handle the REST command for the FTP server.

    The REST command is used to restart a file transfer from a specific point.
    This implementation currently does not support the REST command and will
    notify the client that the command is not implemented.

    Args:
        ftp_server: The instance of the FTP server handling the request.
        client_socket: The socket object representing the connection to the client.
        args: Additional arguments for the REST command.

    Returns:
        None
    """
    client_socket.send(b"502 REST not implemented\r\n")

def handle_abor(ftp_server, client_socket,state, args):
    """
    Handles the ABOR (abort) command from the FTP client.

    This command is used to abort the previous FTP service command and any 
    associated transfer of data. The server will send a response indicating 
    that the abort command has been processed.

    Args:
        ftp_server: The instance of the FTP server handling the request.
        client_socket: The socket object representing the connection to the client.
        args: Additional arguments passed with the ABOR command (typically empty).

    Returns:
        None
    """
    client_socket.send(b"226 ABOR processed\r\n")

def handle_site(ftp_server, client_socket,state, args):
    """
    Handles the SITE command for the FTP server.

    Parameters:
    ftp_server (FTPServer): The instance of the FTP server.
    client_socket (socket.socket): The socket connected to the client.
    args (list): The arguments passed with the SITE command.

    Returns:
    None
    """
    client_socket.send(b"200 SITE command not supported\r\n")

def handle_stat(ftp_server, client_socket, state, args):
    """
    Handle the STAT command from the FTP client.
    Parameters:
    - client_socket: The socket connected to the client.
    - client_state: The current state of the client, including user and directory information.
    - args: The arguments provided with the STAT command.
    Behavior:
    - If more than one argument is provided, sends "501 Invalid syntax\r\n".
    - If no arguments are provided, sends the server status including the current user and directory.
    - If a single argument is provided, checks if it is a file or directory:
        - If the target does not exist, sends "550 File or directory not found.\r\n".
        - If the target is a file, sends its size, last modification date, and permissions.
        - If the target is a directory, sends its type, permissions, and the number of files it contains.
    Response Codes:
    - 501: Invalid syntax.
    - 211: Server status.
    - 213: Status of a specific file or directory.
    - 550: File or directory not found.
    """
    if args and len(args) > 1:
        client_socket.send(b"501 Invalid syntax\r\n")
        return
        
    if not args:
        response = "211 FTP server status:\r\n"
        response += f"    User: {state.current_user}\r\n"
        response += f"    Current directory: {state.current_dir}\r\n"
        response += "211 End of status\r\n"
            
    else:
        target = args[0]
        target_path = state.current_dir / target

        if not target_path.exists():
            client_socket.send(b"550 File or directory not found.\r\n")
            return

        response = f"213: Status of {target}:\r\n"
        if target_path.is_file():
            response += f"    Size: {target_path.stat().st_size} bytes\r\n"
            response += f"    Last modification date: {target_path.stat().st_mtime}\r\n"
            response += f"    Permissions: {ftp_server.permissionsGet(target_path)}\r\n"
        elif target_path.is_dir():
            response += f"    Type: Directory\r\n"
            response += f"    Permissions: {ftp_server.permissionsGet(target_path)}\r\n"
            response += f"    Files: {len(list(target_path.iterdir()))}\r\n"
        response += "213 End of status.\r\n"
    client_socket.send(response.encode())

def handle_nlst(ftp_server, client_socket,state, args):
    """
    Handle the NLST (Name List) FTP command.
    This function processes the NLST command, which lists the files in the 
    current directory or a specified directory on the FTP server.
    Parameters:
    ftp_server (FTPServer): The instance of the FTP server handling the request.
    client_socket (socket.socket): The socket connected to the client.
    args (list): A list of arguments provided with the NLST command. It can be empty or contain one directory path.
    Behavior:
    - If more than one argument is provided, it sends a "501 Syntax error" response to the client.
    - If no arguments or one argument is provided, it attempts to list the files in the current directory or the specified directory.
    - Sends a "150 Opening data connection" response before starting the file transfer.
    - Sends the list of files over a data connection.
    - Sends a "226 Transfer complete" response after successfully listing the files.
    - In case of an error, it sends a "550 Error listing files" response to the client and logs the error.
    Exceptions:
    - Catches all exceptions, logs the error, and sends a "550 Error listing files" response to the client.
    """
    if args and len(args) > 1:
        client_socket.send(b"501 Invalid syntax\r\n")
        return
    
    try:
        path = state.current_dir / args[0] if args else state.current_dir
        client_socket.send(b"150 Opening data connection\r\n")
        print(path)
        state.data_socket, _ = state.pasv_socket.accept()
        
        files = "\r\n".join(str(f.name) for f in path.iterdir() if f.is_file())
        state.data_socket.send(files.encode())
        
        client_socket.send(b"226 Transfer complete\r\n")
        state.data_socket.close()
        state.data_socket = None
    except Exception as e:
        print(f"Error in NLST: {e}")
        client_socket.send(b"550 Error listing files\r\n")
        

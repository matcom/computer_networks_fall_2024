import socket
import threading
from pathlib import Path
from .handlers import handle_user, handle_pass, handle_pwd, handle_cwd, handle_cdup, handle_list, handle_quit, handle_mkd, handle_rmd, handle_dele, handle_rnfr, handle_rnto, handle_syst, handle_help, handle_noop, handle_acct, handle_smnt, handle_rein, handle_port, handle_pasv, handle_type, handle_stru, handle_mode, handle_retr, handle_stor, handle_stou, handle_appe, handle_allo, handle_rest, handle_abor, handle_site, handle_stat, handle_nlst


class State:
    def __init__(self, base_dir):
        self.current_user = None
        self.authenticated = False
        self.base_dir = base_dir
        self.current_dir = base_dir
        self.rename_from = None  
        self.data_port = 20
        self.transfer_type = 'A'  
        self.structure = 'F'     
        self.mode = 'S'          
        self.data_socket = None


class FTPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.commands = {
            "USER": handle_user,"PASS": handle_pass,"PWD" : handle_pwd,"CWD" : handle_cwd,
            "CDUP": handle_cdup,"LIST": handle_list,"QUIT": handle_quit,"MKD" : handle_mkd,
            "RMD" : handle_rmd,"DELE": handle_dele,"RNFR":handle_rnfr,"RNTO": handle_rnto,
            "SYST": handle_syst,"HELP": handle_help,"NOOP": handle_noop,"ACCT": handle_acct,
            "SMNT": handle_smnt,"REIN": handle_rein,"PORT": handle_port,"PASV": handle_pasv,
            "TYPE": handle_type,"STRU": handle_stru,"MODE": handle_mode,"RETR": handle_retr,
            "STOR": handle_stor,"STOU": handle_stou,"APPE": handle_appe,"ALLO": handle_allo,
            "REST": handle_rest,"ABOR": handle_abor,"SITE": handle_site,"STAT": handle_stat,
            "NLST": handle_nlst
        }
        
        self.users = {
            "Mauricio": "Mauricio"
        }
        
        self.base_dir = Path.cwd()

        self.commands_help = {
            "USER": "Specifies the user. Syntax: USER <username>",
            "PASS": "Specifies the password. Syntax: PASS <password>",
            "PWD" : "Shows the current directory. Syntax: PWD",
            "CWD" : "Changes the working directory. Syntax: CWD <pathname>",
            "CDUP": "Changes the working directory to the parent directory. Syntax: CDUP",
            "LIST": "Lists files and directories. Syntax: LIST [<pathname>]",
            "MKD" : "Creates a directory. Syntax: MKD <pathname>",
            "RMD" : "Removes a directory. Syntax: RMD <pathname>",
            "DELE": "Deletes a file. Syntax: DELE <pathname>",
            "RNFR": "Specifies the file to rename. Syntax: RNFR <pathname>",
            "RNTO": "Specifies the new name. Syntax: RNTO <pathname>",
            "QUIT": "Closes the connection. Syntax: QUIT",
            "HELP": "Shows help. Syntax: HELP [<command>]",
            "SYST": "Shows system information. Syntax: SYST",
            "NOOP": "Does not perform any operation. Syntax: NOOP",
            "ACCT": "Specifies the user account. Syntax: ACCT <account_info>",
            "SMNT": "Mounts a file system structure. Syntax: SMNT <pathname>",
            "REIN": "Restarts the connection. Syntax: REIN",
            "PORT": "Specifies address and port for connection. Syntax: PORT <host-port>",
            "PASV": "Enters passive mode. Syntax: PASV",
            "TYPE": "Sets the transfer type, types are [A]SCII, [E]BCDIC, [I]mage, and [L]ocal_Byte. Syntax: TYPE <type_code>",
            "STRU": "Sets the file structure, types are [F]ile, [R]ecord, and [P]age. Syntax: STRU <structure_code>",
            "MODE": "Sets the transfer mode, types are [S]tream, [B]lock, and [C]ompressed. Syntax: MODE <mode_code>",
            "RETR": "Retrieves a file. Syntax: RETR <pathname>",
            "STOR": "Stores a file. Syntax: STOR <pathname>",
            "STOU": "Stores a file with a unique name. Syntax: STOU",
            "APPE": "Appends data to a file. Syntax: APPE <pathname>",
            "ALLO": "Allocates space. Syntax: ALLO <decimal_integer> or ALLO [R <decimal_integer>]",
            "REST": "Restarts transfer from a point. Syntax: REST <marker>",
            "ABOR": "Aborts an ongoing operation. Syntax: ABOR",
            "SITE": "Site-specific commands. Syntax: SITE <string>",
            "STAT": "Returns current status. Syntax: STAT [<pathname>]",
            "NLST": "Lists file names. Syntax: NLST [<pathname>]"
        }
        self.structs = {
            "F": "File",
            "R": "Record",
            "P": "Page"
        }
        self.modes = {
            "S": "Stream",
            "B": "Block",
            "C": "Compressed"
        }

    def start(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"FTP server started on {self.host}:{self.port}")
        while True:
            client_socket, client_address = server_socket.accept()
            print(f"Connection accepted from {client_address}")
            client_state = State(self.base_dir)
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket,client_state))
            client_thread.start()

    
    def handle_client(self, client_socket, client_state):
            client_socket.send(b"220 Welcome to our FTP server\r\n")
            client_state.rename_from = None  
            client_state.authenticated = False  
            
            while True:
                try:
                    data = client_socket.recv(8192).decode().strip()
                    print(data)
                    if not data:
                        break

                    print(f"Command received: {data}")
                    cmd_parts = data.split()
                    cmd = cmd_parts[0].upper()
                    args = cmd_parts[1:] if len(cmd_parts) > 1 else []

                    if cmd in ["HELP", "QUIT", "USER", "PASS"]:
                        self.commands[cmd](self,client_socket, client_state, args)
                    else:
                        if not client_state.authenticated:
                            client_socket.send(b"530 Please login with USER and PASS.\r\n")
                            continue

                        if cmd in self.commands:
                            self.commands[cmd](self,client_socket, client_state, args)
                        else:
                            client_socket.send(b"502 Command not implemented.\r\n")

                except Exception as e:
                    print(f"Error: {e}")
                    break

            client_socket.close()

                
def permissionsGet(self, path):
    """
    Retrieve the permission string for a given file or directory path.
    Args:
        path (Path): The path to the file or directory for which to retrieve permissions.
    Returns:
        str: A string representing the permissions of the file or directory in the format 'rwxrwxrwx',
             where 'r' stands for read, 'w' stands for write, 'x' stands for execute, and '-' indicates
             the absence of a permission.
    """
    
    import stat
    mode = path.stat().st_mode
    permissions = {
        stat.S_IRUSR: 'r', stat.S_IWUSR: 'w', stat.S_IXUSR: 'x',
        stat.S_IRGRP: 'r', stat.S_IWGRP: 'w', stat.S_IXGRP: 'x',
        stat.S_IROTH: 'r', stat.S_IWOTH: 'w', stat.S_IXOTH: 'x'
    }
    perm_str = ''
    for mask, char in permissions.items():
        perm_str += char if mode & mask else '-'
    return perm_str


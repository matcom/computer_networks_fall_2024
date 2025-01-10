import socket
import os

# Configuración inicial
FTP_SERVER_ADDR = '127.0.0.1'       # Dirección del servidor
FTP_CONTROL_PORT = 21               # Puerto del servidor FTP para manejar sesiones. Este valor no cambia
FTP_DATA_PORT = 20                  # Puerto del servidor FTP para enviar y recibir datos
BUFFER_SIZE = 1024
TYPE = None

# Funciones -------------------------------------------------------------------------------------------------------------------

def response(socket):
    response = ''
    while True:
        data = socket.recv(BUFFER_SIZE).decode
        response += data
        if data.endswith('\r\n') or len(data) < BUFFER_SIZE:
            break
    return response

def client_connects_to_server(socket):
    socket.connect((FTP_SERVER_ADDR, FTP_CONTROL_PORT))
    return response(socket)

def send(socket, message):
    socket.sendall(f"{message}\r\n".encode())
    return response(socket)

def default_login(socket):
    send(socket, f"USER anonymous")
    response = send(socket, "PASS anonymous")

    if "230" in response: 
        print("Autenticado como usuario anónimo.")
        return response
    else:
        return (f"Error de autenticación: {response}")

def client_login(socket):
    username = input("Ingrese el nombre de usuario: ")
    if username == "":
        return default_login()
    
    send(socket, f"USER {username}")
    password = getpass.getpass("Ingrese la contraseña: ")
    response = send(socket, f"PASS {password}")

    req = input("Requiere una cuenta específica?   s -> SI    [otra tecla] -> NO: ")
    if req == "s" or req == "S":
        account = input("Ingrese su cuenta: ")
        acct_response = send(socket, f"ACCT {account}") 
        return acct_response

    elif "230" in response: 
        return response
    else:
        return (f"Error de autenticación: {response}")

def argument_handler(min_required_args, max_required_args, given_args):
    if min_required_args>given_args:
        if min_required_args==max_required_args:
            return f"504: Este comando requiere {min_required_args} argumentos, sin embargo {given_args} fueron recibidos."
        else:
            return f"504: Este comando requiere al menos {min_required_args} argumentos, sin embargo {given_args} fueron recibidos."
    elif max_required_args<given_args:
        return f"504: Este comando recibió {given_args-max_required_args} argumentos innecesarios."
    else:
        return "200"


# Funciones para manejar comandos ---------------------------------------------------------------------------------------------

# Control de acceso:
def cmd_USER(socket, *args):
    """Comando usado para autenticarse en el servidor"""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    if response == "200":
        return send(socket, f'USER {args[0]}')
    else:
        return response

def cmd_PASS(socket, *args):
    """Comando usado para introducir la contraseña en el servidor"""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    if response == "200":
        return send(socket, f'PASS {args[0]}')
    else:
        return response

def cmd_ACCT(socket, *args):
    """Comando usado para pasar al servidor información adicional de la cuenta"""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    if response == "200":
        return send(socket, f'ACCT {args[0]}')
    else:
        return response

def cmd_SMNT(socket, *args):
    """Monta un sistema de archivos remoto en el servidor FTP."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    if response == "200":
        return send(socket, f'SMNT {args[0]}')
    else:
        return response

def cmd_REIN(socket, *args):
    """Reinicia la sesión FTP actual."""
    args_len = len(args)
    response = argument_handler(0,0,args_len)
    if response == "200":
        return send(socket, f'REIN')
    else:
        return response

def cmd_QUIT(socket, *args):
    """Cierra la sesión y termina la ejecución del cliente"""
    args_len = len(args)
    response = argument_handler(0,0,args_len)
    if response == "200":
        response = send(socket, f'QUIT')
        if not socket is None:
            socket.close()
    return response

# Navegación:
def cmd_PWD(socket, *args):
    """Muestra el directorio de trabajo actual."""
    args_len = len(args)
    response = argument_handler(0,0,args_len)
    if response == "200":
        return send(socket, f'PWD')
    else:
        return response

def cmd_CWD(socket, *args):
    """Cambia el directorio actual al especificado."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    if response == "200":
        return send(socket, f'CWD {args[0]}')
    else:
        return response

def cmd_CDUP(socket, *args):
    """Cambia al directorio padre del directorio de trabajo actual."""
    args_len = len(args)
    response = argument_handler(0,0,args_len)
    if response == "200":
        return send(socket, f'CDUP')
    else:
        return response

def cmd_MKD(socket, *args):
    """Crea un nuevo directorio con el nombre especificado."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    if response == "200":
        return send(socket, f'MKD {args[0]}')
    else:
        return response

def cmd_RMD(socket, *args):
    """Elimina el directorio especificado."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    if response == "200":
        return send(socket, f'RMD {args[0]}')
    else:
        return response

# Transferencia de archivos:
def cmd_DELE(socket, *args):
    """Elimina el directorio especificado."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    if response == "200":
        return send(socket, f'DELE {args[0]}')
    else:
        return response

def cmd_STOR(socket, *args):
    pass

def cmd_APPE(socket, *args):
    pass

def cmd_DELE(socket, *args):
    pass

def cmd_LIST(socket, *args):
    pass

def cmd_NLST(socket, *args):
    pass

def cmd_ABOR(socket, *args):
    """Cancela el comando actual en el servidor FTP."""
    args_len = len(args)
    response = argument_handler(0,0,args_len)
    if response == "200":
        return send(socket, f'ABOR')
    else:
        return response

# Configuración de transferencia:
def cmd_TYPE(socket, *args):
    pass

def cmd_MODE(socket, *args):
    pass

def cmd_STRU(socket, *args):
    pass

# Control de conexión:
def cmd_PORT(socket, *args):
    pass

def cmd_PASV(socket, *args):
    pass

# Información del sistema:
def cmd_SYST(socket, *args):
    """Solicita información del sistema operativo del servidor FTP."""
    args_len = len(args)
    response = argument_handler(0,0,args_len)
    if response == "200":
        return send(socket, f'SYST')
    else:
        return response

def cmd_STAT(socket, *args):
    """Solicita el estado del servidor FTP o de un archivo específico."""
    args_len = len(args)
    response = argument_handler(0,1,args_len)
    if response == "200":
        if args_len==0:
            return send(socket, f'STAT')
        else:
            return send(socket, f'STAT {args[0]}')
    else:
        return response

def cmd_HELP(socket, *args):
    """Solicita ayuda sobre un comando específico o sobre el servicio FTP en general."""
    args_len = len(args)
    response = argument_handler(0,1,args_len)
    if response == "200":
        if args_len==0:
            print(send(socket, f'HELP'))
        else:
            print(send(socket, f'HELP {args[0]}'))
        return response(socket)
    else:
        return response

# Control de archivos:
def cmd_RNFR(socket, *args):
    """Inicia el proceso de renombrar un archivo en el servidor FTP."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    if response == "200":
        return send(socket, f'RNFR {args[0]}')
    else:
        return response

def cmd_RNTO(socket, *args):
    """Completa el proceso de renombrar un archivo en el servidor FTP."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    if response == "200":
        return send(socket, f'RNTO {args[0]}')
    else:
        return response

# Otros comandos:
def cmd_NOOP(socket, *args):
    """Envía un comando NOOP al servidor FTP, no es muy útil excepto si quieres mantener la conexión activa."""
    args_len = len(args)
    response = argument_handler(0,0,args_len)
    if response == "200":
        return send(socket, f'NOOP')
    else:
        return response

def cmd_STOU(socket, *args):
    pass

def cmd_ALLO(socket, *args):
    """Indica al servidor FTP que el cliente está listo para recibir datos."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    if response == "200":
        return send(socket, f'ALLO {args[0]}')
    else:
        return response

def cmd_REST(socket, *args):
    """Especifica un punto de inicio para la transferencia de datos."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    if response == "200":
        return send(socket, f'REST {args[0]}')
    else:
        return response

def cmd_SITE(socket, *args):
    """Envía un comando específico del sitio al servidor FTP."""
    args_len = len(args)
    response = argument_handler(1,1,args_len)
    if response == "200":
        return send(socket, f'SITE {args[0]}')
    else:
        return response

# Ejecución principal del cliente ---------------------------------------------------------------------------------------------

# Conexión inicial
FTP_SERVER_ADDR = input("Ingrese la dirección IP del servidor FTP: ")
socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    print(client_connects_to_server(socket))
except Exception as e:
    print(f"Error al conectar con el servidor: {e}")
    exit()

# Autenticación de usuario
while True:
    response = client_login(socket)
    print(response)
    if "230" in response:
        break
    else:
        print("Inténtelo de nuevo.")

# Ejecución de comandos del cliente
while True:
    try:
        user_input = input("=> ")
        command_parts = user_input.strip().split(" ")
        command = command_parts[0].lower()
        args = command_parts[1:]

        if command == 'user':
            print(cmd_USER(socket, *args))
        elif command == 'pass':
            print(cmd_PASS(socket, *args))
        elif command == 'acct':
            print(cmd_ACCT(socket, *args))
        elif command == 'smnt':
            print(cmd_SMNT(socket, *args))
        elif command == 'rein':
            print(cmd_REIN(socket, *args))
        elif command == 'quit':
            print(cmd_QUIT(socket, *args))
            break #Revisar si es necesario el break
        elif command == 'pwd':
            print(cmd_PWD(socket, *args))
        elif command == 'cwd':
            print(cmd_CWD(socket, *args))
        elif command == 'cdup':
            print(cmd_CDUP(socket, *args))
        elif command == 'mkd':
            print(cmd_MKD(socket, *args))
        elif command == 'rmd':
            print(cmd_RMD(socket, *args))
        elif command == 'retr':
            print(cmd_RETR(socket, *args))
        elif command == 'stor':
            print(cmd_STOR(socket, *args))
        elif command == 'appe':
            print(cmd_APPE(socket, *args))
        elif command == 'dele':
            print(cmd_DELE(socket, *args))
        elif command == 'list':
            print(cmd_LIST(socket, *args))
        elif command == 'nlst':
            print(cmd_NLST(socket, *args))
        elif command == 'abor':
            print(cmd_ABOR(socket, *args))
        elif command == 'type':
            print(cmd_TYPE(socket, *args))
        elif command == 'mode':
            print(cmd_MODE(socket, *args))
        elif command == 'stru':
            print(cmd_STRU(socket, *args))
        elif command == 'port':
            print(cmd_PORT(socket, *args))
        elif command == 'pasv':
            print(cmd_PASV(socket, *args))
        elif command == 'syst':
            print(cmd_SYST(socket, *args))
        elif command == 'stat':
            print(cmd_STAT(socket, *args))
        elif command == 'help':
            print(cmd_HELP(socket, *args))
        elif command == 'rnfr':
            print(cmd_RNFR(socket, *args))
        elif command == 'rnto':
            print(cmd_RNTO(socket, *args))
        elif command == 'noop':
            print(cmd_NOOP(socket, *args))
        elif command == 'stou':
            print(cmd_STOU(socket, *args))
        elif command == 'allo':
            print(cmd_ALLO(socket, *args))
        elif command == 'rest':
            print(cmd_REST(socket, *args))
        elif command == 'site':
            print(cmd_SITE(socket, *args))

        else:
            print("502: Comando no reconocido, por favor intente de nuevo.")

    except Exception as e:
        print(f"Error: {e}")
    
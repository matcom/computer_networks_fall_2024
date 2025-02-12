import argparse
import socket

from client_connection import connection
from response import response
from utils import log, from_json, to_json

def check_connection(host, port):
    conn = connection(host, port)
    
    success = conn.connect()
    
    if success:
        print('220 Welcome to the FTP server.')
        return conn, '220'
    else:
        return None, '500'
    
def authenticate(conn: connection, user, password):
    # Enviar credenciales de usuario
    resp = conn.send(f'USER {user}\r\n'.encode())
    data = {
        'status_code': resp.decode().split(' ')[0],
        'message': ' '.join(resp.decode().split(' ')[1:])
    }
    
    print(data)
    
    rsp = response(data['status_code'], data['message'])
    
    if(rsp.status_code == '331'):
        resp = conn.send(f'PASS {password}\r\n'.encode())
        data = {
            'status_code': resp.decode().split(' ')[0],
            'message': ' '.join(resp.decode().split(' ')[1:])
        }
        
        print(data)
        
        rsp = response(data['status_code'], data['message'])
        
        if(rsp.status_code == '230'):
            return True
        
    return False

def handle_command_list(conn: connection):
    resp = conn.send(b'LIST\r\n')
    
    data = {
        'status_code': resp.decode().split(' ')[0],
        'message': ' '.join(resp.decode().split(' ')[1:])
    }
    
    print(data)
        
def handle_command_pwd(conn: connection):
    resp = conn.send(b'PWD\r\n')
    
    data = {
        'status_code': resp.decode().split(' ')[0],
        'message': ' '.join(resp.decode().split(' ')[1:])
    }
    
    print(data)
        
def handle_command_cwd(conn: connection, dirname: str):
    resp = conn.send(f'CWD {dirname}\r\n'.encode())
    
    data = {
        'status_code': resp.decode().split(' ')[0],
        'message': ' '.join(resp.decode().split(' ')[1:])
    }
    
    print(data)
        
def handle_command_retr(conn: connection, filename: str):
    resp = conn.send(f'PASV\r\n'.encode())
    
    status_code = resp.decode().split(' ')[0]
    
    message, addr_part = resp.decode().split(' ', 1)[1].strip().split('(', 1)
    nums = addr_part.rstrip(').\r\n').split(',')
    ip = '.'.join(nums[:4])
    port = int(nums[4]) * 256 + int(nums[5])
    data = {
        'status_code': status_code,
        'message': message,
        'ip': ip,
        'port': port
    }
    
    print(data)
    
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.connect((data['ip'], data['port']))
    
    resp = conn.send(f'RETR {filename}\r\n'.encode())
    
    data = {
        'status_code': resp.decode().split(' ')[0],
        'message': ' '.join(resp.decode().split(' ')[1:])
    }
    
    print(data)
    
    file = open(filename, 'wb')
    while True:
        data = data_socket.recv(1024)
        if not data:
            break
        file.write(data)
    file.close()
    
    data_socket.close()
    
    resp = conn.client_socket.recv(1024)
    
    data = {
        'status_code': resp.decode().split(' ')[0],
        'message': ' '.join(resp.decode().split(' ')[1:])
    }
    
    print(data)
        
def handle_command_stor(conn : connection, filepath: str, filename: str):
    resp = conn.send(f'PASV\r\n'.encode())
    
    status_code = resp.decode().split(' ')[0]
    
    message, addr_part = resp.decode().split(' ', 1)[1].strip().split('(', 1)
    nums = addr_part.rstrip(').\r\n').split(',')
    ip = '.'.join(nums[:4])
    port = int(nums[4]) * 256 + int(nums[5])
    data = {
        'status_code': status_code,
        'message': message,
        'ip': ip,
        'port': port
    }
    
    print(data)
    
    data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    data_socket.connect((data['ip'], data['port']))
    
    resp = conn.send(f'RETR {filename}\r\n'.encode())
    
    data = {
        'status_code': resp.decode().split(' ')[0],
        'message': ' '.join(resp.decode().split(' ')[1:])
    }
    
    print(data)
    
    file = open(filepath, 'rb')
    
    data_socket.sendfile(file)
    
    file.close()
    
    data_socket.close()
    
    resp = conn.client_socket.recv(1024)
    
    data = {
        'status_code': resp.decode().split(' ')[0],
        'message': ' '.join(resp.decode().split(' ')[1:])
    }
    
    print(data)
        
def handle_command_rnfr(conn: connection, old_filename: str, new_filename: str):
    resp = conn.send(f'RNFR {old_filename}\r\n'.encode())
    
    data = {
        'status_code': resp.decode().split(' ')[0],
        'message': ' '.join(resp.decode().split(' ')[1:])
    }
    
    print(data)
    
    rsp = response(data['status_code'], data['message'])
    
    if(rsp.status_code == '350'):
        resp = conn.send(f'RNTO {new_filename}\r\n'.encode())
        
        data = {
            'status_code': resp.decode().split(' ')[0],
            'message': ' '.join(resp.decode().split(' ')[1:])
        }
        
        print(data)
        
def handle_command_dele(conn: connection, filename: str):
    resp = conn.send(f'DELE {filename}\r\n'.encode())
    
    data = {
        'status_code': resp.decode().split(' ')[0],
        'message': ' '.join(resp.decode().split(' ')[1:])
    }
    
    print(data)
        
def handle_command_mkd(conn: connection, dirname: str):
    resp = conn.send('MKD {dirname}\r\n'.encode())
    
    data = {
        'status_code': resp.decode().split(' ')[0],
        'message': ' '.join(resp.decode().split(' ')[1:])
    }
    
    print(data)
        
def handle_command_rmd(conn: connection, dirname: str):
    resp = conn.send('RMD {dirname}\r\n'.encode())
    
    data = {
        'status_code': resp.decode().split(' ')[0],
        'message': ' '.join(resp.decode().split(' ')[1:])
    }
    
    print(data)
        
def close_connection(conn: connection):
    log('Closing connection...')
    resp = conn.send('QUIT\r\n'.encode())
    
    data = {
        'status_code': resp.decode().split(' ')[0],
        'message': ' '.join(resp.decode().split(' ')[1:])
    }
    
    print(data)

def handle_command(conn: connection, command, arg1, arg2):
    if command == 'LIST':
        handle_command_list(conn)
    elif command == 'PWD':
        handle_command_pwd(conn)
    elif command == 'CWD':
        handle_command_cwd(conn, arg1)
    elif command == 'RETR':
        handle_command_retr(conn, arg1)
    elif command == 'STOR':
        handle_command_stor(conn, arg1, arg2)
    elif command == 'RNFR':
        handle_command_rnfr(conn, arg1, arg2)
    elif command == 'DELE':
        handle_command_dele(conn, arg1)
    elif command == 'MKD':
        handle_command_mkd(conn, arg1)
    elif command == 'RMD':
        handle_command_rmd(conn, arg1)
    elif command == 'QUIT':
        pass
    else:
        print('Invalid command.')

def main():
    parser = argparse.ArgumentParser(description='Cliente FTP: obtiene argumentos para conexión.', add_help=False)
    parser.add_argument('-h', '--host', required=True, help='Dirección del servidor FTP')
    parser.add_argument('-p', '--port', type=int, default=21, help='Puerto del servidor FTP (por defecto 21)')
    parser.add_argument('-u', '--user', required=True, help='Nombre de usuario para autenticación')
    parser.add_argument('-w', '--password', required=True, help='Contraseña para autenticación')
    parser.add_argument('-c', '--command', help='Comando a ejecutar en el servidor FTP')
    parser.add_argument('-a', '--arg1', help='Primer argumento del comando')
    parser.add_argument('-b', '--arg2', help='Segundo argumento del comando')
    
    args = parser.parse_args()
    
    conn, status = check_connection(args.host, args.port)
    
    if status != '220':
        return
 
    authenticated = authenticate(conn, args.user, args.password)
    
    if(not authenticated):
        print('Login Failed.')
        return
    
    if args.command:
        handle_command(conn, args.command, args.arg1, args.arg2)
    
    close_connection(conn)

if __name__ == '__main__':
    main()
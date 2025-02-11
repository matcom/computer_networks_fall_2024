import socket
import argparse

from client_connection import connection
from response import response
from utils import log, from_json, to_json

def check_connection(host, port):
    conn = connection(host, port)
    
    success = conn.connect()
    
    if success:
        print('220')
        return conn, '220'
    else:
        return None, '500'
    
def authenticate(conn: connection, user, password):
    # Enviar credenciales de usuario
    resp = conn.send(f'USER {user}')
    data = {
        'status_code': resp.decode().split(' ')[0],
        'message': ' '.join(resp.decode().split(' ')[1:])
    }
    
    rsp = response(data['status_code'], data['message'])
    
    log(rsp.message)
    
    if(rsp.status_code == '331'):
        resp = conn.send(f'PASS {password}')
        data = {
            'status_code': resp.decode().split(' ')[0],
            'message': ' '.join(resp.decode().split(' ')[1:])
        }
        
        rsp = response(data['status_code'], data['message'])
        
        if(rsp.status_code == '230'):
            log('Authentication successful.')
            print(rsp.status_code)
            return True
        
    return False

def handle_command_list(conn: connection):
    data = from_json(conn.send(to_json({'command': 'LIST', 'args': []})))
    rsp = response(data['status_code'], data['message'])
    
    if(rsp.status_code == '150'):
        rsp = response(data['status_code'], data['message'], data['data'])
        log(rsp.message)
        print('\n'.join(rsp.data))
    else:
        print(rsp.message)
        
def handle_command_pwd(conn: connection):
    data = from_json(conn.send(to_json({'command': 'PWD', 'args': []})))
    rsp = response(data['status_code'], data['message'], data['data'])
    
    if(rsp.status_code == '257'):
        log(rsp.message)
        print(rsp.data)
    else:
        print(rsp.message)
        
def handle_command_cwd(conn: connection, dirname: str):
    data = from_json(conn.send(to_json({'command': 'CWD', 'args': [dirname]})))
    rsp = response(data['status_code'], data['message'])
    
    if(rsp.status_code == '250'):
        log(rsp.message)
    else:
        print(rsp.message)
        
def handle_command_retr(conn: connection, filename: str):
    data = from_json(conn.send(to_json({'command': 'RETR', 'args': [filename]})))
    rsp = response(data['status_code'], data['message'])
    
    if(rsp.status_code == '150'):
        log(rsp.message)
        
        file = conn.client_socket.recv(1024)
        with open(filename, 'wb') as f:
            f.write(file)
            
        data = from_json(conn.client_socket.recv(1024))
        rsp = response(data['status_code'], data['message'])
        
        if(rsp.status_code == '226'):
            log(rsp.message)
        else:
            print(rsp.message)
    else:
        print(rsp.message)
        
def handle_command_stor(conn : connection, filepath: str, filename: str):
    data = from_json(conn.send(to_json({'command': 'STOR', 'args': [filename]})))
    rsp = response(data['status_code'], data['message'])
    
    if(rsp.status_code == '150'):
        log(rsp.message)
        
        conn.send_file(filepath)
            
        data = from_json(conn.client_socket.recv(1024))
        rsp = response(data['status_code'], data['message'])
        
        if(rsp.status_code == '226'):
            log(rsp.message)
        else:
            print(rsp.message)
    else:
        print(rsp.message)
        
def handle_command_rnfr(conn: connection, old_filename: str, new_filename: str):
    data = from_json(conn.send(to_json({'command': 'RNFR', 'args': [old_filename]})))
    rsp = response(data['status_code'], data['message'])
    
    if(rsp.status_code == '350'):
        log(rsp.message)
        
        data = from_json(conn.send(to_json({'command': 'RNTO', 'args': [new_filename]})))
        rsp = response(data['status_code'], data['message'])
        
        if(rsp.status_code == '250'):
            log(rsp.message)
        else:
            print(rsp.message)
    else:
        print(rsp.message)
        
def handle_command_dele(conn: connection, filename: str):
    data = from_json(conn.send(to_json({'command': 'DELE', 'args': [filename]})))
    rsp = response(data['status_code'], data['message'])
    
    if(rsp.status_code == '250'):
        log(rsp.message)
    else:
        print(rsp.message)
        
def handle_command_mkd(conn: connection, dirname: str):
    data = from_json(conn.send(to_json({'command': 'MKD', 'args': [dirname]})))
    rsp = response(data['status_code'], data['message'])
    
    if(rsp.status_code == '257'):
        log(rsp.message)
    else:
        print(rsp.message)
        
def handle_command_rmd(conn: connection, dirname: str):
    data = from_json(conn.send(to_json({'command': 'RMD', 'args': [dirname]})))
    rsp = response(data['status_code'], data['message'])
    
    if(rsp.status_code == '250'):
        log(rsp.message)
    else:
        print(rsp.message)
        
def close_connection(conn: connection):
    log('Closing connection...')
    conn.send(to_json({'command': 'QUIT', 'args': []}))

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
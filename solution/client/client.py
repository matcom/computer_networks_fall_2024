import socket
import argparse

from client_connection import connection
from response import response
from utils import log, from_json, to_json

def check_connection(host, port):
    conn = connection(host, port)
    
    success = conn.connect()
    
    if success:
        return conn, '220'
    else:
        return None, '500'
    
def authenticate(conn: connection, user, password):
    # Enviar credenciales de usuario
    data = from_json(conn.send(to_json({'command': 'USER', 'args': [user]})))
    
    rsp = response(data['status_code'], data['message'])
    
    log(rsp.message)
    
    if(rsp.status_code == '331'):
        data = from_json(conn.send(to_json({'command': 'PASS', 'args': [password]})))
        rsp = response(data['status_code'], data['message'])
        
        if(rsp.status_code == '230'):
            print('Authentication successful.')
            return True
        
    return False

def handle_command(conn: connection, command, arg1, arg2):
    if(command == 'LIST'):
        data = from_json(conn.send(to_json({'command': 'LIST', 'args': []})))
        rsp = response(data['status_code'], data['message'])
        
        if(rsp.status_code == '150'):
            rsp = response(data['status_code'], data['message'], data['data'])
            log(rsp.message)
            print('\n'.join(rsp.data))
        else:
            print(rsp.message)
            
    elif(command == 'RETR'):
        data = from_json(conn.send(to_json({'command': 'RETR', 'args': [arg1]})))
        rsp = response(data['status_code'], data['message'])
        
        if(rsp.status_code == '150'):
            log(rsp.message)
            
            file = conn.client_socket.recv(1024)
            with open(arg1, 'wb') as f:
                f.write(file)
                
            data = from_json(conn.client_socket.recv(1024))
            rsp = response(data['status_code'], data['message'])
            
            if(rsp.status_code == '226'):
                log(rsp.message)
            else:
                print(rsp.message)
        else:
            print(rsp.message)
    else:
        print('Invalid command.')
        
def close_connection(conn: connection):
    log('Closing connection...')
    conn.send(to_json({'command': 'QUIT', 'args': []}))

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
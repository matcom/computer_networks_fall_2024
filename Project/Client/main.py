from Client import Client

def get_connection_details():
    print("FTP Client Configuration")
    print("-----------------------")
    server_ip = input("Server IP (default: 127.0.0.1): ").strip() or '127.0.0.1'
    
    while True:
        try:
            port = input("Server Port (default: 12000): ").strip() or '12001'
            port = int(port)
            if 0 <= port <= 65535:
                return server_ip, port
            print("Error: Port must be between 0 and 65535")
        except ValueError:
            print("Error: Port must be a number")

def main():
    try:
        # Obtener detalles de conexión
        server_ip, server_port = get_connection_details()
        
        # Crear instancia del cliente
        print(f"\nConnecting to {server_ip}:{server_port}...")
        ftp_client = Client(server_ip, server_port)
        
        # Inicia el cliente
        ftp_client.ftp_client()
        
    except ConnectionRefusedError:
        print("\nError: Could not connect to server. Make sure the server is running.")
    except KeyboardInterrupt:
        print("\nClient terminated by user.")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()
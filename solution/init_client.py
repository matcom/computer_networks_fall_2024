from Client import IRCClient

def main():
    host = input("Ingrese la dirección del host: ")
    port = int(input("Ingrese la dirección del puerto: "))
    nick = input("Ingrese su nick: ")

    client = IRCClient(host, port, nick)

    client.connect()

    if client.connected:
        print(f"Conexión exitosa. Bienvenido {client.nick}!")

        # Iniciar un nuevo hilo para manejar la entrada de la consola
        client.start_receiving()

        while client.connected:
            user_input = input()
            if user_input.startswith('/'):
                parts= user_input.split(" ", 1)
                if len(parts)==1: parts.append("")
                client.handle_command(parts[0], parts[1])
                if parts[0] == '/quit':
                    client.sock.close()
                    client.connected= False
            else:
                client.send_command(user_input)

    else:
        print("No se pudo conectar al servidor. Por favor, vuelva a intentarlo más tarde.")


main()
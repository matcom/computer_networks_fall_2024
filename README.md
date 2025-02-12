# Python IRC Client

A feature-rich Internet Relay Chat (IRC) client implementation built with Python and Tkinter. This client provides a graphical user interface for connecting to IRC servers and managing multiple chat channels.
## Authors:
- Jorge Alejandro Echevarría Brunet.
- Amalia Beatriz Valiente Hinojosa.
  
  
## Features

- Graphical user interface built with Tkinter
- Support for multiple chat windows
- SSL/TLS encryption support
- Command-based interaction
- Private messaging
- Channel management
- User commands (kick, invite, whois, etc.)
- Timestamp display for messages
- Server message handling
- Configuration saving

## Components

The application is structured into several key components:

- `main.py`: Entry point of the application
- `controller.py`: Main application controller handling communication between UI and server
- `main_window.py`: Primary window implementation with server connection and command menus
- `chat_window.py`: Individual chat window implementation for channels and private messages
- `server_interface.py`: Handles server communication and message processing

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/irc-client.git
cd irc-client
```

2. Ensure you have Python 3.x installed

3. Run the application:
```bash
python main.py
```

## Usage

### Connecting to a Server

1. Launch the application
2. Click on Server → Connect in the menu
3. Enter the server details:
   - Server address
   - Port number
   - Nickname
   - Select SSL if required
4. Click Connect

### Available Commands

The client supports standard IRC commands including:

- `/JOIN #channel`: Join a channel
- `/PART #channel`: Leave a channel
- `/PRIVMSG user message`: Send a private message
- `/NOTICE user message`: Send a notice
- `/WHOIS user`: Get information about a user
- `/INVITE user #channel`: Invite a user to a channel
- `/KICK #channel user`: Kick a user from a channel

### GUI Features

- **Main Window**: Displays server messages and provides command input
- **Channel Windows**: Individual windows for each joined channel
- **Menu Options**:
  - Server connection/disconnection
  - Channel joining/parting
  - User commands (query, notice, whois, invite, kick)

## Configuration

The application saves connection settings in a `config.json` file, which stores:
- Last used server address
- Port number
- Nickname

## Security Features

- SSL/TLS support for encrypted connections
- Basic error handling for connection issues
- Safe message parsing and handling

## Technical Details

### Message Handling

The client implements proper IRC protocol message handling including:
- PRIVMSG processing
- NOTICE handling
- JOIN/PART events
- PING/PONG server checks
- Invite and kick management

### Threading

The application uses threading to:
- Maintain server connection
- Handle incoming messages
- Keep UI responsive

## Contributing

Feel free to contribute to this project by:
1. Forking the repository
2. Creating a feature branch
3. Committing your changes
4. Opening a pull request






# Repositorio para la entrega de proyectos de la asignatura de Redes de Computadoras. Otoño 2024 - 2025

### Requisitos para la ejecución de las pruebas:

1. Ajustar la variable de entorno `procotol` dentro del archivo `env.sh` al protocolo correspondiente. 

2. Modificar el archivo `run.sh` con respecto a la ejecución de la solución propuesta.

### Ejecución de los tests:

1. En cada fork del proyecto principal, en el apartado de `actions` se puede ejecutar de forma manual la verificación del código propuesto.

2. Abrir un `pull request` en el repo de la asignatura a partir de la propuesta con la solución.

### Descripción general del funcionamineto de las pruebas:

Todas las pruebas siguen un modelo de ejecución simple. Cada comprobación ejecuta un llamado al scrip `run.sh` contenido en la raíz del proyecto, inyectando los parametros correspondientes.

La forma de comprobación es similar a todos los protocolos y se requiere que el ejecutable provisto al script `run.sh` sea capaz de, en cada llamado, invocar el método o argumento provisto y terminar la comunicación tras la ejecución satisfactoria del metodo o funcionalidad provista.

### Argumentos provistos por protocolo:

#### HTTP:
1. -m method. Ej. `GET`
2. -u url. Ej `http://localhost:4333/example`
3. -h header. Ej `{}` o `{"User-Agent": "device"}`
4. -d data. Ej `Body content`

#### SMTP:
1. -p port. Ej. `25`
2. -u host. Ej `127.0.0.1`
3. -f from_mail. Ej. `user1@uh.cu`
4. -f to_mail. Ej. `["user2@uh.cu", "user3@uh.cu"]`
5. -s subject. Ej `"Email for testing purposes"`
6. -b body. Ej `"Body content"`
7. -h header. Ej `{}` o ```{"CC": "cc@examplecom"}```

#### FTP:
1. -p port. Ej. `21`
2. -h host. Ej `127.0.0.1`
3. -u user. Ej. `user`
4. -w pass. Ej. `pass`
5. -c command. Ej `STOR`
6. -a first argument. Ej `"tests/ftp/new.txt"`
7. -b second argument. Ej `"new.txt"`

#### IRC
1. -p port. Ej. `8080`
2. -H host. Ej `127.0.0.1`
3. -n nick. Ej. `TestUser1`
4. -c command. Ej `/nick`
5. -a argument. Ej `"NewNick"`

### Comportamiento de la salida esperada por cada protocolo:

1. ``HTTP``: Json con formato ```{"status": 200, "body": "server output"}```

2. ``SMTP``: Json con formato ```{"status_code": 333, "message": "server output"}```

3. ``FTP``: Salida Unificada de cada interacción con el servidor.

4. ``IRC``:  Salida Unificada de cada interacción con el servidor.

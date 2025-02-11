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


import threading
import logging
import re
from dataclasses import dataclass, field
from typing import  Optional
from typing import Dict
from typing import List
from typing import Set
import socket
from datetime import datetime

# RFC 2812 Message Parser and Generator
class IRCMessage:
    """
    Implements RFC 2812 message parsing and generation
    Format: [:prefix] command parameters[:trailing]
    """
    def __init__(self, raw: str = None):
        self.prefix: Optional[str] = None
        self.command: str = ""
        self.parameters: List[str] = []
        self.trailing: Optional[str] = None
        
        if raw:
            self.parse(raw)
    
    def parse(self, message: str) -> None:
        """Parse raw IRC message according to RFC 2812"""
        if not message:
            return

        # Remove line endings
        message = message.strip('\r\n')
        
        # Handle prefix
        if message.startswith(':'):
            prefix_end = message.find(' ')
            self.prefix = message[1:prefix_end]
            message = message[prefix_end + 1:]
        
        # Split into parts
        parts = message.split(' ')
        
        # Extract command
        self.command = parts[0].upper()
        
        # Handle parameters and trailing
        params = parts[1:]
        for i, param in enumerate(params):
            if param.startswith(':'):
                self.trailing = ' '.join(params[i:])[1:]
                params = params[:i]
                break
        self.parameters = params

    def to_string(self) -> str:
        """Convert message to raw IRC format"""
        parts = []
        
        if self.prefix:
            parts.append(f":{self.prefix}")
            
        parts.append(self.command)
        
        if self.parameters:
            parts.extend(self.parameters)
            
        if self.trailing:
            parts.append(f":{self.trailing}")
            
        return ' '.join(parts) + '\r\n'

# RFC 2812 Numeric Replies
class IRCNumerics:
    """RFC 2812 numeric replies"""
    RPL_WELCOME = "001"
    RPL_YOURHOST = "002"
    RPL_CREATED = "003"
    RPL_MYINFO = "004"
    RPL_TOPIC = "332"
    RPL_NAMREPLY = "353"
    RPL_ENDOFNAMES = "366"
    
    ERR_NOSUCHNICK = "401"
    ERR_NOSUCHCHANNEL = "403"
    ERR_CANNOTSENDTOCHAN = "404"
    ERR_ERRONEUSNICKNAME = "432"
    ERR_NICKNAMEINUSE = "433"
    ERR_NEEDMOREPARAMS = "461"

@dataclass
class IRCUser:
    """Represents an IRC user with RFC 2812 properties"""
    nickname: str
    username: str = ""
    hostname: str = ""
    realname: str = ""
    socket: Optional['socket.socket']  = None
    channels: Set[str] = field(default_factory=set)  # Corrección aquí
    modes: Set[str] = field(default_factory=set)  # Corrección aquí   

    def __post_init__(self):
        if self.channels is None:
            self.channels = set()
        if self.modes is None:
            self.modes = set()
    
    @property
    def prefix(self) -> str:
        """Generate user prefix according to RFC 2812"""
        return f"{self.nickname}!{self.username}@{self.hostname}"

class IRCChannel:
    """Implements RFC 2812 channel functionality"""
    def __init__(self, name: str):
        self.name = name
        self.topic: str = ""
        self.modes: Set[str] = set()
        self.users: Dict[str, Set[str]] = {}  # nickname -> modes
        self.bans: List[str] = []
        
    def add_user(self, user: IRCUser, modes: Set[str] = None):
        """Add user to channel with optional modes"""
        self.users[user.nickname] = modes or set()
        
    def remove_user(self, nickname: str):
        """Remove user from channel"""
        if nickname in self.users:
            del self.users[nickname]
            
    def has_user(self, nickname: str) -> bool:
        """Check if user is in channel"""
        return nickname in self.users
        
    def get_user_modes(self, nickname: str) -> Set[str]:
        """Get user's modes in this channel"""
        return self.users.get(nickname, set())

class IRCServer:
    """RFC 2812 compliant IRC server implementation"""
    def __init__(self, host='localhost', port=6667):
        self.host = host
        self.port = port
        self.creation_time = datetime.now()
        self.server_name = "PythonIRC"
        self.version = "1.0"
        self.available_user_modes = set('iwso')
        self.available_channel_modes = set('opsitnm')
        
        self.users: Dict[str, IRCUser] = {}
        self.channels: Dict[str, IRCChannel] = {}
        
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('IRCServer')

    def start(self):
        """Start the IRC server"""
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)
        self.logger.info(f"Server started on {self.host}:{self.port}")
        
        while True:
            client_socket, address = self.socket.accept()
            client_thread = threading.Thread(
                target=self.handle_client,
                args=(client_socket, address)
            )
            client_thread.daemon = True
            client_thread.start()

    def handle_client(self, client_socket: socket.socket, address):
        """Handle client connection according to RFC 2812"""
        user = None
        
        try:
            while True:
                data = client_socket.recv(1024).decode('utf-8', 'ignore')
                if not data:
                    break
                    
                for line in data.split('\n'):
                    if not line.strip():
                        continue
                        
                    message = IRCMessage(line)
                    
                    if message.command == 'NICK':
                        self.handle_nick(message, client_socket, user)
                    elif message.command == 'USER':
                        self.handle_user(message, client_socket, user)
                    elif message.command == 'JOIN':
                        self.handle_join(message, user)
                    elif message.command == 'PRIVMSG':
                        self.handle_privmsg(message, user)
                    elif message.command == 'PART':
                        self.handle_part(message, user)
                    elif message.command == 'QUIT':
                        self.handle_quit(message, user)
                    # Add more command handlers here
                    
        except Exception as e:
            self.logger.error(f"Error handling client: {e}")
        finally:
            if user:
                self.remove_user(user)
            client_socket.close()

    def handle_nick(self, message: IRCMessage, socket: socket.socket, user: Optional[IRCUser]):
        """Handle NICK command"""
        if len(message.parameters) < 1:
            self.send_numeric(socket, IRCNumerics.ERR_NEEDMOREPARAMS, "NICK :Not enough parameters")
            return
            
        nickname = message.parameters[0]
        
        # Validate nickname
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9\-_]{0,8}$', nickname):
            self.send_numeric(socket, IRCNumerics.ERR_ERRONEUSNICKNAME, f"{nickname} :Erroneous nickname")
            return
            
        # Check if nickname is in use
        if nickname in self.users:
            self.send_numeric(socket, IRCNumerics.ERR_NICKNAMEINUSE, f"{nickname} :Nickname is already in use")
            return
            
        if user:
            # Nickname change
            old_nickname = user.nickname
            user.nickname = nickname
            self.users[nickname] = user
            del self.users[old_nickname]
            self.broadcast_to_all(f":{old_nickname} NICK {nickname}")
        else:
            # New user
            user = IRCUser(nickname=nickname, socket=socket)
            self.users[nickname] = user

    def handle_user(self, message: IRCMessage, socket: socket.socket, user: IRCUser):
        """Handle USER command"""
        if len(message.parameters) < 4:
            self.send_numeric(socket, IRCNumerics.ERR_NEEDMOREPARAMS, "USER :Not enough parameters")
            return
            
        if not user:
            return
            
        user.username = message.parameters[0]
        user.realname = message.trailing or message.parameters[3]
        user.hostname = socket.getpeername()[0]
        
        # Send welcome messages
        self.send_numeric(socket, IRCNumerics.RPL_WELCOME, f":Welcome to the Internet Relay Network {user.prefix}")
        self.send_numeric(socket, IRCNumerics.RPL_YOURHOST, f":Your host is {self.server_name}, running version {self.version}")
        self.send_numeric(socket, IRCNumerics.RPL_CREATED, f":This server was created {self.creation_time}")
        self.send_numeric(socket, IRCNumerics.RPL_MYINFO, f"{self.server_name} {self.version} {self.available_user_modes} {self.available_channel_modes}")

    def handle_join(self, message: IRCMessage, user: IRCUser):
        """Handle JOIN command"""
        if not user or len(message.parameters) < 1:
            return
            
        channels = message.parameters[0].split(',')
        
        for channel_name in channels:
            if not channel_name.startswith('#'):
                channel_name = f"#{channel_name}"
                
            if channel_name not in self.channels:
                channel = IRCChannel(channel_name)
                self.channels[channel_name] = channel
            else:
                channel = self.channels[channel_name]
                
            if user.nickname not in channel.users:
                channel.add_user(user)
                user.channels.add(channel_name)
                
                # Broadcast join to channel
                self.broadcast_to_channel(channel_name, f":{user.prefix} JOIN {channel_name}")
                
                # Send channel topic
                if channel.topic:
                    self.send_numeric(user.socket, IRCNumerics.RPL_TOPIC, f"{channel_name} :{channel.topic}")
                    
                # Send names list
                self.send_names_list(user, channel)

    def handle_privmsg(self, message: IRCMessage, user: IRCUser):
        """Handle PRIVMSG command"""
        if not user or len(message.parameters) < 1 or not message.trailing:
            return
            
        target = message.parameters[0]
        
        if target.startswith('#'):
            # Channel message
            if target in self.channels:
                channel = self.channels[target]
                if user.nickname in channel.users:
                    self.broadcast_to_channel(
                        target,
                        f":{user.prefix} PRIVMSG {target} :{message.trailing}",
                        exclude={user.nickname}
                    )
        else:
            # Private message
            if target in self.users:
                target_user = self.users[target]
                self.send_message(
                    target_user.socket,
                    f":{user.prefix} PRIVMSG {target} :{message.trailing}"
                )

    def send_numeric(self, socket: socket.socket, numeric: str, message: str):
        """Send numeric reply"""
        self.send_message(socket, f":{self.server_name} {numeric} {message}")

    def send_message(self, socket: socket.socket, message: str):
        """Send raw message to socket"""
        try:
            socket.send(f"{message}\r\n".encode('utf-8'))
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")

    def broadcast_to_channel(self, channel: str, message: str, exclude: Set[str] = None):
        """Broadcast message to channel users"""
        if channel not in self.channels:
            return
            
        exclude = exclude or set()
        
        for nickname in self.channels[channel].users:
            if nickname not in exclude and nickname in self.users:
                self.send_message(self.users[nickname].socket, message)

    def broadcast_to_all(self, message: str, exclude: Set[str] = None):
        """Broadcast message to all users"""
        exclude = exclude or set()
        
        for nickname, user in self.users.items():
            if nickname not in exclude:
                self.send_message(user.socket, message)

    def remove_user(self, user: IRCUser):
        """Remove user from server"""
        # Part from all channels
        for channel_name in user.channels.copy():
            if channel_name in self.channels:
                channel = self.channels[channel_name]
                channel.remove_user(user.nickname)
                self.broadcast_to_channel(channel_name, f":{user.prefix} QUIT :Connection closed")

        # Remove from users list
        if user.nickname in self.users:
            del self.users[user.nickname]

if __name__ == "__main__":
    server = IRCServer()
    server.start()

import socket
import threading
import json
import queue
import logging
from typing import Callable, List, Dict
from datetime import datetime

class IRCClientMessage:
    """Handles IRC message formatting for the client"""
    def __init__(self, command: str, parameters: List[str] = None, trailing: str = None):
        self.command = command
        self.parameters = parameters or []
        self.trailing = trailing

    def to_string(self) -> str:
        """Convert to IRC protocol format"""
        parts = [self.command]
        
        if self.parameters:
            parts.extend(self.parameters)
            
        if self.trailing:
            parts.append(f":{self.trailing}")
            
        return f"{' '.join(parts)}\r\n"

class EnhancedIRCClient:
    """Enhanced IRC Client that works with RFC-compliant server"""
    def __init__(self, host='localhost', port=6667):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.nickname = None
        self.username = None
        self.realname = None
        self.channels = []
        self.connected = False
        
        # Message queue for GUI
        self.message_queue = queue.Queue()
        
        # Callbacks for different events
        self.callbacks = {
            'message': [],
            'join': [],
            'part': [],
            'nick': [],
            'error': [],
            'connect': [],
            'disconnect': []
        }
        
        self.logger = logging.getLogger('IRCClient')

    def connect(self, nickname: str, username: str = None, realname: str = None) -> bool:
        """Connect to IRC server and register"""
        try:
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # Save user information
            self.nickname = nickname
            self.username = username or nickname
            self.realname = realname or nickname
            
            # Send registration commands
            self.send_message(IRCClientMessage('NICK', [nickname]))
            self.send_message(IRCClientMessage('USER', 
                [self.username, '0', '*'],
                trailing=self.realname
            ))
            
            # Start receive thread
            self.receive_thread = threading.Thread(target=self._receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            self._trigger_callbacks('connect', None)
            return True
            
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            self._trigger_callbacks('error', str(e))
            return False

    def disconnect(self):
        """Disconnect from server"""
        if self.connected:
            self.send_message(IRCClientMessage('QUIT', trailing='Goodbye'))
            self.connected = False
            self.socket.close()
            self._trigger_callbacks('disconnect', None)

    def join_channel(self, channel: str):
        """Join an IRC channel"""
        if not channel.startswith('#'):
            channel = f"#{channel}"
            
        self.send_message(IRCClientMessage('JOIN', [channel]))
        if channel not in self.channels:
            self.channels.append(channel)

    def leave_channel(self, channel: str):
        """Leave an IRC channel"""
        if not channel.startswith('#'):
            channel = f"#{channel}"
            
        self.send_message(IRCClientMessage('PART', [channel]))
        if channel in self.channels:
            self.channels.remove(channel)

    def send_channel_message(self, channel: str, message: str):
        """Send message to channel"""
        self.send_message(IRCClientMessage('PRIVMSG', [channel], trailing=message))

    def send_private_message(self, nickname: str, message: str):
        """Send private message to user"""
        self.send_message(IRCClientMessage('PRIVMSG', [nickname], trailing=message))

    def send_message(self, message: IRCClientMessage):
        """Send raw message to server"""
        try:
            self.socket.send(message.to_string().encode('utf-8'))
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            self._trigger_callbacks('error', str(e))

    def on(self, event: str, callback: Callable):
        """Register callback for event"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)

    def _receive_messages(self):
        """Handle incoming server messages"""
        buffer = ""
        
        while self.connected:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break
                    
                buffer += data
                lines = buffer.split('\r\n')
                buffer = lines.pop()  # Keep incomplete line in buffer
                
                for line in lines:
                    self._handle_message(line)
                    
            except Exception as e:
                self.logger.error(f"Error receiving message: {e}")
                self._trigger_callbacks('error', str(e))
                break
                
        self.connected = False
        self._trigger_callbacks('disconnect', None)

    def _handle_message(self, line: str):
        """Parse and handle IRC message"""
        # Split message into parts
        if line.startswith(':'):
            prefix_end = line.find(' ')
            prefix = line[1:prefix_end]
            line = line[prefix_end + 1:].strip()
        else:
            prefix = None
            
        parts = line.split(' ')
        command = parts[0].upper()
        
        # Extract parameters and trailing
        params = []
        trailing = None
        
        for i, part in enumerate(parts[1:]):
            if part.startswith(':'):
                trailing = ' '.join(parts[i+1:])[1:]
                break
            params.append(part)
            
        # Handle different message types
        if command == 'PRIVMSG':
            self._handle_privmsg(prefix, params, trailing)
        elif command == 'JOIN':
            self._handle_join(prefix, params)
        elif command == 'PART':
            self._handle_part(prefix, params)
        elif command == 'NICK':
            self._handle_nick(prefix, params)
        elif command.isdigit():
            self._handle_numeric(command, params, trailing)
            
        # Add message to queue for GUI
        self.message_queue.put({
            'type': command.lower(),
            'prefix': prefix,
            'params': params,
            'trailing': trailing,
            'timestamp': datetime.now()
        })

    def _handle_privmsg(self, prefix, params, trailing):
        """Handle PRIVMSG command"""
        if prefix and params:
            nickname = prefix.split('!')[0]
            target = params[0]
            self._trigger_callbacks('message', {
                'from': nickname,
                'to': target,
                'message': trailing
            })

    def _handle_join(self, prefix, params):
        """Handle JOIN command"""
        if prefix and params:
            nickname = prefix.split('!')[0]
            channel = params[0]
            self._trigger_callbacks('join', {
                'user': nickname,
                'channel': channel
            })

    def _handle_part(self, prefix, params):
        """Handle PART command"""
        if prefix and params:
            nickname = prefix.split('!')[0]
            channel = params[0]
            self._trigger_callbacks('part', {
                'user': nickname,
                'channel': channel
            })

    def _handle_nick(self, prefix, params):
        """Handle NICK command"""
        if prefix and params:
            old_nick = prefix.split('!')[0]
            new_nick = params[0]
            self._trigger_callbacks('nick', {
                'old': old_nick,
                'new': new_nick
            })

    def _handle_numeric(self, numeric: str, params: List[str], trailing: str):
        """Handle numeric replies"""
        if numeric in ['001', '002', '003', '004']:  # Welcome messages
            self._trigger_callbacks('connect', trailing)
        elif numeric in ['431', '432', '433', '436']:  # Nickname errors
            self._trigger_callbacks('error', trailing)

    def _trigger_callbacks(self, event: str, data):
        """Trigger callbacks for event"""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"Error in callback: {e}")
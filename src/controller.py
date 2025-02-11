from server_interface import ServerInterface
from main_window import MainWindow
from chat_window import ChatWindow


class ClientController:
    def __init__(self):
        self.main_window = None
        self.server_interface = None
        self.chat_windows = {}
        self.user_nick = ""
        self.VALID_COMMANDS = {"PASS", "NICK", "USER","OPER", "MODE","SERVICE","QUIT","SQUIT","JOIN","PART","TOPIC","NAMES","LIST","INVITE","KICK","PRIVMSG","NOTICE","MOTD","LUSERS","VERSION","STATS","LINKS","TIME","CONNECT","TRACE","ADMIN","INFO","SERVLIST","SQUERY","WHO","WHOIS","WHOWAS","KILL","PING","PONG","ERROR"}

    def start(self):
        # Create the main window
        self.main_window = MainWindow(self)
        self.main_window.show()

    def connect_to_server(self, server, port, nickname, use_ssl):
        # Create the server interface
        self.server_interface = ServerInterface(server, port, nickname, self.handle_server_message, use_ssl)
        try: 
            self.server_interface.connect(nickname, nickname, nickname) 
            self.user_nick = nickname
        except Exception as e:
            self.main_window.display_message("Connection Error: " + str(e))

    def disconnect_from_server(self):
        self.send_message("QUIT")

    def join_channel(self, channel):
        # Create a new channel window
        self.send_message("JOIN "+ channel)
        # self.chat_windows[channel] = ChatWindow(self, channel)
        # self.chat_windows[channel].show()

    def part_channel(self, channel):
        self.send_message("PART "+ channel)

    def join_channel_async(self, channel, callback=None): 
        self.chat_windows[channel] = ChatWindow(self, channel) 
        # self.chat_windows[channel].show()
        self.main_window.window.after(0, self.chat_windows[channel].show)
        self.main_window.window.after(0, self.chat_windows[channel].display_message, "- now you are talking in "+channel)
        if callback is not None:
            callback()

    def handle_user_input(self, input, channel=None):
        if self.server_interface is None:       # send error message back
            return
        
        # Check if the input is a command
        if input.startswith("/"):
            self.handle_user_command(input)
        else:
            self.send_message(input, channel)

    def handle_user_command(self, command):
        # Split the command into the command name and arguments
        parts = command[1:].split(" ",1)
        command_name = parts[0].upper()
        command_args = parts[1] if len(parts) > 1 else ""

        if command_name not in self.VALID_COMMANDS:
            self.main_window.display_message("Invalid command: " + command)
            return 
        self.send_message(command_name + " " + command_args)
        print("handle user command: " + command)

    def send_message(self, message, channel=None):
        # Send a message to the server or a specific channel
        if channel:
            message = ("PRIVMSG {} :{}".format(channel, message))
            print(channel+" "+message)
      
        self.server_interface.send_message(message)
        
    def send_notice(self, message, target):
        # Send a specific target
        message = ("NOTICE {} :{}".format(target, message))
            
        self.server_interface.send_message(message)

    def whois_user(self, user):
        message = ("WHOIS {}".format(user))
            
        self.server_interface.send_message(message)

    def invite_user(self, user, channel):
        message = ("INVITE {} {}".format(user, channel))
            
        self.server_interface.send_message(message)

    def ban_user(self, user, channel):
        message = ("BAN {} {}".format(user, channel)) # not like this
            
        self.server_interface.send_message(message)

    def kick_user(self, user, channel):
        message = ("KICK {} {}".format(channel, user))
            
        self.server_interface.send_message(message)

    def handle_server_message(self, line): 
        if ' PRIVMSG ' in line:
            # Parse the line to determine its type and content 
            sender, channel, message = self.parse_channel_message(line)

            if channel == self.server_interface.nickname:
                channel = sender
            # Check if the channel window exists
            if channel in self.chat_windows:
                self.chat_windows[channel].display_message(message, sender)
            else:
                # Handle the case where the channel window doesn't exist
                self.join_channel_async(channel, callback=lambda: self.chat_windows[channel].display_message(message, sender))
        elif 'PING' in line:
            ping_message = line.split(":", 1)[1] 
            self.server_interface.send_message(f"PONG :{ping_message}")
        elif 'NOTICE' in line:
            msg = line.rsplit(":", 1)[1] 
            user = line.split("!", 1)[0][1:]
            formatted_msg = f"NOTICE from {user}: {msg}"
            self.main_window.display_message(formatted_msg)
        elif ' INVITE ' in line:  
            channel = line.rsplit(" ", 1)[1]
            user = line.split("!", 1)[0][1:]
            formatted_msg = f"INVITE from {user} to join {channel}"
            self.main_window.display_message(formatted_msg) 
        elif f"341 {self.user_nick}" in line:
            guest,channel = line.split(f"{self.user_nick} ", 1)[1].split(" ", 1)
            formatted_msg = f"You have invited <{guest}> to join {channel}"
            self.main_window.display_message(formatted_msg)
        elif ' JOIN ' in line: 
            user_joined = line.split("!",1)[0][1:]
            channel_name = line.split(" JOIN ", 1)[1][1:]           #wdf

            if  user_joined == self.user_nick:
                self.join_channel_async(channel_name)
            else:
                self.chat_windows[channel_name].display_message(user_joined+" joined "+channel_name)
        elif ' PART ' in line:
            channel_name = line.split(" PART ", 1)[1]
            self.remove_channel_window(channel_name)
            self.main_window.display_message("you left "+channel_name) 
        elif ' KICK ' in line:
            # Parse the KICK message
            parts = line.split(' KICK ')
            sender = parts[0].split('!')[0][1:]
            splitted_msg = parts[1].split(' ',2)
            channel, user_kicked = splitted_msg[0], splitted_msg[1]
            if user_kicked == self.user_nick:
                formatted_msg = f"<{sender}> kicked you from {channel}"
            else:
                formatted_msg = f"<{sender}> kicked <{user_kicked}> from {channel}"
            self.main_window.display_message(formatted_msg)
        else:
            # Check if the message contains the user nickname
            parts = line.split(self.user_nick, 1)
            if len(parts) > 1:
                # Remove the first ':' from the second part
                message = parts[1].replace(":", "", 1)
                self.main_window.display_message(message)
            else:
                # Display the whole message if it doesn't contain the user nickname
                self.main_window.display_message(line)

    def parse_server_message(self, line):
            return 'server', line               #TO DO
    
    def parse_channel_message(self, line):
        # Channel messages contain 'PRIVMSG #'
        if 'PRIVMSG ' in line:
            parts = line.split('PRIVMSG ', 1)
            sender = parts[0].split('!')[0][1:]
            channel_message = parts[1].split(' :', 1)
            channel = channel_message[0]
            message = channel_message[1]
            return sender, channel, message
        else:
            return 'server', line
        
    def stop(self):
        # Close all channel windows
        for channel_window in self.chat_windows.values():
            channel_window.on_close()  # replace with your method to close a channel window

        # Stop the server interface
        if self.server_interface is not None:
            self.server_interface.stop()  # replace with your method to stop the server interface

    
    def remove_channel_window(self, name):
        if name in self.chat_windows:
            self.chat_windows[name].window.destroy()
            del self.chat_windows[name]
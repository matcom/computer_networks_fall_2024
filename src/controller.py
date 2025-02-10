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
    
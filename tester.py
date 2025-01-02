import subprocess
import threading
import time
from client import Client


class IRCTestClient(Client):
    def __init__(self, host, port, nick, name):
        super().__init__(host, port, nick, name)
        self.responses = []

    def connect(self):
        self.connect_to_irc_server()
        threading.Thread(target=self.receive_responses, daemon=True).start()

    def send_command(self, command):
        self.send_message(command)

    def receive_responses(self):
        buffer = ""
        while self.connected:
            try:
                info = self.socket.recv(4096)  # 4096 bytes received
                if not info:
                    continue
                buffer += info.decode('utf-8', errors='replace')
                while "\r\n" in buffer:
                    message, buffer = buffer.split("\r\n", 1)
                    self.responses.append(message)
                    print(message)
            except UnicodeDecodeError as e:
                print(f"Decoding error in receiving messages: {e}.")
            except Exception as e:
                print(f"Error receiving message: {e}.")

    def close(self):
        self.socket.close()


def evaluate_response(expected, actual):
    return expected in actual


class Test:
    def __init__(self, command, expected, args=None):
        self.command = command
        self.expected = expected
        self.args = args if args else []
        self.received = None
        self.success = False

    def run(self, client: IRCTestClient):
        # Format the command with the provided arguments
        formatted_command = self.command.format(*self.args)
        client.send_command(formatted_command)
        time.sleep(1)  # Wait for response
        self.received = client.responses.copy()
        self.success = any(evaluate_response(self.expected, response) for response in self.received)
        if not self.success:
            print(f"Expected: {self.expected}, but got: {self.received[-1]}")


def run_tests():
    # Path to the server executable
    server_executable_path = 'dist/server'

    # Run the server executable in the background
    server_process = subprocess.Popen([server_executable_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Give the server some time to start up
    time.sleep(5)

    client = IRCTestClient("localhost", 8080, "testnick", "testuser")
    client.connect()
    time.sleep(1)  # Wait for connection to establish

    tests = [
        Test("JOIN #{}", "Te has unido al canal #testchannel", ["testchannel"]),
        Test("PRIVMSG #{} {}", "Mensaje de testnick", ["testchannel", "Hello, world!"]),
        Test("PART #{}", "Has salido del canal #testchannel", ["testchannel"]),
        Test("NICK {}", "Tu nuevo apodo es testnick2", ["testnick2"]),
        Test("QUIT", "Desconectado del servidor", []),
    ]

    for test in tests:
        test.run(client)

    client.close()

    # Terminate the server process after tests are done
    server_process.terminate()

    print("\nTest Results:")
    for test in tests:
        status = "Success" if test.success else "Failed"
        print(f"Command: {test.command.split()[0]} - {status}")


if __name__ == "__main__":
    run_tests()

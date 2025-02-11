from controller import ClientController

def main():
    # Create an instance of the IRCClientController and start the application
    controller = ClientController()
    controller.start()

if __name__ == "__main__":
    main()
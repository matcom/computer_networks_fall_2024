from src.server.server import SMTPServer

if __name__ == "__main__":
    server = SMTPServer(host="localhost", port=1025)
    server.start()
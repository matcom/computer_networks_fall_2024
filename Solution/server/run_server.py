from app.ftp_server import FTPServer

if __name__ == "__main__":
    server = FTPServer('0.0.0.0', 21)
    server.start()

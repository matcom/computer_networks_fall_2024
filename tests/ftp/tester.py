import subprocess
import time
import os
from ftpclient import FTPClient


def start_ftp_server():
    """Start the FTP server in a subprocess."""
    server_process = subprocess.Popen(['dist/ftpserver'])
    time.sleep(2)  # Give the server some time to start
    return server_process


def stop_ftp_server(server_process):
    """Stop the FTP server subprocess."""
    server_process.terminate()
    server_process.wait()


def test_ftp_client():
    """Test the FTP client with basic actions."""
    ftp = FTPClient('127.0.0.1')

    # Connect to the server
    print("Connecting to server...")
    response = ftp.connect()
    print(response)

    # Login
    print("Logging in...")
    response = ftp.login('user1', 'password1')
    print(response)

    # List files in the root directory
    print("Listing files in root directory...")
    response = ftp.list_files()
    print(response)

    # Create a new directory
    print("Creating a new directory 'test_dir'...")
    response = ftp.make_directory('test_dir')
    print(response)

    # Change to the new directory
    print("Changing to 'test_dir' directory...")
    response = ftp.change_directory('test_dir')
    print(response)

    # Print working directory
    print("Printing working directory...")
    response = ftp.print_working_directory()
    print(response)

    # Upload a file
    test_file = 'test_upload.txt'
    with open(test_file, 'w') as f:
        f.write('This is a test file for upload.')
    print(f"Uploading file '{test_file}'...")
    response = ftp.store_file(test_file, test_file)
    print(response)

    # List files in the current directory
    print("Listing files in 'test_dir' directory...")
    response = ftp.list_files()
    print(response)

    # Download the file
    print(f"Downloading file '{test_file}'...")
    response = ftp.retrieve_file(test_file, f'downloaded_{test_file}')
    print(response)

    # Delete the file
    print(f"Deleting file '{test_file}'...")
    response = ftp.delete_file(test_file)
    print(response)

    # Remove the directory
    print("Removing 'test_dir' directory...")
    response = ftp.change_directory('..')
    response = ftp.remove_directory('test_dir')
    print(response)

    # Quit the session
    print("Quitting the session...")
    response = ftp.quit()
    print(response)

    # Clean up local test files
    os.remove(test_file)
    os.remove(f'downloaded_{test_file}')


if __name__ == "__main__":
    server_process = start_ftp_server()
    try:
        test_ftp_client()
    finally:
        stop_ftp_server(server_process)

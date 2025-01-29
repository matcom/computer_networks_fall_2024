import subprocess, sys

def make_test(args, expeteted_output, error_msg):
    command = f"./run.sh {args}"

    output = subprocess.run('pwd', capture_output=True, text=True)
    print(output)
    output = subprocess.run('ls', capture_output=True, text=True)
    print(output)
    output = subprocess.run('chmod +x run.sh', capture_output=True, text=True)
    print(output)
    output = subprocess.run(command, capture_output=True, text=True)

    if not all([x in output for x in expeteted_output]):
        print(error_msg)
        return False
    
    print(f"Test: {command} completed")

    return True


# initial folder structure
# /: 1. directory 2. 2.txt
# /directory: 1.txt

tests = [
    ("-h localhost -p 21 -u user -p pass", ("220","230",), "Login Failed"),
    ("-h localhost -p 21 -u user -p pass -c PWD", ("150","226",), "/ directory listing failed"),
    ("-h localhost -p 21 -u user -p pass -c CWD -a /directory", ("250",), "change directory failed"),
    ("-h localhost -p 21 -u user -p pass -c QUIT", ("221",), "exiting ftp server failed"),
    ("-h localhost -p 21 -u user -p pass -c RETR -a 2.txt" , ("150","226",), "could not retrieve 2.txt file"),
    ("-h localhost -p 21 -u user -p pass -c STOR -a tests/ftp/new.txt -b new.txt", ("150", "226",), "file new.txt upload failed"),
    ("-h localhost -p 21 -u user -p pass -c RNFR -a 2.txt -b 3.txt", ("350", "250",), "rename from 2.txt to 3.txt failed"),
    ("-h localhost -p 21 -u user -p pass -c DELE -a new.txt", ("250",), "delete new.txt failed"),
    ("-h localhost -p 21 -u user -p pass -c MKD -a directory2", ("257",), "directory directory2 creation failed"),
    ("-h localhost -p 21 -u user -p pass -c RMD -a directory2", ("250",), "directory directory2 removal failed"),
]

succeed = True

for x in tests:
    succeed = succeed and make_test(x[0],x[1],x[2])

if not succeed:
    print("Errors ocurred during tests process")
    sys.exit(1)

print("All commands executed successfully")
import sys
from client import *

def print_status(response: HTTPResponse):
    print(response)

def print_headers(response: HTTPResponse):
    for key in response.headers:
        print(f"\"{key}\":\"{response.headers[key]}\"")

def print_body(response: HTTPResponse):
    print(response.get_body_raw())

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Expected : 'app <URL>'")
        sys.exit(1)

    url = sys.argv[1]
    try:
        res = request("GET", url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"})
    except BadUrlError as e:
        print(e)
        sys.exit(1)

    # print_status(res)
    # print_headers(res)
    print_body(res)
    # Cannot visualize on my Pc yet
    # res.visualise()


import argparse
import json
import sys
from client import request, HTTPResponse

def fix_curious_design_choices(args):
    final_args = []
    merged_headers = []
    merged_data = []
    header_index = False
    data_index = False
    for i in args:
        if i == "-h":
            if data_index:
                final_args.append(" ".join(merged_data))
                merged_data = []
            data_index = False
            header_index = True
            final_args.append(i)
            continue
        elif i == "-d":
            if header_index:
                final_args.append(" ".join(merged_headers))
                merged_data = []
            data_index = True
            header_index = False
            final_args.append(i)
            continue


        if header_index:
            merged_headers.append(i)
        elif data_index:
            merged_data.append(i)
        if not header_index and not data_index:
            final_args.append(i)

    if header_index:
        final_args.append(" ".join(merged_headers))
    elif data_index:
        final_args.append(" ".join(merged_data))

    return final_args

def main(sys_args):
    # Set up argument parser
    sys_args = fix_curious_design_choices(sys_args)

    parser = argparse.ArgumentParser(description="HTTP Client CLI", add_help=False)
    parser.add_argument("-m", "--method", required=True, help="HTTP method (e.g., GET, POST)")
    parser.add_argument("-u", "--url", required=True, help="Request URL")
    parser.add_argument("-h", "--header", type=str, default="{}", help="Request headers in JSON format (e.g., '{\"User-Agent\": \"device\"}')")
    parser.add_argument("-d", "--data", type=str, default="", help="Request body data")

    # Parse arguments
    args = parser.parse_args(sys_args)

    # Prepare headers from JSON string
    try:
        headers = json.loads(args.header)
    except json.JSONDecodeError:
        print("Invalid header format. Please provide valid JSON.")
        sys.exit(1)

    # Make the HTTP request
    response: HTTPResponse = request(method=args.method, url=args.url, headers=headers, body=args.data)

    # Prepare output JSON format
    output = {
        "status": response.code,
        "body": response.get_body_raw().decode('utf-8')  # Assuming body is in bytes and needs to be decoded
    }

    # Print output as JSON
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main(sys.argv[1:])

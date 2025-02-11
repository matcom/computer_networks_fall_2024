import streamlit as st
import socket
from interface_client import HTTPClient

# Create an instance of the HTTPClient
client = HTTPClient()

# Streamlit Interface
st.title("HTTP Client with Sockets 🔌")

# HTTP method and URL selector
col1, col2 = st.columns([1, 4])
with col1:
    http_method = st.selectbox("HTTP Method", ["GET", "POST", "HEAD", "DELETE", "PATCH", "PUT"])
with col2:
    url = st.text_input("URL", "http://httpbin.org/post")

# Query parameters
with st.expander("Query Parameters"):
    raw_params = st.text_area("Query Parameters (format: key=value)", height=100)
    if raw_params:
        # Format the query parameters
        params = "&".join([line.strip() for line in raw_params.split("\n") if "=" in line])
        url += ("?" + params if "?" not in url else "&" + params)

# Custom headers
with st.expander("Headers"):
    raw_headers = st.text_area("Headers (format: Key: Value)", "Content-Type: application/json", height=100)
    headers = {}
    if raw_headers:
        # Parse the headers
        for line in raw_headers.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()

# Body for POST requests
body = ""

if http_method in ["POST", "DELETE", "PATCH", "PUT"]:  #Allow body for DELETE
    body = st.text_area("Body (plain text or JSON)", height=200, value='{\n    "key": "value"\n}')
else:
    body = None 

# Send request button
if st.button("Send Request"):     
    # Manage requests
    if http_method == "HEAD":
        status_code, response_headers, response_body = client.head(url, headers=headers)
    elif http_method == "DELETE":
        status_code, response_headers, response_body = client.delete(url, body=body, headers=headers)
    elif http_method == "PATCH":
        status_code, response_headers, response_body = client.patch(url, body=body, headers=headers)
    elif http_method == "PUT":
        status_code, response_headers, response_body = client.put(url, body=body, headers=headers)
    else:
        status_code, response_headers, response_body = client.http_request(
            method=http_method,
            url=url,
            body=body,
            headers=headers
        )
    
    st.subheader("Response")
    st.markdown(f"**Status Code:** `{status_code}`")
    
    st.subheader("Response Headers")
    st.text_area("Headers", response_headers, height=200)
    
    st.subheader("Response Body")
    # Show warning for HEAD
    if http_method == "HEAD":
        st.warning("HEAD responses don't have a body by specification")
    st.text_area("Content", response_body, height=400)
    

# Examples section
st.markdown("---")
st.info("💡 Examples:\n"
        "**GET/POST:**\n"
        "- URL: http://httpbin.org/get\n"
        "- URL: http://httpbin.org/post\n"
        "- Body example: {\n    'name': 'Ada'\n}\n\n"
        "**HEAD:**\n"
        "- URL: http://httpbin.org/headers\n\n"
        "**DELETE:**\n"
        "- URL: http://httpbin.org/delete\n"
        "- Body example: {\n    'id': 123\n}\n\n"
        "**PATCH:**\n"
        "- URL: http://httpbin.org/patch\n"
        "- Body example: {\n    'key': 'updated_value'\n}\n\n"
        "**PUT:**\n"
        "- URL: http://httpbin.org/put\n"
        "- Body example: {\n    'key': 'new_value'\n}")
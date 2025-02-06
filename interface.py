import streamlit as st
import socket
from client import HTTPClient

# Create an instance of the HTTPClient
client = HTTPClient()

# Streamlit Interface
st.title("HTTP Client with Sockets 🔌")

# HTTP method and URL selector
col1, col2 = st.columns([1, 4])
with col1:
    http_method = st.selectbox("HTTP Method", ["GET", "POST", "HEAD"])
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
if http_method == "POST":
    body = st.text_area("Body (plain text or JSON)", height=200, value='{\n    "key": "value"\n}')
else :
    body = None

# Send request button
if st.button("Send Request"):
    try:
        # Validate URL
        if not url.startswith("http://"):
            raise ValueError("Only HTTP URLs are supported (not HTTPS)")
        
        # Make the HTTP request
        status_code, response_body = client.http_request(
            method=http_method,
            url=url,
            body=body,
            headers=headers
        )
        
        # Display the response
        st.subheader("Response")
        st.markdown(f"**Status Code:** `{status_code}`")
        
        st.subheader("Response Body")
        
        if http_method == "HEAD":
            st.warning("HEAD responses don't have a body by specification")
        st.text_area("Content", response_body, height=400)
        
        
    except Exception as e:
        # Display error message
        st.error(f"Error: {str(e)}")

# Examples section
st.markdown("---")
st.info("💡 Example POST:\n"
        "- URL: http://httpbin.org/post\n"
        "- Body: {\n    'name': 'Ada',\n    'profession': 'Programmer'\n}")
import re
import json

class basic_rules : 
    def is_char(self, c: str) -> bool : 
        return 0 <= ord(c) and ord(c) <= 127
    def is_upalpha(self, c: str) -> bool : 
        return c.isupper()
    def is_loalpha(self, c: str) -> bool : 
        return c.islower()
    def is_alpha(self, c: str) -> bool :
        return self.is_upalpha(c) or self.is_loalpha(c)
    def is_digit(self, c: str) -> bool :
        return c.isdigit()
    def is_ctl(self, c: str) -> bool :
        return (0 <= ord(c) and ord(c) <= 31) or ord(c) == 127
    def is_cr(self, c: str) -> bool :
        return c == self.cr
    def is_lf(self, c: str) -> bool :
        return c == self.lf
    def is_sp(self, c: str) -> bool :
        return c == self.sp
    def is_ht(self, c: str) -> bool :
        return c == self.ht
    def is_text(self, c: str) -> bool :
        return self.is_char(c) and not self.is_ctl(c)
    def is_hex(self, c: str) -> bool :
        return self.is_digit(c) or ('A' <= c and c <= 'F') or ('a' <= c and c <= 'f')    
    def is_separator(self, c: str) -> bool :
        return c in self.separators
    cr = '\r'
    lf = '\n'
    sp = ' '
    ht = '\t'
    crlf = cr + lf
    separators = '()<>@,;:\\\"/[]?={}' + sp + ht
    
class httpMessage:
  def get_http_version(min: int, max: int):
    return "HTTP" + "/" + str(min) + '.' + str(max)
  def get_url_info(url: str):
    scheme = False
    default_port = 80
    if url.startswith("http://"):
        url = url[len("http://"):]
    elif url.startswith("https://"):
        url = url[len("https://"):]
        default_port = 443
        scheme = True 

    slash_i = url.find("/")
    if slash_i == -1:
        host_port = url
        path = "/"
    else:
        host_port = url[:slash_i]
        path = url[slash_i:]

    colon_i = host_port.find(":")
    if colon_i == -1:
        host = host_port
        port = default_port
    else:
        host = host_port[:colon_i]
        port = int(host_port[colon_i + 1:])

    return scheme, host, port, path
      

class httpRequest:
  def is_valid_method(s: str) -> bool :
    return s in ["OPTIONS", "GET", "HEAD", "POST", "PUT", "DELETE", "TRACE", "CONNECT"]
  def build_request_line(method: str, request_uri: str, http_version: str) :
    sp = basic_rules.sp
    crlf = basic_rules.crlf
    return method + sp + request_uri + sp + http_version + crlf
  def build_headers(headers_str: str) -> str :
    if not headers_str:
      return ""
    json_headers = json.loads(headers_str)
    headers = ""
    for key, value in json_headers.items():
        headers += key + ": " + value + basic_rules.crlf
    return headers
  def build_req(method: str, uri:str, headers: str = None, body: str =None):
    return httpRequest.build_request_line(method, uri, httpMessage.get_http_version(1, 1)) + httpRequest.build_headers(headers) + basic_rules.crlf + body
  def get_head_info(head: str):
    request_line, headers = head.split(basic_rules.crlf, 1)
    method, uri, http_version = request_line.split(basic_rules.sp)
    headers = headers.split(basic_rules.crlf)
    header_fields = {}
    for header in headers:
      if not header:
          continue
      key, value = re.split(r":\s+", header, 1)
      header_fields[key] = value
    return {
        "method": method,
        "uri": uri,
        "http_version": http_version,
        "headers": header_fields
    }

class httpResponse:
  def extract_head_info(head: str):
    status_line, headers = head.split(basic_rules.crlf, 1)
    headers = headers.split(basic_rules.crlf)
    header_fields = {}
    for header in headers:
        if not header:
            continue
        key, value = re.split(r":\s+", header, 1)
        header_fields[key] = value
    http_version, status_code, reason_phrase = status_line.split(basic_rules.sp, 2)
    
    return {
        "http_version": http_version,
        "status_code": int(status_code),
        "reason_phrase": reason_phrase,
        "headers": header_fields
    }
  def build_response_line(http_version: str, status_code: int, reason_phrase: str):
    sp = basic_rules.sp
    crlf = basic_rules.crlf
    return http_version + sp + str(status_code) + sp + reason_phrase + crlf
  def build_headers(status: int, body: str) -> dict:
    #TODO: add more stuff
    headers = {}
    if len(body) > 0:
      headers["Content-Length"] = len(body)
    return headers
      
  def stringify_headers(headers: dict) -> str:
    result = ""
    for key, value in headers.items():
      result += key + ": " + str(value) + basic_rules.crlf
    return result
      
  def build_res(status_code: int, reason_phrase: str, headers: str = None, body: str = None):
    return httpResponse.build_response_line(httpMessage.get_http_version(1,1), status_code, reason_phrase) + headers + basic_rules.crlf + body
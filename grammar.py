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
    separators = '()<>@,;:\\\"/[]?=\{\}' + sp + ht
    
class httpMessage:
  def get_http_version(min, max):
    return "HTTP" + "/" + min + '.' + max
  def get_host_port(url: str):
    if url.startswith("http://"):
        url = url[len("http://"):]
        default_port = 80
    elif url.startswith("https://"):
        url = url[len("https://"):]
        default_port = 443
    else:
        default_port = 80

    slash_i = url.find("/")
    if slash_i == -1:
        host_port = url
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

    return host, port
      

class httpRequest:
  def is_valid_method(s: str) -> bool :
    return s in ["OPTIONS", "GET", "HEAD", "POST", "PUT", "DELETE", "TRACE", "CONNECT"]
  def get_request_line(method: str, request_uri: str, http_version: str) :
    sp = basic_rules.sp
    crlf = basic_rules.crlf
    return method + sp + request_uri + sp + http_version + crlf
  def build(self, method: str, uri:str, headers: str = None, body: str =None):
    return self.get_request_line(method, uri, httpMessage.get_http_version(1, 1)) + headers + basic_rules.crlf + body
  
class BadUrlError(Exception):
    pass

def parse_http_url(url: str):
    def parse_http_scheme(url: str,index: int):
        isHttp: bool = False
        httpScheme = "http://"
        i = 0
        while i < len(httpScheme) and index + i < len(url):
            if url[index + i].lower() != httpScheme[i]:
                break
            i = i + 1
        if i == len(httpScheme):
            isHttp = True
        if not isHttp:
            raise BadUrlError(f"Not an http url scheme: `{url[:len(httpScheme)]}`")
        return index + i

    def parse_host(url: str,index: int):
        start_index = index
        while index < len(url) and url[index] != ':' and url[index] != '/':
            index = index + 1
        return (index,url[start_index:index])
    
    def parse_port(url: str,index: int):
        if index < len(url) and url[index] == ':':
            index = index + 1
        start_index = index
        while index < len(url) and url[index] != '/':
            index = index + 1
        port = url[start_index:index]
        if port == '':
            port = 80
        elif not port.isnumeric():
            raise BadUrlError(f"Port is not a number: `{port}`")
        return (index,int(port))
    def parse_abs_path(url: str,index: int):
        startIndex = index
        while index < len(url) and url[index] != '?':
            index = index + 1
        absPath = url[startIndex:index]
        if absPath == "":
            absPath = "/"
        return (index,absPath)
    def parse_query(url: str,index: int):
        return (index,url[index:])
    
    index = 0
    index = parse_http_scheme(url,index)
    index, host = parse_host(url,index)
    index, port = parse_port(url,index)
    index, absPath = parse_abs_path(url,index)
    index, query = parse_query(url,index)
    return (host,port,absPath,query)

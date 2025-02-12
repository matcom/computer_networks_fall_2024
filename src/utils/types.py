from typing import TypedDict, Union

class HTTPResponse(TypedDict):
    status_code: int
    headers: dict[str, str]
    body: Union[str, dict, None]
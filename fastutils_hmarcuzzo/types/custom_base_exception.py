from typing import List


class CustomBaseException(Exception):
    def __init__(self, msg: str, loc: List[str] = None, exception_type: str = None):
        self.msg = msg
        self.loc = loc
        self.type = exception_type

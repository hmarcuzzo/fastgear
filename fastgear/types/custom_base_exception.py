class CustomBaseException(Exception):
    def __init__(self, msg: str, loc: list[str] = None, _type: str = None) -> None:
        self.msg = msg
        self.loc = loc
        self.type = _type

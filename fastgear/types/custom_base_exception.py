class CustomBaseException(Exception):
    def __init__(self, msg: str, loc: list[str] | None = None, _type: str | None = None) -> None:
        if not isinstance(msg, str):
            raise TypeError("msg must be a string")
        if loc is not None and not isinstance(loc, list):
            raise TypeError("loc must be a list of strings")
        if _type is not None and not isinstance(_type, str):
            raise TypeError("type must be a string")

        self.msg = msg
        self.loc = loc
        self.type = _type

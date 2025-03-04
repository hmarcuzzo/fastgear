from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_429_TOO_MANY_REQUESTS,
)

from fastutils_hmarcuzzo.types.custom_base_exception import CustomBaseException


class BadRequestException(CustomBaseException):
    def __init__(self, msg: str, loc: list[str] = None, _type: str = "Bad Request") -> None:
        if loc is None:
            loc = []
        self.status_code = HTTP_400_BAD_REQUEST
        super().__init__(msg, loc, _type)


class UnauthorizedException(CustomBaseException):
    def __init__(self, msg: str, loc: list[str] = None, _type: str = "unauthorized") -> None:
        if loc is None:
            loc = []
        self.status_code = HTTP_401_UNAUTHORIZED
        super().__init__(msg, loc, _type)


class ForbiddenException(CustomBaseException):
    def __init__(self, msg: str, loc: list[str] = None, _type: str = "forbidden") -> None:
        if loc is None:
            loc = []
        self.status_code = HTTP_403_FORBIDDEN
        super().__init__(msg, loc, _type)


class NotFoundException(CustomBaseException):
    def __init__(self, msg: str, loc: list[str] = None, _type: str = "Not Found") -> None:
        if loc is None:
            loc = []
        self.status_code = HTTP_404_NOT_FOUND
        super().__init__(msg, loc, _type)


class UnprocessableEntityException(CustomBaseException):
    def __init__(
        self, msg: str, loc: list[str] = None, _type: str = "Unprocessable Entity",
    ) -> None:
        if loc is None:
            loc = []
        self.status_code = HTTP_422_UNPROCESSABLE_ENTITY
        super().__init__(msg, loc, _type)


class DuplicateValueException(CustomBaseException):
    def __init__(self, msg: str, loc: list[str] = None, _type: str = "Duplicate Value") -> None:
        if loc is None:
            loc = []
        self.status_code = HTTP_422_UNPROCESSABLE_ENTITY
        super().__init__(msg, loc, _type)


class RateLimitException(CustomBaseException):
    def __init__(self, msg: str, loc: list[str] = None, _type: str = "Rate Limit") -> None:
        if loc is None:
            loc = []
        self.status_code = HTTP_429_TOO_MANY_REQUESTS
        super().__init__(msg, loc, _type)


CustomHTTPExceptionType = (
    BadRequestException
    | UnauthorizedException
    | ForbiddenException
    | NotFoundException
    | UnprocessableEntityException
    | DuplicateValueException
    | RateLimitException
)

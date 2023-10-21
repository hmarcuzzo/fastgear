from typing import List

from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

from fastutils_hmarcuzzo.common.base_exception import BaseExceptionType


class BadRequestException(BaseExceptionType):
    def __init__(self, msg: str, loc: List[str] = [], exception_type: str = "Bad Request"):
        self.status_code = HTTP_400_BAD_REQUEST
        super().__init__(msg, loc, exception_type)


class UnauthorizedException(BaseExceptionType):
    def __init__(self, msg: str, loc: List[str] = [], _type: str = "unauthorized"):
        self.status_code = HTTP_401_UNAUTHORIZED
        super().__init__(msg, loc, _type)


class ForbiddenException(BaseExceptionType):
    def __init__(self, msg: str, loc: List[str] = [], _type: str = "forbidden"):
        self.status_code = HTTP_403_FORBIDDEN
        super().__init__(msg, loc, _type)


class NotFoundException(BaseExceptionType):
    def __init__(self, msg: str, loc: List[str] = [], exception_type: str = "Not Found"):
        self.status_code = HTTP_404_NOT_FOUND
        super().__init__(msg, loc, exception_type)

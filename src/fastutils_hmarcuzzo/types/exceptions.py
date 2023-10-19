from typing import List

from fastutils_hmarcuzzo.common.base_exception import BaseExceptionType
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND


class BadRequestException(BaseExceptionType):
    def __init__(self, msg: str, loc: List[str] = [], exception_type: str = "Bad Request"):
        self.status_code = HTTP_400_BAD_REQUEST
        super().__init__(msg, loc, exception_type)


class NotFoundException(BaseExceptionType):
    def __init__(self, msg: str, loc: List[str] = [], exception_type: str = "Not Found"):
        self.status_code = HTTP_404_NOT_FOUND
        super().__init__(msg, loc, exception_type)

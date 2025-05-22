import pytest
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_429_TOO_MANY_REQUESTS,
)

from fastgear.types.http_exceptions import (
    BadRequestException,
    CustomHTTPExceptionType,
    DuplicateValueException,
    ForbiddenException,
    NotFoundException,
    RateLimitException,
    UnauthorizedException,
    UnprocessableEntityException,
)
from tests.fixtures.types.http_exceptions_fixtures import (  # noqa: F401
    basic_exception_data,
    empty_message_data,
    full_exception_data,
)


@pytest.mark.describe("🧪  HTTP Exceptions")
class TestHTTPExceptions:
    @pytest.mark.it("✅  Should create exceptions with correct status codes and types")
    @pytest.mark.parametrize(
        "exception_class, status_code, default_type",  # noqa: PT006
        [
            (BadRequestException, HTTP_400_BAD_REQUEST, "Bad Request"),
            (UnauthorizedException, HTTP_401_UNAUTHORIZED, "unauthorized"),
            (ForbiddenException, HTTP_403_FORBIDDEN, "forbidden"),
            (NotFoundException, HTTP_404_NOT_FOUND, "Not Found"),
            (UnprocessableEntityException, HTTP_422_UNPROCESSABLE_ENTITY, "Unprocessable Entity"),
            (DuplicateValueException, HTTP_422_UNPROCESSABLE_ENTITY, "Duplicate Value"),
            (RateLimitException, HTTP_429_TOO_MANY_REQUESTS, "Rate Limit"),
        ],
    )
    def test_exception_creation(
        self, exception_class: type, status_code: int, default_type: str, basic_exception_data: dict
    ) -> None:
        exception = exception_class(**basic_exception_data)
        assert exception.status_code == status_code
        assert exception.msg == basic_exception_data["msg"]
        assert exception.loc == []
        assert exception.type == default_type

    @pytest.mark.it("✅  Should handle exceptions with full data")
    @pytest.mark.parametrize(
        "exception_class",  # noqa: PT006
        [
            BadRequestException,
            UnauthorizedException,
            ForbiddenException,
            NotFoundException,
            UnprocessableEntityException,
            DuplicateValueException,
            RateLimitException,
        ],
    )
    def test_exceptions_with_full_data(
        self, exception_class: type, full_exception_data: dict
    ) -> None:
        exception = exception_class(**full_exception_data)
        assert exception.msg == full_exception_data["msg"]
        assert exception.loc == full_exception_data["loc"]
        assert exception.type == full_exception_data["_type"]

    @pytest.mark.it("✅  Should handle exceptions with empty message")
    @pytest.mark.parametrize(
        "exception_class, default_type",  # noqa: PT006
        [
            (BadRequestException, "Bad Request"),
            (UnauthorizedException, "unauthorized"),
            (ForbiddenException, "forbidden"),
            (NotFoundException, "Not Found"),
            (UnprocessableEntityException, "Unprocessable Entity"),
            (DuplicateValueException, "Duplicate Value"),
            (RateLimitException, "Rate Limit"),
        ],
    )
    def test_exceptions_with_empty_message(
        self, exception_class: type, default_type: str, empty_message_data: dict
    ) -> None:
        exception = exception_class(**empty_message_data)
        assert exception.msg == ""
        assert exception.loc == []
        assert exception.type == default_type

    @pytest.mark.it("✅  Should verify CustomHTTPExceptionType union type")
    @pytest.mark.parametrize(
        "exception_class",  # noqa: PT006
        [
            BadRequestException,
            UnauthorizedException,
            ForbiddenException,
            NotFoundException,
            UnprocessableEntityException,
            DuplicateValueException,
            RateLimitException,
        ],
    )
    def test_custom_http_exception_type(self, exception_class: type) -> None:
        assert exception_class in CustomHTTPExceptionType.__args__  # type: ignore

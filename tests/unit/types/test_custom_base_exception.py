import pytest

from fastgear.types.custom_base_exception import CustomBaseException
from tests.fixtures.types.custom_base_exception_fixtures import (
    basic_exception_data,
    empty_message_data,
    full_exception_data,
)


@pytest.mark.describe("🧪  CustomBaseException")
class TestCustomBaseException:
    @pytest.mark.it("✅  Should create exception with basic data")
    def test_basic_exception(self, basic_exception_data: dict) -> None:
        exception = CustomBaseException(**basic_exception_data)

        assert exception.msg == basic_exception_data["msg"]
        assert exception.loc is None
        assert exception.type is None

    @pytest.mark.it("✅  Should create exception with full data")
    def test_full_exception(self, full_exception_data: dict) -> None:
        exception = CustomBaseException(**full_exception_data)

        assert exception.msg == full_exception_data["msg"]
        assert exception.loc == full_exception_data["loc"]
        assert exception.type == full_exception_data["_type"]

    @pytest.mark.it("✅  Should create exception with empty message")
    def test_empty_message(self, empty_message_data: dict) -> None:
        exception = CustomBaseException(**empty_message_data)

        assert exception.msg == ""
        assert exception.loc is None
        assert exception.type is None

    @pytest.mark.it("❌  Should fail when message is not provided")
    def test_missing_message(self) -> None:
        with pytest.raises(TypeError, match="missing 1 required positional argument: 'msg'"):
            CustomBaseException()

    @pytest.mark.it("❌  Should fail when message is not a string")
    def test_invalid_message_type(self) -> None:
        with pytest.raises(TypeError, match="msg must be a string"):
            CustomBaseException(msg=123)  # type: ignore

    @pytest.mark.it("❌  Should fail when location is not a list of strings")
    def test_invalid_location_type(self) -> None:
        with pytest.raises(TypeError, match="loc must be a list of strings"):
            CustomBaseException(msg="test", loc="invalid")  # type: ignore

    @pytest.mark.it("❌  Should fail when type is not a string")
    def test_invalid_type_type(self) -> None:
        with pytest.raises(TypeError, match="type must be a string"):
            CustomBaseException(msg="test", _type=123)  # type: ignore

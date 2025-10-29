from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from starlette.status import HTTP_422_UNPROCESSABLE_CONTENT

from fastgear.common.schema.exception_response_schema import (
    DetailResponseSchema,
    ExceptionResponseSchema,
)


@pytest.mark.describe("🧪  DetailResponseSchema")
class TestDetailResponseSchema:
    @pytest.mark.it("✅  Should create DetailResponseSchema with correct values and types")
    def test_create_detail_response_schema(self) -> None:
        detail = DetailResponseSchema(loc=["field"], msg="Bad value", type="value_error")

        assert isinstance(detail.loc, list)
        assert detail.loc == ["field"]
        assert isinstance(detail.msg, str)
        assert detail.msg == "Bad value"
        assert isinstance(detail.type, str)
        assert detail.type == "value_error"

    @pytest.mark.it("❌  Should raise ValidationError when fields have wrong types")
    def test_detail_schema_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            # loc must be a list[str]
            DetailResponseSchema(loc="not-a-list", msg=123, type=[])


@pytest.mark.describe("🧪  ExceptionResponseSchema")
class TestExceptionResponseSchema:
    @pytest.mark.it(
        "✅  Should create ExceptionResponseSchema with default status_code and nested detail"
    )
    def test_create_exception_response_schema_with_defaults(self) -> None:
        detail = DetailResponseSchema(loc=["a"], msg="m", type="t")
        ts = datetime.now(UTC)

        exc = ExceptionResponseSchema(
            detail=[detail],
            timestamp=ts,
            path="/x",
            method="GET",
            status_code=HTTP_422_UNPROCESSABLE_CONTENT,
        )

        # status_code is expected to be 422
        assert exc.status_code == HTTP_422_UNPROCESSABLE_CONTENT
        assert isinstance(exc.timestamp, datetime)
        assert exc.timestamp == ts
        assert exc.path == "/x"
        assert exc.method == "GET"
        assert isinstance(exc.detail, list)
        assert isinstance(exc.detail[0], DetailResponseSchema)

    @pytest.mark.it("✅  Should accept dicts for nested detail and coerce to DetailResponseSchema")
    def test_detail_accepts_dict_and_coerces(self) -> None:
        detail_dict = {"loc": ["x"], "msg": "m", "type": "t"}
        ts = datetime.now(UTC)

        exc = ExceptionResponseSchema(
            detail=[detail_dict], timestamp=ts, path="/p", method="POST", status_code=422
        )

        assert isinstance(exc.detail[0], DetailResponseSchema)
        assert exc.detail[0].loc == ["x"]

    @pytest.mark.it("❌  Should forbid extra fields when creating the model")
    def test_extra_fields_are_forbidden(self) -> None:
        detail = DetailResponseSchema(loc=["x"], msg="m", type="t")
        ts = datetime.now(UTC)

        with pytest.raises(ValidationError):
            ExceptionResponseSchema(
                detail=[detail],
                timestamp=ts,
                path="/p",
                method="POST",
                status_code=422,
                extra_field="not_allowed",
            )

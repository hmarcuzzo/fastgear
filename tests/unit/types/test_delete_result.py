from typing import Any

import pytest

from fastgear.types.delete_result import DeleteResult


@pytest.mark.describe("🧪  DeleteResult")
class TestDeleteResult:
    @pytest.mark.it("✅  Should create DeleteResult with valid data")
    def test_create_delete_result(self) -> None:
        result = DeleteResult(raw={"id": 1}, affected=1)

        assert isinstance(result, dict)
        assert result["raw"] == {"id": 1}
        assert result["affected"] == 1

    @pytest.mark.it("✅  Should create DeleteResult with zero affected rows")
    def test_create_delete_result_zero_affected(self) -> None:
        result = DeleteResult(raw={}, affected=0)

        assert isinstance(result, dict)
        assert result["raw"] == {}
        assert result["affected"] == 0

    @pytest.mark.it("✅  Should create DeleteResult with multiple affected rows")
    def test_create_delete_result_multiple_affected(self) -> None:
        result = DeleteResult(raw={"ids": [1, 2, 3]}, affected=3)

        assert isinstance(result, dict)
        assert result["raw"] == {"ids": [1, 2, 3]}
        assert result["affected"] == 3

    @pytest.mark.it("✅  Should allow any type for raw field")
    @pytest.mark.parametrize(
        "raw_value", ["string", 123, None, {"key": "value"}, [1, 2, 3], True, False, 1.5, [], {}]
    )
    def test_raw_field_accepts_any_type(self, raw_value: Any) -> None:
        result = DeleteResult(raw=raw_value, affected=1)
        assert result["raw"] == raw_value

    @pytest.mark.it("✅  Should allow any numeric value for affected field")
    @pytest.mark.parametrize("affected_value", [0, -1, 1.5, 100, -100, 0.0, -0.0, 1e10, -1e10])
    def test_affected_field_accepts_any_numeric(self, affected_value: float) -> None:
        result = DeleteResult(raw={}, affected=affected_value)
        assert result["affected"] == affected_value

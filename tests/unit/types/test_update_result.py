import pytest

from fastgear.types.update_result import UpdateResult
from tests.fixtures.types.update_result_fixtures import (  # noqa: F401
    basic_update_result,
    empty_update_result,
    full_update_result,
)


@pytest.mark.describe("🧪  UpdateResult")
class TestUpdateResult:
    @pytest.mark.it("✅  Should create UpdateResult with basic data")
    def test_basic_update_result(self, basic_update_result: dict) -> None:
        result = UpdateResult(**basic_update_result)
        assert result["raw"] == basic_update_result["raw"]
        assert result["affected"] == basic_update_result["affected"]
        assert result["generated_maps"] == basic_update_result["generated_maps"]

    @pytest.mark.it("✅  Should create UpdateResult with full data")
    def test_full_update_result(self, full_update_result: dict) -> None:
        result = UpdateResult(**full_update_result)
        assert result["raw"] == full_update_result["raw"]
        assert result["affected"] == full_update_result["affected"]
        assert result["generated_maps"] == full_update_result["generated_maps"]

    @pytest.mark.it("✅  Should create UpdateResult with empty data")
    def test_empty_update_result(self, empty_update_result: dict) -> None:
        result = UpdateResult(**empty_update_result)
        assert result["raw"] == empty_update_result["raw"]
        assert result["affected"] == empty_update_result["affected"]
        assert result["generated_maps"] == empty_update_result["generated_maps"]

    @pytest.mark.it("✅  Should accept any type for raw field")
    @pytest.mark.parametrize(
        "raw_value", ["string", 123, None, {"key": "value"}, [1, 2, 3], True, False, 1.5, [], {}]
    )
    def test_raw_field_accepts_any_type(self, raw_value: any) -> None:
        result = UpdateResult(raw=raw_value, affected=1, generated_maps=None)
        assert result["raw"] == raw_value

    @pytest.mark.it("✅  Should accept any type for generated_maps field")
    @pytest.mark.parametrize(
        "generated_maps_value",
        ["string", 123, None, {"key": "value"}, [1, 2, 3], True, False, 1.5, [], {}],
    )
    def test_generated_maps_field_accepts_any_type(self, generated_maps_value: any) -> None:
        result = UpdateResult(raw={}, affected=1, generated_maps=generated_maps_value)
        assert result["generated_maps"] == generated_maps_value

    @pytest.mark.it("✅  Should accept any numeric value for affected field")
    @pytest.mark.parametrize("affected_value", [0, -1, 1.5, 100, -100, 0.0, -0.0, 1e10, -1e10])
    def test_affected_field_accepts_any_numeric(self, affected_value: float) -> None:
        result = UpdateResult(raw={}, affected=affected_value, generated_maps=None)
        assert result["affected"] == affected_value

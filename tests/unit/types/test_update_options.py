from typing import Any

import pytest
from sqlalchemy import BinaryExpression, Column

from fastgear.types.update_options import UpdateOptions
from tests.fixtures.types.update_options_fixtures import test_columns


@pytest.mark.describe("🧪  UpdateOptions")
class TestUpdateOptions:
    @pytest.mark.it("✅  Should create UpdateOptions with where condition")
    def test_create_update_options_with_where(
        self, test_columns: tuple[Column, Column, Column]
    ) -> None:
        id_column, _, _ = test_columns
        where_condition = id_column > 0

        options = UpdateOptions(where=where_condition)

        assert isinstance(options, dict)
        assert isinstance(options["where"], BinaryExpression)

    @pytest.mark.it("✅  Should create UpdateOptions with None where condition")
    def test_create_update_options_with_none_where(self) -> None:
        options = UpdateOptions(where=None)

        assert isinstance(options, dict)
        assert options["where"] is None

    @pytest.mark.it("✅  Should create UpdateOptions with different where conditions")
    @pytest.mark.parametrize(
        "condition_builder",
        [
            lambda cols: cols[0] == 1,
            lambda cols: cols[1].like("%test%"),
            lambda cols: cols[2].is_(True),
            lambda cols: cols[0].in_([1, 2, 3]),
        ],
    )
    def test_create_update_options_with_different_where_conditions(
        self, test_columns: tuple[Column, Column, Column], condition_builder
    ) -> None:
        where_condition = condition_builder(test_columns)

        options = UpdateOptions(where=where_condition)

        assert isinstance(options, dict)
        assert isinstance(options["where"], BinaryExpression)

    @pytest.mark.it("✅  Should create empty UpdateOptions")
    def test_create_empty_update_options(self) -> None:
        options = UpdateOptions()

        assert isinstance(options, dict)
        assert "where" not in options

    @pytest.mark.it("✅  Should create UpdateOptions with Any type value")
    def test_create_update_options_with_any_type(self) -> None:
        custom_condition: Any = {"custom": "condition"}

        options = UpdateOptions(where=custom_condition)

        assert isinstance(options, dict)
        assert options["where"] == custom_condition

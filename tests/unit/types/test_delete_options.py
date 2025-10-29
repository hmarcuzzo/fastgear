from typing import Any

import pytest
from sqlalchemy import BinaryExpression, Column

from fastgear.types.delete_options import DeleteOptions
from tests.fixtures.types.delete_options_fixtures import test_columns


@pytest.mark.describe("🧪  DeleteOptions")
class TestDeleteOptions:
    @pytest.mark.it("✅  Should create DeleteOptions with where condition")
    def test_create_delete_options_with_where(
        self, test_columns: tuple[Column, Column, Column]
    ) -> None:
        id_column, _, _ = test_columns
        where_condition = id_column > 0

        options = DeleteOptions(where=where_condition)

        assert isinstance(options, dict)
        assert isinstance(options["where"], BinaryExpression)

    @pytest.mark.it("✅  Should create DeleteOptions with None where condition")
    def test_create_delete_options_with_none_where(self) -> None:
        options = DeleteOptions(where=None)

        assert isinstance(options, dict)
        assert options["where"] is None

    @pytest.mark.it("✅  Should create DeleteOptions with different where conditions")
    @pytest.mark.parametrize(
        "condition_builder",
        [
            lambda cols: cols[0] == 1,
            lambda cols: cols[1].like("%test%"),
            lambda cols: cols[2].is_(True),
            lambda cols: cols[0].in_([1, 2, 3]),
        ],
    )
    def test_create_delete_options_with_different_where_conditions(
        self, test_columns: tuple[Column, Column, Column], condition_builder
    ) -> None:
        where_condition = condition_builder(test_columns)

        options = DeleteOptions(where=where_condition)

        assert isinstance(options, dict)
        assert isinstance(options["where"], BinaryExpression)

    @pytest.mark.it("✅  Should create empty DeleteOptions")
    def test_create_empty_delete_options(self) -> None:
        options = DeleteOptions()

        assert isinstance(options, dict)
        assert "where" not in options

    @pytest.mark.it("✅  Should create DeleteOptions with Any type value")
    def test_create_delete_options_with_any_type(self) -> None:
        custom_condition: Any = {"custom": "condition"}

        options = DeleteOptions(where=custom_condition)

        assert isinstance(options, dict)
        assert options["where"] == custom_condition

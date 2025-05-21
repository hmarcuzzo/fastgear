from typing import Any

import pytest
from sqlalchemy import BinaryExpression, Column

from fastgear.types.find_many_options import FindManyOptions
from tests.fixtures.types.find_many_options_fixtures import base_options, test_columns  # noqa: F401


@pytest.mark.describe("🧪  FindManyOptions")
class TestFindManyOptions:
    @pytest.mark.it("✅  Should create FindManyOptions with all fields")
    def test_create_find_many_options_with_all_fields(
        self, test_columns: tuple[Column, Column, Column], base_options: dict
    ) -> None:
        id_column, _, _ = test_columns
        where_condition = id_column > 0

        options = FindManyOptions(where=where_condition, **base_options)

        assert isinstance(options, dict)
        assert options["select"] == base_options["select"]
        assert isinstance(options["where"], BinaryExpression)
        assert options["order_by"] == base_options["order_by"]
        assert options["relations"] == base_options["relations"]
        assert options["having"] == base_options["having"]
        assert options["skip"] == base_options["skip"]
        assert options["take"] == base_options["take"]

    @pytest.mark.it("✅  Should create FindManyOptions with only where condition")
    def test_create_find_many_options_with_where(
        self, test_columns: tuple[Column, Column, Column]
    ) -> None:
        _, name_column, _ = test_columns
        where_condition = name_column.like("%test%")

        options = FindManyOptions(where=where_condition)

        assert isinstance(options, dict)
        assert isinstance(options["where"], BinaryExpression)
        assert "select" not in options
        assert "order_by" not in options
        assert "relations" not in options
        assert "having" not in options
        assert "skip" not in options
        assert "take" not in options

    @pytest.mark.it("✅  Should create FindManyOptions with different field combinations")
    @pytest.mark.parametrize(
        "field_name, field_value, expected_value",  # noqa: PT006
        [
            ("select", ["id", "name", "email"], ["id", "name", "email"]),
            ("relations", ["user", "profile", "address"], ["user", "profile", "address"]),
            ("having", [True, False], [True, False]),
            ("order_by", "name", "name"),
            ("skip", 0, 0),
            ("take", 10, 10),
        ],
    )
    def test_create_find_many_options_with_single_field(
        self, field_name: str, field_value: Any, expected_value: Any
    ) -> None:
        options = FindManyOptions(**{field_name: field_value})

        assert isinstance(options, dict)
        assert options[field_name] == expected_value

        # Verify other fields are not present
        for other_field in ["select", "where", "order_by", "relations", "having", "skip", "take"]:
            if other_field != field_name:
                assert other_field not in options

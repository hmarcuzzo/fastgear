from typing import Any

import pytest
from sqlalchemy import BinaryExpression, Column

from fastgear.types.find_one_options import FindOneOptions
from tests.fixtures.types.find_one_options_fixtures import base_options, test_columns


@pytest.mark.describe("🧪  FindOneOptions")
class TestFindOneOptions:
    @pytest.mark.it("✅  Should create FindOneOptions with all fields")
    def test_create_find_one_options_with_all_fields(
        self, test_columns: tuple[Column, Column, Column], base_options: dict
    ) -> None:
        id_column, _, _ = test_columns
        where_condition = id_column > 0

        options = FindOneOptions(where=where_condition, **base_options)

        assert isinstance(options, dict)
        assert options["select"] == base_options["select"]
        assert isinstance(options["where"], BinaryExpression)
        assert options["order_by"] == base_options["order_by"]
        assert options["relations"] == base_options["relations"]
        assert options["having"] == base_options["having"]

    @pytest.mark.it("✅  Should create FindOneOptions with only where condition")
    def test_create_find_one_options_with_where(
        self, test_columns: tuple[Column, Column, Column]
    ) -> None:
        _, name_column, _ = test_columns
        where_condition = name_column.like("%test%")

        options = FindOneOptions(where=where_condition)

        assert isinstance(options, dict)
        assert isinstance(options["where"], BinaryExpression)
        assert "select" not in options
        assert "order_by" not in options
        assert "relations" not in options
        assert "having" not in options

    @pytest.mark.it("✅  Should create FindOneOptions with different field combinations")
    @pytest.mark.parametrize(
        "field_name, field_value, expected_value",
        [
            ("select", ["id", "name", "email"], ["id", "name", "email"]),
            ("relations", ["user", "profile", "address"], ["user", "profile", "address"]),
            ("having", [True, False], [True, False]),
            ("order_by", "name", "name"),
        ],
    )
    def test_create_find_one_options_with_single_field(
        self, field_name: str, field_value: Any, expected_value: Any
    ) -> None:
        options = FindOneOptions(**{field_name: field_value})

        assert isinstance(options, dict)
        assert options[field_name] == expected_value

        # Verify other fields are not present
        for other_field in ["select", "where", "order_by", "relations", "having"]:
            if other_field != field_name:
                assert other_field not in options

    @pytest.mark.it("✅  Should create FindOneOptions with None where condition")
    def test_create_find_one_options_with_none_where(self) -> None:
        options = FindOneOptions(where=None)

        assert isinstance(options, dict)
        assert options["where"] is None
        assert "select" not in options
        assert "order_by" not in options
        assert "relations" not in options
        assert "having" not in options

    @pytest.mark.it("✅  Should accept any type for select field")
    def test_any_type_for_select(self) -> None:
        options = FindOneOptions(select="invalid")  # type: ignore
        assert options["select"] == "invalid"

    @pytest.mark.it("✅  Should accept any type for relations field")
    def test_any_type_for_relations(self) -> None:
        options = FindOneOptions(relations="invalid")  # type: ignore
        assert options["relations"] == "invalid"

    @pytest.mark.it("✅  Should accept any type for having field")
    def test_any_type_for_having(self) -> None:
        options = FindOneOptions(having="invalid")  # type: ignore
        assert options["having"] == "invalid"

import re

import pytest
from pydantic import BaseModel

from fastgear.types.http_exceptions import BadRequestException
from fastgear.types.pagination import Pagination
from fastgear.utils import PaginationUtils
from tests.fixtures.utils.pagination_utils_fixtures import (
    DummyOrderByQuery,
    DummyQuery,
    User,
    pagination_utils,
)


@pytest.mark.describe("🧪  PaginationUtils")
class TestPaginationUtils:
    @pytest.mark.it(
        "✅  build_pagination_options Should build pagination options with default sort and search"
    )
    @pytest.mark.parametrize(("page", "size"), [(1, 10), (2, 5)])
    def test_build_pagination_options_default(
        self, pagination_utils: PaginationUtils, page: int, size: int
    ) -> None:
        result = pagination_utils.build_pagination_options(
            page, size, None, None, None, None, DummyQuery
        )

        assert isinstance(result, Pagination)
        assert result.skip == (page - 1) * size
        assert result.take == size
        assert result.sort == []
        assert result.search == []

    @pytest.mark.it(
        "✅  build_pagination_options Should build pagination options with provided sort and search"
    )
    def test_build_pagination_options_with_sort_and_search(
        self, pagination_utils: PaginationUtils
    ) -> None:
        sort = ["name:ASC", "age:DESC"]
        search = ["name:john", "age:30"]
        result = pagination_utils.build_pagination_options(
            1, 10, search, None, sort, None, DummyQuery, DummyQuery
        )

        assert all(isinstance(s, dict) for s in result.sort)
        assert all(isinstance(s, dict) for s in result.search)
        assert {s["field"] for s in result.sort} == {"name", "age"}
        assert {s["by"] for s in result.sort} == {"ASC", "DESC"}
        assert {s["field"] for s in result.search} == {"name", "age"}
        assert {s["value"] for s in result.search} == {"john", "30"}

    @pytest.mark.it(
        "✅  build_pagination_options Should remove duplicate sort and search parameters"
    )
    def test_build_pagination_options_removes_duplicates(
        self, pagination_utils: PaginationUtils
    ) -> None:
        sort = ["name:ASC", "name:ASC", "age:DESC"]
        search = ["name:john", "name:john", "age:30"]
        result = pagination_utils.build_pagination_options(
            1, 10, search, None, sort, None, DummyQuery, DummyQuery
        )

        expected_sort_serach_length = 2
        assert len(result.sort) == expected_sort_serach_length
        assert len(result.search) == expected_sort_serach_length

    @pytest.mark.it(
        "❌  build_pagination_options Should raise BadRequestException for invalid sort format"
    )
    def test_build_pagination_options_invalid_sort_raises(
        self, pagination_utils: PaginationUtils
    ) -> None:
        sort = ["invalid:ASC"]
        with pytest.raises(BadRequestException):
            pagination_utils.build_pagination_options(
                1, 10, None, None, sort, None, DummyQuery, DummyQuery, DummyQuery
            )

    @pytest.mark.it(
        "❌  build_pagination_options Should raise BadRequestException for invalid search format"
    )
    def test_build_pagination_options_invalid_search_raises(
        self, pagination_utils: PaginationUtils
    ) -> None:
        search = ["invalid:foo"]
        with pytest.raises(BadRequestException):
            pagination_utils.build_pagination_options(
                1, 10, search, None, None, None, DummyQuery, DummyQuery, DummyQuery
            )

    @pytest.mark.it(
        "✅  build_pagination_options Should build pagination options with search_all only (grouped list)"
    )
    def test_build_pagination_options_with_search_all_only(
        self, pagination_utils: PaginationUtils
    ) -> None:
        term = "john"
        result = pagination_utils.build_pagination_options(
            1, 10, None, term, None, None, DummyQuery, DummyQuery
        )

        assert len(result.search) == 1
        grouped = result.search[0]
        assert isinstance(grouped, list)
        fields = {entry["field"] for entry in grouped}
        assert fields == set(DummyQuery.model_fields.keys())
        assert all(entry["value"] == term for entry in grouped)

    @pytest.mark.it(
        "✅  build_pagination_options Should append search_all group after explicit search filters"
    )
    def test_build_pagination_options_with_search_and_search_all(
        self, pagination_utils: PaginationUtils
    ) -> None:
        term = "doe"
        explicit_search = ["name:jane"]
        result = pagination_utils.build_pagination_options(
            1, 10, explicit_search, term, None, None, DummyQuery, DummyQuery
        )

        assert len(result.search) == 2
        assert isinstance(result.search[0], dict)
        assert result.search[0]["field"] == "name"
        assert result.search[0]["value"] == "jane"
        assert isinstance(result.search[1], list)
        grouped = result.search[1]
        fields = {entry["field"] for entry in grouped}
        assert fields == set(DummyQuery.model_fields.keys())
        assert all(entry["value"] == term for entry in grouped)

    @pytest.mark.it("✅  build_pagination_options Should set columns when columns list is provided")
    def test_build_pagination_options_with_columns(self, pagination_utils: PaginationUtils) -> None:
        columns = ["name", "age", "name"]  # inclui duplicata
        result = pagination_utils.build_pagination_options(
            1, 10, None, None, None, columns, DummyQuery, DummyQuery
        )
        assert sorted(result.columns) == ["age", "name"]

    @pytest.mark.it(
        "❌  build_pagination_options Should raise BadRequestException for invalid columns"
    )
    def test_build_pagination_options_invalid_columns_raises(
        self, pagination_utils: PaginationUtils
    ) -> None:
        columns = ["unknown"]
        with pytest.raises(BadRequestException) as excinfo:
            pagination_utils.build_pagination_options(
                1, 10, None, None, None, columns, DummyQuery, DummyQuery
            )
        assert "Invalid columns" in str(excinfo.value)

    @pytest.mark.it(
        "✅  assert_no_blocked_attributes Should not raise when no blocked attributes are present"
    )
    def test_assert_no_blocked_attributes_allows_when_none(self) -> None:
        PaginationUtils.assert_no_blocked_attributes(["search", "sort"], None, None, None, None)

    @pytest.mark.it(
        "❌  assert_no_blocked_attributes Should raise BadRequestException when blocked attributes are used"
    )
    def test_assert_no_blocked_attributes_raises(self) -> None:
        blocked_attrs = ["search", "columns"]
        search = ["name:john"]
        columns = ["id"]

        with pytest.raises(BadRequestException) as excinfo:
            PaginationUtils.assert_no_blocked_attributes(blocked_attrs, search, None, columns, None)

        assert excinfo.value.loc == ["search", "columns"]

    @pytest.mark.it(
        "✅  assert_search_param_convertible Should return True when receives a valid value"
    )
    def test_assert_search_param_convertible_valid(self) -> None:
        search_param = {"field": "age", "value": "30"}
        assert PaginationUtils.assert_search_param_convertible(DummyQuery, search_param) is True

    @pytest.mark.it(
        "❌  assert_search_param_convertible Should raise BadRequestException when receives an invalid value"
    )
    def test_assert_search_param_convertible_invalid_raises(self) -> None:
        search_param = {"field": "age", "value": "not_an_int"}
        with pytest.raises(BadRequestException):
            PaginationUtils.assert_search_param_convertible(DummyQuery, search_param)

    @pytest.mark.it("✅  _is_list_type_hint should correctly detect list type hints")
    @pytest.mark.parametrize(
        ("type_hint", "expected"),
        [(list[str], True), (list[int], True), (int, False), (list[str] | None, False)],
        ids=["list of str", "list of int", "int", "optional list"],
    )
    def test_is_list_type_hint_parametrized(self, type_hint, expected) -> None:
        assert PaginationUtils._is_list_type_hint(type_hint) is expected

    @pytest.mark.it("✅  to_page_response Should return correct page and metadata for offset 0")
    def test_to_page_response_basic(self) -> None:
        items = [1, 2, 3]
        total = 50
        offset = 0
        size = 10

        page = PaginationUtils.to_page_response(items, total, offset, size)

        assert page.items == items
        assert page.page == 1
        assert page.size == size
        assert page.total == total
        assert page.pages == 5

    @pytest.mark.it("✅  to_page_response Should calculate current page from offset and size")
    def test_to_page_response_with_offset(self) -> None:
        items = ["a", "b"]
        total = 55
        offset = 20
        size = 10

        page = PaginationUtils.to_page_response(items, total, offset, size)

        assert page.items == items
        assert page.page == 3
        assert page.size == size
        assert page.total == total
        assert page.pages == 6

    @pytest.mark.it("✅  to_page_response Should return 1 page when total < size")
    def test_to_page_response_total_less_than_size(self) -> None:
        items = []
        total = 3
        offset = 0
        size = 10

        page = PaginationUtils.to_page_response(items, total, offset, size)

        assert page.items == items
        assert page.page == 1
        assert page.size == size
        assert page.total == total
        assert page.pages == 1

    @pytest.mark.it("❌  to_page_response Should propagate error when receiving size equal to zero")
    def test_to_page_response_zero_size_raises(self) -> None:
        with pytest.raises(ZeroDivisionError):
            PaginationUtils.to_page_response([], 10, 0, 0)

    @pytest.mark.it("✅  aggregate_values_by_field Should return single value for non-list field")
    def test_aggregate_values_single_non_list_field(self) -> None:
        from pydantic import BaseModel

        class Q(BaseModel):
            age: int

        entries = [{"field": "age", "value": "30"}]

        result = PaginationUtils.aggregate_values_by_field(entries, Q)

        assert result == [{"field": "age", "value": "30"}]

    @pytest.mark.it(
        "✅  aggregate_values_by_field should return list for single entry when field is list-typed"
    )
    def test_aggregate_values_single_list_field(self) -> None:
        from pydantic import BaseModel

        class Q(BaseModel):
            tags: list[str]

        entries = [{"field": "tags", "value": "x"}]

        result = PaginationUtils.aggregate_values_by_field(entries, Q)

        assert result == [{"field": "tags", "value": ["x"]}]

    @pytest.mark.it(
        "✅  aggregate_values_by_field should aggregate multiple values into a list for non-list field"
    )
    def test_aggregate_values_multiple_non_list_field(self) -> None:
        from pydantic import BaseModel

        class Q(BaseModel):
            age: int

        entries = [{"field": "age", "value": "1"}, {"field": "age", "value": "2"}]

        result = PaginationUtils.aggregate_values_by_field(entries, Q)

        assert result == [{"field": "age", "value": ["1", "2"]}]

    @pytest.mark.it(
        "✅  aggregate_values_by_field should aggregate multiple values into a list for list-typed field"
    )
    def test_aggregate_values_multiple_list_field(self) -> None:
        from pydantic import BaseModel

        class Q(BaseModel):
            tags: list[str]

        entries = [{"field": "tags", "value": "a"}, {"field": "tags", "value": "b"}]

        result = PaginationUtils.aggregate_values_by_field(entries, Q)

        assert result == [{"field": "tags", "value": ["a", "b"]}]

    @pytest.mark.it("✅  merge_with_required_columns returns selected columns")
    def test_merge_with_required_columns_returns_selected_scalar_columns_no_relations(
        self, pagination_utils: PaginationUtils
    ) -> None:
        selected_columns = ["name", "age"]

        result_selected = PaginationUtils.merge_with_required_columns(
            selected_columns.copy(), DummyQuery
        )

        assert isinstance(result_selected, list)
        assert len(result_selected) == 2
        assert result_selected == selected_columns

    @pytest.mark.it("✅  merge_with_required_columns Should keep non-existing columns")
    def test_merge_with_required_columns_keeps_nonexistent(
        self, pagination_utils: PaginationUtils
    ) -> None:
        selected_columns = ["nonexistent"]

        result_selected = PaginationUtils.merge_with_required_columns(
            selected_columns.copy(), DummyQuery
        )

        assert isinstance(result_selected, list)
        assert result_selected == selected_columns

    @pytest.mark.it(
        "✅  merge_with_required_columns Should add required fields from Schema when missing"
    )
    def test_merge_with_required_columns_adds_required_fields(
        self, pagination_utils: PaginationUtils
    ) -> None:
        # create a Schema with a required field (no default) so model_fields marks it required
        class RequiredCols(BaseModel):
            name: str

        result_selected = PaginationUtils.merge_with_required_columns([], RequiredCols)

        assert isinstance(result_selected, list)
        assert result_selected == ["name"]

    @pytest.mark.it("✅  merge_with_required_columns Should keep selected scalar fields unchanged")
    def test_merge_with_required_columns_keeps_selected_scalar_fields_unchanged(self) -> None:
        class Cols(BaseModel):
            personal_data: str = None
            name: str = None

        columns = ["name"]  # non-relationship selected

        result_selected = PaginationUtils.merge_with_required_columns(columns.copy(), Cols)

        # returned selected list should still contain the original selected (name handled)
        assert result_selected == columns

    @pytest.mark.it("✅  is_valid_column_selection should return True for empty list")
    def test_is_valid_column_selection_empty(self) -> None:
        assert PaginationUtils.is_valid_column_selection([], DummyQuery) is True

    @pytest.mark.it("✅  is_valid_column_selection should return True when all columns are valid")
    def test_is_valid_column_selection_all_valid(self) -> None:
        assert PaginationUtils.is_valid_column_selection(["name", "age"], DummyQuery) is True

    @pytest.mark.it("❌  is_valid_column_selection should return False when any column is invalid")
    def test_is_valid_column_selection_invalid(self) -> None:
        assert (
            PaginationUtils.is_valid_column_selection(["name", "nonexistent"], DummyQuery) is False
        )

    @pytest.mark.it(
        "✅  validate_required_search_filter should return True when all required fields are present"
    )
    def test_validate_required_search_filter_all_present(self) -> None:
        class Q(BaseModel):
            name: str
            age: int | None = None

        search = [{"field": "name", "value": "john"}]
        assert PaginationUtils.validate_required_search_filter(search, Q.model_fields) is True

    @pytest.mark.it(
        "❌  validate_required_search_filter should return False when a required field is missing"
    )
    def test_validate_required_search_filter_missing_required(self) -> None:
        class Q(BaseModel):
            name: str
            age: int | None = None

        search = [{"field": "age", "value": "33"}]  # missing required 'name'
        assert PaginationUtils.validate_required_search_filter(search, Q.model_fields) is False

    @pytest.mark.it(
        "✅  validate_required_search_filter should return True when there are no required fields"
    )
    def test_validate_required_search_filter_no_required_fields(self) -> None:
        class Q(BaseModel):
            name: str | None = None
            age: int | None = None

        search: list[dict[str, str]] = []
        assert PaginationUtils.validate_required_search_filter(search, Q.model_fields) is True

    @pytest.mark.it(
        "✅  validate_required_search_filter should return True when multiple required fields are present"
    )
    def test_validate_required_search_filter_multiple_required_present(self) -> None:
        class Q(BaseModel):
            name: str
            age: int

        search = [{"field": "name", "value": "john"}, {"field": "age", "value": "30"}]
        assert PaginationUtils.validate_required_search_filter(search, Q.model_fields) is True

    @pytest.mark.it("✅  _is_valid_search_params should return True for valid inputs")
    def test__is_valid_search_params_valid(self) -> None:
        class Q(BaseModel):
            name: str

        search = [{"field": "name", "value": "john"}]
        assert PaginationUtils._is_valid_search_params(search, Q) is True

    @pytest.mark.it(
        "❌  _is_valid_search_params should return False when required fields are missing"
    )
    def test__is_valid_search_params_missing_required(self) -> None:
        class Q(BaseModel):
            name: str

        search: list[dict[str, str]] = []
        assert PaginationUtils._is_valid_search_params(search, Q) is False

    @pytest.mark.it(
        "❌  _is_valid_search_params should return False when any field is not in the schema"
    )
    def test__is_valid_search_params_invalid_field(self) -> None:
        class Q(BaseModel):
            name: str = None

        search = [{"field": "nonexistent", "value": "x"}]
        assert PaginationUtils._is_valid_search_params(search, Q) is False

    @pytest.mark.it(
        "❌  _is_valid_search_params should raise BadRequestException for unconvertible value"
    )
    def test__is_valid_search_params_unconvertible_value_raises(self) -> None:
        class Q(BaseModel):
            age: int

        search = [{"field": "age", "value": "not_an_int"}]
        with pytest.raises(BadRequestException):
            PaginationUtils._is_valid_search_params(search, Q)

    @pytest.mark.it(
        "✅  _is_valid_search_params should aggregate multiple list values and validate"
    )
    def test__is_valid_search_params_aggregate_list_values(self) -> None:
        class Q(BaseModel):
            tags: list[str]

        search = [{"field": "tags", "value": "a"}, {"field": "tags", "value": "b"}]
        assert PaginationUtils._is_valid_search_params(search, Q) is True

    @pytest.mark.it(
        "❌  _is_valid_search_params should return False when field is annotated as ClassVar (present in type hints but not in model_fields)"
    )
    def test__is_valid_search_params_field_not_in_model_fields_returns_false(self) -> None:
        from typing import ClassVar

        class Q(BaseModel):
            # Present in typing.get_type_hints but not in Pydantic model_fields
            name: ClassVar[str] = "default"

        search = [{"field": "name", "value": "john"}]

        assert PaginationUtils._is_valid_search_params(search, Q) is False

    @pytest.mark.it(
        "❌  _is_valid_search_params should raise BadRequestException when aggregate_values_by_field raises KeyError"
    )
    def test__is_valid_search_params_aggregate_keyerror(self, monkeypatch) -> None:
        class Q(BaseModel):
            name: str

        def fake_aggregate(_entries, _query):
            raise KeyError("name")

        monkeypatch.setattr(
            PaginationUtils, "aggregate_values_by_field", staticmethod(fake_aggregate)
        )

        search = [{"field": "name", "value": "john"}]
        with pytest.raises(BadRequestException) as excinfo:
            PaginationUtils._is_valid_search_params(search, Q)

        assert "Invalid search filters" in str(excinfo.value)

    @pytest.mark.it("✅  _is_valid_sort_params should return True for valid fields and directions")
    def test__is_valid_sort_params_valid(self) -> None:
        class OrderBy(BaseModel):
            name: str
            age: str | None = None

        sort = [{"field": "name", "by": "ASC"}, {"field": "age", "by": "DESC"}]
        assert PaginationUtils._is_valid_sort_params(sort, OrderBy) is True

    @pytest.mark.it("❌  _is_valid_sort_params should return False when field not in schema")
    def test__is_valid_sort_params_invalid_field(self) -> None:
        class OrderBy(BaseModel):
            name: str

        sort = [{"field": "unknown", "by": "ASC"}]
        assert PaginationUtils._is_valid_sort_params(sort, OrderBy) is False

    @pytest.mark.it("❌  _is_valid_sort_params should return False when direction is invalid")
    def test__is_valid_sort_params_invalid_direction(self) -> None:
        class OrderBy(BaseModel):
            name: str

        sort = [{"field": "name", "by": "UP"}]
        assert PaginationUtils._is_valid_sort_params(sort, OrderBy) is False

    @pytest.mark.it(
        "❌  _is_valid_sort_params should return False when any of multiple sorts is invalid"
    )
    def test__is_valid_sort_params_mixed_valid_invalid(self) -> None:
        class OrderBy(BaseModel):
            name: str
            age: str | None = None

        sort = [{"field": "name", "by": "ASC"}, {"field": "nonexistent", "by": "DESC"}]
        assert PaginationUtils._is_valid_sort_params(sort, OrderBy) is False

    @pytest.mark.it("✅  _is_valid_sort_params should return True for empty sort list")
    def test__is_valid_sort_params_empty(self) -> None:
        class OrderBy(BaseModel):
            name: str

        sort: list[dict[str, str]] = []
        # all([]) is True for both checks -> overall True
        assert PaginationUtils._is_valid_sort_params(sort, OrderBy) is True

    @pytest.mark.it(
        "✅  _check_and_raise_for_invalid_search_filters should do nothing when find_all_query is None"
    )
    def test__check_and_raise_for_invalid_search_filters_no_schema(self) -> None:
        search = [{"field": "name", "value": "john"}]
        # Should not raise when no schema is provided
        PaginationUtils._check_and_raise_for_invalid_search_filters(search, None)

    @pytest.mark.it(
        "✅  _check_and_raise_for_invalid_search_filters should not raise for valid filters"
    )
    def test__check_and_raise_for_invalid_search_filters_valid(self) -> None:
        class Q(BaseModel):
            name: str

        search = [{"field": "name", "value": "john"}]
        # Valid given schema -> should not raise
        PaginationUtils._check_and_raise_for_invalid_search_filters(search, Q)

    @pytest.mark.it(
        "❌  _check_and_raise_for_invalid_search_filters should raise BadRequestException when required field is missing"
    )
    def test__check_and_raise_for_invalid_search_filters_missing_required_raises(self) -> None:
        class Q(BaseModel):
            name: str  # required
            age: int | None = None

        search = [{"field": "age", "value": "33"}]  # missing required 'name'
        with pytest.raises(BadRequestException) as excinfo:
            PaginationUtils._check_and_raise_for_invalid_search_filters(search, Q)

        assert str(excinfo.value) == "Invalid search filters"

    @pytest.mark.it(
        "❌  _check_and_raise_for_invalid_search_filters should propagate BadRequestException for unknown field"
    )
    def test__check_and_raise_for_invalid_search_filters_unknown_field_propagates(self) -> None:
        class Q(BaseModel):
            name: str

        search = [{"field": "unknown", "value": "x"}]
        # aggregate_values_by_field will raise KeyError internally, which becomes BadRequestException
        with pytest.raises(BadRequestException) as excinfo:
            PaginationUtils._check_and_raise_for_invalid_search_filters(search, Q)

        # Message should include the invalid field reference
        assert "Invalid search filters" in str(excinfo.value.msg)

    @pytest.mark.it(
        "✅  _check_and_raise_for_invalid_sort_filters should do nothing when order_by_query is None"
    )
    def test__check_and_raise_for_invalid_sort_filters_no_schema(self) -> None:
        sorts = [{"field": "name", "by": "ASC"}]
        # Should not raise when no schema is provided
        PaginationUtils._check_and_raise_for_invalid_sort_filters(sorts, None)

    @pytest.mark.it(
        "✅  _check_and_raise_for_invalid_sort_filters should not raise for valid sort filters"
    )
    def test__check_and_raise_for_invalid_sort_filters_valid(self) -> None:
        sorts = [{"field": "name", "by": "ASC"}, {"field": "personal_data__address", "by": "DESC"}]
        PaginationUtils._check_and_raise_for_invalid_sort_filters(sorts, DummyOrderByQuery)

    @pytest.mark.it(
        "❌  _check_and_raise_for_invalid_sort_filters should raise when field is not in schema"
    )
    def test__check_and_raise_for_invalid_sort_filters_invalid_field_raises(self) -> None:
        sorts = [{"field": "unknown", "by": "ASC"}]
        with pytest.raises(BadRequestException) as excinfo:
            PaginationUtils._check_and_raise_for_invalid_sort_filters(sorts, DummyOrderByQuery)
        assert "Invalid sort filters" in str(excinfo.value)

    @pytest.mark.it(
        "❌  _check_and_raise_for_invalid_sort_filters should raise when direction is invalid"
    )
    def test__check_and_raise_for_invalid_sort_filters_invalid_direction_raises(self) -> None:
        sorts = [{"field": "name", "by": "UP"}]  # invalid direction
        with pytest.raises(BadRequestException) as excinfo:
            PaginationUtils._check_and_raise_for_invalid_sort_filters(sorts, DummyOrderByQuery)
        assert "Invalid sort filters" in str(excinfo.value)

    @pytest.mark.it("✅  _create_pagination_search should build list of field/value mappings")
    def test__create_pagination_search_basic(self) -> None:
        entries = ["name:john", "age:30"]
        result = PaginationUtils._create_pagination_search(entries)

        assert isinstance(result, list)
        assert result[0]["field"] == "name"
        assert result[0]["value"] == "john"
        assert result[1]["field"] == "age"
        assert result[1]["value"] == "30"

    @pytest.mark.it("✅  _create_pagination_search should split only on the first colon")
    def test__create_pagination_search_splits_on_first_colon_only(self) -> None:
        entries = ["note:hello:world"]
        result = PaginationUtils._create_pagination_search(entries)

        assert result == [{"field": "note", "value": "hello:world"}]

    @pytest.mark.it(
        "❌  _create_pagination_search should raise ValueError for invalid format (no colon)"
    )
    def test__create_pagination_search_invalid_format_raises(self) -> None:
        entries = ["invalid"]
        with pytest.raises(
            ValueError, match=re.escape("not enough values to unpack (expected 2, got 1)")
        ):
            PaginationUtils._create_pagination_search(entries)

    @pytest.mark.it("✅  _create_pagination_sort should build list of field/by mappings")
    def test__create_pagination_sort_basic(self) -> None:
        entries = ["name:ASC", "age:DESC"]
        result = PaginationUtils._create_pagination_sort(entries)

        assert isinstance(result, list)
        assert result[0]["field"] == "name"
        assert result[0]["by"] == "ASC"
        assert result[1]["field"] == "age"
        assert result[1]["by"] == "DESC"

    @pytest.mark.it("✅  _create_pagination_sort should split only on the first colon")
    def test__create_pagination_sort_splits_on_first_colon_only(self) -> None:
        entries = ["note:hello:world"]
        result = PaginationUtils._create_pagination_sort(entries)

        assert result == [{"field": "note", "by": "hello:world"}]

    @pytest.mark.it(
        "❌  _create_pagination_sort should raise ValueError for invalid format (no colon)"
    )
    def test__create_pagination_sort_invalid_format_raises(self) -> None:
        entries = ["invalid"]
        with pytest.raises(
            ValueError, match=re.escape("not enough values to unpack (expected 2, got 1)")
        ):
            PaginationUtils._create_pagination_sort(entries)

    @pytest.mark.it("✅  select_columns should map existing entity attributes into select")
    def test_select_columns_success_maps_attributes(self) -> None:
        columns = ["name", "age"]

        result = PaginationUtils.select_columns(columns, DummyQuery)

        assert len(result) == 2
        assert "name" in result
        assert "age" in result

    @pytest.mark.it("❌  select_columns should raise BadRequestException for any invalid column")
    def test_select_columns_invalid_raises(self) -> None:
        selected_columns = ["unknown"]

        with pytest.raises(BadRequestException) as excinfo:
            PaginationUtils.select_columns(selected_columns, DummyQuery)

        assert "Invalid columns" in str(excinfo.value)

    @pytest.mark.it(
        "✅  select_columns should add required fields from Schema when selected is empty"
    )
    def test_select_columns_empty_adds_required_from_schema(self) -> None:
        class RequiredCols(BaseModel):
            name: str  # required

        selected_columns: list[str] = []

        result = PaginationUtils.select_columns(selected_columns, RequiredCols)

        assert "name" in result

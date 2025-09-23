# ruff: noqa: PLR2004

import pytest
from pydantic import BaseModel

from fastgear.types.http_exceptions import BadRequestException
from fastgear.utils import PaginationUtils
from tests.fixtures.utils.pagination_utils_fixtures import (  # noqa: F401
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
        result = pagination_utils.build_pagination_options(page, size, None, None)

        assert isinstance(result, dict)
        assert result["skip"] == page
        assert result["take"] == size
        assert result["sort"] == []
        assert result["search"] == []

    @pytest.mark.it(
        "✅  build_pagination_options Should build pagination options with provided sort and search"
    )
    def test_build_pagination_options_with_sort_and_search(
        self, pagination_utils: PaginationUtils
    ) -> None:
        sort = ["name:ASC", "age:DESC"]
        search = ["name:john", "age:30"]
        result = pagination_utils.build_pagination_options(
            1, 10, search, sort, DummyQuery, DummyQuery
        )

        assert all(isinstance(s, dict) for s in result["sort"])
        assert all(isinstance(s, dict) for s in result["search"])
        assert {s["field"] for s in result["sort"]} == {"name", "age"}
        assert {s["by"] for s in result["sort"]} == {"ASC", "DESC"}
        assert {s["field"] for s in result["search"]} == {"name", "age"}
        assert {s["value"] for s in result["search"]} == {"john", "30"}

    @pytest.mark.it(
        "✅  build_pagination_options Should remove duplicate sort and search parameters"
    )
    def test_build_pagination_options_removes_duplicates(
        self, pagination_utils: PaginationUtils
    ) -> None:
        sort = ["name:ASC", "name:ASC", "age:DESC"]
        search = ["name:john", "name:john", "age:30"]
        result = pagination_utils.build_pagination_options(
            1, 10, search, sort, DummyQuery, DummyQuery
        )

        expected_sort_serach_length = 2
        assert len(result["sort"]) == expected_sort_serach_length
        assert len(result["search"]) == expected_sort_serach_length

    @pytest.mark.it(
        "❌  build_pagination_options Should raise BadRequestException for invalid sort format"
    )
    def test_build_pagination_options_invalid_sort_raises(
        self, pagination_utils: PaginationUtils
    ) -> None:
        sort = ["invalid:ASC"]
        with pytest.raises(BadRequestException):
            pagination_utils.build_pagination_options(1, 10, None, sort, DummyQuery, DummyQuery)

    @pytest.mark.it(
        "❌  build_pagination_options Should raise BadRequestException for invalid search format"
    )
    def test_build_pagination_options_invalid_search_raises(
        self, pagination_utils: PaginationUtils
    ) -> None:
        search = ["invalid:foo"]
        with pytest.raises(BadRequestException):
            pagination_utils.build_pagination_options(1, 10, search, None, DummyQuery, DummyQuery)

    @pytest.mark.it(
        "✅  get_paging_data Should return formatted paging data without sort/search/columns"
    )
    def test_get_paging_data_basic(self, pagination_utils: PaginationUtils) -> None:
        paging_options = pagination_utils.build_pagination_options(1, 10, None, None)

        result = pagination_utils.get_paging_data(
            entity=User,
            paging_options=paging_options,
            columns=[],
            search_all=None,
            columns_query=DummyQuery,
            find_all_query=None,
        )

        # skip should be converted to offset (page 1 -> 0)
        assert result["skip"] == 0
        assert result["take"] == 10
        assert "relations" not in result
        assert "select" not in result
        assert result.get("order_by") == []
        assert result.get("where") == []

    @pytest.mark.it("✅  get_paging_data Should build where clause when search_all is provided")
    def test_get_paging_data_search_all(self, pagination_utils: PaginationUtils) -> None:
        paging_options = pagination_utils.build_pagination_options(1, 10, None, None)

        result = pagination_utils.get_paging_data(
            entity=User,
            paging_options=paging_options,
            columns=[],
            search_all="john",
            columns_query=DummyQuery,
            find_all_query=DummyQuery,
        )

        # when search_all is provided, where should contain at least one clause
        assert "where" in result
        assert result["where"] != []

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

    @pytest.mark.it("✅  sort_data Should correctly sort data with ASC and DESC order")
    def test_sort_data_basic(self) -> None:
        from sqlalchemy.sql.elements import UnaryExpression

        paging_options = {"sort": [{"field": "name", "by": "ASC"}, {"field": "age", "by": "DESC"}]}
        paging_data = {"order_by": []}
        PaginationUtils.sort_data(paging_options, User, paging_data)

        assert len(paging_data["order_by"]) == 2
        assert all(isinstance(o, UnaryExpression) for o in paging_data["order_by"])
        assert str(paging_data["order_by"][0]).endswith(".name ASC")
        assert str(paging_data["order_by"][1]).endswith(".age DESC")

    @pytest.mark.it("✅  sort_data Should not modify order_by if sort is missing")
    def test_sort_data_no_sort(self) -> None:
        paging_options = {}
        paging_data = {"order_by": []}
        PaginationUtils.sort_data(paging_options, User, paging_data)

        assert paging_data["order_by"] == []

    @pytest.mark.it("✅  sort_data Should handle sort field not present in entity")
    def test_sort_data_field_not_in_entity(self) -> None:
        paging_options = {"sort": [{"field": "nonexistent", "by": "ASC"}]}
        paging_data = {"order_by": []}
        PaginationUtils.sort_data(paging_options, User, paging_data)

        assert len(paging_data["order_by"]) == 1
        assert "nonexistent" in str(paging_data["order_by"][0])

    @pytest.mark.it("✅  sort_data Should handle multiple sort fields")
    def test_sort_data_multiple_fields(self) -> None:
        paging_options = {
            "sort": [
                {"field": "name", "by": "ASC"},
                {"field": "age", "by": "DESC"},
                {"field": "nonexistent", "by": "ASC"},
            ]
        }
        paging_data = {"order_by": []}
        PaginationUtils.sort_data(paging_options, User, paging_data)

        assert len(paging_data["order_by"]) == 3
        assert str(paging_data["order_by"][0]).endswith(".name ASC")
        assert str(paging_data["order_by"][1]).endswith(".age DESC")
        assert "nonexistent" in str(paging_data["order_by"][2])

    @pytest.mark.it("✅  search_data Should not modify where if search is missing")
    def test_search_data_no_search(self) -> None:
        paging_options = {}
        paging_data = {"where": []}
        PaginationUtils.search_data(paging_options, User, paging_data)

        assert paging_data["where"] == []

    @pytest.mark.it(
        "✅  search_data Should build ilike condition when search field exists on entity"
    )
    def test_search_data_field_in_entity(self) -> None:
        paging_options = {"search": [{"field": "name", "value": "john"}]}
        paging_data = {"where": []}
        PaginationUtils.search_data(paging_options, User, paging_data)

        assert len(paging_data["where"]) == 1
        assert "lower(users.name) like lower(:name_1)" in str(paging_data["where"][0]).lower()

    @pytest.mark.it("✅  search_data Should append dict when search field not in entity")
    def test_search_data_field_not_in_entity(self) -> None:
        paging_options = {"search": [{"field": "nonexistent", "value": "foo"}]}
        paging_data = {"where": []}
        PaginationUtils.search_data(paging_options, User, paging_data)

        assert len(paging_data["where"]) == 1
        assert isinstance(paging_data["where"][0], dict)
        assert paging_data["where"][0] == {"field": "nonexistent", "value": "foo"}

    @pytest.mark.it("✅  search_all_data Should not modify where if search_all is missing")
    def test_search_all_no_search(self) -> None:
        paging_data = {"where": []}
        PaginationUtils.search_all_data(User, paging_data, search_all=None, find_all_query=None)
        assert paging_data["where"] == []

    @pytest.mark.it(
        "✅  search_all_data Should append an OR clause when all find_all_query fields map to entity columns"
    )
    def test_search_all_with_find_all_query_mapping_to_entity(self) -> None:
        from pydantic import BaseModel

        class LocalQuery(BaseModel):
            name: str
            age: str

        paging_data = {"where": []}
        PaginationUtils.search_all_data(
            User, paging_data, search_all="john", find_all_query=LocalQuery
        )

        assert len(paging_data["where"]) == 1
        clause_str = str(paging_data["where"][0]).lower()
        assert "like" in clause_str or "ilike" in clause_str

    @pytest.mark.it(
        "✅  search_all_data Should append list when some find_all_query fields are not entity columns"
    )
    def test_search_all_with_mixed_find_all_query_fields(self) -> None:
        from pydantic import BaseModel

        class MixedQuery(BaseModel):
            name: str
            external: str

        paging_data = {"where": []}
        PaginationUtils.search_all_data(
            User, paging_data, search_all="foo", find_all_query=MixedQuery
        )

        assert len(paging_data["where"]) == 1
        where_item = paging_data["where"][0]
        assert isinstance(where_item, list)
        assert any(isinstance(w, dict) and w.get("field") == "external" for w in where_item)

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

    @pytest.mark.it(
        "✅  resolve_selected_columns_and_relations Should map existing entity attributes into select and not set relations when none"
    )
    def test_resolve_selected_columns_maps_attributes(
        self, pagination_utils: PaginationUtils
    ) -> None:
        paging_options = {}
        selected_columns = ["name", "age"]

        result_opts, result_selected = PaginationUtils.resolve_selected_columns_and_relations(
            paging_options, selected_columns.copy(), DummyQuery, User
        )

        # select should be created and contain SQLAlchemy column attributes
        assert "select" in result_opts
        assert len(result_opts["select"]) == 2
        assert any(".name" in str(c) or "name" in str(c) for c in result_opts["select"])
        assert any(".age" in str(c) or "age" in str(c) for c in result_opts["select"])
        # no relations expected
        assert "relations" not in result_opts
        # returned selected list should be unchanged in this path
        assert result_selected == selected_columns

    @pytest.mark.it(
        "✅  resolve_selected_columns_and_relations Should keep non-existing columns as strings"
    )
    def test_resolve_selected_columns_keeps_nonexistent_strings(
        self, pagination_utils: PaginationUtils
    ) -> None:
        paging_options = {}
        selected_columns = ["nonexistent"]

        result_opts, result_selected = PaginationUtils.resolve_selected_columns_and_relations(
            paging_options, selected_columns.copy(), DummyQuery, User
        )

        assert "select" in result_opts
        assert result_opts["select"][0] == "nonexistent"
        assert result_selected == selected_columns

    @pytest.mark.it(
        "✅  resolve_selected_columns_and_relations Should add required fields from Schema when missing"
    )
    def test_resolve_selected_columns_adds_required_fields(
        self, pagination_utils: PaginationUtils
    ) -> None:
        # create a Schema with a required field (no default) so model_fields marks it required
        class RequiredCols(BaseModel):
            name: str

        paging_options = {}
        selected_columns: list[str] = []

        result_opts, result_selected = PaginationUtils.resolve_selected_columns_and_relations(
            paging_options, selected_columns, RequiredCols, User
        )

        assert "select" in result_opts
        # the required `name` should have been added as an attribute on the entity
        assert any("name" in str(c) for c in result_opts["select"]) is True
        # returned selected should include the original (empty) list or remain a list
        assert isinstance(result_selected, list)

    @pytest.mark.it(
        "✅  resolve_selected_columns_and_relations Should handle fields that are entity relationships"
    )
    def test_resolve_selected_columns_handles_relationship_field(self) -> None:
        class Cols(BaseModel):
            personal_data: str | None

        paging_options = {}
        selected_columns = ["personal_data"]

        result_opts, result_selected = PaginationUtils.resolve_selected_columns_and_relations(
            paging_options, selected_columns.copy(), Cols, User
        )

        # relation should be set
        assert "relations" in result_opts
        assert result_opts["relations"] == ["personal_data"]
        # select should not contain personal_data because it's a relationship
        assert "select" not in result_opts
        # returned selected should not contain personal_data because it's a relationship
        assert "personal_data" not in result_selected

    @pytest.mark.it(
        "❌ resolve_selected_columns_and_relations Should add required relationship when not selected"
    )
    def test_resolve_selected_columns_add_relationship_when_not_selected(self) -> None:
        class Cols(BaseModel):
            personal_data: str

        paging_options = {}
        selected_columns: list[str] = []  # relationship not selected and not required

        result_opts, result_selected = PaginationUtils.resolve_selected_columns_and_relations(
            paging_options, selected_columns.copy(), Cols, User
        )

        # relation should be set because personal_data is required
        assert "relations" in result_opts
        # returned selected stays empty
        assert result_selected == selected_columns

    @pytest.mark.it(
        "✅ resolve_selected_columns_and_relations Should map selected non-relationship field and ignore unselected relationship"
    )
    def test_resolve_selected_columns_maps_selected_non_relationship_and_ignores_relationship(
        self,
    ) -> None:
        class Cols(BaseModel):
            personal_data: str = None
            name: str = None

        paging_options = {}
        selected_columns = ["name"]  # non-relationship selected

        result_opts, result_selected = PaginationUtils.resolve_selected_columns_and_relations(
            paging_options, selected_columns.copy(), Cols, User
        )

        # relation should not be set because personal_data wasn't selected and is optional
        assert "relations" not in result_opts
        # select should contain mapped name attribute
        assert "select" in result_opts
        assert any("name" in str(c) for c in result_opts["select"]) is True
        # returned selected list should still contain the original selected (name handled)
        assert result_selected == selected_columns

    @pytest.mark.it("✅  validate_columns should return True for empty list")
    def test_validate_columns_empty(self) -> None:
        assert PaginationUtils.validate_columns([], DummyQuery) is True

    @pytest.mark.it("✅  validate_columns should return True when all columns are valid")
    def test_validate_columns_all_valid(self) -> None:
        assert PaginationUtils.validate_columns(["name", "age"], DummyQuery) is True

    @pytest.mark.it("❌  validate_columns should return False when any column is invalid")
    def test_validate_columns_invalid(self) -> None:
        assert PaginationUtils.validate_columns(["name", "nonexistent"], DummyQuery) is False

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
        "❌  _is_valid_search_params should raise BadRequestException for unknown field"
    )
    def test__is_valid_search_params_unknown_field_raises(self) -> None:
        class Q(BaseModel):
            name: str = None

        search = [{"field": "nonexistent", "value": "x"}]
        with pytest.raises(BadRequestException):
            PaginationUtils._is_valid_search_params(search, Q)

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
        "❌  _create_pagination_search should raise IndexError for invalid format (no colon)"
    )
    def test__create_pagination_search_invalid_format_raises(self) -> None:
        entries = ["invalid"]
        with pytest.raises(IndexError):
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
        "❌  _create_pagination_sort should raise IndexError for invalid format (no colon)"
    )
    def test__create_pagination_sort_invalid_format_raises(self) -> None:
        entries = ["invalid"]
        with pytest.raises(IndexError):
            PaginationUtils._create_pagination_sort(entries)

    @pytest.mark.it("✅  format_skip_take_options Should convert page 1 and size to offset 0")
    def test_format_skip_take_options_first_page_zero_offset(self) -> None:
        paging_options = {"skip": 1, "take": 10}
        result = PaginationUtils.format_skip_take_options(paging_options)
        assert result["skip"] == 0
        assert result["take"] == 10

    @pytest.mark.it(
        "✅  format_skip_take_options Should compute offset = (page-1)*size for page > 1"
    )
    def test_format_skip_take_options_page_two(self) -> None:
        paging_options = {"skip": 2, "take": 10}
        result = PaginationUtils.format_skip_take_options(paging_options)
        assert result["skip"] == 10
        assert result["take"] == 10

    @pytest.mark.it("✅  format_skip_take_options Should handle values wrapped with .default")
    def test_format_skip_take_options_handles_default_wrapped_values(self) -> None:
        class V:
            def __init__(self, default: int) -> None:
                self.default = default

        paging_options = {"skip": V(3), "take": V(5)}
        result = PaginationUtils.format_skip_take_options(paging_options)
        assert result["skip"] == (3 - 1) * 5
        assert result["take"] == 5

    @pytest.mark.it("✅  format_skip_take_options Should accept numeric strings and cast to int")
    def test_format_skip_take_options_accepts_string_numbers(self) -> None:
        paging_options = {"skip": "4", "take": "3"}
        result = PaginationUtils.format_skip_take_options(paging_options)
        assert result["skip"] == (4 - 1) * 3
        assert result["take"] == 3

    @pytest.mark.it("✅  select_columns should map existing entity attributes into select")
    def test_select_columns_success_maps_attributes(self) -> None:
        paging_options: dict = {}
        selected_columns = ["name", "age"]

        PaginationUtils.select_columns(selected_columns, DummyQuery, User, paging_options)

        assert "select" in paging_options
        assert len(paging_options["select"]) == 2
        select_str = ",".join(map(str, paging_options["select"]))
        assert "name" in select_str
        assert "age" in select_str

    @pytest.mark.it("❌  select_columns should raise BadRequestException for any invalid column")
    def test_select_columns_invalid_raises(self) -> None:
        paging_options: dict = {}
        selected_columns = ["unknown"]

        with pytest.raises(BadRequestException) as excinfo:
            PaginationUtils.select_columns(selected_columns, DummyQuery, User, paging_options)

        assert "Invalid columns" in str(excinfo.value)

    @pytest.mark.it(
        "✅  select_columns should add required fields from Schema when selected is empty"
    )
    def test_select_columns_empty_adds_required_from_schema(self) -> None:
        class RequiredCols(BaseModel):
            name: str  # required

        paging_options: dict = {}
        selected_columns: list[str] = []

        PaginationUtils.select_columns(selected_columns, RequiredCols, User, paging_options)

        assert "select" in paging_options
        select_str = ",".join(map(str, paging_options["select"]))
        assert "name" in select_str

    @pytest.mark.it("✅  select_columns should deduplicate selected columns")
    def test_select_columns_deduplicates(self) -> None:
        paging_options: dict = {}
        selected_columns = ["name", "name", "age", "age"]

        PaginationUtils.select_columns(selected_columns, DummyQuery, User, paging_options)

        assert "select" in paging_options
        assert len(paging_options["select"]) == 2
        select_str = ",".join(map(str, paging_options["select"]))
        assert "name" in select_str
        assert "age" in select_str

    @pytest.mark.it("✅  select_columns should set relations when a relationship field is selected")
    def test_select_columns_sets_relations_when_relationship_selected(self) -> None:
        class Cols(BaseModel):
            personal_data: str | None = None

        paging_options: dict = {}
        selected_columns = ["personal_data"]

        PaginationUtils.select_columns(selected_columns, Cols, User, paging_options)

        assert "relations" in paging_options
        assert paging_options["relations"] == ["personal_data"]
        assert "select" not in paging_options

# ruff: noqa: PLR2004

import pytest
from pydantic import BaseModel

from fastgear.types.http_exceptions import BadRequestException
from fastgear.utils import PaginationUtils
from tests.fixtures.utils.pagination_utils_fixtures import (  # noqa: F401
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

    @pytest.mark.it("✅  validate_columns should return True for empty list")
    def test_validate_columns_empty(self) -> None:
        assert PaginationUtils.validate_columns([], DummyQuery) is True

    @pytest.mark.it("✅  validate_columns should return True when all columns are valid")
    def test_validate_columns_all_valid(self) -> None:
        assert PaginationUtils.validate_columns(["name", "age"], DummyQuery) is True

    @pytest.mark.it("❌  validate_columns should return False when any column is invalid")
    def test_validate_columns_invalid(self) -> None:
        assert PaginationUtils.validate_columns(["name", "nonexistent"], DummyQuery) is False

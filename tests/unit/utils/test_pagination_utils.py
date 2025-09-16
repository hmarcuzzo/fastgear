import pytest

from fastgear.types.http_exceptions import BadRequestException
from fastgear.utils.pagination_utils import PaginationUtils
from tests.fixtures.utils.pagination_utils_fixtures import (  # noqa: F401
    DummyQuery,
    User,
    pagination_utils,
)


@pytest.mark.describe("🧪  PaginationUtils")
class TestPaginationUtils:
    @pytest.mark.it("✅  Should build pagination options with default sort and search")
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

    @pytest.mark.it("✅  Should build pagination options with provided sort and search")
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

    @pytest.mark.it("✅  Should remove duplicate sort and search parameters")
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

    @pytest.mark.it("❌  Should raise BadRequestException for invalid sort format")
    def test_build_pagination_options_invalid_sort_raises(
        self, pagination_utils: PaginationUtils
    ) -> None:
        sort = ["invalid:ASC"]
        with pytest.raises(BadRequestException):
            pagination_utils.build_pagination_options(1, 10, None, sort, DummyQuery, DummyQuery)

    @pytest.mark.it("❌  Should raise BadRequestException for invalid search format")
    def test_build_pagination_options_invalid_search_raises(
        self, pagination_utils: PaginationUtils
    ) -> None:
        search = ["invalid:foo"]
        with pytest.raises(BadRequestException):
            pagination_utils.build_pagination_options(1, 10, search, None, DummyQuery, DummyQuery)

    @pytest.mark.it("✅  Should return formatted paging data without sort/search/columns")
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
        assert result["take"] == 10  # noqa: PLR2004
        assert "relations" not in result
        assert "select" not in result
        assert result.get("order_by") == []
        assert result.get("where") == []

    @pytest.mark.it("✅  Should build where clause when search_all is provided")
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

    @pytest.mark.it("✅  Should not raise when no blocked attributes are present")
    def test_assert_no_blocked_attributes_allows_when_none(self) -> None:
        from fastgear.utils.pagination_utils import PaginationUtils

        PaginationUtils.assert_no_blocked_attributes(["search", "sort"], None, None, None, None)

    @pytest.mark.it("❌  Should raise BadRequestException when blocked attributes are used")
    def test_assert_no_blocked_attributes_raises(self) -> None:
        from fastgear.utils.pagination_utils import PaginationUtils

        blocked_attrs = ["search", "columns"]
        search = ["name:john"]
        columns = ["id"]

        with pytest.raises(BadRequestException) as excinfo:
            PaginationUtils.assert_no_blocked_attributes(blocked_attrs, search, None, columns, None)

        assert excinfo.value.loc == ["search", "columns"]

    @pytest.mark.it(
        "✅  Should return True when assert_search_param_convertible receives a valid value"
    )
    def test_assert_search_param_convertible_valid(self) -> None:
        from fastgear.utils.pagination_utils import PaginationUtils

        search_param = {"field": "age", "value": "30"}
        assert PaginationUtils.assert_search_param_convertible(DummyQuery, search_param) is True

    @pytest.mark.it(
        "❌  Should raise BadRequestException when assert_search_param_convertible receives an invalid value"
    )
    def test_assert_search_param_convertible_invalid_raises(self) -> None:
        from fastgear.utils.pagination_utils import PaginationUtils

        search_param = {"field": "age", "value": "not_an_int"}
        with pytest.raises(BadRequestException):
            PaginationUtils.assert_search_param_convertible(DummyQuery, search_param)

    @pytest.mark.it("✅  _is_list_type_hint should correctly detect list type hints")
    @pytest.mark.parametrize(
        ("type_hint", "expected"),
        [(list[str], True), (list[int], True), (int, False), (list[str] | None, False)],
        ids=["list of str", "list of int", "int", "optional list"],
    )
    def test_is_list_type_hint_parametrized(
        self, pagination_utils: PaginationUtils, type_hint, expected
    ) -> None:
        from fastgear.utils.pagination_utils import PaginationUtils

        assert PaginationUtils._is_list_type_hint(type_hint) is expected

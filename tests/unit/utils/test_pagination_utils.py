import pytest

from fastgear.types.http_exceptions import BadRequestException
from fastgear.utils.pagination_utils import PaginationUtils
from tests.fixtures.utils.pagination_utils_fixtures import (  # noqa: F401
    DummyQuery,
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

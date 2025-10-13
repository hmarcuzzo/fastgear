import pytest

from fastgear.types.pagination import Pagination, PaginationSearch, PaginationSort
from tests.fixtures.types.pagination_fixtures import (
    valid_pagination,
    valid_search,
    valid_sort,
)


@pytest.mark.describe("🧪  Pagination Types")
class TestPaginationTypes:
    @pytest.mark.it("✅  Should create valid PaginationSearch")
    def test_valid_pagination_search(self, valid_search: dict) -> None:
        search = PaginationSearch(**valid_search)
        assert search["field"] == valid_search["field"]
        assert search["value"] == valid_search["value"]

    @pytest.mark.it("✅  Should create valid PaginationSort")
    def test_valid_pagination_sort(self, valid_sort: dict) -> None:
        sort = PaginationSort(**valid_sort)
        assert sort["field"] == valid_sort["field"]
        assert sort["by"] == valid_sort["by"]

    @pytest.mark.it("✅  Should create valid Pagination with all fields")
    def test_valid_pagination(self, valid_pagination: dict) -> None:
        pagination = Pagination(**valid_pagination)
        assert pagination.skip == (valid_pagination["skip"] - 1) * valid_pagination["take"]
        assert pagination.take == valid_pagination["take"]
        assert len(pagination.sort) == len(valid_pagination["sort"])
        assert len(pagination.search) == len(valid_pagination["search"])

    @pytest.mark.it("✅  Should create valid Pagination with empty lists")
    def test_valid_pagination_empty_lists(self) -> None:
        pagination = Pagination(skip=1, take=10, sort=[], search=[], columns=None)
        assert pagination.skip == 0
        assert pagination.take == 10
        assert pagination.sort == []
        assert pagination.search == []
        assert pagination.columns is None

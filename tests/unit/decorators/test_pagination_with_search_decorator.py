from unittest.mock import Mock

import pytest

import fastgear.decorators.pagination_with_search_decorator as mod
from fastgear.decorators.pagination_with_search_decorator import PaginationWithSearchOptions
from fastgear.types.pagination import Pagination
from tests.fixtures.utils.pagination_utils_fixtures import DummyOrderByQuery, DummyQuery


@pytest.mark.describe("🧪  PaginationWithSearchOptions")
class TestPaginationWithSearchOptions:
    @pytest.mark.it("✅  Should pass arguments to PaginationUtils and return paging data")
    def test_call_passes_arguments_to_pagination_utils(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mock_utils = Mock()
        mock_utils.build_pagination_options.return_value = Pagination(
            skip=5, take=10, sort=[], search=[], columns=None
        )
        mock_utils.assert_no_blocked_attributes = Mock()

        monkeypatch.setattr(mod, "PaginationUtils", lambda: mock_utils)

        opts = PaginationWithSearchOptions(
            columns_query="cols_query",
            find_all_query="find_q",
            order_by_query="order_q",
            block_attributes=["search"],
        )

        result = opts.__call__(
            page=2, size=10, search=["field:value"], sort=["f:by"], columns=None, search_all=None
        )

        mock_utils.assert_no_blocked_attributes.assert_called_once_with(
            opts.block_attributes, ["field:value"], ["f:by"], None, None
        )
        mock_utils.build_pagination_options.assert_called_once_with(
            2, 10, ["field:value"], None, ["f:by"], None, "cols_query", "find_q", "order_q"
        )
        assert result == mock_utils.build_pagination_options.return_value

    @pytest.mark.it("✅  Should initialize correctly with DummyQuery and DummyOrderByQuery")
    def test_init_with_dummyquery_dummyorderbyquery(self):
        options = PaginationWithSearchOptions(
            columns_query=DummyQuery, find_all_query=DummyQuery, order_by_query=DummyOrderByQuery
        )

        assert options.columns_query is DummyQuery
        assert options.find_all_query is DummyQuery
        assert options.order_by_query is DummyOrderByQuery

        result = options.__call__(
            page=1, size=5, search=["name:john", "personal_data__address:street"]
        )

        assert {"field": "personal_data__address", "value": "street"} in result.search
        assert len(result.search) == 2

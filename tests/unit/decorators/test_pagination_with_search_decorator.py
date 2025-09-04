from unittest.mock import Mock

import pytest

import fastgear.decorators.pagination_with_search_decorator as mod
from fastgear.decorators.pagination_with_search_decorator import PaginationWithSearchOptions


@pytest.mark.describe("🧪  PaginationWithSearchOptions")
class TestPaginationWithSearchOptions:
    @pytest.mark.it("✅  Should pass arguments to PaginationUtils and return paging data")
    def test_call_passes_arguments_to_pagination_utils(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mock_utils = Mock()
        mock_utils.generate_paging_parameters.return_value = {"skip": 5, "take": 10}
        mock_utils.get_paging_data.return_value = {"data": "ok"}

        monkeypatch.setattr(mod, "PaginationUtils", lambda: mock_utils)

        opts = PaginationWithSearchOptions(
            entity="EntityX",
            columns_query="cols_query",
            find_all_query="find_q",
            order_by_query="order_q",
            block_attributes=["search"],
        )

        result = opts.__call__(
            page=2, size=10, search=["field:value"], sort=["f:by"], columns=None, search_all=None
        )

        mock_utils.validate_block_attributes.assert_called_once_with(
            opts.block_attributes, ["field:value"], ["f:by"], None, None
        )
        mock_utils.generate_paging_parameters.assert_called_once_with(
            2, 10, ["field:value"], ["f:by"], "find_q", "order_q"
        )
        mock_utils.get_paging_data.assert_called_once_with(
            "EntityX",
            mock_utils.generate_paging_parameters.return_value,
            [],
            None,
            "cols_query",
            "find_q",
        )
        assert result == mock_utils.get_paging_data.return_value

    @pytest.mark.it("✅  Should forward provided columns to get_paging_data")
    def test_columns_provided_are_forwarded(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_utils = Mock()
        mock_utils.generate_paging_parameters.return_value = {"skip": 0, "take": 5}
        mock_utils.get_paging_data.return_value = {"items": []}

        monkeypatch.setattr(mod, "PaginationUtils", lambda: mock_utils)

        opts = PaginationWithSearchOptions(
            entity="E",
            columns_query="cols",
            find_all_query=None,
            order_by_query=None,
            block_attributes=[],
        )

        cols = ["id", "name"]
        _ = opts.__call__(page=1, size=5, search=None, sort=None, columns=cols, search_all="x")

        mock_utils.get_paging_data.assert_called_once_with(
            "E", mock_utils.generate_paging_parameters.return_value, cols, "x", "cols", None
        )

    @pytest.mark.it(
        "✅  Should convert columns=None to an empty list before calling get_paging_data"
    )
    def test_columns_none_converted_to_empty_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_utils = Mock()
        mock_utils.generate_paging_parameters.return_value = {"skip": 1, "take": 2}
        mock_utils.get_paging_data.return_value = {"ok": True}

        monkeypatch.setattr(mod, "PaginationUtils", lambda: mock_utils)

        opts = PaginationWithSearchOptions(
            entity="Ent",
            columns_query="c",
            find_all_query=None,
            order_by_query=None,
            block_attributes=None,
        )

        res = opts.__call__(page=1, size=2, search=None, sort=None, columns=None, search_all=None)

        mock_utils.get_paging_data.assert_called_once_with(
            "Ent", mock_utils.generate_paging_parameters.return_value, [], None, "c", None
        )
        assert res == mock_utils.get_paging_data.return_value

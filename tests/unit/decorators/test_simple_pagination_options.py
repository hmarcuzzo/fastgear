from unittest.mock import Mock

import pytest

import fastgear.decorators.simple_pagination_decorator as mod
from fastgear.decorators.simple_pagination_decorator import SimplePaginationOptions
from fastgear.types.custom_pages import custom_page_query, custom_size_query
from fastgear.types.find_many_options import FindManyOptions


class TestSimplePaginationOptions:
    def setup_method(self):
        self.paginator = SimplePaginationOptions()

    @pytest.mark.it("✅  Should return default pagination values when no parameters are provided")
    def test_default_values(self, monkeypatch: pytest.MonkeyPatch):
        page_default = int(custom_page_query.default)
        size_default = int(custom_size_query.default)
        expected = {"skip": (page_default - 1) * size_default, "take": size_default}

        mock_fn = Mock(return_value=expected)
        monkeypatch.setattr(mod.PaginationUtils, "format_skip_take_options", mock_fn)

        result = self.paginator()

        self._assert_pagination_values(mock_fn, expected, result, page_default, size_default)

    @pytest.mark.it(
        "✅  Should return correct pagination values when custom page and size are provided"
    )
    @pytest.mark.parametrize(("page", "size"), [(1, 10), (2, 25), (5, 100)])
    def test_custom_values(self, page: int, size: int, monkeypatch: pytest.MonkeyPatch):
        expected = {"skip": (page - 1) * size, "take": size}

        mock_fn = Mock(return_value=expected)
        monkeypatch.setattr(mod.PaginationUtils, "format_skip_take_options", mock_fn)

        result = self.paginator(page=page, size=size)

        self._assert_pagination_values(mock_fn, expected, result, page, size)

    @pytest.mark.it("❌  Should fail when page or size is not an integer")
    @pytest.mark.parametrize(("page", "size"), [(None, 10), (1, None)])
    def test_invalid_types(self, page: int | None, size: int | None):
        with pytest.raises((TypeError, ValueError)):
            self.paginator(page=page, size=size)

    @staticmethod
    def _assert_pagination_values(
        mock_fn: Mock, expected: dict, result: FindManyOptions, page: int, size: int
    ) -> None:
        assert result == expected
        mock_fn.assert_called_once()
        passed_pagination = mock_fn.call_args[0][0]
        assert getattr(passed_pagination["skip"], "default", passed_pagination["skip"]) == page
        assert getattr(passed_pagination["take"], "default", passed_pagination["take"]) == size

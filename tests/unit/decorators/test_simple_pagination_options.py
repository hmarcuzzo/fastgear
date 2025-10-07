import pytest

from fastgear.decorators.simple_pagination_decorator import SimplePaginationOptions
from fastgear.types.custom_pages import custom_page_query, custom_size_query
from fastgear.types.pagination import Pagination


@pytest.mark.describe("🧪  SimplePaginationOptions")
class TestSimplePaginationOptions:
    def setup_method(self):
        self.paginator = SimplePaginationOptions()

    @pytest.mark.it("✅  Should return default pagination values when no parameters are provided")
    def test_default_values(self):
        page_default = int(custom_page_query.default)
        size_default = int(custom_size_query.default)
        expected = Pagination(
            skip=page_default, take=size_default, sort=[], search=[], columns=None
        )

        result = self.paginator()

        self._assert_pagination_values(expected, result, page_default, size_default)

    @pytest.mark.it(
        "✅  Should return correct pagination values when custom page and size are provided"
    )
    @pytest.mark.parametrize(("page", "size"), [(1, 10), (2, 25), (5, 100)])
    def test_custom_values(self, page: int, size: int, monkeypatch: pytest.MonkeyPatch):
        expected = Pagination(skip=page, take=size, sort=[], search=[], columns=None)

        result = self.paginator(page=page, size=size)

        self._assert_pagination_values(expected, result, page, size)

    @pytest.mark.it("❌  Should fail when page or size is not an integer")
    @pytest.mark.parametrize(("page", "size"), [(None, 10), (1, None)])
    def test_invalid_types(self, page: int | None, size: int | None):
        with pytest.raises(TypeError):
            self.paginator(page=page, size=size)

    @staticmethod
    def _assert_pagination_values(
        expected: Pagination, result: Pagination, page: int, size: int
    ) -> None:
        assert result == expected
        assert getattr(result.skip, "default", result.skip) == (page - 1) * size
        assert getattr(result.take, "default", result.take) == size

import pytest

from fastgear.decorators.simple_pagination_decorator import SimplePaginationOptions
from fastgear.types.custom_pages import custom_page_query, custom_size_query


class TestSimplePaginationOptions:
    def setup_method(self):
        self.paginator = SimplePaginationOptions()

    @pytest.mark.it("✅ Should return default pagination values when no parameters are provided")
    def test_default_values(self):
        result = self.paginator()

        self._assert_pagination_values(
            result, int(custom_page_query.default), int(custom_size_query.default)
        )

    @pytest.mark.it(
        "✅ Should return correct pagination values when custom page and size are provided"
    )
    @pytest.mark.parametrize(("page", "size"), [(1, 10), (2, 25), (5, 100)])
    def test_custom_values(self, page: int, size: int):
        result = self.paginator(page=page, size=size)

        self._assert_pagination_values(result, page, size)

    @pytest.mark.it("❌ Should fail when page or size is not an integer")
    @pytest.mark.parametrize(("page", "size"), [(None, 10), (1, None)])
    def test_invalid_types(self, page: int | None, size: int | None):
        with pytest.raises((TypeError, ValueError)):
            self.paginator(page=page, size=size)

    @staticmethod
    def _assert_pagination_values(result: dict, skip: int, take: int) -> None:
        assert type(result) is dict
        assert "skip" in result
        assert "take" in result

        expected_skip = (skip - 1) * take
        expected_take = take
        assert result["skip"] == expected_skip
        assert result["take"] == expected_take

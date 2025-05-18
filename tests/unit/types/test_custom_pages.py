import pytest
from fastapi_pagination.links.bases import Links
from pydantic import BaseModel

from fastgear.types.custom_pages import Page, custom_page_query, custom_size_query
from tests.fixtures.types.custom_pages_fixtures import (  # noqa: F401
    TestItem,
    test_items,
    valid_links,
    valid_page_params,
)


@pytest.mark.describe("🧪  CustomPages")
class TestCustomPages:
    @pytest.mark.it("✅  Should have correct page query parameters")
    def test_page_query_params(self) -> None:
        class TestModel(BaseModel):
            page: int = custom_page_query

        model = TestModel()
        assert model.page == 1

        with pytest.raises(ValueError, match="Input should be greater than or equal to 1"):
            TestModel(page=0)

        model = TestModel(page=1)
        assert model.page == 1

    @pytest.mark.it("✅  Should have correct size query parameters")
    def test_size_query_params(self) -> None:
        class TestModel(BaseModel):
            size: int = custom_size_query

        model = TestModel()
        assert model.size == 10  # noqa: PLR2004

        with pytest.raises(ValueError, match="Input should be greater than or equal to 1"):
            TestModel(size=0)

        with pytest.raises(ValueError, match="Input should be less than or equal to 100"):
            TestModel(size=101)

        model = TestModel(size=1)
        assert model.size == 1
        model = TestModel(size=100)
        assert model.size == 100  # noqa: PLR2004

    @pytest.mark.it("✅  Should create a page with correct parameters")
    def test_page_creation(
        self, test_items: list[TestItem], valid_links: Links, valid_page_params: dict
    ) -> None:
        page = Page(items=test_items, links=valid_links, **valid_page_params)

        assert page.items == test_items
        assert page.total == valid_page_params["total"]
        assert page.page == valid_page_params["page"]
        assert page.size == valid_page_params["size"]

    @pytest.mark.it("✅  Should validate page number")
    def test_page_number_validation(self, test_items: list[TestItem], valid_links: Links) -> None:
        with pytest.raises(ValueError, match="Input should be greater than or equal to 1"):
            Page(items=test_items, total=1, page=0, size=10, links=valid_links)

    @pytest.mark.it("❌  Should fail when items is not a list")
    def test_invalid_items_type(self, valid_links: Links, valid_page_params: dict) -> None:
        with pytest.raises(ValueError, match="Input should be an instance of Sequence"):
            Page(
                items=TestItem(id=1),  # Should be a list
                links=valid_links,
                **valid_page_params,
            )

    @pytest.mark.it("❌  Should fail when total is negative")
    def test_negative_total(self, test_items: list[TestItem], valid_links: Links) -> None:
        with pytest.raises(ValueError, match="Input should be greater than or equal to 0"):
            Page(items=test_items, total=-1, page=1, size=10, links=valid_links)

    @pytest.mark.it("❌  Should fail when links is missing")
    def test_missing_links(self, test_items: list[TestItem], valid_page_params: dict) -> None:
        with pytest.raises(RuntimeError, match="request context var must be set"):
            Page(items=test_items, **valid_page_params)

    @pytest.mark.it("❌  Should fail when links.self is missing")
    def test_missing_links_self(self, test_items: list[TestItem], valid_page_params: dict) -> None:
        with pytest.raises(
            ValueError, match="1 validation error for Links\nself\n  Field required"
        ):
            Page(
                items=test_items,
                links=Links(first=None, next=None, prev=None, last=None),
                **valid_page_params,
            )

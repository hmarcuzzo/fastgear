import pytest
from fastapi_pagination.links.bases import Links
from pydantic import BaseModel


class ItemFixture(BaseModel):
    id: int
    name: str = "Test Item"


@pytest.fixture
def test_items() -> list[ItemFixture]:
    return [ItemFixture(id=1, name="Test 1"), ItemFixture(id=2, name="Test 2")]


@pytest.fixture
def valid_links() -> Links:
    return Links(self="http://test.com?page=1&size=10", first=None, next=None, prev=None, last=None)


@pytest.fixture
def valid_page_params() -> dict:
    return {"total": 2, "page": 1, "size": 10}

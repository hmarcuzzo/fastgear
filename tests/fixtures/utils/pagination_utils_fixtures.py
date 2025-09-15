import pytest
from pydantic import BaseModel, Field

from fastgear.utils import PaginationUtils


class DummyQuery(BaseModel):
    name: str | None = Field(default=None)
    age: int | None = Field(default=None)


@pytest.fixture
def pagination_utils() -> PaginationUtils:
    return PaginationUtils()

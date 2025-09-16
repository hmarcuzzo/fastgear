import pytest
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String

from fastgear.common.database.sqlalchemy.base import Base
from fastgear.utils import PaginationUtils


class DummyQuery(BaseModel):
    name: str | None = Field(default=None)
    age: int | None = Field(default=None)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)


@pytest.fixture
def pagination_utils() -> PaginationUtils:
    return PaginationUtils()

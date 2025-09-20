from typing import Annotated

import pytest
from pydantic import BaseModel, StringConstraints
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import declarative_base, relationship

from fastgear.constants import regex
from fastgear.utils import PaginationUtils

TestBase = declarative_base()


class User(TestBase):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)

    personal_data = relationship(
        "PersonalData", back_populates="user", cascade="all, delete-orphan"
    )


class PersonalData(TestBase):
    __tablename__ = "personal_data"
    id = Column(Integer, primary_key=True)
    address = Column(String)
    phone_number = Column(String)

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="personal_data", lazy="selectin")


class DummyQuery(BaseModel):
    name: str = None
    age: int = None
    personal_data__address: str = None


class DummyOrderByQuery(BaseModel):
    name: Annotated[str, StringConstraints(pattern=regex.ORDER_BY_QUERY)] | None
    personal_data__address: Annotated[str, StringConstraints(pattern=regex.ORDER_BY_QUERY)] | None


@pytest.fixture
def pagination_utils() -> PaginationUtils:
    return PaginationUtils()

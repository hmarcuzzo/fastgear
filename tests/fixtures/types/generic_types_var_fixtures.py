from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase


class TestBase(DeclarativeBase):
    pass


class TestEntity(TestBase):
    __tablename__ = "test_entity"

    id = Column(Integer, primary_key=True)
    name = Column(String)


class TestModel(BaseModel):
    id: int
    name: str

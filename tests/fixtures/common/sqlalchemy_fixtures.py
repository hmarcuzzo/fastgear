from collections.abc import Iterator

import pytest
from pydantic import BaseModel
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from fastgear.common.database.sqlalchemy.session import db_session


class UpdateSchema(BaseModel):
    name: str | None = None
    age: int | None = None


@pytest.fixture
def mock_db() -> object:
    sentinel = object()
    token = db_session.set(sentinel)
    try:
        yield sentinel
    finally:
        db_session.reset(token)


@pytest.fixture
def engine() -> Iterator[Engine]:
    engine = create_engine("sqlite:///:memory:", future=True)
    try:
        yield engine
    finally:
        engine.dispose()

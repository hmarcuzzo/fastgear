import pytest

from fastgear.common.database.sqlalchemy.session import db_session


@pytest.fixture
def mock_db() -> object:
    sentinel = object()
    token = db_session.set(sentinel)
    try:
        yield sentinel
    finally:
        db_session.reset(token)

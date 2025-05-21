import pytest
from sqlalchemy import Boolean, Column, Integer, String


@pytest.fixture
def test_columns() -> tuple[Column, Column, Column]:
    id_column = Column("id", Integer)
    name_column = Column("name", String)
    active_column = Column("active", Boolean)
    return id_column, name_column, active_column


@pytest.fixture
def base_options() -> dict:
    return {
        "select": ["id", "name"],
        "order_by": "name",
        "relations": ["user", "profile"],
        "having": [True],
        "skip": 10,
        "take": 20,
    }

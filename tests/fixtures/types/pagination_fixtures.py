import pytest


@pytest.fixture
def valid_search() -> dict:
    return {"field": "name", "value": "test"}


@pytest.fixture
def valid_sort() -> dict:
    return {"field": "created_at", "by": "desc"}


@pytest.fixture
def valid_pagination() -> dict:
    return {
        "skip": 0,
        "take": 10,
        "sort": [{"field": "created_at", "by": "desc"}, {"field": "name", "by": "asc"}],
        "search": [
            {"field": "name", "value": "test"},
            {"field": "email", "value": "test@example.com"},
        ],
    }

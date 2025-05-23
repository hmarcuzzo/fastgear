import pytest


@pytest.fixture
def basic_update_result() -> dict:
    return {"raw": {"id": 1}, "affected": 1, "generated_maps": None}


@pytest.fixture
def full_update_result() -> dict:
    return {
        "raw": {"id": 1, "name": "test", "email": "test@example.com"},
        "affected": 3,
        "generated_maps": [
            {"id": 1, "name": "test1"},
            {"id": 2, "name": "test2"},
            {"id": 3, "name": "test3"},
        ],
    }


@pytest.fixture
def empty_update_result() -> dict:
    return {"raw": {}, "affected": 0, "generated_maps": []}

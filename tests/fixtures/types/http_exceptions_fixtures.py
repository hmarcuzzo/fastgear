import pytest


@pytest.fixture
def basic_exception_data() -> dict:
    return {"msg": "Test error message"}


@pytest.fixture
def full_exception_data() -> dict:
    return {"msg": "Validation error", "loc": ["user", "email"], "_type": "value_error.email"}


@pytest.fixture
def empty_message_data() -> dict:
    return {"msg": ""}

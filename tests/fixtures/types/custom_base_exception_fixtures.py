"""Fixtures for CustomBaseException testing."""

import pytest


@pytest.fixture
def basic_exception_data() -> dict:
    """Fixture that provides basic exception data.

    Returns:
        dict: Basic exception data with message only.
    """
    return {"msg": "Test error message", "loc": None, "_type": None}


@pytest.fixture
def full_exception_data() -> dict:
    """Fixture that provides complete exception data.

    Returns:
        dict: Complete exception data with message, location, and type.
    """
    return {"msg": "Validation error", "loc": ["user", "email"], "_type": "value_error.email"}


@pytest.fixture
def empty_message_data() -> dict:
    """Fixture that provides exception data with empty message.

    Returns:
        dict: Exception data with empty message.
    """
    return {"msg": "", "loc": None, "_type": None}

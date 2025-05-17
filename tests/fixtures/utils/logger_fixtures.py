from datetime import datetime, timezone
from typing import cast

import pytest
from loguru import Record


@pytest.fixture
def mock_record() -> dict:
    """Fixture that provides a basic mock record for logger testing.

    Returns:
        dict: A mock record with basic fields.
    """
    return {
        "time": datetime(2024, 3, 20, 10, 30, 45, 123456, tzinfo=timezone.utc),
        "extra": {"name": "test_module"},
        "module": "test_module",
        "level": type("Level", (), {"name": "INFO"}),
        "message": "Test message",
    }


@pytest.fixture
def mock_record_without_name() -> Record:
    """Fixture that provides a mock record without name in extra.

    Returns:
        Record: A mock record without name in extra field.
    """
    return cast(
        Record,
        {
            "time": datetime(2024, 3, 20, 10, 30, 45, 123456, tzinfo=timezone.utc),
            "extra": {},
            "module": "test_module",
            "level": type("Level", (), {"name": "ERROR"}),
            "message": "Error message",
        },
    )


@pytest.fixture
def log_levels() -> list[str]:
    """Fixture that provides a list of log levels.

    Returns:
        list[str]: List of standard log levels.
    """
    return ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

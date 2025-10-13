import sys
from unittest.mock import patch

import pytest
from loguru import logger

from fastgear.utils.logger_utils import LoggerUtils
from tests.fixtures.utils.logger_fixtures import (
    log_levels,
    mock_record,
    mock_record_without_name,
)


@pytest.mark.describe("🧪  LoggerUtils")
class TestLoggerUtils:
    @pytest.mark.it("✅  Should configure logging with correct level")
    def test_configure_logging_level(self):
        with patch.object(logger, "remove") as mock_remove, patch.object(logger, "add") as mock_add:
            LoggerUtils.configure_logging("INFO")

            mock_remove.assert_called_once()
            mock_add.assert_called_once_with(
                sys.stdout, level="INFO", format=LoggerUtils._formatter, enqueue=True
            )

    @pytest.mark.it("✅  Should format log record correctly")
    def test_formatter(self, mock_record: dict) -> None:
        formatted = LoggerUtils._formatter(mock_record)  # type: ignore
        expected = "2024-03-20 10:30:45.123 - test_module - [<level>INFO</level>]: Test message\n"
        assert formatted == expected

    @pytest.mark.it("✅  Should use module name when name is not in extra")
    def test_formatter_without_name(self, mock_record_without_name: dict) -> None:
        formatted = LoggerUtils._formatter(mock_record_without_name)  # type: ignore
        expected = "2024-03-20 10:30:45.123 - test_module - [<level>ERROR</level>]: Error message\n"
        assert formatted == expected

    @pytest.mark.it("✅  Should handle different log levels")
    def test_formatter_different_levels(self, mock_record: dict, log_levels: list[str]) -> None:
        for level in log_levels:
            # Create a new record with the current level
            current_record = mock_record.copy()
            current_record["level"] = type("Level", (), {"name": level})
            current_record["message"] = f"{level} message"

            formatted = LoggerUtils._formatter(current_record)  # type: ignore
            expected = f"2024-03-20 10:30:45.123 - test_module - [<level>{level}</level>]: {level} message\n"
            assert formatted == expected

import sys
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from loguru import logger

from fastgear.utils.logger_utils import LoggerUtils


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
    def test_formatter(self):
        mock_record = {
            "time": datetime(2024, 3, 20, 10, 30, 45, 123456, tzinfo=timezone.utc),
            "extra": {"name": "test_module"},
            "module": "test_module",
            "level": type("Level", (), {"name": "INFO"}),
            "message": "Test message",
        }

        formatted = LoggerUtils._formatter(mock_record)
        expected = "2024-03-20 10:30:45.123 - test_module - [<level>INFO</level>]: Test message\n"
        assert formatted == expected

    @pytest.mark.it("✅  Should use module name when name is not in extra")
    def test_formatter_without_name(self):
        mock_record = {
            "time": datetime(2024, 3, 20, 10, 30, 45, 123456, tzinfo=timezone.utc),
            "extra": {},
            "module": "test_module",
            "level": type("Level", (), {"name": "ERROR"}),
            "message": "Error message",
        }

        formatted = LoggerUtils._formatter(mock_record)
        expected = "2024-03-20 10:30:45.123 - test_module - [<level>ERROR</level>]: Error message\n"
        assert formatted == expected

    @pytest.mark.it("✅  Should handle different log levels")
    def test_formatter_different_levels(self):
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in levels:
            mock_record = {
                "time": datetime(2024, 3, 20, 10, 30, 45, 123456, tzinfo=timezone.utc),
                "extra": {"name": "test_module"},
                "module": "test_module",
                "level": type("Level", (), {"name": level}),
                "message": f"{level} message",
            }

            formatted = LoggerUtils._formatter(mock_record)
            expected = f"2024-03-20 10:30:45.123 - test_module - [<level>{level}</level>]: {level} message\n"
            assert formatted == expected

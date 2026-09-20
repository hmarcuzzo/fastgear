import io
import json
import logging
from collections.abc import Callable

import pytest
import structlog

from fastgear.utils.logger_utils import LoggerUtils
from tests.fixtures.utils.logger_fixtures import log_levels, reset_logging, stdout_capture


@pytest.mark.describe("🧪  LoggerUtils")
class TestLoggerUtils:
    @pytest.mark.it("✅  Should configure the root logger with a single structlog handler")
    def test_configure_logging_handler(self, stdout_capture: Callable[..., io.StringIO]) -> None:
        stdout = stdout_capture()

        LoggerUtils.configure_logging("INFO")

        root_logger = logging.getLogger()
        assert len(root_logger.handlers) == 1
        assert root_logger.level == logging.INFO

        handler = root_logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert handler.stream is stdout
        assert isinstance(handler.formatter, structlog.stdlib.ProcessorFormatter)

    @pytest.mark.it("✅  Should replace previously installed handlers")
    def test_configure_logging_replaces_handlers(
        self, stdout_capture: Callable[..., io.StringIO]
    ) -> None:
        stdout_capture()
        logging.getLogger().addHandler(logging.NullHandler())

        LoggerUtils.configure_logging("INFO")

        assert len(logging.getLogger().handlers) == 1

    @pytest.mark.it("✅  Should accept the level as a name or as a logging constant")
    def test_configure_logging_level(
        self, stdout_capture: Callable[..., io.StringIO], log_levels: list[str]
    ) -> None:
        stdout_capture()

        for level in log_levels:
            LoggerUtils.configure_logging(level)
            assert logging.getLogger().level == logging.getLevelName(level)

            LoggerUtils.configure_logging(logging.getLevelName(level))
            assert logging.getLogger().level == logging.getLevelName(level)

    @pytest.mark.it("❌  Should raise when the level name is unknown")
    def test_configure_logging_unknown_level(
        self, stdout_capture: Callable[..., io.StringIO]
    ) -> None:
        stdout_capture()

        with pytest.raises(ValueError, match="Unknown log level: NOT_A_LEVEL"):
            LoggerUtils.configure_logging("NOT_A_LEVEL")

    @pytest.mark.it("✅  Should render structured logs as JSON when json_logs is enabled")
    def test_json_rendering(self, stdout_capture: Callable[..., io.StringIO]) -> None:
        stdout = stdout_capture()
        LoggerUtils.configure_logging("INFO", json_logs=True)

        LoggerUtils.get_logger("test_module").info("Test message", user_id=1)

        record = json.loads(stdout.getvalue())
        assert record["event"] == "Test message"
        assert record["level"] == "info"
        assert record["logger"] == "test_module"
        assert record["user_id"] == 1
        assert "timestamp" in record

    @pytest.mark.it("✅  Should render human-readable logs when json_logs is disabled")
    def test_console_rendering(self, stdout_capture: Callable[..., io.StringIO]) -> None:
        # A non-terminal stream keeps the console renderer from emitting ANSI colour codes.
        stdout = stdout_capture(tty=False)
        LoggerUtils.configure_logging("INFO", json_logs=False)

        LoggerUtils.get_logger("test_module").info("Test message", user_id=1)

        output = stdout.getvalue()
        assert "Test message" in output
        assert "test_module" in output
        assert "user_id=1" in output

    @pytest.mark.it("✅  Should pick the renderer from the stdout stream when json_logs is None")
    def test_renderer_auto_detection(self, stdout_capture: Callable[..., io.StringIO]) -> None:
        terminal_stdout = stdout_capture(tty=True)
        LoggerUtils.configure_logging("INFO")
        LoggerUtils.get_logger("test_module").info("Terminal message")

        assert "Terminal message" in terminal_stdout.getvalue()
        with pytest.raises(json.JSONDecodeError):
            json.loads(terminal_stdout.getvalue())

        piped_stdout = stdout_capture(tty=False)
        LoggerUtils.configure_logging("INFO")
        LoggerUtils.get_logger("test_module").info("Piped message")

        assert json.loads(piped_stdout.getvalue())["event"] == "Piped message"

    @pytest.mark.it("✅  Should not emit records below the configured level")
    def test_level_filtering(self, stdout_capture: Callable[..., io.StringIO]) -> None:
        stdout = stdout_capture()
        LoggerUtils.configure_logging("WARNING", json_logs=True)

        logger = LoggerUtils.get_logger("test_module")
        logger.info("Ignored message")
        logger.warning("Emitted message")

        assert "Ignored message" not in stdout.getvalue()
        assert json.loads(stdout.getvalue())["event"] == "Emitted message"

    @pytest.mark.it("✅  Should render standard library records through the same pipeline")
    def test_stdlib_integration(self, stdout_capture: Callable[..., io.StringIO]) -> None:
        stdout = stdout_capture()
        LoggerUtils.configure_logging("INFO", json_logs=True)

        logging.getLogger("uvicorn.access").info("Foreign %s", "message")

        record = json.loads(stdout.getvalue())
        assert record["event"] == "Foreign message"
        assert record["logger"] == "uvicorn.access"
        assert record["level"] == "info"

    @pytest.mark.it("✅  Should include the traceback of an exception in the JSON output")
    def test_exception_rendering(self, stdout_capture: Callable[..., io.StringIO]) -> None:
        stdout = stdout_capture()
        LoggerUtils.configure_logging("INFO", json_logs=True)

        try:
            raise ValueError("boom")
        except ValueError:
            LoggerUtils.get_logger("test_module").exception("Something failed")

        record = json.loads(stdout.getvalue())
        assert record["event"] == "Something failed"
        assert record["exception"][0]["exc_type"] == "ValueError"
        assert record["exception"][0]["exc_value"] == "boom"

    @pytest.mark.it("✅  Should return a logger bound to the given name")
    def test_get_logger_with_name(self, stdout_capture: Callable[..., io.StringIO]) -> None:
        stdout = stdout_capture()
        LoggerUtils.configure_logging("INFO", json_logs=True)

        LoggerUtils.get_logger("explicit_name").info("Named message")

        assert json.loads(stdout.getvalue())["logger"] == "explicit_name"

    @pytest.mark.it("✅  Should infer the logger name from the caller when none is given")
    def test_get_logger_without_name(self, stdout_capture: Callable[..., io.StringIO]) -> None:
        stdout = stdout_capture()
        LoggerUtils.configure_logging("INFO", json_logs=True)

        LoggerUtils.get_logger().info("Inferred message")

        assert json.loads(stdout.getvalue())["logger"] == __name__

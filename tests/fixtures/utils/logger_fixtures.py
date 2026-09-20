import io
import logging
import sys
from collections.abc import Callable, Generator

import pytest
import structlog


class _InMemoryStdout(io.StringIO):
    def __init__(self, *, tty: bool) -> None:
        super().__init__()
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


@pytest.fixture(autouse=True)
def reset_logging() -> Generator[None]:
    """Fixture that restores structlog and the root logger to their original state.

    Yields:
        None.
    """
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level

    yield

    structlog.reset_defaults()
    root_logger.handlers = original_handlers
    root_logger.setLevel(original_level)


@pytest.fixture
def stdout_capture(monkeypatch: pytest.MonkeyPatch) -> Callable[..., io.StringIO]:
    """Fixture that provides a factory replacing stdout with an in-memory stream.

    The factory is called from the test body rather than patching on setup because pytest resumes
    its own capture at the start of the call phase, which would restore `sys.stdout`.

    Returns:
        Callable[..., io.StringIO]: A factory taking whether the stream reports itself as a
            terminal and returning the in-memory stream that replaced stdout.
    """

    def _replace_stdout(*, tty: bool = True) -> io.StringIO:
        stream = _InMemoryStdout(tty=tty)
        monkeypatch.setattr(sys, "stdout", stream)

        return stream

    return _replace_stdout


@pytest.fixture
def log_levels() -> list[str]:
    """Fixture that provides a list of log levels.

    Returns:
        list[str]: List of standard log levels.
    """
    return ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

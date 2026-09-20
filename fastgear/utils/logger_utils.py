import logging
import sys

import structlog
from structlog.typing import Processor


class LoggerUtils:
    @staticmethod
    def configure_logging(
        level: int | str = logging.INFO, *, json_logs: bool | None = None
    ) -> None:
        """Configures structlog and the standard library logging to share a single output pipeline.

        Every record, whether emitted through structlog or through a third-party library that uses
        the standard `logging` module (uvicorn, sqlalchemy, ...), is rendered by the same processor
        chain and written to stdout.

        Args:
            level (int | str): The minimum level to emit. Accepts either a `logging` constant or
                its name (e.g. `"INFO"`). Defaults to `logging.INFO`.
            json_logs (bool | None): Whether to render the logs as JSON. When None, the renderer is
                chosen automatically: human-readable output when stdout is a terminal, JSON
                otherwise. Defaults to None.

        Returns:
            None.
        """
        level = LoggerUtils._resolve_level(level)
        json_logs = LoggerUtils._should_use_json() if json_logs is None else json_logs

        shared_processors = LoggerUtils._shared_processors(json_logs=json_logs)

        structlog.configure(
            processors=[
                *shared_processors,
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                *LoggerUtils._render_processors(json_logs=json_logs),
            ],
        )

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.addHandler(handler)
        root_logger.setLevel(level)

    @staticmethod
    def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
        """Returns a logger bound to the given name.

        Args:
            name (str | None): The name of the logger, usually `__name__`. When None, structlog
                infers it from the calling module. Defaults to None.

        Returns:
            structlog.stdlib.BoundLogger: The bound logger.
        """
        # An explicit `None` would reach `logging.getLogger` and resolve to the root logger, so the
        # name is only forwarded when it was actually provided.
        if name is None:
            return structlog.stdlib.get_logger()

        return structlog.stdlib.get_logger(name)

    @staticmethod
    def _resolve_level(level: int | str) -> int:
        """Normalizes a log level given as a name or as a `logging` constant into its integer value.

        Args:
            level (int | str): The level to normalize.

        Returns:
            int: The numeric log level.

        Raises:
            ValueError: If the level name is not a known log level.
        """
        if isinstance(level, int):
            return level

        resolved = logging.getLevelName(level.upper())
        if not isinstance(resolved, int):
            raise ValueError(f"Unknown log level: {level}")

        return resolved

    @staticmethod
    def _should_use_json() -> bool:
        """Determines whether the logs should be rendered as JSON based on the stdout stream.

        Returns:
            bool: True when stdout is not a terminal, False otherwise.
        """
        return not sys.stdout.isatty()

    @staticmethod
    def _shared_processors(*, json_logs: bool) -> list[Processor]:
        """Builds the processor chain shared by structlog and standard library records.

        Args:
            json_logs (bool): Whether the logs are rendered as JSON.

        Returns:
            list[Processor]: The shared processors.
        """
        timestamper = (
            structlog.processors.TimeStamper(fmt="iso", utc=True)
            if json_logs
            else structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S.%f")
        )

        return [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
        ]

    @staticmethod
    def _render_processors(*, json_logs: bool) -> list[Processor]:
        """Builds the processors responsible for rendering the log record.

        Args:
            json_logs (bool): Whether the logs are rendered as JSON.

        Returns:
            list[Processor]: The rendering processors.
        """
        if json_logs:
            # ConsoleRenderer formats `exc_info` on its own, the JSON pipeline does not.
            return [structlog.processors.dict_tracebacks, structlog.processors.JSONRenderer()]

        return [structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty())]

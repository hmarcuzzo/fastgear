import sys
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from loguru import Record


class LoggerUtils:
    @staticmethod
    def configure_logging(level: int | str) -> None:
        logger.remove()

        logger.add(sys.stdout, level=level, format=LoggerUtils._formatter, enqueue=True)

    @staticmethod
    def _formatter(record: "Record") -> str:
        ts = record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        who = record["extra"].get("name", record["module"])
        return f"{ts} - {who} - [<level>{record['level'].name}</level>]: {record['message']}\n"

import logging
import sys


class LoggerUtils:
    @staticmethod
    def configure_logging(level: int | str) -> None:
        logger = logging.getLogger()
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter("%(asctime)s - %(name)s - [%(levelname)s]: %(message)s")
            handler.setFormatter(formatter)

            logger.setLevel(level)
            logger.addHandler(handler)

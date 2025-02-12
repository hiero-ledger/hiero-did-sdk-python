import logging
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARN", "ERROR"]

DEFAULT_LOG_LEVEL: LogLevel = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s: %(filename)s: %(message)s"


def configure_logger(logger, log_level: LogLevel | None, log_format: str | None):
    """Helper function to configure SDK logger.

    For log format pattern reference, please see Python docs:
        - https://docs.python.org/3/library/logging.html#formatter-objects
        - https://docs.python.org/3/library/logging.html#logrecord-attributes

    Args:
        logger: Logger instance
        log_level: Log level
        log_format: Log format
    """
    logger.setLevel(log_level or DEFAULT_LOG_LEVEL)

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(log_format or DEFAULT_LOG_FORMAT))

    logger.addHandler(console)

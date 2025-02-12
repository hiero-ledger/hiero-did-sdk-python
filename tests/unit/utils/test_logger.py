import logging
import logging.config
from logging import DEBUG, ERROR, INFO, WARN

import pytest

from hiero_did_sdk_python.utils.logger import configure_logger


def _log_all_levels(logger):
    logger.error("error")
    logger.warning("warning")
    logger.info("info")
    logger.debug("debug")


@pytest.fixture()
def all_expected_error_tuples():
    return [
        (__name__, ERROR, "error"),
        (__name__, WARN, "warning"),
        (__name__, INFO, "info"),
        (__name__, DEBUG, "debug"),
    ]


class TestLogConfigurer:
    @pytest.mark.parametrize(
        ("log_level", "expected_max_level"),
        [(None, INFO), ("DEBUG", DEBUG), ("INFO", INFO), ("WARN", WARN), ("ERROR", ERROR)],
    )
    def test_log_levels(self, log_level, expected_max_level, all_expected_error_tuples, caplog):
        logger = logging.getLogger(__name__)

        configure_logger(logger, log_level, None)

        _log_all_levels(logger)

        max_index = len(all_expected_error_tuples)
        for index, tuple_ in enumerate(all_expected_error_tuples):
            if tuple_[1] == expected_max_level:
                max_index = index
                break

        expected_error_tuples = all_expected_error_tuples[0 : max_index + 1]

        assert caplog.record_tuples == expected_error_tuples

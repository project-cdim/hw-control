# Copyright 2025 NEC Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
#  under the License.

"""This is a test program."""
import logging
import pytest
import app.common.basic_exceptions as exc
import app.common.utils.log as log
import app.common.messages.message as msg
from app.common.settings import settings


def _log_contains(record, level, message) -> bool:
    return next(filter(lambda x: (x[1] == level) and (message in x[2]), record), None) is not None


def test_debug(mocker, caplog):
    """ log test
    """
    mocker.patch.object(settings, 'LOGGING_LEVEL', "DEBUG")
    # LOGGER is generated at load time, so it is forced to be rewritten.
    log.Logger._logger = {}  # pylint: disable=W0212
    log.LOGGER = log.Logger.get_logger()

    log.LOGGER.debug('debug message.')

    assert _log_contains(caplog.record_tuples, logging.DEBUG, "debug message.")

def test_get_logger_continue(mocker, caplog):
    """ log test
    """
    mocker.patch.object(settings, 'LOGGING_LEVEL', "DEBUG")
    # LOGGER is generated at load time, so it is forced to be rewritten.
    log.Logger._logger = {}  # pylint: disable=W0212
    log.LOGGER = log.Logger.get_logger()
    log.LOGGER = log.Logger.get_logger()
    log.LOGGER.debug('debug message.')

    assert _log_contains(caplog.record_tuples, logging.DEBUG, "debug message.")

def test_info(caplog):
    """ log test
    """
    log.LOGGER.info(msg.get_log_message(msg.I00003, ['manager_id']))

    assert _log_contains(caplog.record_tuples, logging.INFO,
                         "I00003: manager_id Plugin Call.")


def test_message_error():
    """ log test
    """

    # Catch the exception class that may occur in pytest.
    with pytest.raises(exc.InvalidLogMessageParameterHwControlError) as error:
        log.LOGGER.info(msg.get_log_message(msg.I00001, ['few items']))

    # Verify if it is the expected error class.
    assert error.type == exc.InvalidLogMessageParameterHwControlError


def test_fail_to_get_logger(mocker, caplog):
    """ log test
    """
    mocker.patch.object(settings, 'LOGGING_LEVEL', "bad setting")
    # LOGGER is generated at load time, so it is forced to be rewritten.
    log.Logger._logger = {}  # pylint: disable=W0212

    with pytest.raises(exc.UnexpectedExceptionHwControlError) as error:
        log.LOGGER = log.Logger.get_logger()

    # Verify if it is the expected error class.
    assert error.type == exc.UnexpectedExceptionHwControlError

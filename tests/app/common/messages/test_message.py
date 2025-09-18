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
import app
import app.common.basic_exceptions as exc
import app.common.messages.message as msg


def _log_contains(record, level, message) -> bool:
    return next(filter(lambda x: (x[1] == level) and (message in x[2]), record), None) is not None


def test_info(caplog):
    """log test"""
    app_logger = logging.getLogger(app.__name__)
    app_logger.info(msg.get_log_message(msg.I00003, ["manager_id"]))

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00003: manager_id Plugin Call.")


def test_message_error():
    """log test"""

    # Catch the exception class that may occur in pytest.
    app_logger = logging.getLogger(app.__name__)
    with pytest.raises(exc.InvalidLogMessageParameterHWControlError) as error:
        app_logger.info(msg.get_log_message(msg.I00001, ["few items"]))

    # Verify if it is the expected error class.
    assert error.type == exc.InvalidLogMessageParameterHWControlError

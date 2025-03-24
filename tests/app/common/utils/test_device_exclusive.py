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

"""Unit test module for device_exclusive.py."""

import json
import logging
import threading

import pytest

from tests.app.routers.control import test_util

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.common.utils.device_exclusive import DeviceExclusive  # type: ignore

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestLock:
    """Unit test class for DeviceExclusive.lock"""

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    def test_lock_success(self, caplog):
        """test for DeviceExclusive.lock success case"""

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        device_id = "2b078f92-5ece-48ad-99fc-d7ae87575d7a"

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with caplog.at_level(logging.INFO, logger="LOGGER"):
            result = DeviceExclusive.lock(device_id)

        log_message = json.loads(caplog.records[0].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # test for lock state
        assert result
        assert DeviceExclusive._locks[device_id].locked()  # pylint: disable=W0212

        # test for log
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "INFO"
        assert log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert log_message["message"]["detail"] is None
        assert log_message["message"]["action"] == "acquire lock"
        assert log_message["message"]["target_device"] == device_id

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    def test_lock_error(self, caplog):
        """test for DeviceExclusive.lock error case"""

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        device_id = "2b078f92-5ece-48ad-99fc-d7ae87575d7a"
        _ = DeviceExclusive.lock(device_id)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="LOGGER"):
            result = DeviceExclusive.lock(device_id)

        log_message = json.loads(caplog.records[0].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # test for lock state
        assert not result
        assert DeviceExclusive._locks.get(device_id)  # pylint: disable=W0212

        # test for log
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "WARNING"
        assert log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert log_message["message"]["detail"] is None
        assert log_message["message"]["action"] == "failed to acquire lock"
        assert log_message["message"]["target_device"] == device_id


class TestUnlock:
    """Unit test class for DeviceExclusive.unlock"""

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    def test_unlock_success(self, caplog):
        """test for DeviceExclusive.unlock success case"""

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        device_id = "2b078f92-5ece-48ad-99fc-d7ae87575d7a"
        _ = DeviceExclusive.lock(device_id)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="LOGGER"):
            result = DeviceExclusive.unlock(device_id)

        log_message = json.loads(caplog.records[0].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # test for lock state
        assert result
        assert not DeviceExclusive._locks.get(device_id)  # pylint: disable=W0212

        # test for log
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "INFO"
        assert log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert log_message["message"]["detail"] is None
        assert log_message["message"]["action"] == "release lock"
        assert log_message["message"]["target_device"] == device_id

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    def test_unlock_error(self, caplog):
        """test for DeviceExclusive.unlock error case"""

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        device_id = "2b078f92-5ece-48ad-99fc-d7ae87575d7a"

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="LOGGER"):
            result = DeviceExclusive.unlock(device_id)

        log_message = json.loads(caplog.records[0].getMessage())
        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # test for lock state
        assert not result
        assert not DeviceExclusive._locks.get(device_id)  # pylint: disable=W0212

        # test for log
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"
        assert log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert log_message["message"]["detail"] == "The specified device is not locked."
        assert log_message["message"]["action"] == "failed to release lock"
        assert log_message["message"]["target_device"] == device_id

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    def test_unlock_exception(self, caplog):
        """test for DeviceExclusive.unlock RuntimeError case"""

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        device_id = "2b078f92-5ece-48ad-99fc-d7ae87575d7a"

        DeviceExclusive._locks[device_id] = threading.Lock()  # pylint: disable=W0212
        DeviceExclusive._locks[device_id].acquire(blocking=False)  # pylint: disable=W0212
        DeviceExclusive._locks[device_id].release()  # pylint: disable=W0212

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#

        caplog.clear()
        with caplog.at_level(logging.INFO, logger="LOGGER"):
            result = DeviceExclusive.unlock(device_id)

        log_message_01 = json.loads(caplog.records[0].getMessage())
        log_message_02 = json.loads(caplog.records[1].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # test for lock state
        assert not result
        assert not DeviceExclusive._locks[device_id].locked()  # pylint: disable=W0212

        # test for log
        assert len(caplog.records) == 2

        assert caplog.records[0].levelname == "ERROR"
        assert log_message_01["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert log_message_01["message"]["detail"] is None
        assert log_message_01["message"]["action"] == "exception raised"
        assert log_message_01["message"].get("trace_back") is not None

        assert caplog.records[1].levelname == "ERROR"
        assert log_message_02["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert log_message_02["message"]["detail"] is None
        assert log_message_02["message"]["action"] == "failed to release lock"
        assert log_message_02["message"]["target_device"] == device_id

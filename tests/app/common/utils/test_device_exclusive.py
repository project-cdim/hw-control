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

import logging
import threading

from pytest import LogCaptureFixture

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.common.utils import device_exclusive

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestLock:
    """Unit test class for DeviceExclusive.lock"""

    def test_lock_success(self, caplog: LogCaptureFixture):
        """Test for DeviceExclusive.lock success case.

        Args:
            caplog (LogCaptureFixture):
                The fixture used to capture log records.
        """

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        device_id = "2b078f92-5ece-48ad-99fc-d7ae87575d7a"

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with caplog.at_level(logging.INFO, logger=device_exclusive.__name__):
            result = device_exclusive.DeviceExclusive.lock(device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # test for lock state
        assert result
        assert device_exclusive.DeviceExclusive._locks[device_id].locked()  # pylint: disable=W0212

        # test for log
        assert len(caplog.records) == 1

        # Inspection: Check the lock acquire result log.
        lock_acquire_result_log = caplog.records[0]
        assert lock_acquire_result_log.levelname == "INFO"
        assert lock_acquire_result_log.getMessage() == "Acquire the device lock."
        assert hasattr(
            lock_acquire_result_log, "target_device_id"
        ), "target_device_id should be present in the log record"
        assert getattr(lock_acquire_result_log, "target_device_id") == device_id

    def test_lock_error(self, caplog: LogCaptureFixture):
        """Test for DeviceExclusive.lock error case.

        Args:
            caplog (LogCaptureFixture):
                The fixture used to capture log records.
        """

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        device_id = "2b078f92-5ece-48ad-99fc-d7ae87575d7a"
        _ = device_exclusive.DeviceExclusive.lock(device_id)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=device_exclusive.__name__):
            result = device_exclusive.DeviceExclusive.lock(device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # test for lock state
        assert not result
        assert device_exclusive.DeviceExclusive._locks.get(device_id)  # pylint: disable=W0212

        # test for log
        assert len(caplog.records) == 1

        # Inspection: Check the lock acquire result log.
        lock_acquire_result_log = caplog.records[0]
        assert lock_acquire_result_log.levelname == "WARNING"
        assert lock_acquire_result_log.getMessage() == "Failed to acquire the device lock."

        assert hasattr(
            lock_acquire_result_log, "target_device_id"
        ), "target_device_id should be present in the log record"
        assert getattr(lock_acquire_result_log, "target_device_id") == device_id


class TestUnlock:
    """Unit test class for DeviceExclusive.unlock"""

    def test_unlock_success(self, caplog: LogCaptureFixture):
        """Test for DeviceExclusive.unlock success case.

        Args:
            caplog (LogCaptureFixture):
                The fixture used to capture log records.
        """

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        device_id = "2b078f92-5ece-48ad-99fc-d7ae87575d7a"
        _ = device_exclusive.DeviceExclusive.lock(device_id)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=device_exclusive.__name__):
            result = device_exclusive.DeviceExclusive.unlock(device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # test for lock state
        assert result
        assert not device_exclusive.DeviceExclusive._locks.get(device_id)  # pylint: disable=W0212

        # test for log
        assert len(caplog.records) == 1

        # Inspection: Check the lock release result log.
        lock_release_result_log = caplog.records[0]
        assert lock_release_result_log.levelname == "INFO"

        assert lock_release_result_log.getMessage() == "Released the device lock."

        assert hasattr(
            lock_release_result_log, "target_device_id"
        ), "target_device_id should be present in the log record"
        assert getattr(lock_release_result_log, "target_device_id") == device_id

    def test_unlock_error(self, caplog: LogCaptureFixture):
        """Test for DeviceExclusive.unlock error case.

        Args:
            caplog (LogCaptureFixture):
                The fixture used to capture log records.
        """

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        device_id = "2b078f92-5ece-48ad-99fc-d7ae87575d7a"

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=device_exclusive.__name__):
            result = device_exclusive.DeviceExclusive.unlock(device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # test for lock state
        assert not result
        assert not device_exclusive.DeviceExclusive._locks.get(device_id)  # pylint: disable=W0212

        # test for log
        assert len(caplog.records) == 1

        # Inspection: Check the lock release result log.
        lock_release_result_log = caplog.records[0]
        assert lock_release_result_log.levelname == "ERROR"
        assert (
            lock_release_result_log.getMessage()
            == "Failed to release the device lock. The specified device is not locked."
        )

        assert hasattr(
            lock_release_result_log, "target_device_id"
        ), "target_device_id should be present in the log record"
        assert getattr(lock_release_result_log, "target_device_id") == device_id

    def test_unlock_exception(self, caplog: LogCaptureFixture):
        """Test for DeviceExclusive.unlock RuntimeError case.

        Args:
            caplog (LogCaptureFixture):
                The fixture used to capture log records.
        """

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        device_id = "2b078f92-5ece-48ad-99fc-d7ae87575d7a"

        device_exclusive.DeviceExclusive._locks[device_id] = threading.Lock()  # pylint: disable=W0212
        device_exclusive.DeviceExclusive._locks[device_id].acquire(blocking=False)  # pylint: disable=W0212
        device_exclusive.DeviceExclusive._locks[device_id].release()  # pylint: disable=W0212

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#

        caplog.clear()
        with caplog.at_level(logging.INFO, logger=device_exclusive.__name__):
            result = device_exclusive.DeviceExclusive.unlock(device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # test for lock state
        assert not result
        assert not device_exclusive.DeviceExclusive._locks[device_id].locked()  # pylint: disable=W0212

        # test for log
        assert len(caplog.records) == 1

        # Inspection: Check the lock release result log.
        lock_release_result_log = caplog.records[0]
        assert lock_release_result_log.levelname == "ERROR"
        assert lock_release_result_log.getMessage() == "Failed to release the device lock."

        assert hasattr(
            lock_release_result_log, "target_device_id"
        ), "target_device_id should be present in the log record"
        assert getattr(lock_release_result_log, "target_device_id") == device_id

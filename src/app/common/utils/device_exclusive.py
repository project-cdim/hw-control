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

"""Manages the lock state of devices.

This module manages the exclusive lock state of the specified device.

file path:/app/common/utils/device_exclusive.py

"""

import traceback
import threading

from app.common.utils.log import LOGGER
from app.common.messages import message


class DeviceExclusive:
    """Manages the lock state of the specified device.

    This class exclude concurrent requests to a single device.

    Attributes:
        _locks (dict):

            Device ID is the identifier that uniquely identifies
            the device.

            "Lock-Object" is an object for managing the "exclusive
            lock state" of the device.
            Use an instance of the Lock class in the threading module.
            There are two "exclusive lock states" for devices managed
            by this class:
            Lock state:
                The device is currently being used for another control
                and cannot accept concurrent requests.
            Unlock state:
                The device can accept request.

        _internal_lock (threading.Lock):
            Object for exclusive control of access to _lock (dict).
            Use an instance of the Lock class in the threading module.
    """

    _locks: dict = {}
    _internal_lock = threading.Lock()

    @staticmethod
    def lock(device_id: str) -> bool:
        """Acquires exclusive lock the specified device.

        This method acquires the exclusive lock of the device
        specified by the Device ID.

        Args:
            device_id (str):
                Device ID of the device to acquire the exclusive lock.

        Returns:
            bool:
                Result of acquiring the exclusive lock for the device
                specified by the Device ID.

        Raises:
            None

        Note:
            If you acquire an exclusive lock by calling this method,
            be sure to call the unlock method to release the
            exclusive lock.

        """

        LOGGER.debug(f"[{DeviceExclusive.lock.__name__}] begin device_id={device_id}")
        with DeviceExclusive._internal_lock:  # Exclusive _locks.
            # check the specified device lock state.
            if device_id not in DeviceExclusive._locks:
                # If it does not exist, add a lock object with the device ID as the key.
                DeviceExclusive._locks[device_id] = threading.Lock()
                LOGGER.debug(f"[{DeviceExclusive.lock.__name__}] new lock for {device_id}")

            # acquire device lock.
            result = DeviceExclusive._locks[device_id].acquire(blocking=False)

            if result:
                LOGGER.info(message.DeviceLockLog(target_device=device_id).to_json_encodable())

            else:
                LOGGER.warning(message.DeviceLockFailedLog(target_device=device_id).to_json_encodable())

            LOGGER.debug(f"[{DeviceExclusive.lock.__name__}] end")
            return result

    @staticmethod
    def unlock(device_id: str) -> bool:
        """Releases exclusive lock the specified device.

        This method releases the exclusive lock of the device
        specified by the Device ID.

        Args:
            device_id (str): Device ID of the device you want to
            the exclusive for.

        Returns:
            bool: Result of release the exclusive lock for
                    the device specified by the Device ID.

        Raises:
            None

        """
        LOGGER.debug(f"[{DeviceExclusive.unlock.__name__}] begin device_id={device_id}")

        with DeviceExclusive._internal_lock:  # Exclusive _locks.
            # check the specified device lock state.
            if device_id not in DeviceExclusive._locks:
                LOGGER.error(
                    message.DeviceLockReleaseFailedLog(
                        detail="The specified device is not locked.", target_device=device_id
                    ).to_json_encodable()
                )
                result = False
            else:
                try:
                    # release device lock.
                    DeviceExclusive._locks[device_id].release()
                    del DeviceExclusive._locks[device_id]
                    LOGGER.info(message.DeviceLockReleasedLog(target_device=device_id).to_json_encodable())
                    result = True
                except RuntimeError:
                    LOGGER.error(message.ExceptionLog(trace_back=traceback.format_exc()).to_json_encodable())
                    LOGGER.error(message.DeviceLockReleaseFailedLog(target_device=device_id).to_json_encodable())
                    result = False
            LOGGER.debug(f"[{DeviceExclusive.unlock.__name__}] end")
            return result

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
"""

import logging
import threading

logger = logging.getLogger(__name__)


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

        logger.debug("[%s] begin device_id=%s", DeviceExclusive.lock.__name__, device_id)
        with DeviceExclusive._internal_lock:  # Exclusive _locks.
            # check the specified device lock state.
            if device_id not in DeviceExclusive._locks:
                # If it does not exist, add a lock object with the device ID as the key.
                DeviceExclusive._locks[device_id] = threading.Lock()
                logger.debug("[%s] new lock for %s", DeviceExclusive.lock.__name__, device_id)

            # acquire device lock.
            result = DeviceExclusive._locks[device_id].acquire(blocking=False)

            if result:
                logger.info("Acquire the device lock.", extra={"target_device_id": device_id})

            else:
                logger.warning("Failed to acquire the device lock.", extra={"target_device_id": device_id})

            logger.debug("[%s] end", DeviceExclusive.lock.__name__)
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
        logger.debug("[%s] begin device_id=%s", DeviceExclusive.unlock.__name__, device_id)

        with DeviceExclusive._internal_lock:  # Exclusive _locks.
            # check the specified device lock state.
            if device_id not in DeviceExclusive._locks:
                logger.error(
                    "Failed to release the device lock. The specified device is not locked.",
                    extra={"target_device_id": device_id},
                )
                result = False
            else:
                try:
                    # release device lock.
                    DeviceExclusive._locks[device_id].release()
                    del DeviceExclusive._locks[device_id]
                    logger.info("Released the device lock.", extra={"target_device_id": device_id})
                    result = True
                except RuntimeError:
                    logger.exception("Failed to release the device lock.", extra={"target_device_id": device_id})
                    result = False
            logger.debug("[%s] end", DeviceExclusive.unlock.__name__)
            return result

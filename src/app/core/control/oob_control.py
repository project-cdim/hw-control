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

"""
HW independent section - oob control

Upon receiving a request from the control API,
Makes a control request to OOB for the device
specified by the device id.
"""

import logging

from app.core.control.control_base import (
    PowerControlTargetDevice,
    OOBPluginRequestTarget,
)
from app.common import constants
from app.common.utils import plugin_manager
import app.common.basic_exceptions as exc

logger = logging.getLogger(__name__)


class OOBController:
    """
    A class to control the OOB (Out-of-Band) Manager by calling methods
    defined in different OOB plugins.

    Attributes: None

    Methods:
        power_on:
            Turns the power on for the target device using the OOB plugin.

        reset:
            Resets the CPU of the target device using the OOB plugin.

        force_off:
            Forces the power off for the target device using the OOB plugin.

        power_off:
            Turns the power off for the target device using the OOB plugin.
    """

    @staticmethod
    def power_on(target_device: PowerControlTargetDevice) -> None:
        """
        Turns the power on for the target device using the OOB plugin.

        Args:
            target_device (PowerControlTargetDevice):
                The device to be powered on.

        Returns:
            None

        Raises:
            UnexpectedExceptionHWControlError:
                plugin raise unexpected Exception.
        """

        oob_plugin = plugin_manager.get_oob_plugin(manager_id=target_device.oob_manager_id)

        oob_plugin_argument = [
            OOBPluginRequestTarget(
                oob_device_id=target_device.oob_device_id,
                device_type=target_device.device_type,
            ).model_dump()
        ]

        logger.info(
            "Request device power on to OOB plugin.",
            extra={
                "manager_type": constants.ManagerType.OOB.value,
                "manager_id": target_device.oob_manager_id,
                "class_name": oob_plugin.__class__.__name__,
                "method_name": "post_power_on",
            },
        )

        try:
            oob_plugin.post_power_on(oob_plugin_argument)
        except exc.DeviceNotFoundHWControlError as e:
            e.append_error_message(f"The target Device ID is follow: {target_device.device_id}")
            raise
        except exc.BaseHWControlError:
            raise
        except Exception as e:
            # Raise UnexpectedExceptionHWControlError
            # when OOB-plugin raise Unexpected Exception.
            raise exc.UnexpectedExceptionHWControlError from e

    @staticmethod
    def reset(target_device: PowerControlTargetDevice) -> None:
        """
        Resets the CPU of the target device using the OOB plugin.

        Args:
            target_device (PowerControlTargetDevice):
                The device whose CPU is to be reset.

        Returns:
            None

        Raises:
            RequestNotSupportedHWControlError:
                If the specified device is not a CPU.

            UnexpectedExceptionHWControlError:
                plugin raise unexpected Exception.
        """

        if target_device.device_type != constants.DeviceType.CPU.value:
            raise exc.RequestNotSupportedHWControlError("Reset is supported only by the CPU.")

        oob_plugin = plugin_manager.get_oob_plugin(manager_id=target_device.oob_manager_id)

        oob_plugin_argument = [
            OOBPluginRequestTarget(
                oob_device_id=target_device.oob_device_id,
                device_type=target_device.device_type,
            ).model_dump()
        ]

        logger.info(
            "Request Host CPU reset to OOB plugin.",
            extra={
                "manager_type": constants.ManagerType.OOB.value,
                "manager_id": target_device.oob_manager_id,
                "class_name": oob_plugin.__class__.__name__,
                "method_name": "post_cpu_reset",
            },
        )

        try:
            oob_plugin.post_cpu_reset(oob_plugin_argument)
        except exc.DeviceNotFoundHWControlError as e:
            e.append_error_message(f"The target Device ID is follow: {target_device.device_id}")
            raise
        except exc.BaseHWControlError:
            raise
        except Exception as e:
            # Raise UnexpectedExceptionHWControlError
            # when OOB-plugin raise Unexpected Exception.
            raise exc.UnexpectedExceptionHWControlError from e

    @staticmethod
    def force_off(target_device: PowerControlTargetDevice) -> None:
        """
        Forces the power off for the target device using the OOB plugin.

        Args:
            target_device (PowerControlTargetDevice):
                The device to be forcibly powered off.

        Returns:
            None

        Raises:
            UnexpectedExceptionHWControlError:
                plugin raise unexpected Exception.
        """
        oob_plugin = plugin_manager.get_oob_plugin(manager_id=target_device.oob_manager_id)

        oob_plugin_argument = [
            OOBPluginRequestTarget(
                oob_device_id=target_device.oob_device_id,
                device_type=target_device.device_type,
            ).model_dump()
        ]

        logger.info(
            "Request device power off to OOB plugin.",
            extra={
                "manager_type": constants.ManagerType.OOB.value,
                "manager_id": target_device.oob_manager_id,
                "class_name": oob_plugin.__class__.__name__,
                "method_name": "post_power_off",
            },
        )

        try:
            oob_plugin.post_power_off(oob_plugin_argument)
        except exc.DeviceNotFoundHWControlError as e:
            e.append_error_message(f"The target Device ID is follow: {target_device.device_id}")
            raise
        except exc.BaseHWControlError:
            raise
        except Exception as e:
            # Raise UnexpectedExceptionHWControlError
            # when OOB-plugin raise Unexpected Exception.
            raise exc.UnexpectedExceptionHWControlError from e

    @staticmethod
    def power_off(target_device: PowerControlTargetDevice) -> None:
        """
        Turns the power off for the target device using the OOB plugin.

        Args:
            target_device (PowerControlTargetDevice): The device to be powered off.

        Returns:
            None

        Raises:
            UnexpectedExceptionHWControlError:
                plugin raise unexpected Exception.
        """

        oob_plugin = plugin_manager.get_oob_plugin(manager_id=target_device.oob_manager_id)

        oob_plugin_argument = [
            OOBPluginRequestTarget(
                oob_device_id=target_device.oob_device_id,
                device_type=target_device.device_type,
            ).model_dump()
        ]

        try:
            if target_device.device_type == constants.DeviceType.CPU.value:

                logger.info(
                    "Request Host CPU shutdown to OOB plugin.",
                    extra={
                        "manager_type": constants.ManagerType.OOB.value,
                        "manager_id": target_device.oob_manager_id,
                        "class_name": oob_plugin.__class__.__name__,
                        "method_name": "post_os_shutdown",
                    },
                )

                oob_plugin.post_os_shutdown(oob_plugin_argument)

            else:
                logger.info(
                    "Request device power off to OOB plugin.",
                    extra={
                        "manager_type": constants.ManagerType.OOB.value,
                        "manager_id": target_device.oob_manager_id,
                        "class_name": oob_plugin.__class__.__name__,
                        "method_name": "post_power_off",
                    },
                )

                oob_plugin.post_power_off(oob_plugin_argument)

        except exc.DeviceNotFoundHWControlError as e:
            e.append_error_message(f"The target Device ID is follow: {target_device.device_id}")
            raise
        except exc.BaseHWControlError:
            raise
        except Exception as e:
            # Raise UnexpectedExceptionHWControlError
            # when OOB-plugin raise Unexpected Exception.
            raise exc.UnexpectedExceptionHWControlError from e

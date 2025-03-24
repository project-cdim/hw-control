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
from typing import cast

from app.core.control.control_base import (
    PowerControlTargetDevice,
    OobPluginRequestTarget,
)
from app.common.utils.oob_plugin_base import OOBPluginBase
from app.common import constants
from app.common.utils import plugin_manager
import app.common.basic_exceptions as exc
from app.common.utils.log import LOGGER
from app.common.messages import message


class OobController:
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
            UnexpectedExceptionHwControlError:
                plugin raise unexpected Exception.
        """

        plugin = plugin_manager.get_plugin(
            manager_type=constants.ManagerType.OOB.value,
            manager_id=target_device.oob_manager_id,
        )
        oob_plugin = cast(OOBPluginBase, plugin)

        oob_plugin_argument = [
            OobPluginRequestTarget(
                oob_device_id=target_device.oob_device_id,
                device_type=target_device.device_type,
            ).model_dump()
        ]

        LOGGER.info(
            message=message.PluginCallLog(
                manager_type=constants.ManagerType.OOB.value,
                manager_id=target_device.oob_manager_id,
                class_name=plugin.__class__.__name__,
                method_name="post_power_on",
            ).to_json_encodable()
        )

        try:
            oob_plugin.post_power_on(oob_plugin_argument)
        except exc.DeviceNotFoundHwControlError as e:
            e.append_error_message(f"The target Device ID is follow: {target_device.device_id}")
            raise
        except exc.BaseHwControlError:
            raise
        except Exception as e:
            # Raise UnexpectedExceptionHwControlError
            # when OOB-plugin raise Unexpected Exception.
            raise exc.UnexpectedExceptionHwControlError from e

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
            RequestNotSupportedHwControlError:
                If the specified device is not a CPU.

            UnexpectedExceptionHwControlError:
                plugin raise unexpected Exception.
        """

        if target_device.device_type != constants.DeviceType.CPU.value:
            raise exc.RequestNotSupportedHwControlError("Reset is supported only by the CPU.")

        plugin = plugin_manager.get_plugin(
            manager_type=constants.ManagerType.OOB.value,
            manager_id=target_device.oob_manager_id,
        )
        oob_plugin = cast(OOBPluginBase, plugin)

        oob_plugin_argument = [
            OobPluginRequestTarget(
                oob_device_id=target_device.oob_device_id,
                device_type=target_device.device_type,
            ).model_dump()
        ]

        LOGGER.info(
            message=message.PluginCallLog(
                manager_type=constants.ManagerType.OOB.value,
                manager_id=target_device.oob_manager_id,
                class_name=plugin.__class__.__name__,
                method_name="post_cpu_reset",
            ).to_json_encodable()
        )

        try:
            oob_plugin.post_cpu_reset(oob_plugin_argument)
        except exc.DeviceNotFoundHwControlError as e:
            e.append_error_message(f"The target Device ID is follow: {target_device.device_id}")
            raise
        except exc.BaseHwControlError:
            raise
        except Exception as e:
            # Raise UnexpectedExceptionHwControlError
            # when OOB-plugin raise Unexpected Exception.
            raise exc.UnexpectedExceptionHwControlError from e

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
            UnexpectedExceptionHwControlError:
                plugin raise unexpected Exception.
        """
        plugin = plugin_manager.get_plugin(
            manager_type=constants.ManagerType.OOB.value,
            manager_id=target_device.oob_manager_id,
        )
        oob_plugin = cast(OOBPluginBase, plugin)

        oob_plugin_argument = [
            OobPluginRequestTarget(
                oob_device_id=target_device.oob_device_id,
                device_type=target_device.device_type,
            ).model_dump()
        ]

        LOGGER.info(
            message=message.PluginCallLog(
                manager_type=constants.ManagerType.OOB.value,
                manager_id=target_device.oob_manager_id,
                class_name=plugin.__class__.__name__,
                method_name="post_power_off",
            ).to_json_encodable()
        )

        try:
            oob_plugin.post_power_off(oob_plugin_argument)
        except exc.DeviceNotFoundHwControlError as e:
            e.append_error_message(f"The target Device ID is follow: {target_device.device_id}")
            raise
        except exc.BaseHwControlError:
            raise
        except Exception as e:
            # Raise UnexpectedExceptionHwControlError
            # when OOB-plugin raise Unexpected Exception.
            raise exc.UnexpectedExceptionHwControlError from e

    @staticmethod
    def power_off(target_device: PowerControlTargetDevice) -> None:
        """
        Turns the power off for the target device using the OOB plugin.

        Args:
            target_device (PowerControlTargetDevice): The device to be powered off.

        Returns:
            None

        Raises:
            UnexpectedExceptionHwControlError:
                plugin raise unexpected Exception.
        """

        plugin = plugin_manager.get_plugin(
            manager_type=constants.ManagerType.OOB.value,
            manager_id=target_device.oob_manager_id,
        )
        oob_plugin = cast(OOBPluginBase, plugin)

        oob_plugin_argument = [
            OobPluginRequestTarget(
                oob_device_id=target_device.oob_device_id,
                device_type=target_device.device_type,
            ).model_dump()
        ]

        try:
            if target_device.device_type == constants.DeviceType.CPU.value:

                LOGGER.info(
                    message=message.PluginCallLog(
                        manager_type=constants.ManagerType.OOB.value,
                        manager_id=target_device.oob_manager_id,
                        class_name=plugin.__class__.__name__,
                        method_name="post_os_shutdown",
                    ).to_json_encodable()
                )

                oob_plugin.post_os_shutdown(oob_plugin_argument)

            else:
                LOGGER.info(
                    message=message.PluginCallLog(
                        manager_type=constants.ManagerType.OOB.value,
                        manager_id=target_device.oob_manager_id,
                        class_name=plugin.__class__.__name__,
                        method_name="post_power_off",
                    ).to_json_encodable()
                )

                oob_plugin.post_power_off(oob_plugin_argument)

        except exc.DeviceNotFoundHwControlError as e:
            e.append_error_message(f"The target Device ID is follow: {target_device.device_id}")
            raise
        except exc.BaseHwControlError:
            raise
        except Exception as e:
            # Raise UnexpectedExceptionHwControlError
            # when OOB-plugin raise Unexpected Exception.
            raise exc.UnexpectedExceptionHwControlError from e

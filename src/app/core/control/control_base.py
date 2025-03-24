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

"""HW independent section - control function base

app.core.control.control_base

This module defines common constants and processes used 
in control functions.
"""
from typing import cast

from pydantic import BaseModel, Field

from app.common.utils.oob_plugin_base import OOBPluginBase
from app.common.deviceIdManager import device_id_base as deviceIdManager
from app.common.utils.device_exclusive import DeviceExclusive
import app.common.basic_exceptions as exc
from app.common.utils.log import LOGGER
from app.common.messages import message
from app.common import constants
from app.common.utils import plugin_manager


class OobPluginRequestTarget(BaseModel):
    """generate OOB plugin request format

    Attributes:
        oob_device_id (str):
            Identifier that uniquely identifies the device in OOB.

        device_type (str):
            Indicates the classification of the device.
            Defaults to None.

    """

    oob_device_id: str = Field()

    device_type: str = Field()


class ControlTargetDevice(BaseModel):
    """
    Class for holding device information.

    This class represents a device in hw-control control part.

    Attributes:
        device_id (str):
            Identifier that uniquely identifies the device.
    """

    device_id: str = Field()

    def get_lock(self) -> None:
        """
        Acquire a lock on the target device.

        This method attempts to acquire an exclusive lock on the target device.

        Args:
            None

        Returns:
            None

        Raises:
            DeviceBusyHwControlError:
                If the target device is already locked and thus busy.
        """
        device_lock = DeviceExclusive.lock(device_id=self.device_id)
        if not device_lock:
            raise exc.DeviceBusyHwControlError(additional_message=f"The target Device ID is follow: {self.device_id}")

    def release_lock(self) -> None:
        """
        Release the lock on the target device.

        This method releases the exclusive lock on the target device.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        DeviceExclusive.unlock(self.device_id)


class PowerControlTargetDevice(ControlTargetDevice):
    """
    Class for holding device information related to power control.

    This class extends ControlTargetDevice and adds additional attributes
    for managing power state information.

    Attributes:
        device_id (str):
            Identifier that uniquely identifies the device.
            (Inherited from ControlTargetDevice)

        device_type (str):
            Indicates the classification of the device.

        oob_manager_id (str):
            Identifier that uniquely identifies the OOB plug-in.

        oob_device_id (str):
            Identifier that uniquely identifies the device in OOB.

        power_state (DevicePowerState):
            Indicates the current power state of the device.
            Defaults to constants.DevicePowerState.UNKNOWN.
    """

    device_type: str = Field(default="")

    oob_manager_id: str = Field(default="")

    oob_device_id: str = Field(default="")

    power_state: constants.DevicePowerState = Field(default=constants.DevicePowerState.UNKNOWN)

    def model_post_init(self, __context):
        """Post-initialization method for PowerControlTargetDevice.

        This method is called after the initialization of an instance of PowerControlTargetDevice. It sets
        the 'Device Type', 'OOB Manager ID', and 'OOB Manager ID' for the target device. If any of these
        settings fail, a RequestNotSupportedHwControlError is raised.

        Raises:
            exc.RequestNotSupportedHwControlError: If setting the fm_port_id, fm_port_id, or switch_port_type fails.
        """
        try:
            self.set_device_type()
            self.set_oob_device_id()
            self.set_oob_manager_id()
        except ValueError as e:
            raise exc.RequestNotSupportedHwControlError from e

    def set_oob_manager_id(self) -> None:
        """
        Set oob_manager_id from information of deviceIdManager.

        This method gets the 'OOB Manager ID' of the specified device from app.common.deviceIdManager
        and set self.oob_manager_id.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError:
            - The 'OOB Manager ID' could not be obtained from deviceIdManager.

            DeviceNotFoundHwControlError:
                The specified device is not found.

            Raise the following exception thrown from device_id_to_manager_id.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_ID_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_ID_info.json file did not exist
                in "/app/common/device_id_manager/".

        """
        try:
            raw_manager_ids: dict = deviceIdManager.device_id_to_manager_id(device_id=self.device_id)
        # ApiUsageHwControlError: Raised when the specified device_id
        # is an invalid UUID.
        # DeviceIdNotFoundHwControlError: Raised when the specified
        # device_id does not exist in device id manager.
        except (exc.ApiUsageHwControlError, exc.DeviceIdNotFoundHwControlError) as e:
            raise exc.DeviceNotFoundHwControlError(
                additional_message=f"The target Device ID is follow: {self.device_id}"
            ) from e

        oob_manager_id = raw_manager_ids.get("oob")
        if not oob_manager_id:
            raise ValueError
        self.oob_manager_id = oob_manager_id

    def set_device_type(self) -> None:
        """
        Set device_type from information of deviceIdManager.

        This method gets the 'Device Type' of the specified device from app.common.deviceIdManager
        and set self.device_type.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError:
            - The 'Device Type' could not be obtained from deviceIdManager.

            DeviceNotFoundHwControlError:
                The specified device is not found.

            Raise the following exception thrown from device_id_to_device_type.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_ID_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_ID_info.json file did not exist
                in "/app/common/device_id_manager/".

        """
        try:
            raw_device_type = deviceIdManager.device_id_to_device_type(device_id=self.device_id)
        # ApiUsageHwControlError: Raised when the specified device_id
        # is an invalid UUID.
        # DeviceIdNotFoundHwControlError: Raised when the specified
        # device_id does not exist in device id manager.
        except (exc.ApiUsageHwControlError, exc.DeviceIdNotFoundHwControlError) as e:
            raise exc.DeviceNotFoundHwControlError(
                additional_message=f"The target Device ID is follow: {self.device_id}"
            ) from e

        if not raw_device_type:
            raise ValueError("The 'Device Type' could not be obtained.")
        self.device_type = raw_device_type

    def set_oob_device_id(self) -> None:
        """
        Set oob_device_id from information of deviceIdManager.

        This method gets the 'OOB Device ID' of the specified device
        from deviceIdManager and set self.oob_device_id.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError:
            - The 'OOB Device ID' could not be obtained from deviceIdManager.

            DeviceNotFoundHwControlError:
                The specified device is not found.

            Raise the following exception thrown from device_id_to_oob_device_id.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_ID_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_ID_info.json file did not exist
                in "/app/common/device_id_manager/".

        """
        try:
            raw_oob_device_id = deviceIdManager.device_id_to_oob_device_id(device_id=self.device_id)
        # ApiUsageHwControlError: Raised when the specified device_id
        # is an invalid UUID.
        # DeviceIdNotFoundHwControlError: Raised when the specified
        # device_id does not exist in device id manager.
        except (exc.ApiUsageHwControlError, exc.DeviceIdNotFoundHwControlError) as e:
            raise exc.DeviceNotFoundHwControlError(
                additional_message=f"The target Device ID is follow: {self.device_id}"
            ) from e

        if not raw_oob_device_id:
            raise ValueError("The 'OOB Device ID' could not be obtained.")
        self.oob_device_id = raw_oob_device_id

    def set_power_state(self) -> None:
        """Set the power state of device from information of OOB.

        This method calls the OOB plugin to provide the ability
        to set the power state of the specified device object.

        Args:
            None

        Returns:
            None

        Raises:
            Subclass of BaseHwControlError:
                Raise the subclass of BaseHwControlError dispatched
                by the FM plug-in as it is.

            UnexpectedExceptionHwControlError:
                If the FM-plugin raises an unexpected exception,
                convert it to this exception.

            InternalHwControlError:
                The spec information of the device was obtained,
                but the power status could not be retrieved, or
                the retrieved power status was an unknown value.

            ValueError:
                ValueError is raised when specifying device
                that does not support power control.
        """
        plugin = plugin_manager.get_plugin(manager_type=constants.ManagerType.OOB.value, manager_id=self.oob_manager_id)
        oob_plugin = cast(OOBPluginBase, plugin)

        oob_plugin_argument = [
            OobPluginRequestTarget(
                oob_device_id=self.oob_device_id,
                device_type=self.device_type,
            ).model_dump()
        ]

        LOGGER.info(
            message=message.PluginCallLog(
                manager_type=constants.ManagerType.OOB.value,
                manager_id=self.oob_manager_id,
                class_name=plugin.__class__.__name__,
                method_name="get_power_state",
            ).to_json_encodable()
        )

        try:
            response_data = oob_plugin.get_power_state(oob_plugin_argument)
        except exc.DeviceNotFoundHwControlError as e:
            e.append_error_message(f"The target Device ID is follow: {self.device_id}")
            raise
        except exc.BaseHwControlError:
            raise
        except Exception as e:
            raise exc.UnexpectedExceptionHwControlError from e

        power_state_response = response_data["devices"][0]["powerState"]

        if power_state_response is None:
            raise ValueError

        try:
            power_state = constants.DevicePowerState(power_state_response)
        except ValueError:
            LOGGER.warning(message=message.BaseLogMessage(detail=power_state_response).to_json_encodable())
            power_state = constants.DevicePowerState.UNKNOWN

        self.power_state = power_state

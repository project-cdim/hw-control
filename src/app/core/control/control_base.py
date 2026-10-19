# Copyright 2025-2026 NEC Corporation
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

"""HW independent section - control function base.

app.core.control.control_base

This module defines common constants and processes used
in control functions.
"""

import logging

from pydantic import BaseModel, Field

import app.common.basic_exceptions as exc
from app.common import constants
from app.common.dim import device_id_base as dim
from app.common.plugin import plugin_manager

logger = logging.getLogger(__name__)


class OOBPluginRequestTarget(BaseModel):
    """generate OOB plugin request format.

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
    """Class for holding device information.

    This class represents a device in hw-control control part.

    Attributes:
        device_id (str):
            Identifier that uniquely identifies the device.
    """

    device_id: str = Field()


class PowerControlTargetDevice(ControlTargetDevice):
    """Class for holding device information related to power control.

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

    def model_post_init(self, __context, /):
        """Post-initialization method for PowerControlTargetDevice.

        This method is called after the initialization of an instance of PowerControlTargetDevice. It sets
        the 'Device Type', 'OOB Manager ID', and 'OOB Manager ID' for the target device. If any of these
        settings fail, a RequestNotSupportedHWControlError is raised.

        Raises:
            exc.RequestNotSupportedHWControlError: If setting the fm_port_id, fm_port_id, or switch_port_type fails.
        """
        try:
            self.set_device_type()
            self.set_oob_device_id()
            self.set_oob_manager_id()
        except ValueError as e:
            raise exc.RequestNotSupportedHWControlError from e

    def set_oob_manager_id(self) -> None:
        """Set oob_manager_id from information of dim.

        This method gets the 'OOB Manager ID' of the specified device from app.common.dim
        and set self.oob_manager_id.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError:
            - The 'OOB Manager ID' could not be obtained from dim.

            DeviceNotFoundHWControlError:
                The specified device is not found.

            Raise the following exception thrown from device_id_to_manager_id.

            DeviceIDFileIncorrectHWControlError:
                When there is an error in the contents of the
                device_ID_info.json file.

            DeviceIDFileNotFoundHWControlError:
                If the device_ID_info.json file did not exist
                in "/app/common/device_id_manager/".

        """
        try:
            raw_manager_ids: dict = dim.device_id_to_manager_id(device_id=self.device_id)
        # APIUsageHWControlError: Raised when the specified device_id
        # is an invalid UUID.
        # DeviceIDNotFoundHWControlError: Raised when the specified
        # device_id does not exist in device id manager.
        except (exc.APIUsageHWControlError, exc.DeviceIDNotFoundHWControlError) as e:
            raise exc.DeviceNotFoundHWControlError(
                additional_message=f"The target Device ID is follow: {self.device_id}"
            ) from e

        oob_manager_id = raw_manager_ids.get("oob")
        if not oob_manager_id:
            raise ValueError
        self.oob_manager_id = oob_manager_id

    def set_device_type(self) -> None:
        """Set device_type from information of dim.

        This method gets the 'Device Type' of the specified device from app.common.dim
        and set self.device_type.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError:
            - The 'Device Type' could not be obtained from dim.

            DeviceNotFoundHWControlError:
                The specified device is not found.

            Raise the following exception thrown from device_id_to_device_type.

            DeviceIDFileIncorrectHWControlError:
                When there is an error in the contents of the
                device_ID_info.json file.

            DeviceIDFileNotFoundHWControlError:
                If the device_ID_info.json file did not exist
                in "/app/common/device_id_manager/".

        """
        try:
            raw_device_type = dim.device_id_to_device_type(device_id=self.device_id)
        # APIUsageHWControlError: Raised when the specified device_id
        # is an invalid UUID.
        # DeviceIDNotFoundHWControlError: Raised when the specified
        # device_id does not exist in device id manager.
        except (exc.APIUsageHWControlError, exc.DeviceIDNotFoundHWControlError) as e:
            raise exc.DeviceNotFoundHWControlError(
                additional_message=f"The target Device ID is follow: {self.device_id}"
            ) from e

        if not raw_device_type:
            raise ValueError("The 'Device Type' could not be obtained.")
        self.device_type = raw_device_type

    def set_oob_device_id(self) -> None:
        """Set oob_device_id from information of dim.

        This method gets the 'OOB Device ID' of the specified device
        from dim and set self.oob_device_id.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError:
            - The 'OOB Device ID' could not be obtained from dim.

            DeviceNotFoundHWControlError:
                The specified device is not found.

            Raise the following exception thrown from device_id_to_oob_device_id.

            DeviceIDFileIncorrectHWControlError:
                When there is an error in the contents of the
                device_ID_info.json file.

            DeviceIDFileNotFoundHWControlError:
                If the device_ID_info.json file did not exist
                in "/app/common/device_id_manager/".

        """
        try:
            raw_oob_device_id = dim.device_id_to_oob_device_id(device_id=self.device_id)
        # APIUsageHWControlError: Raised when the specified device_id
        # is an invalid UUID.
        # DeviceIDNotFoundHWControlError: Raised when the specified
        # device_id does not exist in device id manager.
        except (exc.APIUsageHWControlError, exc.DeviceIDNotFoundHWControlError) as e:
            raise exc.DeviceNotFoundHWControlError(
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
            Subclass of BaseHWControlError:
                Raise the subclass of BaseHWControlError dispatched
                by the FM plug-in as it is.

            UnexpectedExceptionHWControlError:
                If the FM-plugin raises an unexpected exception,
                convert it to this exception.

            InternalHWControlError:
                The spec information of the device was obtained,
                but the power status could not be retrieved, or
                the retrieved power status was an unknown value.

            ValueError:
                ValueError is raised when specifying device
                that does not support power control.
        """
        oob_plugin = plugin_manager.get_oob_plugin(manager_id=self.oob_manager_id)

        oob_plugin_argument = [
            OOBPluginRequestTarget(
                oob_device_id=self.oob_device_id,
                device_type=self.device_type,
            ).model_dump()
        ]

        logger.info(
            "Request get device power state to OOB plugin.",
            extra={
                "manager_type": constants.ManagerType.OOB.value,
                "manager_id": self.oob_manager_id,
                "class_name": oob_plugin.__class__.__name__,
                "method_name": "get_power_state",
            },
        )

        try:
            response_data = oob_plugin.get_power_state(oob_plugin_argument)
        except exc.DeviceNotFoundHWControlError as e:
            e.append_error_message(f"The target Device ID is follow: {self.device_id}")
            raise
        except exc.BaseHWControlError:
            raise
        except Exception as e:
            raise exc.UnexpectedExceptionHWControlError from e

        power_state_response = response_data["devices"][0]["powerState"]

        if power_state_response is None:
            raise ValueError

        try:
            power_state = constants.DevicePowerState(power_state_response)
        except ValueError:
            logger.warning(
                "The obtained power state is not a valid DevicePowerState.",
                exc_info=True,
                extra={"obtained_power_state": power_state_response},
            )
            power_state = constants.DevicePowerState.UNKNOWN

        self.power_state = power_state

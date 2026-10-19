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

"""HW independent section - fm control.

Upon receiving a request from the control API,
Makes a control request to FM for the device
specified by the 'Device ID'.
"""

import logging

from pydantic import BaseModel, Field

import app.common.basic_exceptions as exc
from app.common import constants
from app.common.dim import device_id_base as dim
from app.common.plugin import plugin_manager
from app.core.control.control_base import ControlTargetDevice

logger = logging.getLogger(__name__)


class FMControlTargetDevice(ControlTargetDevice):
    """Data class for holding FM control target device information.

    Holds the information of the target device for fm-control.

    Attributes:
        device_id (str):
            Identifier that uniquely identifies the device.
            (Inherited from ControlTargetDevice)

        fm_port_id (str):
            Identifier that uniquely identifies the device in FM.

        fm_manager_id (str):
            Identifier that uniquely identifies the FM plug-in.

        switch_port_type (str):
            USP:
                If the device is connected Upstream-Switch-Port of the switch.

            DSP:
                If the device is connected Downstream-Switch-Port of the switch.

            None:
                In the following cases:
                    If the device is placed on the motherboard.
                    If the device is switch.


    """

    switch_port_type: str = Field(default="")
    fm_port_id: str = Field(default="")
    fm_manager_id: str = Field(default="")

    def model_post_init(self, __context, /):
        """Post-initialization method for FMControlTargetDevice.

        This method is called after the initialization of an instance of FMControlTargetDevice. It sets
        the 'Switch Port Type', 'FM Manager ID', and 'FM Port ID' for the target device. If any of these
        settings fail, a RequestNotSupportedHWControlError is raised.

        Raises:
            exc.RequestNotSupportedHWControlError: If setting the fm_port_id, fm_port_id, or switch_port_type fails.
        """
        try:
            self.set_switch_port_type()
            self.set_fm_port_id()
            self.set_fm_manager_id()
        except ValueError as e:
            raise exc.RequestNotSupportedHWControlError from e

    def set_fm_manager_id(self) -> None:
        """Set fm_manager_id from information of dim.

        This method gets the 'FM Manager ID' of the specified device from app.common.dim
        and set self.fm_manager_id.


        Args:
            None

        Returns:
            None

        Raises:
            ValueError:
            - The 'FM Manager ID' could not be obtained from dim.

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

        fm_manager_id = raw_manager_ids.get("fm")
        if not fm_manager_id:
            raise ValueError("The 'FM Manager ID' could not be obtained.")
        self.fm_manager_id = fm_manager_id

    def set_fm_port_id(self) -> None:
        """Set fm_port_id from information of dim.

        This method gets the 'FM Port ID' of the specified device
        from dim and set self.fm_port_id.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError:
            - The specified device 'Device Type' is a switch.
            - The 'FM Port ID' could not be obtained from dim.

            DeviceNotFoundHWControlError:
                The specified device is not found.

            Raise the following exception thrown from device_id_to_fm_port_id.

            DeviceIDFileIncorrectHWControlError:
                When there is an error in the contents of the
                device_ID_info.json file.

            DeviceIDFileNotFoundHWControlError:
                If the device_ID_info.json file did not exist
                in "/app/common/device_id_manager/".

        """
        try:
            raw_fm_port_id = dim.device_id_to_fm_port_id(device_id=self.device_id)
        # APIUsageHWControlError: Raised when the specified device_id
        # is an invalid UUID.
        # DeviceIDNotFoundHWControlError: Raised when the specified
        # device_id does not exist in device id manager.
        except (exc.APIUsageHWControlError, exc.DeviceIDNotFoundHWControlError) as e:
            raise exc.DeviceNotFoundHWControlError(
                additional_message=f"The target Device ID is follow: {self.device_id}"
            ) from e
        # InvalidTypeDeviceIDHWControlError: Raised when the specified
        # device_id is the device id of the Switch.
        except exc.InvalidTypeDeviceIDHWControlError as e:
            raise ValueError("The specified device 'Device Type' is a switch.") from e

        if not raw_fm_port_id:
            raise ValueError("The 'FM Port ID' could not be obtained.")
        self.fm_port_id = raw_fm_port_id

    def set_switch_port_type(self) -> None:
        """Set switch_port_type from information of dim.

        This method gets the 'Switch Port Type' of the specified device
        from dim and set self.switch_port_type.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError:
                The 'Switch Port Type' could not be obtained from dim.

            DeviceNotFoundHWControlError:
                The specified device is not found.

            Raise the following exception thrown from
            device_id_to_switch_port_type.

            DeviceIDFileIncorrectHWControlError:
                When there is an error in the contents of the
                device_ID_info.json file.

            DeviceIDFileNotFoundHWControlError:
                If the device_ID_info.json file did not exist
                in "/app/common/device_id_manager/".
                device_id_to_switch_port_type

        """
        try:
            raw_switch_port_type = dim.device_id_to_switch_port_type(device_id=self.device_id)
        # APIUsageHWControlError: Raised when the specified device_id
        # is an invalid UUID.
        # DeviceIDNotFoundHWControlError: Raised when the specified
        # device_id does not exist in device id manager.
        except (exc.APIUsageHWControlError, exc.DeviceIDNotFoundHWControlError) as e:
            raise exc.DeviceNotFoundHWControlError(
                additional_message=f"The target Device ID is follow: {self.device_id}"
            ) from e
        if not raw_switch_port_type:
            raise ValueError("The 'Switch Port Type' could not be obtained.")
        self.switch_port_type = raw_switch_port_type


class FMControlTargetDevicePair(BaseModel):
    """Data class for holding control target device pair information.

    Holds the information of the target-device-pair for conducting fm-control.

    Attributes:
        upstream_device (FMControlTargetDevice):
            Holds the information of the control target upstream side device.

        downstream_device (FMControlTargetDevice):
            Holds the information of the control target downstream side device.

    """

    upstream_device: FMControlTargetDevice
    downstream_device: FMControlTargetDevice

    def model_post_init(self, __context, /):
        """Post-initialization method for FMControlTargetDevicePair.

        This method is called after the initialization of an instance of FMControlTargetDevicePair.

        Raises:
            RequestNotSupportedHWControlError:
                Raised if the device_id of target upstream side device and downstream side device are the same.
        """
        if self.upstream_device.device_id == self.downstream_device.device_id:
            raise exc.RequestNotSupportedHWControlError


class FMController:
    """Perform operations using FM.

    Execute control through FM.

    Attributes:
        None

    """

    @staticmethod
    def connect(device_pair: FMControlTargetDevicePair) -> None:
        """Connect the the upstream side device to the downstream side device.

        Args:
            device_pair (FMControlTargetDevicePair):
                Represents control target device pair.

        Returns:
            None

        Raises:
            exc.UnexpectedExceptionHWControlError:
                FM-plugin raise Unexpected Exception.
        """
        # Raise RequestNotSupportedHWControlError when the following cases occur.
        # 1. The switch_port_type of the specified upstream_device is not "USP".
        # 2. switch_port_type of the specified downstream_device is not "DSP".
        # 3. The fm_manager_id of the specified upstream_device and downstream_device do not match.
        if (
            device_pair.upstream_device.switch_port_type != constants.SwitchPortType.USP.value
            or device_pair.downstream_device.switch_port_type != constants.SwitchPortType.DSP.value
        ):
            raise exc.RequestNotSupportedHWControlError

        if device_pair.upstream_device.fm_manager_id != device_pair.downstream_device.fm_manager_id:
            raise exc.RequestNotSupportedHWControlError

        fm_plugin = plugin_manager.get_fm_plugin(manager_id=device_pair.upstream_device.fm_manager_id)

        try:
            logger.info(
                "Request connect upstream device and downstream device to FM plugin.",
                extra={
                    "manager_type": constants.ManagerType.FM.value,
                    "manager_id": device_pair.upstream_device.fm_manager_id,
                    "class_name": fm_plugin.__class__.__name__,
                    "method_name": "connect",
                },
            )

            fm_plugin.connect(
                device_pair.upstream_device.fm_port_id,
                device_pair.downstream_device.fm_port_id,
            )

        # TODO: Remove this class after migration to the recommended exceptions is complete.
        except exc.HostCPUAndDeviceNotFoundHWControlError as e:
            e.append_error_message(
                "The target Device IDs are follow: "
                f"{device_pair.upstream_device.device_id}, {device_pair.downstream_device.device_id}"
            )
            raise

        # TODO: Remove HostCPUNotFoundHWControlError handling after migration.
        except (exc.HostCPUNotFoundHWControlError, exc.UpstreamDeviceNotFoundHWControlError) as e:
            e.append_error_message(f"The target Device ID is follow: {device_pair.upstream_device.device_id}")
            raise

        # TODO: Remove DeviceNotFoundHWControlError handling after migration.
        except (exc.DeviceNotFoundHWControlError, exc.DownstreamDeviceNotFoundHWControlError) as e:
            e.append_error_message(f"The target Device ID is follow: {device_pair.downstream_device.device_id}")
            raise

        except exc.BaseHWControlError:
            raise
        # Raise UnexpectedExceptionHWControlError
        # when FM-plugin raise Unexpected Exception.
        except Exception as e:
            raise exc.UnexpectedExceptionHWControlError from e

    @staticmethod
    def disconnect(device_pair: FMControlTargetDevicePair) -> None:
        """Disconnect the downstream side device from the upstream side device.

        Args:
            device_pair (FMControlTargetDevicePair):
                Represents control target device pair.

        Returns:
            None

        Raises:
            exc.UnexpectedExceptionHWControlError:
                FM-plugin raise Unexpected Exception.
        """
        if (
            device_pair.upstream_device.switch_port_type != constants.SwitchPortType.USP.value
            or device_pair.downstream_device.switch_port_type != constants.SwitchPortType.DSP.value
        ):
            raise exc.RequestNotSupportedHWControlError

        if device_pair.upstream_device.fm_manager_id != device_pair.downstream_device.fm_manager_id:
            raise exc.RequestNotSupportedHWControlError

        fm_plugin = plugin_manager.get_fm_plugin(manager_id=device_pair.upstream_device.fm_manager_id)

        logger.info(
            "Request disconnect upstream device and downstream device to FM plugin.",
            extra={
                "manager_type": constants.ManagerType.FM.value,
                "manager_id": device_pair.upstream_device.fm_manager_id,
                "class_name": fm_plugin.__class__.__name__,
                "method_name": "disconnect",
            },
        )

        try:
            fm_plugin.disconnect(
                device_pair.upstream_device.fm_port_id,
                device_pair.downstream_device.fm_port_id,
            )

        # TODO: Remove this class after migration to the recommended exceptions is complete.
        except exc.HostCPUAndDeviceNotFoundHWControlError as e:
            e.append_error_message(
                "The target Device IDs are follow: "
                f"{device_pair.upstream_device.device_id}, {device_pair.downstream_device.device_id}"
            )
            raise

        # TODO: Remove HostCPUNotFoundHWControlError handling after migration.
        except (exc.HostCPUNotFoundHWControlError, exc.UpstreamDeviceNotFoundHWControlError) as e:
            e.append_error_message(f"The target Device ID is follow: {device_pair.upstream_device.device_id}")
            raise

        # TODO: Remove DeviceNotFoundHWControlError handling after migration.
        except (exc.DeviceNotFoundHWControlError, exc.DownstreamDeviceNotFoundHWControlError) as e:
            e.append_error_message(f"The target Device ID is follow: {device_pair.downstream_device.device_id}")
            raise

        except exc.BaseHWControlError:
            raise
        # Raise UnexpectedExceptionHWControlError
        # when FM-plugin raise Unexpected Exception.
        except Exception as e:
            raise exc.UnexpectedExceptionHWControlError from e

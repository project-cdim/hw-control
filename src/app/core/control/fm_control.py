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
HW independent section - fm control

Upon receiving a request from the control API,
Makes a control request to FM for the device
specified by the 'Device ID'.
"""
from typing import cast

from pydantic import BaseModel, Field

from app.core.control.control_base import ControlTargetDevice
from app.common import constants

from app.common.utils.fm_plugin_base import FMPluginBase
from app.common.deviceIdManager import device_id_base as deviceIdManager
from app.common.utils import plugin_manager
import app.common.basic_exceptions as exc
from app.common.utils.log import LOGGER
from app.common.messages import message


class FmControlTargetDevice(ControlTargetDevice):
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

    def model_post_init(self, __context):
        """Post-initialization method for FmControlTargetDevice.

        This method is called after the initialization of an instance of FmControlTargetDevice. It sets
        the 'Switch Port Type', 'FM Manager ID', and 'FM Port ID' for the target device. If any of these
        settings fail, a RequestNotSupportedHwControlError is raised.

        Raises:
            exc.RequestNotSupportedHwControlError: If setting the fm_port_id, fm_port_id, or switch_port_type fails.
        """
        try:
            self.set_switch_port_type()
            self.set_fm_port_id()
            self.set_fm_manager_id()
        except ValueError as e:
            raise exc.RequestNotSupportedHwControlError from e

    def set_fm_manager_id(self) -> None:
        """
        Set fm_manager_id from information of deviceIdManager.

        This method gets the 'FM Manager ID' of the specified device from app.common.deviceIdManager
        and set self.fm_manager_id.


        Args:
            None

        Returns:
            None

        Raises:
            ValueError:
            - The 'FM Manager ID' could not be obtained from deviceIdManager.

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

        fm_manager_id = raw_manager_ids.get("fm")
        if not fm_manager_id:
            raise ValueError("The 'FM Manager ID' could not be obtained.")
        self.fm_manager_id = fm_manager_id

    def set_fm_port_id(self) -> None:
        """set fm_port_id from information of deviceIdManager.

        This method gets the 'FM Port ID' of the specified device
        from deviceIdManager and set self.fm_port_id.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError:
            - The specified device 'Device Type' is a switch.
            - The 'FM Port ID' could not be obtained from deviceIdManager.

            DeviceNotFoundHwControlError:
                The specified device is not found.

            Raise the following exception thrown from device_id_to_fm_port_id.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_ID_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_ID_info.json file did not exist
                in "/app/common/device_id_manager/".

        """

        try:
            raw_fm_port_id = deviceIdManager.device_id_to_fm_port_id(device_id=self.device_id)
        # ApiUsageHwControlError: Raised when the specified device_id
        # is an invalid UUID.
        # DeviceIdNotFoundHwControlError: Raised when the specified
        # device_id does not exist in device id manager.
        except (exc.ApiUsageHwControlError, exc.DeviceIdNotFoundHwControlError) as e:
            raise exc.DeviceNotFoundHwControlError(
                additional_message=f"The target Device ID is follow: {self.device_id}"
            ) from e
        # InvalidTypeDeviceIdHwControlError: Raised when the specified
        # device_id is the device id of the Switch.
        except exc.InvalidTypeDeviceIdHwControlError as e:
            raise ValueError("The specified device 'Device Type' is a switch.") from e

        if not raw_fm_port_id:
            raise ValueError("The 'FM Port ID' could not be obtained.")
        self.fm_port_id = raw_fm_port_id

    def set_switch_port_type(self) -> None:
        """Set switch_port_type from information of deviceIdManager.

        This method gets the 'Switch Port Type' of the specified device
        from deviceIdManager and set self.switch_port_type.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError:
                The 'Switch Port Type' could not be obtained from deviceIdManager.

            DeviceNotFoundHwControlError:
                The specified device is not found.

            Raise the following exception thrown from
            device_id_to_switch_port_type.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_ID_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_ID_info.json file did not exist
                in "/app/common/device_id_manager/".
                device_id_to_switch_port_type

        """
        try:
            raw_switch_port_type = deviceIdManager.device_id_to_switch_port_type(device_id=self.device_id)
        # ApiUsageHwControlError: Raised when the specified device_id
        # is an invalid UUID.
        # DeviceIdNotFoundHwControlError: Raised when the specified
        # device_id does not exist in device id manager.
        except (exc.ApiUsageHwControlError, exc.DeviceIdNotFoundHwControlError) as e:
            raise exc.DeviceNotFoundHwControlError(
                additional_message=f"The target Device ID is follow: {self.device_id}"
            ) from e
        if not raw_switch_port_type:
            raise ValueError("The 'Switch Port Type' could not be obtained.")
        self.switch_port_type = raw_switch_port_type


class FmControlTargetDevicePair(BaseModel):
    """Data class for holding control target device pair information.

    Holds the information of the target-device-pair for conducting fm-control.

    Attributes:
        host_cpu (FmControlTargetDevice):
            Holds the information of the control target host-cpu.

        target_device (FmControlTargetDevice):
            Holds the information of the control target device.

    """

    host_cpu: FmControlTargetDevice
    target_device: FmControlTargetDevice

    def model_post_init(self, __context):
        """Post-initialization method for FmControlTargetDevicePair.

        This method is called after the initialization of an instance of FmControlTargetDevicePair.

        Raises:
            RequestNotSupportedHwControlError:
                Raised if the device_id of host_cpu and target_device are the same.
        """
        if self.host_cpu.device_id == self.target_device.device_id:
            raise exc.RequestNotSupportedHwControlError

    def get_lock(self) -> None:
        """get host-cpu and target-device lock.

        get host-cpu and target-device lock.

        Args:
            None

        Returns:
            None

        Raises:
            exc.DeviceBusyHwControlError:
                specified target_device is Busy.

        """

        self.target_device.get_lock()

        try:
            self.host_cpu.get_lock()
        except exc.DeviceBusyHwControlError as e:
            self.target_device.release_lock()
            raise e

    def release_lock(self) -> None:
        """release host-cpu and target-device lock.

        release host-cpu and target-device lock.

        Args:
            None

        Returns:
            None

        """

        self.host_cpu.release_lock()
        self.target_device.release_lock()


class FmController:
    """Perform operations using FM.

    Execute control through FM.

    Attributes:
        None

    """

    @staticmethod
    def connect(device_pair: FmControlTargetDevicePair) -> None:
        """connect the host-cpu to the other device.

        Args:
            device_pair (FmControlTargetDevicePair):
                Represents control target device pair.

        Returns:
            None

        Raises:
            exc.UnexpectedExceptionHwControlError:
                FM-plugin raise Unexpected Exception.
        """

        # Raise RequestNotSupportedHwControlError when the following cases occur.
        # 1. The switch_port_type of the specified host_cpu is not "USP".
        # 2. switch_port_type of the specified target_device is not "DSP".
        # 3. The fm_manager_id of the specified host_cpu and  host_cpu do not match.
        if (
            device_pair.host_cpu.switch_port_type != constants.SwitchPortType.USP.value
            or device_pair.target_device.switch_port_type != constants.SwitchPortType.DSP.value
        ):
            raise exc.RequestNotSupportedHwControlError

        if device_pair.host_cpu.fm_manager_id != device_pair.target_device.fm_manager_id:
            raise exc.RequestNotSupportedHwControlError

        plugin = plugin_manager.get_plugin(
            manager_type=constants.ManagerType.FM.value, manager_id=device_pair.host_cpu.fm_manager_id
        )
        fm_plugin = cast(FMPluginBase, plugin)

        try:

            LOGGER.info(
                message=message.PluginCallLog(
                    manager_type=constants.ManagerType.FM.value,
                    manager_id=device_pair.host_cpu.fm_manager_id,
                    class_name=plugin.__class__.__name__,
                    method_name="connect",
                ).to_json_encodable()
            )

            fm_plugin.connect(
                device_pair.host_cpu.fm_port_id,
                device_pair.target_device.fm_port_id,
            )

        except exc.HostCpuAndDeviceNotFoundHwControlError as e:
            e.append_error_message(
                (
                    "The target Device IDs are follow: "
                    f"{device_pair.host_cpu.device_id}, {device_pair.target_device.device_id}"
                )
            )
            raise
        except exc.HostCpuNotFoundHwControlError as e:
            e.append_error_message(f"The target Device ID is follow: {device_pair.host_cpu.device_id}")
            raise
        except exc.DeviceNotFoundHwControlError as e:
            e.append_error_message(f"The target Device ID is follow: {device_pair.target_device.device_id}")
            raise
        except exc.BaseHwControlError:
            raise
        # Raise UnexpectedExceptionHwControlError
        # when FM-plugin raise Unexpected Exception.
        except Exception as e:
            raise exc.UnexpectedExceptionHwControlError from e

    @staticmethod
    def disconnect(device_pair: FmControlTargetDevicePair) -> None:
        """disconnect the host-cpu to the other device.

        Args:
            device_pair (FmControlTargetDevicePair):
                Represents control target device pair.

        Returns:
            None

        Raises:
            exc.UnexpectedExceptionHwControlError:
                FM-plugin raise Unexpected Exception.
        """

        if (
            device_pair.host_cpu.switch_port_type != constants.SwitchPortType.USP.value
            or device_pair.target_device.switch_port_type != constants.SwitchPortType.DSP.value
        ):
            raise exc.RequestNotSupportedHwControlError

        if device_pair.host_cpu.fm_manager_id != device_pair.target_device.fm_manager_id:
            raise exc.RequestNotSupportedHwControlError

        plugin = plugin_manager.get_plugin(
            manager_type=constants.ManagerType.FM.value, manager_id=device_pair.host_cpu.fm_manager_id
        )
        fm_plugin = cast(FMPluginBase, plugin)

        LOGGER.info(
            message=message.PluginCallLog(
                manager_type=constants.ManagerType.FM.value,
                manager_id=device_pair.host_cpu.fm_manager_id,
                class_name=plugin.__class__.__name__,
                method_name="disconnect",
            ).to_json_encodable()
        )

        try:

            fm_plugin.disconnect(
                device_pair.host_cpu.fm_port_id,
                device_pair.target_device.fm_port_id,
            )

        except exc.HostCpuAndDeviceNotFoundHwControlError as e:
            e.append_error_message(
                (
                    "The target Device IDs are follow: "
                    f"{device_pair.host_cpu.device_id}, {device_pair.target_device.device_id}"
                )
            )
            raise
        except exc.HostCpuNotFoundHwControlError as e:
            e.append_error_message(f"The target Device ID is follow: {device_pair.host_cpu.device_id}")
            raise
        except exc.DeviceNotFoundHwControlError as e:
            e.append_error_message(f"The target Device ID is follow: {device_pair.target_device.device_id}")
            raise
        except exc.BaseHwControlError:
            raise
        # Raise UnexpectedExceptionHwControlError
        # when FM-plugin raise Unexpected Exception.
        except Exception as e:
            raise exc.UnexpectedExceptionHwControlError from e

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

"""Module that defined the base class of an Fabric Manager plug-in

File: hw-control/src/app/common/utils/fm_plugin_base.py
"""

import abc
from abc import ABCMeta
from typing import Dict, Optional, List, Literal, Self
from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator, model_validator
from app.common.utils.plugin_base import ManagerPluginBase


_HEXADECIMAL = r"^[0-9a-fA-F]*$"


class FmPortData(BaseModel):
    """FM Port Data Class
    Defines types of port data's field

    Class Name:
        FmPortData

    Raises:
        pydantic.ValidationError
    """

    model_config = ConfigDict(validate_assignment=True)
    id: StrictStr
    switch_id: Optional[StrictStr] = Field(None, alias="switchId")
    switch_port_number: Optional[StrictStr] = Field(None, alias="switchPortNumber")
    switch_port_type: Optional[Literal["USP", "DSP"]] = Field(None, alias="switchPortType")
    fabric_id: Optional[StrictStr] = Field(None, alias="fabricId")
    link: Optional[List[str]] = Field(None)
    device_type: Optional[
        Literal["CXL-Type1", "CXL-Type2", "CXL-Type3", "CXL-Type3-MLD", "PCIe", "Undetected", "Other", "Unknown"]
    ] = Field(None, alias="deviceType")
    pci_class_code: Optional[Dict[str, int]] = Field(None, min_length=3, max_length=3, alias="PCIClassCode")
    pcie_vendor_id: Optional[StrictStr] = Field(
        None, min_length=4, max_length=4, pattern=_HEXADECIMAL, alias="PCIeVendorId"
    )
    pcie_device_id: Optional[StrictStr] = Field(
        None, min_length=4, max_length=4, pattern=_HEXADECIMAL, alias="PCIeDeviceId"
    )
    pcie_device_serial_number: Optional[StrictStr] = Field(
        None, min_length=16, max_length=16, pattern=_HEXADECIMAL, alias="PCIeDeviceSerialNumber"
    )
    cpu_manufacturer: Optional[StrictStr] = Field(None, alias="CPUManufacturer")
    cpu_model: Optional[StrictStr] = Field(None, alias="CPUModel")
    cpu_serial_number: Optional[StrictStr] = Field(None, alias="CPUSerialNumber")
    ltssm_state: Optional[
        Literal["L0", "L0s", "L2", "Detect", "Polling", "Configuration", "Recovery", "HotReset", "Disable", "Loopback"]
    ] = Field(None, alias="LTSSMState")
    device_keys: dict = Field({}, alias="deviceKeys")
    port_keys: dict = Field({}, alias="portKeys")
    capacity: Optional[Dict[str, StrictInt]] = Field(None, min_length=1, max_length=3)

    @field_validator("pci_class_code")
    @classmethod
    def validate_pci_class_code(cls, value):
        """This method validates the value to be set for pci_class_code.

        The pci_class_code must be as follows:
         - {'base': 0-255, 'sub': 0-255, 'prog': 0-255}

        Method Name:
            validate_pci_class_code

        Args:
            value (Optional[Dict[str, int]]): The value to set for
                pci_class_code.

        Returns:
            The value set for pci_class_code.
        """
        if value is None:
            return value
        if set(["base", "sub", "prog"]) != set(value.keys()) or len([x for x in value.values() if 0 <= x < 0x100]) != 3:
            raise ValueError
        return value

    @staticmethod
    def _fix_capacity(value: dict):
        """This static method fills in any missing items in capacity.

        Method Name:
            _fix_capacity

        Args:
            value (Dict[str, StrictInt]): The value to set for capacity.

        Returns:
            None

        Notes:
            The argument value may be updated within this method.
        """
        if len(value) == 1:
            if "volatile" in value:
                value["total"] = value["volatile"]
                value["persistent"] = 0
            elif "persistent" in value:
                value["total"] = value["persistent"]
                value["volatile"] = 0
        elif len(value) == 2:
            if "volatile" in value and "persistent" in value:
                value["total"] = value["volatile"] + value["persistent"]
            elif "volatile" in value and "total" in value:
                value["persistent"] = value["total"] - value["volatile"]
            elif "persistent" in value and "total" in value:
                value["volatile"] = value["total"] - value["persistent"]

    @field_validator("capacity")
    @classmethod
    def validate_capacity(cls, value):
        """This method validates the value to be set for capacity.

        Method Name:
            validate_capacity

        Args:
            value (Optional[Dict[str, StrictInt]]): The value to set for
                capacity.

        Returns:
            The value set for capacity.
        """
        if value is None:
            return value

        cls._fix_capacity(value)
        if "volatile" not in value or "persistent" not in value or "total" not in value:
            raise ValueError
        if (
            value["total"] != value["persistent"] + value["volatile"]
            or value["total"] < 0
            or value["persistent"] < 0
            or value["volatile"] < 0
        ):
            raise ValueError
        return value

    @model_validator(mode="after")
    def validate_port_type_cpu_pcie(self) -> Self:
        """
        PCIe data must be None if switchPortType is USP,
        CPU data must be None if switchPortType is DSP

        Method Name:
            validate_port_type_cpu_pcie

        Args:
            None

        Returns:
            FmPortData class instance.
        """
        if self.switch_port_type == "USP" and (
            self.pcie_vendor_id is not None
            or self.pcie_device_id is not None
            or self.pcie_device_serial_number is not None
        ):
            raise ValueError
        if self.switch_port_type == "DSP" and (
            self.cpu_manufacturer is not None or self.cpu_model is not None or self.cpu_serial_number is not None
        ):
            raise ValueError
        return self


class FmSwitchData(BaseModel):
    """FM Switch Data Class
    Defines types of switch data's field

    Class Name:
        FmSwitchData

    Raises:
        pydantic.ValidationError
    """

    model_config = ConfigDict(validate_assignment=True)
    switch_id: StrictStr = Field(..., alias="switchId")
    switch_manufacturer: Optional[StrictStr] = Field(None, alias="switchManufacturer")
    switch_model: Optional[StrictStr] = Field(None, alias="switchModel")
    switch_serial_number: Optional[StrictStr] = Field(None, alias="switchSerialNumber")
    link: Optional[List[str]] = Field(None)


class FMPluginBase(ManagerPluginBase, metaclass=ABCMeta):
    """It defines the base class of an FM(Fabric Manager) plug-in

    This class defines the methods that the FM plug-in must implement.
    FM plug-ins must inherit from this class.
    This class inherits from ManagerPluginBase.

    Class Name:
        FMPluginBase

    Raises:
        The FM plug-in may raise the following exception defined for
        app.common.basic_exceptions module:
            - HostCpuNotFoundHwControlError
            - DeviceNotFoundHwControlError
            - HostCpuAndDeviceNotFoundHwControlError
            - ResourceNotFoundHwControlError
            - SwitchNotFoundHwControlError
            - RequestConflictHwControlError
            - BadRequestHwControlError
            - AuthenticationHwControlError
            - FmConnectFailureHwControlError
            - FmDisconnectFailureHwControlError
            - ControlObjectHwControlError
            - ConfigurationHwControlError
            - InternalHwControlError
            - UnknownHwControlError
        The FM plug-in may also raise vendor-specific exceptions that
        inherit BaseHwControlError.
    """

    # FM API definition
    @abc.abstractmethod
    def connect(self, cpu_id: str, device_id: str) -> None:
        """Definition of an API for the connection

        FM plug-ins should provide the ability to connect upstream and
        downstream ports with this method.

        Method Name:
            connect

        Args:
            cpu_id (str): Unique id associated with the up stream port.
            device_id (str): Unique id associated with the down stream
                port.

        Returns:
            None
        """

    @abc.abstractmethod
    def disconnect(self, cpu_id: str, device_id: str) -> None:
        """Definition of an API for the disconnecting.

        FM plug-ins should provide the ability to disconnect upstream
        and downstream ports with this method.

        Method Name:
            disconnect

        Args:
            cpu_id (str): Unique id associated with the up stream port.
            device_id (str): Unique id associated with the down stream
                port.

        Returns:
            None
        """

    @abc.abstractmethod
    def get_port_info(self, target_id: Optional[str] = None) -> dict:
        """Definition of an API for get information.

        The FM plug-in should provide the ability to return port
        information with this method.

        Method Name:
            get_port_info

        Args:
            target_id (str): Optional.
                Specify the id of the data you want to acquire.
                If omitted, all data of up and down stream ports.

        Returns:
            A dictionary-type data with the "data" key.
            The value of the "data" key is a list of FmPortData class
            instances.
            If an argument is specified, the list contains only one
            specified port.
            If no argument is specified, the list contains all the ports
            retrieved.
        """

    @abc.abstractmethod
    def get_switch_info(self, switch_id: Optional[str] = None) -> dict:
        """Definition of an API for get information of switch.

        The FM plug-in should provide the ability to return switch
        information with this method.

        Method Name:
            get_switch_info

        Args:
            switch_id (str): Optional.
                Specify the id of the data you want to acquire.
                If omitted, all data of switches managed by FM.

        Returns:
            A dictionary-type data with the "data" key.
            The value of the "data" key is a list of FmPortData class
            instances.
            If an argument is specified, the list contains only one
            specified switch.
            If no argument is specified, the list contains all the
            switches retrieved.
        """

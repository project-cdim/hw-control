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

"""Module that defined the base class of an OOB plug-in.

File: hw-control/src/app/common/utils/oob_plugin_base.py
"""

import abc
from abc import ABCMeta

from pydantic import BaseModel, Field

from app.common.utils.plugin_base import ManagerPluginBase


class OOBDeviceListItem(BaseModel, validate_assignment=True):
    """Information identifying an OOB device."""

    pcie_vendor_id: str | None = Field(None, alias="PCIeVendorId")
    pcie_device_id: str | None = Field(None, alias="PCIeDeviceId")
    pcie_device_serial_number: str | None = Field(None, alias="PCIeDeviceSerialNumber")
    cpu_serial_number: str | None = Field(None, alias="CPUSerialNumber")
    cpu_manufacturer: str | None = Field(None, alias="CPUManufacturer")
    cpu_model: str | None = Field(None, alias="CPUModel")
    port_keys: dict | None = Field(None, alias="portKeys")
    device_keys: dict | None = Field(None, alias="deviceKeys")
    device_type: str = Field(alias="deviceType")
    oob_device_id: str = Field(alias="oobDeviceID")


class OOBPluginBase(ManagerPluginBase, metaclass=ABCMeta):
    """The base class of OOB plug-in.

    This class defines the methods that the OOB plug-in must implement.
    """

    @abc.abstractmethod
    def get_spec_info(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        """Get device information.

        Get the specification information of the devices identified by the OOB Device IDs.

        Args:
            key_values (list[dict[str, str]]): a list of dictionaries containing OOB Device IDs (oob_device_id)
                                               and Device Types (device_type)

        Returns:
            dict[str, list[dict]]: the device information obtained from the Manager
        """

    @abc.abstractmethod
    def get_metric_info(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        """Get metric information.

        Get the metric information of the devices identified by the OOB Device IDs.

        Args:
            key_values (list[dict[str, str]]): a list of dictionaries containing OOB Device IDs (oob_device_id)
                                               and Device Types (device_type)

        Returns:
            dict[str, list[dict]]: the metric information obtained from the Manager
        """

    @abc.abstractmethod
    def get_power_state(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        """Get power state.

        Get the power state of the devices identified by the OOB Device IDs.

        Args:
            key_values (list[dict[str, str]]): a list of dictionaries containing OOB Device IDs (oob_device_id)
                                               and Device Types (device_type)

        Returns:
            dict[str, list[dict]]: the power state obtained from the Manager
        """

    @abc.abstractmethod
    def get_device_info(self) -> list[OOBDeviceListItem]:
        """Get identifying information.

        Get the information that identifies the OOB device.

        Args:
            None

        Returns:
            list[OOBDeviceListItem]: the identifying information obtained from the Manager
        """

    @abc.abstractmethod
    def post_power_on(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        """Power on.

        Power on the devices identified by the OOB Device IDs.

        Args:
            key_values (list[dict[str, str]]): a list of dictionaries containing OOB Device IDs (oob_device_id)
                                               and Device Types (device_type)

        Returns:
            dict[str, list[dict]]: execution status
        """

    @abc.abstractmethod
    def post_power_off(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        """Power off.

        Power off the devices identified by the OOB Device IDs.

        Args:
            key_values (list[dict[str, str]]): a list of dictionaries containing OOB Device IDs (oob_device_id)
                                               and Device Types (device_type)

        Returns:
            dict[str, list[dict]]: execution status
        """

    @abc.abstractmethod
    def post_cpu_reset(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        """Reset CPU.

        Reset the CPUs identified by the OOB Device IDs.

        Args:
            key_values (list[dict[str, str]]): a list of dictionaries containing OOB Device IDs (oob_device_id)
                                               and Device Types (device_type)

        Returns:
            dict[str, list[dict]]: execution status
        """

    @abc.abstractmethod
    def post_os_shutdown(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        """Shutdown OS.

        Shutdown the OS running on the devices identified by the OOB Device IDs.

        Args:
            key_values (list[dict[str, str]]): a list of dictionaries containing OOB Device IDs (oob_device_id)
                                               and Device Types (device_type)

        Returns:
            dict[str, list[dict]]: execution status
        """

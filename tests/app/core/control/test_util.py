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

"""This module define Utilities for app.core.control."""

from enum import Enum

from app.common import constants
from app.common.utils.fm_plugin_base import FMPluginBase, FMPortData, FMSwitchData
from app.common.utils.oob_plugin_base import OOBPluginBase, OOBDeviceListItem

# ++++ test data ++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class DummyCPUInfo(Enum):
    """Define a collection of name/plugin_type value pairs."""

    DEVICE_ID = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"
    DEVICE_TYPE = constants.DeviceType.CPU.value
    FM_PORT_ID = "852f416b-a6e7-4d32-b9c4-238901544d48"
    OOB_DEVICE_ID = "0001"
    FM_MANAGER_ID = "7_77-abc777"
    OOB_MANAGER_ID = "1111111_abc"
    UP_DOWN = constants.SwitchPortType.USP.value
    SWITCH_PORT_TYPE = constants.SwitchPortType.USP.value
    IP_ADDRESS = "11.11.11.11"


class DummyDeviceInfo(Enum):
    """Define a collection of name/plugin_type value pairs."""

    DEVICE_ID = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"
    DEVICE_TYPE = constants.DeviceType.MEMORY.value
    FM_PORT_ID = "eed37ccf-293e-4da4-aeef-f42843192f53"
    OOB_DEVICE_ID = "0002"
    FM_MANAGER_ID = "7_77-abc777"
    OOB_MANAGER_ID = "1111111_abc"
    UP_DOWN = constants.SwitchPortType.DSP.value
    SWITCH_PORT_TYPE = constants.SwitchPortType.DSP.value


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


# ++++ side effect of mock ++++++++++++++++++++++++++++++++++++++++++++#
class DummyFMPlugin(FMPluginBase):
    """Dummy FM Plugin class for UT."""

    def connect(self, cpu_id: str, device_id: str) -> None:
        """Dummy connect method."""
        return None

    def disconnect(self, cpu_id: str, device_id: str) -> None:
        """Dummy disconnect method."""
        return None

    def get_port_info(self, target_id: str | None = None) -> dict[str, list[FMPortData]]:
        """Dummy get_port_info method ."""
        return {}

    def get_switch_info(self, switch_id: str | None = None) -> dict[str, list[FMSwitchData]]:
        """Dummy get_port_info method ."""
        return {}


class DummyOOBPlugin(OOBPluginBase):
    """Dummy OOB Plugin class for UT."""

    def get_spec_info(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        """Dummy get_spec_info method."""
        return {}

    def get_metric_info(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        """Dummy get_metric_info method."""
        return {}

    def get_power_state(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        """Dummy get_power_state method."""
        return {}

    def get_device_info(self) -> list[OOBDeviceListItem]:
        """Dummy get_device_info method."""
        return []

    def post_power_on(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        """Dummy post_power_on method."""
        return {}

    def post_power_off(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        """Dummy post_power_off method."""
        return {}

    def post_cpu_reset(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        """Dummy post_cpu_reset method."""
        return {}

    def post_os_shutdown(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        """Dummy post_os_shutdown method."""
        return {}

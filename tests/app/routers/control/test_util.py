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

"""unit test util"""
from enum import Enum

from app.common import constants  # type: ignore

CONSTANT_REQUEST_ID = "test_request_id"


class DummyCpuInfo(Enum):
    """Define a collection of name/plugin_type value pairs."""

    DEVICE_ID = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"
    DEVICE_TYPE = constants.DeviceType.CPU.value
    FM_PORT_ID = "852f416b-a6e7-4d32-b9c4-238901544d48"
    OOB_DEVICE_ID = "0001"
    FM_MANAGER_ID = "7_77-abc777"
    OOB_MANAGER_ID = "1111111_abc"
    UP_DOWN = constants.SwitchPortType.USP.value
    SWITCH_PORT_TYPE = constants.SwitchPortType.USP.value
    IP_ADDRESS = "192.168.122.11"


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

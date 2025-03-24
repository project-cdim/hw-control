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

"""This is a test program."""

from app.common.constants import DeviceType


def test_device_type_enum_unique():
    """Test that the number of types of ENUM values is correct (must be unique)
    """
    # Verify that the number of ENUM values is correct (unique).
    device_types = set(item.value for item in DeviceType)
    assert len(device_types) == 8


def test_device_type_enum_member_value():
    """Test the value of ENUM member
    """
    assert DeviceType.CPU.value == "CPU"
    assert DeviceType.MEMORY.value == "memory"
    assert DeviceType.STORAGE.value == "storage"
    assert DeviceType.NIC.value == "networkInterface"
    assert DeviceType.GPU.value == "GPU"
    assert DeviceType.GC.value == "graphicController"
    assert DeviceType.SWITCH.value == "switch"
    assert DeviceType.VM.value == "virtualMedia"

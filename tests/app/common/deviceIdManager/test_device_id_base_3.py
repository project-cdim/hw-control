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

# pylint: disable=R0801
"""unit test module in device_ID_base.py (part 3)

system under test
/app/common/deviceIdManager/device_id_base.py

Test target function:
device_id_to_manager_id_multi_host
device_id_to_fm_switch_id
fm_switch_id_to_device_id
"""

import pytest
import pandas as pd
from pytest_mock import MockFixture
import app.common.basic_exceptions as exc

## system under test ###################
from app.common.deviceIdManager import device_id_base as dim

dummy_device_id_info = [
    {
        "DeviceID": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
        "deviceType": "CPU",
        "fmPortID": "852f416b-a6e7-4d32-b9c4-238901544d48",
        "oobDeviceID": "0001",
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "123456789",
        "CPUManufacturer": "AMD",
        "CPUModel": "ABCDEF",
        "fmSwitchID": None,
        "connectedFmSwitchID": "connect_fm_switch_id",
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": "test_1",
        "oobManagerID": "1111111_abc",
        "portKeys": None,
        "deviceKeys": {"SimulatedDeviceID": None, "MemorySerialNumber": None},
        "switchPortType": "USP",
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "b9f9b678-bce8-49a1-bca3-dbbc32259abf",
        "deviceType": "memory",
        "fmPortID": "eed37ccf-293e-4da4-aeef-f42843192f53",
        "oobDeviceID": "0002",
        "PCIeVendorId": "1af4",
        "PCIeDeviceId": "1042",
        "PCIeDeviceSerialNumber": "deadbeef00000007",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": None,
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": "6_66-abc666",
        "oobManagerID": None,
        "portKeys": {"GIGAIODSPSlot": "2", "GIGAIODSPPort": "9"},
        "deviceKeys": {"SimulatedDeviceID": "0002", "MemorySerialNumber": "123456789"},
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "b9f9b678-bce8-49a1-bca3-dbbc32259abk",
        "deviceType": "memory",
        "fmPortID": "eed37ccf-293e-4da4-aeef-f42843192f53",
        "oobDeviceID": "0003",
        "PCIeVendorId": "1af5",
        "PCIeDeviceId": "1043",
        "PCIeDeviceSerialNumber": "deadbeef00000009",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "fm_switch_id",
        "connectedFmSwitchID": "connect_fm_switch_id",
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": "6_66-abc666",
        "oobManagerID": None,
        "portKeys": {"GIGAIODSPSlot": "2", "GIGAIODSPPort": "9"},
        "deviceKeys": {"SimulatedDeviceID": "0002", "MemorySerialNumber": "123456789"},
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "e9345fcb-4951-4da8-a569-358b00361083",
        "deviceType": "switch",
        "fmPortID": None,
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "fm_switch_id",
        "connectedFmSwitchID": None,
        "switchSerialNumber": "switch_serial_number",
        "switchManufacturer": "switch_manufacturer",
        "switchModel": "switch_model",
        "fmManagerID": "7_77-abc777",
        "oobManagerID": None,
        "portKeys": None,
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": False,
        "valid": True,
    },
    {
        "DeviceID": "e9345fcb-4951-4da8-a569-358b00361084",
        "deviceType": "switch",
        "fmPortID": None,
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "fm_switch_id",
        "connectedFmSwitchID": None,
        "switchSerialNumber": "switch_serial_number_2",
        "switchManufacturer": "switch_manufacturer_2",
        "switchModel": "switch_model_2",
        "fmManagerID": "7_77-abc777",
        "oobManagerID": None,
        "portKeys": None,
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "e9345fcb-4951-4da8-a569-358b00361085",
        "deviceType": "switch",
        "fmPortID": None,
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "fm_switch_id",
        "connectedFmSwitchID": None,
        "switchSerialNumber": "switch_serial_number_3",
        "switchManufacturer": "switch_manufacturer_3",
        "switchModel": "switch_model_3",
        "fmManagerID": "7_77-abc777",
        "oobManagerID": None,
        "portKeys": None,
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "6409b69d-232e-4e83-8f69-40914a103ae6",
        "deviceType": None,
        "fmPortID": None,
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": None,
        "oobManagerID": None,
        "portKeys": None,
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": True,
        "valid": True,
    },
]

dummy_device_id_info_ite12 = [
    {
        "DeviceID": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
        "deviceType": "CPU",
        "fmPortID": {"test_1": ["852f416b-a6e7-4d32-b9c4-238901544d48"]},
        "oobDeviceID": "0001",
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "123456789",
        "CPUManufacturer": "AMD",
        "CPUModel": "ABCDEF",
        "fmSwitchID": None,
        "connectedFmSwitchID": {"test_1": ["connect_fm_switch_id"]},
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": ["test_1"],
        "oobManagerID": ["1111111_abc"],
        "portKeys": None,
        "deviceKeys": {"SimulatedDeviceID": None, "MemorySerialNumber": None},
        "switchPortType": "USP",
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "b9f9b678-bce8-49a1-bca3-dbbc32259abf",
        "deviceType": "memory",
        "fmPortID": {"6_66-abc666": ["eed37ccf-293e-4da4-aeef-f42843192f53"]},
        "oobDeviceID": "0002",
        "PCIeVendorId": "1af4",
        "PCIeDeviceId": "1042",
        "PCIeDeviceSerialNumber": "deadbeef00000007",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": {"6_66-abc666": []},
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": ["6_66-abc666"],
        "oobManagerID": [],
        "portKeys": {"GIGAIODSPSlot": "2", "GIGAIODSPPort": "9"},
        "deviceKeys": {"SimulatedDeviceID": "0002", "MemorySerialNumber": "123456789"},
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "b9f9b678-bce8-49a1-bca3-dbbc32259abk",
        "deviceType": "memory",
        "fmPortID": {"6_66-abc666": ["eed37ccf-293e-4da4-aeef-f42843192f53"]},
        "oobDeviceID": "0003",
        "PCIeVendorId": "1af5",
        "PCIeDeviceId": "1043",
        "PCIeDeviceSerialNumber": "deadbeef00000009",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "fm_switch_id",
        "connectedFmSwitchID": {"6_66-abc666": ["connect_fm_switch_id"]},
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": ["6_66-abc666"],
        "oobManagerID": [],
        "portKeys": {"GIGAIODSPSlot": "2", "GIGAIODSPPort": "9"},
        "deviceKeys": {"SimulatedDeviceID": "0002", "MemorySerialNumber": "123456789"},
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "e9345fcb-4951-4da8-a569-358b00361083",
        "deviceType": "switch",
        "fmPortID": {"7_77-abc777": []},
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "fm_switch_id",
        "connectedFmSwitchID": {"7_77-abc777": []},
        "switchSerialNumber": "switch_serial_number",
        "switchManufacturer": "switch_manufacturer",
        "switchModel": "switch_model",
        "fmManagerID": ["7_77-abc777"],
        "oobManagerID": [],
        "portKeys": None,
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": False,
        "valid": True,
    },
    {
        "DeviceID": "e9345fcb-4951-4da8-a569-358b00361084",
        "deviceType": "switch",
        "fmPortID": {"7_77-abc777": []},
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "fm_switch_id",
        "connectedFmSwitchID": {"7_77-abc777": []},
        "switchSerialNumber": "switch_serial_number_2",
        "switchManufacturer": "switch_manufacturer_2",
        "switchModel": "switch_model_2",
        "fmManagerID": ["7_77-abc777"],
        "oobManagerID": [],
        "portKeys": None,
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "e9345fcb-4951-4da8-a569-358b00361085",
        "deviceType": "switch",
        "fmPortID": {"7_77-abc777": []},
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "fm_switch_id",
        "connectedFmSwitchID": {"7_77-abc777": []},
        "switchSerialNumber": "switch_serial_number_3",
        "switchManufacturer": "switch_manufacturer_3",
        "switchModel": "switch_model_3",
        "fmManagerID": ["7_77-abc777"],
        "oobManagerID": [],
        "portKeys": None,
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "6409b69d-232e-4e83-8f69-40914a103ae6",
        "deviceType": None,
        "fmPortID": {},
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": {},
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": [],
        "oobManagerID": [],
        "portKeys": None,
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": True,
        "valid": True,
    },
]

dummy_device_id_info_oob = [
    {
        "DeviceID": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
        "deviceType": "CPU",
        "fmPortID": "852f416b-a6e7-4d32-b9c4-238901544d48",
        "oobDeviceID": "0001",
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "123456789",
        "CPUManufacturer": "AMD",
        "CPUModel": "ABCDEF",
        "fmSwitchID": None,
        "connectedFmSwitchID": "connect_fm_switch_id",
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": None,
        "oobManagerID": "1111111_abc",
        "portKeys": None,
        "deviceKeys": {"SimulatedDeviceID": None, "MemorySerialNumber": None},
        "switchPortType": "USP",
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "b9f9b678-bce8-49a1-bca3-dbbc32259abf",
        "deviceType": "memory",
        "fmPortID": "eed37ccf-293e-4da4-aeef-f42843192f53",
        "oobDeviceID": "0002",
        "PCIeVendorId": "1af4",
        "PCIeDeviceId": "1042",
        "PCIeDeviceSerialNumber": "deadbeef00000007",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": {},
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": None,
        "oobManagerID": "6_66-abc666",
        "portKeys": {"GIGAIODSPSlot": "2", "GIGAIODSPPort": "9"},
        "deviceKeys": {"SimulatedDeviceID": "0002", "MemorySerialNumber": "123456789"},
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "b9f9b678-bce8-49a1-bca3-dbbc32259abk",
        "deviceType": "memory",
        "fmPortID": "eed37ccf-293e-4da4-aeef-f42843192f53",
        "oobDeviceID": "0003",
        "PCIeVendorId": "1af5",
        "PCIeDeviceId": "1043",
        "PCIeDeviceSerialNumber": "deadbeef00000009",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "fm_switch_id",
        "connectedFmSwitchID": "connect_fm_switch_id",
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": None,
        "oobManagerID": "6_66-abc666",
        "portKeys": {"GIGAIODSPSlot": "2", "GIGAIODSPPort": "9"},
        "deviceKeys": {"SimulatedDeviceID": "0002", "MemorySerialNumber": "123456789"},
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "e9345fcb-4951-4da8-a569-358b00361083",
        "deviceType": "switch",
        "fmPortID": None,
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "fm_switch_id",
        "connectedFmSwitchID": None,
        "switchSerialNumber": "switch_serial_number",
        "switchManufacturer": "switch_manufacturer",
        "switchModel": "switch_model",
        "fmManagerID": "7_77-abc777",
        "oobManagerID": None,
        "portKeys": None,
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": False,
        "valid": True,
    },
    {
        "DeviceID": "e9345fcb-4951-4da8-a569-358b00361084",
        "deviceType": "switch",
        "fmPortID": None,
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "fm_switch_id",
        "connectedFmSwitchID": None,
        "switchSerialNumber": "switch_serial_number_2",
        "switchManufacturer": "switch_manufacturer_2",
        "switchModel": "switch_model_2",
        "fmManagerID": "7_77-abc777",
        "oobManagerID": None,
        "portKeys": None,
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "e9345fcb-4951-4da8-a569-358b00361085",
        "deviceType": "switch",
        "fmPortID": None,
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "fm_switch_id",
        "connectedFmSwitchID": None,
        "switchSerialNumber": "switch_serial_number_3",
        "switchManufacturer": "switch_manufacturer_3",
        "switchModel": "switch_model_3",
        "fmManagerID": "7_77-abc777",
        "oobManagerID": None,
        "portKeys": None,
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "6409b69d-232e-4e83-8f69-40914a103ae6",
        "deviceType": None,
        "fmPortID": None,
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": None,
        "oobManagerID": None,
        "portKeys": None,
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": True,
        "valid": True,
    },
]

dummy_device_id_info_2_item = [
    {
        "DeviceID": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
        "deviceType": "CPU",
        "fmPortID": "852f416b-a6e7-4d32-b9c4-238901544d48",
        "oobDeviceID": "0001",
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "123456789",
        "CPUManufacturer": "AMD",
        "CPUModel": "ABCDEF",
        "fmSwitchID": None,
        "connectedFmSwitchID": "connect_fm_switch_id",
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": None,
        "oobManagerID": "1111111_abc",
        "portKeys": None,
        "deviceKeys": {"SimulatedDeviceID": None, "MemorySerialNumber": None},
        "switchPortType": "USP",
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "b9f9b678-bce8-49a1-bca3-dbbc32259abf",
        "deviceType": "memory",
        "fmPortID": "eed37ccf-293e-4da4-aeef-f42843192f53",
        "oobDeviceID": "0002",
        "PCIeVendorId": "1af4",
        "PCIeDeviceId": "1042",
        "PCIeDeviceSerialNumber": "deadbeef00000007",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": None,
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": "6_66-abc666",
        "oobManagerID": None,
        "portKeys": {"GIGAIODSPSlot": "2", "GIGAIODSPPort": "9"},
        "deviceKeys": {"SimulatedDeviceID": "0002", "MemorySerialNumber": "123456789"},
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": True,
    },
]

dummy_device_id_info_not_switch = [
    {
        "DeviceID": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
        "deviceType": "CPU",
        "fmPortID": "852f416b-a6e7-4d32-b9c4-238901544d48",
        "oobDeviceID": "0001",
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "123456789",
        "CPUManufacturer": "AMD",
        "CPUModel": "ABCDEF",
        "fmSwitchID": "not_sw",
        "connectedFmSwitchID": "connect_fm_switch_id",
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": None,
        "oobManagerID": "1111111_abc",
        "portKeys": None,
        "deviceKeys": {"SimulatedDeviceID": None, "MemorySerialNumber": None},
        "switchPortType": "USP",
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "b9f9b678-bce8-49a1-bca3-dbbc32259abf",
        "deviceType": "memory",
        "fmPortID": "eed37ccf-293e-4da4-aeef-f42843192f53",
        "oobDeviceID": "0002",
        "PCIeVendorId": "1af4",
        "PCIeDeviceId": "1042",
        "PCIeDeviceSerialNumber": "deadbeef00000007",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": None,
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": "6_66-abc666",
        "oobManagerID": None,
        "portKeys": {"GIGAIODSPSlot": "2", "GIGAIODSPPort": "9"},
        "deviceKeys": {"SimulatedDeviceID": "0002", "MemorySerialNumber": "123456789"},
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "b9f9b678-bce8-49a1-bca3-dbbc32259abk",
        "deviceType": "memory",
        "fmPortID": "eed37ccf-293e-4da4-aeef-f42843192f53",
        "oobDeviceID": "0003",
        "PCIeVendorId": "1af5",
        "PCIeDeviceId": "1043",
        "PCIeDeviceSerialNumber": "deadbeef00000009",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": "connect_fm_switch_id",
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": "6_66-abc666",
        "oobManagerID": None,
        "portKeys": {"GIGAIODSPSlot": "2", "GIGAIODSPPort": "9"},
        "deviceKeys": {"SimulatedDeviceID": "0002", "MemorySerialNumber": "123456789"},
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": True,
    },
]


class TestDeviceIdToManagerIdMultiHost:
    """Unit test class for device_id_to_manager_id_multi_hostport.

    SUT:/device_id_manager/device_ID_base.py/device_id_to_manager_id_multi_hostport
    """

    def test_successful_case_fm_manager(self, mocker: MockFixture):
        """Test successful case of .

        Expect sut return fm_manager_id.
        """
        # preparation
        expected = {"fm": ["6_66-abc666"], "oob": []}

        device_id = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_2_item)

        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.device_id_to_manager_id_multi_hostport(device_id)

        # inspection
        assert expected == actual

    def test_successful_case_fm_manager_ite12(self, mocker: MockFixture):
        """Test successful case of .

        Expect sut return fm_manager_id.
        """
        # preparation
        expected = {"fm": ["6_66-abc666"], "oob": []}

        device_id = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_2_item)
        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.device_id_to_manager_id_multi_hostport(device_id)

        # inspection
        assert expected == actual

    def test_successful_case_oob_manager(self, mocker: MockFixture):
        """Test successful case of .

        Expect sut return oob_manager_id.
        """
        # preparation
        expected = {"fm": [], "oob": ["1111111_abc"]}

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_2_item)
        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.device_id_to_manager_id_multi_hostport(device_id)

        # inspection
        assert expected == actual

    def test_device_already_disabled_sub_flow(self, mocker: MockFixture):
        """Test Device already disabled case.

        Test following cases.

            If specified device has been disabled.
            Expect sut return following dict.
                {'fm': None, 'oob': None}
        """
        dim.id_to_info = {}
        # preparation
        expected = {"fm": [], "oob": []}

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # disabled device
        device_id = "6409b69d-232e-4e83-8f69-40914a103ae6"

        # execution
        actual = dim.device_id_to_manager_id_multi_hostport(device_id)

        # inspection
        assert expected == actual

    def test_apiusagehwcontrolerror_case(self):
        """Test ApiUsageHwControlError case.

        Test for errors in the following cases.

            _is_valid_uuid raise ApiUsageHwControlError.
            Expect sut raise ApiUsageHwControlError.
        """
        # preparation
        device_id = "mogumogu"

        # execution
        with pytest.raises(exc.ApiUsageHwControlError):
            _ = dim.device_id_to_manager_id_multi_hostport(device_id)

    def test_empty_json_data_case(self, mocker: MockFixture):
        """Test Json file empty case.

        Test for errors in the following cases.

        _read_json_file return empty Json file such that

        {"data": []}

        Expect sut raise DeviceIdNotFoundHwControlError.
        """
        dim.id_to_info = {}
        # preparation
        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        empty_device_id_info = {}
        mocker.patch.object(dim, "_read_json_file", return_value=empty_device_id_info)

        # execution
        with pytest.raises(exc.DeviceIdNotFoundHwControlError):
            _ = dim.device_id_to_manager_id_multi_hostport(device_id)

    def test_deviceidfilenotfoundhwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIdFileNotFoundHwControlError case.

        Test for errors in the following cases.

            _read_json_file raise DeviceIdFileNotFoundHwControlError.
            Expect sut raise DeviceIdFileNotFoundHwControlError.
        """
        # preparation
        mocker.patch.object(dim, "_read_json_file", side_effect=exc.DeviceIdFileNotFoundHwControlError)

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        # execution
        with pytest.raises(exc.DeviceIdFileNotFoundHwControlError):
            _ = dim.device_id_to_manager_id_multi_hostport(device_id)

    def test_deviceidfileincorrecthwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIdFileIncorrectHwControlError case.

        Test for errors in the following cases.

            _read_json_file raise DeviceIdFileIncorrectHwControlError.
            Expect sut raise DeviceIdFileIncorrectHwControlError.
        """
        dim.id_to_info = {}

        # preparation
        mocker.patch.object(dim, "_read_json_file", side_effect=exc.DeviceIdFileIncorrectHwControlError)

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        # execution
        with pytest.raises(exc.DeviceIdFileIncorrectHwControlError):
            _ = dim.device_id_to_manager_id_multi_hostport(device_id)

    def test_deviceidnotfoundhwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIdNotFoundHwControlError case.

        Test for errors in the following cases.

            If the specified device is a switch.
            Expect sut raise DeviceIdNotFoundHwControlError.
        """
        dim.id_to_info = {}

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # nonexistent device ID
        device_id = "4d4f8988-ce27-4e6a-b83b-6309e4f7d5ad"

        # execution
        with pytest.raises(exc.DeviceIdNotFoundHwControlError):
            _ = dim.device_id_to_manager_id_multi_hostport(device_id)


class TestDeviceIdToFmSwitchId:
    """Unit test class for device_id_to_fm_switch_id.

    SUT:/device_id_manager/device_ID_base.py/device_id_to_fm_switch_id.
    """

    def test_successful_case(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return fm_switch_id.
        """
        # preparation
        expected = "fm_switch_id"

        device_id = "e9345fcb-4951-4da8-a569-358b00361083"
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_json_file", return_value=dummy_obtained_data)

        # execution
        actual = dim.device_id_to_fm_switch_id(device_id)

        # inspection
        assert expected == actual

    def test_successful_case_ite12(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return fm_switch_id.
        """
        # preparation
        expected = "fm_switch_id"

        device_id = "e9345fcb-4951-4da8-a569-358b00361083"

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_ite12)

        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.device_id_to_fm_switch_id(device_id)

        # inspection
        assert expected == actual

    def test_apiusagehwcontrolerror_case(self):
        """Test ApiUsageHwControlError case.

        Test for errors in the following cases.

            _is_valid_uuid raise ApiUsageHwControlError.
            Expect sut raise ApiUsageHwControlError.
        """
        # preparation
        device_id = "mogumogu"

        # execution
        with pytest.raises(exc.ApiUsageHwControlError):
            _ = dim.device_id_to_fm_switch_id(device_id)

    def test_empty_json_data_case(self, mocker: MockFixture):
        """Test Json file empty case.

        Test for errors in the following cases.

        _read_json_file return empty Json file such that

        {"data": []}

        Expect sut raise DeviceIdNotFoundHwControlError.
        """
        dim.id_to_info = {}
        # preparation
        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        empty_device_id_info = {}
        mocker.patch.object(dim, "_read_json_file", return_value=empty_device_id_info)

        # execution
        with pytest.raises(exc.DeviceIdNotFoundHwControlError):
            _ = dim.device_id_to_fm_switch_id(device_id)

    def test_invalidtypedeviceidhwcontrolerror_case(self, mocker: MockFixture):
        """Test InvalidTypeDeviceIdHwControlError case.

        Test following cases.

            If specified device is not Switch.
            Expect sut raise InvalidTypeDeviceIdHwControlError.
        """
        # preparation
        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")
        mocker.patch.object(dim, "_read_json_file", return_value=dummy_obtained_data)

        # execution
        with pytest.raises(exc.InvalidTypeDeviceIdHwControlError):
            _ = dim.device_id_to_fm_switch_id(device_id)

    def test_deviceidnotfoundhwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIdNotFoundHwControlError case.

        Test for errors in the following cases.

            If the specified device is a switch.
            Expect sut raise DeviceIdNotFoundHwControlError.
        """
        # preparation
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_json_file", return_value=dummy_obtained_data)

        # nonexistent deviceID
        device_id = "4d4f8988-ce27-4e6a-b83b-6309e4f7d5ad"

        # execution
        with pytest.raises(exc.DeviceIdNotFoundHwControlError):
            _ = dim.device_id_to_fm_switch_id(device_id)

    def test_deviceidfilenotfoundhwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIdFileNotFoundHwControlError case.

        Test for errors in the following cases.

            _read_json_file raise DeviceIdFileNotFoundHwControlError.
            Expect sut raise DeviceIdFileNotFoundHwControlError.
        """
        dim.id_to_info = {}

        # preparation
        mocker.patch.object(dim, "_read_json_file", side_effect=exc.DeviceIdFileNotFoundHwControlError)

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        # execution
        with pytest.raises(exc.DeviceIdFileNotFoundHwControlError):
            _ = dim.device_id_to_fm_switch_id(device_id)

    def test_deviceidfileincorrecthwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIdFileIncorrectHwControlError case.

        Test for errors in the following cases.

            _read_json_file raise DeviceIdFileIncorrectHwControlError.
            Expect sut raise DeviceIdFileIncorrectHwControlError.
        """
        dim.id_to_info = {}

        # preparation
        mocker.patch.object(dim, "_read_json_file", side_effect=exc.DeviceIdFileIncorrectHwControlError)
        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        # execution
        with pytest.raises(exc.DeviceIdFileIncorrectHwControlError):
            _ = dim.device_id_to_fm_switch_id(device_id)


class TestFmSwitchIdToDeviceId:
    """Unit test class for fm_switch_id_to_device_id.

    SUT:/device_id_manager/device_ID_base.py/fm_switch_id_to_device_id.
    """

    def test_successful_case(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return device_id.
        """
        # preparation
        expected = "e9345fcb-4951-4da8-a569-358b00361083"

        fm_switch_id = "fm_switch_id"
        fm_manager_id = "7_77-abc777"

        # clear id_to_info for mock
        dim.id_to_info = {}

        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.fm_switch_id_to_device_id(fm_switch_id, fm_manager_id)

        # inspection
        assert expected == actual

    def test_successful_case_ite12(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return device_id.
        """
        # preparation
        expected = "e9345fcb-4951-4da8-a569-358b00361083"

        fm_switch_id = "fm_switch_id"
        fm_manager_id = "7_77-abc777"

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_ite12)
        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.fm_switch_id_to_device_id(fm_switch_id, fm_manager_id)

        # inspection
        assert expected == actual

    def test_not_fm_manager(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return device_id.
        """
        dim.id_to_info = {}
        # preparation
        expected = None

        fm_switch_id = "fm_switch_id"
        fm_manager_id = "no_same"
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_json_file", return_value=dummy_obtained_data)

        # execution
        actual = dim.fm_switch_id_to_device_id(fm_switch_id, fm_manager_id)

        # inspection
        assert expected == actual

    def test_not_switch(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return device_id.
        """
        dim.id_to_info = {}
        # preparation
        expected = None

        fm_switch_id = "not_sw"
        fm_manager_id = "no_same"
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_not_switch)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_json_file", return_value=dummy_obtained_data)

        # execution
        actual = dim.fm_switch_id_to_device_id(fm_switch_id, fm_manager_id)

        # inspection
        assert expected == actual

    def test_not_switch_2(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return device_id.
        """
        dim.id_to_info = {}
        # preparation
        expected = None

        fm_switch_id = "fm_switch_id"
        fm_manager_id = "7_77-abc777"

        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_not_switch)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")
        mocker.patch.object(dim, "_read_json_file", return_value=dummy_obtained_data)

        # execution
        actual = dim.fm_switch_id_to_device_id(fm_switch_id, fm_manager_id)

        # inspection
        assert expected == actual

    def test_fm_manager_id_not_found(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return none.
        """
        # preparation
        expected = None

        fm_switch_id = "fm_switch_id"
        fm_manager_id = "mogumogu"

        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")
        mocker.patch.object(dim, "_read_json_file", return_value=dummy_obtained_data)

        # execution
        actual = dim.fm_switch_id_to_device_id(fm_switch_id, fm_manager_id)

        # inspection
        assert expected == actual

    def test_empty_json_data_case(self, mocker: MockFixture):
        """Test Json file empty case.

        Test for errors in the following cases.

        _read_json_file return empty Json file such that

        {"data": []}

        Expect return None.
        """
        dim.id_to_info = {}
        # preparation
        expected = None

        fm_switch_id = "fm_switch_id"
        fm_manager_id = "mogumogu"

        empty_device_id_info = {}
        mocker.patch.object(dim, "_read_json_file", return_value=empty_device_id_info)

        # execution
        actual = dim.fm_switch_id_to_device_id(fm_switch_id, fm_manager_id)
        # inspection
        assert expected == actual

    def test_device_already_disabled_sub_flow(self, mocker: MockFixture):
        """Test Device already disabled case.

        Test following cases.

            If specified device has been disabled.
            Expect sut return None.
        """
        # preparation
        expected = None
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_json_file", return_value=dummy_obtained_data)
        # disabled device
        fm_switch_id = "9_99-abc777"
        fm_manager_id = "9_99-def8888"

        # execution
        actual = dim.fm_switch_id_to_device_id(fm_switch_id, fm_manager_id)

        # inspection
        assert expected == actual

    def test_deviceidfilenotfoundhwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIdFileNotFoundHwControlError case.

        Test for errors in the following cases.

            _read_json_file raise DeviceIdFileNotFoundHwControlError.
            Expect sut raise DeviceIdFileNotFoundHwControlError.
        """
        dim.id_to_info = {}

        mocker.patch.object(dim, "_read_json_file", side_effect=exc.DeviceIdFileNotFoundHwControlError)

        fm_switch_id = "fm_switch_id"
        fm_manager_id = "7_77-abc777"

        # execution
        with pytest.raises(exc.DeviceIdFileNotFoundHwControlError):
            _ = dim.fm_switch_id_to_device_id(fm_switch_id, fm_manager_id)

    def test_deviceidfileincorrecthwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIdFileIncorrectHwControlError case.

        Test for errors in the following cases.

            _read_json_file raise DeviceIdFileIncorrectHwControlError.
            Expect sut raise DeviceIdFileIncorrectHwControlError.
        """
        dim.id_to_info = {}

        # preparation
        mocker.patch.object(dim, "_read_json_file", side_effect=exc.DeviceIdFileIncorrectHwControlError)

        fm_switch_id = "fm_switch_id"
        fm_manager_id = "7_77-abc777"

        # execution
        with pytest.raises(exc.DeviceIdFileIncorrectHwControlError):
            _ = dim.fm_switch_id_to_device_id(fm_switch_id, fm_manager_id)

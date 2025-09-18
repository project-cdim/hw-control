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

# pylint: disable=W0212,R0801
"""unit test module in device_ID_base.py (part 4)

system under test
/app/common/dim/device_id_base.py

Test target function:
get_controllable_device_id_list
device_id_to_switch_port_type
device_id_to_fm_valid
get_switch_device_id_list
"""

import pytest
import pandas as pd
from pytest_mock import MockFixture
import app.common.basic_exceptions as exc

## system under test ###################
from app.common.dim import device_id_base as dim

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
        "deviceKeys": "{'SimulatedDeviceID': None, 'MemorySerialNumber': None}",
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
        "portKeys": "{'GIGAIODSPSlot': '2', 'GIGAIODSPPort': '9'}",
        "deviceKeys": "{'SimulatedDeviceID': '0002', 'MemorySerialNumber': '123456789'}",
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
        "portKeys": "{'GIGAIODSPSlot': '2', 'GIGAIODSPPort': '9'}",
        "deviceKeys": "{'SimulatedDeviceID': '0002', 'MemorySerialNumber': '123456789'}",
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
        "deviceKeys": "{'SimulatedDeviceID': None, 'MemorySerialNumber': None}",
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
        "portKeys": "{'GIGAIODSPSlot': '2', 'GIGAIODSPPort': '9'}",
        "deviceKeys": "{'SimulatedDeviceID': '0002', 'MemorySerialNumber': '123456789'}",
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
        "portKeys": "{'GIGAIODSPSlot': '2', 'GIGAIODSPPort': '9'}",
        "deviceKeys": "{'SimulatedDeviceID': '0002', 'MemorySerialNumber': '123456789'}",
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

dummy_all_disabled_device_id_info = [
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
        "deviceKeys": "{'SimulatedDeviceID': None, 'MemorySerialNumber': None}",
        "switchPortType": "USP",
        "valid": False,
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
        "connectedFmSwitchID": "connect_fm_switch_id",
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": "6_66-abc666",
        "oobManagerID": None,
        "portKeys": "{'GIGAIODSPSlot': '2', 'GIGAIODSPPort': '9'}",
        "deviceKeys": "{'SimulatedDeviceID': '0002', 'MemorySerialNumber': '123456789'}",
        "switchPortType": "DSP",
        "valid": False,
    },
    {
        "DeviceID": "e9345fcb-4951-4da8-a569-358b00361083",
        "deviceType": None,
        "fmPortID": None,
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "fm_switch_id",
        "switchSerialNumber": "switch_serial_number_1",
        "switchManufacturer": "switch_manufacturer_2",
        "switchModel": "switch_model",
        "fmManagerID": "7_77-abc777",
        "oobManagerID": None,
        "portKeys": None,
        "deviceKeys": None,
        "upDown": None,
        "valid": False,
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
        "upDown": None,
        "valid": False,
    },
]


class TestGetControllableDeviceIDList:
    """Unit test class for get_controllable_device_id_list.

    SUT:/device_id_manager/device_ID_base.py/get_controllable_device_id_list.
    """

    def test_successful_case(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return following list.
        ["d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
         "b9f9b678-bce8-49a1-bca3-dbbc32259abf",
         "b9f9b678-bce8-49a1-bca3-dbbc32259abk"]
        """
        dim.id_to_info = {}
        # preparation
        expected = [
            "d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
            "b9f9b678-bce8-49a1-bca3-dbbc32259abf",
            "b9f9b678-bce8-49a1-bca3-dbbc32259abk",
        ]

        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_device_id_info_d = dim._change_info_to_new_type(dummy_device_id_info_d)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_device_id_manager_file_dict", return_value=dummy_obtained_data)

        # execution
        actual = dim.get_controllable_device_id_list()

        # inspection
        assert expected == actual

    def test_successful_case_ite12(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return following list.
        ["d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
         "b9f9b678-bce8-49a1-bca3-dbbc32259abf",
         "b9f9b678-bce8-49a1-bca3-dbbc32259abk",]
        """
        dim.id_to_info = {}
        # preparation
        expected = [
            "d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
            "b9f9b678-bce8-49a1-bca3-dbbc32259abf",
            "b9f9b678-bce8-49a1-bca3-dbbc32259abk",
        ]

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_ite12)
        dummy_device_id_info_d = dim._change_info_to_new_type(dummy_device_id_info_d)
        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.get_controllable_device_id_list()

        # inspection
        assert expected == actual

    def test_successful_not_empty_global_valuecase(self):
        """Test successful case.

        Expect sut return following list.
        ["d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
         "b9f9b678-bce8-49a1-bca3-dbbc32259abf",
         "b9f9b678-bce8-49a1-bca3-dbbc32259abk"]
        """
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_device_id_info_d = dim._change_info_to_new_type(dummy_device_id_info_d)
        dim.id_to_info = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")
        # preparation
        expected = [
            "d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
            "b9f9b678-bce8-49a1-bca3-dbbc32259abf",
            "b9f9b678-bce8-49a1-bca3-dbbc32259abk",
        ]

        # execution
        actual = dim.get_controllable_device_id_list()

        # inspection
        assert expected == actual

    def test_successful_case_check_by_oob(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return following list.
        ["d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
         "b9f9b678-bce8-49a1-bca3-dbbc32259abf",
         "b9f9b678-bce8-49a1-bca3-dbbc32259abk"]
        """
        dim.id_to_info = {}
        # preparation
        expected = [
            "d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
            "b9f9b678-bce8-49a1-bca3-dbbc32259abf",
            "b9f9b678-bce8-49a1-bca3-dbbc32259abk",
        ]

        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_oob)
        dummy_device_id_info_d = dim._change_info_to_new_type(dummy_device_id_info_d)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_device_id_manager_file_dict", return_value=dummy_obtained_data)

        # execution
        actual = dim.get_controllable_device_id_list()

        # inspection
        assert expected == actual

    def test_all_device_already_disabled_sub_flow(self, mocker: MockFixture):
        """Test Device already disabled case.

        Test following cases.

            If specified device has been disabled.
            Expect sut return following list.
                []
        """
        dim.id_to_info = {}
        # preparation
        expected = []
        dummy_device_id_info_d = pd.DataFrame(dummy_all_disabled_device_id_info)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_device_id_manager_file_dict", return_value=dummy_obtained_data)

        # execution
        actual = dim.get_controllable_device_id_list()

        # inspection
        assert expected == actual

    def test_empty_json_data_case(self, mocker: MockFixture):
        """Test Json file empty case.

        Test for errors in the following cases.

        _read_device_id_manager_file_dict return empty Json file such that

        {"data": []}

        Expect sut raise empty list such that

        []
        """
        # preparation
        dim.id_to_info = {}
        expected = []

        empty_device_id_info = {}
        mocker.patch.object(dim, "_read_device_id_manager_file_dict", return_value=empty_device_id_info)

        # execution

        actual = dim.get_controllable_device_id_list()

        # inspection
        assert actual == expected

    def test_deviceidfilenotfoundhwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIDFileNotFoundHWControlError case.

        Test for errors in the following cases.

            _read_device_id_manager_file_dict raise DeviceIDFileNotFoundHWControlError.
            Expect sut raise DeviceIDFileNotFoundHWControlError.
        """
        dim.id_to_info = {}
        mocker.patch.object(
            dim, "_read_device_id_manager_file_dict", side_effect=exc.DeviceIDFileNotFoundHWControlError
        )

        # execution
        with pytest.raises(exc.DeviceIDFileNotFoundHWControlError):
            _ = dim.get_controllable_device_id_list()

    def test_deviceidfileincorrecthwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIDFileIncorrectHWControlError case.

        Test for errors in the following cases.

            _read_device_id_manager_file_dict raise DeviceIDFileIncorrectHWControlError.
            Expect sut raise DeviceIDFileIncorrectHWControlError.
        """
        dim.id_to_info = {}
        mocker.patch.object(
            dim, "_read_device_id_manager_file_dict", side_effect=exc.DeviceIDFileIncorrectHWControlError
        )

        # execution
        with pytest.raises(exc.DeviceIDFileIncorrectHWControlError):
            _ = dim.get_controllable_device_id_list()


class TestDeviceIDToSwitchPortType:
    """Unit test class for device_id_to_switch_port_type.

    SUT:/device_id_manager/device_ID_base.py/device_id_to_switch_port_type.
    """

    def test_successful_case(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return SwitchPortType.
        """
        dim.id_to_info = {}
        # preparation
        expected = "USP"

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_device_id_manager_file_dict", return_value=dummy_obtained_data)

        # execution
        actual = dim.device_id_to_switch_port_type(device_id)

        # inspection
        assert expected == actual

    def test_successful_case_ite12(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return SwitchPortType.
        """
        dim.id_to_info = {}
        # preparation
        expected = "USP"

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_ite12)
        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.device_id_to_switch_port_type(device_id)

        # inspection
        assert expected == actual

    def test_successful_case_none(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return upDown.
        """
        # preparation
        expected = None

        device_id = "e9345fcb-4951-4da8-a569-358b00361083"
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_device_id_manager_file_dict", return_value=dummy_obtained_data)

        # execution
        actual = dim.device_id_to_switch_port_type(device_id)

        # inspection
        assert expected == actual

    def test_apiusagehwcontrolerror_case(self):
        """Test APIUsageHWControlError case.

        Test for errors in the following cases.

            _is_valid_uuid raise APIUsageHWControlError.
            Expect sut raise APIUsageHWControlError.
        """
        # preparation
        device_id = "mogumogu"

        # execution
        with pytest.raises(exc.APIUsageHWControlError):
            _ = dim.device_id_to_switch_port_type(device_id)

    def test_empty_json_data_case(self, mocker: MockFixture):
        """Test Json file empty case.

        Test for errors in the following cases.

        _read_device_id_manager_file_dict return empty Json file such that

        {"data": []}

        Expect sut raise DeviceIDNotFoundHWControlError.
        """
        dim.id_to_info = {}
        # preparation
        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        empty_device_id_info = {}
        mocker.patch.object(dim, "_read_device_id_manager_file_dict", return_value=empty_device_id_info)

        # execution
        with pytest.raises(exc.DeviceIDNotFoundHWControlError):
            _ = dim.device_id_to_switch_port_type(device_id)

    def test_deviceidnotfoundhwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIDNotFoundHWControlError case.

        Test for errors in the following cases.

            If the specified device is a switch.
            Expect sut raise DeviceIDNotFoundHWControlError.
        """
        # preparation
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_device_id_manager_file_dict", return_value=dummy_obtained_data)

        # nonexistent device ID
        device_id = "4d4f8988-ce27-4e6a-b83b-6309e4f7d5ad"

        # execution
        with pytest.raises(exc.DeviceIDNotFoundHWControlError):
            _ = dim.device_id_to_switch_port_type(device_id)

    def test_deviceidfilenotfoundhwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIDFileNotFoundHWControlError case.

        Test for errors in the following cases.

            _read_device_id_manager_file_dict raise DeviceIDFileNotFoundHWControlError.
            Expect sut raise DeviceIDFileNotFoundHWControlError.
        """
        dim.id_to_info = {}

        # preparation
        mocker.patch.object(
            dim, "_read_device_id_manager_file_dict", side_effect=exc.DeviceIDFileNotFoundHWControlError
        )

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        # execution
        with pytest.raises(exc.DeviceIDFileNotFoundHWControlError):
            _ = dim.device_id_to_switch_port_type(device_id)

    def test_deviceidfileincorrecthwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIDFileIncorrectHWControlError case.

        Test for errors in the following cases.

            _read_device_id_manager_file_dict raise DeviceIDFileIncorrectHWControlError.
            Expect sut raise DeviceIDFileIncorrectHWControlError.
        """
        dim.id_to_info = {}

        # preparation
        mocker.patch.object(
            dim, "_read_device_id_manager_file_dict", side_effect=exc.DeviceIDFileIncorrectHWControlError
        )

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        # execution
        with pytest.raises(exc.DeviceIDFileIncorrectHWControlError):
            _ = dim.device_id_to_switch_port_type(device_id)


class TestDeviceIDToFMValid:
    """Unit test class for device_id_to_fm_valid.

    SUT:/device_id_manager/device_ID_base.py/device_id_to_fm_valid.
    """

    def test_successful_case(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return upDown.
        """
        dim.id_to_info = {}
        # preparation
        expected = True

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_device_id_manager_file_dict", return_value=dummy_obtained_data)

        # execution
        actual = dim.device_id_to_fm_valid(device_id)

        # inspection
        assert expected == actual

    def test_successful_case_ite12(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return upDown.
        """
        dim.id_to_info = {}
        # preparation
        expected = True

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_ite12)

        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.device_id_to_fm_valid(device_id)

        # inspection
        assert expected == actual

    def test_successful_case_false(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return upDown.
        """
        # preparation
        expected = False

        device_id = "e9345fcb-4951-4da8-a569-358b00361083"
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_device_id_manager_file_dict", return_value=dummy_obtained_data)

        # execution
        actual = dim.device_id_to_fm_valid(device_id)

        # inspection
        assert expected == actual

    def test_apiusagehwcontrolerror_case(self):
        """Test APIUsageHWControlError case.

        Test for errors in the following cases.

            _is_valid_uuid raise APIUsageHWControlError.
            Expect sut raise APIUsageHWControlError.
        """
        # preparation
        device_id = "mogumogu"

        # execution
        with pytest.raises(exc.APIUsageHWControlError):
            _ = dim.device_id_to_fm_valid(device_id)

    def test_empty_json_data_case(self, mocker: MockFixture):
        """Test Json file empty case.

        Test for errors in the following cases.

        _read_device_id_manager_file_dict return empty Json file such that

        {"data": []}

        Expect sut raise DeviceIDNotFoundHWControlError.
        """
        dim.id_to_info = {}
        # preparation
        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        empty_device_id_info = {}
        mocker.patch.object(dim, "_read_device_id_manager_file_dict", return_value=empty_device_id_info)

        # execution
        with pytest.raises(exc.DeviceIDNotFoundHWControlError):
            _ = dim.device_id_to_fm_valid(device_id)

    def test_deviceidnotfoundhwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIDNotFoundHWControlError case.

        Test for errors in the following cases.

            If the specified device is a switch.
            Expect sut raise DeviceIDNotFoundHWControlError.
        """
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_device_id_manager_file_dict", return_value=dummy_obtained_data)

        # nonexistent device ID
        device_id = "4d4f8988-ce27-4e6a-b83b-6309e4f7d5ad"

        # execution
        with pytest.raises(exc.DeviceIDNotFoundHWControlError):
            _ = dim.device_id_to_fm_valid(device_id)

    def test_deviceidfilenotfoundhwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIDFileNotFoundHWControlError case.

        Test for errors in the following cases.

            _read_device_id_manager_file_dict raise DeviceIDFileNotFoundHWControlError.
            Expect sut raise DeviceIDFileNotFoundHWControlError.
        """
        dim.id_to_info = {}

        # preparation
        mocker.patch.object(
            dim, "_read_device_id_manager_file_dict", side_effect=exc.DeviceIDFileNotFoundHWControlError
        )
        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        # execution
        with pytest.raises(exc.DeviceIDFileNotFoundHWControlError):
            _ = dim.device_id_to_fm_valid(device_id)

    def test_deviceidfileincorrecthwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIDFileIncorrectHWControlError case.

        Test for errors in the following cases.

            _read_device_id_manager_file_dict raise DeviceIDFileIncorrectHWControlError.
            Expect sut raise DeviceIDFileIncorrectHWControlError.
        """
        dim.id_to_info = {}

        # preparation
        mocker.patch.object(
            dim, "_read_device_id_manager_file_dict", side_effect=exc.DeviceIDFileIncorrectHWControlError
        )

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        # execution
        with pytest.raises(exc.DeviceIDFileIncorrectHWControlError):
            _ = dim.device_id_to_fm_valid(device_id)


class TestGetSwitchDeviceIDList:
    """Unit test class for get_switch_device_id_list.

    SUT:/device_id_manager/device_ID_base.py/get_switch_device_id_list.
    """

    def test_successful_case(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return following list.
        ["e9345fcb-4951-4da8-a569-358b00361083",
         "e9345fcb-4951-4da8-a569-358b00361084",
         "e9345fcb-4951-4da8-a569-358b00361085"]
        """
        dim.id_to_info = {}
        # preparation
        expected = [
            "e9345fcb-4951-4da8-a569-358b00361083",
            "e9345fcb-4951-4da8-a569-358b00361084",
            "e9345fcb-4951-4da8-a569-358b00361085",
        ]

        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_device_id_manager_file_dict", return_value=dummy_obtained_data)

        # execution
        actual = dim.get_switch_device_id_list()

        # inspection
        assert expected == actual

    def test_successful_case_ite12(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return following list.
        ["e9345fcb-4951-4da8-a569-358b00361083",
         "e9345fcb-4951-4da8-a569-358b00361084",
         "e9345fcb-4951-4da8-a569-358b00361085"]
        """
        dim.id_to_info = {}
        # preparation
        expected = [
            "e9345fcb-4951-4da8-a569-358b00361083",
            "e9345fcb-4951-4da8-a569-358b00361084",
            "e9345fcb-4951-4da8-a569-358b00361085",
        ]

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_ite12)

        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.get_switch_device_id_list()

        # inspection
        assert expected == actual

    def test_successful_not_empty_global_valuecase(self):
        """Test successful case.

        Expect sut return following list.
        ["e9345fcb-4951-4da8-a569-358b00361083",
         "e9345fcb-4951-4da8-a569-358b00361084",
         "e9345fcb-4951-4da8-a569-358b00361085"]
        """
        dim.id_to_info = pd.DataFrame(dummy_device_id_info).set_index("DeviceID").to_dict(orient="index")
        # preparation
        expected = [
            "e9345fcb-4951-4da8-a569-358b00361083",
            "e9345fcb-4951-4da8-a569-358b00361084",
            "e9345fcb-4951-4da8-a569-358b00361085",
        ]

        # execution
        actual = dim.get_switch_device_id_list()

        # inspection
        assert expected == actual

    def test_all_device_already_disabled_sub_flow(self, mocker: MockFixture):
        """Test Device already disabled case.

        Test following cases.

            If specified device has been disabled.
            Expect sut return following list.
                []
        """
        dim.id_to_info = {}
        # preparation
        expected = []
        dummy_device_id_info_d = pd.DataFrame(dummy_all_disabled_device_id_info)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_device_id_manager_file_dict", return_value=dummy_obtained_data)

        # execution
        actual = dim.get_switch_device_id_list()

        # inspection
        assert expected == actual

    def test_empty_json_data_case(self, mocker: MockFixture):
        """Test Json file empty case.

        Test for errors in the following cases.

        _read_device_id_manager_file_dict return empty Json file such that

        {"data": []}

        Expect sut raise empty list such that

        []
        """
        dim.id_to_info = {}
        # preparation
        expected = []

        empty_device_id_info = {}
        mocker.patch.object(dim, "_read_device_id_manager_file_dict", return_value=empty_device_id_info)

        # execution
        actual = dim.get_switch_device_id_list()

        # inspection
        assert actual == expected

    def test_deviceidfilenotfoundhwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIDFileNotFoundHWControlError case.

        Test for errors in the following cases.

            _read_device_id_manager_file_dict raise DeviceIDFileNotFoundHWControlError.
            Expect sut raise DeviceIDFileNotFoundHWControlError.
        """
        dim.id_to_info = {}

        # preparation
        mocker.patch.object(
            dim, "_read_device_id_manager_file_dict", side_effect=exc.DeviceIDFileNotFoundHWControlError
        )

        # execution
        with pytest.raises(exc.DeviceIDFileNotFoundHWControlError):
            _ = dim.get_switch_device_id_list()

    def test_deviceidfileincorrecthwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIDFileIncorrectHWControlError case.

        Test for errors in the following cases.

            _read_device_id_manager_file_dict raise DeviceIDFileIncorrectHWControlError.
            Expect sut raise DeviceIDFileIncorrectHWControlError.
        """
        dim.id_to_info = {}

        # preparation
        mocker.patch.object(
            dim, "_read_device_id_manager_file_dict", side_effect=exc.DeviceIDFileIncorrectHWControlError
        )

        # execution
        with pytest.raises(exc.DeviceIDFileIncorrectHWControlError):
            _ = dim.get_switch_device_id_list()

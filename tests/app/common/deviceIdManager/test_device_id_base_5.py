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
"""unit test module in device_ID_base.py (part 5)

system under test
/app/common/deviceIdManager/device_id_base.py

Test target function:
device_id_to_connected_fm_switch_id
device_id_to_connected_fm_switch_id_multi_host
connected_fm_switch_id_to_device_id_list
_get_device_info
"""

from unittest.mock import patch
from unittest.mock import MagicMock
import pytest
from pytest_mock import MockFixture

import pandas as pd

## system under test ###################
import app.common.basic_exceptions as exc
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
        "deviceKeys": {"SimulatedDeviceID": None, "MemorySerialNumber": None},
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
        "portKeys": {"GIGAIODSPSlot": "2", "GIGAIODSPPort": "9"},
        "deviceKeys": {"SimulatedDeviceID": "0002", "MemorySerialNumber": "123456789"},
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


class TestDeviceIdToConnectedFmSwitchId:
    """Unit test class for device_id_to_switch_port_type.

    SUT:/device_id_manager/device_ID_base.py/device_id_to_connected_fm_switch_id.
    """

    def test_successful_case(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return connectedFmSwitchID.
        """
        # preparation
        expected = "connect_fm_switch_id"

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.device_id_to_connected_fm_switch_id(device_id)

        # inspection
        assert expected == actual

    def test_successful_case_ite12(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return connectedFmSwitchID.
        """
        # preparation
        expected = "connect_fm_switch_id"

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_ite12)
        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.device_id_to_connected_fm_switch_id(device_id)

        # inspection
        assert expected == actual

    def test_successful_case_none(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return connectedFmSwitchID.
        """
        # preparation
        expected = None

        device_id = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_json_file", return_value=dummy_obtained_data)

        # execution
        actual = dim.device_id_to_connected_fm_switch_id(device_id)

        # inspection
        assert expected == actual

    def test_successful_case_none_empty_dict(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return connectedFmSwitchID.
        """
        # preparation
        dim.id_to_info = {}
        expected = None

        device_id = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_oob)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")
        mocker.patch.object(dim, "_read_json_file", return_value=dummy_obtained_data)

        # execution
        actual = dim.device_id_to_connected_fm_switch_id(device_id)

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
            _ = dim.device_id_to_connected_fm_switch_id(device_id)

    def test_empty_json_data_case(self, mocker: MockFixture):
        """Test Json file empty case.

        Test for errors in the following cases.

        _read_json_file return empty Json file such that

        {"data": []}

        Expect sut raise DeviceIdNotFoundHwControlError.
        """
        dim.id_to_info = {}
        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        empty_device_id_info = {}
        mocker.patch.object(dim, "_read_json_file", return_value=empty_device_id_info)

        # execution
        with pytest.raises(exc.DeviceIdNotFoundHwControlError):
            _ = dim.device_id_to_connected_fm_switch_id(device_id)

    def test_invalidtypedeviceidhwcontrolerror_case(self, mocker: MockFixture):
        """Test InvalidTypeDeviceIdHwControlError case.

        Test following cases.

            If specified device is not Switch.
            Expect sut raise InvalidTypeDeviceIdHwControlError.
        """
        device_id = "e9345fcb-4951-4da8-a569-358b00361083"
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_json_file", return_value=dummy_obtained_data)

        # execution
        with pytest.raises(exc.InvalidTypeDeviceIdHwControlError):
            _ = dim.device_id_to_connected_fm_switch_id(device_id)

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

        # nonexistent device ID
        device_id = "4d4f8988-ce27-4e6a-b83b-6309e4f7d5ad"

        # execution
        with pytest.raises(exc.DeviceIdNotFoundHwControlError):
            _ = dim.device_id_to_connected_fm_switch_id(device_id)

    def test_deviceidfilenotfoundhwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIdFileNotFoundHwControlError case.

        Test for errors in the following cases.

            _read_json_file raise DeviceIdFileNotFoundHwControlError.
            Expect sut raise DeviceIdFileNotFoundHwControlError.
        """
        dim.id_to_info = {}
        mocker.patch.object(dim, "_read_json_file", side_effect=exc.DeviceIdFileNotFoundHwControlError)

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        # execution
        with pytest.raises(exc.DeviceIdFileNotFoundHwControlError):
            _ = dim.device_id_to_connected_fm_switch_id(device_id)

    def test_deviceidfileincorrecthwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIdFileIncorrectHwControlError case.

        Test for errors in the following cases.

            _read_json_file raise DeviceIdFileIncorrectHwControlError.
            Expect sut raise DeviceIdFileIncorrectHwControlError.
        """
        dim.id_to_info = {}
        mocker.patch.object(dim, "_read_json_file", side_effect=exc.DeviceIdFileIncorrectHwControlError)

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        # execution
        with pytest.raises(exc.DeviceIdFileIncorrectHwControlError):
            _ = dim.device_id_to_connected_fm_switch_id(device_id)


class TestDeviceIdToConnectedFmSwitchIdMultiHost:
    """Unit test class for device_id_to_connected_fm_switch_id_multi_hostport.

    SUT:/device_id_manager/device_ID_base.py/device_id_to_connected_fm_switch_id_multi_hostport.
    """

    def test_successful_case(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return connectedFmSwitchID.
        """
        # preparation
        expected = ["connect_fm_switch_id"]

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"
        fm_manager_id = "test_1"

        # clear id_to_info for mock
        dim.id_to_info = {}

        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.device_id_to_connected_fm_switch_id_multi_hostport(device_id, fm_manager_id)

        # inspection
        assert expected == actual

    def test_successful_case_ite12(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return connectedFmSwitchID.
        """
        # preparation
        expected = ["connect_fm_switch_id"]

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"
        fm_manager_id = "test_1"

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_ite12)

        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.device_id_to_connected_fm_switch_id_multi_hostport(device_id, fm_manager_id)

        # inspection
        assert expected == actual

    def test_successful_case_none(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return connectedFmSwitchID.
        """
        # preparation
        expected = []

        device_id = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"
        fm_manager_id = "6_66-abc666"

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)

        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.device_id_to_connected_fm_switch_id_multi_hostport(device_id, fm_manager_id)

        # inspection
        assert expected == actual

    def test_successful_case_none_2(self, mocker: MockFixture):
        """Test successful case with incorrect fmManagerID.

        Expect sut return connectedFmSwitchID.
        """
        # preparation
        expected = []

        # invalid fmManagerID
        device_id = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"
        fm_manager_id = "mogumogu"

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)

        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.device_id_to_connected_fm_switch_id_multi_hostport(device_id, fm_manager_id)

        # inspection
        assert expected == actual

    def test_apiusagehwcontrolerror_case(self):
        """Test ApiUsageHwControlError case.

        Test for errors in the following cases.

            _is_valid_uuid raise ApiUsageHwControlError.
            Expect sut raise ApiUsageHwControlError.
        """
        device_id = "mogumogu"
        fm_manager_id = "6_66-abc666"

        # execution
        with pytest.raises(exc.ApiUsageHwControlError):
            _ = dim.device_id_to_connected_fm_switch_id_multi_hostport(device_id, fm_manager_id)

    def test_empty_json_data_case(self, mocker: MockFixture):
        """Test Json file empty case.

        Test for errors in the following cases.

        _read_json_file return empty Json file such that

        {"data": []}

        Expect sut raise DeviceIdNotFoundHwControlError.
        """
        dim.id_to_info = {}
        device_id = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"
        fm_manager_id = "6_66-abc666"

        empty_device_id_info = {}
        mocker.patch.object(dim, "_read_json_file", return_value=empty_device_id_info)

        # execution
        with pytest.raises(exc.DeviceIdNotFoundHwControlError):
            _ = dim.device_id_to_connected_fm_switch_id_multi_hostport(device_id, fm_manager_id)

    def test_invalidtypedeviceidhwcontrolerror_case(self, mocker: MockFixture):
        """Test InvalidTypeDeviceIdHwControlError case.

        Test following cases.

            If specified device is not Switch.
            Expect sut raise InvalidTypeDeviceIdHwControlError.
        """
        device_id = "e9345fcb-4951-4da8-a569-358b00361083"
        fm_manager_id = "7_77-abc777"

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)

        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        with pytest.raises(exc.InvalidTypeDeviceIdHwControlError):
            _ = dim.device_id_to_connected_fm_switch_id_multi_hostport(device_id, fm_manager_id)

    def test_deviceidnotfoundhwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIdNotFoundHwControlError case.

        Test for errors in the following cases.

            If the specified device is a switch.
            Expect sut raise DeviceIdNotFoundHwControlError.
        """
        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # nonexistent device ID
        device_id = "4d4f8988-ce27-4e6a-b83b-6309e4f7d5ad"
        fm_manager_id = "mogumogu"

        # execution
        with pytest.raises(exc.DeviceIdNotFoundHwControlError):
            _ = dim.device_id_to_connected_fm_switch_id_multi_hostport(device_id, fm_manager_id)

    def test_deviceidfilenotfoundhwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIdFileNotFoundHwControlError case.

        Test for errors in the following cases.

            _read_json_file raise DeviceIdFileNotFoundHwControlError.
            Expect sut raise DeviceIdFileNotFoundHwControlError.
        """
        dim.id_to_info = {}
        mocker.patch.object(dim, "_read_json_file", side_effect=exc.DeviceIdFileNotFoundHwControlError)

        device_id = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"
        fm_manager_id = "6_66-abc666"

        # execution
        with pytest.raises(exc.DeviceIdFileNotFoundHwControlError):
            _ = dim.device_id_to_connected_fm_switch_id_multi_hostport(device_id, fm_manager_id)

    def test_deviceidfileincorrecthwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIdFileIncorrectHwControlError case.

        Test for errors in the following cases.

            _read_json_file raise DeviceIdFileIncorrectHwControlError.
            Expect sut raise DeviceIdFileIncorrectHwControlError.
        """
        dim.id_to_info = {}
        mocker.patch.object(dim, "_read_json_file", side_effect=exc.DeviceIdFileIncorrectHwControlError)

        device_id = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"
        fm_manager_id = "6_66-abc666"

        # execution
        with pytest.raises(exc.DeviceIdFileIncorrectHwControlError):
            _ = dim.device_id_to_connected_fm_switch_id_multi_hostport(device_id, fm_manager_id)


class TestConnectedFmSwitchIdToDeviceIdList:
    """Unit test class for connected_fm_switch_id_to_device_id_list.

    SUT:/device_id_manager/device_ID_base.py/connected_fm_switch_id_to_device_id_list.
    """

    def test_successful_case(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return following list.
        ["d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
         "b9f9b678-bce8-49a1-bca3-dbbc32259abk"]
        """
        dim.id_to_info = {}
        # preparation
        expected = ["d62e98bf-6c50-4b88-95f9-49c609d2fdc9", "b9f9b678-bce8-49a1-bca3-dbbc32259abk"]

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)

        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        connect_fm_switch_id = "connect_fm_switch_id"
        # execution
        actual = dim.connected_fm_switch_id_to_device_id_list(connect_fm_switch_id)

        # inspection
        assert expected == actual

    def test_successful_case_ite12(self, mocker: MockFixture):
        """Test successful case.

        Expect sut return following list.
        ["d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
         "b9f9b678-bce8-49a1-bca3-dbbc32259abk"]
        """
        dim.id_to_info = {}
        # preparation
        expected = ["d62e98bf-6c50-4b88-95f9-49c609d2fdc9", "b9f9b678-bce8-49a1-bca3-dbbc32259abk"]

        # clear id_to_info for mock
        dim.id_to_info = {}
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_ite12)

        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        connect_fm_switch_id = "connect_fm_switch_id"
        # execution
        actual = dim.connected_fm_switch_id_to_device_id_list(connect_fm_switch_id)

        # inspection
        assert expected == actual

    def test_successful_not_empty_global_value_case(self):
        """Test successful case.

        Expect sut return following list.
        ["d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
         "b9f9b678-bce8-49a1-bca3-dbbc32259abk"]
        """
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_device_id_info_d = dim._change_info_to_new_type(dummy_device_id_info_d)
        dim.id_to_info = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")
        # preparation
        expected = ["d62e98bf-6c50-4b88-95f9-49c609d2fdc9", "b9f9b678-bce8-49a1-bca3-dbbc32259abk"]

        connect_fm_switch_id = "connect_fm_switch_id"
        # execution
        actual = dim.connected_fm_switch_id_to_device_id_list(connect_fm_switch_id)

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

        mocker.patch.object(dim, "_read_json_file", return_value=dummy_obtained_data)

        connect_fm_switch_id = "connect_fm_switch_id"
        # execution
        actual = dim.connected_fm_switch_id_to_device_id_list(connect_fm_switch_id)

        # inspection
        assert expected == actual

    def test_empty_json_data_case(self, mocker: MockFixture):
        """Test Json file empty case.

        Test for errors in the following cases.

        _read_json_file return empty Json file such that

        {"data": []}

        Expect sut raise empty list such that

        []
        """
        dim.id_to_info = {}
        # preparation
        expected = []

        empty_device_id_info = {}
        mocker.patch.object(dim, "_read_json_file", return_value=empty_device_id_info)

        connect_fm_switch_id = "connect_fm_switch_id"
        # execution
        actual = dim.connected_fm_switch_id_to_device_id_list(connect_fm_switch_id)

        # inspection
        assert actual == expected

    def test_deviceidfilenotfoundhwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIdFileNotFoundHwControlError case.

        Test for errors in the following cases.

            _read_json_file raise DeviceIdFileNotFoundHwControlError.
            Expect sut raise DeviceIdFileNotFoundHwControlError.
        """
        dim.id_to_info = {}
        mocker.patch.object(dim, "_read_json_file", side_effect=exc.DeviceIdFileNotFoundHwControlError)

        connect_fm_switch_id = "connect_fm_switch_id"
        # execution
        with pytest.raises(exc.DeviceIdFileNotFoundHwControlError):
            _ = dim.connected_fm_switch_id_to_device_id_list(connect_fm_switch_id)

    def test_deviceidfileincorrecthwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIdFileIncorrectHwControlError case.

        Test for errors in the following cases.

            _read_json_file raise DeviceIdFileIncorrectHwControlError.
            Expect sut raise DeviceIdFileIncorrectHwControlError.
        """
        dim.id_to_info = {}
        mocker.patch.object(dim, "_read_json_file", side_effect=exc.DeviceIdFileIncorrectHwControlError)

        connect_fm_switch_id = "connect_fm_switch_id"
        # execution
        with pytest.raises(exc.DeviceIdFileIncorrectHwControlError):
            _ = dim.connected_fm_switch_id_to_device_id_list(connect_fm_switch_id)


class TestGetDeviceInfo:  # pylint: disable=R0903
    """Unit test class for _get_devices_info.

    SUT:/device_id_manager/device_ID_base.py/_get_devices_info.
    """

    @patch("app.common.deviceIdManager.device_id_base.device_id_info_lock")
    def test_id_to_info_is_not_empty_by_2nd_check(self, mock_device_id_info_lock):
        """Test global variable is not empty when checked again case.

        Test the case where the global variable is empty initially,
        but contains information when checked again.
        """
        expected = {"changed": "not empty"}

        def enter_effect():
            """set id_to_info"""
            dim.id_to_info = {"changed": "not empty"}

        mock_device_id_info_lock.__enter__.side_effect = enter_effect
        mock_device_id_info_lock.__exit__ = MagicMock()

        # execution
        actual = dim._get_devices_info()
        mock_device_id_info_lock.__enter__.assert_called_once()
        mock_device_id_info_lock.__exit__.assert_called_once()

        # inspection
        assert expected == actual

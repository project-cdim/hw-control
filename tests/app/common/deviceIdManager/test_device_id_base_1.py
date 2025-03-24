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
"""unit test module in device_ID_base.py (part 1)

system under test
/app/common/deviceIdManager/device_id_base.py

Test target function:
_change_info_to_new_type
_is_valid_uuid
_read_json_file
assign_device_id
device_id_to_fm_port_id
device_id_to_fm_port_id_multi_host_port
"""

import uuid
import json
import pytest
import pandas as pd
from pytest_mock import MockFixture
import app.common.basic_exceptions as exc

## system under test ###################
from app.common.deviceIdManager import device_id_base as dim
from app.common.utils.file_location_settings import FileLocationSettings as path_setting

# For log check
DIM_MODULE_NAME = "app.common.deviceIdManager.device_id_base"
CONSTANT_REQUEST_ID = "test_request_id"


def check_log_message(caplog, levelname, request_id, messages):
    """

    check log

    """
    index = 0
    for record in caplog.records:
        call_log_message = json.loads(record.getMessage())
        if record.levelname == levelname and call_log_message["message"]["request_id"] == request_id:
            assert call_log_message["message"]["detail"] == messages[index]
            index += 1
    assert len(messages) == index


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

dummy_device_id_info_2_item_dict = {
    "d62e98bf-6c50-4b88-95f9-49c609d2fdc9": {
        "CPUManufacturer": "AMD",
        "CPUModel": "ABCDEF",
        "CPUSerialNumber": "123456789",
        "deviceKeys": {"MemorySerialNumber": None, "SimulatedDeviceID": None},
        "deviceType": "CPU",
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "PCIeVendorId": None,
        "portKeys": None,
        "connectedFmSwitchID": {},
        "fmManagerID": [],
        "fmPortID": {},
        "fmSwitchID": None,
        "oobDeviceID": "0001",
        "oobManagerID": ["1111111_abc"],
        "switchManufacturer": None,
        "switchModel": None,
        "switchPortType": "USP",
        "switchSerialNumber": None,
        "fmValid": True,
        "valid": True,
    },
    "b9f9b678-bce8-49a1-bca3-dbbc32259abf": {
        "CPUManufacturer": None,
        "CPUModel": None,
        "CPUSerialNumber": None,
        "deviceKeys": {"MemorySerialNumber": "123456789", "SimulatedDeviceID": "0002"},
        "deviceType": "memory",
        "PCIeDeviceId": "1042",
        "PCIeDeviceSerialNumber": "deadbeef00000007",
        "PCIeVendorId": "1af4",
        "portKeys": {"GIGAIODSPPort": "9", "GIGAIODSPSlot": "2"},
        "connectedFmSwitchID": {"6_66-abc666": []},
        "fmManagerID": ["6_66-abc666"],
        "fmPortID": {"6_66-abc666": ["eed37ccf-293e-4da4-aeef-f42843192f53"]},
        "fmSwitchID": None,
        "oobDeviceID": "0002",
        "oobManagerID": [],
        "switchManufacturer": None,
        "switchModel": None,
        "switchPortType": "DSP",
        "switchSerialNumber": None,
        "fmValid": True,
        "valid": True,
    },
}

dummy_device_id_info_invalid_value = [
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
        "fmManagerID": {"test_1": "test_1"},
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
        "connectedFmSwitchID": None,
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
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
        "portKeys": {"GIGAIODSPSlot": "2", "GIGAIODSPPort": "9"},
        "deviceKeys": {"SimulatedDeviceID": "0002", "MemorySerialNumber": "123456789"},
        "switchPortType": "DSP",
        "fmValid": True,
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
]

dummy_device_id_info_2_item_new_type = [
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
        "connectedFmSwitchID": {},
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": ["6_66-abc666"],
        "oobManagerID": None,
        "portKeys": {"GIGAIODSPSlot": "2", "GIGAIODSPPort": "9"},
        "deviceKeys": {"SimulatedDeviceID": "0002", "MemorySerialNumber": "123456789"},
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": True,
    },
]

dummy_device_id_info_change_keys = [
    {
        "DeviceID": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
        "DeviceType": "CPU",
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
        "PortKeys": None,
        "DeviceKeys": {"SimulatedDeviceID": None, "MemorySerialNumber": None},
        "switchPortType": "USP",
        "fmValid": True,
        "valid": True,
    },
]


dummy_device_id_info_test_first_key = [
    {
        "DeviceID": "e9345fcb-4951-4da8-a569-358b00361085",
        "deviceType": "memory",
        "fmPortID": None,
        "oobDeviceID": None,
        "PCIeVendorId": "1af5",
        "PCIeDeviceId": "1043",
        "PCIeDeviceSerialNumber": "deadbeef00000009",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "fm_switch_id",
        "connectedFmSwitchID": None,
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": "7_77-abc777",
        "oobManagerID": None,
        "portKeys": None,
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": True,
        "valid": True,
    },
]


class TestChangeInfoToNewType:  # pylint: disable=R0903
    """Unit test class for _change_info_to_new_type.

    SUT:/device_id_manager/device_ID_base.py/_change_info_to_new_type

    Basically, test this along with another function.

    Here, test only the missing parts separately.
    """

    def test_is_new_type(self):
        """Test case of new type.
        SUT:/device_id_manager/device_ID_base.py/_change_info_to_new_type
        """
        # preparation
        test_info = pd.DataFrame(dummy_device_id_info_2_item_new_type)
        expected = test_info

        # execution
        actual = pd.DataFrame()
        actual: pd.DataFrame = dim._change_info_to_new_type(test_info)

        # inspection
        assert expected.to_dict() == actual.to_dict()

    def test_is_new_type_change_keys(self):
        """Test case of new type.
        SUT:/device_id_manager/device_ID_base.py/_change_info_to_new_type
        """
        # preparation
        test_info = pd.DataFrame(dummy_device_id_info_change_keys)
        expected = test_info.rename(
            columns={
                "DeviceKeys": "deviceKeys",
                "PortKeys": "portKeys",
                "DeviceType": "deviceType",
            }
        )

        # execution
        actual = pd.DataFrame()
        actual: pd.DataFrame = dim._change_info_to_new_type(test_info)

        # inspection
        assert expected.to_dict() == actual.to_dict()


class TestIsValidUuid:
    """Unit test class for _is_valid_uuid.
    SUT:/device_id_manager/device_ID_base.py/_is_valid_uuid
    """

    def test_successful_case(self):
        """Test successful case of _is_valid_uuid.

        SUT:/device_id_manager/device_ID_base.py/_is_valid_uuid
        """
        # preparation
        test_identifier = str(uuid.uuid4())
        expected = True

        # execution
        actual = dim._is_valid_uuid(identifier=test_identifier)

        # inspection
        assert expected is actual

    def test_invalid_uuid_case(self):
        """Test invalid uuid case.
        SUT:/device_id_manager/device_ID_base.py/_is_valid_uuid
        Test for errors in the following cases.
            An identifier other than uuid was entered.
        """
        # preparation
        test_identifier_01 = 1
        test_identifier_02 = "0001"
        expected_01 = False
        expected_02 = False

        # execution
        actual_01 = dim._is_valid_uuid(identifier=test_identifier_01)
        actual_02 = dim._is_valid_uuid(identifier=test_identifier_02)

        # inspection
        assert expected_01 is actual_01
        assert expected_02 is actual_02


class TestReadJsonFile:
    """Unit test class for _read_json_file.
    SUT:/device_id_manager/device_ID_base.py/_read_json_file
    """

    def test_successful_case(self, mocker: MockFixture):
        """Test successful case of _read_json_file."""
        # preparation
        expected = {}
        path = path_setting().data_file_dir + dim._DEVICE_ID_MANAGER_FILE_NAME
        ret_device_id_info = pd.DataFrame(expected)
        mocker.patch.object(pd, "read_json", return_value=ret_device_id_info)
        # execution
        actual = dim._read_json_file(path)

        # inspection
        assert expected == actual

    def test_successful_case_not_empty(self, mocker: MockFixture):
        """Test successful case of _read_json_file."""
        # preparation
        expected = dummy_device_id_info_2_item_dict
        path = path_setting().data_file_dir + dim._DEVICE_ID_MANAGER_FILE_NAME

        ret_device_id_info = pd.DataFrame(dummy_device_id_info_2_item)

        mocker.patch.object(pd, "read_json", return_value=ret_device_id_info)
        # execution
        actual = dim._read_json_file(path)

        # inspection
        assert expected == actual

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    def test_jsondecodeecodeerror_case(self, mocker: MockFixture, caplog):
        """Test JSONDecodeError error.
        Test for errors in the following cases.
            json.load() raise json.JSONDecodeError.
        """
        # preparation
        path = path_setting().data_file_dir + dim._DEVICE_ID_MANAGER_FILE_NAME
        caplog.clear()  # clear log

        mocker.patch.object(pd, "read_json", side_effect=json.JSONDecodeError)

        # execution
        with pytest.raises(exc.DeviceIdFileIncorrectHwControlError):
            _ = dim._read_json_file(path)

        # check log
        levelname = "ERROR"
        messages = [f"[{DIM_MODULE_NAME}] The Device ID Management File is incorrect."]
        check_log_message(caplog, levelname, CONSTANT_REQUEST_ID, messages)

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    def test_permission_error_case(self, mocker: MockFixture, caplog):
        """Test PermissionError error.
        Test for errors in the following cases.
            with open raise FileNotFoundError.
        """
        # preparation
        path = path_setting().data_file_dir + dim._DEVICE_ID_MANAGER_FILE_NAME
        caplog.clear()  # clear log

        mocker.patch.object(pd, "read_json", side_effect=PermissionError)

        # execution
        with pytest.raises(exc.DeviceIdFileNotFoundHwControlError):
            _ = dim._read_json_file(path)
        # check log
        levelname = "ERROR"
        messages = [f"[{DIM_MODULE_NAME}] The Device ID Management File was not found or there was a permission error."]
        check_log_message(caplog, levelname, CONSTANT_REQUEST_ID, messages)

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    def test_filenotfounderror_case(self, mocker: MockFixture, caplog):
        """Test FileNotFoundError error.
        Test for errors in the following cases.
         with open raise FileNotFoundError.
        """
        # preparation
        path = path_setting().data_file_dir + dim._DEVICE_ID_MANAGER_FILE_NAME
        caplog.clear()  # clear log

        mocker.patch.object(pd, "read_json", side_effect=FileNotFoundError)

        expected = {}

        # execution
        actual = None
        actual = dim._read_json_file(path)
        # inspection
        assert expected == actual

    def test_err_from_chang_type(self, mocker: MockFixture):
        """Test DeviceIdFileIncorrectHwControlError case of
        _read_json_file because TypeError/KeyError is occurred from
        _change_info_to_new_type

        """
        # preparation
        path = path_setting().data_file_dir + dim._DEVICE_ID_MANAGER_FILE_NAME

        ret_device_id_info = pd.DataFrame(dummy_device_id_info_invalid_value)

        mocker.patch.object(pd, "read_json", return_value=ret_device_id_info)
        # execution
        with pytest.raises(exc.DeviceIdFileIncorrectHwControlError):
            _ = dim._read_json_file(path)


class TestAssignDeviceId:
    """Unit test class for assign_device_id.
    SUT:/device_id_manager/device_ID_base.py/assign_device_id
    """

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    def test_permission_error_case_device_id_file(self, mocker: MockFixture, caplog):
        """Test PermissionError error.
        Test for errors in the following cases.
        with open raise FileNotFoundError.
        """
        # preparation
        caplog.clear()  # clear log
        mocker.patch.object(pd, "read_json", side_effect=PermissionError)
        # execution
        with pytest.raises(exc.DeviceIdFileNotFoundHwControlError):
            dim.assign_device_id()

        # check log
        levelname = "ERROR"
        messages = [f"[{DIM_MODULE_NAME}] The Device ID Management File was not found or there was a permission error."]
        check_log_message(caplog, levelname, CONSTANT_REQUEST_ID, messages)

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    def test_permission_error_case_invalid_serial_number_file(self, mocker: MockFixture, caplog):
        """Test PermissionError error.
        Test for errors in the following cases.
        with open raise FileNotFoundError.
        """
        # preparation
        caplog.clear()  # clear log

        def mocked_read_json(file_path, dtype):  # pylint: disable=W0613
            """side_effect"""
            if file_path == path_setting().data_file_dir + dim._DEVICE_ID_MANAGER_FILE_NAME:
                return pd.DataFrame()
            raise PermissionError

        mocker.patch.object(pd, "read_json", side_effect=mocked_read_json)
        # execution
        with pytest.raises(exc.InvalidSerialNumberConfigFileNotFoundHwControlError):
            dim.assign_device_id()
        # check log
        levelname = "ERROR"
        messages = [
            f"[{DIM_MODULE_NAME}] The invalid serial number file was not found or there was a permission error."
        ]
        check_log_message(caplog, levelname, CONSTANT_REQUEST_ID, messages)


class TestDeviceIdToFmPortId:
    """Unit test class for device_id_to_fm_port_id.
    SUT:/device_id_manager/device_ID_base.py/device_id_to_fm_port_id
    """

    def test_empty_json_data_case(self, mocker: MockFixture):
        """Test  case.
        Test for errors in the following cases.
        _read_json_file return empty Json file such that
        {"data": []}
        Expect sut raise DeviceIdNotFoundHwControlError.
        """
        dim.id_to_info = {}

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"
        empty_device_id_info: dict = {}
        mocker.patch.object(dim, "_read_json_file", return_value=empty_device_id_info)

        # execution
        with pytest.raises(exc.DeviceIdNotFoundHwControlError):
            _ = dim.device_id_to_fm_port_id(device_id)

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
            _ = dim.device_id_to_fm_port_id(device_id)

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
            _ = dim.device_id_to_fm_port_id(device_id)

    def test_successful_case(self, mocker: MockFixture):
        """Test successful case of device_id_to_fm_port_id."""
        # preparation
        expected = "852f416b-a6e7-4d32-b9c4-238901544d48"

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        # clear id_to_info for mock
        dim.id_to_info = {}

        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.device_id_to_fm_port_id(device_id)

        # inspection
        assert expected == actual

    def test_successful_case_ite12(self, mocker: MockFixture):
        """Test successful case of device_id_to_fm_port_id."""
        # preparation
        expected = "852f416b-a6e7-4d32-b9c4-238901544d48"

        device_id = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"

        # clear id_to_info for mock
        dim.id_to_info = {}

        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_ite12)

        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.device_id_to_fm_port_id(device_id)

        # inspection
        assert expected == actual

    def test_device_already_disabled_sub_flow(self, mocker: MockFixture):
        """Test Device already disabled case.
        Test following cases.
        If specified device has been disabled.
        Expect sut return None.
        """
        dim.id_to_info = {}
        # preparation
        expected = None
        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        dummy_obtained_data = dummy_device_id_info_d.set_index("DeviceID").to_dict(orient="index")

        mocker.patch.object(dim, "_read_json_file", return_value=dummy_obtained_data)

        # disabled device
        device_id = "6409b69d-232e-4e83-8f69-40914a103ae6"

        # execution
        actual = dim.device_id_to_fm_port_id(device_id)

        # inspection
        assert expected is actual

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
            _ = dim.device_id_to_fm_port_id(device_id)

    def test_invaliddeviceidinfohwcontrolerror_case(self, mocker: MockFixture):
        """Test InvalidDeviceIdInfoHwControlError case.
        Test for errors in the following cases.
        If the specified device is a switch.
        Expect sut raise InvalidDeviceIdInfoHwControlError.
        """
        mocker.patch.object(dim, "_read_json_file", side_effect=exc.InvalidTypeDeviceIdHwControlError)

        # dummy data of switch
        device_id = "e9345fcb-4951-4da8-a569-358b00361083"

        with pytest.raises(exc.InvalidTypeDeviceIdHwControlError):
            _ = dim.device_id_to_fm_port_id(device_id)

    def test_deviceidnotfoundhwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIdNotFoundHwControlError case.

        Test for errors in the following cases.

            If the specified device is a switch.
            Expect sut raise DeviceIdNotFoundHwControlError.
        """
        mocker.patch.object(dim, "_read_json_file", side_effect=exc.DeviceIdNotFoundHwControlError)

        # nonexistent device ID
        device_id = "4d4f8988-ce27-4e6a-b83b-6309e4f7d5ad"

        # execution
        with pytest.raises(exc.DeviceIdNotFoundHwControlError):
            _ = dim.device_id_to_fm_port_id(device_id)

    def test_first_key_empty(self, mocker: MockFixture):
        """Test case of first key is empty."""
        # preparation
        expected = None

        device_id = "e9345fcb-4951-4da8-a569-358b00361085"

        # clear id_to_info for mock
        dim.id_to_info = {}

        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_test_first_key)
        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.device_id_to_fm_port_id(device_id)

        # inspection
        assert expected == actual


class TestDeviceIdToFmPortIdMultiHostPort:
    """Unit test class for device_id_to_fm_port_id_multi_hostport.

    SUT:/device_id_manager/device_ID_base.py/device_id_to_fm_port_id_multi_hostport
    """

    def test_empty_json_data_case(self, mocker: MockFixture):
        """Test  case.

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
            _ = dim.device_id_to_fm_port_id_multi_hostport(device_id, fm_manager_id)

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
            _ = dim.device_id_to_fm_port_id_multi_hostport(device_id, fm_manager_id)

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
            _ = dim.device_id_to_fm_port_id_multi_hostport(device_id, fm_manager_id)

    def test_successful_case(self, mocker: MockFixture):
        """Test successful case of device_id_to_fm_port_id."""
        # preparation
        expected = ["eed37ccf-293e-4da4-aeef-f42843192f53"]

        device_id = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"
        fm_manager_id = "6_66-abc666"

        # clear id_to_info for mock
        dim.id_to_info = {}

        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.device_id_to_fm_port_id_multi_hostport(device_id, fm_manager_id)

        # inspection
        assert expected == actual

    def test_successful_case_ite12(self, mocker: MockFixture):
        """Test successful case of device_id_to_fm_port_id."""
        # preparation
        expected = ["eed37ccf-293e-4da4-aeef-f42843192f53"]

        device_id = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"
        fm_manager_id = "6_66-abc666"

        # clear id_to_info for mock
        dim.id_to_info = {}

        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info_ite12)
        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # execution
        actual = dim.device_id_to_fm_port_id_multi_hostport(device_id, fm_manager_id)

        # inspection
        assert expected == actual

    def test_successful_case_none(self, mocker: MockFixture):
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
        actual = dim.device_id_to_fm_port_id_multi_hostport(device_id, fm_manager_id)

        # inspection
        assert expected == actual

    def test_device_already_disabled_sub_flow(self, mocker: MockFixture):
        """Test Device already disabled case.

        Test following cases.

            If specified device has been disabled.
            Expect sut return None.
        """
        dim.id_to_info = {}
        # preparation
        expected = []

        # clear id_to_info for mock
        dim.id_to_info = {}

        dummy_device_id_info_d = pd.DataFrame(dummy_device_id_info)
        mocker.patch.object(pd, "read_json", return_value=dummy_device_id_info_d)

        # disabled device
        device_id = "6409b69d-232e-4e83-8f69-40914a103ae6"
        fm_manager_id = "dummy"

        # execution
        actual = dim.device_id_to_fm_port_id_multi_hostport(device_id, fm_manager_id)

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
            _ = dim.device_id_to_fm_port_id_multi_hostport(device_id, fm_manager_id)

    def test_invaliddeviceidinfohwcontrolerror_case(self, mocker: MockFixture):
        """Test InvalidDeviceIdInfoHwControlError case.

        Test for errors in the following cases.

            If the specified device is a switch.
            Expect sut raise InvalidDeviceIdInfoHwControlError.
        """
        mocker.patch.object(dim, "_read_json_file", side_effect=exc.InvalidTypeDeviceIdHwControlError)

        # dummy data of switch
        device_id = "e9345fcb-4951-4da8-a569-358b00361083"
        fm_manager_id = "7_77-abc777"

        # execution
        with pytest.raises(exc.InvalidTypeDeviceIdHwControlError):
            _ = dim.device_id_to_fm_port_id_multi_hostport(device_id, fm_manager_id)

    def test_deviceidnotfoundhwcontrolerror_case(self, mocker: MockFixture):
        """Test DeviceIdNotFoundHwControlError case.
        Test for errors in the following cases.
        If the specified device is a switch.
        Expect sut raise DeviceIdNotFoundHwControlError.
        """
        mocker.patch.object(dim, "_read_json_file", side_effect=exc.DeviceIdNotFoundHwControlError)

        # nonexistent device ID
        device_id = "4d4f8988-ce27-4e6a-b83b-6309e4f7d5ad"
        fm_manager_id = "mogumogu"

        # execution
        with pytest.raises(exc.DeviceIdNotFoundHwControlError):
            _ = dim.device_id_to_fm_port_id_multi_hostport(device_id, fm_manager_id)

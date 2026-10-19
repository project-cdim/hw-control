# Copyright 2026 NEC Corporation
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


"""unit test module in device_id_base.py (part 6)

system under test
/app/common/dim/device_id_base.py

Test target function:
get_device_id_of_switch_port_type
"""

import logging
import typing
import uuid
from unittest.mock import Mock
from pytest_mock import MockerFixture
import pytest
import pandas

## system under test ###################
from app.common import constants as con
from app.common.dim import device_id_base as dim
from app.common import basic_exceptions as exc

_TEST_LOGGER_MODULE = "app.common.dim.device_id_base"

dummy_device_id_info = [
    {
        "DeviceID": "e7dd954e-de27-4b2a-a06b-98bdfee6270d",
        "deviceType": "networkInterface",
        "fmPortID": {"fm-host-switch-001": ["0x00000001"]},
        "oobDeviceID": "NIC-0001",
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": {"fm-host-switch-001": ["host-switch-id"]},
        "switchSerialNumber": None,
        "switchModel": None,
        "switchManufacturer": None,
        "fmManagerID": ["fm-host-switch-001"],
        "oobManagerID": ["oob-host-switch-001"],
        "portKeys": None,
        "deviceKeys": "{'fabric_key': 'host', 'unique_key': '00:11:22:33:44:55'}",
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "5fed488e-9898-4ae0-bfc4-41cd2cf46629",
        "deviceType": "networkInterface",
        "fmPortID": {},
        "oobDeviceID": "NIC-0002",
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": {},
        "switchSerialNumber": None,
        "switchModel": None,
        "switchManufacturer": None,
        "fmManagerID": [],
        "oobManagerID": ["oob-host-switch-001"],
        "portKeys": None,
        "deviceKeys": "{'fabric_key': 'host', 'unique_key': '00:11:22:33:44:66'}",
        "switchPortType": None,
        "fmValid": False,
        "valid": False,
    },
    {
        "DeviceID": "70a374c5-d771-421a-9319-6c845166b2a5",
        "deviceType": "CPU",
        "fmPortID": {},
        "oobDeviceID": "PROC-0001",
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "CN705213WV",
        "CPUManufacturer": "NEC",
        "CPUModel": "Express5800/R120i-2M",
        "fmSwitchID": None,
        "connectedFmSwitchID": {},
        "switchSerialNumber": None,
        "switchModel": None,
        "switchManufacturer": None,
        "fmManagerID": [],
        "oobManagerID": ["oob-host-switch-001"],
        "portKeys": None,
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": False,
        "valid": True,
    },
    {
        "DeviceID": "d865a6cc-bc21-4faa-90a6-e09ea9fffad2",
        "deviceType": "switch",
        "fmPortID": {},
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "host-switch-id",
        "connectedFmSwitchID": {},
        "switchSerialNumber": None,
        "switchModel": None,
        "switchManufacturer": None,
        "fmManagerID": ["fm-host-switch-001"],
        "oobManagerID": [],
        "portKeys": None,
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "db438c89-5d88-4c46-9bfa-0e4366a7c655",
        "deviceType": "networkInterface",
        "fmPortID": {"fm-device-switch-001": ["plx1"]},
        "oobDeviceID": "NIC-0001",
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": {"fm-device-switch-001": ["device-switch-id"]},
        "switchSerialNumber": None,
        "switchModel": None,
        "switchManufacturer": None,
        "fmManagerID": ["fm-device-switch-001"],
        "oobManagerID": ["oob-device-switch-001"],
        "portKeys": None,
        "deviceKeys": "{'fabric_key': 'device', 'unique_key': '00:11:22:33:44:55'}",
        "switchPortType": "USP",
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "6fac67fc-84c2-437a-8e48-a68b557582ac",
        "deviceType": "networkInterface",
        "fmPortID": {"fm-device-switch-001": ["plx2"]},
        "oobDeviceID": "NIC-0002",
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": {"fm-device-switch-001": ["device-switch-id"]},
        "switchSerialNumber": None,
        "switchModel": None,
        "switchManufacturer": None,
        "fmManagerID": ["fm-device-switch-001"],
        "oobManagerID": ["oob-device-switch-001"],
        "portKeys": None,
        "deviceKeys": "{'fabric_key': 'device', 'unique_key': '00:11:22:33:44:66'}",
        "switchPortType": "USP",
        "fmValid": True,
        "valid": False,
    },
    {
        "DeviceID": "0a0fffe6-c418-4d6d-b328-fa9e1cd3c324",
        "deviceType": "GPU",
        "fmPortID": {"fm-device-switch-001": ["plx10"]},
        "oobDeviceID": "GPU-0001",
        "PCIeVendorId": "1bcf",
        "PCIeDeviceId": "001c",
        "PCIeDeviceSerialNumber": "deadbeef1badcafe",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": {"fm-device-switch-001": ["device-switch-id"]},
        "switchSerialNumber": None,
        "switchModel": None,
        "switchManufacturer": None,
        "fmManagerID": ["fm-device-switch-001"],
        "oobManagerID": ["oob-device-switch-001"],
        "portKeys": None,
        "deviceKeys": "{'GPU_GUID_V1': 'GPU-b96ff8ea-a035-0f52-2b48-55df655304c1'}",
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "cb063bce-3c16-4dd9-b074-a3b86e302012",
        "deviceType": "switch",
        "fmPortID": {},
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "device-switch-id",
        "connectedFmSwitchID": {},
        "switchSerialNumber": None,
        "switchModel": None,
        "switchManufacturer": None,
        "fmManagerID": ["fm-device-switch-001"],
        "oobManagerID": [],
        "portKeys": None,
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "cc7896b2-ae41-4d3c-80b3-f9137b5f0a72",
        "deviceType": "networkInterface",
        "fmPortID": {},
        "oobDeviceID": "NIC-0002",
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": {},
        "switchSerialNumber": None,
        "switchModel": None,
        "switchManufacturer": None,
        "fmManagerID": [],
        "oobManagerID": ["oob-host-switch-001"],
        "portKeys": None,
        "deviceKeys": "{'fabric_key': 'host', 'unique_key': '00:11:22:33:44:77'}",
        "switchPortType": None,
        "fmValid": False,
        "valid": True,
    },
    {
        "DeviceID": "4b5fc402-bd86-476a-8720-7675128b4ce0",
        "deviceType": "networkInterface",
        "fmPortID": {"fm-device-switch-001": ["plx2"]},
        "oobDeviceID": "NIC-0002",
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": {"fm-device-switch-001": ["device-switch-id"]},
        "switchSerialNumber": None,
        "switchModel": None,
        "switchManufacturer": None,
        "fmManagerID": ["fm-device-switch-001"],
        "oobManagerID": ["oob-device-switch-001"],
        "portKeys": None,
        "deviceKeys": "{'fabric_key': 'device', 'unique_key': '00:11:22:33:44:77'}",
        "switchPortType": "USP",
        "fmValid": True,
        "valid": True,
    },
]


def _create_dummy_device_info(device_keys: typing.Any) -> dict:
    """Create a dummy device information dictionary."""
    return {
        "DeviceID": str(uuid.uuid4()),
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
        "connectedFmSwitchID": None,
        "switchSerialNumber": None,
        "switchModel": None,
        "switchManufacturer": None,
        "fmManagerID": None,
        "oobManagerID": None,
        "portKeys": None,
        "deviceKeys": device_keys,
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": True,
    }


@pytest.fixture(scope="function")
def _get_devices_info(mocker: MockerFixture) -> Mock:
    """Fixture to mock _get_devices_info function."""
    data = pandas.DataFrame(dummy_device_id_info).set_index("DeviceID").to_dict(orient="index")
    return mocker.patch("app.common.dim.device_id_base._get_devices_info", return_value=data)


@pytest.mark.parametrize(
    ("device_id", "switch_port_type"),
    [
        ("e7dd954e-de27-4b2a-a06b-98bdfee6270d", con.SwitchPortType.DSP),
        ("6fac67fc-84c2-437a-8e48-a68b557582ac", con.SwitchPortType.USP),
        ("70a374c5-d771-421a-9319-6c845166b2a5", None),
    ],
)
def test_get_device_id_of_switch_port_type_same_port_type(
    device_id: str, switch_port_type: con.SwitchPortType | None, _get_devices_info: Mock
):
    """Test case where the specified device ID matches the switch port type."""
    assert dim.get_device_id_of_switch_port_type(device_id, switch_port_type) == device_id


@pytest.mark.parametrize(
    ("device_id", "switch_port_type"),
    [
        ("70a374c5-d771-421a-9319-6c845166b2a5", con.SwitchPortType.DSP),
        ("0a0fffe6-c418-4d6d-b328-fa9e1cd3c324", con.SwitchPortType.USP),
    ],
)
def test_get_device_id_of_switch_port_type_unique_key_not_set(
    device_id: str, switch_port_type: con.SwitchPortType, _get_devices_info: Mock, caplog: pytest.LogCaptureFixture
):
    """Test case where a device ID that does not have a unique key is specified."""
    caplog.set_level(logging.INFO, logger=_TEST_LOGGER_MODULE)
    assert dim.get_device_id_of_switch_port_type(device_id, switch_port_type) is None
    assert f"{switch_port_type.value} device_id={device_id} does not have unique_key" in caplog.text


@pytest.mark.parametrize(("switch_port_type"), [con.SwitchPortType.DSP, con.SwitchPortType.USP, None])
def test_get_device_id_of_switch_port_type_invalid_device_id(
    switch_port_type: con.SwitchPortType | None, _get_devices_info: Mock, caplog: pytest.LogCaptureFixture
):
    """Test case where a non-existent device ID is specified."""
    caplog.set_level(logging.INFO, logger=_TEST_LOGGER_MODULE)
    assert dim.get_device_id_of_switch_port_type("7fb988f8-ab0d-4821-a319-b2ccd3f32a65", switch_port_type) is None
    assert "device_id=7fb988f8-ab0d-4821-a319-b2ccd3f32a65 not found" in caplog.text


@pytest.mark.parametrize(
    ("device_id", "switch_port_type", "expected"),
    [
        ("db438c89-5d88-4c46-9bfa-0e4366a7c655", con.SwitchPortType.DSP, "e7dd954e-de27-4b2a-a06b-98bdfee6270d"),
        ("e7dd954e-de27-4b2a-a06b-98bdfee6270d", con.SwitchPortType.USP, "db438c89-5d88-4c46-9bfa-0e4366a7c655"),
        ("4b5fc402-bd86-476a-8720-7675128b4ce0", None, "cc7896b2-ae41-4d3c-80b3-f9137b5f0a72"),
        ("cc7896b2-ae41-4d3c-80b3-f9137b5f0a72", con.SwitchPortType.USP, "4b5fc402-bd86-476a-8720-7675128b4ce0"),
    ],
)
def test_get_device_id_of_switch_port_type_found(
    device_id: str, switch_port_type: con.SwitchPortType | None, expected: str, _get_devices_info: Mock
):
    """Test case where the conversion of the specified device ID is successful,"""
    assert dim.get_device_id_of_switch_port_type(device_id, switch_port_type) == expected


@pytest.mark.parametrize(
    ("device_id", "switch_port_type", "switch_port_type_str"),
    [
        ("6fac67fc-84c2-437a-8e48-a68b557582ac", None, "None"),
        ("5fed488e-9898-4ae0-bfc4-41cd2cf46629", con.SwitchPortType.USP, con.SwitchPortType.USP.value),
    ],
)
def test_get_device_id_of_switch_port_type_not_found(
    device_id: str,
    switch_port_type: con.SwitchPortType | None,
    switch_port_type_str: str,
    _get_devices_info: Mock,
    caplog: pytest.LogCaptureFixture,
):
    """Test case where the target device ID for conversion is not found."""
    caplog.set_level(logging.INFO, logger=_TEST_LOGGER_MODULE)
    assert dim.get_device_id_of_switch_port_type(device_id, switch_port_type) is None
    assert f"{switch_port_type_str} device_id={device_id} the unique_key=00:11:22:33:44:66 not found" in caplog.text


def test_get_device_id_of_switch_port_type_device_keys_data_broken(
    mocker: MockerFixture, caplog: pytest.LogCaptureFixture
):
    """Test for cases where the stored device_keys information is corrupted."""
    _info = dummy_device_id_info.copy()
    _info.append(_create_dummy_device_info(1))
    _info.append(_create_dummy_device_info("{'key': }"))
    data = pandas.DataFrame(_info).set_index("DeviceID").to_dict(orient="index")
    mocker.patch("app.common.dim.device_id_base._get_devices_info", return_value=data)
    caplog.set_level(logging.WARNING, logger=_TEST_LOGGER_MODULE)
    dim.get_device_id_of_switch_port_type("5fed488e-9898-4ae0-bfc4-41cd2cf46629", con.SwitchPortType.USP)
    assert "invalid format deviceKeys=1 saved" in caplog.text
    assert "invalid format deviceKeys={'key': } saved" in caplog.text
    assert "ValueError" in caplog.text
    assert "SyntaxError" in caplog.text


@pytest.mark.parametrize(
    ("exception"), [(exc.DeviceIDFileNotFoundHWControlError), (exc.DeviceIDFileIncorrectHWControlError)]
)
def test_get_device_id_of_switch_port_type_device_exception(exception: type[Exception], mocker: MockerFixture):
    """Test for case where an exception occurs in the _get_device_info function."""
    mocker.patch("app.common.dim.device_id_base._get_devices_info", side_effect=exception)
    with pytest.raises(exception):
        dim.get_device_id_of_switch_port_type("7fb988f8-ab0d-4821-a319-b2ccd3f32a65", None)

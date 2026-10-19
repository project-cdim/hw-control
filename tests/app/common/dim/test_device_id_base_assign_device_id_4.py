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


"""Device manager UT (part 4)

Device manager UT.
Note: Currently,
data accuracy is not automated and must be checked manually.
"""

import logging
import os
import json
import shutil
from collections import Counter

from unittest.mock import patch
import pytest
from pytest import LogCaptureFixture, MonkeyPatch
from pytest_mock import MockFixture

import pandas as pd

from app.common.dim.device_id_base import assign_device_id
from app.common.dim.device_id_base import update_same_sn_devices
from app.common.dim import device_id_manager as dim
from app.common.utils.fm_plugin_base import FMPortData, FMSwitchData
from app.common.utils.oob_plugin_base import OOBDeviceListItem

reset_data = []

fm_manager_list = ["qemu-01"]
fm_manager_list_multi = ["qemu-01", "qemu-02"]
oob_manager_list = ["oob-1"]

_TP_FILE_PATH = os.path.dirname(os.path.realpath(__file__))
_INVALID_SERIAL_NUMBER_FILE_DIR = "/invalid_serial_number.json"
_DEVICE_ID_MANAGER_FILE_DIR = "/device_id_info.json"
_DEV_ID_MNG_FILE = _TP_FILE_PATH + _DEVICE_ID_MANAGER_FILE_DIR
_EVN_SET_PATH = _TP_FILE_PATH
_INVALID_SERIAL_NUMBER_FILE_PATH = _EVN_SET_PATH + _INVALID_SERIAL_NUMBER_FILE_DIR
_DEVICE_ID_MANAGER_FILE_PATH = _EVN_SET_PATH + _DEVICE_ID_MANAGER_FILE_DIR
_INVALID_SERIAL_NUMBER_FILE_PATH_bak = _INVALID_SERIAL_NUMBER_FILE_PATH + ".bak"
_DEVICE_ID_MANAGER_FILE_PATH_bak = _DEVICE_ID_MANAGER_FILE_PATH + ".bak"

_CHECK_keys = [
    "deviceType",
    "fmPortID",
    "oobDeviceID",
    "PCIeVendorId",
    "PCIeDeviceId",
    "PCIeDeviceSerialNumber",
    "CPUSerialNumber",
    "CPUManufacturer",
    "CPUModel",
    "fmSwitchID",
    "connectedFmSwitchID",
    "switchSerialNumber",
    "switchModel",
    "switchManufacturer",
    "fmManagerID",
    "oobManagerID",
    "portKeys",
    "deviceKeys",
    "switchPortType",
    "fmValid",
    "valid",
]


@pytest.fixture(autouse=True)
def set_env(monkeypatch):
    """
    Set environment variable.
    """
    monkeypatch.setenv("HW_CONTROL_DATA_FILE_DIR", _EVN_SET_PATH)
    monkeypatch.setenv("HW_CONTROL_CONFIG_FILE_DIR", _EVN_SET_PATH)
    with open(_DEVICE_ID_MANAGER_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump([], f)
    with open(_INVALID_SERIAL_NUMBER_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump([], f)


def all_reset():
    """no error
    This is not test case.
    reset all information files.
    """
    try:
        os.rename(_INVALID_SERIAL_NUMBER_FILE_PATH_bak, _INVALID_SERIAL_NUMBER_FILE_PATH)
        os.rename(_DEVICE_ID_MANAGER_FILE_PATH_bak, _DEVICE_ID_MANAGER_FILE_PATH)
    except Exception:
        pass
    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, reset_data)


def convert_port_data(dict_data: dict) -> dict[str, list[FMPortData]]:
    """
    change list type to FMPortData.
    """
    return {"data": [FMPortData(**port_data) for port_data in dict_data["data"]]}


def convert_switch_data(dict_data: dict) -> dict[str, list[FMSwitchData]]:
    """
    change list type to FMSwitchData.
    """
    return {"data": [FMSwitchData(**switch_data) for switch_data in dict_data["data"]]}


def convert_device_data(list_data: list) -> list[OOBDeviceListItem]:
    """
    change list type to OOBDeviceListItem.
    """
    return [OOBDeviceListItem(**device_data) for device_data in list_data]


def mv_output(ptn: str):
    """
    Back up the device_id_info.json file.
    """
    tgt_path = _TP_FILE_PATH + "/output/" + ptn
    os.makedirs(tgt_path, exist_ok=True)
    shutil.copy(_DEV_ID_MNG_FILE, tgt_path + "/device_id_info.json")


def __is_same_data(e_data: dict[str, str], new_data: dict[str, str], keys: list[str], inx: int) -> bool:
    """
    Check if the data is identical to the expected data.
    """
    count = 0
    for key in keys:
        except_data = e_data.get(key)
        out_data = new_data.get(key)
        if except_data != out_data:
            if (
                isinstance(except_data, list)
                and isinstance(out_data, list)
                and Counter(except_data) == Counter(out_data)
            ):
                continue
            count = inx + 1
            print(f"Failed: {count}th {key} is different")
            print(f"Failed: except_data is {except_data}")
            print(f"Failed: out_data is {out_data}")
            return False
    return True


def check_output(ptn: str):
    """
    Check the output of device_id_info.json file.
    """
    outf_d = _TP_FILE_PATH + "/output/"
    outf = _TP_FILE_PATH + "/output/" + ptn + "/device_id_info.json"
    expectf = _TP_FILE_PATH + "/expect_data/" + ptn + "/device_id_info.json"
    compile_ret = False
    with open(outf, encoding="utf-8") as f:
        try:
            data = json.load(f)
            new_data = data
            with open(expectf, encoding="utf-8") as e_f:
                data = json.load(e_f)
                e_deta = data
            if new_data == e_deta:
                compile_ret = True
            else:
                inx = 0
                for c_data in new_data:
                    compile_ret = __is_same_data(e_deta[inx], c_data, _CHECK_keys, inx)
                    inx = inx + 1
                    if compile_ret is False:
                        break
        except json.JSONDecodeError as e:
            print(f"Failed: {e}")
            shutil.rmtree(outf_d)
            assert False
        finally:
            f.close()
    shutil.rmtree(outf_d)
    assert compile_ret is True


class MockPluginGetManagerList:
    """set result of get_manager_list
    set result get_manager_list
    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        return {"data": []}

    def get_switch_info(self):
        """set result of get_switch_info
        set result of all get_switch_info
        """
        return {"data": []}

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        return []

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "FM":
            return fm_manager_list
        return oob_manager_list


def is_valid_type(column_data, expected_type):
    """Check if all elements in the column match the expected type."""
    return column_data.apply(lambda x: isinstance(x, expected_type) if pd.notna(x) else True).all()


def check_data_type():
    """Check the type of data."""
    # Read the DataFrame
    with open(_INVALID_SERIAL_NUMBER_FILE_PATH, "w", encoding="utf-8"):
        df = pd.read_json(_DEVICE_ID_MANAGER_FILE_PATH, dtype="object")

    if df.empty:
        return True

    # Column names and expected types
    column_checks = {
        "DeviceID": str,
        "deviceType": str,
        "fmPortID": dict,
        "oobDeviceID": str,
        "PCIeVendorId": str,
        "PCIeDeviceId": str,
        "PCIeDeviceSerialNumber": str,
        "CPUSerialNumber": str,
        "CPUManufacturer": str,
        "CPUModel": str,
        "fmSwitchID": str,
        "switchSerialNumber": str,
        "switchManufacturer": str,
        "portKeys": str,
        "deviceKeys": str,
        "switchPortType": str,
        "fmValid": bool,
        "valid": bool,
    }

    for column, expected_type in column_checks.items():
        if not is_valid_type(df[column], expected_type):
            print(f"Type of {column} is Incorrect")
            return False

    # Special case checks for lists (fmManagerID and oobManagerID)
    list_columns = ["fmManagerID", "oobManagerID"]
    for column in list_columns:
        if (
            not df[column]
            .apply(
                lambda x: isinstance(x, list)
                and (
                    len(x) == 0
                    or (len(x) > 0 and (not isinstance(x[0], list) or all(len(sublist) > 0 for sublist in x)))
                )
            )
            .all()
        ):
            print(f"Type of {column} is Incorrect")
            return False
    return True


def reset_setting_file(file_path: str, data):
    """reset the setting file.

    Reset the setting file device_id_info.json.
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.seek(0)
        json.dump(data, f, indent=4)


def reset_setting_file_not_json(file_path: str, data):
    """reset the setting file.

    Reset the setting file invalid_serial_number.json.
    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.seek(0)
        f.write(data)


pre_data = [
    {
        "DeviceID": "485063f8-3076-459c-8523-9bd8ba5487eb",
        "deviceType": None,
        "fmPortID": "333333333",
        "oobDeviceID": "test_oob_id_1",
        "PCIeVendorId": "000A",
        "PCIeDeviceId": "010B",
        "PCIeDeviceSerialNumber": "abcdef3312345678",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "test_data_5",
        "connectedFmSwitchID": "test_data_5",
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": "qemu-001",
        "oobManagerID": None,
        "portKeys": "test_data_6",
        "deviceKeys": None,
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "f3efffb7-b11b-4198-bd39-9da6458dc931",
        "deviceType": None,
        "fmPortID": None,
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "test_data_7",
        "connectedFmSwitchID": "test_data_7",
        "switchSerialNumber": "test_data_8",
        "switchManufacturer": "test_data_9",
        "switchModel": "test_data_10",
        "fmManagerID": "test_fm",
        "oobManagerID": None,
        "portKeys": "test_data_11",
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": True,
        "valid": True,
    },
    {
        "DeviceID": "5b96d128-bc88-4254-aaa5-5b4c8cbc49cc",
        "deviceType": "CPU",
        "fmPortID": None,
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "test_data_11",
        "CPUManufacturer": "test_data_12",
        "CPUModel": "test_data_13",
        "fmSwitchID": None,
        "connectedFmSwitchID": None,
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": None,
        "oobManagerID": "test_oob",
        "portKeys": None,
        "deviceKeys": "{'test': 'test_deviceKeys_01'}",
        "switchPortType": None,
        "fmValid": True,
        "valid": True,
    },
]

pre_data_sn = [
    {
        "PCIeVendorId": "",
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "CPU-123456789",
        "CPUManufacturer": "1af4",
        "CPUModel": "1024CPU",
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
    },
    {
        "PCIeVendorId": "1af4",
        "PCIeDeviceId": "1042",
        "PCIeDeviceSerialNumber": "1234567812345678",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": "",
    },
    {
        "PCIeVendorId": None,
        "PCIeDeviceId": "",
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": "",
        "CPUModel": None,
        "switchSerialNumber": "test_fac",
        "switchManufacturer": "test_model",
        "switchModel": "98765",
    },
]

switch_list_pre = {
    "data": [
        {
            "switchId": "test_data_7",
            "switchManufacturer": "test_data_8",
            "switchModel": "test_data_9",
            "switchSerialNumber": "test_data_10",
            "link": None,
        }
    ]
}

port_list_def = {
    "data": [
        {
            "id": "111",
            "switchId": "/aaaa/bbb/ccccc",
            "switchPortNumber": None,
            "switchPortType": "DSP",
            "fabricId": None,
            "link": None,
            "deviceType": "PCIe",
            "PCIClassCode": None,
            "PCIeVendorId": "1af4",
            "PCIeDeviceId": "1024",
            "PCIeDeviceSerialNumber": "1234567812345678",
            "CPUManufacturer": None,
            "CPUModel": None,
            "CPUSerialNumber": None,
            "LTSSMState": None,
            "deviceKeys": {},
            "portKeys": {"test": "tttttttttttt"},
            "capacity": None,
        }
    ]
}

switch_list_def = {
    "data": [
        {
            "switchId": "/ccccc/bbb/aaaaaa",
            "switchManufacturer": "test_fac",
            "switchModel": "test_model",
            "switchSerialNumber": "98765",
            "link": None,
        }
    ]
}

device_list_def = [
    {
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "CPU-123456789",
        "CPUManufacturer": "1af4",
        "CPUModel": "1024CPU",
        "portKeys": None,
        "deviceKeys": None,
        "deviceType": "CPU",
        "oobDeviceID": "test",
    }
]

port_list_invalid = {
    "data": [
        {
            "id": "test_id_1",
            "switchId": "test_si_2",
            "switchPortNumber": None,
            "switchPortType": "DSP",
            "fabricId": None,
            "link": None,
            "deviceType": "PCIe",
            "PCIClassCode": None,
            "PCIeVendorId": "1af4",
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": "1234567812345678",
            "CPUManufacturer": None,
            "CPUModel": None,
            "CPUSerialNumber": None,
            "LTSSMState": None,
            "deviceKeys": {},
            "portKeys": {},
            "capacity": None,
        }
    ]
}

switch_list_invalid = {
    "data": [
        {
            "switchId": "123",
            "switchManufacturer": "test_model",
            "switchModel": None,
            "switchSerialNumber": "test_fac",
            "link": None,
        }
    ]
}

device_list_invalid = [
    {
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "CPU-123456789",
        "CPUManufacturer": "1af4",
        "CPUModel": None,
        "portKeys": None,
        "deviceKeys": None,
        "deviceType": "CPU",
        "oobDeviceID": "12345677",
    }
]


class MockPluginPortAndSwitchAndDeviceInfo:
    """set result of get_xxxx_info
    all info
    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        return convert_port_data(port_list_def)

    def get_switch_info(self):
        """set result of get_switch_info
        set result of all get_switch_info
        """
        return convert_switch_data(switch_list_def)

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        return convert_device_data(device_list_def)

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


port_list_invalid_sn = {
    "data": [
        {
            "id": "test_id_1",
            "switchId": "test_si_2",
            "switchPortNumber": None,
            "switchPortType": "DSP",
            "fabricId": None,
            "link": None,
            "deviceType": "PCIe",
            "PCIClassCode": None,
            "PCIeVendorId": "1af4",
            "PCIeDeviceId": "1042",
            "PCIeDeviceSerialNumber": "1234567812345678",
            "CPUManufacturer": None,
            "CPUModel": None,
            "CPUSerialNumber": None,
            "LTSSMState": None,
            "deviceKeys": {},
            "portKeys": {"test": "test_pk_1"},
            "capacity": None,
        }
    ]
}

switch_list_invalid_sn = {
    "data": [
        {
            "switchId": "test_switchId",
            "switchManufacturer": "test_model",
            "switchModel": "98765",
            "switchSerialNumber": "test_fac",
            "link": None,
        }
    ]
}

device_list_invalid_sn = [
    {
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "CPU-123456789",
        "CPUManufacturer": "1af4",
        "CPUModel": "1024CPU",
        "portKeys": {"test": "test_pk_2"},
        "deviceKeys": {"test": "test_dk_2"},
        "deviceType": "CPU",
        "oobDeviceID": "12345",
    }
]


class MockPluginPortAndSwitchAndDeviceInfo9:
    """set result of get_xxxx_info
    set result of all get_xxxx_info
    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        return convert_port_data(port_list_invalid_sn)

    def get_switch_info(self):
        """set result of get_switch_info
        set result of all get_switch_info
        """
        return convert_switch_data(switch_list_invalid_sn)

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        return convert_device_data(device_list_invalid_sn)

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch("app.common.plugin.plugin_manager._get_plugin", return_value=MockPluginPortAndSwitchAndDeviceInfo9())
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_new_data_invalid_sn(monkeypatch, mocker: MockFixture):
    """No err

    New registration, invalid serial number
    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, pre_data_sn)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn26")
    check_output("ptn26")


device_list_invalid_sn_devicekeys = [
    {
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "CPU-123456789",
        "CPUManufacturer": "1af4",
        "CPUModel": "1024CPU",
        "portKeys": {"test": "test_pk_2"},
        "deviceKeys": {"test": "test_deviceKeys_01"},
        "deviceType": "CPU",
        "oobDeviceID": "12345",
    }
]


class MockPluginPortAndSwitchAndDeviceInfo10:
    """set result of get_xxxx_info
    set result of all get_xxxx_info
    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        return convert_port_data(port_list_invalid_sn)

    def get_switch_info(self):
        """set result of get_switch_info
        set result of all get_switch_info
        """
        return convert_switch_data(switch_list_invalid_sn)

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        return convert_device_data(device_list_invalid_sn_devicekeys)

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch(
    "app.common.plugin.plugin_manager._get_plugin",
    return_value=MockPluginPortAndSwitchAndDeviceInfo10(),
)
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_new_data_invalid_sn_but_device_keys(monkeypatch, mocker: MockFixture):
    """No err

    New registration, invalid serial number, deviceKeys
    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, pre_data_sn)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)

    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn27")
    check_output("ptn27")


pre_data_sn_not_str = [
    {
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "CPU-123456789",
        "CPUManufacturer": "1af4",
        "CPUModel": 1024,
        "switchSerialNumber": "",
        "switchManufacturer": None,
        "switchModel": None,
    },
    {
        "PCIeVendorId": "1af4",
        "PCIeDeviceId": "1042",
        "PCIeDeviceSerialNumber": 123456789,
        "CPUSerialNumber": None,
        "CPUManufacturer": "",
        "CPUModel": None,
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
    },
    {
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": "",
        "switchSerialNumber": "test_fac",
        "switchManufacturer": "test_model",
        "switchModel": 98765,
    },
]


@patch("app.common.plugin.plugin_manager._get_plugin", return_value=MockPluginPortAndSwitchAndDeviceInfo9())
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_new_data_invalid_sn_not_str(monkeypatch, mocker: MockFixture):
    """No err

    New registration, invalid serial number, not str
    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)
    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, pre_data_sn_not_str)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)

    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn28")
    check_output("ptn28")


port_list_invalid = {
    "data": [
        {
            "id": "test_id_1",
            "switchId": "test_si_2",
            "switchPortNumber": None,
            "switchPortType": "DSP",
            "fabricId": None,
            "link": None,
            "deviceType": "PCIe",
            "PCIClassCode": None,
            "PCIeVendorId": "1af4",
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": "1234567812345678",
            "CPUManufacturer": None,
            "CPUModel": None,
            "CPUSerialNumber": None,
            "LTSSMState": None,
            "deviceKeys": {},
            "portKeys": {},
            "capacity": None,
        }
    ]
}

switch_list_invalid = {
    "data": [
        {
            "switchId": "123",
            "switchManufacturer": "test_model",
            "switchModel": None,
            "switchSerialNumber": "test_fac",
            "link": None,
        }
    ]
}

device_list_invalid = [
    {
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "CPU-123456789",
        "CPUManufacturer": "1af4",
        "CPUModel": None,
        "portKeys": None,
        "deviceKeys": None,
        "deviceType": "CPU",
        "oobDeviceID": "12345677",
    }
]


class MockPluginPortAndSwitchAndDeviceInvalidInfo:
    """set result of get_xxxx_info
    set result of all get_xxxx_info
    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        return convert_port_data(port_list_invalid)

    def get_switch_info(self):
        """set result of get_switch_info
        set result of all get_switch_info
        """
        return convert_switch_data(switch_list_invalid)

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        return convert_device_data(device_list_invalid)

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch(
    "app.common.plugin.plugin_manager._get_plugin",
    return_value=MockPluginPortAndSwitchAndDeviceInvalidInfo(),
)
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_new_data_invalid_info(
    monkeypatch: MonkeyPatch, mocker: MockFixture, caplog: LogCaptureFixture
):
    """No err

    New registration, invalid serial number
    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, pre_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)

    ret = 0
    caplog.clear()
    with caplog.at_level(logging.INFO, logger=dim.__name__):
        assign_device_id()
        ret = 1

    assert ret == 1
    assert check_data_type()
    mv_output("ptn29")
    check_output("ptn29")

    # check log
    assert len(caplog.records) == 2

    # Inspection: Check the fm invalid device log.
    fm_invalid_device_log = caplog.records[0]
    assert fm_invalid_device_log.levelname == "INFO"
    assert (
        fm_invalid_device_log.getMessage() == f"device_info (FM Port ID: {str({'qemu-01': ['test_id_1']})}) is invalid."
    )

    # Inspection: Check the oob invalid device log.
    oob_invalid_device_log = caplog.records[1]
    assert oob_invalid_device_log.levelname == "INFO"
    assert oob_invalid_device_log.getMessage() == "device_info (OOB Device ID: 12345677) is invalid."


port_list_no_managerIds = {
    "data": [
        {
            "id": "1111",
            "switchId": "test_data_5",
            "switchPortNumber": None,
            "switchPortType": "DSP",
            "fabricId": None,
            "link": None,
            "deviceType": "PCIe",
            "PCIClassCode": None,
            "PCIeVendorId": "1af4",
            "PCIeDeviceId": "2a4b",
            "PCIeDeviceSerialNumber": "1234567812345678",
            "CPUManufacturer": None,
            "CPUModel": None,
            "CPUSerialNumber": None,
            "LTSSMState": None,
            "deviceKeys": {},
            "portKeys": {"test": "tttttttttttt"},
            "capacity": None,
        }
    ]
}

switch_list_no_managerIds = {
    "data": [
        {
            "switchId": "/ccccc/bbb/aaaaaa",
            "switchManufacturer": "test_data_9",
            "switchModel": "test_data_10",
            "switchSerialNumber": "test_data_8",
            "link": None,
        }
    ]
}

device_list_no_managerIds = [
    {
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "test_data_11",
        "CPUManufacturer": "test_data_12",
        "CPUModel": "test_data_13",
        "portKeys": None,
        "deviceKeys": None,
        "deviceType": "CPU",
        "oobDeviceID": "123",
    }
]


class MockPluginPortAndSwitchAndDeviceInfoNoManagerIDs:
    """set result of get_xxxx_info
    set result of all get_xxxx_info
    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        return convert_port_data(port_list_no_managerIds)

    def get_switch_info(self):
        """set result of get_switch_info
        set result of all get_switch_info
        """
        return convert_switch_data(switch_list_no_managerIds)

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        return convert_device_data(device_list_no_managerIds)


pre_data_no_managerIds = [
    {
        "DeviceID": "485063f8-3076-459c-8523-9bd8ba5487eb",
        "deviceType": None,
        "fmPortID": "333333333",
        "oobDeviceID": "test_oob_id_1",
        "PCIeVendorId": "000A",
        "PCIeDeviceId": "010B",
        "PCIeDeviceSerialNumber": "abcdef3312345678",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "test_data_5",
        "connectedFmSwitchID": "test_data_5",
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": "dummy",
        "fmManagerID": None,
        "oobManagerID": None,
        "portKeys": "test_data_6",
        "deviceKeys": None,
        "switchPortType": "DSP",
        "fmValid": False,
        "valid": True,
    },
    {
        "DeviceID": "f3efffb7-b11b-4198-bd39-9da6458dc931",
        "deviceType": None,
        "fmPortID": None,
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "test_data_7",
        "connectedFmSwitchID": "test_data_7",
        "switchSerialNumber": "test_data_8",
        "switchManufacturer": "test_data_9",
        "switchModel": "test_data_10",
        "fmManagerID": None,
        "oobManagerID": None,
        "portKeys": "test_data_11",
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": False,
        "valid": True,
    },
    {
        "DeviceID": "5b96d128-bc88-4254-aaa5-5b4c8cbc49cc",
        "deviceType": "CPU",
        "fmPortID": None,
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "test_data_11",
        "CPUManufacturer": "test_data_12",
        "CPUModel": "test_data_13",
        "fmSwitchID": None,
        "connectedFmSwitchID": None,
        "switchSerialNumber": None,
        "switchManufacturer": None,
        "switchModel": None,
        "fmManagerID": None,
        "oobManagerID": None,
        "portKeys": None,
        "deviceKeys": None,
        "switchPortType": None,
        "fmValid": False,
        "valid": True,
    },
]


@patch(
    "app.common.plugin.plugin_manager._get_plugin",
    return_value=MockPluginPortAndSwitchAndDeviceInfoNoManagerIDs(),
)
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_old_device_info_no_manager_ids(monkeypatch, mocker: MockFixture):
    """No err

    There is no managerId in the existing information
    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)
    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, pre_data_sn)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data_no_managerIds)

    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn30")
    check_output("ptn30")


port_list_diff_fmportid = {
    "data": [
        {
            "id": "1111_change",
            "switchId": "test_data_5",
            "switchPortNumber": None,
            "switchPortType": "DSP",
            "fabricId": None,
            "link": None,
            "deviceType": "PCIe",
            "PCIClassCode": None,
            "PCIeVendorId": "1a4f",
            "PCIeDeviceId": "3c1f",
            "PCIeDeviceSerialNumber": None,
            "CPUManufacturer": None,
            "CPUModel": None,
            "CPUSerialNumber": None,
            "LTSSMState": None,
            "deviceKeys": {},
            "portKeys": {"test": "test_data_6"},
            "capacity": None,
        }
    ]
}


class MockPluginPortAndSwitchAndDeviceInfoDiffFMPortID:
    """set result of get_xxxx_info
    set result of all get_xxxx_info
    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        return convert_port_data(port_list_diff_fmportid)

    def get_switch_info(self):
        """set result of get_switch_info
        set result of all get_switch_info
        """
        return convert_switch_data(switch_list_no_managerIds)

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        return convert_device_data(device_list_no_managerIds)

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch(
    "app.common.plugin.plugin_manager._get_plugin",
    return_value=MockPluginPortAndSwitchAndDeviceInfoDiffFMPortID(),
)
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_old_device_info_diff_fmportid(monkeypatch, mocker: MockFixture):
    """No err
    Existing information, different port information
    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)
    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, pre_data_sn)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)

    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn31")
    check_output("ptn31")


def test__update_db_info_pci_cpu_sw():
    """No err

    update dataframe, serialNumber is same
    """
    base_info = [
        {
            "DeviceID": "new_deveic_id",
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
            "switchManufacturer": None,
            "switchModel": None,
            "fmManagerID": None,
            "oobManagerID": None,
            "portKeys": None,
            "deviceKeys": None,
            "switchPortType": None,
            "fmValid": False,
            "valid": True,
        }
    ]

    new_info = [
        {
            "DeviceID": "new_deveic_id",
            "deviceType": None,
            "fmPortID": None,
            "oobDeviceID": None,
            "PCIeVendorId": None,
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": None,
            "CPUSerialNumber": "22-22",
            "CPUManufacturer": "33-33",
            "CPUModel": "11-11",
            "fmSwitchID": None,
            "connectedFmSwitchID": None,
            "switchSerialNumber": None,
            "switchManufacturer": None,
            "switchModel": None,
            "fmManagerID": None,
            "oobManagerID": None,
            "portKeys": None,
            "deviceKeys": None,
            "switchPortType": None,
            "fmValid": False,
            "valid": True,
        },
        {
            "DeviceID": "new_deveic_id",
            "deviceType": None,
            "fmPortID": None,
            "oobDeviceID": None,
            "PCIeVendorId": None,
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": None,
            "CPUSerialNumber": "22-22",
            "CPUManufacturer": "33-33",
            "CPUModel": "11-11",
            "fmSwitchID": None,
            "connectedFmSwitchID": None,
            "switchSerialNumber": None,
            "switchManufacturer": None,
            "switchModel": None,
            "fmManagerID": None,
            "oobManagerID": None,
            "portKeys": None,
            "deviceKeys": None,
            "switchPortType": None,
            "fmValid": False,
            "valid": True,
        },
        {
            "DeviceID": "new_deveic_id",
            "deviceType": None,
            "fmPortID": None,
            "oobDeviceID": None,
            "PCIeVendorId": None,
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": None,
            "CPUSerialNumber": "22-22",
            "CPUManufacturer": "33-33",
            "CPUModel": "11-11",
            "fmSwitchID": None,
            "connectedFmSwitchID": None,
            "switchSerialNumber": None,
            "switchManufacturer": None,
            "switchModel": None,
            "fmManagerID": None,
            "oobManagerID": None,
            "portKeys": None,
            "deviceKeys": None,
            "switchPortType": None,
            "fmValid": False,
            "valid": True,
        },
    ]
    merge_keys = ["CPUSerialNumber", "CPUManufacturer", "CPUModel"]
    merge_keys_add = []
    info_type = "port_info"
    same_sn_info_d = pd.DataFrame()

    devices_info_json = pd.DataFrame(base_info)
    new_info_d = pd.DataFrame(new_info)

    expected_devices_info_json = devices_info_json.copy()
    expected_moved_devices = new_info_d.copy()
    expected_moved_devices.loc[:, "info_from"] = info_type  # Add info_from column


    (
        devices_info_json,
        moved_devices,
        new_info_devicekeys_info,
        unmerged_no_devicekeys_info,
    ) = dim._update_db_info_pci_cpu_sw(
        devices_info_json, new_info_d, merge_keys, merge_keys_add, "deviceKeys", info_type, same_sn_info_d
    )


    # check expected_devices_info_json == devices_info_json
    diff_devices_info_json = pd.concat([expected_devices_info_json, devices_info_json]).drop_duplicates(keep=False)
    assert diff_devices_info_json.empty
    # check expected_moved_devices == moved_devices
    diff_moved_devices = pd.concat([expected_moved_devices, moved_devices]).drop_duplicates(keep=False)
    assert diff_moved_devices.empty
    # new_info_devicekeys_info is empty
    assert new_info_devicekeys_info.empty
    # unmerged_no_devicekeys_info is empty
    assert unmerged_no_devicekeys_info.empty


def test__update_db_info_new_info_sw_sn_d_no_unmerged():
    """No err
    update dataframe, has no unmerged info
    """
    device_info_list = switch_list_pre["data"]
    manager = "test"
    info_type = "switch_info"
    devices_info_json = pd.DataFrame()
    moved_devices = pd.DataFrame()
    invalid_sn_info_json = pd.DataFrame()
    ret = 0

    dim._update_db_info(device_info_list, manager, info_type, devices_info_json, moved_devices, invalid_sn_info_json)

    ret = 1
    assert ret == 1


def test_update_same_sn_devices_moved_devices_fm_same_sn_not_empty():
    """No err

    update dataframe, has moved_devices
    """
    base_info = [
        {
            "DeviceID": "new_deveic_id",
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
            "switchManufacturer": None,
            "switchModel": None,
            "fmManagerID": None,
            "oobManagerID": None,
            "portKeys": None,
            "deviceKeys": None,
            "switchPortType": None,
            "fmValid": False,
            "valid": True,
        }
    ]
    devices_info = [
        {
            "DeviceID": "new_deveic_id",
            "deviceType": None,
            "fmPortID": {"qemu-01": ["22222"]},
            "oobDeviceID": None,
            "PCIeVendorId": None,
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": None,
            "CPUSerialNumber": "22-22",
            "CPUManufacturer": "33-33",
            "CPUModel": "11-11",
            "fmSwitchID": None,
            "connectedFmSwitchID": None,
            "switchSerialNumber": None,
            "switchManufacturer": None,
            "switchModel": None,
            "fmManagerID": ["qemu-01"],
            "oobManagerID": None,
            "portKeys": None,
            "deviceKeys": None,
            "switchPortType": None,
            "fmValid": True,
            "info_from": "port_info",
            "valid": True,
        },
        {
            "DeviceID": "new_deveic_id2",
            "deviceType": None,
            "fmPortID": {"qemu-01": ["22222"]},
            "oobDeviceID": None,
            "PCIeVendorId": None,
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": None,
            "CPUSerialNumber": "22-22",
            "CPUManufacturer": "33-33",
            "CPUModel": "11-11",
            "fmSwitchID": None,
            "connectedFmSwitchID": None,
            "switchSerialNumber": None,
            "switchManufacturer": None,
            "switchModel": None,
            "fmManagerID": ["qemu-01"],
            "oobManagerID": None,
            "portKeys": None,
            "deviceKeys": None,
            "switchPortType": None,
            "fmValid": True,
            "info_from": "port_info",
            "valid": True,
        },
        {
            "DeviceID": "new_deveic_id3",
            "deviceType": None,
            "fmPortID": {"qemu-03": ["33333"]},
            "oobDeviceID": None,
            "PCIeVendorId": None,
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": None,
            "CPUSerialNumber": "22-22",
            "CPUManufacturer": "33-33",
            "CPUModel": "11-11",
            "fmSwitchID": None,
            "connectedFmSwitchID": None,
            "switchSerialNumber": None,
            "switchManufacturer": None,
            "switchModel": None,
            "fmManagerID": ["qemu-03"],
            "oobManagerID": None,
            "portKeys": None,
            "deviceKeys": None,
            "switchPortType": None,
            "fmValid": True,
            "info_from": "port_info",
            "valid": True,
        },
    ]

    devices_info_json = pd.DataFrame(base_info)
    moved_devices = pd.DataFrame(devices_info)

    ret = 0
    update_same_sn_devices(devices_info_json, moved_devices)
    ret = 1
    assert ret == 1


def test_all_reset():
    """no error
    rest setting file
    """
    all_reset()
    os.remove(_DEVICE_ID_MANAGER_FILE_PATH)
    os.remove(_INVALID_SERIAL_NUMBER_FILE_PATH)

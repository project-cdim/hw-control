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
"""Device manager UT (part 5)

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

import app.common.basic_exceptions as Err
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


class MockPluginGetManagerListMulti:
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
            return fm_manager_list_multi
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
        "CPUManufacturer": "None",
        "CPUModel": "",
        "fmSwitchID": "test_data_5",
        "connectedFmSwitchID": "test_data_5",
        "switchSerialNumber": None,
        #        "switchManufacturer": None, NaN when converting to DataFrame
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


port_list_pre = {
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
            "PCIeVendorId": "000A",
            "PCIeDeviceId": "010B",
            "PCIeDeviceSerialNumber": "abcdef3312345678",
            "CPUManufacturer": None,
            "CPUModel": None,
            "CPUSerialNumber": None,
            "LTSSMState": None,
            "deviceKeys": {},
            "portKeys": {"test": "test"},
            "capacity": None,
        },
        {
            "id": "222",
            "switchId": None,
            "switchPortNumber": None,
            "switchPortType": "USP",
            "fabricId": None,
            "link": None,
            "deviceType": "PCIe",
            "PCIClassCode": None,
            "PCIeVendorId": None,
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": None,
            "CPUSerialNumber": "12345678abcdef33",
            "CPUManufacturer": "test_data_12",
            "CPUModel": "test_data_13",
            "LTSSMState": None,
            "deviceKeys": {"test": "dk11"},
            "portKeys": {"test": "test2"},
            "capacity": None,
        },
    ]
}

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

device_list_pre = [
    {
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "CPU-test_data_11",
        "CPUManufacturer": "test_data_12",
        "CPUModel": "test_data_13",
        "portKeys": None,
        "deviceKeys": {"test": "dk11"},
        "deviceType": "CPU",
        "oobDeviceID": "12345",
    },
    {
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "CPU-test_data_11",
        "CPUManufacturer": "test_data_12",
        "CPUModel": "test_data_13",
        "portKeys": None,
        "deviceKeys": {"test": "dk12"},
        "deviceType": "CPU",
        "oobDeviceID": "12345",
    },
    {
        "PCIeVendorId": None,
        "PCIeDeviceId": "",
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "CPU-test_data_11",
        "CPUManufacturer": "test_data_12",
        "CPUModel": "test_data_13",
        "portKeys": None,
        "deviceKeys": {"test": "dk12"},
        "deviceType": "CPU",
        "oobDeviceID": "12345",
    },
    {
        "PCIeVendorId": "",
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": "CPU-test_data_11",
        "CPUManufacturer": "test_data_12",
        "CPUModel": "test_data_13",
        "portKeys": None,
        "deviceKeys": None,
        "deviceType": "CPU",
        "oobDeviceID": "54321",
    },
]

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


def test__find_different_info_right_col():
    """No err

    find different info

    """
    data = {
        "Name_left": ["Alice", "Bob", "Charlie", "David"],
        "Age_left": ["25", "30", "35", "40"],
        "City_left": ["New York", "Los Angeles", "Chicago", "Houston"],
        "Name_right": ["Alice", "Bob", "Charlie", "David"],
        "Age_right": ["25", "30", "35", "40"],
        "City_right": ["New York", "Los Angeles", "Chicago", "Houston"],
    }
    df = pd.DataFrame(data)
    ret = 0
    # pylint: disable=W0212
    index_info = dim._find_different_info(df)
    # pylint: enable=W0212
    ret = 1
    assert ret == 1
    assert index_info == []


class MockPluginMovedMultiDevices:
    """set result of get_xxxx_info

    set result of all get_xxxx_info

    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        return convert_port_data(port_list_pre)

    def get_switch_info(self):
        """set result of get_switch_info
        set result of all get_switch_info
        """
        return convert_switch_data(switch_list_pre)

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        return convert_device_data(device_list_pre)

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch("app.common.utils.plugin_manager.get_plugin", return_value=MockPluginMovedMultiDevices())
def test_update_same_sn_devices_multi_devices(monkeypatch):
    """No err

    update dataframe, multi devices

    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, pre_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)

    devices_info_json = pd.DataFrame()
    moved_devices_info = [
        {
            "DeviceID": "11111111",
            "deviceType": None,
            "fmPortID": {"qemu-01": ["11111"], "qemu-03": ["111-2"]},
            "oobDeviceID": None,
            "PCIeVendorId": "test_data_2",
            "PCIeDeviceId": "test_data_3",
            "PCIeDeviceSerialNumber": "test_data_4",
            "CPUSerialNumber": None,
            "CPUManufacturer": None,
            "CPUModel": None,
            "fmSwitchID": None,
            "connectedFmSwitchID": {"qemu-01": ["48338cae491002d7"], "qemu-03": ["48338cae491002a3"]},
            "switchSerialNumber": None,
            "switchManufacturer": None,
            "switchModel": None,
            "fmManagerID": ["qemu-01", "qemu-03"],
            "oobManagerID": ["1"],
            "portKeys": None,
            "deviceKeys": None,
            "info_from": "port_info",
            "upDown": None,
            "valid": True,
        },
        {
            "DeviceID": "222222222",
            "deviceType": None,
            "fmPortID": {"qemu-02": ["2222"]},
            "oobDeviceID": None,
            "PCIeVendorId": None,
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": None,
            "CPUSerialNumber": None,
            "CPUManufacturer": None,
            "CPUModel": None,
            "fmSwitchID": "test_data_7",
            "connectedFmSwitchID": {"qemu-02": ["48338cae491002d7"]},
            "switchManufacturer": "test_data_8",
            "switchModel": "test_data_9",
            "switchSerialNumber": "test_data_10",
            "fmManagerID": ["qemu-02"],
            "oobManagerID": ["12"],
            "portKeys": None,
            "deviceKeys": None,
            "info_from": "switch_info",
            "upDown": None,
            "valid": True,
        },
        {
            "DeviceID": "333333333333",
            "deviceType": "CPU",
            "fmPortID": {"qemu-03": ["33333-2"]},
            "oobDeviceID": "test_oob_id",
            "PCIeVendorId": None,
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": None,
            "CPUSerialNumber": "test_data_11",
            "CPUManufacturer": "test_data_12",
            "CPUModel": "test_data_13",
            "fmSwitchID": None,
            "connectedFmSwitchID": {"qemu-03": ["48338cae491002d7"]},
            "switchSerialNumber": None,
            "switchManufacturer": None,
            "switchModel": None,
            "fmManagerID": ["qemu-03"],
            "oobManagerID": ["oob_manager_id"],
            "portKeys": None,
            "deviceKeys": None,
            "info_from": "port_info",
            "upDown": None,
            "valid": True,
        },
    ]
    moved_devices = pd.DataFrame(moved_devices_info)
    devices_info_json = moved_devices.copy()

    ret = 0
    update_same_sn_devices(devices_info_json, moved_devices)
    ret = 1
    assert ret == 1


class MockPluginMovedMultiDevicesInvalidInfo:
    """set result of get_xxxx_info

    set result of all get_xxxx_info

    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        return convert_port_data(port_list_pre)

    def get_switch_info(self):
        """set result of get_switch_info
        set result of all get_switch_info
        """
        return convert_switch_data(switch_list_pre)

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        return convert_device_data(device_list_pre)

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch(
    "app.common.utils.plugin_manager.get_plugin",
    return_value=MockPluginMovedMultiDevicesInvalidInfo(),
)
def test_update_same_sn_devices_multi_devices_invalid_info(monkeypatch):
    """No err

    update dataframe, multi invalid devices

    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, pre_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)

    devices_info_json = pd.DataFrame()
    moved_devices_info = [
        {
            "DeviceID": None,
            "deviceType": None,
            "fmPortID": {"fm_manager_id": ["111"]},
            "oobDeviceID": None,
            "PCIeVendorId": "test_data_2",
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": "test_data_4",
            "CPUSerialNumber": None,
            "CPUManufacturer": None,
            "CPUModel": None,
            "fmSwitchID": None,
            "connectedFmSwitchID": {"fm_manager_id": ["48338cae491002d7"]},
            "switchSerialNumber": None,
            "switchManufacturer": None,
            "switchModel": None,
            "fmManagerID": ["fm_manager_id"],
            "oobManagerID": None,
            "portKeys": None,
            "deviceKeys": None,
            "info_from": "port_info",
            "upDown": None,
            "valid": True,
        },
        {
            "DeviceID": None,
            "deviceType": None,
            "fmPortID": {"fm_manager_id": ["222"]},
            "oobDeviceID": None,
            "PCIeVendorId": None,
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": None,
            "CPUSerialNumber": None,
            "CPUManufacturer": None,
            "CPUModel": None,
            "fmSwitchID": "test_data_7",
            "connectedFmSwitchID": {"fm_manager_id": ["48338cae491002d7"]},
            "switchManufacturer": None,
            "switchModel": "test_data_9",
            "switchSerialNumber": "test_data_10",
            "fmManagerID": ["fm_manager_id"],
            "oobManagerID": None,
            "portKeys": None,
            "deviceKeys": None,
            "info_from": "port_info",
            "upDown": None,
            "valid": True,
        },
        {
            "DeviceID": None,
            "deviceType": "CPU",
            "fmPortID": None,
            "oobDeviceID": "test_oob_id",
            "PCIeVendorId": None,
            "PCIeDeviceId": "",
            "PCIeDeviceSerialNumber": None,
            "CPUSerialNumber": None,
            "CPUManufacturer": "test_data_12",
            "CPUModel": "test_data_13",
            "fmSwitchID": None,
            "connectedFmSwitchID": {"fm_manager_id": ["48338cae491002d7"]},
            "switchSerialNumber": "",
            "switchManufacturer": None,
            "switchModel": None,
            "fmManagerID": None,
            "oobManagerID": "oob_manager_id",
            "portKeys": None,
            "deviceKeys": None,
            "info_from": "device_info",
            "upDown": None,
            "valid": True,
        },
    ]

    moved_devices = pd.DataFrame(moved_devices_info)
    devices_info_json = moved_devices.copy()
    ret = 0
    update_same_sn_devices(devices_info_json, moved_devices)
    ret = 1
    assert ret == 1


def test_log_invalid_device_info_switch(mocker: MockFixture, caplog: LogCaptureFixture):
    """error

    pandas merge error

    """
    mocker.patch.object(pd, "merge", side_effect=custom_side_effect_pd_merge)
    info_type = "switch_info"
    device_info = pd.DataFrame()

    caplog.clear()
    with caplog.at_level(logging.INFO, logger=dim.__name__):
        dim._log_invalid_device_info(info_type, device_info)  # pylint: disable=W0212

    # check log
    assert len(caplog.records) == 1

    # Inspection: Check the invalid switch log.
    invalid_switch_log = caplog.records[0]
    assert invalid_switch_log.levelname == "INFO"
    assert invalid_switch_log.getMessage() == "device_info (FM Switch ID: None) is invalid."


port_list_pre_err = {
    "data": [
        {
            "id": "111",
            "switchId": None,
            "switchPortNumber": None,
            "switchPortType": "DSP",
            "link": None,
            "deviceType": "PCI",
            "PCIClassCode": None,
            "PCIeVendorId": None,
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": None,
            "CPUManufacturer": None,
            "CPUModel": None,
            "CPUSerialNumber": None,
            "LTSSMState": None,
            "deviceKeys": None,
            "portKeys": "test",
        },
        {
            "id": "222",
            "switchId": None,
            "switchPortNumber": "",
            "switchPortType": "USP",
            "link": None,
            "deviceType": "CPU",
            "PCIClassCode": None,
            "PCIeVendorId": None,
            "PCIeDeviceId": "",
            "PCIeDeviceSerialNumber": None,
            "CPUManufacturer": None,
            "CPUModel": None,
            "CPUSerialNumber": None,
            "LTSSMState": None,
            "deviceKeys": None,
            "portKeys": "test",
        },
    ]
}


def custom_side_effect_pd_merge(*args, **kwargs):
    """set pandas error

    set pandas error

    """
    raise TypeError


port_list_def_nosn = {
    "data": [
        {
            "id": "test_id_1",
            "switchId": "test_si_2",
            "switchPortNumber": None,
            "switchPortType": "USP",
            "fabricId": None,
            "link": [],
            "deviceType": "PCIe",
            "PCIClassCode": None,
            "PCIeVendorId": None,
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": None,
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

switch_list_def_nosn = {
    "data": [
        {
            "switchId": "test_si_1",
            "switchManufacturer": "",
            "switchModel": None,
            "switchSerialNumber": "",
            "link": None,
        }
    ]
}

device_list_def_nosn = [
    {
        "PCIeVendorId": "",
        "PCIeDeviceId": "",
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": "",
        "CPUModel": None,
        "portKeys": {"test": "test_pk_2"},
        "deviceKeys": {"test": "test_dk_2"},
        "deviceType": "CPU",
        "oobDeviceID": "test",
    }
]


class MockPluginPortAndSwitchAndDeviceInfo4:
    """set result of get_xxxx_info

    set result of all get_xxxx_info

    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        return convert_port_data(port_list_def_nosn)

    def get_switch_info(self):
        """set result of get_switch_info
        set result of all get_switch_info
        """
        return convert_switch_data(switch_list_def_nosn)

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        return convert_device_data(device_list_def_nosn)

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch(
    "app.common.utils.plugin_manager.get_plugin",
    return_value=MockPluginPortAndSwitchAndDeviceInfo4(),
)
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_new_data_not_bysn(monkeypatch, mocker: MockFixture):
    """No err

    New registration without serial number

    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn16")
    check_output("ptn16")


port_list_def_dk = {
    "data": [
        {
            "id": "test_id_2",
            "switchId": "test_si_2",
            "switchPortNumber": None,
            "switchPortType": "USP",
            "fabricId": None,
            "link": None,
            "deviceType": "PCIe",
            "PCIClassCode": None,
            "PCIeVendorId": None,
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": None,
            "CPUManufacturer": None,
            "CPUModel": None,
            "CPUSerialNumber": None,
            "LTSSMState": None,
            "deviceKeys": {"test": "test_dk_1"},
            "portKeys": {"test": "test_pk_1"},
            "capacity": None,
        }
    ]
}

switch_list_def_dk = {
    "data": [
        {
            "switchId": "test_si_1",
            "switchManufacturer": "",
            "switchModel": "",
            "switchSerialNumber": None,
            "link": None,
        }
    ]
}

device_list_def_dk = [
    {
        "PCIeVendorId": None,
        "PCIeDeviceId": "",
        "PCIeDeviceSerialNumber": "",
        "CPUSerialNumber": None,
        "CPUManufacturer": "",
        "CPUModel": None,
        "portKeys": {"test": "test_pk_2"},
        "deviceKeys": {"test": "test_dk_2"},
        "deviceType": "CPU",
        "oobDeviceID": "",
    }
]


class MockPluginPortAndSwitchAndDeviceInfo5:
    """set result of get_xxxx_info
    set result of all get_xxxx_info
    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        return convert_port_data(port_list_def_dk)

    def get_switch_info(self):
        """set result of get_switch_info
        set result of all get_switch_info
        """
        return convert_switch_data(switch_list_def_dk)

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        return convert_device_data(device_list_def_dk)

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch(
    "app.common.utils.plugin_manager.get_plugin",
    return_value=MockPluginPortAndSwitchAndDeviceInfo5(),
)
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_new_data_bydk(monkeypatch, mocker: MockFixture):
    """No err

    New registration with deviceKeys

    """

    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn17")
    check_output("ptn17")


@patch("app.common.utils.plugin_manager.get_plugin", return_value=MockPluginPortAndSwitchAndDeviceInfo())
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_merge_err(self, monkeypatch: MonkeyPatch, mocker: MockFixture, caplog: LogCaptureFixture):
    """error

    pandas merge error

    """
    self.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, pre_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)

    mocker.patch.object(pd, "merge", side_effect=custom_side_effect_pd_merge)

    ret = 0
    try:
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=dim.__name__):
            assign_device_id()
    except Err.DeviceIDFileIncorrectHWControlError:
        ret = 1
    assert ret == 1

    # check log
    assert len(caplog.records) == 1

    # Inspection: Check the device assign error log.
    device_assign_error_log = caplog.records[0]
    assert device_assign_error_log.levelname == "ERROR"
    assert device_assign_error_log.getMessage() == "Failed to assign device id by FM info."


def custom_side_effect(*args, **kwargs):
    """set error

    set error

    """
    raise FileNotFoundError


def test_assign_device_file_replace_err(mocker: MockFixture, caplog: LogCaptureFixture):
    """error

    file replace error

    """

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, pre_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)

    ret = 0
    mocker.patch.object(os, "replace", side_effect=custom_side_effect)
    try:
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=dim.__name__):
            assign_device_id()
    except Err.DeviceIDFileNotFoundHWControlError:
        ret = 1

    assert ret == 1

    # check log
    assert len(caplog.records) == 1

    # Inspection: Check the file error log.
    file_error_log = caplog.records[0]
    assert file_error_log.levelname == "ERROR"
    assert file_error_log.getMessage() == "Failed to update Device ID Management File."


@patch("app.common.utils.plugin_manager.get_plugin", return_value=MockPluginPortAndSwitchAndDeviceInfo())
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_open_err_1(monkeypatch: MonkeyPatch, mocker: MockFixture, caplog: LogCaptureFixture):
    """error

    file open error

    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    ret = 0
    reset_setting_file_not_json(_INVALID_SERIAL_NUMBER_FILE_PATH, "wwwwwwww")
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)

    try:
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=dim.__name__):
            assign_device_id()
    except Err.InvalidSerialNumberConfigFileIncorrectHWControlError:
        ret = 1

    assert ret == 1

    # check log
    assert len(caplog.records) == 1

    # Inspection: Check the invalid serial error log.
    invalid_serial_error_log = caplog.records[0]
    assert invalid_serial_error_log.levelname == "ERROR"
    assert invalid_serial_error_log.getMessage() == "The invalid serial number file is incorrect."


def test_assign_device_open_err_2(caplog: LogCaptureFixture):
    """error

    file open error

    """
    ret = 0
    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file_not_json(_DEVICE_ID_MANAGER_FILE_PATH, "wwwwwwww")

    try:
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=dim.__name__):
            assign_device_id()
    except Err.DeviceIDFileIncorrectHWControlError:
        ret = 1

    assert ret == 1

    # check log
    assert len(caplog.records) == 1

    # Inspection: Check the file incorrect error log.
    file_incorrect_error_log = caplog.records[0]
    assert file_incorrect_error_log.levelname == "ERROR"
    assert file_incorrect_error_log.getMessage() == "The Device ID Management File is incorrect."


def all_reset():
    """no error

    This is not test case.
    reset all information files.

    """
    try:
        os.rename(_INVALID_SERIAL_NUMBER_FILE_PATH_bak, _INVALID_SERIAL_NUMBER_FILE_PATH)
        os.rename(_DEVICE_ID_MANAGER_FILE_PATH_bak, _DEVICE_ID_MANAGER_FILE_PATH)
    except Exception:  # pylint: disable=W0718
        pass
    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, reset_data)


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
    "app.common.utils.plugin_manager.get_plugin",
    return_value=MockPluginPortAndSwitchAndDeviceInvalidInfo(),
)
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_disable_all_info_file_not_found(monkeypatch: MonkeyPatch, mocker: MockFixture):
    """error

    file not found

    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    os.rename(_DEVICE_ID_MANAGER_FILE_PATH, _DEVICE_ID_MANAGER_FILE_PATH_bak)
    assign_device_id()
    assert check_data_type()
    mv_output("ptn35")
    check_output("ptn35")
    all_reset()


class MockPluginPortAndSwitchAndDeviceInfo2:
    """set result of get_xxxx_info

    set result of all get_xxxx_info

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


@patch(
    "app.common.utils.plugin_manager.get_plugin",
    return_value=MockPluginPortAndSwitchAndDeviceInfo2(),
)
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_new_invalid_file_not_found(monkeypatch: MonkeyPatch, mocker: MockFixture):
    """error

    invalid file not found

    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, pre_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)

    os.rename(_INVALID_SERIAL_NUMBER_FILE_PATH, _INVALID_SERIAL_NUMBER_FILE_PATH_bak)
    assign_device_id()
    assert check_data_type()
    mv_output("ptn36")
    check_output("ptn36")
    all_reset()


def test_all_reset():
    """no error
    rest setting file
    """
    all_reset()
    os.remove(_DEVICE_ID_MANAGER_FILE_PATH)
    os.remove(_INVALID_SERIAL_NUMBER_FILE_PATH)

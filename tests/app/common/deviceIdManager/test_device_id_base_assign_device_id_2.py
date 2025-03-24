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
"""Device manager UT (part 2)

Device manager UT.
Note: Currently,
data accuracy is not automated and must be checked manually.

"""
import os
import json
from typing import Dict
from typing import List
import shutil
from collections import Counter

from unittest.mock import patch
import pytest
from pytest_mock import MockFixture

from app.common.deviceIdManager.device_id_base import assign_device_id
from app.common.deviceIdManager import device_id_manager as dim
from app.common.utils.fm_plugin_base import FmPortData, FmSwitchData
from app.common.utils.oob_plugin_base import OOBDeviceListItem

import pandas as pd

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


# for checking log
DIM_MODULE_NAME = "app.common.deviceIdManager.device_id_manager"
DIM_BASE_MODULE_NAME = "app.common.deviceIdManager.device_id_base"
CONSTANT_REQUEST_ID = "test_request_id"


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


def convert_port_data(dict_data: dict) -> dict[str, List[FmPortData]]:
    """
    change list type to FmPortData.
    """
    return {"data": [FmPortData(**port_data) for port_data in dict_data["data"]]}


def convert_switch_data(dict_data: dict) -> dict[str, List[FmSwitchData]]:
    """
    change list type to FmSwitchData.
    """
    return {"data": [FmSwitchData(**switch_data) for switch_data in dict_data["data"]]}


def convert_device_data(list_data: list) -> List[OOBDeviceListItem]:
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


def __is_same_data(e_data: Dict[str, str], new_data: Dict[str, str], keys: list[str], inx: int) -> bool:
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
    with open(outf, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            new_data = data
            with open(expectf, "r", encoding="utf-8") as e_f:
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

"""
pre data in file
"""

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


class MockPluginPortAndSwitchAndDeviceInfForBySn:
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
    "app.common.deviceIdManager.device_id_manager.get_plugin",
    return_value=MockPluginPortAndSwitchAndDeviceInfForBySn(),
)
@patch(
    "app.common.deviceIdManager.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_use_old_data_by_sn(monkeypatch, mocker: MockFixture):
    """No err

    ID reuse by serial number

    """
    monkeypatch.setattr("app.common.deviceIdManager.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.deviceIdManager.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn18")
    check_output("ptn18")


port_list_pre_up = {
    "data": [
        {
            "id": "123456",
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
            "CPUManufacturer": "",
            "CPUModel": None,
            "CPUSerialNumber": None,
            "LTSSMState": None,
            "deviceKeys": {"test": "test_data_2"},
            "portKeys": {"test": "test"},
            "capacity": None,
        }
    ]
}


class MockPluginPortAndSwitchAndDeviceInfo6:
    """set result of get_xxxx_info

    set result of all get_xxxx_info

    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        return convert_port_data(port_list_pre_up)

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
    "app.common.deviceIdManager.device_id_manager.get_plugin",
    return_value=MockPluginPortAndSwitchAndDeviceInfo6(),
)
@patch(
    "app.common.deviceIdManager.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_use_old_data_by_sn2(monkeypatch, mocker: MockFixture):
    """No err

    ID reuse by serial number

    """
    monkeypatch.setattr("app.common.deviceIdManager.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.deviceIdManager.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn19")
    check_output("ptn19")


class MockPluginPortAndSwitchAndDeviceInfo7:
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
    "app.common.deviceIdManager.device_id_manager.get_plugin",
    return_value=MockPluginPortAndSwitchAndDeviceInfo7(),
)
@patch(
    "app.common.deviceIdManager.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_use_old_data_by_sn_no_manager_ids(monkeypatch, mocker: MockFixture):
    """No err

    ID reuse by serial number, no managerId

    """
    monkeypatch.setattr("app.common.deviceIdManager.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.deviceIdManager.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data_no_managerIds)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn20")
    check_output("ptn20")


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


class MockPluginPortAndSwitchAndDeviceInfo8:
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


@patch(
    "app.common.deviceIdManager.device_id_manager.get_plugin",
    return_value=MockPluginPortAndSwitchAndDeviceInfo8(),
)
@patch(
    "app.common.deviceIdManager.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_use_old_data_not_by_sn(monkeypatch, mocker: MockFixture):
    """No err

    ID reuse by others than serial number

    """
    monkeypatch.setattr("app.common.deviceIdManager.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.deviceIdManager.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, pre_data_sn)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn21")
    check_output("ptn21")


port_list_def_disable_old = {
    "data": [
        {
            "id": "test_id_2",
            "switchId": "test_data_5",
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
            "deviceKeys": {},
            "portKeys": {"test": "test_data_6"},
            "capacity": None,
        }
    ]
}

switch_list_def_disable_old = {
    "data": [
        {
            "switchId": "test_data_5",
            "switchManufacturer": "",
            "switchModel": "test_data_11",
            "switchSerialNumber": None,
            "link": None,
        }
    ]
}

device_list_def_disable_old = [
    {
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": "",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "portKeys": {"test": "test_data_6"},
        "deviceKeys": None,
        "deviceType": "CPU",
        "oobDeviceID": "test_oob_id_2",
    }
]


class MockPluginPortAndSwitchAndDeviceInfodisableOld:
    """set result of get_xxxx_info

    set result of all get_xxxx_info

    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        return convert_port_data(port_list_def_disable_old)

    def get_switch_info(self):
        """set result of get_switch_info
        set result of all get_switch_info
        """
        return convert_switch_data(switch_list_def_disable_old)

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        return convert_device_data(device_list_def_disable_old)

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch(
    "app.common.deviceIdManager.device_id_manager.get_plugin",
    return_value=MockPluginPortAndSwitchAndDeviceInfodisableOld(),
)
@patch(
    "app.common.deviceIdManager.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_new_id_and_disable_old(monkeypatch, mocker: MockFixture):
    """No err

    Both new registration and ID reuse are available

    """
    monkeypatch.setattr("app.common.deviceIdManager.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.deviceIdManager.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn22")
    check_output("ptn22")


class MockPluginPortAndSwitchAndDeviceInfodisableOld2:
    """set result of get_xxxx_info

    set result of all get_xxxx_info

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
        return convert_device_data(device_list_def_disable_old)

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch(
    "app.common.deviceIdManager.device_id_manager.get_plugin",
    return_value=MockPluginPortAndSwitchAndDeviceInfodisableOld2(),
)
@patch(
    "app.common.deviceIdManager.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_new_id_and_disable_old2(monkeypatch, mocker: MockFixture):
    """No err

    Both new registration and ID reuse are available

    """
    monkeypatch.setattr("app.common.deviceIdManager.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.deviceIdManager.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn23")
    check_output("ptn23")


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


class MockPluginPortAndSwitchAndDeviceInfodisableOld3:
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
        return convert_switch_data(switch_list_def_disable_old)

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
    "app.common.deviceIdManager.device_id_manager.get_plugin",
    return_value=MockPluginPortAndSwitchAndDeviceInfodisableOld3(),
)
@patch(
    "app.common.deviceIdManager.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_new_id_and_disable_old3(monkeypatch, mocker: MockFixture):
    """No err

    Both new registration and ID reuse are available

    """
    monkeypatch.setattr("app.common.deviceIdManager.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.deviceIdManager.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn24")
    check_output("ptn24")


port_list_def_disable_same_fm = {
    "data": [
        {
            "id": "333333333",
            "switchId": "test_data_5_2",
            "switchPortNumber": None,
            "switchPortType": "USP",
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
            "portKeys": {"test": "test_data_11"},
            "capacity": None,
        }
    ]
}


class MockPluginPortAndSwitchAndDeviceInfodisableSameFm:
    """set result of get_xxxx_info

    set result of all get_xxxx_info

    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        return port_list_def_disable_same_fm

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
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch(
    "app.common.deviceIdManager.device_id_manager.get_plugin",
    return_value=MockPluginPortAndSwitchAndDeviceInfodisableSameFm(),
)
@patch(
    "app.common.deviceIdManager.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_new_id_and_disable_same_fm(monkeypatch, mocker: MockFixture):
    """No err

    New registration, invalidation of same port

    """
    monkeypatch.setattr("app.common.deviceIdManager.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.deviceIdManager.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn25")
    check_output("ptn25")


port_list_pre_same_porkets = {
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
            "PCIeDeviceId": "011B",
            "PCIeDeviceSerialNumber": "abcdef3312345679",
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
        {
            "id": "333",
            "switchId": "/aaaa/bbb/ccccc",
            "switchPortNumber": None,
            "switchPortType": "DSP",
            "fabricId": None,
            "link": None,
            "deviceType": "PCIe",
            "PCIClassCode": None,
            "PCIeVendorId": "000A",
            "PCIeDeviceId": "010B",
            "PCIeDeviceSerialNumber": "abcdef33123456aa",
            "CPUManufacturer": None,
            "CPUModel": None,
            "CPUSerialNumber": None,
            "LTSSMState": None,
            "deviceKeys": {},
            "portKeys": {"test": "test"},
            "capacity": None,
        },
        {
            "id": "4444",
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
            "CPUSerialNumber": "12345678abcdef34",
            "CPUManufacturer": "test_data_13",
            "CPUModel": "test_data_14",
            "LTSSMState": None,
            "deviceKeys": {},
            "portKeys": {"test": "test"},
            "capacity": None,
        },
    ]
}


class MockPluginPortAndSwitchAndDeviceInfSamePortkeys:
    """set result of get_xxxx_info

    set result of all get_xxxx_info

    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        return convert_port_data(port_list_pre_same_porkets)

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
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch(
    "app.common.deviceIdManager.device_id_manager.get_plugin",
    return_value=MockPluginPortAndSwitchAndDeviceInfSamePortkeys(),
)
@patch(
    "app.common.deviceIdManager.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
@pytest.mark.usefixtures("set_dummy_constant_request_id")
def test_assign_device_id_same_portkeys(monkeypatch, mocker: MockFixture, caplog):
    """No err

    Invalid data with duplicate ['portKeys'] within the same plugin
    have been removed.

    """
    monkeypatch.setattr("app.common.deviceIdManager.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.deviceIdManager.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)
    caplog.clear()  # clear log
    assign_device_id()

    assert check_data_type()
    mv_output("ptn37")
    check_output("ptn37")
    # check log
    assert len(caplog.records) == 2
    plugin_call_log_message = json.loads(caplog.records[0].getMessage())
    assert caplog.records[0].levelname == "INFO"
    assert plugin_call_log_message["message"]["request_id"] == CONSTANT_REQUEST_ID
    assert (
        plugin_call_log_message["message"]["detail"] == f"[{DIM_MODULE_NAME}] Invalid data with duplicate "
        f"{str(['portKeys'])} within the same plugin have been removed."
    )
    plugin_call_log_message = json.loads(caplog.records[1].getMessage())
    assert caplog.records[1].levelname == "WARNING"
    assert plugin_call_log_message["message"]["request_id"] == CONSTANT_REQUEST_ID
    assert plugin_call_log_message["message"]["trace_back"] is not None


device_list_def_same_devicekeys = [
    {
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": "12345679765423",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "portKeys": None,
        "deviceKeys": {"test": "same_device_keys_1"},
        "deviceType": "CPU",
        "oobDeviceID": "test_oob_id_same_device_keys_1",
    },
    {
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": "12345679762222",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "portKeys": None,
        "deviceKeys": {"test": "same_device_keys_1"},
        "deviceType": "CPU",
        "oobDeviceID": "test_oob_id_same_device_keys_2",
    },
    {
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": "12345679763333",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "portKeys": None,
        "deviceKeys": {"test": "same_device_keys_1"},
        "deviceType": "CPU",
        "oobDeviceID": "test_oob_id_same_device_keys_3",
    },
]


class MockPluginPortAndSwitchAndDeviceInfSameDeviceKeys:
    """set result of get_xxxx_info

    set result of all get_xxxx_info

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
        return convert_device_data(device_list_def_same_devicekeys)

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch(
    "app.common.deviceIdManager.device_id_manager.get_plugin",
    return_value=MockPluginPortAndSwitchAndDeviceInfSameDeviceKeys(),
)
@patch(
    "app.common.deviceIdManager.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
@pytest.mark.usefixtures("set_dummy_constant_request_id")
def test_assign_device_id_same_devicekeys(monkeypatch, mocker: MockFixture, caplog):
    """No err

    Invalid data with duplicate ['deviceKeys'] within the same plugin
    have been removed.

    """
    monkeypatch.setattr("app.common.deviceIdManager.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.deviceIdManager.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)
    caplog.clear()  # clear log
    assign_device_id()

    assert check_data_type()
    mv_output("ptn37")
    check_output("ptn37")
    # check log
    assert len(caplog.records) == 2
    plugin_call_log_message = json.loads(caplog.records[0].getMessage())
    assert caplog.records[0].levelname == "INFO"
    assert plugin_call_log_message["message"]["request_id"] == CONSTANT_REQUEST_ID
    assert (
        plugin_call_log_message["message"]["detail"] == f"[{DIM_MODULE_NAME}] Invalid data with duplicate "
        f"{str(['deviceKeys'])} within the same plugin have been removed."
    )
    plugin_call_log_message = json.loads(caplog.records[1].getMessage())
    assert caplog.records[1].levelname == "WARNING"
    assert plugin_call_log_message["message"]["request_id"] == CONSTANT_REQUEST_ID
    assert plugin_call_log_message["message"]["trace_back"] is not None


def test_update_db_info_devicekeys_empty_new_data(caplog):
    """No err

    new_info_d is empty.

    """
    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)
    caplog.clear()  # clear log
    devices_info_json = pd.DataFrame()
    new_info_d = pd.DataFrame()
    merge_keys = "deviceKeys"
    # pylint: disable=W0212
    devices_info, unmerged = dim._update_db_info_devicekeys(devices_info_json, new_info_d, merge_keys)
    # pylint: enable=W0212
    assert devices_info.empty
    assert unmerged.empty


def test_update_db_info_portkkeys_empty_new_data(caplog):
    """No err

    new_info_d is empty.

    """
    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)
    caplog.clear()  # clear log
    devices_info_json = pd.DataFrame()
    new_info_d = pd.DataFrame()
    merge_keys = "portKeys"
    merge_keys_add = []
    # pylint: disable=W0212
    devices_info, unmerged = dim._update_db_info_fmswid_portkeys(
        devices_info_json, new_info_d, merge_keys, merge_keys_add
    )
    # pylint: enable=W0212
    assert devices_info.empty
    assert unmerged.empty
    all_reset()


def test_all_reset():
    """no error
    rest setting file
    """
    all_reset()
    os.remove(_DEVICE_ID_MANAGER_FILE_PATH)
    os.remove(_INVALID_SERIAL_NUMBER_FILE_PATH)

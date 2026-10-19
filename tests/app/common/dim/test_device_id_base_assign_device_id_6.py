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


"""Device manager UT (part 5)

Device manager UT.
Note: Currently,
data accuracy is not automated and must be checked manually.

"""

import logging
import os
import json
import shutil
import itertools
from collections import Counter

import pytest
from pytest import LogCaptureFixture, MonkeyPatch
from pytest_mock import MockFixture

import pandas as pd

from app.common.dim.device_id_base import assign_device_id
from app.common.dim import device_id_manager as dim
from app.common.dim import device_id_base as dib
from app.common.utils.fm_plugin_base import FMPortData, FMSwitchData
from app.common.utils.oob_plugin_base import OOBDeviceListItem

reset_data = []

fm_manager_list = ["qemu-01"]

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


def reset_setting_file(file_path: str, data):
    """reset the setting file.

    Reset the setting file device_id_info.json.

    """
    with open(file_path, "w", encoding="utf-8") as f:
        f.seek(0)
        json.dump(data, f, indent=4)


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


class MockDoAssignDeviceID4CheckInvalidSNInfoJSON:
    """set result of

    set result of all get_xxxx_info

    """

    wrong_invalid_sn_info = [
        {
            "PCIeVendorId": "None",
            "PCIeDeviceId": "NaN",
            "PCIeDeviceSerialNumber": "nan",
            "CPUManufacturer": "p-CPUManufacturer-14",
            "CPUModel": "p-CPUModel-14",
            "CPUSerialNumber": "",
            "switchSerialNumber": "None",
            "switchManufacturer": "NaN",
            "switchModel": "nan",
        },
        {
            "PCIeVendorId": "",
            "PCIeDeviceId": "None",
            "PCIeDeviceSerialNumber": "NaN",
            "CPUSerialNumber": "nan",
            "CPUManufacturer": "",
            "CPUModel": "None",
            "switchManufacturer": "s-switchManufacturer-14",
            "switchModel": "s-switchModel-14",
            "switchSerialNumber": "NaN",
        },
        {
            "PCIeVendorId": "d-PCIeVendorId-14",
            "PCIeDeviceId": "d-PCIeDeviceId-14",
            "PCIeDeviceSerialNumber": "nan",
            "CPUSerialNumber": "",
            "CPUManufacturer": "None",
            "CPUModel": "NaN",
            "switchSerialNumber": "nan",
            "switchManufacturer": "",
            "switchModel": "None",
        },
    ]

    def check_assign_fm_device_id(
        self,
        devices_info_json: pd.DataFrame,
        moved_devices: pd.DataFrame,
        invalid_sn_info_json: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """check invalid_sn_info_json and return dummy dataframe"""
        invalid_sn_info_json_values = list(itertools.chain.from_iterable(invalid_sn_info_json.values.tolist()))
        assert ("NaN" in invalid_sn_info_json_values) is False
        assert ("nan" in invalid_sn_info_json_values) is False
        assert ("None" in invalid_sn_info_json_values) is False
        assert ("" in invalid_sn_info_json_values) is False

        return dim.assign_fm_device_id(devices_info_json, moved_devices, invalid_sn_info_json)

    def check_assign_oob_device_id(
        self,
        devices_info_json: pd.DataFrame,
        moved_devices: pd.DataFrame,
        invalid_sn_info_json: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """check invalid_sn_info_json and return dummy dataframe"""
        invalid_sn_info_json_values = list(itertools.chain.from_iterable(invalid_sn_info_json.values.tolist()))
        assert ("NaN" in invalid_sn_info_json_values) is False
        assert ("nan" in invalid_sn_info_json_values) is False
        assert ("None" in invalid_sn_info_json_values) is False
        assert ("" in invalid_sn_info_json_values) is False

        return dim.assign_oob_device_id(devices_info_json, moved_devices, invalid_sn_info_json)


def test_check_invalid_sn_info_json(mocker: MockFixture):
    """no error

    Check if the value read from the invalid serial number setting file,
    which indicates a None string, has been converted to a None object.
    """
    mocker.patch.object(dim, "get_fm_plugin", return_value=MockPluginPortAndSwitchAndDeviceInfo4())
    mocker.patch.object(dim, "get_oob_plugin", return_value=MockPluginPortAndSwitchAndDeviceInfo4())
    mocker.patch.object(dim, "get_manager_list", side_effect=MockPluginGetManagerList().get_manager_list)
    mocker.patch.object(
        dib, "assign_fm_device_id", side_effect=MockDoAssignDeviceID4CheckInvalidSNInfoJSON().check_assign_fm_device_id
    )
    mocker.patch.object(
        dib,
        "assign_oob_device_id",
        side_effect=MockDoAssignDeviceID4CheckInvalidSNInfoJSON().check_assign_oob_device_id,
    )

    reset_setting_file(
        _INVALID_SERIAL_NUMBER_FILE_PATH, MockDoAssignDeviceID4CheckInvalidSNInfoJSON().wrong_invalid_sn_info
    )
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    mv_output("ptn38")
    check_output("ptn38")


check_base_json_info = [
    {
        "DeviceID": "new_deveic_id",
        "deviceType": "storage",
        "fmPortID": {"qemu-001": ["1-1"]},
        "oobDeviceID": "ODI-2501",
        "PCIeVendorId": "22",
        "PCIeDeviceId": "333",
        "PCIeDeviceSerialNumber": "4444",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": {"qemu-001": ["5-5-5-5-5"]},
        "switchSerialNumber": None,
        "switchModel": None,
        "switchManufacturer": None,
        "fmManagerID": ["qemu-001"],
        "oobManagerID": ["BMC-1"],
        "portKeys": "{'port': '0123'}",
        "deviceKeys": "{'SimulatedDeviceID': '666666'}",
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": False,
    }
]

check_new_info_sn_none = [
    {
        "DeviceID": "new_deveic_id",
        "deviceType": "storage",
        "fmPortID": {"qemu-001": ["1-1"]},
        "oobDeviceID": "ODI-2501",
        "PCIeVendorId": "22",
        "PCIeDeviceId": "333",
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": {"qemu-001": ["5-5-5-5-5"]},
        "switchSerialNumber": None,
        "switchModel": None,
        "switchManufacturer": None,
        "fmManagerID": ["qemu-001"],
        "oobManagerID": ["BMC-1"],
        "portKeys": "{'port': '0123'}",
        "deviceKeys": "{'SimulatedDeviceID': '666666'}",
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": True,
    }
]


check_new_info_sn_dk_none = [
    {
        "DeviceID": "new_deveic_id",
        "deviceType": "storage",
        "fmPortID": {"qemu-001": ["1-1"]},
        "oobDeviceID": "ODI-2501",
        "PCIeVendorId": "22",
        "PCIeDeviceId": "333",
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": {"qemu-001": ["5-5-5-5-5"]},
        "switchSerialNumber": None,
        "switchModel": None,
        "switchManufacturer": None,
        "fmManagerID": ["qemu-001"],
        "oobManagerID": ["BMC-1"],
        "portKeys": "{'port': '0123'}",
        "deviceKeys": None,
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": True,
    }
]

check_base_json_info_diff = [
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


def test__update_db_info_fmswid_portkeys_samedata_fid():
    """No err

    same data

    """
    devices_info_json = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d["valid"] = True  # for new_info_d

    expected_devices_info_json = devices_info_json.copy(deep=True)
    expected_devices_info_json["valid"] = True


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(
        devices_info_json, new_info_fm_sw_id_d, ["fmSwitchID", "fmManagerID"]
    )

    assert ret1.equals(expected_devices_info_json)
    assert ret2.empty


def test__update_db_info_fmswid_portkeys_sn_none_fid():
    """No err

    Temporarily without a serial number.

    """
    devices_info_json = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_info_sn_none)

    expected_devices_info_json = devices_info_json.copy(deep=True)
    expected_devices_info_json["valid"] = True


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(
        devices_info_json, new_info_fm_sw_id_d, ["fmSwitchID", "fmManagerID"]
    )

    assert ret1.equals(expected_devices_info_json)
    assert ret2.empty


def test__update_db_info_fmswid_portkeys_sn_dk_none_fid():
    """No err

    Temporarily without a serial number and deviceKeys.

    """
    devices_info_json = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_info_sn_dk_none)

    expected_devices_info_json = devices_info_json.copy(deep=True)
    expected_devices_info_json["valid"] = True


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(
        devices_info_json, new_info_fm_sw_id_d, ["fmSwitchID", "fmManagerID"]
    )

    assert ret1.equals(expected_devices_info_json)
    assert ret2.empty


def test__update_db_info_fmswid_portkeys_sn_dk_none_diff_other_fid():
    """No err

    - Temporarily without a serial number.
    - portKeys match, but other information does not match.

    """
    devices_info_json = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_info_sn_dk_none)
    new_info_fm_sw_id_d["PCIeVendorId"] = "77"


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(
        devices_info_json, new_info_fm_sw_id_d, ["fmSwitchID", "fmManagerID"]
    )

    assert ret1.equals(devices_info_json)
    assert ret2.equals(new_info_fm_sw_id_d)


def test__update_db_info_fmswid_portkeys_sn_dk_none_diff_portkeys_fid():
    """No err

    - Temporarily without a serial number.
    - portKeys does not match, but other informations match.

    """
    devices_info_json = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_info_sn_dk_none)
    new_info_fm_sw_id_d["portKeys"] = "{'port': '1234'}"


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(
        devices_info_json, new_info_fm_sw_id_d, ["fmSwitchID", "fmManagerID"]
    )

    assert ret1.equals(devices_info_json)
    assert ret2.equals(new_info_fm_sw_id_d)


def test__update_db_info_fmswid_portkeys_sn_dk_none_diff_portkeys_other_fid():
    """No err

    - Temporarily without a serial number.
    - portKeys and other information do not match.

    """
    devices_info_json = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_info_sn_dk_none)
    new_info_fm_sw_id_d["portKeys"] = "{'port': '1234'}"
    new_info_fm_sw_id_d["PCIeVendorId"] = "77"


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(
        devices_info_json, new_info_fm_sw_id_d, ["fmSwitchID", "fmManagerID"]
    )

    assert ret1.equals(devices_info_json)
    assert ret2.equals(new_info_fm_sw_id_d)


def test__update_db_info_fmswid_portkeys_samedata_pk():
    """No err

    same data

    """
    devices_info_json = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d["valid"] = True  # for new_info_d

    expected_devices_info_json = devices_info_json.copy(deep=True)
    expected_devices_info_json["valid"] = True


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(devices_info_json, new_info_fm_sw_id_d, ["portKeys"])

    assert ret1.equals(expected_devices_info_json)
    assert ret2.empty


def test__update_db_info_fmswid_portkeys_sn_none_pk():
    """No err

    Temporarily without a serial number.

    """
    devices_info_json = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_info_sn_none)

    expected_devices_info_json = devices_info_json.copy(deep=True)
    expected_devices_info_json["valid"] = True


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(devices_info_json, new_info_fm_sw_id_d, ["portKeys"])

    assert ret1.equals(expected_devices_info_json)
    assert ret2.empty


def test__update_db_info_fmswid_portkeys_sn_dk_none_pk():
    """No err

    Temporarily without a serial number and deviceKeys.

    """
    devices_info_json = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_info_sn_dk_none)

    expected_devices_info_json = devices_info_json.copy(deep=True)
    expected_devices_info_json["valid"] = True


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(devices_info_json, new_info_fm_sw_id_d, ["portKeys"])

    assert ret1.equals(expected_devices_info_json)
    assert ret2.empty


def test__update_db_info_fmswid_portkeys_sn_dk_none_diff_other_pk():
    """No err

    - Temporarily without a serial number.
    - portKeys match, but other information does not match.

    """
    devices_info_json = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_info_sn_dk_none)
    new_info_fm_sw_id_d["PCIeVendorId"] = "77"


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(devices_info_json, new_info_fm_sw_id_d, ["portKeys"])

    assert ret1.equals(devices_info_json)
    assert ret2.equals(new_info_fm_sw_id_d)


def test__update_db_info_fmswid_portkeys_sn_dk_none_diff_portkeys_pk():
    """No err

    - Temporarily without a serial number.
    - portKeys does not match, but other informations match.

    """
    devices_info_json = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_info_sn_dk_none)
    new_info_fm_sw_id_d["portKeys"] = "{'port': '1234'}"


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(devices_info_json, new_info_fm_sw_id_d, ["portKeys"])

    # assert ret1.equals(devices_info_json)
    assert ret1.values.tolist() == devices_info_json.values.tolist()
    assert ret2.equals(new_info_fm_sw_id_d)


def test__update_db_info_fmswid_portkeys_sn_dk_none_diff_portkeys_other_pk():
    """No err

    - Temporarily without a serial number.
    - portKeys and other information do not match.

    """
    devices_info_json = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_info_sn_dk_none)
    new_info_fm_sw_id_d["portKeys"] = "{'port': '1234'}"
    new_info_fm_sw_id_d["PCIeVendorId"] = "77"


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(devices_info_json, new_info_fm_sw_id_d, ["portKeys"])

    # assert ret1.equals(devices_info_json)
    assert ret1.values.tolist() == devices_info_json.values.tolist()
    assert ret2.equals(new_info_fm_sw_id_d)


check_base_switch_info = [
    {
        "DeviceID": "new_switch_id",
        "deviceType": "switch",
        "fmPortID": {},
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "A-Alma-93-40",
        "connectedFmSwitchID": {},
        "switchSerialNumber": "22",
        "switchModel": "333",
        "switchManufacturer": "444",
        "fmManagerID": ["qemu-001"],
        "oobManagerID": ["BMC-1"],
        "portKeys": "{'port': '0123'}",
        "deviceKeys": "{'SimulatedDeviceID': '666666'}",
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": False,
    }
]


check_new_switch_info_sn_none = [
    {
        "DeviceID": "new_switch_id",
        "deviceType": "switch",
        "fmPortID": {},
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "A-Alma-93-40",
        "connectedFmSwitchID": {},
        "switchSerialNumber": None,
        "switchModel": "333",
        "switchManufacturer": "444",
        "fmManagerID": ["qemu-001"],
        "oobManagerID": ["BMC-1"],
        "portKeys": "{'port': '0123'}",
        "deviceKeys": "{'SimulatedDeviceID': '666666'}",
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": True,
    }
]


check_new_switch_info_sn_swid_none = [
    {
        "DeviceID": "new_switch_id",
        "deviceType": "switch",
        "fmPortID": {},
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "A-Alma-93-40",
        "connectedFmSwitchID": {},
        "switchSerialNumber": None,
        "switchModel": "333",
        "switchManufacturer": "444",
        "fmManagerID": ["qemu-001"],
        "oobManagerID": ["BMC-1"],
        "portKeys": "{'port': '0123'}",
        "deviceKeys": "{'SimulatedDeviceID': '666666'}",
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": True,
    }
]


def test__update_db_info_fmswid_portkeys_samedata_sw_fid():
    """No err

    same data

    """
    devices_info_json = pd.DataFrame(check_base_switch_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_base_switch_info)
    new_info_fm_sw_id_d["valid"] = True  # for new_info_d

    expected_devices_info_json = devices_info_json.copy(deep=True)
    expected_devices_info_json["valid"] = True


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(
        devices_info_json, new_info_fm_sw_id_d, ["fmSwitchID", "fmManagerID"]
    )

    assert ret1.equals(expected_devices_info_json)
    assert ret2.empty


def test__update_db_info_fmswid_portkeys_sn_none_sw_fid():
    """No err

    Temporarily without a serial number.

    """
    devices_info_json = pd.DataFrame(check_base_switch_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_switch_info_sn_none)

    expected_devices_info_json = devices_info_json.copy(deep=True)
    expected_devices_info_json["valid"] = True


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(
        devices_info_json, new_info_fm_sw_id_d, ["fmSwitchID", "fmManagerID"]
    )

    assert ret1.equals(expected_devices_info_json)
    assert ret2.empty


def test__update_db_info_fmswid_portkeys_sn_none_diff_other_sw_fid():
    """No err

    - Temporarily without a serial number.
    - fmSwitchID match, but other information does not match.

    """
    devices_info_json = pd.DataFrame(check_base_switch_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_switch_info_sn_none)
    new_info_fm_sw_id_d["switchManufacturer"] = "777"


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(
        devices_info_json, new_info_fm_sw_id_d, ["fmSwitchID", "fmManagerID"]
    )

    # assert ret1.equals(devices_info_json)
    assert ret1.equals(devices_info_json)
    assert ret2.equals(new_info_fm_sw_id_d)


def test__update_db_info_fmswid_portkeys_sn_none_diff_fmswid_sw_fid():
    """No err

    - Temporarily without a serial number.
    - fmSwitchID does not match, but other informations match.

    """
    devices_info_json = pd.DataFrame(check_base_switch_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_switch_info_sn_none)
    new_info_fm_sw_id_d["fmSwitchID"] = "D-Alma-93-40"


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(
        devices_info_json, new_info_fm_sw_id_d, ["fmSwitchID", "fmManagerID"]
    )

    # assert ret1.equals(devices_info_json)
    assert ret1.values.tolist() == devices_info_json.values.tolist()
    assert ret2.equals(new_info_fm_sw_id_d)


def test__update_db_info_fmswid_portkeys_sn_none_diff_portkeys_other_sw_fid():
    """No err

    - Temporarily without a serial number and deviceKeys.
    - fmSwitchID and other information do not match.

    """
    devices_info_json = pd.DataFrame(check_base_switch_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_info_sn_dk_none)
    new_info_fm_sw_id_d["switchModel"] = "888"
    new_info_fm_sw_id_d["fmSwitchID"] = "D-Alma-93-40"


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(
        devices_info_json, new_info_fm_sw_id_d, ["fmSwitchID", "fmManagerID"]
    )

    # assert ret1.equals(devices_info_json)
    assert ret1.values.tolist() == devices_info_json.values.tolist()
    assert ret2.equals(new_info_fm_sw_id_d)


def test__update_db_info_fmswid_portkeys_samedata_sw_pk():
    """No err

    same data

    """
    devices_info_json = pd.DataFrame(check_base_switch_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_base_switch_info)
    new_info_fm_sw_id_d["valid"] = True  # for new_info_d

    expected_devices_info_json = devices_info_json.copy(deep=True)
    expected_devices_info_json["valid"] = True


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(devices_info_json, new_info_fm_sw_id_d, ["portKeys"])

    assert ret1.equals(expected_devices_info_json)
    assert ret2.empty


def test__update_db_info_fmswid_portkeys_sn_none_sw_pk():
    """No err

    Temporarily without a serial number.

    """
    devices_info_json = pd.DataFrame(check_base_switch_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_switch_info_sn_none)

    expected_devices_info_json = devices_info_json.copy(deep=True)
    expected_devices_info_json["valid"] = True


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(devices_info_json, new_info_fm_sw_id_d, ["portKeys"])

    assert ret1.equals(expected_devices_info_json)
    assert ret2.empty


def test__update_db_info_fmswid_portkeys_sn_none_diff_other_sw_pk():
    """No err

    - Temporarily without a serial number.
    - fmSwitchID match, but other information does not match.

    """
    devices_info_json = pd.DataFrame(check_base_switch_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_switch_info_sn_none)
    new_info_fm_sw_id_d["switchManufacturer"] = "777"


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(devices_info_json, new_info_fm_sw_id_d, ["portKeys"])

    # assert ret1.equals(devices_info_json)
    assert ret1.equals(devices_info_json)
    assert ret2.equals(new_info_fm_sw_id_d)


def test__update_db_info_fmswid_portkeys_sn_none_diff_fmswid_sw_pk():
    """No err

    - Temporarily without a serial number.
    - fmSwitchID does not match, but other informations match.

    """
    devices_info_json = pd.DataFrame(check_base_switch_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_switch_info_sn_none)
    new_info_fm_sw_id_d["fmSwitchID"] = "D-Alma-93-40"


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(devices_info_json, new_info_fm_sw_id_d, ["portKeys"])

    # assert ret1.equals(devices_info_json)
    assert ret1.values.tolist() == devices_info_json.values.tolist()
    assert ret2.equals(new_info_fm_sw_id_d)


def test__update_db_info_fmswid_portkeys_sn_none_diff_portkeys_other_sw_pk():
    """No err

    - Temporarily without a serial number and deviceKeys.
    - fmSwitchID and other information do not match.

    """
    devices_info_json = pd.DataFrame(check_base_switch_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_info_sn_dk_none)
    new_info_fm_sw_id_d["switchModel"] = "888"
    new_info_fm_sw_id_d["fmSwitchID"] = "D-Alma-93-40"


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(devices_info_json, new_info_fm_sw_id_d, ["portKeys"])

    # assert ret1.equals(devices_info_json)
    assert ret1.values.tolist() == devices_info_json.values.tolist()
    assert ret2.equals(new_info_fm_sw_id_d)


check_new_info_diff_fmid = [
    {
        "DeviceID": "new_switch_id",
        "deviceType": "switch",
        "fmPortID": {},
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "A-Alma-93-40",
        "connectedFmSwitchID": {},
        "switchSerialNumber": "22",
        "switchModel": "333",
        "switchManufacturer": "444",
        "fmManagerID": ["qemu-002"],
        "oobManagerID": ["BMC-1"],
        "portKeys": "{'port': '0123'}",
        "deviceKeys": "{'SimulatedDeviceID': '666666'}",
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": False,
    }
]


def test__update_db_info_fmswid_portkeys_diff_fmmanagerid_fid():
    """No err

    The fmSwitchID matches but the fmManagerID differs in new_info_d and devices_info_json.

    """
    devices_info_json = pd.DataFrame(check_base_switch_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_info_diff_fmid)


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(
        devices_info_json, new_info_fm_sw_id_d, ["fmSwitchID", "fmManagerID"]
    )

    # assert ret1.equals(devices_info_json)
    assert ret1.values.tolist() == devices_info_json.values.tolist()
    assert ret2.equals(new_info_fm_sw_id_d)


check_new_info_same_fmswitchid_fmmanagerid = [
    {
        "DeviceID": "new_switch_id",
        "deviceType": "switch",
        "fmPortID": {},
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "A-Alma-93-40",
        "connectedFmSwitchID": {},
        "switchSerialNumber": "22",
        "switchModel": "333",
        "switchManufacturer": "444",
        "fmManagerID": ["qemu-001"],
        "oobManagerID": ["BMC-1"],
        "portKeys": "{'port': '0123'}",
        "deviceKeys": "{'SimulatedDeviceID': '666666'}",
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": False,
    },
    {
        "DeviceID": "new_switch_id2",
        "deviceType": "switch",
        "fmPortID": {},
        "oobDeviceID": None,
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": "A-Alma-93-40",
        "connectedFmSwitchID": {},
        "switchSerialNumber": "2222",
        "switchModel": "333333",
        "switchManufacturer": "444444",
        "fmManagerID": ["qemu-001"],
        "oobManagerID": ["BMC-2"],
        "portKeys": "{'port': '01230123'}",
        "deviceKeys": "{'SimulatedDeviceID': '666666666666'}",
        "switchPortType": "PSD",
        "fmValid": True,
        "valid": False,
    },
]


def test__update_db_info_fmswid_portkeys_same_fmswitchid_fmmanagerid_fid():
    """No err

    The fmSwitchID matches but the fmManagerID differs in new_info_d and devices_info_json.

    """
    devices_info_json = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_info_same_fmswitchid_fmmanagerid)


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(
        devices_info_json, new_info_fm_sw_id_d, ["fmSwitchID", "fmManagerID"]
    )

    # assert ret1.equals(devices_info_json)
    assert ret1.values.tolist() == devices_info_json.values.tolist()
    assert ret2.empty


# Either the fmSwitchID or the fmManagerID is None
# - See test__update_db_info_fmswid_portkeys_sn_dk_none_diff_portkeys_other_fid().


def test__update_db_info_fmswid_portkeys_none_fmswitchid_fmmanagerid_fid():
    """No err

    The fmSwitchID and the fmManagerID are None in new_info_d.

    """
    devices_info_json = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d["fmSwitchID"] = None
    new_info_fm_sw_id_d["fmManagerID"] = None
    new_info_fm_sw_id_d["valid"] = True  # for new_info_d


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(
        devices_info_json, new_info_fm_sw_id_d, ["fmSwitchID", "fmManagerID"]
    )

    # assert ret1.equals(devices_info_json)
    assert ret1.values.tolist() == devices_info_json.values.tolist()
    assert ret2.equals(new_info_fm_sw_id_d)


# The portKeys matches in new_info_d and devices_info_json.
# - See test__update_db_info_fmswid_portkeys_sn_none_pk()


check_new_info_same_portkeys = [
    {
        "DeviceID": "new_deveic_id",
        "deviceType": "storage",
        "fmPortID": {"qemu-001": ["1-1"]},
        "oobDeviceID": "ODI-2501",
        "PCIeVendorId": "22",
        "PCIeDeviceId": "333",
        "PCIeDeviceSerialNumber": "4444",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": {"qemu-001": ["5-5-5-5-5"]},
        "switchSerialNumber": None,
        "switchModel": None,
        "switchManufacturer": None,
        "fmManagerID": ["qemu-001"],
        "oobManagerID": ["BMC-1"],
        "portKeys": "{'port': '0123'}",
        "deviceKeys": "{'SimulatedDeviceID': '666666'}",
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": False,
    },
    {
        "DeviceID": "new_deveic_id2",
        "deviceType": "storage",
        "fmPortID": {"qemu-001": ["1-1-1-1"]},
        "oobDeviceID": "ODI-2501",
        "PCIeVendorId": "2222",
        "PCIeDeviceId": "333333",
        "PCIeDeviceSerialNumber": "44444444",
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "fmSwitchID": None,
        "connectedFmSwitchID": {"qemu-001": ["5-5-5-5-5-5-5-5-5-5"]},
        "switchSerialNumber": None,
        "switchModel": None,
        "switchManufacturer": None,
        "fmManagerID": ["qemu-002"],
        "oobManagerID": ["BMC-2"],
        "portKeys": "{'port': '0123'}",
        "deviceKeys": "{'SimulatedDeviceID': '666666666666'}",
        "switchPortType": "DSP",
        "fmValid": True,
        "valid": False,
    },
]


def test__update_db_info_fmswid_portkeys_same_portkeys_pk():
    """No err

    The portKeys matches in new_info_d.

    """
    devices_info_json = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_new_info_same_portkeys)


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(devices_info_json, new_info_fm_sw_id_d, ["portKeys"])

    # assert ret1.equals(devices_info_json)
    assert ret1.values.tolist() == devices_info_json.values.tolist()
    assert ret2.empty


def test__update_db_info_fmswid_portkeys_none_portkeys_pk():
    """No err

    The portKeys is None in new_info_d.

    """
    devices_info_json = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d = pd.DataFrame(check_base_json_info)
    new_info_fm_sw_id_d["portKeys"] = None
    new_info_fm_sw_id_d["valid"] = True  # for new_info_d


    ret1, ret2 = dim._update_db_info_fmswid_portkeys(devices_info_json, new_info_fm_sw_id_d, ["portKeys"])

    # assert ret1.equals(devices_info_json)
    assert ret1.values.tolist() == devices_info_json.values.tolist()
    assert ret2.equals(new_info_fm_sw_id_d)


# The portKeys matches but the PCIVendorID differs in new_info_d and devices_info_json.
# - see test__update_db_info_fmswid_portkeys_sn_dk_none_diff_other_pk()


def test_all_reset():
    """no error
    rest setting file
    """
    all_reset()
    os.remove(_DEVICE_ID_MANAGER_FILE_PATH)
    os.remove(_INVALID_SERIAL_NUMBER_FILE_PATH)

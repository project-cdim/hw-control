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
"""Device manager UT (part 1)

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
from app.common.dim import device_id_base
from app.common.dim.device_id_base import assign_device_id
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
def set_env(monkeypatch: MonkeyPatch):
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
    except Exception:  # pylint: disable=W0718
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


def test_assign_device_id_plugin_list_empty():
    """No err

    list from get_manager_list() is empty

    """
    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, reset_data)
    manager_list = []
    ret = 0
    with patch("app.common.dim.device_id_manager.get_manager_list", autospec=True) as mock_get_manager_list:
        mock_get_manager_list.return_value = manager_list
        assign_device_id()
        ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn1")
    check_output("ptn1")


@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_get_plugin_err(mocker: MockFixture, caplog: LogCaptureFixture):
    """No err

    get_plugin is error

    """
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, reset_data)

    ret = 0
    with patch("app.common.utils.plugin_manager.get_plugin", autospec=True) as mock_get_plugin:
        mock_get_plugin.side_effect = Err.APIUsageHWControlError
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=device_id_base.__name__):
            assign_device_id()
            ret = 1

    assert ret == 1
    assert check_data_type()
    mv_output("ptn2")
    check_output("ptn2")

    # check log
    assert len(caplog.records) == 2

    # Inspection: Check the fm plugin call log.
    fm_plugin_call_log = caplog.records[0]
    assert fm_plugin_call_log.levelname == "WARNING"
    assert fm_plugin_call_log.getMessage() == "Failed to get Plugin class instance (FM:qemu-01)."
    assert fm_plugin_call_log.exc_info is not None, "exc_info should be present in the log record"
    assert fm_plugin_call_log.exc_info[0] is not None
    assert fm_plugin_call_log.exc_info[0].__name__ == "APIUsageHWControlError"

    # Inspection: Check the oob plugin call log.
    oob_plugin_call_log = caplog.records[1]
    assert oob_plugin_call_log.levelname == "WARNING"
    assert oob_plugin_call_log.getMessage() == "Failed to get Plugin class instance (OOB:oob-1)."
    assert oob_plugin_call_log.exc_info is not None, "exc_info should be present in the log record"
    assert oob_plugin_call_log.exc_info[0] is not None
    assert oob_plugin_call_log.exc_info[0].__name__ == "APIUsageHWControlError"


@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_get_plugin_err_exception(mocker: MockFixture, caplog: LogCaptureFixture):
    """No err

    get_plugin() is error(Unexpected error)

    """
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, reset_data)

    ret = 0
    with patch("app.common.utils.plugin_manager.get_plugin", autospec=True) as mock_get_plugin:
        mock_get_plugin.side_effect = Err.BaseHWControlError
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=device_id_base.__name__):
            assign_device_id()
            ret = 1

    assert ret == 1
    assert check_data_type()
    mv_output("ptn3")
    check_output("ptn3")

    # check log
    assert len(caplog.records) == 2

    # Inspection: Check the fm plugin call log.
    fm_plugin_call_log = caplog.records[0]
    assert fm_plugin_call_log.levelname == "WARNING"
    assert fm_plugin_call_log.getMessage() == "Failed to get Plugin class instance due to other error (FM:qemu-01)."
    assert fm_plugin_call_log.exc_info is not None, "exc_info should be present in the log record"
    assert fm_plugin_call_log.exc_info[0] is not None
    assert fm_plugin_call_log.exc_info[0].__name__ == "BaseHWControlError"

    # Inspection: Check the oob plugin call log.
    oob_plugin_call_log = caplog.records[1]
    assert oob_plugin_call_log.levelname == "WARNING"
    assert oob_plugin_call_log.getMessage() == "Failed to get Plugin class instance due to other error (OOB:oob-1)."
    assert oob_plugin_call_log.exc_info is not None, "exc_info should be present in the log record"
    assert oob_plugin_call_log.exc_info[0] is not None
    assert oob_plugin_call_log.exc_info[0].__name__ == "BaseHWControlError"


class MockPluginErr:
    """set error

    raise error when get_xxx_info is invoked

    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        raise Err.BaseHWControlError

    def get_switch_info(self):
        """set result of get_switch_info
        set result of all get_switch_info
        """
        raise Err.BaseHWControlError

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        raise Err.BaseHWControlError

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch("app.common.utils.plugin_manager.get_plugin", return_value=MockPluginErr())
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_get_xxxx_info_all_err(
    monkeypatch: MonkeyPatch, mocker: MockFixture, caplog: LogCaptureFixture
):
    """No err

    All get_xxxx_info() are error

    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, reset_data)

    ret = 0
    caplog.clear()
    with caplog.at_level(logging.INFO, logger=device_id_base.__name__):
        assign_device_id()
        ret = 1

    assert ret == 1
    assert check_data_type()
    mv_output("ptn4")
    check_output("ptn4")

    # check log
    assert len(caplog.records) == 3

    # Inspection: Check the fm port info log.
    fm_port_info_log = caplog.records[0]
    assert fm_port_info_log.levelname == "WARNING"
    assert fm_port_info_log.getMessage() == "Failed to get port info of (qemu-01)."
    assert fm_port_info_log.exc_info is not None, "exc_info should be present in the log record"
    assert fm_port_info_log.exc_info[0] is not None
    assert fm_port_info_log.exc_info[0].__name__ == "BaseHWControlError"

    # Inspection: Check the switch info log.
    switch_info_log = caplog.records[1]
    assert switch_info_log.levelname == "WARNING"
    assert switch_info_log.getMessage() == "Failed to get switch info of (qemu-01)."
    assert switch_info_log.exc_info is not None, "exc_info should be present in the log record"
    assert switch_info_log.exc_info[0] is not None
    assert switch_info_log.exc_info[0].__name__ == "BaseHWControlError"

    # Inspection: Check the device info log.
    device_info_log = caplog.records[2]
    assert device_info_log.levelname == "WARNING"
    assert device_info_log.getMessage() == "Failed to get device info of (oob-1)."
    assert device_info_log.exc_info is not None, "exc_info should be present in the log record"
    assert device_info_log.exc_info[0] is not None
    assert device_info_log.exc_info[0].__name__ == "BaseHWControlError"


class MockPluginOnlySwitchErr:
    """set error

    raise error when get_switch_info is invoked

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
        raise Err.BaseHWControlError

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        device_list = []
        return device_list

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch("app.common.utils.plugin_manager.get_plugin", return_value=MockPluginOnlySwitchErr())
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_only_get_switch_err(monkeypatch: MonkeyPatch, mocker: MockFixture, caplog: LogCaptureFixture):
    """No err

    Only get_switch_info is error

    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, reset_data)

    ret = 0
    caplog.clear()
    with caplog.at_level(logging.INFO, logger=device_id_base.__name__):
        assign_device_id()
        ret = 1

    assert ret == 1
    assert check_data_type()
    mv_output("ptn5")
    check_output("ptn5")

    # check log
    assert len(caplog.records) == 1
    # Inspection: Check the switch info log.
    switch_info_log = caplog.records[0]
    assert switch_info_log.levelname == "WARNING"
    assert switch_info_log.getMessage() == "Failed to get switch info of (qemu-01)."
    assert switch_info_log.exc_info is not None, "exc_info should be present in the log record"
    assert switch_info_log.exc_info[0] is not None
    assert switch_info_log.exc_info[0].__name__ == "BaseHWControlError"


class MockPluginErrException:
    """set error

    raise error when get_xxxx_info is invoked

    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        raise Err.BaseHWControlError

    def get_switch_info(self):
        """set result of get_switch_info
        set result of all get_switch_info
        """
        raise Err.BaseHWControlError

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        raise Err.BaseHWControlError

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch("app.common.utils.plugin_manager.get_plugin", return_value=MockPluginErrException())
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_get_xxxx_info_all_err_exception(
    monkeypatch: MonkeyPatch, mocker: MockFixture, caplog: LogCaptureFixture
):
    """No err

    all get_xxxx_info are error

    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, reset_data)

    ret = 0
    caplog.clear()
    with caplog.at_level(logging.INFO, logger=device_id_base.__name__):
        assign_device_id()
        ret = 1

    assert ret == 1
    assert check_data_type()
    mv_output("ptn6")
    check_output("ptn6")

    # check log
    assert len(caplog.records) == 3

    # Inspection: Check the fm port info log.
    fm_port_info_log = caplog.records[0]
    assert fm_port_info_log.levelname == "WARNING"
    assert fm_port_info_log.getMessage() == "Failed to get port info of (qemu-01)."
    assert fm_port_info_log.exc_info is not None, "exc_info should be present in the log record"
    assert fm_port_info_log.exc_info[0] is not None
    assert fm_port_info_log.exc_info[0].__name__ == "BaseHWControlError"

    # Inspection: Check the switch info log.
    switch_info_log = caplog.records[1]
    assert switch_info_log.levelname == "WARNING"
    assert switch_info_log.getMessage() == "Failed to get switch info of (qemu-01)."
    assert switch_info_log.exc_info is not None, "exc_info should be present in the log record"
    assert switch_info_log.exc_info[0] is not None
    assert switch_info_log.exc_info[0].__name__ == "BaseHWControlError"

    # Inspection: Check the device info log.
    device_info_log = caplog.records[2]
    assert device_info_log.levelname == "WARNING"
    assert device_info_log.getMessage() == "Failed to get device info of (oob-1)."
    assert device_info_log.exc_info is not None, "exc_info should be present in the log record"
    assert device_info_log.exc_info[0] is not None
    assert device_info_log.exc_info[0].__name__ == "BaseHWControlError"


class MockPluginOnlySwitchErrException:
    """set error

    raise error when get_switch_info is invoked

    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        port_list = {"data": []}
        return port_list

    def get_switch_info(self):
        """set result of get_switch_info
        set result of all get_switch_info
        """
        raise Err.BaseHWControlError

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        device_list = []
        return device_list

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch("app.common.utils.plugin_manager.get_plugin", return_value=MockPluginOnlySwitchErrException())
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_only_get_switch_err_exception(
    monkeypatch: MonkeyPatch, mocker: MockFixture, caplog: LogCaptureFixture
):
    """No err

    Only get_switch_info is error

    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, reset_data)

    ret = 0
    caplog.clear()
    with caplog.at_level(logging.INFO, logger=device_id_base.__name__):
        assign_device_id()
        ret = 1

    assert ret == 1
    assert check_data_type()
    mv_output("ptn7")
    check_output("ptn7")

    # check log
    assert len(caplog.records) == 1

    # Inspection: Check the switch info log.
    switch_info_log = caplog.records[0]
    assert switch_info_log.levelname == "WARNING"
    assert switch_info_log.getMessage() == "Failed to get switch info of (qemu-01)."
    assert switch_info_log.exc_info is not None, "exc_info should be present in the log record"
    assert switch_info_log.exc_info[0] is not None
    assert switch_info_log.exc_info[0].__name__ == "BaseHWControlError"


class MockPluginNoInfo:
    """set result of get_xxxx_info

    no info

    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        port_list = {"data": []}
        return port_list

    def get_switch_info(self):
        """set result of get_switch_info
        set result of all get_switch_info
        """
        switch_list = {"data": []}
        return switch_list

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        device_list = []
        return device_list

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch("app.common.utils.plugin_manager.get_plugin", return_value=MockPluginNoInfo())
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_ok_no_info(monkeypatch: MonkeyPatch, mocker: MockFixture):
    """No err

    No pre data, all new information

    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, reset_data)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn8")
    check_output("ptn8")


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

port_list_def_2 = {
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
            "PCIeVendorId": None,
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": None,
            "CPUManufacturer": None,
            "CPUModel": None,
            "CPUSerialNumber": None,
            "LTSSMState": None,
            "deviceKeys": {"test": "test"},
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


class MockPluginJustPortInfo:
    """set result of get_xxxx_info

    just port info

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
        switch_list = {"data": []}
        return convert_switch_data(switch_list)

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        device_list = []
        return convert_device_data(device_list)

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch("app.common.utils.plugin_manager.get_plugin", return_value=MockPluginJustPortInfo())
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_ok_just_port_info(monkeypatch: MonkeyPatch, mocker: MockFixture):
    """No err

    Only get_port_info has information

    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, reset_data)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn9")
    check_output("ptn9")


class MockPluginJustPortInfo2:
    """set result of get_xxxx_info

    just port info

    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        return convert_port_data(port_list_def_2)

    def get_switch_info(self):
        """set result of get_switch_info
        set result of all get_switch_info
        """
        switch_list = {"data": []}
        return convert_switch_data(switch_list)

    def get_device_info(self):
        """set result of get_xxxx_info
        set result of all get_device_info
        """
        device_list = []
        return convert_device_data(device_list)

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch("app.common.utils.plugin_manager.get_plugin", return_value=MockPluginJustPortInfo2())
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_ok_just_port_info_2(monkeypatch: MonkeyPatch, mocker: MockFixture):
    """No err

    Only get_port_info has information

    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, reset_data)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn10")
    check_output("ptn10")


class MockPluginJustPortAndSwitchInfo:
    """set result of get_xxxx_info

    just port info and switch info

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
        device_list = []
        return convert_device_data(device_list)

    def get_manager_list(self, manager_type):
        """set result of get_xxxx_info
        set result of all get_manager_info
        """
        if manager_type == "fm":
            return fm_manager_list
        return oob_manager_list


@patch("app.common.utils.plugin_manager.get_plugin", return_value=MockPluginJustPortAndSwitchInfo())
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_ok_port_and_switch_info(monkeypatch, mocker: MockFixture):
    """No err

    Only get_port_info and get_switch_info  have information

    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, reset_data)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn11")
    check_output("ptn11")


class MockPluginJustDeviceInfo:
    """set result of get_xxxx_info

    just device info

    """

    def get_port_info(self):
        """set result of get_port_info
        set result of all get_port_info
        """
        port_list = {"data": []}
        return convert_port_data(port_list)

    def get_switch_info(self):
        """set result of get_switch_info
        set result of all get_switch_info
        """
        switch_list = {"data": []}
        return convert_switch_data(switch_list)

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


@patch("app.common.utils.plugin_manager.get_plugin", return_value=MockPluginJustDeviceInfo())
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_ok_just_device_info(monkeypatch, mocker: MockFixture):
    """No err

    Only get_device_info has information

    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, reset_data)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn12")
    check_output("ptn12")


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


@patch("app.common.utils.plugin_manager.get_plugin", return_value=MockPluginPortAndSwitchAndDeviceInfo())
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_ok_port_and_switch_and_device_info(monkeypatch, mocker: MockFixture):
    """No err

    All information is available

    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, reset_data)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn13")
    check_output("ptn13")


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


@patch("app.common.utils.plugin_manager.get_plugin", return_value=MockPluginPortAndSwitchAndDeviceInfo2())
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_new_data_bysn(monkeypatch, mocker: MockFixture):
    """No err

    New registration with serial number

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
    mv_output("ptn14")
    check_output("ptn14")


class MockPluginPortAndSwitchAndDeviceInfo3:
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


@patch("app.common.utils.plugin_manager.get_plugin", return_value=MockPluginPortAndSwitchAndDeviceInfo3())
@patch(
    "app.common.dim.device_id_manager.get_manager_list",
    side_effect=MockPluginGetManagerList().get_manager_list,
)
def test_assign_device_id_new_data_bysn_no_manager_ids(monkeypatch, mocker: MockFixture):
    """No err

    New registration with serial number, no managerId

    """
    monkeypatch.setattr("app.common.dim.device_id_base.some_method", lambda: None)
    mocker.patch("app.common.dim.device_id_base.some_other_method", return_value=42)

    reset_setting_file(_INVALID_SERIAL_NUMBER_FILE_PATH, reset_data)
    reset_setting_file(_DEVICE_ID_MANAGER_FILE_PATH, pre_data_no_managerIds)
    ret = 0
    assign_device_id()
    ret = 1
    assert ret == 1
    assert check_data_type()
    mv_output("ptn15")
    check_output("ptn15")
    all_reset()


def test_all_reset():
    """no error
    rest setting file
    """
    all_reset()
    os.remove(_DEVICE_ID_MANAGER_FILE_PATH)
    os.remove(_INVALID_SERIAL_NUMBER_FILE_PATH)

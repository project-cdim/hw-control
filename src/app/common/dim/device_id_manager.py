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

"""Device ID management

Manage device ID,
it is possible to operate according to the environment.

"""
import logging
from enum import Enum
import uuid
import re
import pandas as pd

from app.common.utils.fm_plugin_base import FMPluginBase
from app.common.utils.oob_plugin_base import OOBPluginBase
from app.common.utils.plugin_manager import get_fm_plugin
from app.common.utils.plugin_manager import get_oob_plugin
from app.common.utils.plugin_manager import get_manager_list
from app.common.constants import ManagerType

import app.common.constants as con
import app.common.basic_exceptions as Err

logger = logging.getLogger(__name__)


class HowToMerge(Enum):
    """
    How to merge...
    """

    BY_PCI_SERIAL_NUMBER = "pci_sn"
    BY_CPU_SERIAL_NUMBER = "cpu_sn"
    BY_SW_SERIAL_NUMBER = "sw_sn"
    BY_FM_SW_ID = "sw_id"
    BY_DEVICE_KEYS = "dk"
    BY_PORT_KEYS = "pk"
    INVALID = "invalid"


_check_items_pci = ["PCIeDeviceSerialNumber", "PCIeVendorId", "PCIeDeviceId"]
_check_items_cpu = ["CPUSerialNumber", "CPUManufacturer", "CPUModel"]
_check_items_switch = ["switchSerialNumber", "switchManufacturer", "switchModel"]
_check_items_port_add = ["fmPortID", "connectedFmSwitchID", "fmManagerID", "deviceKeys", "portKeys", "switchPortType"]
_check_items_switch_add = ["deviceType", "fmSwitchID", "fmManagerID"]

_check_items_device_add = ["deviceType", "oobDeviceID", "oobManagerID", "deviceKeys", "portKeys"]

all_keys = [
    "DeviceID",
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

_to_str_columns = ["fmPortID", "connectedFmSwitchID", "fmManagerID", "oobManagerID"]


def _check_info_is_not_none(info: dict[str, str | list | dict | bool | None], keys: list[str]) -> bool:
    """Check the specified information.

    Check if there is a member with a value of None in the specified
    information(dict).

    Args:
        info (dict[str, str | list | dict | bool | None]): Information(dict) to be checked.
        keys (list[str]): List of members to be checked.

    Returns:
        True: There are no members with a value of None.
        False: There is a member with a value of None.

    Raises:
        None
    """
    for key in keys:
        if info.get(key) is None:
            return False
    return True


def _is_not_invalid_serial_number(
    data: dict[str, str | list | dict | bool | None], invalid_sn_info_json: pd.DataFrame, sn_type: HowToMerge
) -> bool:
    """Check the specified information(Dict).

    Check whether specified information(Dict) is invalid due
    to the following case:
        1. The serial number is invalid.

    Args:
        data ([str, str | list | dict | bool | None]): Data for comparison
            (data obtained with get_port_info() or get_device_info()).
        invalid_sn_info_json(pandas.DataFrame): Invalid serial number
            information (from invalid serial number configuration file).
        sn_type(HowToMerge): The type of serial number.

    Returns:
        True: There is not a invalid serial number.
        False: There is a invalid serial number.

    Raises:
        None
    """
    # There is no information in the invalid serial number configuration
    # file.
    check_info = []

    if invalid_sn_info_json.empty:
        return True
    # Check information
    check_keys = []
    if sn_type == HowToMerge.BY_PCI_SERIAL_NUMBER:
        check_keys = _check_items_pci
    if sn_type == HowToMerge.BY_CPU_SERIAL_NUMBER:
        check_keys = _check_items_cpu
    if sn_type == HowToMerge.BY_SW_SERIAL_NUMBER:
        check_keys = _check_items_switch
    invalid_sn_info_json_copy = invalid_sn_info_json.copy()
    check_info.append(data)
    check_info_d = pd.DataFrame(check_info)

    check_df = pd.merge(check_info_d, invalid_sn_info_json_copy, how="inner", on=check_keys)
    if not check_df.empty:
        return False
    # Check information again without Serial Number.
    if sn_type == HowToMerge.BY_PCI_SERIAL_NUMBER:
        check_info_d["PCIeDeviceSerialNumber"] = None
    if sn_type == HowToMerge.BY_CPU_SERIAL_NUMBER:
        check_info_d["CPUSerialNumber"] = None
    if sn_type == HowToMerge.BY_SW_SERIAL_NUMBER:
        check_info_d["switchSerialNumber"] = None
    check_df = pd.merge(check_info_d, invalid_sn_info_json_copy, how="inner", on=check_keys)
    return check_df.empty


def _how_to_merge(data: dict[str, str | list | bool | dict | None], invalid_sn_info_json: pd.DataFrame) -> HowToMerge:
    """Decide how to merge.

    Decide how to merge by specified information(Dict).

    Args:
        data (dict[str, str | list | bool | dict | None]): Information(dict) to be
            checked.
        invalid_sn_info_json(pandas.DataFrame): Invalid serial number
            information (from invalid serial number configuration file).

    Returns:
        merge_by(HowToMerge): How to merge.

    Raises:
        None
    """
    if _check_info_is_not_none(data, _check_items_pci) and _is_not_invalid_serial_number(
        data, invalid_sn_info_json, HowToMerge.BY_PCI_SERIAL_NUMBER
    ):
        merge_by = HowToMerge.BY_PCI_SERIAL_NUMBER
    elif _check_info_is_not_none(data, _check_items_cpu) and _is_not_invalid_serial_number(
        data, invalid_sn_info_json, HowToMerge.BY_CPU_SERIAL_NUMBER
    ):
        merge_by = HowToMerge.BY_CPU_SERIAL_NUMBER
    elif _check_info_is_not_none(data, _check_items_switch) and _is_not_invalid_serial_number(
        data, invalid_sn_info_json, HowToMerge.BY_SW_SERIAL_NUMBER
    ):
        merge_by = HowToMerge.BY_SW_SERIAL_NUMBER
    elif _check_info_is_not_none(data, ["fmSwitchID"]):
        merge_by = HowToMerge.BY_FM_SW_ID
    elif _check_info_is_not_none(data, ["deviceKeys"]):
        merge_by = HowToMerge.BY_DEVICE_KEYS
    elif _check_info_is_not_none(data, ["portKeys"]):
        merge_by = HowToMerge.BY_PORT_KEYS
    else:
        # Invalid information
        merge_by = HowToMerge.INVALID
    return merge_by


def _assemble_port_data(
    base_info: dict[str, str | list | dict | bool | None], new_info: dict[str, str], manager_id: str
) -> dict[str, str | list | dict | bool | None]:
    """Assemble the data(from get_port_info).

    Assemble the data(from get_port_info) that want to update in the
    device manager ID file.

    Args:
        base_info (dict[str, str | list | dict | bool | None]): Base data.
        new_info (dict[str, str]): Data to be update.
        manager_id (str): Plugin manager ID.

    Returns:
        assembled data (dict[str, str | list | dict | bool | None]).

    Raises:
        None
    """
    assembled_data = base_info
    if new_info.get("id") is not None:
        assembled_data["fmPortID"] = {manager_id: [new_info.get("id")]}
    else:
        assembled_data["fmPortID"] = new_info.get("fmPortID")
    assembled_data["PCIeVendorId"] = new_info.get("PCIeVendorId")
    assembled_data["PCIeDeviceId"] = new_info.get("PCIeDeviceId")
    assembled_data["PCIeDeviceSerialNumber"] = new_info.get("PCIeDeviceSerialNumber")
    assembled_data["CPUSerialNumber"] = new_info.get("CPUSerialNumber")
    assembled_data["CPUManufacturer"] = new_info.get("CPUManufacturer")
    assembled_data["CPUModel"] = new_info.get("CPUModel")
    if new_info.get("switchId") is not None:
        assembled_data["connectedFmSwitchID"] = {manager_id: [new_info.get("switchId")]}
    else:
        assembled_data["connectedFmSwitchID"] = new_info.get("connectedFmSwitchID")
    assembled_data["fmManagerID"] = [manager_id]
    assembled_data["portKeys"] = new_info.get("portKeys")
    assembled_data["deviceKeys"] = new_info.get("deviceKeys")
    assembled_data["switchPortType"] = new_info.get("switchPortType")
    if manager_id is not None:
        assembled_data["fmValid"] = True
    return assembled_data


def _assemble_device_data(
    base_info: dict[str, str | list | dict | bool | None], new_info: dict[str, str], manager_id: str
) -> dict[str, str | list | dict | bool | None]:
    """Assemble the data(from get_device_info).

    Assemble the data(from get_device_info) that want to update in the
    device manager ID file.

    Args:
        base_info (dict[str, str | list | dict | bool | None]): Base data.
        new_info (dict[str, str]): Data to be update.
        manager_id (str): Plugin manager ID.

    Returns:
        assembled data (dict[str, str | list | dict | bool | None]).

    Raises:
        None
    """
    assembled_data = base_info
    # Merging data only occurs when getting data from OOB side,
    # so determining and executing overwriting is only necessary
    # if info_type is device_info.
    assembled_data["deviceType"] = new_info.get("deviceType")
    assembled_data["oobDeviceID"] = new_info.get("oobDeviceID")
    assembled_data["PCIeVendorId"] = new_info.get("PCIeVendorId")
    assembled_data["PCIeDeviceId"] = new_info.get("PCIeDeviceId")
    assembled_data["PCIeDeviceSerialNumber"] = new_info.get("PCIeDeviceSerialNumber")
    assembled_data["CPUSerialNumber"] = new_info.get("CPUSerialNumber")
    assembled_data["CPUManufacturer"] = new_info.get("CPUManufacturer")
    assembled_data["CPUModel"] = new_info.get("CPUModel")
    assembled_data["oobManagerID"] = [manager_id]
    assembled_data["portKeys"] = new_info.get("portKeys")
    assembled_data["deviceKeys"] = new_info.get("deviceKeys")
    return assembled_data


def _assemble_switch_data(
    base_info: dict[str, str | list | dict | bool | None], new_info: dict[str, str], manager_id: str
) -> dict[str, str | list | dict | bool | None]:
    """Assemble the data(from get_switch_info).

    Assemble the data(from get_switch_info) that want to update in the
    device manager ID file.

    Args:
        base_info (dict[str, str | list | dict | bool | None]): Base data.
        new_info (dict[str, str]): Data to be update.
        manager_id (str): Plugin manager ID.

    Returns:
        assembled data (dict[str, str | list | dict | bool | None]).

    Raises:
        None
    """
    assembled_data = base_info
    assembled_data["deviceType"] = con.DeviceType.SWITCH.value
    if new_info.get("switchId") is not None:
        assembled_data["fmSwitchID"] = new_info.get("switchId")
    else:
        assembled_data["fmSwitchID"] = new_info.get("fmSwitchID")
    assembled_data["switchSerialNumber"] = new_info.get("switchSerialNumber")
    assembled_data["switchManufacturer"] = new_info.get("switchManufacturer")
    assembled_data["switchModel"] = new_info.get("switchModel")
    assembled_data["fmManagerID"] = [manager_id]
    if manager_id is not None:
        assembled_data["fmValid"] = True
    return assembled_data


def _assemble_data(
    new_info: dict[str, str], invalid_sn_info_json: pd.DataFrame, manager_id: str, info_type: str
) -> tuple[dict[str, str | list | bool | dict | None], HowToMerge]:
    """Assemble the data.

    Assemble the data that want to update in the device manager ID file.

    Args:
        new_info (Dict[str, str]): Data to be update.
        invalid_sn_info_json (pandas.DataFrame): Invalid serial number
            information (from invalid serial number configuration file).
        manager_id (str): Plugin manager ID.
        info_type (str): From which API.

    Returns:
        assembled data (dict[str, str | list | bool | dict | None]).
        merge_by (HowToMerge): How to merge.

    Raises:
        None
    """
    # Add a new uuid by uuid4
    new_device_id = str(uuid.uuid4())
    assembled_data: dict[str, str | list | dict | bool | None] = {
        "DeviceID": new_device_id,
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
        "fmValid": False,
        "valid": True,
    }

    if info_type == "port_info":
        assembled_data = _assemble_port_data(assembled_data, new_info, manager_id)
    # Merging data only occurs when getting data from OOB side,
    # so determining and executing overwriting is only necessary
    # if info_type is device_info.
    elif info_type == "device_info":
        assembled_data = _assemble_device_data(assembled_data, new_info, manager_id)
    else:
        # info_type is 'switch_info':
        assembled_data = _assemble_switch_data(assembled_data, new_info, manager_id)
    merge_by = _how_to_merge(assembled_data, invalid_sn_info_json)
    return assembled_data, merge_by


def _update_db_info(  # pylint: disable=R0913,R0914,R0917
    device_info_list: list,
    manager: str,
    info_type: str,
    devices_info_json: pd.DataFrame,
    moved_devices: pd.DataFrame,
    invalid_sn_info_json: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Update the device ID manager file.

    Compare the acquired information and registered information.
    If merging is necessary,
    merge and register in the device ID manager file.
    If merging is not required,
    register a new data in the device ID manager file.

    Args:
        device_info_list (list): List of device information.
        manager (str): Plugin manager ID.
        info_type (str): Information type.
            (port_info/device_info/switch_info)
        devices_info_json (pandas.DataFrame): Devices information
            (from device ID manager file).
        moved_devices (pandas.DataFrame): Moved devices information.
        invalid_sn_info_json (pandas.DataFrame): Invalid serial number
            information (from invalid serial number configuration file).

    Returns:
        device_info_json (pandas.DataFrame): Devices information
        moved_devices (pandas.DataFrame): Moved devices information.

    Raises:
        None
    """

    # Generate merged data frame.
    (
        new_info_pci_sn_d,
        new_info_cpu_sn_d,
        new_info_sw_sn_d,
        new_info_fm_sw_id_d,
        new_info_device_keys_d,
        new_info_port_keys_d,
    ) = _update_db_info_mk_dataframe(
        device_info_list,
        manager,
        info_type,
        invalid_sn_info_json,
    )

    unmerged_no_device_keys_d = pd.DataFrame()
    unmerged_device_keys_info = pd.DataFrame()
    unmerged_no_port_keys_info = pd.DataFrame()
    unmerged_info_port_keys = pd.DataFrame()
    unmerged_info_fm_sw_id = pd.DataFrame()

    if info_type == "port_info":
        check_items_add = _check_items_port_add
    elif info_type == "device_info":
        check_items_add = _check_items_device_add
    else:
        check_items_add = _check_items_switch_add

    if not new_info_pci_sn_d.empty:
        (
            devices_info_json,
            moved_devices,
            new_info_device_keys_info,
            unmerged_no_device_keys_info,
        ) = _update_db_info_pci_cpu_sw(
            devices_info_json,
            new_info_pci_sn_d,
            _check_items_pci,
            check_items_add,
            "deviceKeys",  # if merge_by == BY_PCI_SERIAL_NUMBER, next_keys = "deviceKeys"
            info_type,
            moved_devices,
        )
        unmerged_no_device_keys_d = pd.concat(
            [unmerged_no_device_keys_d, unmerged_no_device_keys_info], ignore_index=True
        )
        new_info_device_keys_d = pd.concat([new_info_device_keys_d, new_info_device_keys_info], ignore_index=True)
    if not new_info_cpu_sn_d.empty:
        (
            devices_info_json,
            moved_devices,
            new_info_device_keys_info,
            unmerged_no_device_keys_info,
        ) = _update_db_info_pci_cpu_sw(
            devices_info_json,
            new_info_cpu_sn_d,
            _check_items_cpu,
            check_items_add,
            "deviceKeys",  # if merge_by == BY_CPU_SERIAL_NUMBER, next_keys = "deviceKeys"
            info_type,
            moved_devices,
        )
        unmerged_no_device_keys_d = pd.concat(
            [unmerged_no_device_keys_d, unmerged_no_device_keys_info], ignore_index=True
        )
        new_info_device_keys_d = pd.concat([new_info_device_keys_d, new_info_device_keys_info], ignore_index=True)
    if not new_info_sw_sn_d.empty:
        (
            devices_info_json,
            moved_devices,
            new_info_fm_sw_id_info,
            _,
        ) = _update_db_info_pci_cpu_sw(
            devices_info_json,
            new_info_sw_sn_d,
            _check_items_switch,
            check_items_add,
            "fmSwitchID",  # if merge_by == BY_SW_SERIAL_NUMBER, next_keys = "fmSwitchID"
            info_type,
            moved_devices,
        )
        new_info_fm_sw_id_d = pd.concat([new_info_fm_sw_id_d, new_info_fm_sw_id_info], ignore_index=True)
    if not new_info_device_keys_d.empty:
        (
            devices_info_json,
            unmerged_device_keys_info,
        ) = _update_db_info_devicekeys(
            devices_info_json,
            new_info_device_keys_d,
            ["deviceKeys"],
        )

    unmerged_info_add = pd.concat([unmerged_no_device_keys_d, unmerged_device_keys_info], ignore_index=True)
    if not unmerged_info_add.empty:
        unmerged_port_keys_info = unmerged_info_add[unmerged_info_add["portKeys"].notna()]
        unmerged_no_port_keys_info = unmerged_info_add[~unmerged_info_add["portKeys"].notna()]
        new_info_port_keys_d = pd.concat([new_info_port_keys_d, unmerged_port_keys_info], ignore_index=True)

    if not new_info_fm_sw_id_d.empty:
        (
            devices_info_json,
            unmerged_info_fm_sw_id,
        ) = _update_db_info_fmswid_portkeys(devices_info_json, new_info_fm_sw_id_d, ["fmSwitchID", "fmManagerID"])
    if not new_info_port_keys_d.empty:
        (
            devices_info_json,
            unmerged_info_port_keys,
        ) = _update_db_info_fmswid_portkeys(devices_info_json, new_info_port_keys_d, ["portKeys"])
    add_new_info = pd.concat(
        [unmerged_no_port_keys_info, unmerged_info_port_keys, unmerged_info_fm_sw_id], ignore_index=True
    )
    devices_info_json = pd.concat([devices_info_json, add_new_info], ignore_index=True)
    return devices_info_json, moved_devices


def _log_invalid_device_info(info_type: str, device_info: dict[str, str | list | dict | bool | None]):
    """Log the identifier of the invalid device info

    Log the identifier of the invalid device info.

    Args:
        info_type (str): Information type.
            (port_info/device_info/switch_info)
        devices_info (dict[str, str | list | dict | bool | None]): Devices information.

    Returns:
        None

    Raises:
        None
    """

    if info_type == "port_info":
        invalid_fm_port_id = device_info.get("fmPortID")
        logger.info("device_info (FM Port ID: %s) is invalid.", invalid_fm_port_id)
    elif info_type == "device_info":
        invalid_oob_device_id = device_info.get("oobDeviceID")
        logger.info("device_info (OOB Device ID: %s) is invalid.", invalid_oob_device_id)
    else:
        invalid_fm_switch_id = device_info.get("fmSwitchID")
        logger.info("device_info (FM Switch ID: %s) is invalid.", invalid_fm_switch_id)


def _update_db_info_mk_dataframe(
    device_info_list: list,
    manager: str,
    info_type: str,
    invalid_sn_info_json: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate merged data frame.

    Generate merged data frame.

    Args:
        device_info_list (list): List of device information.
        manager (str): Plugin manager ID.
        info_type (str): Information type.
            (port_info/device_info/switch_info)
        invalid_sn_info_json (pandas.DataFrame): Invalid serial number
            information (from invalid serial number configuration file).

    Returns:

        new_info_pci_sn_d (pandas.DataFrame): Device information including PCI serial numbers.
        new_info_cpu_sn_d (pandas.DataFrame): Device information including CPU serial numbers.
        new_info_sw_sn_d (pandas.DataFrame): Device information including switch serial numbers.
        new_info_fm_sw_id_d (pandas.DataFrame): Device information including fmSwitchID information.
        new_info_device_keys_d (pandas.DataFrame): Device information including deviceKeys information.
        new_info_port_keys_d (pandas.DataFrame): Device information including portKeys information.

    Raises:
        None
    """

    merge_by_pci_sn = []
    merge_by_cpu_sn = []
    merge_by_sw_sn = []
    merge_by_fm_sw_id = []
    merge_by_device_keys = []
    merge_by_port_keys = []

    # Divide into multiple data frames depending on the information.
    for device_info in device_info_list:
        device_info = {key: (None if value == "" else value) for key, value in device_info.items()}
        device_info_assembled, merge_by = _assemble_data(device_info, invalid_sn_info_json, manager, info_type)
        if merge_by == HowToMerge.BY_PCI_SERIAL_NUMBER:
            merge_by_pci_sn.append(device_info_assembled)
        elif merge_by == HowToMerge.BY_CPU_SERIAL_NUMBER:
            merge_by_cpu_sn.append(device_info_assembled)
        elif merge_by == HowToMerge.BY_SW_SERIAL_NUMBER:
            # from get_switch_info
            merge_by_sw_sn.append(device_info_assembled)
        elif merge_by == HowToMerge.BY_FM_SW_ID:
            # from get_switch_info
            merge_by_fm_sw_id.append(device_info_assembled)
        elif merge_by == HowToMerge.BY_DEVICE_KEYS:
            merge_by_device_keys.append(device_info_assembled)
        elif merge_by == HowToMerge.BY_PORT_KEYS:
            merge_by_port_keys.append(device_info_assembled)
        else:
            # Invalid info, skip it
            _log_invalid_device_info(info_type, device_info_assembled)

    # Return merge data
    return (
        pd.DataFrame(merge_by_pci_sn).replace("", None),  # new_info_pci_sn_d
        pd.DataFrame(merge_by_cpu_sn).replace("", None),  # new_info_cpu_sn_d
        pd.DataFrame(merge_by_sw_sn).replace("", None),  # new_info_sw_sn_d
        pd.DataFrame(merge_by_fm_sw_id).replace("", None),  # new_info_fm_sw_id_d
        pd.DataFrame(merge_by_device_keys).replace("", None),  # new_info_device_keys_d
        pd.DataFrame(merge_by_port_keys).replace("", None),  # new_info_port_keys_d
    )


def _find_different_info(info: pd.DataFrame) -> list:
    """Find different information and return the index

    Return the index of rows where, for at least one key,
    both the _left and _right values are not NaN and are different from
    each other.

    Args:
        info (pandas.DataFrame): Devices information

    Returns:
        indices(list): index

    Raises:
        None
    """
    left_cols = [col for col in info.columns if col.endswith("_left")]

    condition = pd.Series(False, index=info.index)
    for left_col in left_cols:
        info[left_col] = info[left_col].apply(
            lambda value: str(value) if isinstance(value, (dict, list)) else value if value is not None else None
        )
        right_col = left_col.replace("_left", "_right")
        info[right_col] = info[right_col].apply(
            lambda value: str(value) if isinstance(value, (dict, list)) else value if value is not None else None
        )
        condition |= (info[left_col].notna()) & (info[right_col].notna()) & (info[left_col] != info[right_col])
    indices = info[condition].index.tolist()
    return indices


def _update_db_info_pci_cpu_sw(  # pylint: disable=R0913,R0917
    devices_info_json: pd.DataFrame,
    new_info_d: pd.DataFrame,
    merge_keys: list[str],
    merge_keys_add: list[str],
    next_keys: str,
    info_type: str,
    same_sn_info_d: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Update the devices_info_json data frame and duplicate serial
    number data frame for PCI serial number, CPU serial number
    or switch serial number.

    Extract duplicate serial number information from the
    devices_info_json data frame and place it in a new data frame.

    Args:
        devices_info_json (pandas.DataFrame): Devices information
            (from device ID manager file).
        new_info_d (pandas.DataFrame): New device information
        merge_keys (list): The keys for merging.
        merge_keys_add (list): Merge keys added for merging.
        next_keys(str): Next key.
        info_type (str): Information type.
            (port_info/device_info/switch_info)
        same_sn_info_d (pandas.DataFrame): Duplicate serial number
            information.

    Returns:
        device_info_json(pandas.DataFrame): Devices information.
        same_sn_info_d(pandas.DataFrame): Moved devices information.
        unmerged_next_keys_info(pandas.DataFrame):
            Unmerged devices information(has next merge key).
        unmerged_no_next_keys_info(pandas.DataFrame):
            Unmerged devices information(no next merge key).

    Raises:
        None
    """

    unmerged_next_keys_info = pd.DataFrame()
    unmerged_no_next_keys_info = pd.DataFrame()
    # Extract rows containing duplicate serial number information.
    same_sn = new_info_d[
        new_info_d.duplicated(subset=merge_keys, keep=False) & new_info_d[merge_keys].notna().all(axis=1)
    ]
    same_sn_d = same_sn.copy()
    # Add new column for saving the type of information.
    same_sn_d["info_from"] = info_type

    if not same_sn_d.empty:
        # Remove rows with duplicate serial number information in
        # new_info_d data frame.
        new_info_d = new_info_d.drop(same_sn_d.index)
        # Update data frame of duplicate serial number information.
        same_sn_d.reset_index(drop=True, inplace=True)
        same_sn_info_d = pd.concat([same_sn_info_d, same_sn_d], ignore_index=True)

    # Update devices_info_json data frame.
    if devices_info_json.empty:
        devices_info_json = pd.concat([devices_info_json, new_info_d], ignore_index=True)
    else:
        merge_keys_full = merge_keys + merge_keys_add
        devices_info_json = _convert_keys_to_str_pd(devices_info_json, _to_str_columns)
        new_info_d_str = _convert_keys_to_str_pd(new_info_d, _to_str_columns)
        devices_info_json = pd.merge(
            devices_info_json, new_info_d_str, on=merge_keys_full, how="left", suffixes=("_left", "_right")
        )

        devices_info_json = _post_process_devices_info(devices_info_json)

        unmerged_info = new_info_d[
            ~new_info_d[merge_keys_full]
            .apply(tuple, axis=1)
            .isin(devices_info_json[merge_keys_full].apply(tuple, axis=1))
        ]
        if not unmerged_info.empty:
            same_sn = pd.merge(unmerged_info, devices_info_json, on=merge_keys, how="inner", suffixes=("", "_new"))
            same_sn.index = unmerged_info[unmerged_info["DeviceID"].isin(same_sn["DeviceID"])].index
            unmerged_info = unmerged_info.drop(same_sn.index)
            new_columns = [col for col in same_sn.columns if "_new" in col]
            same_sn.drop(columns=new_columns, inplace=True)
            same_sn["info_from"] = info_type
            same_sn_info_d = pd.concat([same_sn_info_d, same_sn], ignore_index=True)
            unmerged_info = unmerged_info[~unmerged_info.index.isin(same_sn.index)]
            unmerged_next_keys_info = unmerged_info[unmerged_info[next_keys].notna()]
            unmerged_no_next_keys_info = unmerged_info[~unmerged_info[next_keys].notna()]

    return devices_info_json, same_sn_info_d, unmerged_next_keys_info, unmerged_no_next_keys_info


def _update_db_info_devicekeys(
    devices_info_json: pd.DataFrame,
    new_info_d: pd.DataFrame,
    merge_keys: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Update the devices_info_json data frame and duplicate serial
    number data frame for deviceKeys.

    Extract duplicate serial number information from the
    devices_info_json data frame and place it in a new data frame.

    Args:
        devices_info_json (pandas.DataFrame): Devices information
            (from device ID manager file).
        new_info_d (pandas.DataFrame): New device information
        merge_keys (list): The keys for merging.

    Returns:
        device_info_json(pandas.DataFrame): Devices information.
        unmerged_info_d(pandas.DataFrame): Unmerged devices information.

    Raises:
        None
    """

    unmerged_info_d = pd.DataFrame()

    if not new_info_d.empty:
        is_duplicate = new_info_d[merge_keys].duplicated(keep=False)
        original_rows = new_info_d.shape[0]
        new_info_d = new_info_d[~is_duplicate | new_info_d[merge_keys].isna().any(axis=1)].reset_index(drop=True)
        filtered_rows = new_info_d.shape[0]
        if filtered_rows < original_rows:
            logger.warning("Invalid data with duplicate %s within the same plugin have been removed.", merge_keys)

    # Update devices_info_json data frame.
    if devices_info_json.empty:
        devices_info_json = pd.concat([devices_info_json, new_info_d], ignore_index=True)
    else:
        merge_keys_full = merge_keys + []
        devices_info_json = _convert_keys_to_str_pd(devices_info_json, _to_str_columns)
        new_info_d_str = _convert_keys_to_str_pd(new_info_d, _to_str_columns)
        devices_info_json = pd.merge(
            devices_info_json, new_info_d_str, on=merge_keys_full, how="left", suffixes=("_left", "_right")
        )
        devices_info_json = _post_process_devices_info(devices_info_json)

        unmerged_info = new_info_d[
            ~new_info_d[merge_keys_full]
            .apply(tuple, axis=1)
            .isin(devices_info_json[merge_keys_full].apply(tuple, axis=1))
        ]
        unmerged_info_d = unmerged_info.copy()

    return devices_info_json, unmerged_info_d


def _update_db_info_fmswid_portkeys(
    devices_info_json: pd.DataFrame,
    new_info_d: pd.DataFrame,
    merge_keys: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Update the devices_info_json data frame and duplicate serial
    number data frame for portKeys or fmSwitchID.

    Extract duplicate serial number information from the
    devices_info_json data frame and place it in a new data frame.

    Args:
        devices_info_json (pandas.DataFrame): Devices information
            (from device ID manager file).
        new_info_d (pandas.DataFrame): New device information
        merge_keys (list): The keys for merging.

    Returns:
        device_info_json(pandas.DataFrame): Devices information.
        unmerged_info_d(pandas.DataFrame): Unmerged devices information.

    Raises:
        None
    """

    unmerged_info_d = pd.DataFrame()

    if not new_info_d.empty:
        new_info_d_str = _convert_keys_to_str_pd(new_info_d, _to_str_columns)
        is_duplicate = new_info_d_str[merge_keys].duplicated(keep=False)
        original_rows = new_info_d.shape[0]
        new_info_d = new_info_d[~is_duplicate | new_info_d[merge_keys].isna().any(axis=1)].reset_index(drop=True)
        filtered_rows = new_info_d.shape[0]
        if filtered_rows < original_rows:
            logger.warning("Invalid data with duplicate %s within the same plugin have been removed.", merge_keys)

    # Update devices_info_json data frame.
    if devices_info_json.empty:
        devices_info_json = pd.concat([devices_info_json, new_info_d], ignore_index=True)
    else:
        devices_info_json_bak = devices_info_json.copy()
        devices_info_json = _convert_keys_to_str_pd(devices_info_json, _to_str_columns)
        new_info_d_str = _convert_keys_to_str_pd(new_info_d, _to_str_columns)
        devices_info_json = pd.merge(
            devices_info_json, new_info_d_str, on=merge_keys, how="left", suffixes=("_left", "_right")
        )

        filtered_df = devices_info_json.drop(
            columns=[
                "DeviceID_left",
                "DeviceID_right",
                "valid_left",
                "valid_right",
                "fmValid_left",
                "fmValid_right",
                "fmPortID_bak_left",
                "fmPortID_bak_right",
                "connectedFmSwitchID_bak_left",
                "connectedFmSwitchID_bak_right",
                "fmManagerID_bak_left",
                "fmManagerID_bak_right",
                "oobManagerID_bak_left",
                "oobManagerID_bak_right",
            ]
        )
        devices_info_json = _post_process_devices_info(devices_info_json)
        index = _find_different_info(filtered_df)
        devices_info_json_bak.columns = devices_info_json.columns
        devices_info_json.iloc[index] = devices_info_json_bak.iloc[index].astype(devices_info_json.dtypes)
        devices_info_json_valid = devices_info_json.query("valid == True")

        unmerged_info = new_info_d[
            ~new_info_d[merge_keys].apply(tuple, axis=1).isin(devices_info_json_valid[merge_keys].apply(tuple, axis=1))
        ]
        unmerged_info_d = unmerged_info.copy()

    return devices_info_json, unmerged_info_d


def _post_process_devices_info(devices_info_json: pd.DataFrame) -> pd.DataFrame:
    """Post-processing dataframe after merging.

    Determine the values of DeviceID and other keys

    Args:
        devices_info_json (pandas.DataFrame): Devices information
            (from device ID manager file).

    Returns:
        device_info_json(pandas.DataFrame): Devices information.

    Raises:
        None
    """
    new_column_name = ""
    for column in devices_info_json.columns:
        # If column does not end with "_left" or column includes "_bak",
        # skip the column.
        if column.endswith("_left") is False or "_bak" in column:
            continue

        left_column = column
        right_column = column.replace("_left", "_right")
        new_column_name = right_column[:-6]
        left_backup_column = new_column_name + "_bak" + "_left"
        right_backup_column = new_column_name + "_bak" + "_right"

        # If valid_right is NaN,
        # adopt the value of xxxx_left.
        if column.startswith("DeviceID_"):
            # If DeviceID,
            # basically, the value of xxxx_left is adopted.
            devices_info_json[new_column_name] = devices_info_json[left_column]
            # If valid_left is NaN,
            # and the value of valid_right is True,
            # adopt the value of xxxx_right.
            devices_info_json.loc[
                devices_info_json["valid_left"].isnull() & devices_info_json["valid_right"].astype(bool),
                new_column_name,
            ] = devices_info_json[right_column]
        elif column.startswith("fmPortID_") or column.startswith("connectedFmSwitchID_"):
            # Basically, the value of fmManagerID_right is adopted.
            devices_info_json[new_column_name] = devices_info_json[right_backup_column]
            # If fmPortID_right(or connectedFmSwitchID_right) is
            # NaN, adopt the value of fmPortID_bak_left
            # (or connectedFmSwitchID_left_bak).
            devices_info_json.loc[
                devices_info_json["fmPortID_right"].isnull(),
                new_column_name,
            ] = devices_info_json[left_backup_column]
            # If fmPortID_left(or connectedFmSwitchID_left) is not
            # NaN, and fmPortID_right(or connectedFmSwitchID_right)
            # is not NaN,
            # valid_left is True
            # adopt the value of concatenating
            # fmPortID_left(or connectedFmSwitchID_bak_left) and
            # fmPortID_right(or connectedFmSwitchID_bak_right).
            condition = (
                devices_info_json["fmPortID_right"].notnull()
                & devices_info_json["fmPortID_left"].notnull()
                & devices_info_json["valid_left"].astype(bool)
            )
            devices_info_json.loc[condition, new_column_name] = devices_info_json.loc[
                condition, left_backup_column
            ].combine(devices_info_json.loc[condition, right_backup_column], lambda arg1, arg2: {**arg1, **arg2})
        elif column.startswith("fmManagerID_"):
            # Basically, the value of fmManagerID_bak_right is
            # adopted.
            devices_info_json[new_column_name] = devices_info_json[right_backup_column]
            # If the value of fmManagerID_right is NaN,
            # or valid_right is NaN,
            # adopt the value of fmManagerID_bak_left.
            devices_info_json.loc[
                devices_info_json[right_column].isnull() | (devices_info_json["valid_right"].isnull()),
                new_column_name,
            ] = devices_info_json[left_backup_column]
            # If fmPortID_left is not NaN, and fmPortID_right
            # is not NaN,
            # valid_left is True
            # adopt the value of concatenating
            # fmManagerID_bak_left and fmManagerID_bak_right.
            condition = (
                devices_info_json[left_column].notnull()
                & devices_info_json[right_column].notnull()
                & devices_info_json["valid_left"].astype(bool)
            )
            devices_info_json.loc[condition, new_column_name] = devices_info_json.loc[condition].apply(
                lambda row, left, right: list(set(row[left] + row[right])),
                axis=1,
                args=[left_backup_column, right_backup_column],
            )
        elif column.startswith("oobManagerID_"):
            # Basically, the value of oobManagerID_bak_right is
            # adopted.
            devices_info_json[new_column_name] = devices_info_json[right_backup_column]
            # If the value of oobManagerID_right is NaN,
            # adopt the value of oobManagerID_bak_left.
            devices_info_json.loc[
                devices_info_json[right_column].isnull(),
                new_column_name,
            ] = devices_info_json[left_backup_column]
        elif column.startswith("fmValid_"):
            # If fmValid,
            # Set to True if it is True even once.
            devices_info_json[new_column_name] = devices_info_json[left_column].fillna(False).astype(
                bool
            ) | devices_info_json[right_column].fillna(False).astype(bool)
        else:
            # If others,
            # basically, the value of xxxx_right is adopted.
            devices_info_json[new_column_name] = devices_info_json[right_column]
            # If the value of xxxx_right is NaN,
            # or valid_right is NaN,
            # adopt the value of xxxx_left.
            devices_info_json.loc[
                devices_info_json[right_column].isnull() | (devices_info_json["valid_right"].isnull()),
                new_column_name,
            ] = devices_info_json[left_column]
    # If the data on the left side is the same as the data on the right
    # side, recover the data from _bak.
    for key in ["fmManagerID", "oobManagerID", "fmPortID", "connectedFmSwitchID"]:
        if (key + "_left") not in devices_info_json.columns:
            devices_info_json[key] = devices_info_json[key + "_bak_left"]

    devices_info_json = devices_info_json.loc[:, ~devices_info_json.columns.str.contains("_bak")]
    devices_info_json.loc[:, "valid"] = devices_info_json["valid"].replace({"True": True, "False": False})
    return devices_info_json.reindex(columns=all_keys)


def _convert_keys_to_str_pd(df: pd.DataFrame, target_keys: list) -> pd.DataFrame:
    """Converts the target keys to strings and return the new dataframe.
    Converts the target keys to strings for merging dataframes.

    Args:
        df (pandas.DataFrame): The dictionary before processing.
        target_keys (list): The list of target keys.

    Returns:
        new_df (pd.DataFrame): The dictionary after processing.

    Raises:
        None
    """
    new_df = df.copy()
    for column in target_keys:
        new_df[column + "_bak"] = new_df[column]
        new_df[column] = new_df[column].apply(
            lambda value: str(value) if isinstance(value, (dict, list)) else value if value is not None else None
        )
        new_df[column] = new_df[column].apply(
            lambda x: None if x is not None and not (re.search(r"\[([^\]]+)\]", x)) else x
        )

    return new_df


def _convert_obj_to_str(d: dict, target_keys: list) -> dict:
    """Converts the target keys to strings.

    If the key exists and its corresponding value is not empty,
    it converts the value to a string.
    If the type of the value is a dict (dictionary),
    sorts it by the key names first and then it converts the value to a string.
    If the key exists but its corresponding value is empty,
    it sets the value to None.

    Args:
        d(Dict): The dictionary before processing.
        target_keys(list): The list of target keys.

    Returns:
        d(Dict):The dictionary after processing.

    Raises:
        None
    """
    for key in target_keys:
        if key in d:
            if d[key]:
                if isinstance(d[key], dict):
                    sorted_dict = sorted(d[key].items(), key=lambda x: x[0])
                    d[key].clear()
                    d[key].update(sorted_dict)
                d[key] = str(d[key])
            else:
                d[key] = None
    return d


def assign_fm_device_id(
    devices_info_json: pd.DataFrame, moved_devices: pd.DataFrame, invalid_sn_info_json: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Assign IDs to devices of the specified type.

    Assign IDs to devices of the specified type.

    Args:
        devices_info_json (pandas.DataFrame): Devices information
            (from device ID manager file).
        moved_devices (pandas.DataFrame): Moved devices information.
        invalid_sn_info_json (pandas.DataFrame): Invalid serial number
            information (from invalid serial number configuration file).

    Returns:
        device_info_json (pandas.DataFrame): Devices information
        moved_devices (pandas.DataFrame): Moved devices information.

    Raises:
        None
    """
    # Get the list of the specified managers(list of IDs)
    manager_type = ManagerType.FM.value
    manager_list = get_manager_list(manager_type)
    # Check whether the list of managers is empty or not
    if not manager_list:
        logger.debug("No Manager ID of %s.", manager_type)
        return devices_info_json, moved_devices
    # Loop through the list of plugin manger IDs(return value of
    # get_manager_list())
    for manager in manager_list:
        # Get plugin class instance
        instance = _retrieve_fm_plugin_safely(manager)
        if instance is None:
            continue

        # Get list of device info by get_port_info().
        device_info_list = _get_fm_port_info(instance, manager)
        if device_info_list is not None:
            info_type = "port_info"
            devices_info_json, moved_devices = _update_db_info(
                device_info_list,
                manager,
                info_type,
                devices_info_json,
                moved_devices,
                invalid_sn_info_json,
            )

        # Get list of device info by get_switch_info()
        device_info_list = _get_fm_switch_info(instance, manager)
        if device_info_list is not None:
            info_type = "switch_info"
            devices_info_json, moved_devices = _update_db_info(
                device_info_list,
                manager,
                info_type,
                devices_info_json,
                moved_devices,
                invalid_sn_info_json,
            )

    return devices_info_json, moved_devices


def assign_oob_device_id(
    devices_info_json: pd.DataFrame, moved_devices: pd.DataFrame, invalid_sn_info_json: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Assign IDs to devices of the specified type.

    Assign IDs to devices of the specified type.

    Args:
        devices_info_json (pandas.DataFrame): Devices information
            (from device ID manager file).
        moved_devices (pandas.DataFrame): Moved devices information.
        invalid_sn_info_json (pandas.DataFrame): Invalid serial number
            information (from invalid serial number configuration file).

    Returns:
        device_info_json (pandas.DataFrame): Devices information
        moved_devices (pandas.DataFrame): Moved devices information.

    Raises:
        None
    """
    # Get the list of the specified managers(list of IDs)
    manager_type = ManagerType.OOB.value
    manager_list = get_manager_list(manager_type)
    # Check whether the list of managers is empty or not
    if not manager_list:
        logger.debug("No Manager ID of %s.", manager_type)
        return devices_info_json, moved_devices
    # Loop through the list of plugin manger IDs(return value of
    # get_manager_list())
    for manager in manager_list:
        # Get plugin class instance
        instance = _retrieve_oob_plugin_safely(manager)
        if instance is None:
            continue

        # Get list of device info by get_device_info().
        device_info_list = _get_oob_device_info(instance, manager)
        if device_info_list is not None:
            info_type = "device_info"
            devices_info_json, moved_devices = _update_db_info(
                device_info_list,
                manager,
                info_type,
                devices_info_json,
                moved_devices,
                invalid_sn_info_json,
            )

    return devices_info_json, moved_devices


def _retrieve_fm_plugin_safely(manager: str) -> FMPluginBase | None:
    """Get FM plugin class instance.

    Get FM plugin class instance.

    Args:
        manager (str): Specified managers

    Returns:
        instance (FMPluginBase): Plugin class instance.
        None: Failed to get the specified plugin instance.

    Raises:
        None
    """

    instance = None
    manager_type = ManagerType.FM.value
    try:
        # Get plugin class instance
        instance = get_fm_plugin(manager)
    # If an error occurs in get_plugin(),
    # do not finish this function,
    # and skip to the next plugin manger ID
    except (
        Err.APIUsageHWControlError,
        Err.ManagerIDHWControlError,
        Err.ConfigurationHWControlError,
        Err.UnexpectedExceptionHWControlError,
    ):
        logger.warning("Failed to get Plugin class instance (%s:%s).", manager_type, manager, exc_info=True)
    # Since the plugin may be developed by a vendor outside
    # of NEC, we do not know what kind of exception will be
    # thrown, so we also except exception.
    except Exception:  # pylint: disable=W0718
        logger.warning(
            "Failed to get Plugin class instance due to other error (%s:%s).",
            manager_type,
            manager,
            exc_info=True,
        )

    return instance


def _retrieve_oob_plugin_safely(manager: str) -> OOBPluginBase | None:
    """Get OOB plugin class instance.

    Get OOB plugin class instance.

    Args:
        manager (str): Specified managers

    Returns:
        instance (OOBPluginBase): Plugin class instance.
        None: Failed to get the specified plugin instance.

    Raises:
        None
    """

    instance = None
    manager_type = ManagerType.OOB.value
    try:
        # Get plugin class instance
        instance = get_oob_plugin(manager)
    # If an error occurs in get_plugin(),
    # do not finish this function,
    # and skip to the next plugin manger ID
    except (
        Err.APIUsageHWControlError,
        Err.ManagerIDHWControlError,
        Err.ConfigurationHWControlError,
        Err.UnexpectedExceptionHWControlError,
    ):
        logger.warning("Failed to get Plugin class instance (%s:%s).", manager_type, manager, exc_info=True)
    # Since the plugin may be developed by a vendor outside
    # of NEC, we do not know what kind of exception will be
    # thrown, so we also except exception.
    except Exception:  # pylint: disable=W0718
        logger.warning(
            "Failed to get Plugin class instance due to other error (%s:%s).",
            manager_type,
            manager,
            exc_info=True,
        )

    return instance


def _get_fm_port_info(instance: FMPluginBase, manager: str) -> list | None:
    """Get list of port info.

    Get list of port info with get_port_info() in case of FM.

    Args:
        instance (FMPluginBase): Plugin class instance
        manager (str): Specified managers

    Returns:
        device_info_list (list): List of device info
        None: Failed to get the device info.

    Raises:
        None
    """

    # If manager type is FM,
    # get device information list by get_port_info()
    try:
        fm_port_info_list = instance.get_port_info()["data"]
        device_info_list = [port.model_dump(by_alias=True) for port in fm_port_info_list]
        device_info_list = [_convert_obj_to_str(d, ["deviceKeys", "portKeys"]) for d in device_info_list]
    # If an error occurs in get_port_info() ,
    # do not finish this function,
    # and skip to the next plugin manger ID
    # Since the plugin may be developed by a vendor outside
    # of NEC, we do not know what kind of exception will be
    # thrown, so we except Exception.
    except Exception:  # pylint: disable=W0718
        device_info_list = None
        logger.warning("Failed to get port info of (%s).", manager, exc_info=True)

    return device_info_list


def _get_oob_device_info(instance: OOBPluginBase, manager: str) -> list | None:
    """Get list of device info.

    Get list of device info with get_device_info() in case of OOB.

    Args:
        instance (OOBPluginBase): Plugin class instance
        manager (str): Specified managers

    Returns:
        device_info_list (list): List of device info
        None: Failed to get the device info.

    Raises:
        None
    """

    # If manager type is OOB,
    # get device information list by get_device_info()
    try:
        oob_device_info_list = instance.get_device_info()
        device_info_list = [device.model_dump(by_alias=True) for device in oob_device_info_list]
        device_info_list = [_convert_obj_to_str(d, ["deviceKeys", "portKeys"]) for d in device_info_list]
    # If an error occurs in get_device_info(),
    # do not finish this function,
    # and skip to the next plugin manger ID
    # Since the plugin may be developed by a vendor outside
    # of NEC, we do not know what kind of exception will be
    # thrown, so we except Exception.
    except Exception:  # pylint: disable=W0718
        device_info_list = None
        logger.warning("Failed to get device info of (%s).", manager, exc_info=True)

    return device_info_list


def _get_fm_switch_info(instance: FMPluginBase, manager: str) -> list | None:
    """Get list of switch info.

    Get list of switch info with get_switch_info() in case of FM.

    Args:
        instance (FMPluginBase): Plugin class instance
        manager (str): Specified managers

    Returns:
        device_info_list (list): List of device info
        None: Failed to get the device info.

    Raises:
        None
    """

    device_info_list = []
    try:
        fm_switch_info_list = instance.get_switch_info()["data"]
        device_info_list = [switch.model_dump(by_alias=True) for switch in fm_switch_info_list]
    # If an error occurs in get_switch_info() ,
    # do not finish this function,
    # and skip to the next plugin manger ID
    # Since the plugin may be developed by a vendor outside
    # of NEC, we do not know what kind of exception will be
    # thrown, so we except Exception.
    except Exception:  # pylint: disable=W0718
        device_info_list = None
        logger.warning("Failed to get switch info of (%s).", manager, exc_info=True)

    return device_info_list


def update_same_sn_devices(devices_info_json: pd.DataFrame, moved_devices: pd.DataFrame) -> pd.DataFrame:
    """Merge information in the list of candidate mobile devices to
       the Device ID Management file.

    Args:
        devices_info_json (pandas.DataFrame): Devices information
            (from device ID manager file).
        moved_devices (pandas.DataFrame): Moved devices information.

    Returns:
        device_info_json(pandas.DataFrame): Devices information.

    Raises:
        None
    """
    # Split into two data frames(from fm and oob)
    moved_devices_fm = moved_devices[moved_devices["info_from"] != "device_info"]
    moved_devices_oob = moved_devices[moved_devices["info_from"] == "device_info"]
    moved_devices_fm = moved_devices_fm.drop(columns=["info_from"])
    moved_devices_oob = moved_devices_oob.drop(columns=["info_from"])

    # Separate fm data frame(by fmManagerID)
    grouped = moved_devices_fm.groupby(moved_devices_fm["fmManagerID"].apply(tuple))
    separated_fm_dfs = [group.reset_index(drop=True) for key, group in grouped]

    # set merge_keys for fm: = _check_items_pci + _check_items_cpu + _check_items_switch
    merge_keys = _check_items_pci + _check_items_cpu + _check_items_switch

    # Merge the rows with the same serial number in the same FM DataFrame
    for df in separated_fm_dfs:
        df["group_key_sn"] = (
            df["PCIeDeviceSerialNumber"].combine_first(df["CPUSerialNumber"]).combine_first(df["switchSerialNumber"])
        )
        df["group_key_md"] = df["PCIeDeviceId"].combine_first(df["CPUModel"]).combine_first(df["switchModel"])
        df["group_key_Mf"] = (
            df["PCIeVendorId"].combine_first(df["CPUManufacturer"]).combine_first(df["switchManufacturer"])
        )
        agg_dict = {
            "fmManagerID": lambda x: list(set(sum(x.tolist(), []))),
            "fmPortID": lambda x: {
                k: sum([d.get(k, []) for d in x if d is not None], [])
                for k in {k for d in x if d is not None for k in d.keys()}
            },
            "connectedFmSwitchID": lambda x: {
                k: sum([d.get(k, []) for d in x if d is not None], [])
                for k in {k for d in x if d is not None for k in d.keys()}
            },
        }
        for col in df.columns:
            if col not in agg_dict and col not in ["group_key_sn", "group_key_md", "group_key_Mf"]:
                agg_dict[col] = lambda x: x.iloc[0]
        df = df.groupby(["group_key_sn", "group_key_md", "group_key_Mf"]).agg(agg_dict).reset_index()
        df = df.drop(columns=["group_key_sn", "group_key_md", "group_key_Mf"])
        df_bak = df
        devices_info_json = _convert_keys_to_str_pd(devices_info_json, _to_str_columns)
        df = _convert_keys_to_str_pd(df, _to_str_columns)
        devices_info_json = pd.merge(devices_info_json, df, on=merge_keys, how="left", suffixes=("_left", "_right"))
        unmerged_info = df_bak[
            ~df_bak[merge_keys].apply(tuple, axis=1).isin(devices_info_json[merge_keys].apply(tuple, axis=1))
        ]
        devices_info_json = _post_process_devices_info(devices_info_json)
        devices_info_json = pd.concat([devices_info_json, unmerged_info], ignore_index=True)
    # Split into two type data frames(has same serial number and no same serial number)
    same_sn_oob_pci = moved_devices_oob[
        moved_devices_oob.duplicated(subset=_check_items_pci, keep=False)
        & moved_devices_oob[_check_items_pci].notna().all(axis=1)
    ]
    moved_devices_oob = moved_devices_oob.drop(same_sn_oob_pci.index)
    same_sn_oob_cpu = moved_devices_oob[
        moved_devices_oob.duplicated(subset=_check_items_cpu, keep=False)
        & moved_devices_oob[_check_items_cpu].notna().all(axis=1)
    ]
    moved_devices_oob = moved_devices_oob.drop(same_sn_oob_cpu.index)

    moved_devices_oob_same_sn = pd.concat([same_sn_oob_pci, same_sn_oob_cpu], ignore_index=True)

    # set merge_keys for oob: = _check_items_pci + _check_items_cpu
    merge_keys = _check_items_pci + _check_items_cpu
    if not moved_devices_oob.empty:
        devices_info_json = _convert_keys_to_str_pd(devices_info_json, _to_str_columns)
        moved_devices_oob = _convert_keys_to_str_pd(moved_devices_oob, _to_str_columns)
        devices_info_json = pd.merge(
            devices_info_json, moved_devices_oob, on=merge_keys, how="left", suffixes=("_left", "_right")
        )
        devices_info_json = _post_process_devices_info(devices_info_json)

    # update merge_keys: = oob_merge_keys + _check_items_device_add
    merge_keys = merge_keys + _check_items_device_add
    # Merge data frame
    if not moved_devices_oob_same_sn.empty and not devices_info_json.empty:
        devices_info_json = _convert_keys_to_str_pd(devices_info_json, _to_str_columns)
        moved_devices_oob_same_sn = _convert_keys_to_str_pd(moved_devices_oob_same_sn, _to_str_columns)
        devices_info_json = pd.merge(
            devices_info_json,
            moved_devices_oob_same_sn,
            on=merge_keys,
            how="left",
            suffixes=("_left", "_right"),
        )
        devices_info_json = _post_process_devices_info(devices_info_json)

    return devices_info_json

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

import os
import traceback
import threading
import uuid

import json
import pandas as pd
from app.common.deviceIdManager.device_id_manager import do_assign_device_id
from app.common.deviceIdManager.device_id_manager import update_same_sn_devices
from app.common.deviceIdManager.device_id_manager import all_keys

from app.common.utils.file_location_settings import FileLocationSettings as path_setting

import app.common.messages.message as msg
from app.common.utils.log import LOGGER
import app.common.constants as con
import app.common.basic_exceptions as Err

_DEVICE_ID_MANAGER_FILE_NAME = "device_id_info.json"
_INVALID_SERIAL_NUMBER_FILE_NAME = "invalid_serial_number.json"

device_id_info_lock = threading.Lock()
id_to_info_lock = threading.Lock()
id_to_info = {}


def _change_info_to_new_type(info: pd.DataFrame) -> pd.DataFrame:
    """Change old type information to new type information

    This function converts the old type of info to the new type to
    ensure compatibility.
    The differences are as follows:
        fmPortID: str (old) -> dict (new)
        connectedFmSwitchID: str (old) -> dict (new)
        fmManagerID: str (old) -> list (new)
        oobManagerID: str (old) -> list (new)

    Args:
        info (pd.DataFrame):
            Information.

    Returns:
        info
            New type information

    Raises:
        TypeError/KeyError:
            When there is an error in the contents of the
            device_id_info.json file.
    """
    # Rename the columns if they need to be renamed
    # DeviceKeys -> deviceKeys
    # PortKeys -> portKeys
    # DeviceType -> deviceType
    info = info.rename(
        columns={
            "DeviceKeys": "deviceKeys",
            "PortKeys": "portKeys",
            "DeviceType": "deviceType",
        }
    )

    fm_manager_id_is_list = info["fmManagerID"].apply(lambda x: isinstance(x, list)).any()
    oob_manager_id_is_list = info["oobManagerID"].apply(lambda x: isinstance(x, list)).any()

    if fm_manager_id_is_list or oob_manager_id_is_list:
        # It is new type
        return info

    LOGGER.debug(msg.BaseLogMessage(detail=f"[{__name__}] Change info to new type.").to_json_encodable())

    # It is old type, change to new type
    info = info.assign(new_fmPortID=lambda x: [{}] * len(x), new_connectedFmSwitchID=lambda x: [{}] * len(x))
    condition = info["fmManagerID"].notna()
    info.loc[condition, "new_fmPortID"] = info.loc[condition].apply(
        lambda row: {row["fmManagerID"]: [row["fmPortID"]] if pd.notna(row["fmPortID"]) else []}, axis=1
    )
    info.loc[condition, "new_connectedFmSwitchID"] = info.loc[condition].apply(
        lambda row: {row["fmManagerID"]: [row["connectedFmSwitchID"]] if pd.notna(row["connectedFmSwitchID"]) else []},
        axis=1,
    )
    info["new_fmManagerID"] = info["fmManagerID"].apply(lambda x: [x] if x is not None else [])
    info["new_oobManagerID"] = info["oobManagerID"].apply(lambda x: [x] if x is not None else [])

    # Delete old columns
    info = info.drop(columns=["fmPortID", "connectedFmSwitchID", "fmManagerID", "oobManagerID"])
    # Rename columns
    info = info.rename(
        columns={
            "new_fmPortID": "fmPortID",
            "new_connectedFmSwitchID": "connectedFmSwitchID",
            "new_fmManagerID": "fmManagerID",
            "new_oobManagerID": "oobManagerID",
        }
    )

    return info.reindex(columns=all_keys)


def _is_valid_uuid(identifier: str) -> bool:
    """valid uuid

    This function provides a UUID validation check
    for the specified identifier.

    Args:
        identifier (str):
            Identifier to be checked for UUID validation.

    Returns:
        bool
            True:
                If the specified identifier is a valid UUID.
            False:
                If the specified identifier is a valid UUID.

    Raises:
        None
    """
    try:
        uuid.UUID(identifier, version=4)
        return True
    except (ValueError, AttributeError):
        return False


def _update_id_to_info(devices_info_json: pd.DataFrame):
    """Update global value.

    This function provides the functionality to
    Update global value id_to_info.

    Args:
        devices_info_json (pandas.DataFrame): Devices information .

    Returns:
        None.

    Raises:
        None.

    """
    global id_to_info  # pylint: disable=W0603
    # Update global value
    with id_to_info_lock:
        if not devices_info_json.empty:
            id_to_info = devices_info_json.set_index("DeviceID").to_dict(orient="index")
        else:
            id_to_info = {}


def _update_json_file(devices_info_json: pd.DataFrame, json_file_path: str):
    """Update device ID info file.

    This function provides the functionality to
    Update device ID info file.

    Args:
        devices_info_json (pandas.DataFrame): Devices information .
        json_file_path (str): Path of json file.

    Returns:
        DeviceIdFileNotFoundHwControlError:
            If the device_id_info.json file did not exist
            in "/app/common/device_id_manager/".

    Raises:
        DeviceIdFileNotFoundHwControlError:.

    """
    # Update json file
    tmp_json_file = os.path.join(json_file_path + ".tmp")
    try:
        with open(tmp_json_file, "w", encoding="utf-8") as f:
            devices_info_json.to_json(f, orient="records", lines=False, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_json_file, json_file_path)
    except (FileNotFoundError, PermissionError, OSError) as exc:
        LOGGER.error(
            msg.BaseLogMessage(detail=f"[{__name__}] Failed to update Device ID Management File.").to_json_encodable()
        )
        raise Err.DeviceIdFileNotFoundHwControlError from exc


def _read_json_file(path: str) -> dict[str, dict[str, str | list | dict]]:
    """Read device ID info file.

    This function provides the functionality to
    read and return the contents of the device_id_info.json file.

    Args:
        path (str): device_id_info.json file's Path.

    Returns:
        obtained_data(pandas.DataFrame): file's contents.

    Raises:
        DeviceIdFileIncorrectHwControlError:
            When there is an error in the contents of the
            device_id_info.json file.
        DeviceIdFileNotFoundHwControlError:
            If the device_id_info.json file did not exist
            in "/app/common/device_id_manager/".
            If permission is inappropriate.

    """
    obtained_data = {}
    try:
        json_info = pd.read_json(path, dtype="object")
        json_info = json_info.replace(["NaN", "nan", "None", ""], None)
        if not json_info.empty:  # pylint: disable=E1101
            json_info = _change_info_to_new_type(json_info)
            obtained_data = json_info.set_index("DeviceID").to_dict(orient="index")
    except (ValueError, TypeError) as exc:
        LOGGER.error(
            msg.BaseLogMessage(detail=f"[{__name__}] The Device ID Management File is incorrect.").to_json_encodable()
        )
        raise Err.DeviceIdFileIncorrectHwControlError from exc
    except PermissionError as exc:
        LOGGER.error(
            msg.BaseLogMessage(
                detail=f"[{__name__}] The Device ID Management File was not found or there was a permission error."
            ).to_json_encodable()
        )
        raise Err.DeviceIdFileNotFoundHwControlError from exc
    except FileNotFoundError as exc:
        pass

    return obtained_data


def _get_devices_info() -> dict[str, dict[str, str | list | dict]]:
    """get devices info.

    This function provides the functionality to
    get and return devices info from file(device_id_info.json)
    or global value(id_to_info).

    Args:
        None

    Returns:
        devices info(dict): devices info.
        None: Data does not exist

    Raises:
        None
    """
    global id_to_info  # pylint: disable=W0603

    with id_to_info_lock:
        if id_to_info:
            return id_to_info.copy()
    with device_id_info_lock:
        with id_to_info_lock:
            if not id_to_info:
                dir_path = path_setting().data_file_dir
                device_id_manager_file_path = os.path.join(dir_path, _DEVICE_ID_MANAGER_FILE_NAME)
                LOGGER.debug(
                    msg.BaseLogMessage(
                        detail=f"[{__name__}] Path of device id manager file is {device_id_manager_file_path}."
                    ).to_json_encodable()
                )
                id_to_info = _read_json_file(device_id_manager_file_path)
            return id_to_info.copy()


def device_id_to_fm_port_id(device_id: str) -> str | None:
    """API function of convert device_id to fm_port_id.

    This API function provides the functionality to convert
    device_id to fm_port_id.

    This API function is temporary and serves as an API for
    compatibility with processing up to iteration 11.
    All callers are scheduled to be deprecated after switching to the
    new API.

    Args:
        device_id (str):
            Identifier that uniquely identifies the device.

    Returns:
        str/None:
            str:
                fm_port_id
            None:
                Data does not exist.

    Raises:
        ApiUsageHwControlError:
            If the specified device_id is an invalid UUID.

        InvalidTypeDeviceIdHwControlError:
            If the specified device_id is the device_id of a switch.

        DeviceIdNotFoundHwControlError:
            If the specified device_id does not exist in the file.
            If specified device has been disabled.

        Raise the following exception thrown from _read_json_file as is.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_id_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_id_info.json file did not exist
                in "/app/common/device_id_manager/".
    """
    if _is_valid_uuid(identifier=device_id) is False:
        raise Err.ApiUsageHwControlError
    device = _get_devices_info().get(device_id, {})
    if device.get("valid") is True:
        if device.get("deviceType") == con.DeviceType.SWITCH.value:
            # If the specified device is a switch
            raise Err.InvalidTypeDeviceIdHwControlError
        info = device.get("fmPortID", {})
        result = None
        if info:
            first_key = next(iter(info))
            if info[first_key]:
                result = info[first_key][0]
        return result
    raise Err.DeviceIdNotFoundHwControlError


def device_id_to_fm_port_id_multi_hostport(device_id: str, fm_manager_id: str) -> list:
    """API function of convert device_id to fm_port_id.

    This API function provides the functionality to convert
    device_id to fm_port_id.

    Args:
        device_id (str):
            Identifier that uniquely identifies the device.
        fm_manager_id (str):
            Identifier that uniquely identifies the FM plug-in.

    Returns:
        str/None:
            str:
                fm_port_id
            empty list:
                Data does not exist.

    Raises:
        ApiUsageHwControlError:
            If the specified device_id is an invalid UUID.

        InvalidTypeDeviceIdHwControlError:
            If the specified device_id is the device_id of a switch.

        DeviceIdNotFoundHwControlError:
            If the specified device_id does not exist in the file.
            If specified device has been disabled.

        Raise the following exception thrown from _read_json_file as is.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_id_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_id_info.json file did not exist
                in "/app/common/device_id_manager/".
    """
    if _is_valid_uuid(identifier=device_id) is False:
        raise Err.ApiUsageHwControlError
    device = _get_devices_info().get(device_id, {})
    if device.get("valid") is True:
        if device.get("deviceType") == con.DeviceType.SWITCH.value:
            # If the specified device is a switch
            raise Err.InvalidTypeDeviceIdHwControlError
        result = device.get("fmPortID", {}).get(fm_manager_id, [])
        return result
    raise Err.DeviceIdNotFoundHwControlError


def fm_port_id_to_device_id(fm_port_id: str, fm_manager_id: str) -> str | None:
    """API function of convert fm_port_id to device_id.

    This API function provides the functionality to convert
    fm_port_id to device_id.

    Args:
        fm_port_id (str):
            Identifier that uniquely identifies the device in FM.
        fm_manager_id (str):
            Identifier that uniquely identifies the FM plug-in.

    Returns:
        str/None:
            str:
                device_id.
            None:
                If device has been disabled.
                If device of specified data does not exist.

    Raises:
        Raise the following exception thrown from _read_json_file as is.
            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_id_info.json file.
            DeviceIdFileNotFoundHwControlError:
                If the device_id_info.json file did not exist
                in "/app/common/device_id_manager/".
    """
    id_to_info_copy = _get_devices_info()
    for device_id, device in id_to_info_copy.items():
        if (
            device.get("valid") is True
            and fm_manager_id in device.get("fmManagerID")
            and fm_port_id in device.get("fmPortID", {}).get(fm_manager_id, [])
        ):
            return device_id
    return None


def device_id_to_device_type(device_id: str) -> str | None:
    """API function of convert device_id to device_type.

    This API function provides the functionality to convert
    device_id to device_type.

    Args:
        device_id (str):
            Identifier that uniquely identifies the device.

    Returns:
        str/None:
            str:
                device_type.
            None:
                Data does not exist.

    Raises:
        ApiUsageHwControlError:
            If the specified device_id is an invalid UUID.

        DeviceIdNotFoundHwControlError:
            If the specified device_id does not exist in the file.
            If specified device has been disabled.

        Raise the following exception thrown from _read_json_file as is.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_id_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_id_info.json file did not exist
                in "/app/common/device_id_manager/".
    """
    if _is_valid_uuid(identifier=device_id) is False:
        raise Err.ApiUsageHwControlError
    device = _get_devices_info().get(device_id, {})
    if device.get("valid") is True:
        return device.get("deviceType")
    raise Err.DeviceIdNotFoundHwControlError


def device_id_to_oob_device_id(device_id: str) -> str | None:
    """API function of convert device_id to oob_device_id.

    This API function provides the functionality to convert
    device_id to oob_device_id.

    Args:
        device_id (str):
            Identifier that uniquely identifies the device.

    Returns:
        str/None:
            str:
                oob_device_id.
            None:
                Data does not exist.

    Raises:
        ApiUsageHwControlError:
            If the specified device_id is an invalid UUID.

        DeviceIdNotFoundHwControlError:
            If the specified device_id does not exist in the file.
            If specified device has been disabled.

        Raise the following exception thrown from _read_json_file as is.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_id_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_id_info.json file did not exist
                in "/app/common/device_id_manager/".

    """
    if _is_valid_uuid(identifier=device_id) is False:
        raise Err.ApiUsageHwControlError
    device = _get_devices_info().get(device_id, {})
    if device.get("valid") is True:
        return device.get("oobDeviceID")
    raise Err.DeviceIdNotFoundHwControlError


def oob_device_id_to_device_id(oob_device_id: str, oob_manager_id: str) -> str | None:
    """API function of convert oob_device_id to device_id.

    This API function provides the functionality to convert
    oob_device_id to device_id.

    Args:
        oob_device_id (str):
            Identifier that uniquely identifies the device in OOB.
        oob_manager_id (str):
            Identifier that uniquely identifies the OOB plug-in.

    Returns:
        str/None:
            str:
                device_id.
            None:
                If specified device has been disabled.
                If device of specified data does not exist.

    Raises:
        Raise the following exception thrown from _read_json_file as is.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_id_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_id_info.json file did not exist
                in "/app/common/device_id_manager/".
    """
    id_to_info_copy = _get_devices_info()
    for device_id, device in id_to_info_copy.items():
        if (
            device.get("valid") is True
            and device.get("oobDeviceID") == oob_device_id
            and oob_manager_id in device.get("oobManagerID")
        ):
            return device_id
    return None


def device_id_to_manager_id(device_id: str) -> dict:
    """API function of convert device_id to manager_id.

    This API function provides the functionality to convert
    device_id to manager_id.

    This API function is temporary and serves as an API for
    compatibility with processing up to iteration 11.
    All callers are scheduled to be deprecated after switching to the
    new API.

    Args:
        device_id (str):
            An identifier that uniquely identifies the device.

    Returns:
        dict:
            fm_manager_id (str):
                An identifier that uniquely identifies the FM plugin.
            oob_manager_id (str):
                An identifier that uniquely identifies the OOB plugin.

                example:

                    { "fm": "liquid-001",
                      "oob": "iLO-008"}

    Raises:
        ApiUsageHwControlError:
            If the specified device_id is an invalid UUID.

        DeviceIdNotFoundHwControlError:
            If the specified device_id does not exist in the file.
            If specified device has been disabled.

        Raise the following exception thrown from _read_json_file as is.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_id_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_id_info.json file did not exist
                in "/app/common/device_id_manager/".

    """
    manager_ids = {"fm": None, "oob": None}
    if _is_valid_uuid(identifier=device_id) is False:
        raise Err.ApiUsageHwControlError
    device = _get_devices_info().get(device_id, {})
    if device.get("valid") is True:
        fm_manage_list = device.get("fmManagerID", [])
        fm_manager_id = None
        if fm_manage_list:
            fm_manager_id = fm_manage_list[0]
        oob_manage_list = device.get("oobManagerID", [])
        oob_manager_id = None
        if oob_manage_list:
            oob_manager_id = oob_manage_list[0]

        manager_ids["fm"] = fm_manager_id
        manager_ids["oob"] = oob_manager_id
        return manager_ids
    raise Err.DeviceIdNotFoundHwControlError


def device_id_to_manager_id_multi_hostport(device_id: str) -> dict:
    """API function of convert device_id to manager_id.

    This API function provides the functionality to convert
    device_id to manager_id.

    Args:
        device_id (str):
            An identifier that uniquely identifies the device.

    Returns:
        dict:
            fm_manager_id (dict[str: list[str]]):
                An identifier that uniquely identifies the FM plugin.
            oob_manager_id (dict[str: list[str]]):
                An identifier that uniquely identifies the OOB plugin.

                example:

                    { "fm": ["liquid-001"],
                      "oob": ["iLO-008"]}

    Raises:
        ApiUsageHwControlError:
            If the specified device_id is an invalid UUID.

        DeviceIdNotFoundHwControlError:
            If the specified device_id does not exist in the file.
            If specified device has been disabled.

        Raise the following exception thrown from _read_json_file as is.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_id_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_id_info.json file did not exist
                in "/app/common/device_id_manager/".

    """
    manager_ids = {"fm": [], "oob": []}
    if _is_valid_uuid(identifier=device_id) is False:
        raise Err.ApiUsageHwControlError
    device = _get_devices_info().get(device_id, {})
    if device.get("valid") is True:
        manager_ids["fm"] = device.get("fmManagerID", [])
        manager_ids["oob"] = device.get("oobManagerID", [])
        return manager_ids
    raise Err.DeviceIdNotFoundHwControlError


def device_id_to_fm_switch_id(device_id: str) -> str | None:
    """API function of convert device_id to fm_switch_id.

    This API function provides the functionality to convert
    device_id to fm_switch_id.

    Args:
        str:
            device_id
            An identifier that uniquely identifies the device.

    Returns:
        str/None:
            fm_switch_id
                Identifier for FM to identify the switch.
            None:
                Data does not exist.

    Raises:
        ApiUsageHwControlError:
            If the specified device_id is an invalid UUID.

        DeviceIdNotFoundHwControlError:
            If the specified device_id does not exist in the file.
            If specified device has been disabled.

        InvalidTypeDeviceIdHwControlError:
            If the specified device_id is not the device_id of
            the switch.

        Raise the following exception thrown from _read_json_file as is.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_id_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_id_info.json file did not exist
                in "/app/common/device_id_manager/".

    """
    if _is_valid_uuid(identifier=device_id) is False:
        raise Err.ApiUsageHwControlError
    device = _get_devices_info().get(device_id, {})
    if device.get("valid") is True:
        if device.get("deviceType") == con.DeviceType.SWITCH.value:
            return device.get("fmSwitchID")
        raise Err.InvalidTypeDeviceIdHwControlError
    raise Err.DeviceIdNotFoundHwControlError


def fm_switch_id_to_device_id(fm_switch_id: str, fm_manager_id: str) -> str | None:
    """API function of convert fm_switch_id to device_id.

    This API function provides the functionality to convert.

    Args:
        fm_switch_id (str):
            Identifier for FM to identify the switch.
        fm_manager_id (str):
            Identifier that uniquely identifies the FM plug-in.

    Returns:
        str/None:
            str:
                device_id:
            None:
                If specified device has been disabled.
                If device of specified data does not exist.

    Raises:
        Raise the following exception thrown from _read_json_file as is.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_id_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_id_info.json file did not exist
                in "/app/common/device_id_manager/".

    """
    id_to_info_copy = _get_devices_info()
    for device_id, device in id_to_info_copy.items():
        if (
            device.get("valid") is True
            and device.get("fmSwitchID") == fm_switch_id
            and device.get("deviceType") == con.DeviceType.SWITCH.value
            and fm_manager_id in device.get("fmManagerID")
        ):
            return device_id
    return None


def get_controllable_device_id_list() -> list:
    """API function of get controllable device_ids list.

    This API function provides the functionality to
    get a list of controllable device_ids.

    Args:
        None

    Returns:
        list:
            List of device_id of controllable devices.

    Raises:
        Raise the following exception thrown from _read_json_file as is.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_id_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_id_info.json file did not exist
                in "/app/common/device_id_manager/".
    """
    device_list: list = []
    id_to_info_copy = _get_devices_info()
    for device_id, device in id_to_info_copy.items():
        if device.get("valid") is False:
            continue
        if device.get("oobManagerID", []) and device.get("oobDeviceID", {}):
            device_list.append(device_id)
            continue
        fm_manager_id_list = device.get("fmManagerID", [])
        if fm_manager_id_list:
            for fm_manager_id in fm_manager_id_list:
                if device.get("fmPortID", {}).get(fm_manager_id, []):
                    device_list.append(device_id)
                    break
    return device_list


def device_id_to_switch_port_type(device_id: str) -> str | None:
    """API function of convert device_id to switch Port Type.

    This API function provides the functionality to convert
    device_id to the value of key switchPortType.

    Args:
        device_id (str):
            Identifier that uniquely identifies the device.

    Returns:
        str/None:
            str:
                the value of key switchPortType.
            None:
                Data does not exist.

    Raises:
        ApiUsageHwControlError:
            If the specified device_id is an invalid UUID.

        DeviceIdNotFoundHwControlError:
            If the specified device_id does not exist in the file.
            If specified device has been disabled.

        Raise the following exception thrown from _read_json_file as is.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_id_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_id_info.json file did not exist
                in "/app/common/device_id_manager/".
    """
    if _is_valid_uuid(identifier=device_id) is False:
        raise Err.ApiUsageHwControlError
    device = _get_devices_info().get(device_id, {})
    if device.get("valid") is True:
        return device.get("switchPortType")
    raise Err.DeviceIdNotFoundHwControlError


def get_switch_device_id_list() -> list:
    """API function of get switch device_ids list.

    This API function provides the functionality to
    get a list of switch device_ids.

    Args:
        None

    Returns:
        list:
            List of device_id of switch devices.

    Raises:
        Raise the following exception thrown from _read_json_file as is.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_id_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_id_info.json file did not exist
                in "/app/common/device_id_manager/".
    """
    switch_device_list: list = []
    id_to_info_copy = _get_devices_info()
    for device_id, device in id_to_info_copy.items():
        if device.get("valid") is False:
            continue
        if device.get("deviceType") == con.DeviceType.SWITCH.value:
            switch_device_list.append(device_id)
    return switch_device_list


def device_id_to_connected_fm_switch_id(device_id: str) -> str | None:
    """API function of convert device_id to connectedFmSwitchID.

    This API function provides the functionality to convert
    device_id to connectedFmSwitchID.

    This API function is temporary and serves as an API for
    compatibility with processing up to iteration 11.
    All callers are scheduled to be deprecated after switching to the
    new API.

    Args:
        str:
            device_id
            An identifier that uniquely identifies the device.

    Returns:
        str/None:
            connectedFmSwitchID
                Identification ID of the connected switch device.
            None:
                Data does not exist.

    Raises:
        ApiUsageHwControlError:
            If the specified device_id is an invalid UUID.

        DeviceIdNotFoundHwControlError:
            If the specified device_id does not exist in the file.
            If specified device has been disabled.

        InvalidTypeDeviceIdHwControlError:
            If the specified device_id is a device_id of the switch.

        Raise the following exception thrown from _read_json_file as is.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_id_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_id_info.json file did not exist
                in "/app/common/device_id_manager/".

    """
    if _is_valid_uuid(identifier=device_id) is False:
        raise Err.ApiUsageHwControlError
    device = _get_devices_info().get(device_id, {})
    if device.get("valid") is True:
        if device.get("deviceType") != con.DeviceType.SWITCH.value:
            info = device.get("connectedFmSwitchID", {})
            result = None
            if info:
                first_key = next(iter(info))
                if info[first_key]:
                    result = info[first_key][0]
            return result
        raise Err.InvalidTypeDeviceIdHwControlError
    raise Err.DeviceIdNotFoundHwControlError


def device_id_to_connected_fm_switch_id_multi_hostport(device_id: str, fm_manager_id: str) -> list:
    """API function of convert device_id to connectedFmSwitchID.

    This API function provides the functionality to convert
    device_id to connectedFmSwitchID.

    Args:
        str:
            device_id
                An identifier that uniquely identifies the device.
            fm_manager_id:
                Identifier that uniquely identifies the FM plug-in.

    Returns:
        list:
            connectedFmSwitchID (str)
                Identification ID of the connected switch device.
            empty list:
                Data does not exist.

    Raises:
        ApiUsageHwControlError:
            If the specified device_id is an invalid UUID.

        DeviceIdNotFoundHwControlError:
            If the specified device_id does not exist in the file.
            If specified device has been disabled.

        InvalidTypeDeviceIdHwControlError:
            If the specified device_id is a device_id of the switch.

        Raise the following exception thrown from _read_json_file as is.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_id_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_id_info.json file did not exist
                in "/app/common/device_id_manager/".

    """
    if _is_valid_uuid(identifier=device_id) is False:
        raise Err.ApiUsageHwControlError
    device = _get_devices_info().get(device_id, {})
    if device.get("valid") is True:
        if device.get("deviceType") != con.DeviceType.SWITCH.value:
            result = device.get("connectedFmSwitchID", {}).get(fm_manager_id, [])
            return result
        raise Err.InvalidTypeDeviceIdHwControlError
    raise Err.DeviceIdNotFoundHwControlError


def device_id_to_fm_valid(device_id: str) -> bool:
    """API function of convert device_id to fmValid.

    This API function provides the functionality to convert
    device_id to fmValid.

    Args:
        device_id (str):
            Identifier that uniquely identifies the device.

    Returns:
        fmValid(bool):
            fmValid.

    Raises:
        ApiUsageHwControlError:
            If the specified device_id is an invalid UUID.

        DeviceIdNotFoundHwControlError:
            If the specified device_id does not exist in the file.
            If specified device has been disabled.

        Raise the following exception thrown from _read_json_file as is.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_id_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_id_info.json file did not exist
                in "/app/common/device_id_manager/".
    """
    if _is_valid_uuid(identifier=device_id) is False:
        raise Err.ApiUsageHwControlError
    device = _get_devices_info().get(device_id, {})
    if device.get("valid") is True:
        return device.get("fmValid")
    raise Err.DeviceIdNotFoundHwControlError


def connected_fm_switch_id_to_device_id_list(connected_fm_switch_id: str) -> list:
    """API function of get device_ids list.

    This API function provides the functionality to
    get a list of device_ids for a specified connected_fm_switch_id.

    Args:
        connected_fm_switch_id (str):
            Identification ID of the connected switch device.

    Returns:
        list:
            List of device IDs for devices connected to the switch.

    Raises:
        Raise the following exception thrown from _read_json_file as is.

            DeviceIdFileIncorrectHwControlError:
                When there is an error in the contents of the
                device_id_info.json file.

            DeviceIdFileNotFoundHwControlError:
                If the device_id_info.json file did not exist
                in "/app/common/device_id_manager/".

    """
    device_list: list = []
    id_to_info_copy = _get_devices_info()
    for device_id, device in id_to_info_copy.items():
        if device.get("valid") is False:
            continue
        if any(connected_fm_switch_id in values for values in device.get("connectedFmSwitchID", {}).values()):
            device_list.append(device_id)
    return device_list


def _read_device_id_manager_file(device_id_manager_file_path: str) -> pd.DataFrame:
    """API function of reading device id manager file.

    API function of reading device id manager file.

    Returns:
        devices_info_json (pandas.DataFrame): Devices information
            (from device ID manager file).

    Raises:
        DeviceIdFileIncorrectHwControlError:
            When there is an error in the contents of the
            device_id_info.json file.

        DeviceIdFileNotFoundHwControlError:
            When there is a permission error of the
            device_id_info.json file.
    """
    try:
        dir_ppath = path_setting().data_file_dir
        device_id_manager_file_path = os.path.join(dir_ppath, _DEVICE_ID_MANAGER_FILE_NAME)
        LOGGER.debug(
            msg.BaseLogMessage(
                detail=f"[{__name__}] Path of device id manager file is {device_id_manager_file_path}."
            ).to_json_encodable()
        )
        devices_info_json = pd.read_json(device_id_manager_file_path, dtype="object")
        devices_info_json = devices_info_json.replace(["NaN", "nan", "None", ""], None)
        if not devices_info_json.empty:  # pylint: disable=E1101
            devices_info_json = _change_info_to_new_type(devices_info_json)
    # PermissionError: Raised when the json file is not accessible.
    except PermissionError as exc:
        LOGGER.error(
            msg.BaseLogMessage(
                detail=f"[{__name__}] The Device ID Management File was not found or there was a permission error."
            ).to_json_encodable()
        )
        raise Err.DeviceIdFileNotFoundHwControlError from exc
    # ValueError: Raised when the file does not conform to JSON
    # format.
    # TypeError: Type of data is not pandas.
    except (ValueError, TypeError) as exc:
        LOGGER.error(
            msg.BaseLogMessage(detail=f"[{__name__}] The Device ID Management File is incorrect.").to_json_encodable()
        )
        raise Err.DeviceIdFileIncorrectHwControlError from exc
    # FileNotFoundError: Create a new file, and set empty list in file.
    except FileNotFoundError as exc:
        with open(device_id_manager_file_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        devices_info_json = pd.DataFrame()

    return devices_info_json


def assign_device_id() -> None:
    """API function of assigning IDs to devices.

    API function of assigning IDs to devices.

    Returns:
        None

    Raises:
        InvalidSerialNumberConfigFileNotFoundHwControlError:
            When there is a permission error of the
            invalid_serial_number.json file.

        InvalidSerialNumberConfigFileIncorrectHwControlError:
            When there is an error in the contents of the
            invalid_serial_number.json file.

        DeviceIdFileIncorrectHwControlError:
            When there is an error in the contents of the
            device_id_info.json file.
    """
    pd.set_option("future.no_silent_downcasting", True)
    # The list of candidate mobile devices
    moved_devices = pd.DataFrame(columns=all_keys + ["info_from"])
    # Acquire lock
    with device_id_info_lock:
        dir_ppath = path_setting().data_file_dir
        device_id_manager_file_path = os.path.join(dir_ppath, _DEVICE_ID_MANAGER_FILE_NAME)

        devices_info_json = _read_device_id_manager_file(device_id_manager_file_path)
        try:
            dir_path = path_setting().config_file_dir
            invalid_serial_number_file_path = os.path.join(dir_path, _INVALID_SERIAL_NUMBER_FILE_NAME)
            LOGGER.debug(
                msg.BaseLogMessage(
                    detail=f"[{__name__}] Path of invalid serial number file is {invalid_serial_number_file_path}."
                ).to_json_encodable()
            )
            invalid_sn_info_json = pd.read_json(invalid_serial_number_file_path, dtype="object")
        # PermissionError: Raised when the json file is not accessible.
        except PermissionError as exc:
            LOGGER.error(
                msg.BaseLogMessage(
                    detail=f"[{__name__}] The invalid serial number file was not found or there was a permission error."
                ).to_json_encodable()
            )
            raise Err.InvalidSerialNumberConfigFileNotFoundHwControlError from exc
        # ValueError: Raised when the file does not conform to JSON
        # format.
        # TypeError: Type of data is not pandas.
        except (ValueError, TypeError) as exc:
            LOGGER.error(
                msg.BaseLogMessage(
                    detail=f"[{__name__}] The invalid serial number file is incorrect."
                ).to_json_encodable()
            )
            raise Err.InvalidSerialNumberConfigFileIncorrectHwControlError from exc
        # FileNotFoundError: Set empty dataframe
        except FileNotFoundError as exc:
            invalid_sn_info_json = pd.DataFrame()

        if not devices_info_json.empty:
            # Set valid key to False
            devices_info_json["valid"] = devices_info_json["valid"].astype(bool)
            devices_info_json.loc[:, "valid"] = False
            # Set fmValid key to bool
            devices_info_json["fmValid"] = devices_info_json["fmValid"].astype(bool)
        try:
            # Assign device IDs of FM manager type
            info_type = "FM"
            devices_info_json, moved_devices = do_assign_device_id(
                info_type, devices_info_json, moved_devices, invalid_sn_info_json
            )
            # Assign device IDs of OOB manager type
            info_type = "OOB"
            devices_info_json, moved_devices = do_assign_device_id(
                info_type, devices_info_json, moved_devices, invalid_sn_info_json
            )
            # Merge information in the list of candidate mobile devices
            if not devices_info_json.empty and not moved_devices.empty:
                info_type = "same serialNumber devices"
                devices_info_json = update_same_sn_devices(devices_info_json, moved_devices)
        # Catch errors that occur during DataFrame operations.
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            LOGGER.error(
                msg.BaseLogMessage(
                    detail=f"[{__name__}] Failed to assign device id by {info_type} info."
                ).to_json_encodable()
            )
            LOGGER.error(msg.ExceptionLog(trace_back=traceback.format_exc()).to_json_encodable())
            raise Err.DeviceIdFileIncorrectHwControlError from exc
        _update_json_file(devices_info_json, device_id_manager_file_path)
        _update_id_to_info(devices_info_json)

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

"""Equipment information Acquisition API - Device Information Acquisition

Provide a REST API that receives a device information acquisition
 request from a higher-level function and returns the corresponding
 device information acquisition result.

"""

import datetime
import traceback
from typing import Union
from fastapi import APIRouter
from fastapi.responses import JSONResponse

import app.common.messages.message as msg
from app.common.constants import TIME_STAMP_FORMAT
from app.common.utils.log import LOGGER
from app.common.basic_exceptions import (
    BaseHwControlError,
    DeviceNotFoundHwControlError,
    InternalHwControlError,
)
from app.common.deviceIdManager import device_id_base

from app.routers.info import const_devices
from app.routers.info.const_devices import (
    TAG_LIST,
    TAG_ALL_DEVICES,
    TAG_INFO,
    TAG_METRIC,
    TAG_RESOURCE,
)
from app.routers.info.const_devices import ResourceList
from app.routers.info.const_devices import IncompleteList
from app.routers.info.const_devices import DeviceResourceList
from app.routers.info.const_devices import IncompleteResourceList

from app.core.info.info_core import InformationCore
from app.common.utils import error_utils
from app.common import constants

DEVICE_LIST_ITEM_NAME_DEVICE_LIST = "deviceList"  # Device List
DEVICES_ITEM_NAME_DEVICE_ID = "deviceID"  # Device ID
DEVICES_ITEM_NAME_DEVICE_TYPE = "type"  # Device Type
DEVICES_ITEM_NAME_DEVICE_INFO_TIME = "infoTimestamp"  # Device infoTimestamp

DEVICES_INFO_TYPE_SPEC = "spec"  # Information acquisition type: Device information
DEVICES_INFO_TYPE_METRIC = "metric"  # Information Acquisition Type: Metric information
DEVICES_INFO_TYPE_RESOURCE = "resource"  # Information Acquisition Type: Resource information

DEVICES_API_LOG_TITLE = "/cdim/api/v1/devices"  # Log message title
DEVICES_API_LOG_RESULT_OK = "Success"  # Log message result: Success
DEVICES_API_LOG_RESULT_NG = "Failure"  # Log message result: Failure
DEVICES_API_LOG_RESULT_ERR = "Partial failure"  # Log message result: Partial failure
DEVICES_API_LOG_ERRCODE = " errcode: "  # Log message errcode
DEVICES_API_LOG_ERR_MESSAGE = " err_message: "  # Log message err_message


router = APIRouter(prefix=f"{constants.BASE_URL}/v1")


# No1_Device ID list information acquisition
@router.get(
    "/device-ids",
    description=const_devices.DEVICE_LIST_DESC_STR,
    response_class=JSONResponse,
    tags=[TAG_LIST],
)
def get_device_ids(device_type: Union[str, None] = None) -> JSONResponse:
    """Device ID list information acquisition

    If the specified device type is valid, collect the ID list information for that device type.
    If not specified, all device ID list information will be collected.

    Args:
        device_type (Union[str, None]): specified device type

    Returns:
        response: Collect device ID list information for specified device type
        Refer to No1_device list information acquisition in the information acquisition interface specifications.

    """
    log_param = "/cdim/api/v1/device-ids"
    if device_type:
        log_param += "?device_type=" + device_type

    LOGGER.info(msg.get_log_message(msg.I00001, ["devices", log_param]))

    # Initialization of return value
    result: str = DEVICES_API_LOG_RESULT_NG
    device_list: dict = {}

    try:
        # Assign device ID
        if assign_device_id_error := _assign_device_id(log_param):
            return assign_device_id_error

        # Get device list
        if get_device_list_error := _get_device_list(device_type, log_param, device_list):
            return get_device_list_error

        # device information data exists
        device_cnt = len(device_list[DEVICE_LIST_ITEM_NAME_DEVICE_LIST])
        if device_cnt > 0:
            result = DEVICES_API_LOG_RESULT_OK
            response = device_list
        else:
            # If there is no information acquisition result data count
            LOGGER.warning(msg.get_log_message(msg.W00006, [log_param]))
            return DeviceNotFoundHwControlError().generate_api_response()

    finally:
        LOGGER.info(msg.get_log_message(msg.I00002, ["devices", result]))

    return JSONResponse(response)


# No2_Batch acquisition of all resource information
@router.get(
    "/devices",
    description=const_devices.BATCH_ACQUISITION_DESC_STR,
    response_class=JSONResponse,
    tags=[TAG_ALL_DEVICES],
)
def get_all_devices_information(device_type: Union[str, None] = None) -> JSONResponse:
    """Batch acquisition of all resource information

    If the specified device type is valid, collect all resource information for the corresponding device type.
    If not specified, all resource information will be collected.

    Args:
        device_type (Union[str, None]): specified device type

    Returns:
        response: Collect bulk resource information for the specified device type
        Refer to No.2_Batch information acquisition of all resources
                in the information acquisition interface specifications.

    """
    log_param = DEVICES_API_LOG_TITLE
    if device_type:
        log_param += "?device_type=" + device_type

    LOGGER.info(msg.get_log_message(msg.I00001, ["devices", log_param]))

    # Initialization of return value
    result: str = DEVICES_API_LOG_RESULT_NG
    device_list: dict = {}
    device_infos = DeviceResourceList()
    incomplete_device_infos = IncompleteResourceList()

    try:
        # Assign device ID
        if assign_device_id_error := _assign_device_id(log_param):
            return assign_device_id_error

        # Get device list
        if get_device_list_error := _get_device_list(device_type, log_param, device_list):
            return get_device_list_error

        # Get all device information in the device list
        device_array = device_list[DEVICE_LIST_ITEM_NAME_DEVICE_LIST]
        if isinstance(device_array, list):
            if get_all_device_infos_error := _get_all_device_info(
                device_array, log_param, device_infos, incomplete_device_infos
            ):
                return get_all_device_infos_error

        else:
            # If there is no information acquisition result data
            LOGGER.warning(msg.get_log_message(msg.W00006, [log_param]))
            return DeviceNotFoundHwControlError().generate_api_response()

        # device information data exists
        exists_devices = bool(device_infos.deviceList)
        exists_incomplete_devices = bool(incomplete_device_infos.incompleteDeviceList)
        if exists_devices or exists_incomplete_devices:

            # If the information acquisition result data is only normal
            if not exists_incomplete_devices:
                result = DEVICES_API_LOG_RESULT_OK
                # Convert a class type to a dict type and return it
                response = vars(device_infos)

            elif not exists_devices:
                result = DEVICES_API_LOG_RESULT_ERR
                # Convert a class type to a dict type and return it
                response = vars(incomplete_device_infos)

            else:
                result = DEVICES_API_LOG_RESULT_OK
                device_info_array = ResourceList()
                device_info_array.deviceList = device_infos.deviceList
                device_info_array.incompleteDeviceList = incomplete_device_infos.incompleteDeviceList
                device_info_array.infoTimestamp = device_infos.infoTimestamp
                # Convert a class type to a dict type and return it
                response = vars(device_info_array)

        else:
            result = DEVICES_API_LOG_RESULT_NG
            # If there is no information acquisition result data count
            LOGGER.warning(msg.get_log_message(msg.W00006, [log_param]))
            return DeviceNotFoundHwControlError().generate_api_response()

    finally:
        LOGGER.info(msg.get_log_message(msg.I00002, ["devices", result]))

    return JSONResponse(response)


# No3_Get device information
@router.get(
    "/devices/{device_id}/specs",
    description=const_devices.DEVICES_DESC_STR,
    response_class=JSONResponse,
    tags=[TAG_INFO],
)
def get_devices_information(device_id: str) -> JSONResponse:
    """Get device information

    Get device information corresponding to the specified deviceID

    Args:
        device_id (str): specified deviceID

    Returns:
        response: Individual device information corresponding to deviceID
        Please refer to No.3_Device information acquisition in the information acquisition interface specifications.

    """
    log_param = DEVICES_API_LOG_TITLE + "/" + device_id + "/specs"

    LOGGER.info(msg.get_log_message(msg.I00001, ["devices", log_param]))

    # Initialization of return value
    result: str = DEVICES_API_LOG_RESULT_NG
    err_info_flag: bool = False
    device_info: dict = {}

    # Incorporate exception handling
    try:
        # Added return of error information to information acquisition
        err_info_flag, device_info = _get_individually_specified_device_info(device_id, DEVICES_INFO_TYPE_SPEC)
        if not err_info_flag:
            result = DEVICES_API_LOG_RESULT_OK
        else:
            result = DEVICES_API_LOG_RESULT_ERR
        return JSONResponse(device_info)

    except BaseHwControlError as error:
        # Use JSONResponse generation method of BaseHwControlError
        LOGGER.warning(msg.get_log_message(msg.W00001, [log_param]))
        return error.generate_api_response()

    finally:
        LOGGER.info(msg.get_log_message(msg.I00002, ["devices", result]))


# No4_Get resource information
@router.get(
    "/devices/{device_id}",
    description=const_devices.RESOURCE_DESC_STR,
    response_class=JSONResponse,
    tags=[TAG_RESOURCE],
)
def get_devices_resource(device_id: str) -> JSONResponse:
    """Get resource information

    Get resource information corresponding to the specified deviceID

    Args:
        device_id (str): specified deviceID

    Returns:
        response: resource device information corresponding to deviceID
        Please refer to No.4_Resource information acquisition in the information acquisition interface specifications.

    """
    log_param = DEVICES_API_LOG_TITLE + "/" + device_id

    LOGGER.info(msg.get_log_message(msg.I00001, ["devices", log_param]))

    # Initialization of return value
    result: str = DEVICES_API_LOG_RESULT_NG
    err_info_flag: bool = False
    resource_info: dict = {}

    # Incorporate exception handling
    try:
        # Added return of error information to information acquisition
        err_info_flag, resource_info = _get_individually_specified_device_info(device_id, DEVICES_INFO_TYPE_RESOURCE)
        if not err_info_flag:
            result = DEVICES_API_LOG_RESULT_OK
        else:
            result = DEVICES_API_LOG_RESULT_ERR
        return JSONResponse(resource_info)

    except BaseHwControlError as error:
        # Use JSONResponse generation method of BaseHwControlError
        LOGGER.warning(msg.get_log_message(msg.W00001, [log_param]))
        return error.generate_api_response()

    finally:
        LOGGER.info(msg.get_log_message(msg.I00002, ["devices", result]))


# No5_Get metric information
@router.get(
    "/devices/{device_id}/metrics",
    description=const_devices.METRICS_DESC_STR,
    response_class=JSONResponse,
    tags=[TAG_METRIC],
)
def get_devices_metrics(device_id: str) -> JSONResponse:
    """Get metric information

    Get metrics information corresponding to the specified deviceID

    Args:
        device_id (str): specified deviceID

    Returns:
        response: Individual metric information corresponding to deviceID
        Refer to No.5_Metric information acquisition in the information acquisition interface specifications.

    """
    log_param = DEVICES_API_LOG_TITLE + "/" + device_id + "/metrics"

    LOGGER.info(msg.get_log_message(msg.I00001, ["devices", log_param]))

    # Initialization of return value
    result: str = DEVICES_API_LOG_RESULT_NG
    err_info_flag: bool = False
    metric_info: dict = {}

    # Incorporate exception handling
    try:
        # Added return of error information to information acquisition
        err_info_flag, metric_info = _get_individually_specified_device_info(device_id, DEVICES_INFO_TYPE_METRIC)
        if not err_info_flag:
            result = DEVICES_API_LOG_RESULT_OK
        else:
            result = DEVICES_API_LOG_RESULT_ERR
        return JSONResponse(metric_info)

    except BaseHwControlError as error:
        # Use JSONResponse generation method of BaseHwControlError
        LOGGER.warning(msg.get_log_message(msg.W00001, [log_param]))
        return error.generate_api_response()

    finally:
        LOGGER.info(msg.get_log_message(msg.I00002, ["devices", result]))


def _assign_device_id(log_param: str) -> JSONResponse | None:
    """Assign device ID

    Discover devices and assign IDs.

    Args:
        log_param(str): an additional log message to identify the request URL

    Returns:
        JSONResponse | None: error response if an error occurred, otherwise None
    """

    # Device ID management call
    # Add conditions in the future
    # e.g.(if not device_type:Implementation conditions)
    try:
        # Calling the device ID issuing
        device_id_base.assign_device_id()

    except BaseHwControlError as error:
        # Use JSONResponse generation method of BaseHwControlError
        LOGGER.warning(msg.get_log_message(msg.W00001, [log_param]))
        return error.generate_api_response()

    return None


def _get_device_list(device_type: str | None, log_param: str, device_list: dict) -> JSONResponse | None:
    """Find devices by type

    Return devices of the given type.
    When the type is None, all devices are returned.

    Args:
        device_type (str | None): type of device to find
        log_param (str): an additional log message to identify the request URL
        device_list (dict): dictionary to put the found devices

    Returns:
        JSONResponse | None: error response if an error occurred, otherwise None
    """

    # Device information getter
    get_info = InformationCore()

    # Get device list
    try:
        device_list_result = get_info.get_device_list(device_type)
        if not device_list_result:
            # If the information acquisition result data is invalid
            LOGGER.warning(msg.get_log_message(msg.W00006, [log_param]))
            return InternalHwControlError().generate_api_response()
        if DEVICE_LIST_ITEM_NAME_DEVICE_LIST not in device_list_result:
            # If the information acquisition result data is invalid
            LOGGER.warning(msg.get_log_message(msg.W00006, [log_param]))
            return DeviceNotFoundHwControlError().generate_api_response()

        # Return device list
        device_list.update(device_list_result)

    except BaseHwControlError as error:
        # Use JSONResponse generation method of BaseHwControlError
        LOGGER.warning(msg.get_log_message(msg.W00001, [log_param]))
        return error.generate_api_response()

    return None


def _get_all_device_info(
    device_array: list,
    log_param: str,
    device_infos: DeviceResourceList,
    incomplete_device_infos: IncompleteResourceList,
) -> JSONResponse | None:
    """Get device information by device IDs

    Get information of the devices identified by IDs.

    Args:
        device_array (list): devices containing those IDs
        log_param (str): an additional log message to identify the request URL
        device_infos (DeviceResourceList): data holder to put the device information
        incomplete_device_infos (IncompleteResourceList): data holder to put the incomplete device information

    Returns:
        JSONResponse | None: error response if an error occurred, otherwise None
    """

    for device_item in device_array:
        if isinstance(device_item, dict):
            device_id = str(device_item.get(DEVICES_ITEM_NAME_DEVICE_ID))
            log_para_dev = log_param + ": device_id=" + device_id
            err_info_flag = False

            # Incorporate exception handling
            try:
                # Get detailed device information
                # Added return of error information to information acquisition
                err_info_flag, device_info = _get_individually_specified_device_info(device_id, DEVICES_INFO_TYPE_SPEC)

            except BaseHwControlError as error:
                # Use JSONResponse generation method of BaseHwControlError
                err_code = error.error_code
                err_message = error.message
                log_param_err_info = log_para_dev
                log_param_err_info += DEVICES_API_LOG_ERRCODE + err_code + DEVICES_API_LOG_ERR_MESSAGE + err_message
                LOGGER.warning(msg.get_log_message(msg.W00001, [log_param_err_info]))
                # If exception, proceed to next device
                continue

            except Exception:  # pylint: disable=W0718
                # unexpected exception occurred
                LOGGER.error(msg.get_log_message(msg.E00001, [traceback.format_exc()]))
                LOGGER.warning(msg.get_log_message(msg.W00001, [log_param]))
                # If exception, proceed to next device
                continue

            # If the error information for information acquisition failure is valid
            if err_info_flag:
                incomplete_device_infos.incompleteDeviceList.append(device_info)
                incomplete_device_infos.infoTimestamp = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

            # If the information acquisition result data is normal
            else:
                device_infos.deviceList.append(device_info)
                device_infos.infoTimestamp = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

        else:
            # If the information acquisition result data is invalid
            LOGGER.warning(msg.get_log_message(msg.W00006, [log_param]))
            return InternalHwControlError().generate_api_response()

    return None


def _get_individually_specified_device_info(device_id: str, info_type: str) -> tuple[bool, dict]:
    """Get individual device information

    Gets the individual device information for the specified device ID and acquisition type.

    Args:
        device_type (str): specified deviceID
        info_type (str): info acquisition type

    Returns:
        bool: Whether the error information is valid
            [True]  Error information exists
            [False] Error information does not exist
        response: Acquire individual information corresponding to the device ID
    """
    log_param = "_get_individually_specified_device_info( device_id: " + device_id + ", info_type: " + info_type + ")"

    # Get detailed device information
    get_info = InformationCore()

    # Initialization of return value
    device_info: dict = {}

    # Error information data class for the cause of acquisition failure
    error_info: list = []

    if info_type == DEVICES_INFO_TYPE_SPEC:
        # Acquisition of device information including return of error information
        device_info, error_info = get_info.get_spec_info(device_id)

    elif info_type == DEVICES_INFO_TYPE_METRIC:
        # Acquisition of metric information including return of error information
        device_info, error_info = get_info.get_metric_info(device_id)

    elif info_type == DEVICES_INFO_TYPE_RESOURCE:
        # Acquisition of resource information including return of error information
        device_info, error_info = _get_resource_info(get_info, device_id)

    else:
        # If the information acquisition result data is invalid
        LOGGER.warning(msg.get_log_message(msg.W00006, [log_param]))
        raise InternalHwControlError

    # Make and return result
    return _make_get_device_info_result(device_id, device_info, error_info, log_param)


def _get_resource_info(get_info: InformationCore, device_id: str) -> tuple[dict, list]:
    """Get resource information by device ID

    Get resource information of the device identified by ID.

    Args:
        get_info (InformationCore): domain object getting the resource information
        device_id (str): an ID to identify the device

    Returns:
        tuple[dict, list]: a tuple of resource information and error information
    """

    # Initialization of return values
    device_info: dict = {}
    error_info = []

    # Acquisition of device information including return of error information
    device_info_spec, error_info_spec = get_info.get_spec_info(device_id)
    # If the device ID of the obtained device information matches
    if device_info_spec and device_id == device_info_spec.get(DEVICES_ITEM_NAME_DEVICE_ID):
        # Store device information in resource information
        device_info = device_info_spec

    # Acquisition of metric information including return of error information
    device_info_metric, error_info_metric = get_info.get_metric_info(device_id)
    if device_info_metric and device_id == device_info_metric.get(DEVICES_ITEM_NAME_DEVICE_ID):
        # Store metric information in resource information
        if DEVICES_ITEM_NAME_DEVICE_ID in device_info_spec:
            device_info = {**device_info_spec, **device_info_metric}
        else:
            device_info = device_info_metric

    if error_info_spec or error_info_metric:
        error_info = error_utils.remove_duplicates(error_info_spec + error_info_metric)

    return device_info, error_info


def _make_get_device_info_result(
    device_id: str, device_info: dict, error_infos: list, log_param: str
) -> tuple[bool, dict]:
    """Make return value of _get_individually_specified_device_info()

    Construct the tuple returned by _get_individually_specified_device_info().

    Args:
        device_id (str): an ID to identify the device
        device_info (dict): device information
        error_infos (list): error information
        log_param (str): an additional log message to identify the request URL

    Returns:
        tuple[bool, dict]: a tuple of the error flag and the device information
    """

    # incomplete device information
    incomplete_info = IncompleteList()

    # If the information obtained is invalid
    # If the device ID in the acquired information does not match
    if not device_info or device_id != device_info.get(DEVICES_ITEM_NAME_DEVICE_ID):
        if error_infos:
            # If the error information for information acquisition failure is valid
            _set_err_info_results_item(device_id, error_infos, True, incomplete_info)

            # Returns failure to obtain some information
            result = True
            response = vars(incomplete_info)
            return result, response

        # If the information acquisition result data is invalid
        LOGGER.warning(msg.get_log_message(msg.W00006, [log_param]))
        raise InternalHwControlError

    if error_infos:
        # If the error information for information acquisition failure is valid
        _set_err_info_results_item(device_id, error_infos, False, incomplete_info)
        incomplete_info.infoTimestamp = device_info[DEVICES_ITEM_NAME_DEVICE_INFO_TIME]

        # Returns failure to obtain some information
        result = True
        response = device_info
        response.update(incomplete_info)
        return result, response

    # If the information acquisition result data is normal
    result = False
    return result, device_info


def _set_err_info_results_item(
    device_id: str, error_info: list, time_set_flag: bool, incomplete_info: IncompleteList
) -> None:
    """Set of error information data

    Set error information data for the cause of acquisition failure.

    Args:
            device_id (str): device id
            error_info (list): error information data
            time_set_flag (bool): current date and time set flag
            incomplete_info (IncompleteList) : Incomplete List Device information data

    Returns:
        Nothing
    """

    # the error information for information acquisition failure
    incomplete_info.errorInfo = error_info
    incomplete_info.deviceID = device_id
    # Set current date and time
    if time_set_flag:
        incomplete_info.infoTimestamp = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

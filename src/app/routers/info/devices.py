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

"""Equipment information Acquisition API - Device Information Acquisition.

Provide a REST API that receives a device information acquisition
 request from a higher-level function and returns the corresponding
 device information acquisition result.

"""

import datetime
import logging
import traceback
from typing import Annotated

from fastapi import APIRouter, Path, Query
from fastapi.responses import JSONResponse

import app.common.messages.message as msg
import app.common.plugin.svc.loader as plugin_loader
from app.common import constants
from app.common.basic_exceptions import (
    BaseHWControlError,
    DeviceNotFoundHWControlError,
    InternalHWControlError,
)
from app.common.constants import TIME_STAMP_FORMAT
from app.common.dim import device_id_base
from app.common.utils import error_utils
from app.core.info.info_core import InformationCore
from app.routers import api_metadata
from app.routers.info import info_life_span, response_models
from app.routers.info.response_models import DeviceResourceList, IncompleteList, IncompleteResourceList, ResourceList

DEVICE_LIST_ITEM_NAME_DEVICE_LIST = "deviceList"  # Device List
DEVICES_ITEM_NAME_DEVICE_ID = "deviceID"  # Device ID
DEVICES_ITEM_NAME_DEVICE_TYPE = "type"  # Device Type
DEVICES_ITEM_NAME_DEVICE_INFO_TIME = "infoTimestamp"  # Device infoTimestamp

DEVICES_INFO_TYPE_SPEC = "spec"  # Information acquisition type: Device information
DEVICES_INFO_TYPE_METRIC = "metric"  # Information Acquisition Type: Metric information
DEVICES_INFO_TYPE_RESOURCE = "resource"  # Information Acquisition Type: Resource information

DEVICES_API_LOG_TITLE = f"{constants.BASE_URL}/v1/devices"  # Log message title
DEVICES_API_LOG_RESULT_OK = "Success"  # Log message result: Success
DEVICES_API_LOG_RESULT_NG = "Failure"  # Log message result: Failure
DEVICES_API_LOG_RESULT_ERR = "Partial failure"  # Log message result: Partial failure
DEVICES_API_LOG_ERRCODE = " errcode: "  # Log message errcode
DEVICES_API_LOG_ERR_MESSAGE = " err_message: "  # Log message err_message


router = APIRouter(
    prefix=f"{constants.BASE_URL}/v1",
    tags=[api_metadata.DEVICE_INFO_API],
    lifespan=info_life_span.info_router_lifespan,
    responses={
        422: {
            "description": "HTTP status code 422 will not occur.",
        }  # Remove the default response schema specification for 422 cases set in FastAPI.
    },
)

# Get a logger object.
logger = logging.getLogger(__name__)


# No1_Device ID list information acquisition
@router.get(
    path="/device-ids",
    description="""\
Gets a list of Device IDs for the Device Type specified in type.

If no Device Type is specified, returns a list of all Device IDs.
""",
    response_description=(
        "Successfully retrieved all device ID information.\
         Returns devices ID information for the specified device Type."
    ),
    responses={
        400: api_metadata.error_case_spec_factory(
            case_description="The request is invalid.",
        ),
        404: api_metadata.error_case_spec_factory(
            case_description="The specified device not found.",
        ),
        500: api_metadata.error_cases_spec_factory(
            case_description="Internal server error.",
            sub_case_descriptions=[
                "The application internal error.",
                "The application configuration error.",
            ],
        ),
    },
    response_model=response_models.GetsListDevicesResponseBody,
    response_class=JSONResponse,
    name="Gets a list of devices",
)
def get_device_ids(
    device_type: Annotated[
        str | None,
        Query(
            alias="deviceType",
            description="The device type of the target device for obtaining the device list information.",
        ),
    ] = None,
) -> JSONResponse:
    """Device ID list information acquisition.

    If the specified Device Type is valid, collect the ID list information for that Device Type.
    If not specified, all Device ID list information will be collected.

    Args:
        device_type (str | None): specified Device Type

    Returns:
        JSONResponse: Collect Device ID list information for specified Device Type
        Refer to No1_device list information acquisition in the information acquisition interface specifications.

    """
    log_param = f"{constants.BASE_URL}/v1/device-ids"
    if device_type:
        log_param += "?deviceType=" + device_type

    logger.info(msg.get_log_message(msg.I00001, ["devices", log_param]))

    # Initialization of return value
    result: str = DEVICES_API_LOG_RESULT_NG
    device_list: dict = {}

    try:
        # Assign Device ID
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
            logger.warning(msg.get_log_message(msg.W00006, [log_param]))
            return DeviceNotFoundHWControlError().generate_api_response()

    finally:
        logger.info(msg.get_log_message(msg.I00002, ["devices", result]))

    return JSONResponse(response)


# No2_Batch acquisition of all resource information
@router.get(
    path="/devices",
    description="""\
Gets all resource information for the Device Type specified in type.

All resource information refers to all device configuration information.

If no Device Type is specified, returns all configuration information for all Device Type.
""",
    response_description=(
        "Successfully retrieved all resource information.\
         Returns resource information for the specified device Type."
    ),
    responses={
        400: api_metadata.error_case_spec_factory(
            case_description="The request is invalid.",
        ),
        404: api_metadata.error_case_spec_factory(
            case_description="The specified device not found.",
        ),
        500: api_metadata.error_cases_spec_factory(
            case_description="Internal server error.",
            sub_case_descriptions=[
                "The application internal error.",
                "The application configuration error.",
            ],
        ),
    },
    response_model=response_models.GetsAllDevicesResponseBody,
    response_class=JSONResponse,
    name="Gets all resource information",
)
def get_all_devices_information(
    device_type: Annotated[
        str | None,
        Query(
            alias="deviceType",
            description="The device type of the target device for obtaining the device information.",
        ),
    ] = None,
) -> JSONResponse:
    """Batch acquisition of all resource information.

    If the specified Device Type is valid, collect all resource information for the corresponding Device Type.
    If not specified, all resource information will be collected.

    Args:
        device_type (str | None): specified Device Type

    Returns:
        JSONResponse: Collect bulk resource information for the specified Device Type
        Refer to No.2_Batch information acquisition of all resources
                in the information acquisition interface specifications.

    """
    log_param = DEVICES_API_LOG_TITLE
    if device_type:
        log_param += "?deviceType=" + device_type

    logger.info(msg.get_log_message(msg.I00001, ["devices", log_param]))

    # Initialization of return value
    result: str = DEVICES_API_LOG_RESULT_NG
    device_list: dict = {}
    device_infos = DeviceResourceList()
    incomplete_device_infos = IncompleteResourceList()

    try:
        # Assign Device ID
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
            logger.warning(msg.get_log_message(msg.W00006, [log_param]))
            return DeviceNotFoundHWControlError().generate_api_response()

        # device information data exists
        exists_devices = bool(device_infos.device_list)
        exists_incomplete_devices = bool(incomplete_device_infos.incomplete_device_list)
        if exists_devices or exists_incomplete_devices:
            # If the information acquisition result data is only normal
            if not exists_incomplete_devices:
                result = DEVICES_API_LOG_RESULT_OK
                # Convert a class type to a dict type and return it
                response = device_infos.model_dump(by_alias=True)

            elif not exists_devices:
                result = DEVICES_API_LOG_RESULT_ERR
                # Convert a class type to a dict type and return it
                response = incomplete_device_infos.model_dump(by_alias=True)

            else:
                result = DEVICES_API_LOG_RESULT_OK
                device_info_array = ResourceList()
                device_info_array.device_list = device_infos.device_list
                device_info_array.incomplete_device_list = incomplete_device_infos.incomplete_device_list
                device_info_array.info_timestamp = device_infos.info_timestamp
                # Convert a class type to a dict type and return it
                response = device_info_array.model_dump(by_alias=True)

        else:
            result = DEVICES_API_LOG_RESULT_NG
            # If there is no information acquisition result data count
            logger.warning(msg.get_log_message(msg.W00006, [log_param]))
            return DeviceNotFoundHWControlError().generate_api_response()

    finally:
        logger.info(msg.get_log_message(msg.I00002, ["devices", result]))

    return JSONResponse(response)


# No3_Get device information
@router.get(
    path="/devices/{deviceID}/specs",
    description="""\
Gets configuration information for the Device ID specified in deviceID.
""",
    response_description=(
        "Successfully retrieved device information.\
         Returns configuration information for the specified device ID."
    ),
    responses={
        400: api_metadata.error_case_spec_factory(
            case_description="The request is invalid.",
        ),
        404: api_metadata.error_case_spec_factory(
            case_description="The specified device not found.",
        ),
        500: api_metadata.error_cases_spec_factory(
            case_description="Internal server error.",
            sub_case_descriptions=[
                "The application internal error.",
                "The application configuration error.",
            ],
        ),
    },
    response_model=response_models.GetsDeviceInformationResponseBody,
    response_class=JSONResponse,
    name="Get device information",
)
def get_devices_information(
    device_id: Annotated[
        str,
        Path(
            alias="deviceID",
            description="The Device ID of get device information target device.",
            examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
        ),
    ],
) -> JSONResponse:
    """Get device information.

    Get device information corresponding to the specified deviceID

    Args:
        device_id (str): specified deviceID

    Returns:
        JSONResponse: Individual device information corresponding to deviceID
        Please refer to No.3_Device information acquisition in the information acquisition interface specifications.

    """
    log_param = DEVICES_API_LOG_TITLE + "/" + device_id + "/specs"

    logger.info(msg.get_log_message(msg.I00001, ["devices", log_param]))

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

    except BaseHWControlError as error:
        # Use JSONResponse generation method of BaseHWControlError
        logger.warning(msg.get_log_message(msg.W00001, [log_param]))
        return error.generate_api_response()

    finally:
        logger.info(msg.get_log_message(msg.I00002, ["devices", result]))


# No4_Get resource information
@router.get(
    path="/devices/{deviceID}",
    description="""\
Gets configuration and metric information for the Device ID specified in deviceID.
""",
    response_description=(
        "Successfully retrieved resource information.\
         Returns configuration information and metric information for the specified device ID."
    ),
    responses={
        400: api_metadata.error_case_spec_factory(
            case_description="The request is invalid.",
        ),
        404: api_metadata.error_case_spec_factory(
            case_description="The specified device not found.",
        ),
        500: api_metadata.error_cases_spec_factory(
            case_description="Internal server error.",
            sub_case_descriptions=[
                "The application internal error.",
                "The application configuration error.",
            ],
        ),
    },
    response_model=response_models.GetsResourceInformationResponseBody,
    response_class=JSONResponse,
    name="Get resource information",
)
def get_devices_resource(
    device_id: Annotated[
        str,
        Path(
            alias="deviceID",
            description="The Device ID of get resource information target device.",
            examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
        ),
    ],
) -> JSONResponse:
    """Get resource information.

    Get resource information corresponding to the specified deviceID

    Args:
        device_id (str): specified deviceID

    Returns:
        JSONResponse: resource device information corresponding to deviceID
        Please refer to No.4_Resource information acquisition in the information acquisition interface specifications.

    """
    log_param = DEVICES_API_LOG_TITLE + "/" + device_id

    logger.info(msg.get_log_message(msg.I00001, ["devices", log_param]))

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

    except BaseHWControlError as error:
        # Use JSONResponse generation method of BaseHWControlError
        logger.warning(msg.get_log_message(msg.W00001, [log_param]))
        return error.generate_api_response()

    finally:
        logger.info(msg.get_log_message(msg.I00002, ["devices", result]))


# No5_Get metric information
@router.get(
    path="/devices/{deviceID}/metrics",
    description="""\
Gets metric information for the Device ID specified in deviceID.
""",
    response_description=(
        "Successfully retrieved metric information.\
         Returns metric information for the specified device ID."
    ),
    responses={
        400: api_metadata.error_case_spec_factory(
            case_description="The request is invalid.",
        ),
        404: api_metadata.error_case_spec_factory(
            case_description="The specified device not found.",
        ),
        500: api_metadata.error_cases_spec_factory(
            case_description="Internal server error.",
            sub_case_descriptions=[
                "The application internal error.",
                "The application configuration error.",
            ],
        ),
    },
    response_model=response_models.GetsMetricInformationResponseBody,
    response_class=JSONResponse,
    name="Get metric information",
)
def get_devices_metrics(
    device_id: Annotated[
        str,
        Path(
            alias="deviceID",
            description="The Device ID of get metrics information target device.",
            examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
        ),
    ],
) -> JSONResponse:
    """Get metric information.

    Get metrics information corresponding to the specified deviceID

    Args:
        device_id (str): specified deviceID

    Returns:
        JSONResponse: Individual metric information corresponding to deviceID
        Refer to No.5_Metric information acquisition in the information acquisition interface specifications.

    """
    log_param = DEVICES_API_LOG_TITLE + "/" + device_id + "/metrics"

    logger.info(msg.get_log_message(msg.I00001, ["devices", log_param]))

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

    except BaseHWControlError as error:
        # Use JSONResponse generation method of BaseHWControlError
        logger.warning(msg.get_log_message(msg.W00001, [log_param]))
        return error.generate_api_response()

    finally:
        logger.info(msg.get_log_message(msg.I00002, ["devices", result]))


def _assign_device_id(log_param: str) -> JSONResponse | None:
    """Assign Device ID.

    Discover devices and assign IDs.

    Args:
        log_param(str): an additional log message to identify the request URL

    Returns:
        JSONResponse | None: error response if an error occurred, otherwise None
    """
    # Device ID Manager call
    # Add conditions in the future
    # e.g.(if not device_type:Implementation conditions)
    try:
        # Calling the Device ID issuing
        device_id_base.assign_device_id()

    except BaseHWControlError as error:
        # Use JSONResponse generation method of BaseHWControlError
        logger.warning(msg.get_log_message(msg.W00001, [log_param]))
        return error.generate_api_response()

    return None


def _get_device_list(device_type: str | None, log_param: str, device_list: dict) -> JSONResponse | None:
    """Find devices by type.

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
            logger.warning(msg.get_log_message(msg.W00006, [log_param]))
            return InternalHWControlError().generate_api_response()
        if DEVICE_LIST_ITEM_NAME_DEVICE_LIST not in device_list_result:
            # If the information acquisition result data is invalid
            logger.warning(msg.get_log_message(msg.W00006, [log_param]))
            return DeviceNotFoundHWControlError().generate_api_response()

        # Return device list
        device_list.update(device_list_result)

    except BaseHWControlError as error:
        # Use JSONResponse generation method of BaseHWControlError
        logger.warning(msg.get_log_message(msg.W00001, [log_param]))
        return error.generate_api_response()

    return None


@plugin_loader.enable_plugin_lifecycle
def _get_all_device_info(
    device_array: list,
    log_param: str,
    device_infos: DeviceResourceList,
    incomplete_device_infos: IncompleteResourceList,
) -> JSONResponse | None:
    """Get device information by Device IDs.

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

            except BaseHWControlError as error:
                # Use JSONResponse generation method of BaseHWControlError
                err_code = error.error_code
                err_message = error.message
                log_param_err_info = log_para_dev
                log_param_err_info += DEVICES_API_LOG_ERRCODE + err_code + DEVICES_API_LOG_ERR_MESSAGE + err_message
                logger.warning(msg.get_log_message(msg.W00001, [log_param_err_info]))
                # If exception, proceed to next device
                continue

            except Exception:
                # unexpected exception occurred
                logger.error(msg.get_log_message(msg.E00001, [traceback.format_exc()]))
                logger.warning(msg.get_log_message(msg.W00001, [log_param]))
                # If exception, proceed to next device
                continue

            # If the error information for information acquisition failure is valid
            if err_info_flag:
                incomplete_device_infos.incomplete_device_list.append(device_info)
                incomplete_device_infos.info_timestamp = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

            # If the information acquisition result data is normal
            else:
                device_infos.device_list.append(device_info)
                device_infos.info_timestamp = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

        else:
            # If the information acquisition result data is invalid
            logger.warning(msg.get_log_message(msg.W00006, [log_param]))
            return InternalHWControlError().generate_api_response()

    return None


def _get_individually_specified_device_info(device_id: str, info_type: str) -> tuple[bool, dict]:
    """Get individual device information.

    Gets the individual device information for the specified Device ID and acquisition type.

    Args:
        device_id (str): specified Device ID
        info_type (str): info acquisition type

    Returns:
        bool: Whether the error information is valid
            [True]  Error information exists
            [False] Error information does not exist
        response: Acquire individual information corresponding to the Device ID
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
        logger.warning(msg.get_log_message(msg.W00006, [log_param]))
        raise InternalHWControlError

    # Make and return result
    return _make_get_device_info_result(device_id, device_info, error_info, log_param)


def _get_resource_info(get_info: InformationCore, device_id: str) -> tuple[dict, list]:
    """Get resource information by Device ID.

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
    # If the Device ID of the obtained device information matches
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
    """Make return value of _get_individually_specified_device_info().

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
    # If the Device ID in the acquired information does not match
    if not device_info or device_id != device_info.get(DEVICES_ITEM_NAME_DEVICE_ID):
        if error_infos:
            # If the error information for information acquisition failure is valid
            _set_err_info_results_item(device_id, error_infos, True, incomplete_info)

            # Returns failure to obtain some information
            result = True
            response = incomplete_info.model_dump(by_alias=True)

            return result, response

        # If the information acquisition result data is invalid
        logger.warning(msg.get_log_message(msg.W00006, [log_param]))
        raise InternalHWControlError

    if error_infos:
        # If the error information for information acquisition failure is valid
        _set_err_info_results_item(device_id, error_infos, False, incomplete_info)
        incomplete_info.info_timestamp = device_info[DEVICES_ITEM_NAME_DEVICE_INFO_TIME]

        # Returns failure to obtain some information
        result = True
        response = device_info
        response.update(incomplete_info.model_dump(by_alias=True))

        return result, response

    # If the information acquisition result data is normal
    result = False
    return result, device_info


def _set_err_info_results_item(
    device_id: str, error_info: list, time_set_flag: bool, incomplete_info: IncompleteList
) -> None:
    """Set of error information data.

    Set error information data for the cause of acquisition failure.

    Args:
            device_id (str): Device ID
            error_info (list): error information data
            time_set_flag (bool): current date and time set flag
            incomplete_info (IncompleteList) : Incomplete List Device information data

    Returns:
        Nothing
    """
    # the error information for information acquisition failure
    incomplete_info.error_info = error_info
    incomplete_info.device_id = device_id
    # Set current date and time
    if time_set_flag:
        incomplete_info.info_timestamp = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

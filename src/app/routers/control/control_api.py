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

"""Device Control API.

This module defines Device Control API and its endpoints.

"""

import http
import logging
from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Path, Query
from fastapi.responses import JSONResponse
from pydantic import UUID4, BaseModel, Field

import app.common.basic_exceptions as exc
from app.common import constants
from app.common.dim import device_id_base
from app.core.control import agent_control, control_base, fm_control, oob_control
from app.routers import api_metadata
from app.routers.control import response_models

# The timeout value of the Is OS Ready endpoint.
DEFAULT_IS_OS_READY_TIMEOUT = 30
MIN_IS_OS_READY_TIMEOUT = 1
MAX_IS_OS_READY_TIMEOUT = 600

logger = logging.getLogger(__name__)


class AggregationControlAction(Enum):
    """An enumeration of Aggregation Control action.

    This Enum class is used to represent different types of
    Aggregation Control action-type.

    Attributes:
        CONNECT (str):
            Represents a connect action.

        DISCONNECT (str):
            Represents a disconnect action.

    """

    CONNECT = "connect"
    DISCONNECT = "disconnect"


class PowerControlAction(Enum):
    """An enumeration of Power Control action.

    This Enum class is used to represent different types of
    Power Control action-type.

    Attributes:
        ON (str):
            Represents a power-on action.

        OFF (str):
            Represents a power-off action.

        FORCE_OFF (str):
            Represents a force power-off action.

        RESET (str):
            Represents a reset-cpu action.

    """

    ON = "on"
    OFF = "off"
    FORCE_OFF = "force-off"
    RESET = "reset"


# Define Device Control API router.
router = APIRouter(
    prefix=f"{constants.BASE_URL}/v1",
    tags=[api_metadata.DEVICE_CONTROL_API],
)


def _get_true_device_ids(upstream_device_id: str, downstream_device_id: str) -> tuple[str, str]:
    """Get the true upstream and downstream device IDs based on switch port type.

    Args:
        upstream_device_id (str): The Device ID of the upstream side device.
        downstream_device_id (str): The Device ID of the downstream side device.

    Returns:
        tuple[str, str]: A tuple containing the true upstream device ID and true downstream device ID.

    Example:
        true_upstream_device_id, true_downstream_device_id = _get_true_device_ids("upstream_id", "downstream_id")
    """
    # get true upstream_device_id
    true_upstream_device_id = device_id_base.get_device_id_of_switch_port_type(
        device_id=upstream_device_id, switch_port_type=constants.SwitchPortType.USP
    )
    logger.debug(
        "True upstream device ID determined.",
        extra={"true_upstream_device_id": true_upstream_device_id},
    )
    if true_upstream_device_id is None:
        true_upstream_device_id = upstream_device_id

    # get true downstream_device_id
    true_downstream_device_id = device_id_base.get_device_id_of_switch_port_type(
        device_id=downstream_device_id, switch_port_type=constants.SwitchPortType.DSP
    )
    logger.debug(
        "True downstream device ID determined.",
        extra={"true_downstream_device_id": true_downstream_device_id},
    )
    if true_downstream_device_id is None:
        true_downstream_device_id = downstream_device_id

    return true_upstream_device_id, true_downstream_device_id


class DeviceAggregationControlRequestModel(BaseModel):
    """Request Model of Device Aggregation Control."""

    downstream_device_id: UUID4 = Field(
        alias="destinationDeviceID",
        description="The Device ID of aggregation control target downstream side device.",
        examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
    )

    action: AggregationControlAction = Field(
        description=(
            "Aggregation Control action for the specified upstream side device and downstream side device.  "
            '\n "connect": '
            "Connect the aggregation state of the specified upstream side device and downstream side device.  "
            '\n "disconnect": '
            "Disconnect the aggregation state of the specified upstream side device and downstream side device.  "
        ),
        examples=[AggregationControlAction.CONNECT.value, AggregationControlAction.DISCONNECT.value],
    )


# Device Aggregation Control endpoint
@router.put(
    path="/devices/{sourceDeviceID}/aggregations",
    response_model=response_models.DeviceAggregationControlResponseModel,
    status_code=http.HTTPStatus.OK.value,
    description="Controls the aggregation state between the specified upstream side device and downstream side device.",
    response_description=(
        "Device aggregation control successful."
        " Returns this even if the specified upstream side device and downstream side device"
        " were already in the desired aggregation state."
    ),
    responses={
        400: api_metadata.error_cases_spec_factory(
            case_description="Bad request.",
            sub_case_descriptions=["Your request is not supported for the specified device."],
        ),
        404: api_metadata.error_cases_spec_factory(
            case_description="The specified resource not found.",
            sub_case_descriptions=["The specified path not found.", "The specified device not found."],
        ),
        409: api_metadata.error_case_spec_factory(
            case_description="Your request is conflict to the specified device state.",
        ),
        422: api_metadata.validation_error_case_spec_factory(
            case_description="The request parameter validation error.",
        ),
        500: api_metadata.error_cases_spec_factory(
            case_description="Internal server error.",
            sub_case_descriptions=[
                "Encountered a Control Object error.",
                "Encountered an application internal error.",
                "Encountered a Dependency service error.",
                "The configuration is invalid.",
            ],
        ),
        503: api_metadata.error_case_spec_factory(
            case_description="The specified device is busy.",
        ),
    },
    response_class=JSONResponse,
    name="Device Aggregation Control",
)
def device_aggregation_control_api(
    request_body: DeviceAggregationControlRequestModel,
    upstream_device_id: Annotated[
        UUID4,
        Path(
            alias="sourceDeviceID",
            description="The Device ID of aggregation control target upstream side device.",
            examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
        ),
    ],
) -> response_models.DeviceAggregationControlResponseModel:
    """Control the connection between the upstream side device and the downstream side device.

    This endpoint allows for connecting and disconnecting the upstream side device to/from the downstream side device.
    The action performed is based on the `action` parameter provided in the `request_body`.

    Args:
        request_body (DeviceAggregationControlRequestModel):
            The body of the request containing the action to perform and the target device 'destinationDeviceID'.

        upstream_device_id (UUID4): The 'Device ID' of the upstream side device .

    Returns:
        DeviceAggregationControlResponseModel: The response model of the result of the aggregation control operation.

    Note:
        Actions:
        - If `action="connect"`, the specified the downstream side device is connected to upstream side device.
        - If `action="disconnect"`, the specified the downstream side device is disconnected from upstream side device.

        Error Handling:
        - Any exceptions raised by functions called within this endpoint will be handled by the error handler functions
        defined in `src/app/routers/error_handlers.py`.

    """
    logger.info(
        "Device Aggregation Control start.",
        extra={
            "sourceDeviceID": str(upstream_device_id),
            "destinationDeviceID": str(request_body.downstream_device_id),
            "action": request_body.action.value,
        },
    )

    true_upstream_device_id, true_downstream_device_id = _get_true_device_ids(
        upstream_device_id=str(upstream_device_id), downstream_device_id=str(request_body.downstream_device_id)
    )

    upstream_device = fm_control.FMControlTargetDevice(device_id=true_upstream_device_id)
    downstream_device = fm_control.FMControlTargetDevice(device_id=true_downstream_device_id)
    device_pair = fm_control.FMControlTargetDevicePair(
        upstream_device=upstream_device, downstream_device=downstream_device
    )

    if request_body.action.value == AggregationControlAction.CONNECT.value:
        fm_control.FMController.connect(device_pair=device_pair)
    else:  # The 'action' specified by the client is "disconnect".
        fm_control.FMController.disconnect(device_pair=device_pair)

    return response_models.DeviceAggregationControlResponseModel(
        upstream_device_id=str(upstream_device_id), downstream_device_id=str(request_body.downstream_device_id)
    )


class PowerControlRequestModel(BaseModel):
    """Request Model of Power Control."""

    action: PowerControlAction = Field(
        description=(
            "Power control action for the specified device.  "
            '\n "on": Powers on the specified device.  '
            '\n "off": Powers off the specified device. If the host CPU is specified it will be shut down.  '
            '\n "force-off": Force to power off the specified device regardless of the device state.  '
            '\n "reset": Resets the specified host CPU. Only host CPU is supported as a target.  '
        ),
        examples=[
            PowerControlAction.ON.value,
            PowerControlAction.OFF.value,
            PowerControlAction.FORCE_OFF.value,
            PowerControlAction.RESET.value,
        ],
    )


def _perform_power_off(target_device: control_base.PowerControlTargetDevice) -> None:
    """Perform power off operation for the specified target device.

    This function determines the method of power off (Agent or OOB) based on whether the Agent is supported.
    Agent support is determined by whether an instance of the ControlTargetAgent class can be generated.

    - If the specified device supports an Agent:
        - Shut down through the Agent.
    - If the specified device does not support an Agent (ControlTargetAgent instance cannot be generated), perform power
        off through OOB.

    Args:
        target_device (control_base.PowerControlTargetDevice): The target device object to be powered off.

    """
    try:
        target_agent = agent_control.ControlTargetAgent(host_cpu_device_id=target_device.device_id)
        can_generate_agent = True
    except exc.BaseHWControlError:
        can_generate_agent = False

    if can_generate_agent:
        agent_control.AgentController.os_shutdown(target_device=target_device, target_agent=target_agent)
    else:
        oob_control.OOBController.power_off(target_device=target_device)


# Power Control endpoint
@router.put(
    path="/devices/{deviceID}/power",
    status_code=http.HTTPStatus.OK.value,
    description="Controls the power state of the specified target device.",
    response_description=(
        "Power control successful."
        " Returns this even if the specified target device was already in the desired power state."
    ),
    responses={
        400: api_metadata.error_cases_spec_factory(
            case_description="Bad request.",
            sub_case_descriptions=["Your request is not supported for the specified device."],
        ),
        404: api_metadata.error_cases_spec_factory(
            case_description="The specified resource not found.",
            sub_case_descriptions=["The specified path not found.", "The specified device not found."],
        ),
        409: api_metadata.error_case_spec_factory(
            case_description="Your request is conflict to the specified device state.",
        ),
        422: api_metadata.validation_error_case_spec_factory(
            case_description="The request parameter validation error.",
        ),
        500: api_metadata.error_cases_spec_factory(
            case_description="Internal server error.",
            sub_case_descriptions=[
                "Encountered an Control Object error.",
                "Encountered an application internal error.",
                "Encountered a Dependency service error.",
                "The configuration is invalid.",
            ],
        ),
        503: api_metadata.error_case_spec_factory(
            case_description="The specified device is busy.",
        ),
    },
    response_class=JSONResponse,
    name="Power Control",
)
def power_control_api(
    request_body: PowerControlRequestModel,
    device_id: Annotated[
        UUID4,
        Path(
            alias="deviceID",
            description="The Device ID of power control target device.",
            examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
        ),
    ],
) -> response_models.PowerControlResponseModel:
    """Control the power state of the specified device.

    This endpoint allows for controlling the power state (on, off, reset, force off) of a specified device.
    The action performed is based on the `action` parameter provided in the `request_body`.

    Args:
        request_body (PowerControlRequestModel): The body of the request containing the action to perform.
        device_id (UUID4): The 'Device ID' of power control target device.

    Returns:
        PowerControlResponseModel: The response model of the result of the power control.

    Note:
        Actions:
        - If `action="off"` and the device type is CPU, the OS running on the CPU device will be shut down.
        - The `reset` action is supported only for devices of type CPU.
        - The `force_off` action forces the power off for the specified device, regardless of the device type.

        Error Handling:
        - Any exceptions raised by functions called within this endpoint will be handled by the error handler functions
        defined in `src/app/routers/error_handlers.py`.

    """
    logger.info(
        "Power Control start.",
        extra={"deviceID": str(device_id), "action": request_body.action.value},
    )

    target_device = control_base.PowerControlTargetDevice(device_id=str(device_id))

    if request_body.action.value == PowerControlAction.ON.value:
        oob_control.OOBController.power_on(target_device=target_device)

    elif request_body.action.value == PowerControlAction.FORCE_OFF.value:
        oob_control.OOBController.force_off(target_device=target_device)

    elif request_body.action.value == PowerControlAction.RESET.value:
        oob_control.OOBController.reset(target_device=target_device)

    else:  # The 'action' specified by the client is "off".
        _perform_power_off(target_device=target_device)

    return response_models.PowerControlResponseModel(device_id=target_device.device_id)


# Is OS Ready endpoint
@router.get(
    path="/cpu/{CPUDeviceID}/is-os-ready",
    status_code=http.HTTPStatus.OK.value,
    description="Check if the host OS is running on the specified host CPU.",
    responses={
        400: api_metadata.error_cases_spec_factory(
            case_description="Bad request.",
            sub_case_descriptions=[
                "Your request is not supported for the specified host CPU.",
                "The specified host CPU power state is OFF.",
            ],
        ),
        404: api_metadata.error_cases_spec_factory(
            case_description="The specified resource not found.",
            sub_case_descriptions=["The specified path not found.", "The specified device not found."],
        ),
        422: api_metadata.validation_error_case_spec_factory(
            case_description="The request parameter validation error.",
        ),
        500: api_metadata.error_cases_spec_factory(
            case_description="Internal server error.",
            sub_case_descriptions=[
                "Encountered an Control object error.",
                "Encountered an application internal error.",
                "Encountered a Dependency service error.",
                "The configuration is invalid.",
            ],
        ),
    },
    response_class=JSONResponse,
    name="Is OS Ready",
)
def is_os_ready_api(
    cpu_device_id: Annotated[
        UUID4,
        Path(
            alias="CPUDeviceID",
            description="The Device ID of the host CPU that checks if the host OS is running.",
            examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
        ),
    ],
    time_out: Annotated[
        int,
        Query(
            alias="timeOut",
            description="The timeout value for checking if the host OS is running. Please specify in seconds.",
            examples=[
                MIN_IS_OS_READY_TIMEOUT,
                DEFAULT_IS_OS_READY_TIMEOUT,
                MAX_IS_OS_READY_TIMEOUT,
            ],
            ge=MIN_IS_OS_READY_TIMEOUT,
            le=MAX_IS_OS_READY_TIMEOUT,
        ),
    ] = DEFAULT_IS_OS_READY_TIMEOUT,
) -> response_models.IsOSReadyResponseModel:
    """Check if the OS is ready on the specified CPU device.

    This endpoint checks if the operating system is running on the specified CPU device by querying the status through
    an agent.

    Args:
        cpu_device_id (UUID4):
            The 'Device ID' of the host CPU you want to check.

        time_out (int):
            The timeout value for the agent request, in seconds.
            Must be between MIN_IS_OS_READY_TIMEOUT and MAX_IS_OS_READY_TIMEOUT.
            Defaults to 30.

    Returns:
        IsOSReadyResponseModel: The response model of the result of is OS ready check.

    Error Handling:
        - Any exceptions raised by functions called within this endpoint will be handled by the error handler functions
        defined in `src/app/routers/error_handlers.py`.

    """
    logger.info("Is OS Ready start.", extra={"CPUDeviceID": str(cpu_device_id), "timeOut": time_out})

    target_device = control_base.PowerControlTargetDevice(device_id=str(cpu_device_id))
    target_agent = agent_control.ControlTargetAgent(host_cpu_device_id=str(cpu_device_id))

    os_ready_status = agent_control.AgentController.is_os_ready(
        target_device=target_device, target_agent=target_agent, timeout=time_out
    )

    return response_models.IsOSReadyResponseModel(status=os_ready_status, ip_address=target_agent.ip_address)

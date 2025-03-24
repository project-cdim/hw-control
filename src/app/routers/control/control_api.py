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

"""Device Control API

This module defines Device Control API and its endpoints.

"""

import uuid
from enum import Enum

from pydantic import BaseModel, Field, UUID4
from fastapi import APIRouter, Request, Query, Path
from fastapi.responses import JSONResponse

from app.routers import api_metadata
from app.routers.control import control_responses

from app.core.control import control_base
from app.core.control import fm_control
from app.core.control import oob_control
from app.core.control import agent_control

import app.common.basic_exceptions as exc
from app.common.utils.log import LOGGER
from app.common.messages import message
from app.common import constants

# The timeout value of the Is OS Ready endpoint.
DEFAULT_IS_OS_READY_TIMEOUT = 30
MIN_IS_OS_READY_TIMEOUT = 1
MAX_IS_OS_READY_TIMEOUT = 600


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
    responses={
        422: {
            "description": "HTTP status code 422 will not occur.",
        }  # TODO:Remove the default response schema specification for 422 cases set in FastAPI.
    },
)


class AggregationControlRequestBody(BaseModel):
    """The HTTP Request Body schema of Aggregation Control."""

    device_id: UUID4 = Field(
        alias="deviceID",
        description="The Device ID of aggregation control target device.",
        examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
    )

    action: AggregationControlAction = Field(
        description=(
            "Aggregation Control action for the specified host CPU and target device.  "
            '\n "connect": Connect the aggregation state of the specified host CPU and target device.  '
            '\n "disconnect": Disconnect the aggregation state of the specified host CPU and target device.  '
        ),
        examples=[AggregationControlAction.CONNECT.value, AggregationControlAction.DISCONNECT.value],
    )


# Aggregation Control endpoint
@router.put(
    path="/cpu/{CPUDeviceID}/aggregations",
    response_model=control_responses.AggregationControlResponseBody,
    description="Controls the aggregation state between the specified host CPU and target device.",
    response_class=JSONResponse,
    name="Aggregation Control",
)
def aggregation_control_api(
    request: Request,  # TODO: This code should be removed as you implement custom middleware.
    request_body: AggregationControlRequestBody,
    cpu_device_id: UUID4 = Path(
        alias="CPUDeviceID",
        description="The Device ID of aggregation control target host CPU.",
        examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
    ),
) -> JSONResponse:
    """
    Control the connection between a CPU and a target device.

    This endpoint allows for connecting and disconnecting a CPU device to/from a specified target device.
    The action performed is based on the `action` parameter provided in the `request_body`.

    Args:
        request (Request): The request object that containing the requested content.

        request_body (AggregationControlRequestBody):
            The body of the request containing the action to perform and the target device 'Device ID'.

        cpu_device_id (UUID4): The 'Device ID' of the host CPU device.

    Returns:
        JSONResponse: The response containing the result of the aggregation control operation.

    Note:
        Actions:
        - If `action="connect"`, the specified target device is connected to the host CPU.
        - If `action="disconnect"`, the specified target device is disconnected from the host CPU.

        Error Handling:
        - Any exceptions raised by functions called within this endpoint will be handled by the error handler functions
        defined in `src/app/routers/error_handlers.py`.

    """
    message.set_request_id(
        request_id=str(uuid.uuid4())
    )  # TODO: This code should be moved to custom middleware as part of the custom middleware implementation.

    LOGGER.info(
        message.HttpRequestLog.create_from_request(request=request, body_parameter=request_body).to_json_encodable()
    )  # TODO: This code should be moved to custom middleware as part of the custom middleware implementation.

    host_cpu = fm_control.FmControlTargetDevice(device_id=str(cpu_device_id))
    target_device = fm_control.FmControlTargetDevice(device_id=str(request_body.device_id))
    device_pair = fm_control.FmControlTargetDevicePair(host_cpu=host_cpu, target_device=target_device)

    device_pair.get_lock()
    try:
        if request_body.action.value == AggregationControlAction.CONNECT.value:
            fm_control.FmController.connect(device_pair=device_pair)
        else:  # The 'action' specified by the client is "disconnect".
            fm_control.FmController.disconnect(device_pair=device_pair)
    finally:
        device_pair.release_lock()

    response = control_responses.generate_api_response(
        response_body=control_responses.AggregationControlResponseBody(
            cpu_device_id=device_pair.host_cpu.device_id, device_id=device_pair.target_device.device_id
        )
    )
    LOGGER.info(
        message.HttpResponseLog.create_from_json_response(response=response).to_json_encodable()
    )  # TODO: This code should be moved to custom middleware as part of the custom middleware implementation.

    return response


class PowerControlRequestBody(BaseModel):
    """The HTTP Request Body schema of Power Control."""

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
    except exc.BaseHwControlError:
        can_generate_agent = False

    if can_generate_agent:
        agent_control.AgentController.os_shutdown(target_device=target_device, target_agent=target_agent)
    else:
        oob_control.OobController.power_off(target_device=target_device)


# Power Control endpoint
@router.put(
    path="/devices/{deviceID}/power",
    response_model=control_responses.PowerControlResponseBody,
    description="Controls the power state of the specified target device.",
    response_class=JSONResponse,
    name="Power Control",
)
def power_control_api(
    request: Request,  # TODO: This code should be removed as you implement custom middleware.
    request_body: PowerControlRequestBody,
    device_id: UUID4 = Path(
        alias="deviceID",
        description="The Device ID of power control target device.",
        examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
    ),
) -> JSONResponse:
    """
    Control the power state of the specified device.

    This endpoint allows for controlling the power state (on, off, reset, force off) of a specified device.
    The action performed is based on the `action` parameter provided in the `request_body`.

    Args:
        request (Request): The request object that containing the requested content.
        request_body (PowerControlRequestBody): The body of the request containing the action to perform.
        device_id (UUID4): The 'Device ID' of power control target device.

    Returns:
        JSONResponse: The response containing the result of the power control.

    Note:
        Actions:
        - If `action="off"` and the device type is CPU, the OS running on the CPU device will be shut down.
        - The `reset` action is supported only for devices of type CPU.
        - The `force_off` action forces the power off for the specified device, regardless of the device type.

        Error Handling:
        - Any exceptions raised by functions called within this endpoint will be handled by the error handler functions
        defined in `src/app/routers/error_handlers.py`.

    """
    message.set_request_id(
        request_id=str(uuid.uuid4())
    )  # TODO: This code should be moved to custom middleware as part of the custom middleware implementation.

    LOGGER.info(
        message.HttpRequestLog.create_from_request(request=request, body_parameter=request_body).to_json_encodable()
    )  # TODO: This code should be moved to custom middleware as part of the custom middleware implementation.

    target_device = control_base.PowerControlTargetDevice(device_id=str(device_id))

    target_device.get_lock()
    try:
        if request_body.action.value == PowerControlAction.ON.value:
            oob_control.OobController.power_on(target_device=target_device)

        elif request_body.action.value == PowerControlAction.FORCE_OFF.value:
            oob_control.OobController.force_off(target_device=target_device)

        elif request_body.action.value == PowerControlAction.RESET.value:
            oob_control.OobController.reset(target_device=target_device)

        else:  # The 'action' specified by the client is "off".
            _perform_power_off(target_device=target_device)

    finally:
        target_device.release_lock()

    response = control_responses.generate_api_response(
        response_body=control_responses.PowerControlResponseBody(device_id=target_device.device_id)
    )
    LOGGER.info(
        message.HttpResponseLog.create_from_json_response(response=response).to_json_encodable()
    )  # TODO: This code should be moved to custom middleware as part of the custom middleware implementation.

    return response


# Is OS Ready endpoint
@router.get(
    path="/cpu/{CPUDeviceID}/is-os-ready",
    response_model=control_responses.IsOsReadyResponseBody,
    description="Check if the host OS is running on the specified host CPU.",
    response_class=JSONResponse,
    name="Is OS Ready",
)
def is_os_ready_api(
    request: Request,  # TODO: This code should be removed as you implement custom middleware.
    cpu_device_id: UUID4 = Path(
        alias="CPUDeviceID",
        description="The Device ID of the host CPU that checks if the host OS is running.",
        examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
    ),
    time_out: int = Query(
        default=DEFAULT_IS_OS_READY_TIMEOUT,
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
) -> JSONResponse:
    """
    Check if the OS is ready on the specified CPU device.

    This endpoint checks if the operating system is running on the specified CPU device by querying the status through
    an agent.

    Args:
        request (Request): The request object that containing the requested content.

        cpu_device_id (UUID4):
            The 'Device ID' of the host CPU you want to check.

        time_out (int):
            The timeout value for the agent request, in seconds.
            Must be between MIN_IS_OS_READY_TIMEOUT and MAX_IS_OS_READY_TIMEOUT.
            Defaults to 30.

    Returns:
        JSONResponse:
            HTTP Status and Response Body.

    Error Handling:
        - Any exceptions raised by functions called within this endpoint will be handled by the error handler functions
        defined in `src/app/routers/error_handlers.py`.

    """
    message.set_request_id(
        request_id=str(uuid.uuid4())
    )  # TODO: This code should be moved to custom middleware as part of the custom middleware implementation.
    LOGGER.info(
        message.HttpRequestLog.create_from_request(request=request).to_json_encodable()
    )  # TODO: This code should be moved to custom middleware as part of the custom middleware implementation.

    target_device = control_base.PowerControlTargetDevice(device_id=str(cpu_device_id))
    target_agent = agent_control.ControlTargetAgent(host_cpu_device_id=str(cpu_device_id))

    os_ready_status = agent_control.AgentController.is_os_ready(
        target_device=target_device, target_agent=target_agent, timeout=time_out
    )

    response = control_responses.generate_api_response(
        response_body=control_responses.IsOsReadyResponseBody(
            status=os_ready_status, ip_address=target_agent.ip_address
        )
    )
    LOGGER.info(
        message.HttpResponseLog.create_from_json_response(response=response).to_json_encodable()
    )  # TODO: This code should be moved to custom middleware as part of the custom middleware implementation.

    return response

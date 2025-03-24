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

"""Generate 'Device Control API' Response."""
from http import HTTPStatus
from typing import Any

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field


class BaseResponseBody(BaseModel):
    """Base class of 'Device Control API'.

    Attributes:
        None

    """


class AggregationControlResponseBody(BaseResponseBody):
    """The HTTP Response Body schema of Aggregation Control."""

    cpu_device_id: str = Field(
        serialization_alias="CPUDeviceID",
        description="The Device ID of aggregation control target host CPU.",
        examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
    )

    device_id: str = Field(
        serialization_alias="deviceID",
        description="The Device ID of aggregation control target device.",
        examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
    )


class PowerControlResponseBody(BaseResponseBody):
    """The HTTP Response Body schema of Power Control."""

    device_id: str = Field(
        serialization_alias="deviceID",
        description="The Device ID of power control target device.",
        examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
    )


class IsOsReadyResponseBody(BaseResponseBody):
    """The HTTP Response Body schema of Is OS Ready."""

    status: bool = Field(
        description=(
            "The host OS running state.  "
            "\n  True: The target host OS is running.  "
            "\n  False: The target host OS is not running.  "
        ),
    )
    ip_address: str = Field(
        serialization_alias="IPAddress",
        description="The IP address of target host OS.",
        examples=[],
    )


class ErrorResponseBody(BaseResponseBody):
    """The HTTP Response Body schema of error case."""

    code: str = Field(
        description="The error code of hw-control.",
    )
    message: Any = Field(
        description="The error message.",
    )


def generate_api_response(response_body: BaseResponseBody, status_code: int = HTTPStatus.OK.value) -> JSONResponse:
    """Generate HTTP Response object for Device Control API.

    Generate HTTP Response object in JSON format for Device Control API.

    Args:
        response_body (BaseResponseBody):
            JSON type data to be set in the HTTP response body.

        status_code (int, optional):
            JSON type data to be set in the HTTP response body.
            Defaults to 200.

    Returns:
        JSONResponse:
            The FastAPI response object in JSON format.

    """
    return JSONResponse(status_code=status_code, content=jsonable_encoder(response_body))

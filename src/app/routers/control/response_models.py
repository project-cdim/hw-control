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

"""Define Response models for Device Control API."""

from pydantic import BaseModel, Field


class DeviceAggregationControlResponseModel(BaseModel):
    """The Response Model of Device Aggregation Control."""

    upstream_device_id: str = Field(
        serialization_alias="sourceDeviceID",
        description="The Device ID of aggregation control target upstream side device.",
        examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
    )

    downstream_device_id: str = Field(
        serialization_alias="destinationDeviceID",
        description="The Device ID of aggregation control target downstream side device.",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )


class PowerControlResponseModel(BaseModel):
    """The Response Model of Power Control."""

    device_id: str = Field(
        serialization_alias="deviceID",
        description="The Device ID of power control target device.",
        examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
    )


class IsOSReadyResponseModel(BaseModel):
    """The Response Model of Is OS Ready."""

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
        examples=["192.168.1.100"],
    )

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

"""Constant definition for Fast API

Define constants used in API definition of Fast API

"""
from typing import List
from pydantic import BaseModel

# string constant
NAME = "name"
MODEL = "model"
DESCRIPTION = "description"
APPLICATION = "application/json"

# Fast API tag
TAG_LIST = "deviceList"
TAG_ALL_DEVICES = "allResource"
TAG_INFO = "Information"
TAG_METRIC = "MetricData"
TAG_RESOURCE = "ResourceData"


# Fast API Docs tag
TAGS_METADATA = [
    {NAME: TAG_LIST, DESCRIPTION: "API for retrieving the list of device IDs"},
    {NAME: TAG_ALL_DEVICES, DESCRIPTION: "API for retrieving information on all resources at once"},
    {NAME: TAG_INFO, DESCRIPTION: "API for retrieving device information for the specified device ID"},
    {NAME: TAG_METRIC, DESCRIPTION: "API for retrieving metric information for the specified device ID"},
    {NAME: TAG_RESOURCE, DESCRIPTION: "API for retrieving resource information for the specified device ID"},
]


class DeviceInformation(BaseModel):
    """Device Information

    Device Information data class

    """

    # NOSONAR to match the names defined in the response format (JSON)
    deviceID: str = ""  # NOSONAR
    type: str = ""
    infoTimestamp: str = ""  # NOSONAR


class ErrorInformation(BaseModel):
    """Errors Information

    Error information data class for the cause of acquisition failure
    """

    errorCode: str = ""  # NOSONAR
    errorMessage: str = ""  # NOSONAR


class IncompleteList(BaseModel):
    """Incomplete list information

    Incomplete List Device information data class

    """

    # NOSONAR to match the names defined in the response format (JSON)
    errorInfo: List[ErrorInformation] = []  # NOSONAR
    deviceID: str = ""  # NOSONAR
    infoTimestamp: str = ""  # NOSONAR


class ResourceList(BaseModel):
    """Resource list information

    Resource list information data class

    """

    # NOSONAR to match the names defined in the response format (JSON)
    deviceList: list[dict] = []  # NOSONAR
    incompleteDeviceList: list[dict] = []  # NOSONAR
    infoTimestamp: str = ""  # NOSONAR


class DeviceResourceList(BaseModel):
    """Resource list information

    Resource list information data class

    """

    # NOSONAR to match the names defined in the response format (JSON)
    deviceList: list[dict] = []  # NOSONAR
    infoTimestamp: str = ""  # NOSONAR


class IncompleteResourceList(BaseModel):
    """Resource list information

    Resource list information data class

    """

    # NOSONAR to match the names defined in the response format (JSON)
    incompleteDeviceList: list[dict] = []  # NOSONAR
    infoTimestamp: str = ""  # NOSONAR


# Get device information API Definition
DEVICES_DESC_STR = "## Get device information (JSON format).\n\n\
    Gets configuration information for the device ID specified in deviceID."

# Device ID list information acquisition API Definition
DEVICE_LIST_DESC_STR = "## Gets a list of devices (JSON format).\n\n\
    Gets a list of device IDs for the device type specified in type.\n\n\
    If no device type is specified, returns a list of all device IDs."

# Batch acquisition of all resource information API Definition
BATCH_ACQUISITION_DESC_STR = "## Gets all resource information (JSON format).\n\n\
    Gets all device information for the device type specified in type.\n\n\
    If no device type is specified, returns all resource information for all devices."

# Get metric information API Definition
METRICS_DESC_STR = "## Get metric information (JSON format).\n\n\
    Gets metric information for the device ID specified in deviceID."

# Get resource information API Definition
RESOURCE_DESC_STR = "## Get resource information (JSON format).\n\n\
    Gets configuration and metric information for the device ID specified in deviceID."

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

"""HW control function - constant definition"""
from enum import Enum


# hw-control API base URL.
BASE_URL = "/cdim/api"

# Date and time format
TIME_STAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"

# Correlation ID header
CORRELATION_ID_HEADER = "x-correlation-id"

# Default correlation ID value when not set in context variable (asgi_correlation_id.correlation_id).
# This value is used as a fallback when the correlation ID is not stored in the context variable.
CORRELATION_ID_DEFAULT_VALUE = "-"


class DeviceType(Enum):
    """
    An enumeration of device types.

    This Enum class is used to represent different types of devices.

    Attributes:
        CPU: Represents a CPU device.
        MEMORY: Represents a MEMORY device.
        STORAGE: Represents a STORAGE device.
        NIC: Represents a Network Interface device.
        GPU: Represents a GPU device.
        GC: Represents a Graphic Controller device.
        SWITCH: Represents a SWITCH device.
        VM: Represents a Virtual Media device.
        SFA: Represents a source fabric adapter device.
        DFA: Represents a destination fabric adapter device.
    """

    CPU = "CPU"
    MEMORY = "memory"
    STORAGE = "storage"
    NIC = "networkInterface"
    GPU = "GPU"
    GC = "graphicController"
    SWITCH = "switch"
    VM = "virtualMedia"
    SFA = "sourceFabricAdapter"
    DFA = "destinationFabricAdapter"


class ManagerType(Enum):
    """An enumeration of 'Manager Type'.

    This Enum class is used to represent different types of
    'manager type'.

    Attributes:
        FM (str):
            Represents the 'manager type' of 'FM Plugin'.

        OOB (str):
            Represents the 'manager-type' of 'OOB Plugin'.

    """

    FM = "FM"
    OOB = "OOB"


class SwitchPortType(Enum):
    """An enumeration of 'Switch Port Type'.

    This Enum class is used to represent different types of
    'Switch Port Type'.

    Attributes:
        USP (str):
            Represents a 'Upstream Switch Port' of the switch.

        DSP (str):
            Represents a 'Downstream Switch Port' of the switch.

    """

    USP = "USP"
    DSP = "DSP"


class DevicePowerState(Enum):
    """An enumeration of Device Power State.

    This Enum class is used to represent different types of
    device power state.

    Attributes:
        ON (str):
            Represents device power state is ON.

        OFF (str):
            Represents device power state is OFF.

        POWERING_ON (str):
            Represents device power state is PoweringOn.

        POWERING_OFF (str):
            Represents device power state is PoweringOff.

        PAUSED (str):
            Represents device power state is Paused.

        UNKNOWN (str):
            Represents device power state is unknown.

    """

    ON = "On"
    OFF = "Off"
    POWERING_ON = "PoweringOn"
    POWERING_OFF = "PoweringOff"
    PAUSED = "Paused"
    UNKNOWN = "Unknown"


class ContentType(Enum):
    """An enumeration of HTTP header 'Content-Type'.

    This Enum class is used to represent different types of
    HTTP header 'Content-Type'.

    Attributes:
        APPLICATION_JSON (str):
            Represents Content-Type is application/json.
    """

    APPLICATION_JSON = "application/json"

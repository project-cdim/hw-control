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

"""basic exceptions package.

file_path: /app/common/basic_exceptions/

This package provides basic exceptions for hw-control.
"""

from app.common.basic_exceptions.authentication_exceptions import (
    OOBAuthenticationHWControlError,
)
from app.common.basic_exceptions.bad_request_exceptions import (
    HostCPUPowerOffBadRequestHWControlError,
    RequestNotSupportedHWControlError,
)
from app.common.basic_exceptions.base_exceptions import (
    ERROR_CODE,
    ERROR_MESSAGE,
    AuthenticationHWControlError,
    BadRequestHWControlError,
    BaseHWControlError,
    ConfigurationHWControlError,
    ControlObjectHWControlError,
    DependencyServiceHWControlError,
    DeviceNotFoundHWControlError,
    InternalHWControlError,
    RequestConflictHWControlError,
    ResourceBusyHWControlError,
    UnknownHWControlError,
)
from app.common.basic_exceptions.configuration_exceptions import (
    APIUsageHWControlError,
    DeviceIDFileIncorrectHWControlError,
    DeviceIDFileNotFoundHWControlError,
    DeviceIDFileUpdateHWControlError,
    InvalidDeviceTypeParameterHWControlError,
    InvalidLogMessageParameterHWControlError,
    InvalidSerialNumberConfigFileIncorrectHWControlError,
    InvalidSerialNumberConfigFileNotFoundHWControlError,
    InvalidTypeDeviceIDHWControlError,
    ManagerIDHWControlError,
    PluginGetInstanceHWControlError,
    PluginRespondNoneHWControlError,
    PluginRespondUnExpectedTypeHWControlError,
)
from app.common.basic_exceptions.control_object_exceptions import (
    AgentConnectFailureHWControlError,
    AgentGetInformationFailureHWControlError,
    CPUResetFailureHWControlError,
    FMConnectFailureHWControlError,
    FMDisconnectFailureHWControlError,
    PowerOffFailureHWControlError,
    PowerOnFailureHWControlError,
)
from app.common.basic_exceptions.internal_exceptions import (
    UnexpectedExceptionHWControlError,
)
from app.common.basic_exceptions.resource_busy_exceptions import (
    DeviceBusyHWControlError,
)
from app.common.basic_exceptions.resource_not_found_exceptions import (
    DeviceIDNotFoundHWControlError,
    DownstreamDeviceNotFoundHWControlError,
    HostCPUAndDeviceNotFoundHWControlError,
    HostCPUNotFoundHWControlError,
    ResourceNotFoundHWControlError,
    SwitchNotFoundHWControlError,
    UpstreamDeviceNotFoundHWControlError,
)

__all__ = [
    "ERROR_CODE",
    "ERROR_MESSAGE",
    "APIUsageHWControlError",
    "AgentConnectFailureHWControlError",
    "AgentGetInformationFailureHWControlError",
    "AuthenticationHWControlError",
    "BadRequestHWControlError",
    "BaseHWControlError",
    "CPUResetFailureHWControlError",
    "ConfigurationHWControlError",
    "ControlObjectHWControlError",
    "DependencyServiceHWControlError",
    "DeviceBusyHWControlError",
    "DeviceIDFileIncorrectHWControlError",
    "DeviceIDFileNotFoundHWControlError",
    "DeviceIDFileUpdateHWControlError",
    "DeviceIDNotFoundHWControlError",
    "DeviceNotFoundHWControlError",
    "DownstreamDeviceNotFoundHWControlError",
    "FMConnectFailureHWControlError",
    "FMDisconnectFailureHWControlError",
    "HostCPUAndDeviceNotFoundHWControlError",
    "HostCPUNotFoundHWControlError",
    "HostCPUPowerOffBadRequestHWControlError",
    "InternalHWControlError",
    "InvalidDeviceTypeParameterHWControlError",
    "InvalidLogMessageParameterHWControlError",
    "InvalidSerialNumberConfigFileIncorrectHWControlError",
    "InvalidSerialNumberConfigFileNotFoundHWControlError",
    "InvalidTypeDeviceIDHWControlError",
    "ManagerIDHWControlError",
    "OOBAuthenticationHWControlError",
    "PluginGetInstanceHWControlError",
    "PluginRespondNoneHWControlError",
    "PluginRespondUnExpectedTypeHWControlError",
    "PowerOffFailureHWControlError",
    "PowerOnFailureHWControlError",
    "RequestConflictHWControlError",
    "RequestNotSupportedHWControlError",
    "ResourceBusyHWControlError",
    "ResourceNotFoundHWControlError",
    "SwitchNotFoundHWControlError",
    "UnexpectedExceptionHWControlError",
    "UnknownHWControlError",
    "UpstreamDeviceNotFoundHWControlError",
]

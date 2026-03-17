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

"""basic exceptions package
file_path: /app/common/basic_exceptions/

This package provides basic exceptions for HWCONTROL.
"""

from app.common.basic_exceptions.base_exceptions import (
    BaseHWControlError,
    ERROR_CODE,
    ERROR_MESSAGE,
)

# ++++ Base Exception class +++++++++++++++++++++++++++++++++++++++++++#
from app.common.basic_exceptions.base_exceptions import (
    UnknownHWControlError,
    AuthenticationHWControlError,
    BadRequestHWControlError,
    ControlObjectHWControlError,
    ResourceBusyHWControlError,
    ConfigurationHWControlError,
    InternalHWControlError,
    RequestConflictHWControlError,
    DependencyServiceHWControlError,
    DeviceNotFoundHWControlError,
)

# ++++ Subclasses of AuthenticationHWControlError. ++++++++++++++++++++#
from app.common.basic_exceptions.authentication_exceptions import (
    OOBAuthenticationHWControlError,
)

# ++++ Subclasses of BadRequestHWControlError. ++++++++++++++++++++++++#
from app.common.basic_exceptions.bad_request_exceptions import (
    HostCPUPowerOffBadRequestHWControlError,
    RequestNotSupportedHWControlError,
)

# ++++ Subclasses of ControlObjectHWControlError. +++++++++++++++++++++#
from app.common.basic_exceptions.control_object_exceptions import (
    FMConnectFailureHWControlError,
    FMDisconnectFailureHWControlError,
    PowerOnFailureHWControlError,
    PowerOffFailureHWControlError,
    CPUResetFailureHWControlError,
    AgentConnectFailureHWControlError,
    AgentGetInformationFailureHWControlError,
)

# ++++ Subclasses of ResourceBusyHWControlError. ++++++++++++++++++++++#
from app.common.basic_exceptions.resource_busy_exceptions import (
    DeviceBusyHWControlError,
)

# ++++ Subclasses of ConfigurationHWControlError. +++++++++++++++++++++#
from app.common.basic_exceptions.configuration_exceptions import (
    APIUsageHWControlError,
    ManagerIDHWControlError,
    PluginGetInstanceHWControlError,
    PluginRespondUnExpectedTypeHWControlError,
    InvalidSerialNumberConfigFileNotFoundHWControlError,
    InvalidSerialNumberConfigFileIncorrectHWControlError,
    DeviceIDFileNotFoundHWControlError,
    DeviceIDFileIncorrectHWControlError,
    DeviceIDFileUpdateHWControlError,
    InvalidTypeDeviceIDHWControlError,
    InvalidDeviceTypeParameterHWControlError,
    InvalidLogMessageParameterHWControlError,
    PluginRespondNoneHWControlError,
)

# ++++ Subclasses of InternalHWControlError. ++++++++++++++++++++++++++#
from app.common.basic_exceptions.internal_exceptions import (
    UnexpectedExceptionHWControlError,
)

# ++++ Subclasses of DeviceNotFoundHWControlError. ++++++++++++++++++++#
from app.common.basic_exceptions.resource_not_found_exceptions import (
    HostCPUNotFoundHWControlError,
    HostCPUAndDeviceNotFoundHWControlError,
    SwitchNotFoundHWControlError,
    ResourceNotFoundHWControlError,
    DeviceIDNotFoundHWControlError,
    UpstreamDeviceNotFoundHWControlError,
    DownstreamDeviceNotFoundHWControlError,
)

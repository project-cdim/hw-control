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

"""basic exceptions package 
file_path: /app/common/basic_exceptions/

This package provides basic exceptions for HWCONTROL.
"""

from app.common.basic_exceptions.base_exceptions import (
    BaseHwControlError,
    ERROR_CODE,
    ERROR_MESSAGE,
)

# ++++ Base Exception class +++++++++++++++++++++++++++++++++++++++++++#
from app.common.basic_exceptions.base_exceptions import (
    UnknownHwControlError,
    AuthenticationHwControlError,
    BadRequestHwControlError,
    ControlObjectHwControlError,
    ResourceBusyHwControlError,
    ConfigurationHwControlError,
    InternalHwControlError,
    RequestConflictHwControlError,
    DependencyServiceHwControlError,
    DeviceNotFoundHwControlError,
)

# ++++ Subclasses of AuthenticationHwControlError. ++++++++++++++++++++#
from app.common.basic_exceptions.authentication_exceptions import (
    OobAuthenticationHwControlError,
)

# ++++ Subclasses of BadRequestHwControlError. ++++++++++++++++++++++++#
from app.common.basic_exceptions.bad_request_exceptions import (
    HostCpuPowerOffBadRequestHwControlError,
    RequestNotSupportedHwControlError,
)

# ++++ Subclasses of ControlObjectHwControlError. +++++++++++++++++++++#
from app.common.basic_exceptions.control_object_exceptions import (
    FmConnectFailureHwControlError,
    FmDisconnectFailureHwControlError,
    PowerOnFailureHwControlError,
    PowerOffFailureHwControlError,
    CpuResetFailureHwControlError,
    AgentConnectFailureHwControlError,
    AgentGetInformationFailureHwControlError,
)

# ++++ Subclasses of ResourceBusyHwControlError. ++++++++++++++++++++++#
from app.common.basic_exceptions.resource_busy_exceptions import (
    DeviceBusyHwControlError,
)

# ++++ Subclasses of ConfigurationHwControlError. +++++++++++++++++++++#
from app.common.basic_exceptions.configuration_exceptions import (
    ApiUsageHwControlError,
    ManagerIdHwControlError,
    PluginGetInstanceHwControlError,
    PluginRespondUnExpectedTypeHwControlError,
    InvalidSerialNumberConfigFileNotFoundHwControlError,
    InvalidSerialNumberConfigFileIncorrectHwControlError,
    DeviceIdFileNotFoundHwControlError,
    DeviceIdFileIncorrectHwControlError,
    DeviceIdFileUpdateHwControlError,
    InvalidTypeDeviceIdHwControlError,
    InvalidDeviceTypeParameterHwControlError,
    InvalidLogMessageParameterHwControlError,
    PluginRespondNoneHwControlError,
)

# ++++ Subclasses of InternalHwControlError. ++++++++++++++++++++++++++#
from app.common.basic_exceptions.internal_exceptions import (
    UnexpectedExceptionHwControlError,
)

# ++++ Subclasses of DeviceNotFoundHwControlError. ++++++++++++++++++++#
from app.common.basic_exceptions.resource_not_found_exceptions import (
    HostCpuNotFoundHwControlError,
    HostCpuAndDeviceNotFoundHwControlError,
    SwitchNotFoundHwControlError,
    ResourceNotFoundHwControlError,
    DeviceIdNotFoundHwControlError,
)

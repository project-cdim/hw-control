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

"""Subclasses of  DeviceNotFoundHwControlError.

This module defines an exception class that inherits from the 
DeviceNotFoundHwControlError class.
"""


from app.common.basic_exceptions.base_exceptions import DeviceNotFoundHwControlError


class HostCpuNotFoundHwControlError(DeviceNotFoundHwControlError):
    """HwControl Host CPU Not Found Error Detail Exception class

    This class is common detail exception class for HwControl defined
    exceptions of Host CPU Not Found Error.

    """

    error_code = "EF013BAS001"
    default_error_message: str = "The specified Host CPU is not found."


class HostCpuAndDeviceNotFoundHwControlError(DeviceNotFoundHwControlError):
    """HwControl Host cpu and Device Not Found Error Detail Exception class

    This class is common detail exception class for HwControl defined
    exceptions of Host cpu and Device Not Found Error.

    """

    error_code = "EF013BAS002"
    default_error_message: str = "The specified Host CPU and target device are not found."


class ResourceNotFoundHwControlError(DeviceNotFoundHwControlError):
    """HwControl Resource Not Found Error Detail Exception class

    This class is common detail exception class for HwControl defined
    exceptions of Resource Not Found Error.

    """

    error_code = "EF013BAS003"
    default_error_message: str = "The specified resource is not found."


class SwitchNotFoundHwControlError(DeviceNotFoundHwControlError):
    """HwControl Switch Not Found Error Detail Exception class

    This class is common detail exception class for HwControl defined
    exceptions of Switch Not Found Error.

    """

    error_code = "EF013BAS004"
    default_error_message: str = "The specified switch is not found."


class DeviceIdNotFoundHwControlError(DeviceNotFoundHwControlError):
    """HwControl Device ID Not Found Error Detail Exception class
    This class is common detail exception class for HwControl defined
    exceptions of Device ID Not Found Error.
    """

    error_code = "EF013BAS005"
    default_error_message: str = "The specified Device ID is not found."

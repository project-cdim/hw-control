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

"""Subclasses of  DeviceNotFoundHWControlError.

This module defines an exception class that inherits from the
DeviceNotFoundHWControlError class.
"""


from app.common.basic_exceptions.base_exceptions import DeviceNotFoundHWControlError


class HostCPUNotFoundHWControlError(
    DeviceNotFoundHWControlError
):  # TODO: Remove this class after migration to UpstreamDeviceNotFoundHWControlError is complete.
    """HwControl Host CPU Not Found Error Detail Exception class

    This class is common detail exception class for HwControl defined
    exceptions of Host CPU Not Found Error.

    Note:
        This exception class is deprecated.
        Please consider switching to UpstreamDeviceNotFoundHWControlError.
    """

    error_code = "EF013BAS001"
    default_error_message: str = "The specified Host CPU is not found."


class HostCPUAndDeviceNotFoundHWControlError(
    DeviceNotFoundHWControlError
):  # TODO: Remove this class after migration to the recommended exceptions is complete.
    """HwControl Host cpu and Device Not Found Error Detail Exception class

    This class is common detail exception class for HwControl defined
    exceptions of Host cpu and Device Not Found Error.

    Note:
        This exception class is deprecated.
        Please consider switching to UpstreamDeviceNotFoundHWControlError or DownstreamDeviceNotFoundHWControlError.
        If you find that a device is missing during the aggregation control process,
        please raise an exception at that point.
    """

    error_code = "EF013BAS002"
    default_error_message: str = "The specified Host CPU and target device are not found."


class ResourceNotFoundHWControlError(DeviceNotFoundHWControlError):
    """HwControl Resource Not Found Error Detail Exception class

    This class is common detail exception class for HwControl defined
    exceptions of Resource Not Found Error.

    """

    error_code = "EF013BAS003"
    default_error_message: str = "The specified resource is not found."


class SwitchNotFoundHWControlError(DeviceNotFoundHWControlError):
    """HwControl Switch Not Found Error Detail Exception class

    This class is common detail exception class for HwControl defined
    exceptions of Switch Not Found Error.

    """

    error_code = "EF013BAS004"
    default_error_message: str = "The specified switch is not found."


class DeviceIDNotFoundHWControlError(DeviceNotFoundHWControlError):
    """HwControl Device ID Not Found Error Detail Exception class
    This class is common detail exception class for HwControl defined
    exceptions of Device ID Not Found Error.
    """

    error_code = "EF013BAS005"
    default_error_message: str = "The specified Device ID is not found."


class UpstreamDeviceNotFoundHWControlError(DeviceNotFoundHWControlError):
    """Upstream Device not found case error in aggregation control.

    This class is detail exception class for the error case that represent
    the specified Upstream Device is not found in the FM plugin aggregation control process.
    """


class DownstreamDeviceNotFoundHWControlError(DeviceNotFoundHWControlError):
    """Downstream Device not found case error in aggregation control.

    This class is detail exception class for the error case that represent
    the specified Downstream Device is not found in the FM plugin aggregation control process.
    """

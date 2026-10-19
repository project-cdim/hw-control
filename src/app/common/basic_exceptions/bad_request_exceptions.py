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

"""Classes that inherit BadRequestHWControlError.

file path: /app/common/basic_exceptions/bad_request_exceptions.py

This module defines an exception class that inherits from the
BadRequestHWControlError class.
The exception classes defined in this module are as follows.

HostCPUPowerOffBadRequestHWControlError
RequestNotSupportedHWControlError

"""

from app.common.basic_exceptions.base_exceptions import BadRequestHWControlError


class HostCPUPowerOffBadRequestHWControlError(BadRequestHWControlError):
    """HwControl Host CPU Power Off state Error Detail Exception class.

    This class is common detail exception class for HwControl defined
    exceptions of Host CPU Power Off state Error.
    """

    error_code = "EF003BAS007"
    default_error_message: str = "The specified device power state is already off."


class RequestNotSupportedHWControlError(BadRequestHWControlError):
    """HwControl request not supported Error Detail Exception class.

    This class is common detail exception class for HwControl defined
    exceptions of the specified device does not support the requested
    operation Error.
    """

    error_code = "EF003BAS010"
    default_error_message: str = "Your request is not supported for the specified target device."

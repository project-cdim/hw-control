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

"""Classes that inherit ResourceBusyHwControlError

file path: /app/common/basic_exceptions/resource_busy_exceptions.py

This module defines an exception class that inherits from the 
ResourceBusyHwControlError class.
The exception classes defined in this module are as follows.

DeviceBusyHwControlError

"""

from app.common.basic_exceptions.base_exceptions import ResourceBusyHwControlError


class DeviceBusyHwControlError(ResourceBusyHwControlError):
    """Device Busy Error Detail Exception class

    This class is common HwControl defined detail exception class
    for when Device is busy.
    """

    error_code = "ER005BAS002"
    default_error_message: str = "The specified device is busy."

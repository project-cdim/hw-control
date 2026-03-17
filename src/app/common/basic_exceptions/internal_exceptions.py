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

"""
This module defines an exception class that inherits from the
InternalHWControlError class.
The exception classes defined in this module are as follows.

- UnexpectedExceptionHWControlError
"""

from app.common.basic_exceptions.base_exceptions import InternalHWControlError


class UnexpectedExceptionHWControlError(InternalHWControlError):
    """Unexpected Exception raise Case Exception class

    This class is common HwControl defined detail exception class
    for when an unexpected exception is thrown from a plugin.

    """

    error_code = "CF010BAS002"
    default_error_message: str = "An unexpected error occurred in the Plugin and was unable to complete your request."

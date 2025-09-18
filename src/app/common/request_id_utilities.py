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

"""
This module provides utilities for managing the request ID used in the application.

The request ID is a unique identifier generated for each incoming HTTP request.
It is stored in a context variable and can be accessed throughout the lifecycle
of the request for tracking and logging purposes.

Context Variables:
    _request_id (ContextVar[str]): A context variable used to store the unique
    request ID for the current request.

Functions:
    get_request_id(): Retrieves the request ID from the context variable. If no
    request ID is set, an empty string is returned.

Notes:
    - The `_request_id` context variable is intended to be set when an HTTP request
        is received. It is expected that the request-handling logic will set
        this value at the beginning of the request lifecycle.
"""

from contextvars import ContextVar

# _request_id can only be set by the RequestIDMiddleware in the src/app/routers/middlewares.py module.
_request_id: ContextVar[str] = ContextVar("request_id")


def get_request_id() -> str:
    """Get the 'request ID' value from the context variable.

    This function fetches the value of the 'request ID' stored in the
    context variable. If no value has been set for the context variable,
    the function returns an empty string.

    Args:
        None

    Returns:
        str:
            The 'request ID' value in the context variable.
            Returns an empty string ("") if no value is set in the context variable.
    """
    return _request_id.get("")

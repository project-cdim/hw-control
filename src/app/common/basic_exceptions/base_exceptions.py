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

"""This module defines the base exception class.

file path: /app/common/basic_exceptions/base_exceptions.py

"""

from http import HTTPStatus
from typing import final

from fastapi.responses import JSONResponse

# The key for BaseHWControlError.to_error_dict method.
ERROR_CODE = "errorCode"
ERROR_MESSAGE = "errorMessage"


class BaseHWControlError(Exception):
    """HwControl Base Exception class.

    This class serves as the common base exception class for all exceptions
    defined within HW Control. It can be extended to create custom error
    classes specific to various error scenarios in HwControl.

    Attributes:
        http_code (int): HTTP status code. Defaults to 500 (Internal Server Error).
        error_code (str): Unique error code for this type of exception.
        default_error_message (str): Default error message associated with this exception class.
        message (str): A property that returns all stored error messages concatenated into a single string.
    """

    http_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
    error_code = "CF000BAS000"
    default_error_message: str = "The server encountered an internal error and was unable to complete your request."

    def __init__(self, *args: object, additional_message: str = "") -> None:
        """Initializes a new instance of Custom Exception class.

        Allows the inclusion of an optional additional message to provide
        supplementary information alongside the default error message.

        Args:
            *args: Variable length positional arguments passed to the base Exception class.
            additional_message (str, optional): An additional error message. Defaults to an empty string.

        Attributes:
            _messages (list): A list containing stored error messages.
        """
        super().__init__(*args)
        self._messages: list = [self.default_error_message]
        if additional_message:
            self._messages.append(additional_message)

    def append_error_message(self, additional_message: str) -> None:
        """Appends an additional error message to the existing messages list.

        This method allows users to add extra information to the current list
        of error messages.

        Args:
            additional_message (str): The message to be appended.

        Returns:
            None

        Example:
            >>> try:
            >>>     raise FooHWControlError(additional_message="Foo")
            >>> except BaseHWControlError as e:
            >>>     e.append_error_message(additional_message="Bar")
            >>>     raise

        """
        self._messages.append(additional_message)

    @property
    def message(self):
        """Concatenated error messages.

        This property returns a single string that concatenates all stored error
        messages, separated by spaces. It filters out any empty messages before
        concatenation.

        Returns:
            str: A single string containing all error messages joined by spaces.

        Example:
            If the stored messages are ["Error occurred.", "Please retry."],
            accessing this property would return "Error occurred. Please retry."
        """
        message = " ".join(filter(bool, self._messages))
        return message

    @final
    def to_error_dict(self) -> dict[str, str]:
        """Converts the error information to a dictionary format.

        This method converts the error code and message to a dictionary
        which can be easily used for error reporting.

        Args:
            None

        Returns:
            dict[str, str]: A dictionary containing the error code and message
            with keys "errorCode" and "errorMessage" respectively.

        Example:
            >>> error = FooHWControlError()
            >>> error_dict = error.to_error_dict()
            >>> print(error_dict)
            {"errorCode": str, "errorMessage": str}

        Note:
            This method should not be overridden in subclasses.
            It is designed to provide a consistent error dictionary
            format across all custom exception classes derived from BaseHWControlError.
        """
        return {ERROR_CODE: self.error_code, ERROR_MESSAGE: self.message}

    @final
    def generate_api_response(self) -> JSONResponse:
        """generate_api_response method.

        This method generate api response data

        Args:
            None

        Returns:
            JSONResponse:

        Note:
            This method should not be overridden in subclasses.
        """
        return JSONResponse(status_code=self.http_code, content={"code": self.error_code, "message": self.message})


# ++++ Base Exception class +++++++++++++++++++++++++++++++++++++++++++#


class UnknownHWControlError(BaseHWControlError):
    """HwControl Unknown Error Base Exception class.

    This class is common base exception class for HwControl defined
    exceptions of Unknown Error.

    """

    http_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
    error_code = "CF001BAS000"
    default_error_message: str = "The server encountered an internal error and was unable to complete your request."


class AuthenticationHWControlError(BaseHWControlError):
    """HwControl Authentication Error Base Exception class.

    This class is common base exception class for HwControl defined
    exceptions of Authentication Error.

    """

    http_code = HTTPStatus.UNAUTHORIZED.value
    error_code = "EF002BAS000"
    default_error_message: str = "Authentication failed."


class BadRequestHWControlError(BaseHWControlError):
    """HwControl Bad Request Error Base Exception class.

    This class is common base exception class for HwControl defined
    exceptions of Bad Request Error.

    """

    http_code = HTTPStatus.BAD_REQUEST.value
    error_code = "EF003BAS000"
    default_error_message: str = "Your request is invalid."


class ControlObjectHWControlError(BaseHWControlError):
    """HwControl Control Object Error Base Exception class.

    This class is common base exception class for HwControl defined
    exceptions of Control Object Error.

    """

    http_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
    error_code = "EF004BAS000"
    default_error_message: str = "Failed to operate the specified device."


class ResourceBusyHWControlError(BaseHWControlError):
    """HwControl Resource Busy Error Base Exception class.

    This class is common base exception class for HwControl defined
    exceptions of Resource Busy Error.

    """

    http_code = HTTPStatus.SERVICE_UNAVAILABLE.value
    error_code = "ER005BAS000"
    default_error_message: str = "The specified resource is busy."


class ConfigurationHWControlError(BaseHWControlError):
    """HwControl Configuration Error Base Exception class.

    This class is common base exception class for HwControl defined
    exceptions of Incomplete configuration Error.

    """

    http_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
    error_code = "EF007BAS000"
    default_error_message: str = "Your request failed due to the missing required system configuration."


class InternalHWControlError(BaseHWControlError):
    """HwControl 'Internal Server Error' Base Exception class.

    This class is common base exception class for HwControl defined
    exceptions of 'Internal Server Error'.
    """

    http_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
    error_code = "EF010BAS000"
    default_error_message: str = "The server encountered an internal error."


class RequestConflictHWControlError(BaseHWControlError):
    """HwControl Request Conflict Base Exception class.

    This class is common base exception class for HwControl defined
    exceptions of request conflict to resource state.
    """

    http_code = HTTPStatus.CONFLICT.value
    error_code = "EF011BAS000"
    default_error_message: str = "The request conflicts with the current resource state."


class DependencyServiceHWControlError(BaseHWControlError):
    """Dependency service error case."""

    http_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
    error_code = "EF012BAS000"
    default_error_message: str = "Operation could not be completed due to a failure in external dependencies."


class DeviceNotFoundHWControlError(BaseHWControlError):
    """HwControl Device Not Found Error Detail Exception class.

    This class is common detail exception class for HwControl defined
    exceptions of Device Not Found Error.

    """

    http_code = HTTPStatus.NOT_FOUND.value
    error_code = "EF013BAS000"
    default_error_message: str = "The specified target device is not found."

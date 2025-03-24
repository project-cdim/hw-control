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

"""Defines the message to be included in the application log.

This module defines the 'log message model' classes that include JSON schemas for logging purposes.

The 'log message model' class is designed to provide a standardized way to structure and store log
messages in a JSON format. By inheriting from the BaseLogMessage class, these models guarantee that
the essential fields such as request_id, and detail are included and properly formatted in each log
entry.

The module also uses Python's built-in ContextVar class to set a 'request ID' as a context variable.
This 'request ID' is included in the 'log message model' class's request_id field, enabling the association
of logs with individual requests. This is particularly useful for tracing and analyzing request-specific
logs in the context of a REST API request.

"""

import json
from contextvars import ContextVar

from typing import Any, Dict

from starlette.datastructures import QueryParams
from pydantic import BaseModel, Field, field_serializer
from fastapi import Request as fastapi_Request
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from requests.models import Response as requests_Response
from requests.exceptions import JSONDecodeError as RequestsJSONDecodeError

import app.common.basic_exceptions as exc
from app.common import constants

_request_id: ContextVar[str] = ContextVar("request_id")

LOG_MESSAGES = {
    "I00001": "I00001: {0[0]} API Start {0[1]}",
    "I00002": "I00002: {0[0]} API Respond {0[1]}",
    "I00003": "I00003: {0[0]} Plugin Call. ",
    "I00004": "I00004: {0[0]} Plugin Respond. ",
    "I00005": "I00005: {0[0]} Agent Call. ",
    "I00006": "I00006: {0[0]} Agent Respond. ",
    "I00007": "I00007: {0[0]} Skipping connection to the Agent. {0[1]}",
    "W00001": "W00001: Unexpected Exception: {0[0]}",
    "W00002": "W00002: Unexpected DeviceType: {0[0]}",
    "W00003": "W00003: Failed to Get Plugin Instance: {0[0]}",
    "W00004": "W00004: Plugin Response Contains Invalid Type: {0[0]}]",
    "W00005": "W00005: Plugin Response Unexpected None:",
    "W00006": "W00006: Device information not found: {0[0]}",
    "W00007": "W00007: File does not exist: {0[0]}",
    "W00008": "W00008: Required item does not exist: {0[0]}",
    "W00009": "W00009: Invalid type value: {0[0]}",
    "W00010": "W00010: Power Operation Error: {0[0]}",
    "W00011": "W00011: Not Power Operation Device: {0[0]}",
    "W00012": "W00012: Failed to get OOB Response: {0[0]}",
    "W00013": "W00013: Failed to connect Agent: {0[0]}",
    "W00014": "W00014: Failed to get Agent Response: {0[0]}",
    "E00001": "E00001: Unexpected Exception: {0[0]}",
    "E00002": "E00002: Unexpected DeviceType: {0[0]}",
    "E00003": "E00003: Device information not found: {0[0]}",
    "E00004": "E00004: Power Operation Error: {0[0]}",
    "E00005": "E00005: Not Power Operation Device: {0[0]}",
    "E00006": "E00006: Failed to get OOB Response: {0[0]}",
}

I00001 = "I00001"
"""I00001: {0[0]} API Start {0[1]}"""
I00002 = "I00002"
"""I00002: {0[0]} API Respond {0[1]}"""
I00003 = "I00003"
"""I00003: {0[0]} Plugin Call. """
I00004 = "I00004"
"""I00004: {0[0]} Plugin Respond. """
I00005 = "I00005"
"""I00005: {0[0]} Agent Call. """
I00006 = "I00006"
"""I00006: {0[0]} Agent Respond. """
I00007 = "I00007"
"""I00007: {0[0]} Skipping connection to the Agent. {0[1]}"""
W00001 = "W00001"
"""W00001: Unexpected Exception: {0[0]}"""
W00002 = "W00002"
"""W00002: Unexpected DeviceType: {0[0]}"""
W00003 = "W00003"
"""W00003: Failed to Get Plugin Instance: {0[0]}"""
W00004 = "W00004"
"""W00004: Plugin Response Contains Invalid Type: {0[0]}]"""
W00005 = "W00005"
"""W00005: Plugin Response Unexpected None:"""
W00006 = "W00006"
"""W00006: Device information not found: {0[0]}"""
W00007 = "W00007"
"""W00007: File does not exist: {0[0]}"""
W00008 = "W00008"
"""W00008: Required item does not exist: {0[0]}"""
W00009 = "W00009"
"""W00009: Invalid type value: {0[0]}"""
W00010 = "W00010"
"""W00010: Power Operation Error: {0[0]}"""
W00011 = "W00011"
"""W00011: Not Power Operation Device: {0[0]}"""
W00012 = "W00012"
"""W00012: Failed to get OOB Response: {0[0]}"""
W00013 = "W00013"
"""W00013: Failed to connect Agent: {0[0]}"""
W00014 = "W00014"
"""W00014: Failed to get Agent Response: {0[0]}"""
E00001 = "E00001"
"""E00001: Unexpected Exception: {0[0]}"""
E00002 = "E00002"
"""E00002: Unexpected DeviceType: {0[0]}"""
E00003 = "E00003"
"""E00003: Device information not found: {0[0]}"""
E00004 = "E00004"
"""E00004: Power Operation Error: {0[0]}"""
E00005 = "E00005"
"""E00005: Not Power Operation Device: {0[0]}"""
E00006 = "E00006"
"""E00006: Failed to get OOB Response: {0[0]}"""


def get_log_message(message_code: str, param_list: list):
    """get log message"""
    try:
        return LOG_MESSAGES[message_code].format(param_list)
    except Exception as error:  # pylint: disable=W0718
        raise exc.InvalidLogMessageParameterHwControlError from error


def set_request_id(request_id: str) -> None:
    """Set the 'request ID' in the context variable.

    This function sets the given 'request ID' in the context variable.

    Args:
        request_id (str):
            The 'request ID' to be stored in the context variable.

    Returns:
        None
    """
    _request_id.set(request_id)


def get_request_id() -> str | None:
    """Get the 'request ID' value from the context variable.

    This function fetches the value of the 'request ID' stored in the
    context variable. If no value has been set for the context variable,
    the function returns None.

    Args:
        None

    Returns:
        str:
            The 'request ID' value in the context variable.

        None:
            If no value is set in the context variable.
    """
    return _request_id.get(None)


class LogFieldNotice(BaseModel):
    """A model to represent a notice for log fields.

    This class can be used to encapsulate special messages or notices
    for specific log fields, indicating issues or special handling cases.

    Attributes:
        notice (str): A string message indicating the notice or special handling case
            for the log field. For example, it can be used to indicate that a field's
            data is too large to be logged fully.
    """

    notice: str = Field(
        default=None,
    )


class BaseLogMessage(BaseModel):
    """A base class for 'log message model' class.

    This class serves as a base for 'log message model' class, providing
    common fields and functionality.

    request_id (str | None):
        The identifier of request.

    detail (str | None):
        The additional information that include in the log.
        It is optional and defaults to None if no additional details are provided.

    """

    request_id: str = Field(
        default_factory=get_request_id,
        description="This field is the REST-API request identifier.",
    )

    detail: str | None = Field(
        default=None,
        description="This field can be used by each module to provide additional information.",
    )

    def to_json_encodable(self) -> Dict[str, Any]:
        """Convert the instance to a JSON encodable object.

        This method uses FastAPI's `jsonable_encoder` to convert the instance
        of the `BaseLogMessage` class or its subclasses into a dictionary that can be
        easily serialized to JSON. This is useful for preparing log messages for
        output in JSON format.

        Returns:
            Dict[str, Any]: A dictionary representation of the instance
            that is JSON encodable.
        """
        return jsonable_encoder(self)


class HttpRequestLog(BaseLogMessage):
    """A 'log message model' class for logging HTTP request contents.

    This class extends the BaseLogMessage class to provide additional fields and functionality
    specifically for logging the contents of HTTP requests.
    """

    action: str = Field(
        default="receive http request",
        description="Indicates the operation that was performed when the log was generated.",
    )
    url: str | None = Field(default=None, description="The URL of the HTTP request.")
    http_method: str | None = Field(default=None, description="The HTTP method used for the request.")
    client_ip_address: str | None = Field(
        default=None, description="The IP address of the client that made the HTTP request."
    )
    client_port: int | None = Field(
        default=None, description="The port number on the client that made the HTTP request."
    )
    path_parameter: dict | None = Field(default=None, description="The path parameters included in the HTTP request.")
    query_parameter: Any = Field(default=None, description="The query parameters included in the HTTP request.")

    body_parameter: dict | None = Field(default=None, description="The body parameters included in the HTTP request.")

    @field_serializer("query_parameter")
    def serialize_query_params(self, query_parameter: QueryParams) -> dict | None:
        """Custom serializer of query_parameter field.

        Args:
            A QueryParams instance containing the query parameters to be serialized.
            This is typically an object that holds key-value pairs of query string information
            from an HTTP request.

        Returns:
            dict | None:
                A dictionary representation of the query parameters,
                where keys are parameter names and values are parameter values.
                Returns None if query_parameter is empty.

        Note:
            All values in the resulting dictionary are of type `str`, regardless of their original
            types in the HTTP request. This is because query parameters in HTTP requests are always
            interpreted as strings.
        """
        if not query_parameter:
            return None
        return dict(query_parameter)

    @classmethod
    def create_from_request(
        cls, request: fastapi_Request, detail: str | None = None, body_parameter: BaseModel | None = None
    ) -> "HttpRequestLog":
        """Create an instance of HttpRequestLog from a FastAPI Request object.

        This method extracts relevant information from a FastAPI Request object
        to instantiate an HttpRequestLog object.

        Args:
            request (Request):
                The FastAPI Request object from which HTTP request information
                will be extracted.

            detail (str, optional):
                Additional information to include in the log.
                Defaults to None.

            body_parameter (BaseModel):
                The body_parameter object received in the endpoint function.

        Returns:
            HttpRequestLog:
                An instance of HttpRequestLog class.
        """
        client_ip_address = None
        client_port = None

        if request.client:
            client_ip_address = request.client.host
            client_port = request.client.port

        return cls(
            detail=detail,
            url=str(request.url),
            http_method=request.method,
            client_ip_address=client_ip_address,
            client_port=client_port,
            path_parameter=request.path_params,
            query_parameter=request.query_params,
            body_parameter=jsonable_encoder(body_parameter),
        )


class HttpResponseLog(BaseLogMessage):
    """A 'log message model' class for logging HTTP response contents.

    This class extends the BaseLogMessage class to provide additional fields and functionality
    specifically for logging the contents of HTTP response.
    """

    action: str = Field(
        default="return http response",
        description="Indicates the operation that was performed when the log was generated.",
    )
    status_code: int | None = Field(default=None)
    response_body: Any | None = Field(default=None)

    @classmethod
    def create_from_json_response(cls, response: JSONResponse, detail: str | None = None) -> "HttpResponseLog":
        """Create an instance of HttpResponseLog from a FastAPI JSONResponse object.

        This method extracts relevant information from a fastapi.responses.JSONResponse object
        to instantiate an HttpResponseLog object.

        Args:
            response (fastapi.responses.JSONResponse):
                fastapi.responses.JSONResponse object

            detail (str, optional):
                Additional information to include in the log.
                Defaults to None.

        Returns:
            HttpResponseLog:
                An instance of HttpResponseLog class.
        """

        return cls(
            detail=detail, status_code=response.status_code, response_body=json.loads(response.body.decode("utf-8"))
        )


class AgentRequestLog(BaseLogMessage):
    """A 'log message model' class for logging the contents of HTTP request to an Agent.

    This class extends the BaseLogMessage class to provide additional fields and functionality
    specifically for logging the contents of HTTP request sent to an Agent.
    """

    action: str = Field(
        default="request to Agent",
        description="Indicates the operation that was performed when the log was generated.",
    )
    ip_address: str | None = Field(
        default=None, description="The IP address of the Agent to which the HTTP request was sent."
    )
    port: int | None = Field(
        default=None, description="The port number on the Agent to which the HTTP request was sent."
    )
    url: str | None = Field(default=None, description="The URL to which the HTTP request was sent.")
    http_method: str | None = Field(default=None, description="The HTTP method used for the request.")
    time_out: int | float | None = Field(default=None, description="The timeout value for the HTTP request.")
    request_body: Any = Field(default=None, description="The body of the HTTP request sent to the Agent.")


class AgentResponseLog(BaseLogMessage):
    """A 'log message model' class for logging the contents of HTTP response from an Agent.

    This class extends the BaseLogMessage class to provide additional fields and functionality
    specifically for logging the contents of HTTP response return from an Agent.
    """

    action: str = Field(
        default="receive Agent response",
        description="Indicates the operation that was performed when the log was generated.",
    )
    status_code: int | None = Field(
        default=None, description="The HTTP status code returned from the Agent's response."
    )
    content_type_header: str | None = Field(
        default=None, description="Content-Type header returned from the Agent's response."
    )
    response_body: Any = Field(default=None, description="The body of the HTTP response returned from the Agent.")

    @classmethod
    def create_from_response(cls, response: requests_Response, detail: str | None = None) -> "AgentResponseLog":
        """Create an instance of AgentResponseLog from a requests Response object.

        This method extracts relevant information from a requests.models.Response object
        to instantiate an AgentResponseLog object.

        Args:
            response (requests.models.Response):
                requests.models.Response object

            detail (str, optional):
                Additional information to include in the log.
                Defaults to None.

        Returns:
            AgentResponseLog:
                An instance of AgentResponseLog class.
        """

        response_body = None
        content_type_header = response.headers.get("Content-Type")

        if content_type_header:

            if response.headers.get("Content-Type") == constants.ContentType.APPLICATION_JSON.value:
                try:
                    response_body = response.json()
                except RequestsJSONDecodeError:
                    response_body = LogFieldNotice(notice="Invalid JSON format")
            else:
                response_body = response
                response_body = LogFieldNotice(notice="Unexpected Content-Type")

        elif response.content:
            response_body = LogFieldNotice(notice="Unexpected Content-Type")

        return cls(
            detail=detail,
            status_code=response.status_code,
            content_type_header=content_type_header,
            response_body=response_body,
        )


class PluginCallLog(BaseLogMessage):
    """A 'log message model' class for logging the plugin information.

    This class extends the BaseLogMessage class to provide additional fields and functionality
    specifically for logging the plugin information.
    """

    action: str = Field(
        default="plugin call",
        description="Indicates the operation that was performed when the log was generated.",
    )
    manager_type: str | None = Field(default=None, description="The type of the plugin.")
    manager_id: str | None = Field(default=None, description="The identifier of the plugin.")
    class_name: str | None = Field(default=None, description="The name of the plugin interface class.")
    method_name: str | None = Field(default=None, description="The name of the plugin API method.")


class DeviceLockLog(BaseLogMessage):
    """A 'log message model' class for logging the device lock situation.

    This class extends the BaseLogMessage class to provide additional fields and functionality
    specifically for logging the device loc situation.
    """

    action: str = Field(
        default="acquire lock",
        description="Indicates the operation that was performed when the log was generated.",
    )
    target_device: str | None = Field(
        default=None,
        description="This field is the 'device ID' lock target device.",
    )


class DeviceLockReleasedLog(BaseLogMessage):
    """A 'log message model' class for logging the device loc release situation.

    This class extends the BaseLogMessage class to provide additional fields and functionality
    specifically for logging the device loc release situation.
    """

    action: str = Field(
        default="release lock",
        description="Indicates the operation that was performed when the log was generated.",
    )
    target_device: str | None = Field(
        default=None,
        description="This field is the 'device ID' lock release target device.",
    )


class DeviceLockFailedLog(BaseLogMessage):
    """A 'log message model' class for logging the device loc failed situation.

    This class extends the BaseLogMessage class to provide additional fields and functionality
    specifically for logging the device loc failed situation.
    """

    action: str = Field(
        default="failed to acquire lock",
        description="Indicates the operation that was performed when the log was generated.",
    )
    target_device: str | None = Field(
        default=None,
        description="This field is the 'device ID' lock target device.",
    )


class ExceptionLog(BaseLogMessage):
    """A 'log message model' class for logging the exception class instance.

    This class extends the BaseLogMessage class to provide additional fields and functionality
    specifically for logging the exception class instance.
    """

    action: str = Field(
        default="exception raised",
        description="Indicates the operation that was performed when the log was generated.",
    )
    trace_back: str | None = Field(default=None, description="This field is the traceback of the raised exception.")


class DeviceLockReleaseFailedLog(BaseLogMessage):
    """A 'log message model' class for logging the device loc release failed situation.

    This class extends the BaseLogMessage class to provide additional fields and functionality
    specifically for logging the device loc release failed situation.
    """

    action: str = Field(
        default="failed to release lock",
        description="Indicates the operation that was performed when the log was generated.",
    )

    target_device: str | None = Field(
        default=None,
        description="This field is the 'device ID' lock release target device.",
    )

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
Module for error handling in FastAPI applications.

This module defines custom exception handlers and integrates them
with a FastAPI application. These handlers are designed to log errors,
generate appropriate JSON responses, and handle various types of 
exceptions that might occur during API requests.
"""

import traceback
import uuid
from http import HTTPStatus
from typing import cast

from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response

import app.common.basic_exceptions as custom_exceptions
from app.common.utils.log import LOGGER
from app.common.messages import message
from app.routers.control import control_responses


available_status_codes: list = [
    HTTPStatus.BAD_REQUEST.value,
    HTTPStatus.UNAUTHORIZED.value,
    HTTPStatus.FORBIDDEN.value,
    HTTPStatus.NOT_FOUND.value,
    HTTPStatus.CONFLICT.value,
    HTTPStatus.INTERNAL_SERVER_ERROR.value,
    HTTPStatus.SERVICE_UNAVAILABLE.value,
]
# List of HTTP status codes that are allowed to be used in error responses
# according to the project's REST API common rules.


def hw_control_error_handler(request: Request, exc: Exception) -> Response:  # pylint: disable=W0613
    """
    Handle BaseHwControlError.

    This function handles exceptions of type BaseHwControlError.
    It logs the error and returns a JSON response with the 'status' code and detail
    'message', 'error code', provided by the exception.

    Args:
        exc (BaseHwControlError): The BaseHwControlError that was raised.

    Returns:
        JSONResponse:
            - status_code: The 'status_code' of the BaseHwControlError.
            - content:
                - code: The 'error_code' of the BaseHwControlError.
                - message: The 'message' of the BaseHwControlError.
    """
    hw_control_exc = cast(custom_exceptions.BaseHwControlError, exc)

    trace_back_str = "".join(
        traceback.format_exception(type(hw_control_exc), hw_control_exc, hw_control_exc.__traceback__)
    )
    LOGGER.error(message.ExceptionLog(trace_back=trace_back_str).to_json_encodable())

    response = hw_control_exc.generate_api_response()
    LOGGER.info(
        message.HttpResponseLog.create_from_json_response(response=response).to_json_encodable()
    )  # TODO: This code should be moved to custom middleware as part of the custom middleware implementation.

    return response


def _is_client_error(status_code: int) -> bool:
    """Check if the given HTTP status code is a client error.

    Args:
        status_code (int):
            HTTP status code to check.

    Returns:
        bool:
            True if the status code is a client error (4xx), False otherwise.
    """
    return HTTPStatus.BAD_REQUEST <= status_code < HTTPStatus.INTERNAL_SERVER_ERROR


def custom_http_exception_handler(request: Request, exc: Exception) -> Response:
    """
    Handle HTTP exceptions.

    This function handles exceptions of type starlette.exceptions.HTTPException.
    It logs the error and returns a JSON response with the status code and detail
    message provided by the exception.

    Args:
        request (fastapi.Request): The request object that triggered the exception.
        exc (HTTPException): The HTTPException that was raised.

    Returns:
        JSONResponse:
            - status_code: The 'status_code' of the HTTPException.
            - content:
                - code: "EF003BAS011" (Fixed error code).
                - message: Exception detail message.
    """

    http_exc = cast(StarletteHTTPException, exc)

    message.set_request_id(
        request_id=str(uuid.uuid4())
    )  # TODO: This code should be moved to custom middleware as part of the custom middleware implementation.

    LOGGER.info(
        message.HttpRequestLog.create_from_request(request=request).to_json_encodable()
    )  # TODO: This code should be moved to custom middleware as part of the custom middleware implementation.

    trace_back_str = "".join(traceback.format_exception(type(http_exc), http_exc, http_exc.__traceback__))
    LOGGER.error(message.ExceptionLog(trace_back=trace_back_str).to_json_encodable())

    status_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
    if http_exc.status_code in available_status_codes:
        status_code = http_exc.status_code
    elif _is_client_error(http_exc.status_code):
        status_code = HTTPStatus.BAD_REQUEST.value

    response = control_responses.generate_api_response(
        response_body=control_responses.ErrorResponseBody(code="EF003BAS011", message=http_exc.detail),
        status_code=status_code,
    )
    LOGGER.info(
        message.HttpResponseLog.create_from_json_response(response=response).to_json_encodable()
    )  # TODO: This code should be moved to custom middleware as part of the custom middleware implementation.

    return response


def custom_validation_exception_handler(request: Request, exc: Exception) -> Response:
    """
    Handle RequestValidationError.

    This function handles exceptions of type 'fastapi.exceptions.RequestValidationError'.
    It logs the error and returns a JSON response with a 422 status code, an error code, and
    the validation errors.

    Args:
        request (fastapi.Request): The request object that triggered the exception.
        exc (RequestValidationError): The RequestValidationError that was raised.

    Returns:
        JSONResponse:
            - status_code: 400
            - content:
                - code: "EF003BAS012" (Fixed error code).
                - message: The validation errors that occurred.
    """

    request_validation_exc = cast(RequestValidationError, exc)

    message.set_request_id(
        request_id=str(uuid.uuid4())
    )  # TODO: This code should be moved to custom middleware as part of the custom middleware implementation.

    LOGGER.info(
        message.HttpRequestLog.create_from_request(request=request).to_json_encodable()
    )  # TODO: This code should be moved to custom middleware as part of the custom middleware implementation.

    trace_back_str = "".join(
        traceback.format_exception(
            type(request_validation_exc), request_validation_exc, request_validation_exc.__traceback__
        )
    )
    LOGGER.error(message.ExceptionLog(trace_back=trace_back_str).to_json_encodable())

    response = control_responses.generate_api_response(
        response_body=control_responses.ErrorResponseBody(code="EF003BAS012", message=request_validation_exc.errors()),
        status_code=HTTPStatus.BAD_REQUEST.value,
    )
    LOGGER.info(
        message.HttpResponseLog.create_from_json_response(response=response).to_json_encodable()
    )  # TODO: This code should be moved to custom middleware as part of the custom middleware implementation.

    return response


def custom_exception_handler(request: Request, exc: Exception) -> Response:  # pylint: disable=W0613
    """
    Handle unexpected exceptions.

    This function logs the unexpected exception and generates a JSON response
    with a 500 status code and a general error message.

    Args:
        exc (Exception): The unexpected exception that was raised.

    Returns:
        JSONResponse:
            - status_code: 500
            - content:
                - code: "CF010BAS001" (Fixed error code)
                - message: The general error message indicating an internal server error.
    """
    trace_back_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    LOGGER.error(message.ExceptionLog(trace_back=trace_back_str).to_json_encodable())

    response = control_responses.generate_api_response(
        response_body=control_responses.ErrorResponseBody(
            code="CF010BAS001",
            message="The server encountered an unexpected internal error and was unable to complete your request.",
        ),
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
    )

    LOGGER.info(
        message.HttpResponseLog.create_from_json_response(response=response).to_json_encodable()
    )  # TODO: This code should be moved to custom middleware as part of the custom middleware implementation.

    return response

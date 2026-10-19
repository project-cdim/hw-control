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

"""Module for error handling in FastAPI applications.

This module defines custom exception handlers and integrates them
with a FastAPI application. These handlers are designed to log errors,
generate appropriate JSON responses, and handle various types of
exceptions that might occur during API requests.
"""

import logging
from http import HTTPStatus
from typing import cast

from asgi_correlation_id import correlation_id
from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

import app.common.basic_exceptions as custom_exceptions
from app.common import constants
from app.routers import response_models

logger = logging.getLogger(__name__)

_AVAILABLE_STATUS_CODES: list = [
    HTTPStatus.BAD_REQUEST.value,
    HTTPStatus.UNAUTHORIZED.value,
    HTTPStatus.FORBIDDEN.value,
    HTTPStatus.NOT_FOUND.value,
    HTTPStatus.METHOD_NOT_ALLOWED.value,
    HTTPStatus.CONFLICT.value,
    HTTPStatus.INTERNAL_SERVER_ERROR.value,
    HTTPStatus.SERVICE_UNAVAILABLE.value,
]  # TODO: Consider adding newly allowed HTTP status codes according to the updated common REST API
# List of HTTP status codes that are allowed to be used in error responses
# according to the project's REST API common rules.


def hw_control_error_handler(_: Request, exc: Exception) -> Response:
    """Handle BaseHWControlError.

    This function handles exceptions of type BaseHWControlError.
    It logs the error and returns an HTTP response containing error details in JSON format.

    Args:
        _ (fastapi.Request): The request object (not used in this handler).
        exc (Exception): The exception that was raised. (Should be an instance of BaseHWControlError)

    Returns:
        Response:
            An HTTP response object (typically a JSONResponse) containing:
                - status_code: The `status_code` of the BaseHWControlError.
                - content:
                    - code: The `error_code` of the BaseHWControlError.
                    - message: The `message` of the BaseHWControlError.
    """
    hw_control_exc = cast(custom_exceptions.BaseHWControlError, exc)

    logger.exception(
        msg="An error occurred during processing.",
        exc_info=exc,
        extra={"error_code": hw_control_exc.error_code, "error_message": hw_control_exc.message},
    )

    response = hw_control_exc.generate_api_response()

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


def custom_http_exception_handler(_: Request, exc: Exception) -> Response:
    """Handle HTTP exceptions.

    This function handles exceptions of type starlette.exceptions.HTTPException.
    It logs the error and returns an HTTP response containing error details in JSON format.

    Args:
        request (fastapi.Request): The request object that triggered the exception.
        exc (Exception): The exception that was raised. (Should be an instance of HTTPException)

    Returns:
        Response:
            An HTTP response object (typically a JSONResponse) containing:
                - status_code: The status code of the HTTPException.
                - content:
                    - code: "EF003BAS011" (Fixed error code).
                    - message: Exception detail message.
    """
    http_exc = cast(StarletteHTTPException, exc)

    status_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
    if http_exc.status_code in _AVAILABLE_STATUS_CODES:
        status_code = http_exc.status_code
    elif _is_client_error(http_exc.status_code):
        status_code = HTTPStatus.BAD_REQUEST.value

    error_code = "EF003BAS011"
    error_message = http_exc.detail

    logger.exception(
        msg="Failed to process an invalid request.",
        exc_info=exc,
        extra={"error_code": error_code, "error_message": error_message},
    )

    response_body = response_models.ErrorResponseModel(code=error_code, message=error_message)
    response = JSONResponse(status_code=status_code, content=jsonable_encoder(response_body))

    return response


def custom_validation_exception_handler(_: Request, exc: Exception) -> Response:
    """Handle RequestValidationError.

    This function handles exceptions of type 'fastapi.exceptions.RequestValidationError'.
    It logs the error and returns an HTTP response containing validation error details in JSON format.

    Args:
        _ (fastapi.Request): The request object that triggered the exception.
        exc (Exception): The exception that was raised. (Should be an instance of RequestValidationError)

    Returns:
        Response:
            An HTTP response object (typically a JSONResponse) containing:
                - status_code: 422
                - content:
                    - code: "EF003BAS012" (Fixed error code).
                    - message: A fixed message indicating the request parameter is invalid.
                    - detail: The validation errors that occurred.
    """
    request_validation_exc = cast(RequestValidationError, exc)

    status_code = HTTPStatus.UNPROCESSABLE_ENTITY.value

    error_code = "EF003BAS012"
    error_detail = request_validation_exc.errors()
    error_message = "The request parameter is invalid or missing."

    logger.exception(
        msg="Request parameter validation error occurred.",
        exc_info=exc,
        extra={"error_code": error_code, "error_message": error_message, "error_detail": error_detail},
    )

    response_body = response_models.ValidationErrorResponseModel(
        code=error_code, message=error_message, detail=error_detail
    )
    response = JSONResponse(status_code=status_code, content=jsonable_encoder(response_body))

    return response


def custom_exception_handler(_: Request, exc: Exception) -> Response:
    """Handle unexpected exceptions.

    This function logs the unexpected exception and generates an HTTP response
    containing a general error message in JSON format with a 500 status code.

    Args:
        _ (fastapi.Request): The request object (not used in this handler).
        exc (Exception): The unexpected exception that was raised.

    Returns:
        Response:
            An HTTP response object (typically a JSONResponse) containing:
                - status_code: 500
                - content:
                    - code: "CF010BAS001" (Fixed error code)
                    - message: The general error message indicating an internal server error.
    """
    error_code = "CF010BAS001"
    error_message = "The server encountered an unexpected internal error and was unable to complete your request."

    logger.exception(
        msg="An unexpected error occurred.",
        exc_info=exc,
        extra={"error_code": error_code, "error_message": error_message},
    )

    response_body = response_models.ErrorResponseModel(code=error_code, message=error_message)
    response = JSONResponse(
        content=jsonable_encoder(response_body),
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR.value,
        # Use default value as fallback if correlation ID is not set in context variable
        headers={constants.CORRELATION_ID_HEADER: correlation_id.get() or constants.CORRELATION_ID_DEFAULT_VALUE},
    )

    logger.info(
        msg="Return http response.",
        extra={
            "http_status": response.status_code,
            "content_length": response.headers.get("content-length"),
        },
    )

    return response

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

"""Unit test module for error_handlers.py module."""

import json
import logging
from http import HTTPStatus

import pytest
from fastapi.exceptions import RequestValidationError
from starlette.datastructures import Headers
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

import app.common.basic_exceptions as custom_exceptions
from app.routers import error_handlers


class TestErrorHandlers:
    """Unit test class for error handler function."""

    @pytest.mark.parametrize("input_exception_instance", [Exception(), RuntimeError()])
    def test_custom_expected_handler(self, caplog: pytest.LogCaptureFixture, input_exception_instance):
        """
        Test the custom exception handler for Python built-in exceptions.

        This test verifies that the custom exception handler correctly handles
        instances of common Python built-in exceptions, logs the appropriate messages,
        and returns the expected HTTP response.

        Args:
            caplog (LogCaptureFixture): The fixture used to capture log messages.
            input_exception_instance (Exception): The input exception instance to be tested.

        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the expected value
        expected_status_code = HTTPStatus.INTERNAL_SERVER_ERROR.value
        expected_response_body = {
            "code": "CF010BAS001",
            "message": "The server encountered an unexpected internal error and was unable to complete your request.",
        }

        # Set up the input value
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/items/",
            "headers": Headers({"content-type": "application/json"}).raw,
            "query_string": b"q=5",  # query_string should be bytes
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }
        input_request_object = Request(scope)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=error_handlers.__name__):
            response = error_handlers.custom_exception_handler(input_request_object, input_exception_instance)

        actual_response_body = json.loads(bytes(response.body).decode("utf-8"))

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_status_code
        assert actual_response_body == expected_response_body

        assert len(caplog.records) == 2

        # Inspection: Check the exception log
        exception_log = caplog.records[0]
        assert exception_log.levelname == "ERROR"
        assert exception_log.getMessage() == "An unexpected error occurred."
        assert exception_log.exc_info is not None, "exc_info should be present in the log record"
        assert exception_log.exc_info[1] == input_exception_instance

        assert hasattr(exception_log, "error_code"), "error_code should be present in the log record"
        assert getattr(exception_log, "error_code") == expected_response_body["code"]

        assert hasattr(exception_log, "error_message"), "error_message should be present in the log record"
        assert getattr(exception_log, "error_message") == expected_response_body["message"]

        # Inspection: Check the response log
        response_log = caplog.records[1]
        assert response_log.levelname == "INFO"
        assert response_log.getMessage() == "Return http response."

        assert hasattr(response_log, "content_length"), "`content_length` should be present in the log record"
        assert getattr(response_log, "content_length") == str(len(response.body))

    @pytest.mark.parametrize(
        ("input_exception_instance", "expected_status_code", "expected_response_body"),
        [
            (
                custom_exceptions.BaseHWControlError(),
                HTTPStatus.INTERNAL_SERVER_ERROR.value,
                {
                    "code": "CF000BAS000",
                    "message": "The server encountered an internal error and was unable to complete your request.",
                },
            ),
            (
                custom_exceptions.DeviceNotFoundHWControlError(),
                HTTPStatus.NOT_FOUND.value,
                {
                    "code": "EF013BAS000",
                    "message": "The specified target device is not found.",
                },
            ),
        ],
    )
    def test_hw_control_error_handler(
        self, caplog: pytest.LogCaptureFixture, input_exception_instance, expected_status_code, expected_response_body
    ):
        """
        Test hw_control_error_handler.

        This test verifies that the hw_control_error_handler correctly
        handles instances of the BaseHWControlError, logs the appropriate messages,
        and returns the expected HTTP response.

        Args:
            caplog (LogCaptureFixture):
                The fixture used to capture log messages.

            input_exception_instance (BaseHWControlError):
                The input exception instance to be tested.

            expected_status_code (int):
                The expected HTTP status code in the response.

            expected_response_body (dict):
                The expected response body.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set up the input value
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/items/",
            "headers": Headers({"content-type": "application/json"}).raw,
            "query_string": b"q=5",  # query_string should be bytes
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }
        input_request_object = Request(scope)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=error_handlers.__name__):
            response = error_handlers.hw_control_error_handler(input_request_object, input_exception_instance)

        actual_response_body = json.loads(bytes(response.body).decode("utf-8"))

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_status_code
        assert actual_response_body == expected_response_body

        assert len(caplog.records) == 1

        # Inspection: Check the exception log
        exception_log = caplog.records[-1]
        assert exception_log.levelname == "ERROR"
        assert exception_log.getMessage() == "An error occurred during processing."
        assert exception_log.exc_info is not None, "exc_info should be present in the log record"
        assert exception_log.exc_info[1] == input_exception_instance

        assert hasattr(exception_log, "error_code"), "error_code should be present in the log record"
        assert getattr(exception_log, "error_code") == expected_response_body["code"]

        assert hasattr(exception_log, "error_message"), "error_message should be present in the log record"
        assert getattr(exception_log, "error_message") == expected_response_body["message"]

    @pytest.mark.parametrize(
        ("input_status_code", "expected_status_code"),
        [
            (HTTPStatus.BAD_REQUEST.value, HTTPStatus.BAD_REQUEST.value),
            (
                HTTPStatus.UNAUTHORIZED.value,
                HTTPStatus.UNAUTHORIZED.value,
            ),
            (
                HTTPStatus.FORBIDDEN.value,
                HTTPStatus.FORBIDDEN.value,
            ),
            (
                HTTPStatus.NOT_FOUND.value,
                HTTPStatus.NOT_FOUND.value,
            ),
            (
                HTTPStatus.METHOD_NOT_ALLOWED.value,
                HTTPStatus.METHOD_NOT_ALLOWED.value,
            ),
            (
                HTTPStatus.CONFLICT.value,
                HTTPStatus.CONFLICT.value,
            ),
            (
                HTTPStatus.INTERNAL_SERVER_ERROR.value,
                HTTPStatus.INTERNAL_SERVER_ERROR.value,
            ),
            (
                HTTPStatus.SERVICE_UNAVAILABLE.value,
                HTTPStatus.SERVICE_UNAVAILABLE.value,
            ),
            (499, HTTPStatus.BAD_REQUEST.value),
            (
                599,
                HTTPStatus.INTERNAL_SERVER_ERROR.value,
            ),
            (
                300,
                HTTPStatus.INTERNAL_SERVER_ERROR.value,
            ),
        ],
    )
    def test_custom_http_exception_handler(
        self, caplog: pytest.LogCaptureFixture, input_status_code, expected_status_code
    ):
        """
        Test custom_http_exception_handler.

        This test verifies that the custom HTTP exception handler correctly handles
        HTTPException instances, logs the appropriate messages, and returns the
        expected HTTP response based on the provided HTTP status code.

        Args:
            caplog (LogCaptureFixture): The fixture used to capture log messages.
            input_status_code (int): The input HTTP status code to be tested.
            expected_status_code (int): The expected HTTP status code in the response.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the expected value
        expected_response_body = {
            "code": "EF003BAS011",
            "message": "test_error_message",
        }

        # Set up the input value
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/items/",
            "headers": Headers({"content-type": "application/json"}).raw,
            "query_string": b"q=5",  # query_string should be bytes
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }
        input_request_object = Request(scope)

        input_error_object = StarletteHTTPException(status_code=input_status_code, detail="test_error_message")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=error_handlers.__name__):
            response = error_handlers.custom_http_exception_handler(input_request_object, input_error_object)

        actual_response_body = json.loads(bytes(response.body).decode("utf-8"))

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_status_code
        assert actual_response_body == expected_response_body

        assert len(caplog.records) == 1

        # Inspection: Check the exception log
        exception_log = caplog.records[-1]
        assert exception_log.levelname == "ERROR"
        assert exception_log.getMessage() == "Failed to process an invalid request."
        assert exception_log.exc_info is not None, "exc_info should be present in the log record"
        assert exception_log.exc_info[1] == input_error_object

        assert hasattr(exception_log, "error_code"), "error_code should be present in the log record"
        assert getattr(exception_log, "error_code") == expected_response_body["code"]

        assert hasattr(exception_log, "error_message"), "error_message should be present in the log record"
        assert getattr(exception_log, "error_message") == expected_response_body["message"]

    def test_custom_validation_exception_handler(self, caplog: pytest.LogCaptureFixture):
        """
        Test custom_validation_exception_handler.

        This test verifies that the custom validation exception handler correctly handles
        RequestValidationError instances, logs the appropriate messages, and returns the
        expected HTTP response.

        Args:
            caplog (LogCaptureFixture): The fixture used to capture log messages.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input value
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/items/",
            "headers": Headers({"content-type": "application/json"}).raw,
            "query_string": b"q=5",  # query_string should be bytes
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }
        input_request_object = Request(scope)

        errors = [
            {
                "type": "missing",
                "loc": ("body",),
                "msg": "Field required",
                "input": None,
            }
        ]
        input_error_object = RequestValidationError(errors=errors)

        # Set up the expected value
        expected_status_code = 422
        expected_error_code = "EF003BAS012"
        expected_message = "The request parameter is invalid or missing."
        expected_response_body = {
            "code": expected_error_code,
            "message": expected_message,
            "detail": json.loads(json.dumps(errors)),
        }

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=error_handlers.__name__):
            response = error_handlers.custom_validation_exception_handler(input_request_object, input_error_object)

        response_body = json.loads(bytes(response.body).decode("utf-8"))

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_status_code
        assert response_body == expected_response_body

        assert len(caplog.records) == 1

        # Inspection: Check the exception log
        exception_log = caplog.records[-1]
        assert exception_log.levelname == "ERROR"
        assert exception_log.getMessage() == "Request parameter validation error occurred."
        assert exception_log.exc_info is not None, "exc_info should be present in the log record"
        assert exception_log.exc_info[1] == input_error_object

        assert hasattr(exception_log, "error_code"), "error_code should be present in the log record"
        assert getattr(exception_log, "error_code") == expected_response_body["code"]

        assert hasattr(exception_log, "error_message"), "error_message should be present in the log record"
        assert getattr(exception_log, "error_message") == expected_message

        assert hasattr(exception_log, "error_detail"), "error_detail should be present in the log record"
        assert getattr(exception_log, "error_detail") == errors


class TestIsClientError:
    """Unit test class for _is_client_error."""

    @pytest.mark.parametrize(
        "status_code",
        [
            HTTPStatus.BAD_REQUEST.value,  # 400
            HTTPStatus.UNAUTHORIZED.value,  # 401
            HTTPStatus.PAYMENT_REQUIRED.value,  # 402
            HTTPStatus.FORBIDDEN.value,  # 403
            HTTPStatus.NOT_FOUND.value,  # 404
            HTTPStatus.METHOD_NOT_ALLOWED.value,  # 405
            HTTPStatus.NOT_ACCEPTABLE.value,  # 406
            HTTPStatus.PROXY_AUTHENTICATION_REQUIRED.value,  # 407
            HTTPStatus.CONFLICT.value,  # 409
            499,
        ],
    )
    def test_client_error(self, status_code):
        """test client error case.

        Args:
            status_code (int):
                The HTTP status code checked by the SUT.

        """
        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert error_handlers._is_client_error(status_code=status_code)

    @pytest.mark.parametrize(
        "status_code",
        [
            0,
            HTTPStatus.CONTINUE.value,  # 100
            HTTPStatus.OK.value,  # 200
            HTTPStatus.MULTIPLE_CHOICES.value,  # 300
            HTTPStatus.INTERNAL_SERVER_ERROR.value,  # 500
            600,
        ],
    )
    def test_not_client_error(self, status_code):
        """test not client error.

        Args:
            status_code (int):
                The HTTP status code checked by the SUT.

        """
        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert not error_handlers._is_client_error(status_code=status_code)

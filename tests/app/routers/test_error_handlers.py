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

"""Unit test module for error_handlers.py module."""

from http import HTTPStatus
import json
import logging

import pytest
from pytest import LogCaptureFixture
from pytest_mock import MockFixture
from fastapi.testclient import TestClient

from fastapi.exceptions import RequestValidationError
from starlette.requests import Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.datastructures import Headers

from app.hw_control_main import app
import app.common.basic_exceptions as custom_exceptions

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.routers import error_handlers

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

client = TestClient(app, raise_server_exceptions=False)


class TestErrorHandlers:
    """Unit test class for error handler function."""

    @pytest.mark.parametrize("input_exception_instance", [Exception(), RuntimeError()])
    def test_custom_expected_handler(self, caplog: LogCaptureFixture, input_exception_instance):
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

        assert len(caplog.records) == 1

        # Inspection: Check the exception log
        exception_log = caplog.records[-1]
        assert exception_log.levelname == "ERROR"
        assert exception_log.getMessage() == "An unexpected error occurred."
        assert exception_log.exc_info is not None, "exc_info should be present in the log record"
        assert exception_log.exc_info[1] == input_exception_instance

        assert hasattr(exception_log, "error_code"), "error_code should be present in the log record"
        assert getattr(exception_log, "error_code") == expected_response_body["code"]

        assert hasattr(exception_log, "error_message"), "error_message should be present in the log record"
        assert getattr(exception_log, "error_message") == expected_response_body["message"]

    @pytest.mark.parametrize(
        "input_exception_instance, expected_status_code, expected_response_body",
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
        self, caplog: LogCaptureFixture, input_exception_instance, expected_status_code, expected_response_body
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
        "input_status_code, expected_status_code",
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
    def test_custom_http_exception_handler(self, caplog: LogCaptureFixture, input_status_code, expected_status_code):
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

    def test_custom_validation_exception_handler(self, caplog: LogCaptureFixture):
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
        expected_response_body = {
            "code": expected_error_code,
            "message": errors,
        }

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=error_handlers.__name__):
            response = error_handlers.custom_validation_exception_handler(input_request_object, input_error_object)

        response_body = json.loads(bytes(response.body).decode("utf-8"))

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_status_code
        assert response_body["code"] == expected_error_code

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
        assert getattr(exception_log, "error_message") == expected_response_body["message"]


class TestCustomExceptionHandler:  # pylint: disable=R0903
    """Unit test class for custom_exception_handler."""

    @pytest.mark.parametrize(
        "handle_missing_exception",
        [
            Exception,
            RuntimeError,
        ],
    )
    @pytest.mark.parametrize(
        "endpoint_url, endpoint_method, request_body",
        [
            (
                "/cdim/api/v1/cpu/451b0faf-b70d-4476-832a-4c93f0e6e1ce/is-os-ready",
                "GET",
                None,
            ),
        ],
    )
    def test_missing_exception_handling(  # pylint: disable=R0913, R0917
        self,
        mocker: MockFixture,
        handle_missing_exception,
        endpoint_url,
        endpoint_method,
        request_body,
    ):
        """
        Test the custom exception handler for unhandled exceptions in specific endpoints.

        This test method sends a GET request to the provided dummy endpoint URL.
        It verifies that the custom exception handler, which is defined to catch
        Python's built-in Exception, properly handles unhandled exceptions.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        expected_http_status = HTTPStatus.INTERNAL_SERVER_ERROR.value
        expected_response = {
            "code": "CF010BAS001",
            "message": "The server encountered an unexpected internal error and was unable to complete your request.",
        }

        mocker.patch(
            "app.core.control.control_base.PowerControlTargetDevice",
            side_effect=handle_missing_exception,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.request(method=endpoint_method, url=endpoint_url, json=request_body)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response


class TestCustomHTTPExceptionHandler:  # pylint: disable=R0903
    """Unit test class for custom_http_exception_handler."""

    @pytest.mark.parametrize(
        "http_method",
        [
            "GET",
            "PUT",
            "DELETE",
            "POST",
            "PATCH",
        ],
    )
    def test_requested_url_not_found(self, http_method):
        """
        Test that a request to a non-existent URL returns the appropriate
        error response and status code.

        This test function sends requests to a URL that does not exist using
        various HTTP methods (GET, PUT, DELETE, POST, PATCH) and checks that
        the custom error handler for a "Not Found" error is invoked, returning
        the expected status code and response body.

        Args:
            http_method (str): The HTTP method to use for the request. This is
            provided by pytest's parameterize decorator to test multiple methods.

        Expected Response:
            - Status Code: 404 (HTTPStatus.NOT_FOUND)
            - JSON Body: {"code": "EF003BAS011", "message": "Not Found"}
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        expected_http_status = HTTPStatus.NOT_FOUND.value
        expected_response = {
            "code": "EF003BAS011",
            "message": "Not Found",
        }

        undefined_url = "/cdim/api/v1/test/"

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.request(method=http_method, url=undefined_url)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response


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
        assert error_handlers._is_client_error(status_code=status_code)  # pylint: disable=W0212

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
        assert not error_handlers._is_client_error(status_code=status_code)  # pylint: disable=W0212

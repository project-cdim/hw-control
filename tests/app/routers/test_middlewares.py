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

"""Unit test module for middlewares.py"""

import logging
import uuid

import pytest
from pytest_mock import MockFixture
from pytest import LogCaptureFixture
from fastapi.testclient import TestClient
from starlette import requests
from starlette import responses
from starlette.types import Receive, Scope, Send

from app import hw_control_main

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#

from app.routers import middlewares

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


# Prepare a dummy ASGI app
async def dummy_app(scope: Scope, receive: Receive, send: Send):  # pylint: disable=W0613
    """A minimal ASGI application for testing purposes.

    See following link for more details:
    https://asgi.readthedocs.io/en/latest/specs/main.html#applications
    """
    pass  # pylint: disable=W0107


class TestLoggingMiddleware:
    """Test class for LoggingMiddleware."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "input_scope, expected_client, expected_request_content_length",
        [
            (
                {
                    "type": "http",
                    "http_version": "1.1",
                    "method": "POST",
                    "scheme": "http",
                    "path": "/test",
                    "headers": [
                        (b"content-length", b"123"),
                    ],
                    "client": ("127.0.0.1", 54321),
                    "server": ("localhost", 8000),
                },
                {"ip_address": "127.0.0.1", "port": "54321"},
                "123",
            ),
            (  # content-length not set and client not set in the request.
                {
                    "type": "http",
                    "http_version": "1.1",
                    "method": "POST",
                    "scheme": "http",
                    "path": "/test",
                    "headers": [],
                    "server": ("localhost", 8000),
                },
                {"ip_address": "", "port": ""},  # client in log should be empty if not set
                "",  # content-length in log should be empty if not set
            ),
        ],
    )
    @pytest.mark.parametrize(
        "input_response_headers, expected_response_content_length",
        [
            ({"content-length": "456"}, "456"),
            (  # response object without content-length header
                {},
                "0",  # content-length always set by starlette.responses.Response
            ),
        ],
    )
    async def test_log_request_and_response(  # pylint: disable=R0913, R0917
        self,
        caplog: LogCaptureFixture,
        input_scope: Scope,
        expected_client: dict,
        expected_request_content_length: str,
        input_response_headers: dict,
        expected_response_content_length: str,
    ):
        """Test that LoggingMiddleware logs request and response details.

        Args:
            caplog (LogCaptureFixture): The pytest fixture for capturing log messages.
            input_scope (Scope): The ASGI scope representing the incoming request.
            expected_client (dict): Expected client information to be logged.
            expected_request_content_length (str): Expected content length of the request to be logged.
            input_response_headers (dict): Headers of the response to be logged.
            expected_response_content_length (str): Expected content length of the response to be logged.
        """

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Prepare a dummy request object.
        request = requests.Request(input_scope)

        # Prepare a dummy call_next that returns a response
        async def call_next(_):
            return responses.Response(status_code=201, headers=input_response_headers)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#

        middleware = middlewares.LoggingMiddleware(dummy_app)

        caplog.clear()
        with caplog.at_level(logging.INFO, logger=middlewares.__name__):
            _ = await middleware.dispatch(request, call_next)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#

        assert len(caplog.records) == 2

        # Inspection: Check the request log
        request_log = caplog.records[0]
        assert request_log.levelname == "INFO"
        assert request_log.getMessage() == "Accept http request."
        # Check that extra parameters are present as attributes
        assert hasattr(request_log, "http_method"), "`http_method` should be present in the log record"
        assert getattr(request_log, "http_method") == "POST"

        assert hasattr(request_log, "path"), "`path` should be present in the log record"
        assert getattr(request_log, "path") == "/test"

        assert hasattr(request_log, "content_length"), "`content_length` should be present in the log record"
        assert getattr(request_log, "content_length") == expected_request_content_length

        assert hasattr(request_log, "client"), "`client` should be present in the log record"
        assert getattr(request_log, "client") == expected_client

        # Inspection: Check the response log
        response_log = caplog.records[1]
        assert response_log.levelname == "INFO"
        assert response_log.getMessage() == "Return http response."
        # Check that extra parameters are present as attributes
        assert hasattr(response_log, "http_status"), "`http_status` should be present in the log record"
        assert getattr(response_log, "http_status") == 201

        assert hasattr(response_log, "content_length"), "`content_length` should be present in the log record"
        assert getattr(response_log, "content_length") == expected_response_content_length

        assert hasattr(response_log, "app_process_time"), "`app_process_time` should be present in the log record"

    @pytest.mark.asyncio
    async def test_app_process_time_logged(
        self,
        mocker: MockFixture,
        caplog: LogCaptureFixture,
    ):
        """Test that LoggingMiddleware logs application process time.

        Args:
            mocker (MockFixture): The pytest-mock fixture for mocking.
            caplog (LogCaptureFixture): The pytest fixture for capturing log messages.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Prepare a dummy request object.
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/test",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("localhost", 8000),
        }
        request = requests.Request(scope)

        # mock time.perf_counter to simulate process time
        # This is necessary because LoggingMiddleware uses time.perf_counter() to measure the process time,
        # and we want to ensure that the test is consistent by replacing its return value with fixed values.
        # This allows us to predict the process time that will be logged.
        start_time = 100.0
        end_time = 101.23
        perf_counter_values = [start_time, end_time]
        mocker.patch("time.perf_counter", side_effect=perf_counter_values)
        expected_app_process_time = end_time - start_time

        # Prepare a dummy call_next that returns a response
        async def call_next(_):
            return responses.Response(status_code=200)

        # ++++ execution +++++++++++++++++++++++++++++++++++++++++++++#

        middleware = middlewares.LoggingMiddleware(dummy_app)

        caplog.clear()
        with caplog.at_level(logging.INFO, logger=middlewares.__name__):
            _ = await middleware.dispatch(request, call_next)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#

        assert len(caplog.records) == 2

        response_log = caplog.records[1]
        assert hasattr(response_log, "app_process_time")
        assert getattr(response_log, "app_process_time") == expected_app_process_time


client = TestClient(hw_control_main.app)


class TestCorrelationIdMiddlewareSetting:
    """Test class for CorrelationIdMiddleware setting."""

    def test_correlation_id_from_header(self):
        """Test that Correlation ID from header is correctly set in context.

        This test verifies that when a valid Correlation ID is provided in the
        request header, it is correctly set in the context variable and can be
        retrieved during request processing.

        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_correlation_id = str(uuid.uuid4())
        headers = {"x-correlation-id": test_correlation_id}

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        # Send request with Correlation ID header.
        # Send request to non-existent endpoint to avoid auth dependencies in this test.
        response = client.get("/cdim/api/v1/foo", headers=headers)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # 404 is expected for non-existent endpoint
        assert response.status_code == 404

        # Check that extra response header is present
        assert "x-correlation-id" in response.headers, "`x-correlation-id` should be present in the response headers"
        assert response.headers["x-correlation-id"] == test_correlation_id, "correlation-id should match request header"

    def test_correlation_id_generated_when_no_header(self):
        """Test that Correlation ID is generated when no header is provided.

        This test verifies that when no Correlation ID is provided in the
        request header, the generator function creates a new UUID4 and sets
        it in the context variable.
        """
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        # Send request without Correlation ID header.
        # Send request to non-existent endpoint to avoid auth dependencies in this test.
        response = client.get("/cdim/api/v1/foo")

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # 404 is expected for non-existent endpoint
        assert response.status_code == 404

        # Check the correlation-id set by generator
        # UUID4 format validation
        correlation_id = response.headers["x-correlation-id"]
        assert len(correlation_id) == 36, "correlation-id should be standard UUID4 format"
        parsed_uuid = uuid.UUID(correlation_id)
        assert parsed_uuid.version == 4, "correlation-id set by middleware should be UUID4"

    @pytest.mark.parametrize(
        "invalid_correlation_id",
        [
            "invalid-uuid",  # Invalid format
            "12345678-1234-1234-1234-12345678901g",  # Invalid character
            "short-id",  # Too short
            "",  # Empty string
            "12345678-1234-5234-1234-123456789012",  # Invalid version (should be 4)
        ],
    )
    def test_correlation_id_validation_with_invalid_values(self, invalid_correlation_id: str):
        """Test that invalid Correlation IDs are rejected and new ones are generated.

        This test verifies that when an invalid Correlation ID is provided in the
        request header, the validator rejects it and the generator creates a new
        valid UUID4 instead.

        Args:
            invalid_correlation_id (str): An invalid Correlation ID to test.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        headers = {"x-correlation-id": invalid_correlation_id}

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        # Send request with invalid Correlation ID header.
        # Send request to non-existent endpoint to avoid auth dependencies in this test.
        response = client.get("/cdim/api/v1/foo", headers=headers)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # 404 is expected for non-existent endpoint
        assert response.status_code == 404

        # Check the correlation-id set by generator (rejected invalid one)
        assert (
            response.headers["x-correlation-id"] != invalid_correlation_id
        ), "Invalid Correlation ID should be rejected and replaced with a valid one by middleware."

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

import pytest
from pytest_mock import MockFixture
from starlette import requests, responses
from starlette.types import Receive, Scope, Send

from app.routers import middlewares


# Prepare a dummy ASGI app
async def dummy_app(scope: Scope, receive: Receive, send: Send):
    """A minimal ASGI application for testing purposes.

    See following link for more details:
    https://asgi.readthedocs.io/en/latest/specs/main.html#applications
    """
    pass


class TestLoggingMiddleware:
    """Test class for LoggingMiddleware."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("input_scope", "expected_client", "expected_request_content_length"),
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
        ("input_response_headers", "expected_response_content_length"),
        [
            ({"content-length": "456"}, "456"),
            (  # response object without content-length header
                {},
                "0",  # content-length always set by starlette.responses.Response
            ),
        ],
    )
    async def test_log_request_and_response(
        self,
        caplog: pytest.LogCaptureFixture,
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
        caplog: pytest.LogCaptureFixture,
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

# Copyright 2026 NEC Corporation
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

"""Integration tests for middleware behavior via FastAPI app."""

import uuid

import pytest
from asgi_correlation_id import CorrelationIdFilter
from fastapi.testclient import TestClient

from app.routers import middlewares

# Non-existent endpoint URL used to trigger routing through middleware
# without invoking business logic. Returns 404 from custom_http_exception_handler.
_PROBE_URL = "/cdim/api/v1/probe-middleware"


class TestLoggingMiddlewareIntegration:
    """Integration tests verifying LoggingMiddleware logs requests and responses
    in the context of a real FastAPI request cycle."""

    def test_request_and_response_logged(self, test_client: TestClient, caplog: pytest.LogCaptureFixture):
        """Request and response log records are emitted for a normal request."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with caplog.at_level("INFO", logger=middlewares.__name__):
            response = test_client.get(_PROBE_URL)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 404

        log_messages = [r.getMessage() for r in caplog.records]
        assert "Accept http request." in log_messages
        assert "Return http response." in log_messages

    def test_request_log_contains_method_and_path(self, test_client: TestClient, caplog: pytest.LogCaptureFixture):
        """Request log record includes http_method and path attributes."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with caplog.at_level("INFO", logger=middlewares.__name__):
            test_client.get(_PROBE_URL)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        request_log = next(r for r in caplog.records if r.getMessage() == "Accept http request.")
        assert getattr(request_log, "http_method") == "GET"
        assert getattr(request_log, "path") == _PROBE_URL

    def test_response_log_contains_status_and_process_time(
        self, test_client: TestClient, caplog: pytest.LogCaptureFixture
    ):
        """Response log record includes http_status and app_process_time attributes."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with caplog.at_level("INFO", logger=middlewares.__name__):
            test_client.get(_PROBE_URL)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        response_log = next(r for r in caplog.records if r.getMessage() == "Return http response.")
        assert hasattr(response_log, "http_status")
        assert hasattr(response_log, "app_process_time")
        assert getattr(response_log, "http_status") == 404


class TestCorrelationIdMiddlewareIntegration:
    """Integration tests verifying CorrelationIdMiddleware propagates
    and generates Correlation IDs through the FastAPI app."""

    def test_correlation_id_from_header_is_reflected_in_response(self, test_client: TestClient):
        """A valid UUID4 Correlation ID sent in the request header is returned
        unchanged in the response header."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        correlation_id = str(uuid.uuid4())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.get(_PROBE_URL, headers={"x-correlation-id": correlation_id})

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 404
        assert response.headers.get("x-correlation-id") == correlation_id

    def test_correlation_id_is_consistent_across_all_log_records_for_a_request(
        self, test_client: TestClient, caplog: pytest.LogCaptureFixture
    ):
        """Every log record emitted while handling a single request carries the
        same correlation ID as the one supplied in the request header."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        caplog.handler.addFilter(CorrelationIdFilter())
        correlation_id = str(uuid.uuid4())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with caplog.at_level("INFO", logger="app"):
            response = test_client.get(_PROBE_URL, headers={"x-correlation-id": correlation_id})

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.headers.get("x-correlation-id") == correlation_id

        assert len(caplog.records) > 0
        for record in caplog.records:
            assert hasattr(record, "correlation_id")
            assert record.correlation_id == correlation_id

    def test_correlation_id_generated_when_header_absent(self, test_client: TestClient):
        """When no Correlation ID is sent, the middleware generates a valid UUID4
        and returns it in the response header."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.get(_PROBE_URL)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 404
        correlation_id_header = response.headers.get("x-correlation-id")
        assert correlation_id_header is not None
        parsed = uuid.UUID(correlation_id_header)
        assert parsed.version == 4

    @pytest.mark.parametrize(
        "invalid_correlation_id",
        [
            "invalid-uuid",
            "12345678-1234-1234-1234-12345678901g",
            "short-id",
            "",
            "12345678-1234-5234-1234-123456789012",  # version 5, not 4
        ],
    )
    def test_invalid_correlation_id_is_replaced_with_new_uuid4(
        self, test_client: TestClient, invalid_correlation_id: str
    ):
        """Invalid Correlation IDs are rejected by the validator and replaced
        with a fresh UUID4."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.get(_PROBE_URL, headers={"x-correlation-id": invalid_correlation_id})

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 404
        returned_id = response.headers.get("x-correlation-id")
        assert returned_id != invalid_correlation_id
        parsed = uuid.UUID(returned_id)
        assert parsed.version == 4

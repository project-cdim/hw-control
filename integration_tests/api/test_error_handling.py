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

"""Integration tests for error handler behavior via the FastAPI app.

Verifies that error handlers are correctly wired to the app and produce
the expected HTTP responses and error codes when exceptions occur.
"""

import uuid

import pydantic
import pytest
import requests
from asgi_correlation_id import CorrelationIdFilter
from fastapi.testclient import TestClient
from pytest_mock import MockFixture

import app.common.basic_exceptions as exc
from app.routers.control.control_api import AggregationControlAction, PowerControlAction

_DEVICE_UUID = "451b0faf-b70d-4476-832a-4c93f0e6e1ce"
_DOWNSTREAM_DEVICE_UUID = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"
_POWER_URL = f"/cdim/api/v1/devices/{_DEVICE_UUID}/power"
_IS_OS_READY_URL = f"/cdim/api/v1/cpu/{_DEVICE_UUID}/is-os-ready"
_AGGREGATION_URL = f"/cdim/api/v1/devices/{_DEVICE_UUID}/aggregations"


class TestEndpointNotFoundErrorHandler:
    """Requests to non-existent endpoints return 404 with the standard error format."""

    @pytest.mark.parametrize("http_method", ["GET", "PUT", "DELETE", "POST", "PATCH"])
    def test_undefined_path_returns_404_with_standard_error_format(self, test_client: TestClient, http_method: str):
        """All HTTP methods to an undefined path go through custom_http_exception_handler
        and return 404 with the standard error code."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        undefined_url = "/cdim/api/v1/undefined-path"

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.request(method=http_method, url=undefined_url)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 404
        body = response.json()
        assert set(body.keys()) == {"code", "message"}
        assert body["code"] == "EF003BAS011"
        assert body["message"] == "Not Found"


class TestMethodNotAllowedErrorHandler:
    """Requests with an unsupported HTTP method return 405 with the standard error format."""

    @pytest.mark.parametrize(
        "action",
        [
            PowerControlAction.ON.value,
            PowerControlAction.OFF.value,
            PowerControlAction.FORCE_OFF.value,
            PowerControlAction.RESET.value,
        ],
    )
    @pytest.mark.parametrize("http_method", ["GET", "DELETE", "POST", "PATCH"])
    def test_wrong_method_on_power_endpoint(self, test_client: TestClient, http_method: str, action: str):
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.request(method=http_method, url=_POWER_URL, json={"action": action})

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 405
        body = response.json()
        assert body["code"] == "EF003BAS011"
        assert body["message"] == "Method Not Allowed"

    @pytest.mark.parametrize("http_method", ["PUT", "DELETE", "POST", "PATCH"])
    def test_wrong_method_on_is_os_ready_endpoint(self, test_client: TestClient, http_method: str):
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.request(method=http_method, url=_IS_OS_READY_URL)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 405
        body = response.json()
        assert body["code"] == "EF003BAS011"
        assert body["message"] == "Method Not Allowed"

    @pytest.mark.parametrize(
        "action",
        [AggregationControlAction.CONNECT.value, AggregationControlAction.DISCONNECT.value],
    )
    @pytest.mark.parametrize("http_method", ["GET", "DELETE", "POST", "PATCH"])
    def test_wrong_method_on_aggregations_endpoint(self, test_client: TestClient, http_method: str, action: str):
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.request(
            method=http_method,
            url=_AGGREGATION_URL,
            json={"destinationDeviceID": _DOWNSTREAM_DEVICE_UUID, "action": action},
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 405
        body = response.json()
        assert body["code"] == "EF003BAS011"
        assert body["message"] == "Method Not Allowed"


class TestUnexpectedExceptionHandler:
    """Unhandled Python exceptions (Exception, RuntimeError) are caught by
    custom_exception_handler and return 500 with the standard error code."""

    @pytest.mark.parametrize(
        "raised_exception",
        [Exception, RuntimeError, ZeroDivisionError, pydantic.ValidationError, requests.exceptions.RequestException],
    )
    def test_unhandled_exception(self, test_client: TestClient, mocker: MockFixture, raised_exception: type):
        """When an endpoint raises an unexpected exception, the app returns 500."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        mocker.patch(
            "app.core.control.control_base.PowerControlTargetDevice",
            side_effect=raised_exception,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.get(_IS_OS_READY_URL)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 500
        body = response.json()
        assert body["code"] == "CF010BAS001"
        assert body["message"] == (
            "The server encountered an unexpected internal error and was unable to complete your request."
        )

    def test_unhandled_exception_response_and_logs_carry_correlation_id(
        self, test_client: TestClient, mocker: MockFixture, caplog: pytest.LogCaptureFixture
    ):
        """custom_exception_handler is the outermost handler in Starlette's stack, so
        CorrelationIdMiddleware's on-response-return processing never runs for it.
        The handler must therefore set the correlation ID header and log it itself."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        caplog.handler.addFilter(CorrelationIdFilter())
        correlation_id = str(uuid.uuid4())

        mocker.patch(
            "app.core.control.control_base.PowerControlTargetDevice",
            side_effect=RuntimeError,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with caplog.at_level("INFO", logger="app"):
            response = test_client.get(_IS_OS_READY_URL, headers={"x-correlation-id": correlation_id})

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 500
        assert response.headers.get("x-correlation-id") == correlation_id

        assert len(caplog.records) > 0
        for record in caplog.records:
            assert hasattr(record, "correlation_id")
            assert record.correlation_id == correlation_id


class TestHWControlErrorHandler:
    """BaseHWControlError subclasses are caught by hw_control_error_handler and
    mapped to the correct HTTP status code and error code."""

    @pytest.mark.parametrize(
        ("raised_exception", "expected_status", "expected_code"),
        [
            (
                exc.RequestNotSupportedHWControlError,
                400,
                "EF003BAS010",
            ),
            (
                exc.DeviceNotFoundHWControlError,
                404,
                "EF013BAS000",
            ),
            (
                exc.BaseHWControlError,
                500,
                "CF000BAS000",
            ),
        ],
    )
    def test_hw_control_error_maps_to_correct_status(
        self,
        test_client: TestClient,
        mocker: MockFixture,
        raised_exception: type,
        expected_status: int,
        expected_code: str,
    ):
        """Each BaseHWControlError subclass produces the correct HTTP status and error code."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        mocker.patch(
            "app.core.control.control_base.PowerControlTargetDevice",
            side_effect=raised_exception,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.get(_IS_OS_READY_URL)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_status
        assert response.json()["code"] == expected_code

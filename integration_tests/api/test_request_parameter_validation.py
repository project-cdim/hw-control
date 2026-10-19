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

"""Integration tests for request parameter validation and routing errors.

Verifies that invalid requests trigger the appropriate error handlers:
- custom_validation_exception_handler: returns 422 for malformed parameters
- custom_http_exception_handler: returns 404 for missing path parameters
"""

import pytest
from fastapi.testclient import TestClient

_DEVICE_UUID = "451b0faf-b70d-4476-832a-4c93f0e6e1ce"
_DOWNSTREAM_DEVICE_UUID = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"
_POWER_URL = f"/cdim/api/v1/devices/{_DEVICE_UUID}/power"
_AGGREGATION_URL = f"/cdim/api/v1/devices/{_DEVICE_UUID}/aggregations"
_IS_OS_READY_URL = f"/cdim/api/v1/cpu/{_DEVICE_UUID}/is-os-ready"


class TestPowerControlValidation:
    """Validation tests for the Power Control endpoint."""

    @pytest.mark.parametrize(
        ("path_device_id", "request_body"),
        [
            ("not-a-uuid", {"action": "on"}),
            (_DEVICE_UUID, {"action": "unsupported-action"}),
            (_DEVICE_UUID, {}),
        ],
    )
    def test_invalid_request_returns_422_with_standard_error_code(
        self, test_client: TestClient, path_device_id: str, request_body: dict
    ):
        """Invalid path or body parameters return 422 with error code EF003BAS012."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.put(
            url=f"/cdim/api/v1/devices/{path_device_id}/power",
            json=request_body,
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "EF003BAS012"
        assert body["message"] == "The request parameter is invalid or missing."

    def test_missing_body_returns_422_with_standard_error_code(self, test_client: TestClient):
        """Sending no body at all (not even '{}') also returns 422 with error code EF003BAS012."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.put(url=_POWER_URL)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "EF003BAS012"
        assert body["message"] == "The request parameter is invalid or missing."

    def test_validation_error_response_includes_detail_for_single_error(self, test_client: TestClient):
        """Validation error response includes a 'detail' field with error specifics for a single error."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.put(
            url=f"/cdim/api/v1/devices/{_DEVICE_UUID}/power",
            json={},
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 422
        body = response.json()
        assert body["detail"] == [
            {
                "type": "missing",
                "loc": ["body", "action"],
                "msg": "Field required",
                "input": {},
            }
        ]

    @pytest.mark.parametrize(
        "http_method", ["GET", "PUT"]
    )  # Path resolution (404) takes precedence over method validation (405)
    def test_empty_device_id_returns_404(self, test_client: TestClient, http_method: str):
        """Empty deviceID in the path returns 404."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.request(method=http_method, url="/cdim/api/v1/devices//power")

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "EF003BAS011"
        assert body["message"] == "Not Found"


class TestIsOsReadyValidation:
    """Validation tests for the Is OS Ready endpoint."""

    @pytest.mark.parametrize(
        ("path_device_id", "query_timeout"),
        [
            ("not-a-uuid", 30),
            (_DEVICE_UUID, 0),
            (_DEVICE_UUID, 601),
            (_DEVICE_UUID, "not-a-number"),
        ],
    )
    def test_invalid_request_returns_422_with_standard_error_code(
        self, test_client: TestClient, path_device_id: str, query_timeout
    ):
        """Invalid path or query parameters return 422 with error code EF003BAS012."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.get(
            url=f"/cdim/api/v1/cpu/{path_device_id}/is-os-ready",
            params={"timeOut": query_timeout},
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "EF003BAS012"

    @pytest.mark.parametrize(
        "http_method", ["GET", "PUT"]
    )  # Path resolution (404) takes precedence over method validation (405)
    def test_empty_device_id_returns_404(self, test_client: TestClient, http_method: str):
        """Empty CPUDeviceID in the path returns 404."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.request(method=http_method, url="/cdim/api/v1/cpu//is-os-ready")

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "EF003BAS011"
        assert body["message"] == "Not Found"


class TestDeviceAggregationControlValidation:
    """Validation tests for the Device Aggregation Control endpoint."""

    @pytest.mark.parametrize(
        ("path_device_id", "request_body"),
        [
            (
                "not-a-uuid",
                {"destinationDeviceID": _DOWNSTREAM_DEVICE_UUID, "action": "connect"},
            ),
            (
                _DEVICE_UUID,
                {"destinationDeviceID": "not-a-uuid", "action": "connect"},
            ),
            (
                _DEVICE_UUID,
                {"action": "connect"},
            ),
            (
                _DEVICE_UUID,
                {"destinationDeviceID": _DOWNSTREAM_DEVICE_UUID, "action": "unsupported-action"},
            ),
            (
                _DEVICE_UUID,
                {"destinationDeviceID": _DOWNSTREAM_DEVICE_UUID},
            ),
        ],
    )
    def test_invalid_request_returns_422_with_standard_error_code(
        self, test_client: TestClient, path_device_id: str, request_body: dict
    ):
        """Invalid path or body parameters return 422 with error code EF003BAS012."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.put(
            url=f"/cdim/api/v1/devices/{path_device_id}/aggregations",
            json=request_body,
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "EF003BAS012"
        assert body["message"] == "The request parameter is invalid or missing."

    def test_missing_body_returns_422_with_standard_error_code(self, test_client: TestClient):
        """Sending no body at all (not even '{}') also returns 422 with error code EF003BAS012."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.put(url=_AGGREGATION_URL)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "EF003BAS012"
        assert body["message"] == "The request parameter is invalid or missing."

    def test_validation_error_response_includes_detail_for_multiple_errors(self, test_client: TestClient):
        """Validation error response includes all errors in 'detail' when both path and body are invalid."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.put(
            url="/cdim/api/v1/devices/not-a-uuid/aggregations",
            json={"destinationDeviceID": "also-not-a-uuid", "action": "connect"},
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 422
        body = response.json()
        assert body["detail"] == [
            {
                "type": "uuid_parsing",
                "loc": ["path", "sourceDeviceID"],
                "msg": "Input should be a valid UUID, invalid character: found `n` at 1",
                "input": "not-a-uuid",
                "ctx": {"error": "invalid character: found `n` at 1"},
            },
            {
                "type": "uuid_parsing",
                "loc": ["body", "destinationDeviceID"],
                "msg": "Input should be a valid UUID, invalid character: found `l` at 2",
                "input": "also-not-a-uuid",
                "ctx": {"error": "invalid character: found `l` at 2"},
            },
        ]

    @pytest.mark.parametrize(
        "http_method", ["GET", "PUT"]
    )  # Path resolution (404) takes precedence over method validation (405)
    def test_empty_device_id_returns_404(self, test_client: TestClient, http_method: str):
        """Empty sourceDeviceID in the path returns 404."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.request(method=http_method, url="/cdim/api/v1/devices//aggregations")

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 404
        body = response.json()
        assert body["code"] == "EF003BAS011"
        assert body["message"] == "Not Found"

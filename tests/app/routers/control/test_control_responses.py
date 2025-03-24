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

"""Unit test module for control_responses module ."""

from http import HTTPStatus
import json
import pytest

from tests.app.routers.control import test_util

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.routers.control import control_responses  # type: ignore

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestGenerateApiResponse:
    """Unit test class for control_responses.generate_api_response"""

    @pytest.mark.parametrize(
        "response_body, expected_status_code, expected_response_body",
        [
            (  # input AggregationControlResponseBody case.
                control_responses.AggregationControlResponseBody(
                    cpu_device_id=test_util.DummyCpuInfo.DEVICE_ID.value,
                    device_id=test_util.DummyDeviceInfo.DEVICE_ID.value,
                ),
                HTTPStatus.OK.value,
                json.dumps(
                    {
                        "CPUDeviceID": test_util.DummyCpuInfo.DEVICE_ID.value,
                        "deviceID": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    },
                    separators=(",", ":"),
                ),
            ),
            (  # input PowerControlResponseBody case.
                control_responses.PowerControlResponseBody(device_id=test_util.DummyDeviceInfo.DEVICE_ID.value),
                HTTPStatus.OK.value,
                json.dumps({"deviceID": test_util.DummyDeviceInfo.DEVICE_ID.value}, separators=(",", ":")),
            ),
            (  # input IsOsReadyResponseBody case.
                # target-os is ready case.
                control_responses.IsOsReadyResponseBody(
                    status=True, ip_address=test_util.DummyCpuInfo.IP_ADDRESS.value
                ),
                HTTPStatus.OK.value,
                json.dumps(
                    {"status": True, "IPAddress": test_util.DummyCpuInfo.IP_ADDRESS.value}, separators=(",", ":")
                ),
            ),
            (  # input IsOsReadyResponseBody case.
                # target-os is not ready case.
                control_responses.IsOsReadyResponseBody(
                    status=False, ip_address=test_util.DummyCpuInfo.IP_ADDRESS.value
                ),
                HTTPStatus.OK.value,
                json.dumps(
                    {"status": False, "IPAddress": test_util.DummyCpuInfo.IP_ADDRESS.value}, separators=(",", ":")
                ),
            ),
        ],
    )
    def test_generate_response_default_status_code(self, response_body, expected_status_code, expected_response_body):
        """test can generate response-object default status-code case.

        Args:
            response_body (ResponseBody):
                ResponseBody object input by caller.

            expected_status_code (int):
                expected HTTP-status-code.

            expected_response_body (json):
                expected HTTP-response-body.
        """
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual = control_responses.generate_api_response(response_body=response_body)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual.status_code == expected_status_code
        assert actual.body.decode("utf-8") == expected_response_body

    @pytest.mark.parametrize(
        "responses_body, responses_status_code, expected_status_code, expected_response_body",
        [
            (  # HTTP-status-code = 400 BAD_REQUEST case.
                control_responses.PowerControlResponseBody(device_id=test_util.DummyCpuInfo.DEVICE_ID.value),
                HTTPStatus.BAD_REQUEST.value,
                HTTPStatus.BAD_REQUEST.value,
                json.dumps({"deviceID": test_util.DummyCpuInfo.DEVICE_ID.value}, separators=(",", ":")),
            ),
            (  # HTTP-status-code = 500 INTERNAL_SERVER_ERROR case.
                control_responses.PowerControlResponseBody(device_id=test_util.DummyCpuInfo.DEVICE_ID.value),
                HTTPStatus.INTERNAL_SERVER_ERROR.value,
                HTTPStatus.INTERNAL_SERVER_ERROR.value,
                json.dumps({"deviceID": test_util.DummyCpuInfo.DEVICE_ID.value}, separators=(",", ":")),
            ),
            (  # input ErrorResponseBody case.
                control_responses.ErrorResponseBody(code="EF003BAS011", message="Not Found"),
                HTTPStatus.NOT_FOUND.value,
                HTTPStatus.NOT_FOUND.value,
                json.dumps({"code": "EF003BAS011", "message": "Not Found"}, separators=(",", ":")),
            ),
        ],
    )
    def test_generate_response_and_set_status_code(
        self, responses_body, responses_status_code, expected_status_code, expected_response_body
    ):
        """test can generate response and set HTTP-status-code.

        Args:
            responses_body (_type_):
                ResponseBody object input by caller.

            responses_status_code (int):
                HTTP-status-code input by caller.

            expected_status_code (int):
                expected HTTP-status-code.

            expected_response_body (json):
                expected HTTP-response_body.

        """
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual = control_responses.generate_api_response(
            response_body=responses_body, status_code=responses_status_code
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual.status_code == expected_status_code
        assert actual.body.decode("utf-8") == expected_response_body

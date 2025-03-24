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

# test_control_api.py
"""Unit test module for control_api module ."""

from http import HTTPStatus
import json
import logging
import uuid

import pytest
from pytest_mock import MockFixture
from fastapi.testclient import TestClient

from tests.app.routers.control.test_util import CONSTANT_REQUEST_ID
from tests import test_util

import app.common.basic_exceptions as exc  # type: ignore
from app.core.control import fm_control  # type: ignore
from app.core.control import oob_control
from app.core.control import agent_control
from app.core.control import control_base
from app.hw_control_main import app  # type: ignore

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.routers.control import control_api  # type: ignore

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

client = TestClient(app, raise_server_exceptions=False)


class TestAggregationControlApi:
    """Unit test class for aggregation_control_api."""

    @pytest.mark.parametrize(
        "action, controller_method",
        [
            (control_api.AggregationControlAction.CONNECT.value, "connect"),
            (control_api.AggregationControlAction.DISCONNECT.value, "disconnect"),
        ],
    )
    def test_success(self, caplog, mocker: MockFixture, action, controller_method):
        """test success case.

        Args:
            mocker (MockFixture): The fixture used to mock objects.

            action (str):
                action parameter input by caller.

        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        host_cpu_id = test_util.DummyCpuInfo.DEVICE_ID.value
        target_device_id = test_util.DummyDeviceInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.OK.value
        expected_response = {"CPUDeviceID": host_cpu_id, "deviceID": target_device_id}

        # Set up the mock.
        mocker.patch.object(uuid, "uuid4", return_value=CONSTANT_REQUEST_ID)
        mocker.patch.object(
            fm_control.FmControlTargetDevice,
            "model_post_init",
            return_value=None,
        )
        mocker.patch.object(fm_control.FmController, controller_method, return_value=None)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="LOGGER"):
            response = client.put(
                url=f"/cdim/api/v1/cpu/{host_cpu_id}/aggregations",
                json={"deviceID": target_device_id, "action": action},
            )

        # HttpRequestLog
        request_log_message = json.loads(caplog.records[0].getMessage())

        # HttpResponseLog
        response_log_message = json.loads(caplog.records[-1].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

        assert caplog.records[0].levelname == "INFO"
        assert request_log_message["message"]["request_id"] == CONSTANT_REQUEST_ID
        assert request_log_message["message"]["action"] == "receive http request"
        assert request_log_message["message"]["url"] == f"http://testserver/cdim/api/v1/cpu/{host_cpu_id}/aggregations"
        assert request_log_message["message"]["client_ip_address"] == "testclient"
        assert request_log_message["message"]["client_port"] == 50000
        assert request_log_message["message"]["path_parameter"] == {"CPUDeviceID": host_cpu_id}
        assert request_log_message["message"]["query_parameter"] is None
        assert request_log_message["message"]["body_parameter"] == {"deviceID": target_device_id, "action": action}

        assert caplog.records[-1].levelname == "INFO"
        assert response_log_message["message"]["request_id"] == CONSTANT_REQUEST_ID
        assert response_log_message["message"]["action"] == "return http response"
        assert response_log_message["message"]["status_code"] == HTTPStatus.OK.value
        assert response_log_message["message"]["response_body"] == {
            "CPUDeviceID": host_cpu_id,
            "deviceID": target_device_id,
        }

    @pytest.mark.parametrize(
        "action",
        [control_api.AggregationControlAction.CONNECT.value, control_api.AggregationControlAction.DISCONNECT.value],
    )
    @pytest.mark.parametrize(
        "http_method",
        [
            "GET",
            "DELETE",
            "POST",
            "PATCH",
        ],
    )
    def test_method_not_allow(self, action, http_method):
        """test requested method not allow case.

        Args:
            mocker (MockFixture): The fixture used to mock objects.

            action (str):
                The input action parameter to be tested.

            http_method (str):
                The input HTTP method to be tested.
        """

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        host_cpu_id = test_util.DummyCpuInfo.DEVICE_ID.value
        target_device_id = test_util.DummyDeviceInfo.DEVICE_ID.value

        url = f"/cdim/api/v1/cpu/{host_cpu_id}/aggregations"
        request_body = {"deviceID": target_device_id, "action": action}

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response_body = {
            "code": "EF003BAS011",
            "message": "Method Not Allowed",
        }

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.request(
            method=http_method,
            url=url,
            json=request_body,
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response_body

    @pytest.mark.parametrize(
        "path_parameter, body_parameter",
        [
            (  # path_parameter invalid
                "Foo",
                {
                    "deviceID": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "action": control_api.AggregationControlAction.CONNECT.value,
                },
            ),
            (  # body_parameter deviceID invalid
                test_util.DummyCpuInfo.DEVICE_ID.value,
                {
                    "deviceID": "Foo",
                    "action": control_api.AggregationControlAction.CONNECT.value,
                },
            ),
            (  # body_parameter deviceID unset
                test_util.DummyCpuInfo.DEVICE_ID.value,
                {
                    "action": control_api.AggregationControlAction.CONNECT.value,
                },
            ),
            (  # body_parameter action invalid
                test_util.DummyCpuInfo.DEVICE_ID.value,
                {
                    "deviceID": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "action": "Foo",
                },
            ),
            (  # body_parameter action unset
                test_util.DummyCpuInfo.DEVICE_ID.value,
                {
                    "deviceID": test_util.DummyDeviceInfo.DEVICE_ID.value,
                },
            ),
        ],
    )
    def test_invalid_request_parameter(self, path_parameter, body_parameter):
        """test invalid request parameter case.

        Args:
            mocker (MockFixture): The fixture used to mock objects.

            path_parameter:
                The input path parameter to be tested.

            body_parameter (str):
                The input body parameters to be tested.
        """

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_error_code = "EF003BAS012"

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.put(
            url=f"/cdim/api/v1/cpu/{path_parameter}/aggregations",
            json=body_parameter,
        )

        actual_status_code = response.status_code
        actual_error_code = response.json().get("code")

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_status_code == expected_http_status
        assert actual_error_code == expected_error_code

    @pytest.mark.parametrize(
        "action",
        [control_api.AggregationControlAction.CONNECT.value, control_api.AggregationControlAction.DISCONNECT.value],
    )
    def test_device_can_not_create(self, mocker: MockFixture, action):
        """test device object can not create case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++++++++++#
        host_cpu_id = test_util.DummyCpuInfo.DEVICE_ID.value
        target_device_id = test_util.DummyDeviceInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response = {
            "code": "EF003BAS010",
            "message": "Your request is not supported for the specified target device.",
        }

        # Set up the mock.
        mocker.patch.object(
            fm_control.FmControlTargetDevice, "model_post_init", side_effect=exc.RequestNotSupportedHwControlError
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#

        response = client.put(
            url=f"/cdim/api/v1/cpu/{host_cpu_id}/aggregations",
            json={"deviceID": target_device_id, "action": action},
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

    @pytest.mark.parametrize(
        "action",
        [control_api.AggregationControlAction.CONNECT.value, control_api.AggregationControlAction.DISCONNECT.value],
    )
    def test_device_pair_can_not_create(self, mocker: MockFixture, action):
        """test device pair object can not create case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++++++++++#
        # device_id of host_cpu and target_device are the same case.
        host_cpu_id = "ec020a7c-5014-4c2d-8682-45f69c936e3a"
        target_device_id = "ec020a7c-5014-4c2d-8682-45f69c936e3a"

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response = {
            "code": "EF003BAS010",
            "message": "Your request is not supported for the specified target device.",
        }

        # Set up the mock.
        mocker.patch.object(fm_control.FmControlTargetDevice, "model_post_init", return_value=None)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.put(
            url=f"/cdim/api/v1/cpu/{host_cpu_id}/aggregations",
            json={"deviceID": target_device_id, "action": action},
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

    @pytest.mark.parametrize(
        "action",
        [control_api.AggregationControlAction.CONNECT.value, control_api.AggregationControlAction.DISCONNECT.value],
    )
    def test_device_pair_busy(self, mocker: MockFixture, action):
        """test device pair busy case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        host_cpu_id = test_util.DummyCpuInfo.DEVICE_ID.value
        target_device_id = test_util.DummyDeviceInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.SERVICE_UNAVAILABLE.value
        expected_response = {
            "code": "ER005BAS002",
            "message": f"The specified device is busy. The following Device ID is relevant: {target_device_id}",
        }

        # Set up the mock.
        mocker.patch.object(fm_control.FmControlTargetDevice, "model_post_init", return_value=None)
        mocker.patch.object(
            fm_control.FmControlTargetDevicePair,
            "get_lock",
            side_effect=exc.DeviceBusyHwControlError(
                additional_message=f"The following Device ID is relevant: {target_device_id}"
            ),
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.put(
            url=f"/cdim/api/v1/cpu/{host_cpu_id}/aggregations",
            json={"deviceID": target_device_id, "action": action},
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

    @pytest.mark.parametrize(
        "action, controller_method",
        [
            (control_api.AggregationControlAction.CONNECT.value, "connect"),
            (control_api.AggregationControlAction.DISCONNECT.value, "disconnect"),
        ],
    )
    def test_controller_raise(self, mocker: MockFixture, action, controller_method):
        """test FmController raise Exception."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        host_cpu_id = test_util.DummyCpuInfo.DEVICE_ID.value
        target_device_id = test_util.DummyDeviceInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response = {
            "code": "EF003BAS010",
            "message": "Your request is not supported for the specified target device.",
        }

        # Set up the mock.
        mocker.patch.object(
            fm_control.FmControlTargetDevice,
            "model_post_init",
            return_value=None,
        )

        mocker.patch.object(
            fm_control.FmController, controller_method, side_effect=exc.RequestNotSupportedHwControlError
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.put(
            url=f"/cdim/api/v1/cpu/{host_cpu_id}/aggregations",
            json={"deviceID": target_device_id, "action": action},
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response


class TestPerformPowerOff:
    """Unit test class for control_api._perform_power_off ."""

    def test_power_off_via_oob_success(self, mocker: MockFixture, default_power_control_target_device_fixture):
        """Test power off via OOB success case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock.
        mocker.patch.object(
            oob_control.OobController,
            "power_off",
            return_value=None,
        )

        mocker.patch.object(
            agent_control.ControlTargetAgent,
            "model_post_init",
            side_effect=exc.RequestNotSupportedHwControlError,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        control_api._perform_power_off(  # pylint: disable=W0212
            target_device=default_power_control_target_device_fixture,
        )

    def test_power_off_via_oob_error(
        self,
        mocker: MockFixture,
        default_power_control_target_device_fixture,
    ):
        """Test power off via OOB error case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock.
        mocker.patch.object(oob_control.OobController, "power_off", side_effect=exc.PowerOffFailureHwControlError)

        mocker.patch.object(
            agent_control.ControlTargetAgent,
            "model_post_init",
            side_effect=exc.RequestNotSupportedHwControlError,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.PowerOffFailureHwControlError):
            control_api._perform_power_off(  # pylint: disable=W0212
                target_device=default_power_control_target_device_fixture
            )

    def test_shutdown_via_agent_success(
        self,
        mocker: MockFixture,
        default_power_control_target_device_fixture,
        default_control_target_agent_fixture,
    ):
        """Test power off via Agent success case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock.
        mocker.patch.object(agent_control.AgentController, "os_shutdown", return_value=None)

        mocker.patch(
            "app.core.control.agent_control.ControlTargetAgent",
            return_value=default_control_target_agent_fixture,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        control_api._perform_power_off(  # pylint: disable=W0212
            target_device=default_power_control_target_device_fixture
        )

    def test_shutdown_via_agent_error(
        self,
        mocker: MockFixture,
        default_power_control_target_device_fixture,
        default_control_target_agent_fixture,
    ):
        """Test power off via Agent error case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock.
        mocker.patch.object(
            agent_control.AgentController,
            "os_shutdown",
            side_effect=exc.RequestNotSupportedHwControlError,
        )

        mocker.patch(
            "app.core.control.agent_control.ControlTargetAgent",
            return_value=default_control_target_agent_fixture,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHwControlError):
            control_api._perform_power_off(  # pylint: disable=W0212
                target_device=default_power_control_target_device_fixture
            )


class TestPowerControlApi:
    """Unit test class for power_control_api."""

    @pytest.mark.parametrize(
        "action, controller_method",
        [
            (control_api.PowerControlAction.ON.value, "power_on"),
            (control_api.PowerControlAction.OFF.value, "power_off"),
            (control_api.PowerControlAction.FORCE_OFF.value, "force_off"),
            (control_api.PowerControlAction.RESET.value, "reset"),
        ],
    )
    def test_success(
        self, caplog, mocker: MockFixture, action, controller_method, default_power_control_target_device_fixture
    ):
        """test success case.

        Args:
            caplog (LogCaptureFixture): The fixture used to capture log messages.

            mocker (MockFixture): The fixture used to mock objects.

            action (str):
                action parameter input by caller.

        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCpuInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.OK.value
        expected_response = {"deviceID": target_device_id}

        mocker.patch.object(uuid, "uuid4", return_value=CONSTANT_REQUEST_ID)
        mocker.patch.object(oob_control.OobController, controller_method, return_value=None)

        mocker.patch.object(
            control_base.PowerControlTargetDevice,
            "model_post_init",
            return_value=default_power_control_target_device_fixture,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="LOGGER"):
            response = client.put(
                url=f"/cdim/api/v1/devices/{target_device_id}/power",
                json={"action": action},
            )

        # HttpRequestLog
        request_log_message = json.loads(caplog.records[0].getMessage())

        # HttpResponseLog
        response_log_message = json.loads(caplog.records[-1].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

        # check HttpRequestLog
        assert caplog.records[0].levelname == "INFO"
        assert request_log_message["message"]["request_id"] == CONSTANT_REQUEST_ID
        assert request_log_message["message"]["action"] == "receive http request"
        assert (
            request_log_message["message"]["url"] == f"http://testserver/cdim/api/v1/devices/{target_device_id}/power"
        )
        assert request_log_message["message"]["client_ip_address"] == "testclient"
        assert request_log_message["message"]["client_port"] == 50000
        assert request_log_message["message"]["path_parameter"] == {"deviceID": target_device_id}
        assert request_log_message["message"]["query_parameter"] is None
        assert request_log_message["message"]["body_parameter"] == {"action": action}

        # check HttpResponseLog
        assert caplog.records[-1].levelname == "INFO"
        assert response_log_message["message"]["request_id"] == CONSTANT_REQUEST_ID
        assert response_log_message["message"]["action"] == "return http response"
        assert response_log_message["message"]["status_code"] == HTTPStatus.OK.value
        assert response_log_message["message"]["response_body"] == {"deviceID": target_device_id}

    @pytest.mark.parametrize(
        "action",
        [
            control_api.PowerControlAction.ON.value,
            control_api.PowerControlAction.OFF.value,
            control_api.PowerControlAction.FORCE_OFF.value,
            control_api.PowerControlAction.RESET.value,
        ],
    )
    @pytest.mark.parametrize(
        "http_method",
        [
            "GET",
            "DELETE",
            "POST",
            "PATCH",
        ],
    )
    def test_method_not_allow(self, action, http_method):
        """test requested method not allow case.

        Args:
            mocker (MockFixture): The fixture used to mock objects.

            action (str):
                The input action parameter to be tested.

            http_method (str):
                The input HTTP method to be tested.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCpuInfo.DEVICE_ID.value

        url = f"/cdim/api/v1/devices/{target_device_id}/power"
        request_body = {"action": action}

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response_body = {
            "code": "EF003BAS011",
            "message": "Method Not Allowed",
        }

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.request(
            method=http_method,
            url=url,
            json=request_body,
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response_body

    @pytest.mark.parametrize(
        "path_parameter, body_parameter",
        [
            (  # path_parameter invalid
                "Foo",
                {
                    "action": control_api.AggregationControlAction.CONNECT.value,
                },
            ),
            (  # body_parameter action invalid
                test_util.DummyCpuInfo.DEVICE_ID.value,
                {
                    "action": "Foo",
                },
            ),
            (  # body_parameter action unset
                test_util.DummyCpuInfo.DEVICE_ID.value,
                {},
            ),
        ],
    )
    def test_invalid_request_parameter(self, path_parameter, body_parameter):
        """test invalid request parameter case.

        Args:
            mocker (MockFixture): The fixture used to mock objects.

            path_parameter:
                The input path parameter to be tested.

            body_parameter (str):
                The input body parameters to be tested.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_error_code = "EF003BAS012"

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.put(
            url=f"/cdim/api/v1/devices/{path_parameter}/power",
            json=body_parameter,
        )

        actual_status_code = response.status_code
        actual_error_code = response.json().get("code")

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_status_code == expected_http_status
        assert actual_error_code == expected_error_code

    @pytest.mark.parametrize(
        "action",
        [
            control_api.PowerControlAction.ON.value,
            control_api.PowerControlAction.OFF.value,
            control_api.PowerControlAction.FORCE_OFF.value,
            control_api.PowerControlAction.RESET.value,
        ],
    )
    def test_device_raise(self, mocker: MockFixture, action):
        """test device raise Exception.

        Args:
            mocker (MockFixture): The fixture used to mock objects.

            mocker (MockFixture):
                Provide mock objects for classes and methods that the function under test depends on.

            action (str):
                action parameter input by caller.

        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCpuInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response = {
            "code": "EF003BAS010",
            "message": "Your request is not supported for the specified target device.",
        }

        # Set up the mock.
        mocker.patch.object(
            control_base.PowerControlTargetDevice,
            "model_post_init",
            side_effect=exc.RequestNotSupportedHwControlError,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.put(
            url=f"/cdim/api/v1/devices/{target_device_id}/power",
            json={"action": action},
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

    @pytest.mark.parametrize(
        "action, controller_method",
        [
            (control_api.PowerControlAction.ON.value, "power_on"),
            (control_api.PowerControlAction.OFF.value, "power_off"),
            (control_api.PowerControlAction.FORCE_OFF.value, "force_off"),
            (control_api.PowerControlAction.RESET.value, "reset"),
        ],
    )
    def test_controller_raise(
        self, mocker: MockFixture, action, controller_method, default_power_control_target_device_fixture
    ):
        """test controller raise Exception.

        Args:
            mocker (MockFixture):
                Provide mock objects for classes and methods that the function under test depends on.

            action (str):
                action parameter input by caller.

        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCpuInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response = {
            "code": "EF003BAS010",
            "message": "Your request is not supported for the specified target device.",
        }

        # Set up the mock.
        mocker.patch.object(
            control_base.PowerControlTargetDevice,
            "model_post_init",
            return_value=default_power_control_target_device_fixture,
        )
        mocker.patch.object(
            oob_control.OobController, controller_method, side_effect=exc.RequestNotSupportedHwControlError
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.put(
            url=f"/cdim/api/v1/devices/{target_device_id}/power",
            json={"action": action},
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

    @pytest.mark.parametrize(
        "action, controller_method",
        [
            (control_api.PowerControlAction.ON.value, "power_on"),
            (control_api.PowerControlAction.OFF.value, "power_off"),
            (control_api.PowerControlAction.FORCE_OFF.value, "force_off"),
            (control_api.PowerControlAction.RESET.value, "reset"),
        ],
    )
    def test_device_busy(
        self, mocker: MockFixture, action, controller_method, default_power_control_target_device_fixture
    ):
        """Test target device busy case."""
        target_device_id = test_util.DummyCpuInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.SERVICE_UNAVAILABLE.value
        expected_response = {
            "code": "ER005BAS002",
            "message": f"The specified device is busy. The following Device ID is relevant: {target_device_id}",
        }

        # Set up the mock.
        mocker.patch.object(
            control_base.PowerControlTargetDevice,
            "model_post_init",
            return_value=default_power_control_target_device_fixture,
        )
        mocker.patch.object(oob_control.OobController, controller_method, return_value=None)

        mocker.patch.object(
            control_base.PowerControlTargetDevice,
            "get_lock",
            side_effect=exc.DeviceBusyHwControlError(
                additional_message=f"The following Device ID is relevant: {target_device_id}"
            ),
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.put(
            url=f"/cdim/api/v1/devices/{target_device_id}/power",
            json={"action": action},
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response


class TestIsOSReadyAPI:
    """Unit test class for is_os_ready_api."""

    @pytest.mark.parametrize("os_state", [True, False])
    def test_success_default_timeout(
        self,
        mocker: MockFixture,
        default_power_control_target_device_fixture,
        default_control_target_agent_fixture,
        os_state,
    ):
        """test success case default timeout value.

        Args:
            mocker (MockFixture):
                Provide mock objects for classes and methods that the function under test depends on.

            os_state (bool):
                target host-os state.

        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCpuInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.OK.value
        expected_response = {"status": os_state, "IPAddress": test_util.DummyCpuInfo.IP_ADDRESS.value}

        mocker.patch.object(agent_control.AgentController, "is_os_ready", return_value=os_state)

        mocker.patch(
            "app.core.control.control_base.PowerControlTargetDevice",
            return_value=default_power_control_target_device_fixture,
        )

        mocker.patch(
            "app.core.control.agent_control.ControlTargetAgent",
            return_value=default_control_target_agent_fixture,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.get(
            url=f"/cdim/api/v1/cpu/{target_device_id}/is-os-ready",
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

    @pytest.mark.parametrize("os_state", [True, False])
    @pytest.mark.parametrize("timeout", [control_api.MIN_IS_OS_READY_TIMEOUT, control_api.MAX_IS_OS_READY_TIMEOUT])
    def test_success_within_range_of_timeout(
        self,
        caplog,
        mocker: MockFixture,
        os_state,
        timeout,
        default_power_control_target_device_fixture,
        default_control_target_agent_fixture,
    ):
        """test success case valid range timeout.

        Args:
            mocker (MockFixture):
                Provide mock objects for classes and methods that the function under test depends on.

            os_state (bool):
                os-state of host-os.

            timeout (int):
                timeout value set by caller.

        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCpuInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.OK.value
        expected_response = {"status": os_state, "IPAddress": test_util.DummyCpuInfo.IP_ADDRESS.value}

        mocker.patch.object(uuid, "uuid4", return_value=CONSTANT_REQUEST_ID)
        mocker.patch.object(agent_control.AgentController, "is_os_ready", return_value=os_state)

        mocker.patch(
            "app.core.control.control_base.PowerControlTargetDevice",
            return_value=default_power_control_target_device_fixture,
        )

        mocker.patch(
            "app.core.control.agent_control.ControlTargetAgent",
            return_value=default_control_target_agent_fixture,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="LOGGER"):
            response = client.get(url=f"/cdim/api/v1/cpu/{target_device_id}/is-os-ready", params={"timeOut": timeout})

        # HttpRequestLog
        request_log_message = json.loads(caplog.records[0].getMessage())

        # HttpResponseLog
        response_log_message = json.loads(caplog.records[-1].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

        # check HttpRequestLog
        assert caplog.records[0].levelname == "INFO"
        assert request_log_message["message"]["request_id"] == CONSTANT_REQUEST_ID
        assert request_log_message["message"]["action"] == "receive http request"
        assert (
            request_log_message["message"]["url"]
            == f"http://testserver/cdim/api/v1/cpu/{target_device_id}/is-os-ready?timeOut={timeout}"
        )
        assert request_log_message["message"]["client_ip_address"] == "testclient"
        assert request_log_message["message"]["client_port"] == 50000
        assert request_log_message["message"]["path_parameter"] == {"CPUDeviceID": target_device_id}
        assert request_log_message["message"]["query_parameter"] == {"timeOut": str(timeout)}
        assert request_log_message["message"]["body_parameter"] is None

        assert caplog.records[-1].levelname == "INFO"
        assert response_log_message["message"]["request_id"] == CONSTANT_REQUEST_ID
        assert response_log_message["message"]["action"] == "return http response"
        assert response_log_message["message"]["status_code"] == HTTPStatus.OK.value
        assert response_log_message["message"]["response_body"] == {
            "status": os_state,
            "IPAddress": test_util.DummyCpuInfo.IP_ADDRESS.value,
        }

    @pytest.mark.parametrize(
        "path_parameter, query_parameter",
        [
            ("Foo", control_api.DEFAULT_IS_OS_READY_TIMEOUT),  # path_parameter invalid
            # query_parameters exceed the limit
            (test_util.DummyCpuInfo.DEVICE_ID.value, control_api.MAX_IS_OS_READY_TIMEOUT + 1),
            # query_parameter are below the lower limit
            (test_util.DummyCpuInfo.DEVICE_ID.value, control_api.MIN_IS_OS_READY_TIMEOUT - 1),
            # query_parameter invalid type
            (test_util.DummyCpuInfo.DEVICE_ID.value, "thirty"),
        ],
    )
    def test_invalid_request_parameter(self, path_parameter, query_parameter):
        """test invalid request parameter case.

        Args:
            mocker (MockFixture): The fixture used to mock objects.

            path_parameter:
                The input path parameter to be tested.

            query_parameter:
                The input query parameters to be tested.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_error_code = "EF003BAS012"

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.get(url=f"/cdim/api/v1/cpu/{path_parameter}/is-os-ready", params={"timeOut": query_parameter})

        actual_status_code = response.status_code
        actual_error_code = response.json().get("code")

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_status_code == expected_http_status
        assert actual_error_code == expected_error_code

    @pytest.mark.parametrize(
        "http_method",
        [
            "PUT",
            "DELETE",
            "POST",
            "PATCH",
        ],
    )
    def test_method_not_allow(self, http_method):
        """test requested method not allow case.

        Args:
            http_method (str):
                The input HTTP method to be tested.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCpuInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response_body = {
            "code": "EF003BAS011",
            "message": "Method Not Allowed",
        }

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.request(
            method=http_method,
            url=f"/cdim/api/v1/cpu/{target_device_id}/is-os-ready",
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response_body

    @pytest.mark.parametrize("timeout", [control_api.MIN_IS_OS_READY_TIMEOUT, control_api.MAX_IS_OS_READY_TIMEOUT])
    def test_device_raise(self, mocker: MockFixture, timeout):
        """test device raise exception case.

        Args:
            caplog
                log capture fixture.

            mocker (MockFixture):
                Provide mock objects for classes and methods that the function under test depends on.

            timeout (int):
                timeout value set by caller.

        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCpuInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response = {
            "code": "EF003BAS010",
            "message": "Your request is not supported for the specified target device.",
        }

        mocker.patch.object(
            control_base.PowerControlTargetDevice,
            "model_post_init",
            side_effect=exc.RequestNotSupportedHwControlError,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.get(url=f"/cdim/api/v1/cpu/{target_device_id}/is-os-ready", params={"timeOut": timeout})

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

    @pytest.mark.parametrize("timeout", [control_api.MIN_IS_OS_READY_TIMEOUT, control_api.MAX_IS_OS_READY_TIMEOUT])
    def test_agent_raise(
        self,
        mocker: MockFixture,
        timeout,
        default_power_control_target_device_fixture,
    ):
        """test device raise exception case.

        Args:
            caplog
                log capture fixture.

            mocker (MockFixture):
                Provide mock objects for classes and methods that the function under test depends on.

            timeout (int):
                timeout value set by caller.

        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCpuInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response = {
            "code": "EF003BAS010",
            "message": "Your request is not supported for the specified target device.",
        }
        mocker.patch(
            "app.core.control.control_base.PowerControlTargetDevice",
            return_value=default_power_control_target_device_fixture,
        )
        mocker.patch.object(
            agent_control.ControlTargetAgent,
            "model_post_init",
            side_effect=exc.RequestNotSupportedHwControlError,
        )
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.get(url=f"/cdim/api/v1/cpu/{target_device_id}/is-os-ready", params={"timeOut": timeout})

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

    @pytest.mark.parametrize("timeout", [control_api.MIN_IS_OS_READY_TIMEOUT, control_api.MAX_IS_OS_READY_TIMEOUT])
    def test_controller_raise(
        self,
        mocker: MockFixture,
        timeout,
        default_power_control_target_device_fixture,
        default_control_target_agent_fixture,
    ):
        """test controller raise exception case.

        Args:
            caplog
                log capture fixture.

            mocker (MockFixture):
                Provide mock objects for classes and methods that the function under test depends on.

            timeout (int):
                timeout value set by caller.

        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCpuInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response = {
            "code": "EF003BAS010",
            "message": "Your request is not supported for the specified target device.",
        }

        mocker.patch.object(
            agent_control.AgentController, "is_os_ready", side_effect=exc.RequestNotSupportedHwControlError
        )

        mocker.patch(
            "app.core.control.control_base.PowerControlTargetDevice",
            return_value=default_power_control_target_device_fixture,
        )

        mocker.patch(
            "app.core.control.agent_control.ControlTargetAgent",
            return_value=default_control_target_agent_fixture,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.get(url=f"/cdim/api/v1/cpu/{target_device_id}/is-os-ready", params={"timeOut": timeout})

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

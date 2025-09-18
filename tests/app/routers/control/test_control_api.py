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

"""Unit test module for control_api module ."""

from http import HTTPStatus
import logging

import pytest
from pytest import LogCaptureFixture
from pytest_mock import MockFixture
from fastapi.testclient import TestClient

from tests import test_util

import app.common.basic_exceptions as exc
from app.core.control import fm_control
from app.core.control import oob_control
from app.core.control import agent_control
from app.core.control import control_base
from app.hw_control_main import app

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.routers.control import control_api

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

DUMMY_UPSTREAM_DEVICE_ID = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"
DUMMY_DOWNSTREAM_DEVICE_ID = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"

client = TestClient(app, raise_server_exceptions=False)


class TestAggregationControlAPI:
    """Unit test class for aggregation_control_api."""

    @pytest.mark.parametrize(
        "action, controller_method",
        [
            (control_api.AggregationControlAction.CONNECT.value, "connect"),
            (control_api.AggregationControlAction.DISCONNECT.value, "disconnect"),
        ],
    )
    def test_success(self, caplog: LogCaptureFixture, mocker: MockFixture, action: str, controller_method: str):
        """
        Test the successful case for aggregation control API.

        Args:
            caplog (LogCaptureFixture):
                Pytest fixture for capturing log records.
            mocker (MockFixture):
                Pytest fixture for mocking objects and functions.
            action (str):
                Aggregation action parameter.
            controller_method (str):
                The FMController method name to be called ("connect" or "disconnect").
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        host_cpu_id = test_util.DummyCPUInfo.DEVICE_ID.value
        target_device_id = test_util.DummyDeviceInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.OK.value
        expected_response = {"CPUDeviceID": host_cpu_id, "deviceID": target_device_id}

        # Set up the mock.
        mocker.patch.object(
            fm_control.FMControlTargetDevice,
            "model_post_init",
            return_value=None,
        )
        mocker.patch.object(fm_control.FMController, controller_method, return_value=None)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=control_api.__name__):
            response = client.put(
                url=f"/cdim/api/v1/cpu/{host_cpu_id}/aggregations",
                json={"deviceID": target_device_id, "action": action},
            )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

        # Inspection: Check the request parameter log
        request_parameter_log = caplog.records[1]
        assert request_parameter_log.levelname == "INFO"
        assert request_parameter_log.getMessage() == "Aggregation Control start."

        assert hasattr(request_parameter_log, "CPUDeviceID"), "cpu_device_id should be present in the log record"
        assert getattr(request_parameter_log, "CPUDeviceID") == host_cpu_id

        assert hasattr(request_parameter_log, "deviceID"), "deviceID should be present in the log record"
        assert getattr(request_parameter_log, "deviceID") == target_device_id

        assert hasattr(request_parameter_log, "action"), "action should be present in the log record"
        assert getattr(request_parameter_log, "action") == action

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
    def test_method_not_allow(self, action: str, http_method: str):
        """
        Test that unsupported HTTP methods return METHOD_NOT_ALLOWED.

        Args:
            action (str):
                Aggregation action parameter to be tested.
            http_method (str):
                HTTP method to be tested.
        """

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        host_cpu_id = test_util.DummyCPUInfo.DEVICE_ID.value
        target_device_id = test_util.DummyDeviceInfo.DEVICE_ID.value

        url = f"/cdim/api/v1/cpu/{host_cpu_id}/aggregations"
        request_body = {"deviceID": target_device_id, "action": action}

        expected_http_status = HTTPStatus.METHOD_NOT_ALLOWED.value
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
                test_util.DummyCPUInfo.DEVICE_ID.value,
                {
                    "deviceID": "Foo",
                    "action": control_api.AggregationControlAction.CONNECT.value,
                },
            ),
            (  # body_parameter deviceID unset
                test_util.DummyCPUInfo.DEVICE_ID.value,
                {
                    "action": control_api.AggregationControlAction.CONNECT.value,
                },
            ),
            (  # body_parameter action invalid
                test_util.DummyCPUInfo.DEVICE_ID.value,
                {
                    "deviceID": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "action": "Foo",
                },
            ),
            (  # body_parameter action unset
                test_util.DummyCPUInfo.DEVICE_ID.value,
                {
                    "deviceID": test_util.DummyDeviceInfo.DEVICE_ID.value,
                },
            ),
        ],
    )
    def test_invalid_request_parameter(self, path_parameter, body_parameter):
        """
        Test invalid request parameter cases for aggregation control API.

        Args:
            path_parameter:
                The input path parameter to be tested.
            body_parameter (str):
                The input body parameters to be tested.
        """

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        expected_http_status = 422
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
        """
        Test case where device object cannot be created.

        Args:
            mocker (MockFixture):
                Pytest fixture for mocking objects and functions.
            action (str):
                Aggregation action parameter to be tested.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++++++++++#
        host_cpu_id = test_util.DummyCPUInfo.DEVICE_ID.value
        target_device_id = test_util.DummyDeviceInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response = {
            "code": "EF003BAS010",
            "message": "Your request is not supported for the specified target device.",
        }

        # Set up the mock.
        mocker.patch.object(
            fm_control.FMControlTargetDevice, "model_post_init", side_effect=exc.RequestNotSupportedHWControlError
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
        """
        Test case where device pair object cannot be created.

        Args:
            mocker (MockFixture):
                Pytest fixture for mocking objects and functions.
            action (str):
                Aggregation action parameter to be tested.
        """
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
        mocker.patch.object(fm_control.FMControlTargetDevice, "model_post_init", return_value=None)

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
    def test_device_pair_busy(self, mocker: MockFixture, action: str):
        """
        Test case where the device pair is busy.

        Args:
            mocker (MockFixture):
                Pytest fixture for mocking objects and functions.
            action (str):
                Aggregation action parameter to be tested.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        host_cpu_id = test_util.DummyCPUInfo.DEVICE_ID.value
        target_device_id = test_util.DummyDeviceInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.SERVICE_UNAVAILABLE.value
        expected_response = {
            "code": "ER005BAS002",
            "message": f"The specified device is busy. The following Device ID is relevant: {target_device_id}",
        }

        # Set up the mock.
        mocker.patch.object(fm_control.FMControlTargetDevice, "model_post_init", return_value=None)
        mocker.patch.object(
            fm_control.FMControlTargetDevicePair,
            "get_lock",
            side_effect=exc.DeviceBusyHWControlError(
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
    def test_controller_raise(self, mocker: MockFixture, action: str, controller_method: str):
        """
        Test case where FMController raises an exception.

        Args:
            mocker (MockFixture):
                Pytest fixture for mocking objects and functions.
            action (str):
                Aggregation action parameter to be tested.
            controller_method (str):
                The FMController method name to be called ("connect" or "disconnect").
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        host_cpu_id = test_util.DummyCPUInfo.DEVICE_ID.value
        target_device_id = test_util.DummyDeviceInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response = {
            "code": "EF003BAS010",
            "message": "Your request is not supported for the specified target device.",
        }

        # Set up the mock.
        mocker.patch.object(
            fm_control.FMControlTargetDevice,
            "model_post_init",
            return_value=None,
        )

        mocker.patch.object(
            fm_control.FMController, controller_method, side_effect=exc.RequestNotSupportedHWControlError
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

    def test_power_off_via_oob_success(
        self, mocker: MockFixture, default_power_control_target_device_fixture: control_base.PowerControlTargetDevice
    ):
        """
        Test successful power off via OOB (Out-of-Band).

        Args:
            mocker (MockFixture): Pytest-mock fixture for mocking objects and functions.
            default_power_control_target_device_fixture (PowerControlTargetDevice):
                Target device object to control power.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock.
        mocker.patch.object(
            oob_control.OOBController,
            "power_off",
            return_value=None,
        )

        mocker.patch.object(
            agent_control.ControlTargetAgent,
            "model_post_init",
            side_effect=exc.RequestNotSupportedHWControlError,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        control_api._perform_power_off(  # pylint: disable=W0212
            target_device=default_power_control_target_device_fixture,
        )

    def test_power_off_via_oob_error(
        self,
        mocker: MockFixture,
        default_power_control_target_device_fixture: control_base.PowerControlTargetDevice,
    ):
        """
        Test power off via OOB (Out-of-Band) with error (exception raised).

        Args:
            mocker (MockFixture): Pytest-mock fixture for mocking objects and functions.
            default_power_control_target_device_fixture (PowerControlTargetDevice):
                Target device object to control power.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock.
        mocker.patch.object(oob_control.OOBController, "power_off", side_effect=exc.PowerOffFailureHWControlError)

        mocker.patch.object(
            agent_control.ControlTargetAgent,
            "model_post_init",
            side_effect=exc.RequestNotSupportedHWControlError,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.PowerOffFailureHWControlError):
            control_api._perform_power_off(  # pylint: disable=W0212
                target_device=default_power_control_target_device_fixture
            )

    def test_shutdown_via_agent_success(
        self,
        mocker: MockFixture,
        default_power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        default_control_target_agent_fixture: agent_control.ControlTargetAgent,
    ):
        """
        Test successful shutdown via Agent.

        Args:
            mocker (MockFixture): Pytest-mock fixture for mocking objects and functions.
            default_power_control_target_device_fixture (PowerControlTargetDevice):
                Target device object to control power.
            default_control_target_agent_fixture (ControlTargetAgent):
                Target agent object to control.
        """
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
        default_power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        default_control_target_agent_fixture: agent_control.ControlTargetAgent,
    ):
        """
        Test shutdown via Agent with error (exception raised).

        Args:
            mocker (MockFixture): Pytest-mock fixture for mocking objects and functions.
            default_power_control_target_device_fixture (PowerControlTargetDevice):
                Target device object to control power.
            default_control_target_agent_fixture (ControlTargetAgent):
                Target agent object to control.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock.
        mocker.patch.object(
            agent_control.AgentController,
            "os_shutdown",
            side_effect=exc.RequestNotSupportedHWControlError,
        )

        mocker.patch(
            "app.core.control.agent_control.ControlTargetAgent",
            return_value=default_control_target_agent_fixture,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            control_api._perform_power_off(  # pylint: disable=W0212
                target_device=default_power_control_target_device_fixture
            )


class TestPowerControlAPI:
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
    def test_success(  # pylint: disable=R0913, R0917
        self,
        caplog: LogCaptureFixture,
        mocker: MockFixture,
        action: str,
        controller_method: str,
        default_power_control_target_device_fixture: control_base.PowerControlTargetDevice,
    ):
        """
        Test successful power control API request.

        Args:
            caplog (LogCaptureFixture): Pytest fixture for capturing log records.
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
            action (str): Power control action parameter (ON/OFF/FORCE_OFF/RESET).
            controller_method (str): OOBController method name to be called ("power_on", "power_off", etc).
            default_power_control_target_device_fixture (PowerControlTargetDevice):
                Target device object to control power.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.OK.value
        expected_response = {"deviceID": target_device_id}

        # Set up the mock.
        mocker.patch.object(oob_control.OOBController, controller_method, return_value=None)

        mocker.patch.object(
            control_base.PowerControlTargetDevice,
            "model_post_init",
            return_value=default_power_control_target_device_fixture,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=control_api.__name__):
            response = client.put(
                url=f"/cdim/api/v1/devices/{target_device_id}/power",
                json={"action": action},
            )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

        # Inspection: Check the request parameter log
        request_parameter_log = caplog.records[1]
        assert request_parameter_log.levelname == "INFO"
        assert request_parameter_log.getMessage() == "Power Control start."

        assert hasattr(request_parameter_log, "deviceID"), "deviceID should be present in the log record"
        assert getattr(request_parameter_log, "deviceID") == target_device_id

        assert hasattr(request_parameter_log, "action"), "action should be present in the log record"
        assert getattr(request_parameter_log, "action") == action

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
    def test_method_not_allow(self, action: str, http_method: str):
        """
        Test that unsupported HTTP methods return METHOD_NOT_ALLOWED for power control API.

        Args:
            action (str): Power control action parameter to be tested.
            http_method (str): HTTP method to be tested (GET/DELETE/POST/PATCH).
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        url = f"/cdim/api/v1/devices/{target_device_id}/power"
        request_body = {"action": action}

        expected_http_status = HTTPStatus.METHOD_NOT_ALLOWED.value
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
                test_util.DummyCPUInfo.DEVICE_ID.value,
                {
                    "action": "Foo",
                },
            ),
            (  # body_parameter action unset
                test_util.DummyCPUInfo.DEVICE_ID.value,
                {},
            ),
        ],
    )
    def test_invalid_request_parameter(self, path_parameter, body_parameter):
        """
        Test invalid request parameter cases for power control API.

        Args:
            path_parameter: Path parameter to be tested.
            body_parameter: Body parameters to be tested.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        expected_http_status = 422
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
    def test_device_raise(self, mocker: MockFixture, action: str):
        """
        Test case where device object creation raises an exception.

        Args:
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
            action (str): Power control action parameter to be tested.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response = {
            "code": "EF003BAS010",
            "message": "Your request is not supported for the specified target device.",
        }

        # Set up the mock.
        mocker.patch.object(
            control_base.PowerControlTargetDevice,
            "model_post_init",
            side_effect=exc.RequestNotSupportedHWControlError,
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
        self,
        mocker: MockFixture,
        action: str,
        controller_method: str,
        default_power_control_target_device_fixture: control_base.PowerControlTargetDevice,
    ):
        """
        Test case where OOBController method raises an exception.

        Args:
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
            action (str): Power control action parameter to be tested.
            controller_method (str): OOBController method name to be called.
            default_power_control_target_device_fixture (PowerControlTargetDevice):
                Target device object to control power.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

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
            oob_control.OOBController, controller_method, side_effect=exc.RequestNotSupportedHWControlError
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
        self,
        mocker: MockFixture,
        action: str,
        controller_method: str,
        default_power_control_target_device_fixture: control_base.PowerControlTargetDevice,
    ):
        """
        Test case where the target device is busy and cannot be controlled.

        Args:
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
            action (str): Power control action parameter to be tested.
            controller_method (str): OOBController method name to be called.
            default_power_control_target_device_fixture (PowerControlTargetDevice):
                Target device object to control power.
        """
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

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
        mocker.patch.object(oob_control.OOBController, controller_method, return_value=None)

        mocker.patch.object(
            control_base.PowerControlTargetDevice,
            "get_lock",
            side_effect=exc.DeviceBusyHWControlError(
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
        default_power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        default_control_target_agent_fixture: agent_control.ControlTargetAgent,
        os_state: bool,
    ):
        """
        Test successful is_os_ready API request with default timeout value.

        Args:
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
            default_power_control_target_device_fixture (PowerControlTargetDevice): The target device object.
            default_control_target_agent_fixture (ControlTargetAgent): The target agent object.
            os_state (bool): OS state (True/False) for test case.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.OK.value
        expected_response = {"status": os_state, "IPAddress": test_util.DummyCPUInfo.IP_ADDRESS.value}

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
    def test_success_within_range_of_timeout(  # pylint: disable=R0913, R0917
        self,
        caplog: LogCaptureFixture,
        mocker: MockFixture,
        os_state: bool,
        timeout: int,
        default_power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        default_control_target_agent_fixture: agent_control.ControlTargetAgent,
    ):
        """
        Test successful is_os_ready API request with valid timeout value.

        Args:
            caplog (LogCaptureFixture): Pytest fixture for capturing log records.
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
            os_state (bool): OS state (True/False) for test case.
            timeout (int): Timeout value to be tested.
            default_power_control_target_device_fixture (PowerControlTargetDevice): The target device object.
            default_control_target_agent_fixture (ControlTargetAgent): The target agent object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.OK.value
        expected_response = {"status": os_state, "IPAddress": test_util.DummyCPUInfo.IP_ADDRESS.value}

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
        with caplog.at_level(logging.INFO, logger=control_api.__name__):
            response = client.get(url=f"/cdim/api/v1/cpu/{target_device_id}/is-os-ready", params={"timeOut": timeout})

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

        # Inspection: Check the request parameter log
        request_parameter_log = caplog.records[1]
        assert request_parameter_log.levelname == "INFO"
        assert request_parameter_log.getMessage() == "Is OS Ready start."

        assert hasattr(request_parameter_log, "CPUDeviceID"), "CPUDeviceID should be present in the log record"
        assert getattr(request_parameter_log, "CPUDeviceID") == target_device_id

        assert hasattr(request_parameter_log, "timeOut"), "timeOut should be present in the log record"
        assert getattr(request_parameter_log, "timeOut") == timeout

    @pytest.mark.parametrize(
        "path_parameter, query_parameter",
        [
            ("Foo", control_api.DEFAULT_IS_OS_READY_TIMEOUT),  # path_parameter invalid
            # query_parameters exceed the limit
            (test_util.DummyCPUInfo.DEVICE_ID.value, control_api.MAX_IS_OS_READY_TIMEOUT + 1),
            # query_parameter are below the lower limit
            (test_util.DummyCPUInfo.DEVICE_ID.value, control_api.MIN_IS_OS_READY_TIMEOUT - 1),
            # query_parameter invalid type
            (test_util.DummyCPUInfo.DEVICE_ID.value, "thirty"),
        ],
    )
    def test_invalid_request_parameter(self, path_parameter, query_parameter):
        """
        Test invalid request parameter cases for is_os_ready API.

        Args:
            path_parameter:
                The input path parameter to be tested.

            query_parameter:
                The input query parameters to be tested.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        expected_http_status = 422
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
    def test_method_not_allow(self, http_method: str):
        """
        Test that unsupported HTTP methods return METHOD_NOT_ALLOWED for is_os_ready API.

        Args:
            http_method (str): HTTP method to be tested (PUT/DELETE/POST/PATCH).
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.METHOD_NOT_ALLOWED.value
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
    def test_device_raise(self, mocker: MockFixture, timeout: int):
        """
        Test case where device object creation raises an exception for is_os_ready API.

        Args:
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
            timeout (int): Timeout value to be tested.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response = {
            "code": "EF003BAS010",
            "message": "Your request is not supported for the specified target device.",
        }

        mocker.patch.object(
            control_base.PowerControlTargetDevice,
            "model_post_init",
            side_effect=exc.RequestNotSupportedHWControlError,
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
        timeout: int,
        default_power_control_target_device_fixture: control_base.PowerControlTargetDevice,
    ):
        """
        Test case where agent object creation raises an exception for is_os_ready API.

        Args:
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
            timeout (int): Timeout value to be tested.
            default_power_control_target_device_fixture (PowerControlTargetDevice): The target device object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

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
            side_effect=exc.RequestNotSupportedHWControlError,
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
        timeout: int,
        default_power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        default_control_target_agent_fixture: agent_control.ControlTargetAgent,
    ):
        """
        Test case where AgentController raises an exception for is_os_ready API.

        Args:
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
            timeout (int): Timeout value to be tested.
            default_power_control_target_device_fixture (PowerControlTargetDevice): The target device object.
            default_control_target_agent_fixture (ControlTargetAgent): The target agent object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response = {
            "code": "EF003BAS010",
            "message": "Your request is not supported for the specified target device.",
        }

        mocker.patch.object(
            agent_control.AgentController, "is_os_ready", side_effect=exc.RequestNotSupportedHWControlError
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


class TestDeviceAggregationControlAPI:
    """Unit test class for device_aggregation_control_api."""

    @pytest.mark.parametrize(
        "action, controller_method",
        [
            (control_api.AggregationControlAction.CONNECT.value, "connect"),
            (control_api.AggregationControlAction.DISCONNECT.value, "disconnect"),
        ],
    )
    def test_success_default_timeout(
        self, caplog: LogCaptureFixture, mocker: MockFixture, action: str, controller_method: str
    ):
        """
        Test the successful case for device aggregation control endpoint.

        Args:
            caplog (LogCaptureFixture):
                Pytest fixture for capturing log records.
            mocker (MockFixture):
                Pytest fixture for mocking objects and functions.
            action (str):
                Aggregation action parameter.
            controller_method (str):
                The FMController method name to be called ("connect" or "disconnect").

        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        upstream_device_id = DUMMY_UPSTREAM_DEVICE_ID
        downstream_device_id = DUMMY_DOWNSTREAM_DEVICE_ID

        expected_http_status = HTTPStatus.OK.value
        expected_response = {"sourceDeviceID": upstream_device_id, "destinationDeviceID": downstream_device_id}

        # Set up the mock.
        mocker.patch.object(
            fm_control.FMControlTargetDevice,
            "model_post_init",
            return_value=None,
        )
        mocker.patch.object(fm_control.FMController, controller_method, return_value=None)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=control_api.__name__):
            response = client.put(
                url=f"/cdim/api/v1/devices/{upstream_device_id}/aggregations",
                json={"destinationDeviceID": downstream_device_id, "action": action},
            )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

        # Inspection: Check the request parameter log
        request_parameter_log = caplog.records[1]
        assert request_parameter_log.levelname == "INFO"
        assert request_parameter_log.getMessage() == "Device Aggregation Control start."

        assert hasattr(request_parameter_log, "sourceDeviceID"), "sourceDeviceID should be present in the log record"
        assert getattr(request_parameter_log, "sourceDeviceID") == upstream_device_id

        assert hasattr(
            request_parameter_log, "destinationDeviceID"
        ), "destinationDeviceID should be present in the log record"
        assert getattr(request_parameter_log, "destinationDeviceID") == downstream_device_id

        assert hasattr(request_parameter_log, "action"), "action should be present in the log record"
        assert getattr(request_parameter_log, "action") == action

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
    def test_method_not_allow(self, action: str, http_method: str):
        """
        Test that unsupported HTTP methods return METHOD_NOT_ALLOWED.

        Args:
            action (str):
                Aggregation action parameter to be tested.
            http_method (str):
                HTTP method to be tested.
        """

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        upstream_device_id = DUMMY_UPSTREAM_DEVICE_ID
        downstream_device_id = DUMMY_DOWNSTREAM_DEVICE_ID

        expected_http_status = HTTPStatus.METHOD_NOT_ALLOWED.value
        expected_response_body = {
            "code": "EF003BAS011",
            "message": "Method Not Allowed",
        }

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.request(
            method=http_method,
            url=f"/cdim/api/v1/devices/{upstream_device_id}/aggregations",
            json={"destinationDeviceID": downstream_device_id, "action": action},
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response_body

    @pytest.mark.parametrize(
        "path_parameter, body_parameter",
        [
            (  # path_parameter invalid (not UUID4)
                "Foo",
                {
                    "destinationDeviceID": DUMMY_DOWNSTREAM_DEVICE_ID,
                    "action": control_api.AggregationControlAction.CONNECT.value,
                },
            ),
            (  # body_parameter destinationDeviceID invalid
                DUMMY_UPSTREAM_DEVICE_ID,
                {
                    "destinationDeviceID": "Foo",
                    "action": control_api.AggregationControlAction.CONNECT.value,
                },
            ),
            (  # body_parameter destinationDeviceID unset
                DUMMY_UPSTREAM_DEVICE_ID,
                {
                    "action": control_api.AggregationControlAction.CONNECT.value,
                },
            ),
            (  # body_parameter action invalid
                DUMMY_UPSTREAM_DEVICE_ID,
                {
                    "destinationDeviceID": DUMMY_DOWNSTREAM_DEVICE_ID,
                    "action": "Foo",
                },
            ),
            (  # body_parameter action unset
                DUMMY_UPSTREAM_DEVICE_ID,
                {
                    "destinationDeviceID": DUMMY_DOWNSTREAM_DEVICE_ID,
                },
            ),
        ],
    )
    def test_invalid_request_parameter(self, path_parameter, body_parameter):
        """
        Test invalid request parameter cases for device aggregation control API.

        Args:
            path_parameter:
                The input path parameter to be tested.
            body_parameter (str):
                The input body parameters to be tested.
        """

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        expected_http_status = 422
        expected_error_code = "EF003BAS012"

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.put(
            url=f"/cdim/api/v1/devices/{path_parameter}/aggregations",
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
        """
        Test case where device object cannot be created.

        Args:
            mocker (MockFixture):
                Pytest fixture for mocking objects and functions.
            action (str):
                Aggregation action parameter to be tested.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++++++++++#
        upstream_device_id = DUMMY_UPSTREAM_DEVICE_ID
        downstream_device_id = DUMMY_DOWNSTREAM_DEVICE_ID

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response = {
            "code": "EF003BAS010",
            "message": "Your request is not supported for the specified target device.",
        }

        # Set up the mock.
        mocker.patch.object(
            fm_control.FMControlTargetDevice, "model_post_init", side_effect=exc.RequestNotSupportedHWControlError
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.put(
            url=f"/cdim/api/v1/devices/{upstream_device_id}/aggregations",
            json={"destinationDeviceID": downstream_device_id, "action": action},
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

    @pytest.mark.parametrize(
        "action",
        [control_api.AggregationControlAction.CONNECT.value, control_api.AggregationControlAction.DISCONNECT.value],
    )
    def test_device_pair_can_not_create(self, mocker: MockFixture, action):
        """
        Test case where device pair object cannot be created.

        Args:
            mocker (MockFixture):
                Pytest fixture for mocking objects and functions.
            action (str):
                Aggregation action parameter to be tested.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++++++++++#
        # device_id of upstream_device_id and downstream_device_id are the same case.
        upstream_device_id = "ec020a7c-5014-4c2d-8682-45f69c936e3a"
        downstream_device_id = upstream_device_id

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response = {
            "code": "EF003BAS010",
            "message": "Your request is not supported for the specified target device.",
        }

        # Set up the mock.
        mocker.patch.object(fm_control.FMControlTargetDevice, "model_post_init", return_value=None)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.put(
            url=f"/cdim/api/v1/devices/{upstream_device_id}/aggregations",
            json={"destinationDeviceID": downstream_device_id, "action": action},
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

    @pytest.mark.parametrize(
        "action",
        [control_api.AggregationControlAction.CONNECT.value, control_api.AggregationControlAction.DISCONNECT.value],
    )
    def test_device_pair_busy(self, mocker: MockFixture, action: str):
        """
        Test case where the device pair is busy.

        Args:
            mocker (MockFixture):
                Pytest fixture for mocking objects and functions.
            action (str):
                Aggregation action parameter to be tested.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        upstream_device_id = DUMMY_UPSTREAM_DEVICE_ID
        downstream_device_id = DUMMY_DOWNSTREAM_DEVICE_ID

        expected_http_status = HTTPStatus.SERVICE_UNAVAILABLE.value
        expected_response = {
            "code": "ER005BAS002",
            "message": f"The specified device is busy. The following Device ID is relevant: {downstream_device_id}",
        }

        # Set up the mock.
        mocker.patch.object(fm_control.FMControlTargetDevice, "model_post_init", return_value=None)
        mocker.patch.object(
            fm_control.FMControlTargetDevicePair,
            "get_lock",
            side_effect=exc.DeviceBusyHWControlError(
                additional_message=f"The following Device ID is relevant: {downstream_device_id}"
            ),
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.put(
            url=f"/cdim/api/v1/devices/{upstream_device_id}/aggregations",
            json={"destinationDeviceID": downstream_device_id, "action": action},
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
    def test_controller_raise(self, mocker: MockFixture, action: str, controller_method: str):
        """
        Test case where FMController raises an exception.

        Args:
            mocker (MockFixture):
                Pytest fixture for mocking objects and functions.
            action (str):
                Aggregation action parameter to be tested.
            controller_method (str):
                The FMController method name to be called ("connect" or "disconnect").
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        upstream_device_id = DUMMY_UPSTREAM_DEVICE_ID
        downstream_device_id = DUMMY_DOWNSTREAM_DEVICE_ID

        expected_http_status = HTTPStatus.BAD_REQUEST.value
        expected_response = {
            "code": "EF003BAS010",
            "message": "Your request is not supported for the specified target device.",
        }

        # Set up the mock.
        mocker.patch.object(
            fm_control.FMControlTargetDevice,
            "model_post_init",
            return_value=None,
        )
        mocker.patch.object(
            fm_control.FMController, controller_method, side_effect=exc.RequestNotSupportedHWControlError
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = client.put(
            url=f"/cdim/api/v1/devices/{upstream_device_id}/aggregations",
            json={"destinationDeviceID": downstream_device_id, "action": action},
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == expected_http_status
        assert response.json() == expected_response

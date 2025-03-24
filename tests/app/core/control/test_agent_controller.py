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

"""Unit test module for AgentController class."""

import json
import logging
from http import HTTPStatus
from http import HTTPMethod

import pytest
import requests
from pytest_mock import MockFixture
from pytest import approx

from tests.app.core.control import test_util

from app.common import constants  # type: ignore
import app.common.basic_exceptions as exc  # type: ignore
from app.common.utils.authorization_utilities import authorization_server_client  # type: ignore
from app.core.control.control_base import PowerControlTargetDevice  # type: ignore
from app.core.control.agent_control import ControlTargetAgent  # type: ignore
from app.core.control.oob_control import OobController  # type: ignore
from app.routers.control import control_api  # type: ignore
from app.core.control import agent_control  # type: ignore

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.core.control.agent_control import AgentController  # type: ignore

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestOsShutdown:
    """Unit test class for AgentController.os_shutdown."""

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "power_control_target_device_fixture, control_target_agent_fixture",
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    def test_successful_case(
        self,
        caplog,
        mocker: MockFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
    ):
        """test successful case.

        Args:
            caplog
                log capture fixture

            mocker (MockFixture):
                Fixture for creating mock objects.

        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(PowerControlTargetDevice, "set_power_state", return_value=None)

        dummy_agent_response = test_util.generate_dummy_agent_response(status_code=HTTPStatus.OK.value)
        mocker.patch.object(requests, "put", return_value=dummy_agent_response)

        mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="LOGGER"):
            AgentController.os_shutdown(target_device=target_device, target_agent=target_agent)

        # AgentRequestLog
        agent_request_log_message = json.loads(caplog.records[0].getMessage())
        # AgentResponseLog
        agent_response_log_message = json.loads(caplog.records[-1].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 2

        assert caplog.records[0].levelname == "INFO"
        assert agent_request_log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert agent_request_log_message["message"]["ip_address"] == target_agent.ip_address
        assert agent_request_log_message["message"]["port"] == 8000
        assert (
            agent_request_log_message["message"]["url"]
            == f"http://{target_agent.ip_address}:8000/cdim/api/v1/agent/os-shutdown"
        )
        assert agent_request_log_message["message"]["http_method"] == HTTPMethod.PUT
        assert agent_request_log_message["message"]["time_out"] == approx(3.0)

        assert caplog.records[-1].levelname == "INFO"
        assert agent_response_log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert agent_response_log_message["message"]["status_code"] == HTTPStatus.OK.value
        assert agent_response_log_message["message"]["response_body"] is None

    @pytest.mark.parametrize(
        "power_control_target_device_fixture, control_target_agent_fixture, expected_exception",
        [
            (
                {  # input device object
                    "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyDeviceInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
                exc.RequestNotSupportedHwControlError,
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    def test_invalid_device_type(
        self,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        expected_exception,
    ):
        """test device raise raise exception."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            AgentController.os_shutdown(target_device=target_device, target_agent=target_agent)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture, control_target_agent_fixture",
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.PAUSED,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
            ),
            (
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.UNKNOWN,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    def test_invalid_power_state(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
    ):
        """test device raise raise exception."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(PowerControlTargetDevice, "set_power_state", return_value=None)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.InternalHwControlError):
            AgentController.os_shutdown(target_device=target_device, target_agent=target_agent)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture, control_target_agent_fixture",
        [
            (  # target device already power_off
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.OFF,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
            ),
            (  # target device powering off
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.POWERING_OFF,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    def test_already_power_off(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
    ):
        """Test target device power state already off or powering off case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        mocker.patch.object(PowerControlTargetDevice, "set_power_state", return_value=None)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        AgentController.os_shutdown(target_device=target_device, target_agent=target_agent)

    @pytest.mark.parametrize(
        "auth_client_raise_exception, expected_exception",
        [
            (exc.InternalHwControlError, exc.InternalHwControlError),
            (exc.ConfigurationHwControlError, exc.ConfigurationHwControlError),
        ],
    )
    @pytest.mark.parametrize(
        "control_target_agent_fixture",
        [
            {  # input agent object
                "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
            },
        ],
        indirect=["control_target_agent_fixture"],
    )
    def test_execute_os_shutdown_auth_client_raise(
        self,
        mocker: MockFixture,
        auth_client_raise_exception,
        expected_exception,
        control_target_agent_fixture: ControlTargetAgent,
    ):
        """
        Test authorization_server_client raise case.
        Note : Directly call and test the protected method
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(
            authorization_server_client, "get_agent_access_token", side_effect=auth_client_raise_exception
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            AgentController._execute_os_shutdown(target_agent=target_agent)  # pylint: disable=protected-access

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "auth_client_raise_exception",
        [
            exc.InternalHwControlError,
            exc.ConfigurationHwControlError,
        ],
    )
    @pytest.mark.parametrize(
        "power_control_target_device_fixture, control_target_agent_fixture",
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    def test_auth_client_raise(  # pylint: disable=too-many-arguments
        self,
        caplog,
        mocker: MockFixture,
        auth_client_raise_exception,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
    ):
        """Test authorization_server_client raise case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(PowerControlTargetDevice, "set_power_state", return_value=None)

        mocker.patch.object(
            authorization_server_client, "get_agent_access_token", side_effect=auth_client_raise_exception
        )

        mock_power_off = mocker.patch.object(OobController, "power_off")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.WARNING, logger="LOGGER"):
            AgentController.os_shutdown(target_device=target_device, target_agent=target_agent)

        # ExceptionLog
        log_message = json.loads(caplog.records[0].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        assert caplog.records[0].levelname == "WARNING"
        assert log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert log_message["message"]["detail"] == "Retry with ACPI shutdown"
        assert log_message["message"]["action"] == "exception raised"
        assert log_message["message"].get("trace_back") is not None
        mock_power_off.assert_called_once()

    @pytest.mark.parametrize(
        "control_target_agent_fixture",
        [
            {  # input agent object
                "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
            },
        ],
        indirect=["control_target_agent_fixture"],
    )
    @pytest.mark.parametrize(
        "requests_raise_exception",
        [
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError,
        ],
    )
    def test_execute_os_shutdown_requests_raise(
        self,
        mocker: MockFixture,
        requests_raise_exception,
        control_target_agent_fixture: ControlTargetAgent,
    ):
        """
        Test requests library raise exception case.
        Note : Directly call and test the protected method
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(requests, "put", side_effect=requests_raise_exception)

        mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.InternalHwControlError):
            AgentController._execute_os_shutdown(target_agent=target_agent)  # pylint: disable=protected-access

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "power_control_target_device_fixture, control_target_agent_fixture",
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    @pytest.mark.parametrize(
        "requests_raise_exception",
        [
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ConnectTimeout,
        ],
    )
    def test_requests_raise(  # pylint: disable=too-many-arguments
        self,
        caplog,
        mocker: MockFixture,
        requests_raise_exception,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
    ):
        """Test requests library raise exception case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(PowerControlTargetDevice, "set_power_state", return_value=None)
        mocker.patch.object(requests, "put", side_effect=requests_raise_exception)

        mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

        mock_power_off = mocker.patch.object(OobController, "power_off")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.WARNING, logger="LOGGER"):
            AgentController.os_shutdown(target_device=target_device, target_agent=target_agent)

        # ExceptionLog
        log_message = json.loads(caplog.records[0].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        assert caplog.records[0].levelname == "WARNING"
        assert log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert log_message["message"]["detail"] == "Retry with ACPI shutdown"
        assert log_message["message"]["action"] == "exception raised"
        assert log_message["message"].get("trace_back") is not None
        mock_power_off.assert_called_once()

    @pytest.mark.parametrize(
        "control_target_agent_fixture",
        [
            {  # input agent object
                "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
            },
        ],
        indirect=["control_target_agent_fixture"],
    )
    @pytest.mark.parametrize(
        "expected_exception, agent_return_status_code, agent_return_body",
        [
            (
                exc.AuthenticationHwControlError,
                401,
                {
                    "code": "EFA02BAS000",
                    "message": "Authentication failed. Failed to authenticate to the HW Control Agent.",
                },
            ),  # valid_access_token function handle case.
            (
                exc.ControlObjectHwControlError,
                500,
                {
                    "code": "CFA10BAS001",
                    "message": (
                        "Your request failed due to the missing required system configuration."
                        " There is an issue with the configuration of the environment variables"
                        " related to the access token verification."
                    ),
                },
            ),  # The cases of misconfiguration in the Agent settings.
        ],
    )
    def test_execute_os_shutdown_agent_return_error(  # pylint: disable=too-many-arguments
        self,
        mocker: MockFixture,
        expected_exception,
        agent_return_status_code,
        agent_return_body,
        control_target_agent_fixture: ControlTargetAgent,
    ):
        """
        Test Agent return case.
        Note : Directly call and test the protected method
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set the input value.
        target_agent = control_target_agent_fixture

        # Set up the mock.
        dummy_response = test_util.generate_dummy_agent_response(
            status_code=agent_return_status_code, content=agent_return_body
        )
        mocker.patch.object(requests, "put", return_value=dummy_response)

        mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            AgentController._execute_os_shutdown(target_agent=target_agent)  # pylint: disable=protected-access

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "power_control_target_device_fixture, control_target_agent_fixture",
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    @pytest.mark.parametrize(
        "agent_return_status_code",
        [
            401,  # valid_access_token function handle case.
            500,  # The cases of misconfiguration in the Agent settings.
        ],
    )
    def test_agent_return_error(  # pylint: disable=too-many-arguments
        self,
        caplog,
        mocker: MockFixture,
        agent_return_status_code,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
    ):
        """Test Agent return case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(PowerControlTargetDevice, "set_power_state", return_value=None)

        dummy_response = test_util.generate_dummy_agent_response(status_code=agent_return_status_code)
        mocker.patch.object(requests, "put", return_value=dummy_response)

        mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

        mock_power_off = mocker.patch.object(OobController, "power_off")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.WARNING, logger="LOGGER"):
            AgentController.os_shutdown(target_device=target_device, target_agent=target_agent)

        # ExceptionLog
        log_message = json.loads(caplog.records[0].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        assert caplog.records[0].levelname == "WARNING"
        assert log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert log_message["message"]["detail"] == "Retry with ACPI shutdown"
        assert log_message["message"]["action"] == "exception raised"
        assert log_message["message"].get("trace_back") is not None
        mock_power_off.assert_called_once()

    @pytest.mark.parametrize(
        "power_control_target_device_fixture, control_target_agent_fixture",
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.UNKNOWN,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    @pytest.mark.parametrize(
        "device_raise_exception",
        [
            exc.BaseHwControlError,
            exc.InternalHwControlError,
            exc.RequestNotSupportedHwControlError,
        ],
    )
    def test_device_raise(
        self,
        mocker: MockFixture,
        device_raise_exception,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
    ):
        """test device raise raise exception."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        mocker.patch.object(PowerControlTargetDevice, "set_power_state", side_effect=device_raise_exception)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(device_raise_exception):
            AgentController.os_shutdown(target_device=target_device, target_agent=target_agent)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture, control_target_agent_fixture",
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.UNKNOWN,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    def test_set_power_state_raise_value_error(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
    ):
        """test device raise raise exception."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        mocker.patch.object(PowerControlTargetDevice, "set_power_state", side_effect=ValueError)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHwControlError):
            AgentController.os_shutdown(target_device=target_device, target_agent=target_agent)


class TestIsOsReady:
    """Unit test class for AgentController.is_os_ready."""

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "power_control_target_device_fixture, control_target_agent_fixture, expected_os_state",
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
                True,
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    @pytest.mark.parametrize(
        "timeout",
        [
            control_api.MIN_IS_OS_READY_TIMEOUT,
            control_api.MAX_IS_OS_READY_TIMEOUT,
            agent_control.AGENT_REST_API_TIMEOUT,
        ],
    )
    def test_successful_case(  # pylint: disable=too-many-arguments
        self,
        caplog,
        mocker: MockFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        expected_os_state,
        timeout,
    ):
        """test successful case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(PowerControlTargetDevice, "set_power_state", return_value=None)

        dummy_agent_response = test_util.generate_dummy_agent_response(status_code=HTTPStatus.OK.value)
        mocker.patch.object(requests.Session, "get", return_value=dummy_agent_response)

        mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="LOGGER"):
            actual = AgentController.is_os_ready(
                target_device=target_device, target_agent=target_agent, timeout=timeout
            )

        # AgentRequestLog
        agent_request_log_message = json.loads(caplog.records[0].getMessage())

        # AgentResponseLog
        agent_response_log_message = json.loads(caplog.records[-1].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual == expected_os_state

        assert len(caplog.records) == 2

        assert caplog.records[0].levelname == "INFO"
        assert agent_request_log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert agent_request_log_message["message"]["ip_address"] == target_agent.ip_address
        assert agent_request_log_message["message"]["port"] == 8000
        assert (
            agent_request_log_message["message"]["url"]
            == f"http://{target_agent.ip_address}:8000/cdim/api/v1/agent/is-os-ready"
        )
        assert agent_request_log_message["message"]["http_method"] == HTTPMethod.GET
        assert agent_request_log_message["message"]["time_out"] == timeout

        assert caplog.records[-1].levelname == "INFO"
        assert agent_response_log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert agent_response_log_message["message"]["status_code"] == HTTPStatus.OK.value
        assert agent_response_log_message["message"]["response_body"] is None

    @pytest.mark.parametrize(
        "power_control_target_device_fixture, control_target_agent_fixture, expected_exception",
        [
            (
                {  # input device object
                    "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyDeviceInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
                exc.RequestNotSupportedHwControlError,
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    @pytest.mark.parametrize(
        "timeout",
        [
            control_api.MIN_IS_OS_READY_TIMEOUT,
            control_api.MAX_IS_OS_READY_TIMEOUT,
            agent_control.AGENT_REST_API_TIMEOUT,
        ],
    )
    def test_invalid_device_type(
        self,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        expected_exception,
        timeout,
    ):
        """test device raise raise exception."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            _ = AgentController.is_os_ready(target_device=target_device, target_agent=target_agent, timeout=timeout)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture, control_target_agent_fixture",
        [
            (  # target device already power_off
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.OFF,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
            ),
            (  # target device powering off
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.POWERING_OFF,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    @pytest.mark.parametrize(
        "timeout",
        [
            control_api.MIN_IS_OS_READY_TIMEOUT,
            control_api.MAX_IS_OS_READY_TIMEOUT,
            agent_control.AGENT_REST_API_TIMEOUT,
        ],
    )
    def test_device_power_state_invalid(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        timeout,
    ):
        """Test for plugin return invalid power state case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        mocker.patch.object(PowerControlTargetDevice, "set_power_state", return_value=None)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.HostCpuPowerOffBadRequestHwControlError):
            _ = AgentController.is_os_ready(target_device=target_device, target_agent=target_agent, timeout=timeout)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture, control_target_agent_fixture, expected_os_state",
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
                False,
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    @pytest.mark.parametrize(
        "timeout",
        [
            control_api.MIN_IS_OS_READY_TIMEOUT,
            control_api.MAX_IS_OS_READY_TIMEOUT,
            agent_control.AGENT_REST_API_TIMEOUT,
        ],
    )
    @pytest.mark.parametrize(
        "requests_raise_exception",
        [
            requests.exceptions.Timeout,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ProxyError,
            requests.exceptions.SSLError,
        ],
    )
    def test_request_timeout(  # pylint: disable=too-many-arguments
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        expected_os_state,
        timeout,
        requests_raise_exception,
    ):
        """test request timeout case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(PowerControlTargetDevice, "set_power_state", return_value=None)
        mocker.patch.object(requests.Session, "get", side_effect=requests_raise_exception)

        mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_os_state = AgentController.is_os_ready(
            target_device=target_device, target_agent=target_agent, timeout=timeout
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_os_state == expected_os_state

    @pytest.mark.parametrize(
        "power_control_target_device_fixture, control_target_agent_fixture",
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.PAUSED,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
            ),
            (
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.UNKNOWN,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    @pytest.mark.parametrize(
        "timeout",
        [
            control_api.MIN_IS_OS_READY_TIMEOUT,
            control_api.MAX_IS_OS_READY_TIMEOUT,
            agent_control.AGENT_REST_API_TIMEOUT,
        ],
    )
    def test_invalid_power_state(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        timeout,
    ):
        """Test request raise unexpected exception case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(PowerControlTargetDevice, "set_power_state", return_value=None)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.InternalHwControlError):
            _ = AgentController.is_os_ready(target_device=target_device, target_agent=target_agent, timeout=timeout)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture, control_target_agent_fixture",
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    @pytest.mark.parametrize(
        "timeout",
        [
            control_api.MIN_IS_OS_READY_TIMEOUT,
            control_api.MAX_IS_OS_READY_TIMEOUT,
            agent_control.AGENT_REST_API_TIMEOUT,
        ],
    )
    def test_set_power_state_raise_value_error(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        timeout,
    ):
        """Test request raise unexpected exception case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(PowerControlTargetDevice, "set_power_state", side_effect=ValueError)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHwControlError):
            _ = AgentController.is_os_ready(target_device=target_device, target_agent=target_agent, timeout=timeout)

    @pytest.mark.parametrize(
        "auth_client_raise_exception, expected_exception",
        [
            (exc.InternalHwControlError, exc.InternalHwControlError),
            (exc.ConfigurationHwControlError, exc.ConfigurationHwControlError),
        ],
    )
    @pytest.mark.parametrize(
        "power_control_target_device_fixture, control_target_agent_fixture",
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    @pytest.mark.parametrize(
        "timeout",
        [
            control_api.MIN_IS_OS_READY_TIMEOUT,
            control_api.MAX_IS_OS_READY_TIMEOUT,
            agent_control.AGENT_REST_API_TIMEOUT,
        ],
    )
    def test_auth_client_raise(  # pylint: disable=too-many-arguments
        self,
        mocker: MockFixture,
        auth_client_raise_exception,
        expected_exception,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        timeout,
    ):
        """Test authorization_server_client raise case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(PowerControlTargetDevice, "set_power_state", return_value=None)

        mocker.patch.object(
            authorization_server_client, "get_agent_access_token", side_effect=auth_client_raise_exception
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            _ = AgentController.is_os_ready(target_device=target_device, target_agent=target_agent, timeout=timeout)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture, control_target_agent_fixture",
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    @pytest.mark.parametrize(
        "timeout",
        [
            control_api.MIN_IS_OS_READY_TIMEOUT,
            control_api.MAX_IS_OS_READY_TIMEOUT,
            agent_control.AGENT_REST_API_TIMEOUT,
        ],
    )
    @pytest.mark.parametrize(
        "requests_raise_exception",
        [
            requests.exceptions.RequestException,
            requests.exceptions.InvalidJSONError,
            requests.exceptions.HTTPError,
            requests.exceptions.URLRequired,
            requests.exceptions.TooManyRedirects,
            requests.exceptions.MissingSchema,
            requests.exceptions.InvalidSchema,
        ],
    )
    def test_requests_raise_unexpected_exception(  # pylint: disable=too-many-arguments
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        timeout,
        requests_raise_exception,
    ):
        """Test request raise unexpected exception case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(PowerControlTargetDevice, "set_power_state", return_value=None)
        mocker.patch.object(requests.Session, "get", side_effect=requests_raise_exception)

        mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.InternalHwControlError):
            _ = AgentController.is_os_ready(target_device=target_device, target_agent=target_agent, timeout=timeout)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture, control_target_agent_fixture",
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCpuInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    @pytest.mark.parametrize(
        "timeout",
        [
            control_api.MIN_IS_OS_READY_TIMEOUT,
            control_api.MAX_IS_OS_READY_TIMEOUT,
            agent_control.AGENT_REST_API_TIMEOUT,
        ],
    )
    @pytest.mark.parametrize(
        "expected_exception, agent_return_status_code, agent_return_body",
        [
            (
                exc.AuthenticationHwControlError,
                401,
                {"code": "EF003BAS011", "message": "Failed to authenticate to the HW Control Agent."},
            ),  # valid_access_token function handle case.
            (
                exc.AuthenticationHwControlError,
                401,
                {"code": "EF003BAS011", "message": "Not authenticated"},
            ),  # OAuth2AuthorizationCodeBearer handle case.
            (
                exc.ControlObjectHwControlError,
                500,
                {"foo": "bar"},
            ),
            (
                exc.ControlObjectHwControlError,
                400,
                {"foo": "bar"},
            ),
            (
                exc.ControlObjectHwControlError,
                204,
                {"foo": "bar"},
            ),
        ],
    )
    def test_agent_return_error(  # pylint: disable=too-many-arguments
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        timeout,
        expected_exception,
        agent_return_status_code,
        agent_return_body,
    ):
        """Test agent return error response case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(PowerControlTargetDevice, "set_power_state", return_value=None)

        dummy_response = test_util.generate_dummy_agent_response(
            status_code=agent_return_status_code, content=agent_return_body
        )
        mocker.patch.object(requests.Session, "get", return_value=dummy_response)

        mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            _ = AgentController.is_os_ready(target_device=target_device, target_agent=target_agent, timeout=timeout)

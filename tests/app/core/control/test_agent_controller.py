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

"""Unit test module for AgentController class."""

import json
import logging
from http import HTTPMethod, HTTPStatus

import pytest
import requests
from pytest_mock import MockFixture
from requests.models import Response

import app.common.basic_exceptions as exc
from app.common import constants
from app.common.utils.authorization_utilities import authorization_server_client
from app.core.control import agent_control
from app.core.control.agent_control import AgentController, ControlTargetAgent
from app.core.control.control_base import PowerControlTargetDevice
from app.core.control.oob_control import OOBController
from app.routers.control import control_api
from tests.app.core.control import test_util


class TestOSShutdown:
    """Unit test class for AgentController.os_shutdown."""

    @pytest.mark.parametrize(
        ("power_control_target_device_fixture", "control_target_agent_fixture"),
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    def test_successful_case(
        self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        dummy_correlation_id: str,
    ):
        """test successful case.

        Args:
            caplog
                log capture fixture

            mocker (MockFixture):
                Fixture for creating mock objects.

            dummy_correlation_id (str):
                Dummy correlation ID fixture.

        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(PowerControlTargetDevice, "set_power_state", return_value=None)

        def mock_put_with_verification(url, **kwargs):
            """Mock function to verify request details."""

            # ++++ inspection ++++
            # Verify request details
            assert url == f"http://{target_agent.ip_address}:8000/cdim/api/v1/agent/os-shutdown"
            assert kwargs.get("timeout") == pytest.approx(agent_control.AGENT_REST_API_TIMEOUT)

            # Verify headers
            headers = kwargs.get("headers", {})
            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer dummy_access_token"
            assert constants.CORRELATION_ID_HEADER in headers
            assert headers[constants.CORRELATION_ID_HEADER] == dummy_correlation_id

            # Return dummy response
            dummy_agent_response = Response()
            dummy_agent_response.status_code = HTTPStatus.OK.value
            dummy_agent_response._content = b""
            return dummy_agent_response

        mocker.patch.object(requests, "put", side_effect=mock_put_with_verification)

        mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=agent_control.__name__):
            AgentController.os_shutdown(target_device=target_device, target_agent=target_agent)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 2, "Agent Response log and Agent Response log should be recorded."

        # Inspection: Check the Agent RequestLog log
        agent_request_log = caplog.records[0]
        assert agent_request_log.levelname == "INFO"
        assert agent_request_log.getMessage() == "Send OS shutdown request to Agent."

        assert hasattr(agent_request_log, "url"), "url should be present in the log record"
        assert (
            getattr(agent_request_log, "url") == f"http://{target_agent.ip_address}:8000/cdim/api/v1/agent/os-shutdown"
        )

        assert hasattr(agent_request_log, "http_method"), "http_method should be present in the log record"
        assert getattr(agent_request_log, "http_method") == HTTPMethod.PUT

        assert hasattr(agent_request_log, "time_out"), "time_out should be present in the log record"
        assert getattr(agent_request_log, "time_out") == pytest.approx(3.0)

        # Inspection: Check the Agent Response log
        agent_response_log = caplog.records[1]
        assert agent_response_log.levelname == "INFO"
        assert agent_response_log.getMessage() == "Received OS shutdown response from Agent."

        assert hasattr(agent_response_log, "status_code"), "status_code should be present in the log record"
        assert getattr(agent_response_log, "status_code") == HTTPStatus.OK.value

        assert hasattr(agent_response_log, "response_body"), "response_body should be present in the log record"
        assert getattr(agent_response_log, "response_body") == ""

    @pytest.mark.parametrize(
        ("power_control_target_device_fixture", "control_target_agent_fixture", "expected_exception"),
        [
            (
                {  # input device object
                    "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyDeviceInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
                },
                exc.RequestNotSupportedHWControlError,
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    def test_invalid_device_type(
        self,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        expected_exception: type[exc.BaseHWControlError],
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
        ("power_control_target_device_fixture", "control_target_agent_fixture"),
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.PAUSED,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
                },
            ),
            (
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.UNKNOWN,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    def test_invalid_power_state(
        self,
        mocker: MockFixture,
        caplog: pytest.LogCaptureFixture,
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
        caplog.clear()
        with pytest.raises(exc.InternalHWControlError):
            with caplog.at_level(logging.INFO, logger=agent_control.__name__):
                AgentController.os_shutdown(target_device=target_device, target_agent=target_agent)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1, "log should be recorded."

        # Inspection: Check the unexpected power log
        unexpected_power_log = caplog.records[0]
        assert unexpected_power_log.levelname == "WARNING"
        assert unexpected_power_log.getMessage() == "The device power state is unexpected."

        assert hasattr(unexpected_power_log, "device_id"), "device_id should be present in the log record"
        assert getattr(unexpected_power_log, "device_id") == target_device.device_id

        assert hasattr(unexpected_power_log, "power_state"), "power_state should be present in the log record"
        assert getattr(unexpected_power_log, "power_state") == target_device.power_state

    @pytest.mark.parametrize(
        ("power_control_target_device_fixture", "control_target_agent_fixture"),
        [
            (  # target device already power_off
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.OFF,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
                },
            ),
            (  # target device powering off
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.POWERING_OFF,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
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
        ("auth_client_raise_exception", "expected_exception"),
        [
            (exc.InternalHWControlError, exc.InternalHWControlError),
            (exc.ConfigurationHWControlError, exc.ConfigurationHWControlError),
        ],
    )
    @pytest.mark.parametrize(
        "control_target_agent_fixture",
        [
            {  # input agent object
                "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
            },
        ],
        indirect=["control_target_agent_fixture"],
    )
    def test_execute_os_shutdown_auth_client_raise(
        self,
        mocker: MockFixture,
        auth_client_raise_exception: type[Exception],
        expected_exception: type[exc.BaseHWControlError],
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
            AgentController._execute_os_shutdown(target_agent=target_agent)

    @pytest.mark.parametrize(
        "auth_client_raise_exception",
        [
            exc.InternalHWControlError(),
            exc.ConfigurationHWControlError(),
        ],
    )
    @pytest.mark.parametrize(
        ("power_control_target_device_fixture", "control_target_agent_fixture"),
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    def test_auth_client_raise(
        self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockFixture,
        auth_client_raise_exception: type[Exception],
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

        mock_power_off = mocker.patch.object(OOBController, "power_off")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.WARNING, logger=agent_control.__name__):
            AgentController.os_shutdown(target_device=target_device, target_agent=target_agent)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        mock_power_off.assert_called_once()

        assert len(caplog.records) == 1

        # Inspection: Check the Exception log
        exception_log = caplog.records[0]
        assert exception_log.levelname == "WARNING"
        assert exception_log.getMessage() == "Failed to shutdown the host OS via Agent. Retry ACPI shutdown via OOB."
        assert exception_log.exc_info is not None, "exc_info should be present in the log record"
        assert exception_log.exc_info[1] == auth_client_raise_exception

    @pytest.mark.parametrize(
        "control_target_agent_fixture",
        [
            {  # input agent object
                "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
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
        requests_raise_exception: type[Exception],
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
        with pytest.raises(exc.InternalHWControlError):
            AgentController._execute_os_shutdown(target_agent=target_agent)

    @pytest.mark.parametrize(
        ("power_control_target_device_fixture", "control_target_agent_fixture"),
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    @pytest.mark.parametrize(
        "requests_raise_exception",
        [
            requests.exceptions.ReadTimeout(),
            requests.exceptions.ConnectionError(),
            requests.exceptions.ConnectTimeout(),
        ],
    )
    def test_requests_raise(
        self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockFixture,
        requests_raise_exception: type[Exception],
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

        mock_power_off = mocker.patch.object(OOBController, "power_off")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.WARNING, logger=agent_control.__name__):
            AgentController.os_shutdown(target_device=target_device, target_agent=target_agent)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        mock_power_off.assert_called_once()

        assert len(caplog.records) == 1

        # Inspection: Check the Exception log
        exception_log = caplog.records[0]
        assert exception_log.levelname == "WARNING"
        assert exception_log.getMessage() == "Failed to shutdown the host OS via Agent. Retry ACPI shutdown via OOB."
        assert exception_log.exc_info is not None, "exc_info should be present in the log record"
        assert isinstance(exception_log.exc_info[1], exc.BaseHWControlError), (
            "raised exception should be BaseHWControlError sub class."
        )

    @pytest.mark.parametrize(
        "control_target_agent_fixture",
        [
            {  # input agent object
                "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
            },
        ],
        indirect=["control_target_agent_fixture"],
    )
    @pytest.mark.parametrize(
        ("expected_exception", "agent_return_status_code", "agent_return_body"),
        [
            (
                exc.AuthenticationHWControlError,
                401,
                {
                    "code": "EFA02BAS000",
                    "message": "Authentication failed. Failed to authenticate to the HW Control Agent.",
                },
            ),  # valid_access_token function handle case.
            (
                exc.ControlObjectHWControlError,
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
    def test_execute_os_shutdown_agent_return_error(
        self,
        mocker: MockFixture,
        expected_exception: type[Exception],
        agent_return_status_code: int,
        agent_return_body: dict[str, str],
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
        dummy_agent_response = Response()
        dummy_agent_response.status_code = agent_return_status_code
        dummy_agent_response._content = json.dumps(agent_return_body).encode("utf-8")
        mocker.patch.object(requests, "put", return_value=dummy_agent_response)

        mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            AgentController._execute_os_shutdown(target_agent=target_agent)

    @pytest.mark.parametrize(
        ("power_control_target_device_fixture", "control_target_agent_fixture"),
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
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
    def test_agent_return_error(
        self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockFixture,
        agent_return_status_code: int,
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

        agent_return_response_body = {"Foo": "bar"}
        dummy_agent_response = Response()
        dummy_agent_response.status_code = agent_return_status_code
        dummy_agent_response._content = json.dumps(agent_return_response_body).encode("utf-8")
        dummy_agent_response.headers["Content-Type"] = "application/json"
        dummy_agent_response.encoding = "utf-8"
        mocker.patch.object(requests, "put", return_value=dummy_agent_response)

        mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

        mock_power_off = mocker.patch.object(OOBController, "power_off")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=agent_control.__name__):
            AgentController.os_shutdown(target_device=target_device, target_agent=target_agent)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        mock_power_off.assert_called_once()

        assert len(caplog.records) == 3, "Agent Response log, Agent Response log and Exception log should be recorded."

        # Inspection: Check the Agent Response log
        agent_response_log = caplog.records[1]
        assert agent_response_log.levelname == "INFO"
        assert agent_response_log.getMessage() == "Received OS shutdown response from Agent."

        assert hasattr(agent_response_log, "status_code"), "status_code should be present in the log record"
        assert getattr(agent_response_log, "status_code") == agent_return_status_code

        assert hasattr(agent_response_log, "response_body"), "response_body should be present in the log record"
        assert getattr(agent_response_log, "response_body") == '{"Foo": "bar"}'

        # Inspection: Check the Exception log
        exception_log = caplog.records[2]
        assert exception_log.levelname == "WARNING"
        assert exception_log.getMessage() == "Failed to shutdown the host OS via Agent. Retry ACPI shutdown via OOB."
        assert exception_log.exc_info is not None, "exc_info should be present in the log record"
        assert isinstance(exception_log.exc_info[1], exc.BaseHWControlError), (
            "raised exception should be BaseHWControlError sub class."
        )

    @pytest.mark.parametrize(
        ("power_control_target_device_fixture", "control_target_agent_fixture"),
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.UNKNOWN,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
                },
            ),
        ],
        indirect=["power_control_target_device_fixture", "control_target_agent_fixture"],
    )
    @pytest.mark.parametrize(
        "device_raise_exception",
        [
            exc.BaseHWControlError,
            exc.InternalHWControlError,
            exc.RequestNotSupportedHWControlError,
        ],
    )
    def test_device_raise(
        self,
        mocker: MockFixture,
        device_raise_exception: type[Exception],
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
        ("power_control_target_device_fixture", "control_target_agent_fixture"),
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.UNKNOWN,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
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
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            AgentController.os_shutdown(target_device=target_device, target_agent=target_agent)


class TestIsOSReady:
    """Unit test class for AgentController.is_os_ready."""

    @pytest.mark.parametrize(
        ("power_control_target_device_fixture", "control_target_agent_fixture", "expected_os_state"),
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
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
    def test_successful_case(
        self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        expected_os_state: bool,
        timeout: int,
    ):
        """test successful case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(PowerControlTargetDevice, "set_power_state", return_value=None)

        def mock_get_with_verification(url, **kwargs):
            """Mock function to verify request details."""
            # Verify request details
            assert url == f"http://{target_agent.ip_address}:8000/cdim/api/v1/agent/is-os-ready"
            assert kwargs.get("timeout") == pytest.approx(agent_control.AGENT_REST_API_TIMEOUT)

            # Verify headers
            headers = kwargs.get("headers", {})
            assert "Authorization" in headers
            assert headers["Authorization"] == "Bearer dummy_access_token"
            assert constants.CORRELATION_ID_HEADER in headers
            # Verify correlation ID is default value when context is empty
            assert headers[constants.CORRELATION_ID_HEADER] == constants.CORRELATION_ID_DEFAULT_VALUE

            # Return dummy response
            dummy_agent_response = Response()
            dummy_agent_response.status_code = HTTPStatus.OK.value
            dummy_agent_response._content = b""
            return dummy_agent_response

        mocker.patch.object(requests.Session, "get", side_effect=mock_get_with_verification)

        mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=agent_control.__name__):
            actual = AgentController.is_os_ready(
                target_device=target_device, target_agent=target_agent, timeout=timeout
            )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual == expected_os_state

        assert len(caplog.records) == 2, "Agent Response log and Agent Response log should be recorded."

        # Inspection: Check the Agent RequestLog log
        agent_request_log = caplog.records[0]
        assert agent_request_log.levelname == "INFO"
        assert agent_request_log.getMessage() == "Send OS ready check request to Agent."

        assert hasattr(agent_request_log, "url"), "url should be present in the log record"
        assert (
            getattr(agent_request_log, "url") == f"http://{target_agent.ip_address}:8000/cdim/api/v1/agent/is-os-ready"
        )

        assert hasattr(agent_request_log, "http_method"), "http_method should be present in the log record"
        assert getattr(agent_request_log, "http_method") == HTTPMethod.GET

        assert hasattr(agent_request_log, "time_out"), "time_out should be present in the log record"
        assert getattr(agent_request_log, "time_out") == timeout

        # Inspection: Check the Agent Response log
        agent_response_log = caplog.records[1]
        assert agent_response_log.levelname == "INFO"
        assert agent_response_log.getMessage() == "Received OS ready check response from Agent."

        assert hasattr(agent_response_log, "status_code"), "status_code should be present in the log record"
        assert getattr(agent_response_log, "status_code") == HTTPStatus.OK.value

        assert hasattr(agent_response_log, "response_body"), "response_body should be present in the log record"
        assert getattr(agent_response_log, "response_body") == ""

    @pytest.mark.parametrize(
        ("power_control_target_device_fixture", "control_target_agent_fixture", "expected_exception"),
        [
            (
                {  # input device object
                    "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyDeviceInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
                },
                exc.RequestNotSupportedHWControlError,
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
        expected_exception: type[Exception],
        timeout: int,
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
        ("power_control_target_device_fixture", "control_target_agent_fixture"),
        [
            (  # target device already power_off
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.OFF,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
                },
            ),
            (  # target device powering off
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.POWERING_OFF,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
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
        timeout: int,
    ):
        """Test for plugin return invalid power state case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        mocker.patch.object(PowerControlTargetDevice, "set_power_state", return_value=None)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.HostCPUPowerOffBadRequestHWControlError):
            _ = AgentController.is_os_ready(target_device=target_device, target_agent=target_agent, timeout=timeout)

    @pytest.mark.parametrize(
        ("power_control_target_device_fixture", "control_target_agent_fixture", "expected_os_state"),
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
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
    def test_request_timeout(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        expected_os_state: bool,
        timeout: int,
        requests_raise_exception: type[Exception],
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
        ("power_control_target_device_fixture", "control_target_agent_fixture"),
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.PAUSED,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
                },
            ),
            (
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.UNKNOWN,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
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
        caplog: pytest.LogCaptureFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        timeout: int,
    ):
        """Test request raise unexpected exception case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(PowerControlTargetDevice, "set_power_state", return_value=None)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with pytest.raises(exc.InternalHWControlError):
            with caplog.at_level(logging.INFO, logger=agent_control.__name__):
                _ = AgentController.is_os_ready(target_device=target_device, target_agent=target_agent, timeout=timeout)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1, "log should be recorded."

        # Inspection: Check the unexpected power log
        unexpected_power_log = caplog.records[0]
        assert unexpected_power_log.levelname == "WARNING"
        assert unexpected_power_log.getMessage() == "The device power state is unexpected."

        assert hasattr(unexpected_power_log, "device_id"), "device_id should be present in the log record"
        assert getattr(unexpected_power_log, "device_id") == target_device.device_id

        assert hasattr(unexpected_power_log, "power_state"), "power_state should be present in the log record"
        assert getattr(unexpected_power_log, "power_state") == target_device.power_state

    @pytest.mark.parametrize(
        ("power_control_target_device_fixture", "control_target_agent_fixture"),
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
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
        caplog: pytest.LogCaptureFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        timeout: int,
    ):
        """Test request raise unexpected exception case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(PowerControlTargetDevice, "set_power_state", side_effect=ValueError)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            with caplog.at_level(logging.INFO, logger=agent_control.__name__):
                _ = AgentController.is_os_ready(target_device=target_device, target_agent=target_agent, timeout=timeout)

    @pytest.mark.parametrize(
        ("auth_client_raise_exception", "expected_exception"),
        [
            (exc.InternalHWControlError, exc.InternalHWControlError),
            (exc.ConfigurationHWControlError, exc.ConfigurationHWControlError),
        ],
    )
    @pytest.mark.parametrize(
        ("power_control_target_device_fixture", "control_target_agent_fixture"),
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
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
    def test_auth_client_raise(
        self,
        mocker: MockFixture,
        auth_client_raise_exception: type[Exception],
        expected_exception: type[Exception],
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        timeout: int,
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
        ("power_control_target_device_fixture", "control_target_agent_fixture"),
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
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
    def test_requests_raise_unexpected_exception(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        timeout: int,
        requests_raise_exception: type[Exception],
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
        with pytest.raises(exc.InternalHWControlError):
            _ = AgentController.is_os_ready(target_device=target_device, target_agent=target_agent, timeout=timeout)

    @pytest.mark.parametrize(
        ("power_control_target_device_fixture", "control_target_agent_fixture"),
        [
            (
                {  # input device object
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                    "power_state": constants.DevicePowerState.ON,
                },
                {  # input agent object
                    "host_cpu_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "ip_address": test_util.DummyCPUInfo.IP_ADDRESS.value,
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
        ("expected_exception", "agent_return_status_code", "agent_return_body"),
        [
            (
                exc.AuthenticationHWControlError,
                401,
                {"code": "EF003BAS011", "message": "Failed to authenticate to the HW Control Agent."},
            ),  # valid_access_token function handle case.
            (
                exc.AuthenticationHWControlError,
                401,
                {"code": "EF003BAS011", "message": "Not authenticated"},
            ),  # OAuth2AuthorizationCodeBearer handle case.
            (
                exc.ControlObjectHWControlError,
                500,
                {"foo": "bar"},
            ),
            (
                exc.ControlObjectHWControlError,
                400,
                {"foo": "bar"},
            ),
            (
                exc.ControlObjectHWControlError,
                204,
                {"foo": "bar"},
            ),
        ],
    )
    def test_agent_return_error(
        self,
        mocker: MockFixture,
        caplog: pytest.LogCaptureFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        control_target_agent_fixture: ControlTargetAgent,
        timeout: int,
        expected_exception: type[Exception],
        agent_return_status_code: int,
        agent_return_body: dict,
    ):
        """Test agent return error response case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture
        target_agent = control_target_agent_fixture

        # Set up the mock.
        mocker.patch.object(PowerControlTargetDevice, "set_power_state", return_value=None)

        dummy_agent_response = Response()
        dummy_agent_response.status_code = agent_return_status_code
        dummy_agent_response._content = json.dumps(agent_return_body).encode("utf-8")
        dummy_agent_response.headers["Content-Type"] = "application/json"
        dummy_agent_response.encoding = "utf-8"
        mocker.patch.object(requests.Session, "get", return_value=dummy_agent_response)

        mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with pytest.raises(expected_exception):
            with caplog.at_level(logging.INFO, logger=agent_control.__name__):
                _ = AgentController.is_os_ready(target_device=target_device, target_agent=target_agent, timeout=timeout)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#

        assert len(caplog.records) == 2, "Agent Response log and Agent Response log should be recorded."

        # Inspection: Check the Agent Response log
        agent_response_log = caplog.records[1]
        assert agent_response_log.levelname == "INFO"
        assert agent_response_log.getMessage() == "Received OS ready check response from Agent."

        assert hasattr(agent_response_log, "status_code"), "status_code should be present in the log record"
        assert getattr(agent_response_log, "status_code") == agent_return_status_code

        assert hasattr(agent_response_log, "response_body"), "response_body should be present in the log record"
        assert getattr(agent_response_log, "response_body") == json.dumps(agent_return_body)

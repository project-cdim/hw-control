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

"""Unit test module for control_api module ."""

import logging
import uuid
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockFixture

import app.common.basic_exceptions as exc
from app.core.control import agent_control, control_base, fm_control, oob_control
from app.routers.control import control_api

DUMMY_IP_ADDRESS = "192.0.2.1"


class TestPerformPowerOff:
    """Unit test class for control_api._perform_power_off ."""

    def test_power_off_via_oob_success(self, mocker: MockFixture):
        """
        Test successful power off via OOB (Out-of-Band).

        Args:
            mocker (MockFixture): Pytest-mock fixture for mocking objects and functions.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = MagicMock(spec=control_base.PowerControlTargetDevice, device_id="dummy-device-id")

        mocker.patch.object(
            oob_control.OOBController,
            "power_off",
            return_value=None,
        )

        mocker.patch(
            "app.core.control.agent_control.ControlTargetAgent",
            side_effect=exc.RequestNotSupportedHWControlError,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        control_api._perform_power_off(
            target_device=target_device,
        )

    def test_power_off_via_oob_error(self, mocker: MockFixture):
        """
        Test power off via OOB (Out-of-Band) with error (exception raised).

        Args:
            mocker (MockFixture): Pytest-mock fixture for mocking objects and functions.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = MagicMock(spec=control_base.PowerControlTargetDevice, device_id="dummy-device-id")

        mocker.patch.object(oob_control.OOBController, "power_off", side_effect=exc.PowerOffFailureHWControlError)

        mocker.patch(
            "app.core.control.agent_control.ControlTargetAgent",
            side_effect=exc.RequestNotSupportedHWControlError,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.PowerOffFailureHWControlError):
            control_api._perform_power_off(target_device=target_device)

    def test_shutdown_via_agent_success(self, mocker: MockFixture):
        """
        Test successful shutdown via Agent.

        Args:
            mocker (MockFixture): Pytest-mock fixture for mocking objects and functions.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = MagicMock(spec=control_base.PowerControlTargetDevice, device_id="dummy-device-id")

        mocker.patch.object(agent_control.AgentController, "os_shutdown", return_value=None)
        mocker.patch.object(agent_control.ControlTargetAgent, "model_post_init")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        control_api._perform_power_off(target_device=target_device)

    def test_shutdown_via_agent_error(self, mocker: MockFixture):
        """
        Test shutdown via Agent with error (exception raised).

        Args:
            mocker (MockFixture): Pytest-mock fixture for mocking objects and functions.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = MagicMock(spec=control_base.PowerControlTargetDevice, device_id="dummy-device-id")

        mocker.patch.object(
            agent_control.AgentController,
            "os_shutdown",
            side_effect=exc.RequestNotSupportedHWControlError,
        )
        mocker.patch.object(agent_control.ControlTargetAgent, "model_post_init")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            control_api._perform_power_off(target_device=target_device)


class TestPowerControlAPI:
    """Unit test class for power_control_api."""

    @pytest.mark.parametrize(
        ("action", "controller_method"),
        [
            (control_api.PowerControlAction.ON.value, "power_on"),
            (control_api.PowerControlAction.FORCE_OFF.value, "force_off"),
            (control_api.PowerControlAction.RESET.value, "reset"),
        ],
    )
    def test_success(
        self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockFixture,
        action: str,
        controller_method: str,
    ):
        """
        Test successful call to power_control_api (ON/FORCE_OFF/RESET actions).

        Args:
            caplog (pytest.LogCaptureFixture): Pytest fixture for capturing log records.
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
            action (str): Power control action parameter (ON/FORCE_OFF/RESET).
            controller_method (str): OOBController method name to be called ("power_on", "force_off", "reset").
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_id = uuid.uuid4()

        mocker.patch.object(oob_control.OOBController, controller_method, return_value=None)
        mocker.patch.object(control_base.PowerControlTargetDevice, "model_post_init")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=control_api.__name__):
            result = control_api.power_control_api(
                request_body=control_api.PowerControlRequestModel(action=action),
                device_id=test_device_id,
            )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result.device_id == str(test_device_id)

        # Inspection: Check the request parameter log
        request_parameter_log = caplog.records[0]
        assert request_parameter_log.levelname == "INFO"
        assert request_parameter_log.getMessage() == "Power Control start."

        assert hasattr(request_parameter_log, "deviceID"), "deviceID should be present in the log record"
        assert getattr(request_parameter_log, "deviceID") == str(test_device_id)

        assert hasattr(request_parameter_log, "action"), "action should be present in the log record"
        assert getattr(request_parameter_log, "action") == action

    def test_success_off(
        self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockFixture,
    ):
        """
        Test successful call to power_control_api for the OFF action.

        OFF delegates to _perform_power_off; the Agent-vs-OOB branching inside it is
        covered by TestPerformPowerOff, so here _perform_power_off itself is mocked.

        Args:
            caplog (pytest.LogCaptureFixture): Pytest fixture for capturing log records.
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_id = uuid.uuid4()

        mocker.patch.object(control_base.PowerControlTargetDevice, "model_post_init")
        mocker.patch.object(oob_control.OOBController, "power_off", return_value=None)
        mocker.patch(
            "app.core.control.agent_control.ControlTargetAgent",
            side_effect=exc.RequestNotSupportedHWControlError,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=control_api.__name__):
            result = control_api.power_control_api(
                request_body=control_api.PowerControlRequestModel(action=control_api.PowerControlAction.OFF.value),
                device_id=test_device_id,
            )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result.device_id == str(test_device_id)

        request_parameter_log = caplog.records[0]
        assert request_parameter_log.levelname == "INFO"
        assert request_parameter_log.getMessage() == "Power Control start."

        assert hasattr(request_parameter_log, "deviceID"), "deviceID should be present in the log record"
        assert getattr(request_parameter_log, "deviceID") == str(test_device_id)

        assert hasattr(request_parameter_log, "action"), "action should be present in the log record"
        assert getattr(request_parameter_log, "action") == control_api.PowerControlAction.OFF.value

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
        test_device_id = uuid.uuid4()

        mocker.patch(
            "app.core.control.control_base.PowerControlTargetDevice",
            side_effect=exc.RequestNotSupportedHWControlError,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            control_api.power_control_api(
                request_body=control_api.PowerControlRequestModel(action=action),
                device_id=test_device_id,
            )

    @pytest.mark.parametrize(
        ("action", "controller_method"),
        [
            (control_api.PowerControlAction.ON.value, "power_on"),
            (control_api.PowerControlAction.FORCE_OFF.value, "force_off"),
            (control_api.PowerControlAction.RESET.value, "reset"),
        ],
    )
    def test_controller_raise(
        self,
        mocker: MockFixture,
        action: str,
        controller_method: str,
    ):
        """
        Test case where OOBController method raises an exception (ON/FORCE_OFF/RESET actions).

        Args:
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
            action (str): Power control action parameter to be tested.
            controller_method (str): OOBController method name to be called.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_id = uuid.uuid4()

        mocker.patch.object(control_base.PowerControlTargetDevice, "model_post_init")
        mocker.patch.object(
            oob_control.OOBController, controller_method, side_effect=exc.RequestNotSupportedHWControlError
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            control_api.power_control_api(
                request_body=control_api.PowerControlRequestModel(action=action),
                device_id=test_device_id,
            )

    def test_controller_raise_off(self, mocker: MockFixture):
        """
        Test case where _perform_power_off raises an exception for the OFF action.

        The Agent-vs-OOB branching inside _perform_power_off is covered by
        TestPerformPowerOff, so here _perform_power_off itself is mocked to raise.

        Args:
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_id = uuid.uuid4()

        mocker.patch.object(control_base.PowerControlTargetDevice, "model_post_init")
        mocker.patch(
            "app.core.control.agent_control.ControlTargetAgent",
            side_effect=exc.RequestNotSupportedHWControlError,
        )
        mocker.patch.object(oob_control.OOBController, "power_off", side_effect=exc.RequestNotSupportedHWControlError)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            control_api.power_control_api(
                request_body=control_api.PowerControlRequestModel(action=control_api.PowerControlAction.OFF.value),
                device_id=test_device_id,
            )

    @pytest.mark.parametrize(
        ("action", "controller_method"),
        [
            (control_api.PowerControlAction.ON.value, "power_on"),
            (control_api.PowerControlAction.FORCE_OFF.value, "force_off"),
            (control_api.PowerControlAction.RESET.value, "reset"),
        ],
    )
    def test_device_busy(
        self,
        mocker: MockFixture,
        action: str,
        controller_method: str,
    ):
        """
        Test case where the plugin raises DeviceBusyHWControlError (ON/FORCE_OFF/RESET actions).

        Args:
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
            action (str): Power control action parameter to be tested.
            controller_method (str): OOBController method name to be called.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_id = uuid.uuid4()

        mocker.patch.object(control_base.PowerControlTargetDevice, "model_post_init")
        mocker.patch.object(
            oob_control.OOBController,
            controller_method,
            side_effect=exc.DeviceBusyHWControlError(
                additional_message=f"The following Device ID is relevant: {test_device_id}"
            ),
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.DeviceBusyHWControlError):
            control_api.power_control_api(
                request_body=control_api.PowerControlRequestModel(action=action),
                device_id=test_device_id,
            )

    def test_device_busy_off(self, mocker: MockFixture):
        """
        Test case where _perform_power_off raises DeviceBusyHWControlError for the OFF action.

        The Agent-vs-OOB branching inside _perform_power_off is covered by
        TestPerformPowerOff, so here _perform_power_off itself is mocked to raise.

        Args:
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_id = uuid.uuid4()

        mocker.patch.object(control_base.PowerControlTargetDevice, "model_post_init")
        mocker.patch(
            "app.core.control.agent_control.ControlTargetAgent",
            side_effect=exc.RequestNotSupportedHWControlError,
        )
        mocker.patch.object(
            control_api,
            "_perform_power_off",
            side_effect=exc.DeviceBusyHWControlError(
                additional_message=f"The following Device ID is relevant: {test_device_id}"
            ),
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.DeviceBusyHWControlError):
            control_api.power_control_api(
                request_body=control_api.PowerControlRequestModel(action=control_api.PowerControlAction.OFF.value),
                device_id=test_device_id,
            )


class TestIsOSReadyAPI:
    """Unit test class for is_os_ready_api."""

    @pytest.mark.parametrize("os_state", [True, False])
    def test_success_default_timeout(
        self,
        mocker: MockFixture,
        os_state: bool,
    ):
        """
        Test successful call to is_os_ready_api with default timeout value.

        Args:
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
            os_state (bool): OS state (True/False) for test case.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_id = uuid.uuid4()
        test_ip_address = DUMMY_IP_ADDRESS

        mocker.patch.object(agent_control.AgentController, "is_os_ready", return_value=os_state)

        mocker.patch.object(control_base.PowerControlTargetDevice, "model_post_init")

        mocker.patch(
            "app.core.control.agent_control.ControlTargetAgent",
            return_value=MagicMock(spec=agent_control.ControlTargetAgent, ip_address=test_ip_address),
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = control_api.is_os_ready_api(
            cpu_device_id=test_device_id,
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result.status == os_state
        assert result.ip_address == test_ip_address

    @pytest.mark.parametrize("os_state", [True, False])
    @pytest.mark.parametrize("timeout", [control_api.MIN_IS_OS_READY_TIMEOUT, control_api.MAX_IS_OS_READY_TIMEOUT])
    def test_success_within_range_of_timeout(
        self,
        caplog: pytest.LogCaptureFixture,
        mocker: MockFixture,
        os_state: bool,
        timeout: int,
    ):
        """
        Test successful call to is_os_ready_api with valid timeout value.

        Args:
            caplog (pytest.LogCaptureFixture): Pytest fixture for capturing log records.
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
            os_state (bool): OS state (True/False) for test case.
            timeout (int): Timeout value to be tested.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_id = uuid.uuid4()
        test_ip_address = DUMMY_IP_ADDRESS

        mocker.patch.object(agent_control.AgentController, "is_os_ready", return_value=os_state)

        mocker.patch.object(control_base.PowerControlTargetDevice, "model_post_init")

        mocker.patch(
            "app.core.control.agent_control.ControlTargetAgent",
            return_value=MagicMock(spec=agent_control.ControlTargetAgent, ip_address=test_ip_address),
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=control_api.__name__):
            result = control_api.is_os_ready_api(cpu_device_id=test_device_id, time_out=timeout)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result.status == os_state
        assert result.ip_address == test_ip_address

        # Inspection: Check the request parameter log
        request_parameter_log = caplog.records[0]
        assert request_parameter_log.levelname == "INFO"
        assert request_parameter_log.getMessage() == "Is OS Ready start."

        assert hasattr(request_parameter_log, "CPUDeviceID"), "CPUDeviceID should be present in the log record"
        assert getattr(request_parameter_log, "CPUDeviceID") == str(test_device_id)

        assert hasattr(request_parameter_log, "timeOut"), "timeOut should be present in the log record"
        assert getattr(request_parameter_log, "timeOut") == timeout

    @pytest.mark.parametrize("timeout", [control_api.MIN_IS_OS_READY_TIMEOUT, control_api.MAX_IS_OS_READY_TIMEOUT])
    def test_device_raise(self, mocker: MockFixture, timeout: int):
        """
        Test case where device object creation raises an exception in is_os_ready_api.

        Args:
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
            timeout (int): Timeout value to be tested.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_id = uuid.uuid4()

        mocker.patch(
            "app.core.control.control_base.PowerControlTargetDevice",
            side_effect=exc.RequestNotSupportedHWControlError,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            control_api.is_os_ready_api(cpu_device_id=test_device_id, time_out=timeout)

    @pytest.mark.parametrize("timeout", [control_api.MIN_IS_OS_READY_TIMEOUT, control_api.MAX_IS_OS_READY_TIMEOUT])
    def test_agent_raise(
        self,
        mocker: MockFixture,
        timeout: int,
    ):
        """
        Test case where agent object creation raises an exception in is_os_ready_api.

        Args:
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
            timeout (int): Timeout value to be tested.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_id = uuid.uuid4()

        mocker.patch.object(control_base.PowerControlTargetDevice, "model_post_init")
        mocker.patch(
            "app.core.control.agent_control.ControlTargetAgent",
            side_effect=exc.RequestNotSupportedHWControlError,
        )
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            control_api.is_os_ready_api(cpu_device_id=test_device_id, time_out=timeout)

    @pytest.mark.parametrize("timeout", [control_api.MIN_IS_OS_READY_TIMEOUT, control_api.MAX_IS_OS_READY_TIMEOUT])
    def test_controller_raise(
        self,
        mocker: MockFixture,
        timeout: int,
    ):
        """
        Test case where AgentController raises an exception in is_os_ready_api.

        Args:
            mocker (MockFixture): Pytest fixture for mocking objects and functions.
            timeout (int): Timeout value to be tested.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_id = uuid.uuid4()

        mocker.patch.object(
            agent_control.AgentController, "is_os_ready", side_effect=exc.RequestNotSupportedHWControlError
        )

        mocker.patch.object(control_base.PowerControlTargetDevice, "model_post_init")
        mocker.patch.object(agent_control.ControlTargetAgent, "model_post_init")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            control_api.is_os_ready_api(cpu_device_id=test_device_id, time_out=timeout)


class TestDeviceAggregationControlAPI:
    """Unit test class for device_aggregation_control_api."""

    @pytest.mark.parametrize(
        ("action", "controller_method"),
        [
            (control_api.AggregationControlAction.CONNECT.value, "connect"),
            (control_api.AggregationControlAction.DISCONNECT.value, "disconnect"),
        ],
    )
    def test_success_default_timeout(
        self, caplog: pytest.LogCaptureFixture, mocker: MockFixture, action: str, controller_method: str
    ):
        """
        Test the successful call to device_aggregation_control_api.

        Args:
            caplog (pytest.LogCaptureFixture):
                Pytest fixture for capturing log records.
            mocker (MockFixture):
                Pytest fixture for mocking objects and functions.
            action (str):
                Aggregation action parameter.
            controller_method (str):
                The FMController method name to be called ("connect" or "disconnect").

        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_upstream_device_id = uuid.uuid4()
        test_downstream_device_id = uuid.uuid4()

        mocker.patch.object(control_api, "_get_true_device_ids", return_value=(str(uuid.uuid4()), str(uuid.uuid4())))
        mocker.patch.object(fm_control.FMControlTargetDevice, "model_post_init")
        mocker.patch.object(fm_control.FMController, controller_method, return_value=None)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=control_api.__name__):
            result = control_api.device_aggregation_control_api(
                request_body=control_api.DeviceAggregationControlRequestModel(
                    **{"destinationDeviceID": test_downstream_device_id, "action": action}
                ),
                upstream_device_id=test_upstream_device_id,
            )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result.upstream_device_id == str(test_upstream_device_id)
        assert result.downstream_device_id == str(test_downstream_device_id)

        # Inspection: Check the request parameter log
        request_parameter_log = caplog.records[0]
        assert request_parameter_log.levelname == "INFO"
        assert request_parameter_log.getMessage() == "Device Aggregation Control start."

        assert hasattr(request_parameter_log, "sourceDeviceID"), "sourceDeviceID should be present in the log record"
        assert getattr(request_parameter_log, "sourceDeviceID") == str(test_upstream_device_id)

        assert hasattr(request_parameter_log, "destinationDeviceID"), (
            "destinationDeviceID should be present in the log record"
        )
        assert getattr(request_parameter_log, "destinationDeviceID") == str(test_downstream_device_id)

        assert hasattr(request_parameter_log, "action"), "action should be present in the log record"
        assert getattr(request_parameter_log, "action") == action

    @pytest.mark.parametrize(
        ("action", "controller_method"),
        [
            (control_api.AggregationControlAction.CONNECT.value, "connect"),
            (control_api.AggregationControlAction.DISCONNECT.value, "disconnect"),
        ],
    )
    def test_true_device_id_can_not_get(self, mocker: MockFixture, action: str, controller_method: str):
        """
        Test case where device object cannot be created.

        Args:
            mocker (MockFixture):
                Pytest fixture for mocking objects and functions.
            action (str):
                Aggregation action parameter to be tested.
            controller_method (str):
                The FMController method name to be called ("connect" or "disconnect").
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++++++++++#
        test_upstream_device_id = uuid.uuid4()
        test_downstream_device_id = uuid.uuid4()

        mocker.patch.object(
            control_api,
            "_get_true_device_ids",
            return_value=(str(test_upstream_device_id), str(test_downstream_device_id)),
        )
        mocker.patch.object(fm_control.FMControlTargetDevice, "model_post_init")
        mocker.patch.object(fm_control.FMController, controller_method, return_value=None)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        result = control_api.device_aggregation_control_api(
            request_body=control_api.DeviceAggregationControlRequestModel(
                **{"destinationDeviceID": test_downstream_device_id, "action": action}
            ),
            upstream_device_id=test_upstream_device_id,
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result.upstream_device_id == str(test_upstream_device_id)
        assert result.downstream_device_id == str(test_downstream_device_id)

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
        test_upstream_device_id = uuid.uuid4()
        test_downstream_device_id = uuid.uuid4()

        mocker.patch.object(control_api, "_get_true_device_ids", return_value=(str(uuid.uuid4()), str(uuid.uuid4())))
        mocker.patch(
            "app.core.control.fm_control.FMControlTargetDevice",
            side_effect=exc.RequestNotSupportedHWControlError,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            control_api.device_aggregation_control_api(
                request_body=control_api.DeviceAggregationControlRequestModel(
                    **{"destinationDeviceID": test_downstream_device_id, "action": action}
                ),
                upstream_device_id=test_upstream_device_id,
            )

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
        test_upstream_device_id = uuid.uuid4()
        test_downstream_device_id = test_upstream_device_id

        def dummy_get_true_device_ids(upstream_device_id: str, downstream_device_id: str) -> tuple[str, str]:
            """Dummy_get_true_device_ids"""
            return upstream_device_id, downstream_device_id

        mocker.patch.object(control_api, "_get_true_device_ids", side_effect=dummy_get_true_device_ids)
        mocker.patch.object(fm_control.FMControlTargetDevice, "model_post_init")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            control_api.device_aggregation_control_api(
                request_body=control_api.DeviceAggregationControlRequestModel(
                    **{"destinationDeviceID": test_downstream_device_id, "action": action}
                ),
                upstream_device_id=test_upstream_device_id,
            )

    @pytest.mark.parametrize(
        ("action", "controller_method"),
        [
            (control_api.AggregationControlAction.CONNECT.value, "connect"),
            (control_api.AggregationControlAction.DISCONNECT.value, "disconnect"),
        ],
    )
    def test_device_pair_busy(self, mocker: MockFixture, action: str, controller_method: str):
        """
        Test case where the plugin raises DeviceBusyHWControlError for aggregation control.

        Args:
            mocker (MockFixture):
                Pytest fixture for mocking objects and functions.
            action (str):
                Aggregation action parameter to be tested.
            controller_method (str):
                The FMController method name to be called ("connect" or "disconnect").
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_upstream_device_id = uuid.uuid4()
        test_downstream_device_id = uuid.uuid4()

        mocker.patch.object(control_api, "_get_true_device_ids", return_value=(str(uuid.uuid4()), str(uuid.uuid4())))
        mocker.patch.object(fm_control.FMControlTargetDevice, "model_post_init")
        mocker.patch.object(
            fm_control.FMController,
            controller_method,
            side_effect=exc.DeviceBusyHWControlError(
                additional_message=f"The following Device ID is relevant: {test_downstream_device_id}"
            ),
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.DeviceBusyHWControlError):
            control_api.device_aggregation_control_api(
                request_body=control_api.DeviceAggregationControlRequestModel(
                    **{"destinationDeviceID": test_downstream_device_id, "action": action}
                ),
                upstream_device_id=test_upstream_device_id,
            )

    @pytest.mark.parametrize(
        ("action", "controller_method"),
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
        test_upstream_device_id = uuid.uuid4()
        test_downstream_device_id = uuid.uuid4()

        mocker.patch.object(control_api, "_get_true_device_ids", return_value=(str(uuid.uuid4()), str(uuid.uuid4())))
        mocker.patch.object(fm_control.FMControlTargetDevice, "model_post_init")
        mocker.patch.object(
            fm_control.FMController, controller_method, side_effect=exc.RequestNotSupportedHWControlError
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            control_api.device_aggregation_control_api(
                request_body=control_api.DeviceAggregationControlRequestModel(
                    **{"destinationDeviceID": test_downstream_device_id, "action": action}
                ),
                upstream_device_id=test_upstream_device_id,
            )

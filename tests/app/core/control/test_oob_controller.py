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

"""Unit test module for OOBController class ."""

import logging
from typing import cast

import pytest
from pytest import LogCaptureFixture
from pytest_mock import MockFixture

from tests.app.core.control import test_util

from app.common import constants
import app.common.basic_exceptions as exc
from app.common.utils import plugin_manager
from app.core.control import control_base
from app.core.control import oob_control

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.core.control.oob_control import OOBController

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestPowerOn:
    """Unit test class for OOBController.power_on."""

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
            {
                "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                "device_type": test_util.DummyDeviceInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.OFF.value,
            },
        ],
        indirect=True,
    )
    def test_successful_case(
        self,
        caplog: LogCaptureFixture,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
    ):
        """test successful case.

        Args:
            caplog (LogCaptureFixture):
                The fixture used to capture log messages.

            mocker (MockFixture):
                Fixture for creating mock objects.

            power_control_target_device_fixture (control_base.PowerControlTargetDevice):
                The fixture used to create a target PowerControlTargetDevice object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", return_value=test_util.DummyOOBPlugin())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=oob_control.__name__):
            OOBController.power_on(target_device)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        # Inspection: Check the plugin call log
        plugin_call_log = caplog.records[0]
        assert plugin_call_log.levelname == "INFO"
        assert plugin_call_log.getMessage() == "Request device power on to OOB plugin."

        assert hasattr(plugin_call_log, "manager_type"), "manager_type should be present in the log record"
        assert getattr(plugin_call_log, "manager_type") == "OOB"

        assert hasattr(plugin_call_log, "manager_id"), "manager_id should be present in the log record"
        assert getattr(plugin_call_log, "manager_id") == target_device.oob_manager_id

        assert hasattr(plugin_call_log, "class_name"), "class_name should be present in the log record"
        assert getattr(plugin_call_log, "class_name") == test_util.DummyOOBPlugin.__name__

        assert hasattr(plugin_call_log, "method_name"), "method_name should be present in the log record"
        assert getattr(plugin_call_log, "method_name") == "post_power_on"

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
            {
                "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                "device_type": test_util.DummyDeviceInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.OFF.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.PluginGetInstanceHWControlError, exc.PluginGetInstanceHWControlError),
            (exc.ConfigurationHWControlError, exc.ConfigurationHWControlError),
            (exc.UnexpectedExceptionHWControlError, exc.UnexpectedExceptionHWControlError),
        ],
    )
    def test_plugin_manager_raise(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_raise: type[Exception],
        expected_raise: type[Exception],
    ):
        """Test plugin manager raise case.

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.

            power_control_target_device_fixture (control_base.PowerControlTargetDevice):
                The fixture used to create a target PowerControlTargetDevice object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", side_effect=plugin_raise)
        mocker.patch.object(test_util.DummyOOBPlugin, "post_power_on", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            OOBController.power_on(target_device=target_device)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
            {
                "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                "device_type": test_util.DummyDeviceInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.OFF.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.PowerOnFailureHWControlError, exc.PowerOnFailureHWControlError),
            (RuntimeError, exc.UnexpectedExceptionHWControlError),
        ],
    )
    def test_plugin_raise(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_raise: type[Exception],
        expected_raise: type[Exception],
    ):
        """Test OOB plugin raise case.

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.

            power_control_target_device_fixture (control_base.PowerControlTargetDevice):
                The fixture used to create a target PowerControlTargetDevice object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", return_value=test_util.DummyOOBPlugin())
        mocker.patch.object(test_util.DummyOOBPlugin, "post_power_on", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            OOBController.power_on(target_device)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
            {
                "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                "device_type": test_util.DummyDeviceInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.OFF.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.DeviceNotFoundHWControlError, exc.DeviceNotFoundHWControlError),
        ],
    )
    def test_plugin_raise_not_found_error(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_raise: type[exc.DeviceNotFoundHWControlError],
        expected_raise: type[exc.DeviceNotFoundHWControlError],
    ):
        """Test OOB plugin raise case.

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.

            power_control_target_device_fixture (control_base.PowerControlTargetDevice):
                The fixture used to create a target PowerControlTargetDevice object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture

        # Set up the expected value.
        expected_error_message = (
            f"The specified target device is not found. The target Device ID is follow: {target_device.device_id}"
        )

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", return_value=test_util.DummyOOBPlugin())
        mocker.patch.object(test_util.DummyOOBPlugin, "post_power_on", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise) as e:
            OOBController.power_on(target_device)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        raised_exception = cast(exc.DeviceNotFoundHWControlError, e.value)
        assert raised_exception.message == expected_error_message


class TestForceOff:
    """Unit test class for OOBController.force_off."""

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
            {
                "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                "device_type": test_util.DummyDeviceInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.OFF.value,
            },
        ],
        indirect=True,
    )
    def test_successful_case(
        self,
        caplog: LogCaptureFixture,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
    ):
        """test successful case

        Args:
            caplog (LogCaptureFixture):
                The fixture used to capture log messages.

            mocker (MockFixture):
                Fixture for creating mock objects.

            power_control_target_device_fixture (control_base.PowerControlTargetDevice):
                The fixture used to create a target PowerControlTargetDevice object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", return_value=test_util.DummyOOBPlugin())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=oob_control.__name__):
            OOBController.force_off(target_device)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        # Inspection: Check the plugin call log
        plugin_call_log = caplog.records[0]
        assert plugin_call_log.levelname == "INFO"
        assert plugin_call_log.getMessage() == "Request device power off to OOB plugin."

        assert hasattr(plugin_call_log, "manager_type"), "manager_type should be present in the log record"
        assert getattr(plugin_call_log, "manager_type") == "OOB"

        assert hasattr(plugin_call_log, "manager_id"), "manager_id should be present in the log record"
        assert getattr(plugin_call_log, "manager_id") == target_device.oob_manager_id

        assert hasattr(plugin_call_log, "class_name"), "class_name should be present in the log record"
        assert getattr(plugin_call_log, "class_name") == test_util.DummyOOBPlugin.__name__

        assert hasattr(plugin_call_log, "method_name"), "method_name should be present in the log record"
        assert getattr(plugin_call_log, "method_name") == "post_power_off"

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
            {
                "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                "device_type": test_util.DummyDeviceInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.OFF.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.PluginGetInstanceHWControlError, exc.PluginGetInstanceHWControlError),
            (exc.ConfigurationHWControlError, exc.ConfigurationHWControlError),
            (exc.UnexpectedExceptionHWControlError, exc.UnexpectedExceptionHWControlError),
        ],
    )
    def test_plugin_manager_raise(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture,
        plugin_raise: type[Exception],
        expected_raise: type[Exception],
    ):
        """Test OOB plugin raise case.

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.

            power_control_target_device_fixture (control_base.PowerControlTargetDevice):
                The fixture used to create a target PowerControlTargetDevice object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            OOBController.force_off(target_device=target_device)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.PowerOnFailureHWControlError, exc.PowerOnFailureHWControlError),
            (RuntimeError, exc.UnexpectedExceptionHWControlError),
        ],
    )
    def test_plugin_raise(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_raise: type[Exception],
        expected_raise: type[Exception],
    ):
        """Test OOB plugin raise case.

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.

            power_control_target_device_fixture (control_base.PowerControlTargetDevice):
                The fixture used to create a target PowerControlTargetDevice object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", return_value=test_util.DummyOOBPlugin())
        mocker.patch.object(test_util.DummyOOBPlugin, "post_power_off", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            OOBController.force_off(target_device)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.DeviceNotFoundHWControlError, exc.DeviceNotFoundHWControlError),
        ],
    )
    def test_plugin_raise_not_found_error(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_raise: type[exc.DeviceNotFoundHWControlError],
        expected_raise: type[exc.DeviceNotFoundHWControlError],
    ):
        """Test OOB plugin raise case.

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.

            power_control_target_device_fixture (control_base.PowerControlTargetDevice):
                The fixture used to create a target PowerControlTargetDevice object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture

        # Set up the expected value.
        expected_error_message = (
            f"The specified target device is not found. The target Device ID is follow: {target_device.device_id}"
        )

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", return_value=test_util.DummyOOBPlugin())
        mocker.patch.object(test_util.DummyOOBPlugin, "post_power_off", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise) as e:
            OOBController.force_off(target_device)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        raised_exception = cast(exc.DeviceNotFoundHWControlError, e.value)
        assert raised_exception.message == expected_error_message


class TestReset:
    """Unit test class for OOBController.reset."""

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
        ],
        indirect=True,
    )
    def test_successful_case(
        self,
        caplog: LogCaptureFixture,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
    ):
        """test successful case

        Args:
            caplog (LogCaptureFixture):
                The fixture used to capture log messages.

            mocker (MockFixture):
                Fixture for creating mock objects.

            power_control_target_device_fixture (control_base.PowerControlTargetDevice):
                The fixture used to create a target PowerControlTargetDevice object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", return_value=test_util.DummyOOBPlugin())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=oob_control.__name__):
            OOBController.reset(target_device)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        # Inspection: Check the plugin call log
        plugin_call_log = caplog.records[0]
        assert plugin_call_log.levelname == "INFO"
        assert plugin_call_log.getMessage() == "Request Host CPU reset to OOB plugin."

        assert hasattr(plugin_call_log, "manager_type"), "manager_type should be present in the log record"
        assert getattr(plugin_call_log, "manager_type") == "OOB"

        assert hasattr(plugin_call_log, "manager_id"), "manager_id should be present in the log record"
        assert getattr(plugin_call_log, "manager_id") == target_device.oob_manager_id

        assert hasattr(plugin_call_log, "class_name"), "class_name should be present in the log record"
        assert getattr(plugin_call_log, "class_name") == test_util.DummyOOBPlugin.__name__

        assert hasattr(plugin_call_log, "method_name"), "method_name should be present in the log record"
        assert getattr(plugin_call_log, "method_name") == "post_cpu_reset"

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                "device_type": test_util.DummyDeviceInfo.DEVICE_TYPE.value,  # The Device type is not "CPU".
                "oob_manager_id": test_util.DummyDeviceInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyDeviceInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.UNKNOWN.value,
            },
        ],
        indirect=True,
    )
    def test_device_type_error_case(
        self, mocker: MockFixture, power_control_target_device_fixture: control_base.PowerControlTargetDevice
    ):
        """Test invalid device type case.

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.

            power_control_target_device_fixture (control_base.PowerControlTargetDevice):
                The fixture used to create a target PowerControlTargetDevice object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", return_value=test_util.DummyOOBPlugin())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            OOBController.reset(target_device)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_manager_raise, expected_raise",
        [
            (exc.PluginGetInstanceHWControlError, exc.PluginGetInstanceHWControlError),
            (exc.ConfigurationHWControlError, exc.ConfigurationHWControlError),
            (exc.UnexpectedExceptionHWControlError, exc.UnexpectedExceptionHWControlError),
        ],
    )
    def test_plugin_manager_raise(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_manager_raise: type[Exception],
        expected_raise: type[Exception],
    ):
        """Test plugin manager raise case.

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.

            power_control_target_device_fixture (control_base.PowerControlTargetDevice):
                The fixture used to create a target PowerControlTargetDevice object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", side_effect=plugin_manager_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            OOBController.reset(target_device=target_device)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.PowerOnFailureHWControlError, exc.PowerOnFailureHWControlError),
            (RuntimeError, exc.UnexpectedExceptionHWControlError),
        ],
    )
    def test_plugin_raise(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_raise: type[Exception],
        expected_raise: type[Exception],
    ):
        """Test OOB plugin raise case.

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.

            power_control_target_device_fixture (control_base.PowerControlTargetDevice):
                The fixture used to create a target PowerControlTargetDevice object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", return_value=test_util.DummyOOBPlugin())
        mocker.patch.object(test_util.DummyOOBPlugin, "post_cpu_reset", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            OOBController.reset(target_device)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.DeviceNotFoundHWControlError, exc.DeviceNotFoundHWControlError),
        ],
    )
    def test_plugin_raise_not_found_error(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_raise: type[exc.DeviceNotFoundHWControlError],
        expected_raise: type[exc.DeviceNotFoundHWControlError],
    ):
        """Test OOB plugin raise case.

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.

            power_control_target_device_fixture (control_base.PowerControlTargetDevice):
                The fixture used to create a target PowerControlTargetDevice object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture

        # Set up the expected value.
        expected_error_message = (
            f"The specified target device is not found. The target Device ID is follow: {target_device.device_id}"
        )

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", return_value=test_util.DummyOOBPlugin())
        mocker.patch.object(test_util.DummyOOBPlugin, "post_cpu_reset", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise) as e:
            OOBController.reset(target_device)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        raised_exception = cast(exc.DeviceNotFoundHWControlError, e.value)
        assert raised_exception.message == expected_error_message


class TestPowerOff:
    """Unit test class for OOBController.power_off."""

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
        ],
        indirect=True,
    )
    def test_successful_shutdown_case(
        self,
        caplog: LogCaptureFixture,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
    ):
        """test shutdown successful case

        Args:
            caplog (LogCaptureFixture):
                The fixture used to capture log messages.

            mocker (MockFixture):
                Fixture for creating mock objects.

            power_control_target_device_fixture (control_base.PowerControlTargetDevice):
                The fixture used to create a target PowerControlTargetDevice object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", return_value=test_util.DummyOOBPlugin())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=oob_control.__name__):
            OOBController.power_off(target_device)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        # Inspection: Check the plugin call log
        plugin_call_log = caplog.records[0]
        assert plugin_call_log.levelname == "INFO"
        assert plugin_call_log.getMessage() == "Request Host CPU shutdown to OOB plugin."

        assert hasattr(plugin_call_log, "manager_type"), "manager_type should be present in the log record"
        assert getattr(plugin_call_log, "manager_type") == "OOB"

        assert hasattr(plugin_call_log, "manager_id"), "manager_id should be present in the log record"
        assert getattr(plugin_call_log, "manager_id") == target_device.oob_manager_id

        assert hasattr(plugin_call_log, "class_name"), "class_name should be present in the log record"
        assert getattr(plugin_call_log, "class_name") == test_util.DummyOOBPlugin.__name__

        assert hasattr(plugin_call_log, "method_name"), "method_name should be present in the log record"
        assert getattr(plugin_call_log, "method_name") == "post_os_shutdown"

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                "device_type": test_util.DummyDeviceInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyDeviceInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyDeviceInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.UNKNOWN.value,
            },
        ],
        indirect=True,
    )
    def test_successful_power_off_case(
        self,
        caplog: LogCaptureFixture,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
    ):
        """test power off successful case

        Args:
            caplog (LogCaptureFixture):
                The fixture used to capture log messages.

            mocker (MockFixture):
                Fixture for creating mock objects.

            power_control_target_device_fixture (control_base.PowerControlTargetDevice):
                The fixture used to create a target PowerControlTargetDevice object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", return_value=test_util.DummyOOBPlugin())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=oob_control.__name__):
            OOBController.power_off(target_device)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        # Inspection: Check the plugin call log
        plugin_call_log = caplog.records[0]
        assert plugin_call_log.levelname == "INFO"
        assert plugin_call_log.getMessage() == "Request device power off to OOB plugin."

        assert hasattr(plugin_call_log, "manager_type"), "manager_type should be present in the log record"
        assert getattr(plugin_call_log, "manager_type") == "OOB"

        assert hasattr(plugin_call_log, "manager_id"), "manager_id should be present in the log record"
        assert getattr(plugin_call_log, "manager_id") == target_device.oob_manager_id

        assert hasattr(plugin_call_log, "class_name"), "class_name should be present in the log record"
        assert getattr(plugin_call_log, "class_name") == test_util.DummyOOBPlugin.__name__

        assert hasattr(plugin_call_log, "method_name"), "method_name should be present in the log record"
        assert getattr(plugin_call_log, "method_name") == "post_power_off"

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.UNKNOWN.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_manager_raise, expected_raise",
        [
            (exc.PluginGetInstanceHWControlError, exc.PluginGetInstanceHWControlError),
            (exc.ConfigurationHWControlError, exc.ConfigurationHWControlError),
            (exc.UnexpectedExceptionHWControlError, exc.UnexpectedExceptionHWControlError),
        ],
    )
    def test_plugin_manager_raise(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_manager_raise: type[Exception],
        expected_raise: type[Exception],
    ):
        """Test plugin manager raise case.

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.

            power_control_target_device_fixture (control_base.PowerControlTargetDevice):
                The fixture used to create a target PowerControlTargetDevice object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", side_effect=plugin_manager_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            OOBController.reset(target_device=target_device)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.PowerOnFailureHWControlError, exc.PowerOnFailureHWControlError),
            (RuntimeError, exc.UnexpectedExceptionHWControlError),
        ],
    )
    def test_plugin_shutdown_method_raise_case(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_raise: type[Exception],
        expected_raise: type[Exception],
    ):
        """Test OOB plugin shutdown method raise case.

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.

            power_control_target_device_fixture (control_base.PowerControlTargetDevice):
                The fixture used to create a target PowerControlTargetDevice object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input value.
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", return_value=test_util.DummyOOBPlugin())
        mocker.patch.object(test_util.DummyOOBPlugin, "post_os_shutdown", side_effect=plugin_raise)
        mocker.patch.object(test_util.DummyOOBPlugin, "post_power_off", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            OOBController.power_off(target_device)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCPUInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.DeviceNotFoundHWControlError, exc.DeviceNotFoundHWControlError),
        ],
    )
    def test_plugin_shutdown_method_raise_not_found_error(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_raise: type[exc.DeviceNotFoundHWControlError],
        expected_raise: type[exc.DeviceNotFoundHWControlError],
    ):
        """Test OOB plugin shutdown method raise not found error case.

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.

            power_control_target_device_fixture (control_base.PowerControlTargetDevice):
                The fixture used to create a target PowerControlTargetDevice object.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input value.
        target_device = power_control_target_device_fixture

        # Set up the expected value.
        expected_error_message = (
            "The specified target device is not found." f" The target Device ID is follow: {target_device.device_id}"
        )

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", return_value=test_util.DummyOOBPlugin())
        mocker.patch.object(test_util.DummyOOBPlugin, "post_os_shutdown", side_effect=plugin_raise)
        mocker.patch.object(test_util.DummyOOBPlugin, "post_power_off", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise) as e:
            OOBController.power_off(target_device)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        raised_exception = cast(exc.DeviceNotFoundHWControlError, e.value)
        assert raised_exception.message == expected_error_message

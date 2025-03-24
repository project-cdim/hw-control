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

"""Unit test module for OobController class ."""

import json
import logging
from typing import cast

import pytest
from pytest_mock import MockFixture

from tests.app.core.control import test_util

from app.common import constants  # type: ignore
import app.common.basic_exceptions as exc  # type: ignore
from app.common.utils import plugin_manager  # type: ignore
from app.core.control import control_base  # type: ignore

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.core.control.oob_control import OobController  # type: ignore

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestPowerOn:
    """Unit test class for OobController.power_off."""

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
            {
                "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                "device_type": test_util.DummyDeviceInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.OFF.value,
            },
        ],
        indirect=True,
    )
    def test_successful_case(self, caplog, mocker: MockFixture, power_control_target_device_fixture):
        """test successful case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="LOGGER"):
            OobController.power_on(target_device)

        plugin_call_log_message = json.loads(caplog.records[0].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        assert caplog.records[0].levelname == "INFO"
        assert plugin_call_log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert plugin_call_log_message["message"]["detail"] is None
        assert plugin_call_log_message["message"]["action"] == "plugin call"
        assert plugin_call_log_message["message"]["manager_type"] == "OOB"
        assert plugin_call_log_message["message"]["manager_id"] == target_device.oob_manager_id
        assert plugin_call_log_message["message"]["class_name"] == "DummyPlugin"
        assert plugin_call_log_message["message"]["method_name"] == "post_power_on"

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
            {
                "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                "device_type": test_util.DummyDeviceInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.OFF.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.PluginGetInstanceHwControlError, exc.PluginGetInstanceHwControlError),
            (exc.ConfigurationHwControlError, exc.ConfigurationHwControlError),
            (exc.UnexpectedExceptionHwControlError, exc.UnexpectedExceptionHwControlError),
        ],
    )
    def test_plugin_manager_raise(
        self, mocker: MockFixture, power_control_target_device_fixture, plugin_raise, expected_raise
    ):
        """Test plugin manager raise case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", side_effect=plugin_raise)
        mocker.patch.object(test_util.DummyPlugin, "post_power_on", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            OobController.power_on(target_device=target_device)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
            {
                "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                "device_type": test_util.DummyDeviceInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.OFF.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.PowerOnFailureHwControlError, exc.PowerOnFailureHwControlError),
            (RuntimeError, exc.UnexpectedExceptionHwControlError),
        ],
    )
    def test_plugin_raise(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_raise: exc.BaseHwControlError,
        expected_raise: exc.BaseHwControlError,
    ):
        """Test OOB plugin raise case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())
        mocker.patch.object(test_util.DummyPlugin, "post_power_on", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            OobController.power_on(target_device)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
            {
                "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                "device_type": test_util.DummyDeviceInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.OFF.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.DeviceNotFoundHwControlError, exc.DeviceNotFoundHwControlError),
        ],
    )
    def test_plugin_raise_not_found_error(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_raise: exc.DeviceNotFoundHwControlError,
        expected_raise: exc.DeviceNotFoundHwControlError,
    ):
        """Test OOB plugin raise case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture

        # Set up the expected value.
        expected_error_message = (
            f"The specified target device is not found. The target Device ID is follow: {target_device.device_id}"
        )

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())
        mocker.patch.object(test_util.DummyPlugin, "post_power_on", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise) as e:
            OobController.power_on(target_device)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        raised_exception = cast(exc.DeviceNotFoundHwControlError, e.value)
        assert raised_exception.message == expected_error_message


class TestForceOff:
    """Unit test class for OobController.force_off."""

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
            {
                "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                "device_type": test_util.DummyDeviceInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.OFF.value,
            },
        ],
        indirect=True,
    )
    def test_successful_case(self, caplog, mocker: MockFixture, power_control_target_device_fixture):
        """test successful case

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="LOGGER"):
            OobController.force_off(target_device)

        plugin_call_log_message = json.loads(caplog.records[0].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        assert caplog.records[0].levelname == "INFO"
        assert plugin_call_log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert plugin_call_log_message["message"]["detail"] is None
        assert plugin_call_log_message["message"]["action"] == "plugin call"
        assert plugin_call_log_message["message"]["manager_type"] == "OOB"
        assert plugin_call_log_message["message"]["manager_id"] == target_device.oob_manager_id
        assert plugin_call_log_message["message"]["class_name"] == "DummyPlugin"
        assert plugin_call_log_message["message"]["method_name"] == "post_power_off"

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
            {
                "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                "device_type": test_util.DummyDeviceInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.OFF.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.PluginGetInstanceHwControlError, exc.PluginGetInstanceHwControlError),
            (exc.ConfigurationHwControlError, exc.ConfigurationHwControlError),
            (exc.UnexpectedExceptionHwControlError, exc.UnexpectedExceptionHwControlError),
        ],
    )
    def test_plugin_manager_raise(
        self, mocker: MockFixture, power_control_target_device_fixture, plugin_raise, expected_raise
    ):
        """Test OOB plugin raise case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            OobController.force_off(target_device=target_device)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.PowerOnFailureHwControlError, exc.PowerOnFailureHwControlError),
            (RuntimeError, exc.UnexpectedExceptionHwControlError),
        ],
    )
    def test_plugin_raise(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_raise: exc.BaseHwControlError,
        expected_raise: exc.BaseHwControlError,
    ):
        """Test OOB plugin raise case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())
        mocker.patch.object(test_util.DummyPlugin, "post_power_off", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            OobController.force_off(target_device)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.DeviceNotFoundHwControlError, exc.DeviceNotFoundHwControlError),
        ],
    )
    def test_plugin_raise_not_found_error(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_raise: exc.DeviceNotFoundHwControlError,
        expected_raise: exc.DeviceNotFoundHwControlError,
    ):
        """Test OOB plugin raise case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture

        # Set up the expected value.
        expected_error_message = (
            f"The specified target device is not found. The target Device ID is follow: {target_device.device_id}"
        )

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())
        mocker.patch.object(test_util.DummyPlugin, "post_power_off", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise) as e:
            OobController.force_off(target_device)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        raised_exception = cast(exc.DeviceNotFoundHwControlError, e.value)
        assert raised_exception.message == expected_error_message


class TestReset:
    """Unit test class for OobController.reset."""

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
        ],
        indirect=True,
    )
    def test_successful_case(self, caplog, mocker: MockFixture, power_control_target_device_fixture):
        """test successful case

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="LOGGER"):
            OobController.reset(target_device)

        plugin_call_log_message = json.loads(caplog.records[0].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        assert caplog.records[0].levelname == "INFO"
        assert plugin_call_log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert plugin_call_log_message["message"]["detail"] is None
        assert plugin_call_log_message["message"]["action"] == "plugin call"
        assert plugin_call_log_message["message"]["manager_type"] == "OOB"
        assert plugin_call_log_message["message"]["manager_id"] == target_device.oob_manager_id
        assert plugin_call_log_message["message"]["class_name"] == "DummyPlugin"
        assert plugin_call_log_message["message"]["method_name"] == "post_cpu_reset"

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
    def test_device_type_error_case(self, mocker: MockFixture, power_control_target_device_fixture):
        """Test invalid device type case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHwControlError):
            OobController.reset(target_device)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_manager_raise, expected_raise",
        [
            (exc.PluginGetInstanceHwControlError, exc.PluginGetInstanceHwControlError),
            (exc.ConfigurationHwControlError, exc.ConfigurationHwControlError),
            (exc.UnexpectedExceptionHwControlError, exc.UnexpectedExceptionHwControlError),
        ],
    )
    def test_plugin_manager_raise(
        self, mocker: MockFixture, power_control_target_device_fixture, plugin_manager_raise, expected_raise
    ):
        """Test plugin manager raise case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", side_effect=plugin_manager_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            OobController.reset(target_device=target_device)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.PowerOnFailureHwControlError, exc.PowerOnFailureHwControlError),
            (RuntimeError, exc.UnexpectedExceptionHwControlError),
        ],
    )
    def test_plugin_raise(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_raise: exc.BaseHwControlError,
        expected_raise: exc.BaseHwControlError,
    ):
        """Test OOB plugin raise case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())
        mocker.patch.object(test_util.DummyPlugin, "post_cpu_reset", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            OobController.reset(target_device)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.DeviceNotFoundHwControlError, exc.DeviceNotFoundHwControlError),
        ],
    )
    def test_plugin_raise_not_found_error(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_raise: exc.DeviceNotFoundHwControlError,
        expected_raise: exc.DeviceNotFoundHwControlError,
    ):
        """Test OOB plugin raise case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture

        # Set up the expected value.
        expected_error_message = (
            f"The specified target device is not found. The target Device ID is follow: {target_device.device_id}"
        )

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())
        mocker.patch.object(test_util.DummyPlugin, "post_cpu_reset", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise) as e:
            OobController.reset(target_device)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        raised_exception = cast(exc.DeviceNotFoundHwControlError, e.value)
        assert raised_exception.message == expected_error_message


class TestPowerOff:
    """Unit test class for OobController.power_off."""

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
        ],
        indirect=True,
    )
    def test_successful_shutdown_case(self, caplog, mocker: MockFixture, power_control_target_device_fixture):
        """test shutdown successful case

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="LOGGER"):
            OobController.power_off(target_device)

        plugin_call_log_message = json.loads(caplog.records[0].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        assert caplog.records[0].levelname == "INFO"
        assert plugin_call_log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert plugin_call_log_message["message"]["detail"] is None
        assert plugin_call_log_message["message"]["action"] == "plugin call"
        assert plugin_call_log_message["message"]["manager_type"] == "OOB"
        assert plugin_call_log_message["message"]["manager_id"] == target_device.oob_manager_id
        assert plugin_call_log_message["message"]["class_name"] == "DummyPlugin"
        assert plugin_call_log_message["message"]["method_name"] == "post_os_shutdown"

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
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
    def test_successful_power_off_case(self, caplog, mocker: MockFixture, power_control_target_device_fixture):
        """test power off successful case

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="LOGGER"):
            OobController.power_off(target_device)

        plugin_call_log_message = json.loads(caplog.records[0].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        assert caplog.records[0].levelname == "INFO"
        assert plugin_call_log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert plugin_call_log_message["message"]["detail"] is None
        assert plugin_call_log_message["message"]["action"] == "plugin call"
        assert plugin_call_log_message["message"]["manager_type"] == "OOB"
        assert plugin_call_log_message["message"]["manager_id"] == target_device.oob_manager_id
        assert plugin_call_log_message["message"]["class_name"] == "DummyPlugin"
        assert plugin_call_log_message["message"]["method_name"] == "post_power_off"

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.UNKNOWN.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_manager_raise, expected_raise",
        [
            (exc.PluginGetInstanceHwControlError, exc.PluginGetInstanceHwControlError),
            (exc.ConfigurationHwControlError, exc.ConfigurationHwControlError),
            (exc.UnexpectedExceptionHwControlError, exc.UnexpectedExceptionHwControlError),
        ],
    )
    def test_plugin_manager_raise(
        self, mocker: MockFixture, power_control_target_device_fixture, plugin_manager_raise, expected_raise
    ):
        """Test plugin manager raise case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", side_effect=plugin_manager_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            OobController.reset(target_device=target_device)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.PowerOnFailureHwControlError, exc.PowerOnFailureHwControlError),
            (RuntimeError, exc.UnexpectedExceptionHwControlError),
        ],
    )
    def test_plugin_shutdown_method_raise_case(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_raise: exc.BaseHwControlError,
        expected_raise: exc.BaseHwControlError,
    ):
        """Test OOB plugin shutdown method raise case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input value.
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())
        mocker.patch.object(test_util.DummyPlugin, "post_os_shutdown", side_effect=plugin_raise)
        mocker.patch.object(test_util.DummyPlugin, "post_power_off", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            OobController.power_off(target_device)

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {
                "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                "device_type": test_util.DummyCpuInfo.DEVICE_TYPE.value,
                "oob_manager_id": test_util.DummyCpuInfo.OOB_MANAGER_ID.value,
                "oob_device_id": test_util.DummyCpuInfo.OOB_DEVICE_ID.value,
                "power_state": constants.DevicePowerState.ON.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            (exc.DeviceNotFoundHwControlError, exc.DeviceNotFoundHwControlError),
        ],
    )
    def test_plugin_shutdown_method_raise_not_found_error(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: control_base.PowerControlTargetDevice,
        plugin_raise: exc.DeviceNotFoundHwControlError,
        expected_raise: exc.DeviceNotFoundHwControlError,
    ):
        """Test OOB plugin shutdown method raise not found error case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input value.
        target_device = power_control_target_device_fixture

        # Set up the expected value.
        expected_error_message = (
            "The specified target device is not found." f" The target Device ID is follow: {target_device.device_id}"
        )

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())
        mocker.patch.object(test_util.DummyPlugin, "post_os_shutdown", side_effect=plugin_raise)
        mocker.patch.object(test_util.DummyPlugin, "post_power_off", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise) as e:
            OobController.power_off(target_device)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        raised_exception = cast(exc.DeviceNotFoundHwControlError, e.value)
        assert raised_exception.message == expected_error_message

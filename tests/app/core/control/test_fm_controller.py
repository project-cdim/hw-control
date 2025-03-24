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

"""Unit test module for FmController class ."""

import json
import logging
from typing import cast

import pytest
from pytest_mock import MockFixture

from tests.app.core.control import test_util


import app.common.basic_exceptions as exc  # type: ignore
from app.common import constants
from app.common.utils import plugin_manager  # type: ignore
from app.core.control.fm_control import FmControlTargetDevicePair  # type: ignore

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++#
from app.core.control.fm_control import FmController

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestConnect:
    """Unit test class for FmController.power_control.connect"""

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device pair object
                    # host_cpu parameter
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "host_cpu_switch_port_type": constants.SwitchPortType.USP.value,
                    "host_cpu_fm_manager_id": "test_fm_manager_id",
                    # target_device parameter
                    "target_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "target_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "target_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    def test_successful_case(
        self, caplog, mocker: MockFixture, fm_control_target_device_pair_fixture: FmControlTargetDevicePair
    ):
        """test successful case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="LOGGER"):
            FmController.connect(device_pair=test_device_pair)

        plugin_call_log_message = json.loads(caplog.records[0].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        assert caplog.records[0].levelname == "INFO"
        assert plugin_call_log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert plugin_call_log_message["message"]["action"] == "plugin call"
        assert plugin_call_log_message["message"]["manager_type"] == "FM"
        assert plugin_call_log_message["message"]["manager_id"] == test_device_pair.host_cpu.fm_manager_id
        assert plugin_call_log_message["message"]["class_name"] == "DummyPlugin"
        assert plugin_call_log_message["message"]["method_name"] == "connect"

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (  # host_cpu.switch_port_type is not "USP"
                {  # input device pair object
                    # host_cpu parameter
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "host_cpu_switch_port_type": constants.SwitchPortType.DSP.value,
                    "host_cpu_fm_manager_id": "test_fm_manager_id",
                    # target_device parameter
                    "target_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "target_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "target_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
            (  # target_device.switch_port_type is not "DSP"
                {  # input device pair object
                    # host_cpu parameter
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "host_cpu_switch_port_type": constants.SwitchPortType.USP.value,
                    "host_cpu_fm_manager_id": "test_fm_manager_id",
                    # target_device parameter
                    "target_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "target_device_switch_port_type": constants.SwitchPortType.USP.value,
                    "target_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
            (  # host_cpu.fm_manager_id not match target_device.fm_manager_id
                {  # input device pair object
                    # host_cpu parameter
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "host_cpu_switch_port_type": constants.SwitchPortType.USP.value,
                    "host_cpu_fm_manager_id": "foo",
                    # target_device parameter
                    "target_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "target_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "target_device_fm_manager_id": "bar",
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    def test_invalid_device_pair_input(
        self,
        fm_control_target_device_pair_fixture: FmControlTargetDevicePair,
    ):
        """test plugin raise error case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHwControlError):
            FmController.connect(device_pair=test_device_pair)

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device pair object
                    # host_cpu parameter
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "host_cpu_switch_port_type": constants.SwitchPortType.USP.value,
                    "host_cpu_fm_manager_id": "test_fm_manager_id",
                    # target_device parameter
                    "target_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "target_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "target_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
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
        self,
        mocker: MockFixture,
        fm_control_target_device_pair_fixture: FmControlTargetDevicePair,
        plugin_manager_raise,
        expected_raise,
    ):
        """test plugin raise error case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", side_effect=plugin_manager_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            FmController.connect(device_pair=test_device_pair)

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device object
                    # host_cpu parameter
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "host_cpu_switch_port_type": constants.SwitchPortType.USP.value,
                    "host_cpu_fm_manager_id": "test_fm_manager_id",
                    # target_device parameter
                    "target_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "target_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "target_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            # plugin raise Unexpected Exception case
            (RuntimeError, exc.UnexpectedExceptionHwControlError),
            (Exception, exc.UnexpectedExceptionHwControlError),
            # plugin raise expected Exception case
            (exc.FmConnectFailureHwControlError, exc.FmConnectFailureHwControlError),
            (exc.AuthenticationHwControlError, exc.AuthenticationHwControlError),
        ],
    )
    def test_plugin_raise(
        self,
        mocker: MockFixture,
        fm_control_target_device_pair_fixture: FmControlTargetDevicePair,
        plugin_raise,
        expected_raise,
    ):
        """test plugin raise error case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())
        mocker.patch.object(test_util.DummyPlugin, "connect", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            FmController.connect(device_pair=test_device_pair)

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device object
                    # host_cpu parameter
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "host_cpu_switch_port_type": constants.SwitchPortType.USP.value,
                    "host_cpu_fm_manager_id": "test_fm_manager_id",
                    # target_device parameter
                    "target_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "target_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "target_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise, expected_error_message",
        [
            # plugin raise expected Exception case
            (
                exc.HostCpuAndDeviceNotFoundHwControlError,
                exc.HostCpuAndDeviceNotFoundHwControlError,
                (
                    "The specified Host CPU and target device are not found. The target Device IDs are follow: "
                    f"{test_util.DummyCpuInfo.DEVICE_ID.value}, {test_util.DummyDeviceInfo.DEVICE_ID.value}"
                ),
            ),
            (
                exc.HostCpuNotFoundHwControlError,
                exc.HostCpuNotFoundHwControlError,
                (
                    "The specified Host CPU is not found."
                    f" The target Device ID is follow: {test_util.DummyCpuInfo.DEVICE_ID.value}"
                ),
            ),
            (
                exc.DeviceNotFoundHwControlError,
                exc.DeviceNotFoundHwControlError,
                (
                    "The specified target device is not found."
                    f" The target Device ID is follow: {test_util.DummyDeviceInfo.DEVICE_ID.value}"
                ),
            ),
        ],
    )
    def test_plugin_raise_not_found_error(  # pylint: disable=R0913
        self,
        mocker: MockFixture,
        fm_control_target_device_pair_fixture: FmControlTargetDevicePair,
        plugin_raise: exc.DeviceNotFoundHwControlError,
        expected_raise: exc.DeviceNotFoundHwControlError,
        expected_error_message: str,
    ):
        """Test plugin raise error device not found case error."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())
        mocker.patch.object(test_util.DummyPlugin, "connect", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise) as e:
            FmController.connect(device_pair=test_device_pair)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        raised_exception = cast(exc.DeviceNotFoundHwControlError, e.value)
        assert raised_exception.message == expected_error_message


class TestDisconnect:
    """Unit test class for FmController.power_control.disconnect"""

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device pair object
                    # host_cpu parameter
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "host_cpu_switch_port_type": constants.SwitchPortType.USP.value,
                    "host_cpu_fm_manager_id": "test_fm_manager_id",
                    # target_device parameter
                    "target_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "target_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "target_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    def test_successful_case(
        self, caplog, mocker: MockFixture, fm_control_target_device_pair_fixture: FmControlTargetDevicePair
    ):
        """test successful case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="LOGGER"):
            FmController.disconnect(device_pair=test_device_pair)

        plugin_call_log_message = json.loads(caplog.records[0].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        assert caplog.records[0].levelname == "INFO"
        assert plugin_call_log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert plugin_call_log_message["message"]["action"] == "plugin call"
        assert plugin_call_log_message["message"]["manager_type"] == "FM"
        assert plugin_call_log_message["message"]["manager_id"] == test_device_pair.host_cpu.fm_manager_id
        assert plugin_call_log_message["message"]["class_name"] == "DummyPlugin"
        assert plugin_call_log_message["message"]["method_name"] == "disconnect"

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (  # host_cpu.switch_port_type is not "USP"
                {  # input device pair object
                    # host_cpu parameter
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "host_cpu_switch_port_type": constants.SwitchPortType.DSP.value,
                    "host_cpu_fm_manager_id": "test_fm_manager_id",
                    # target_device parameter
                    "target_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "target_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "target_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
            (  # target_device.switch_port_type is not "DSP"
                {  # input device pair object
                    # host_cpu parameter
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "host_cpu_switch_port_type": constants.SwitchPortType.USP.value,
                    "host_cpu_fm_manager_id": "test_fm_manager_id",
                    # target_device parameter
                    "target_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "target_device_switch_port_type": constants.SwitchPortType.USP.value,
                    "target_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
            (  # host_cpu.fm_manager_id not match target_device.fm_manager_id
                {  # input device pair object
                    # host_cpu parameter
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "host_cpu_switch_port_type": constants.SwitchPortType.USP.value,
                    "host_cpu_fm_manager_id": "foo",
                    # target_device parameter
                    "target_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "target_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "target_device_fm_manager_id": "bar",
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    def test_invalid_device_pair_input(
        self,
        fm_control_target_device_pair_fixture: FmControlTargetDevicePair,
    ):
        """test plugin raise error case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHwControlError):
            FmController.disconnect(device_pair=test_device_pair)

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device pair object
                    # host_cpu parameter
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "host_cpu_switch_port_type": constants.SwitchPortType.USP.value,
                    "host_cpu_fm_manager_id": "test_fm_manager_id",
                    # target_device parameter
                    "target_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "target_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "target_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
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
        self,
        mocker: MockFixture,
        fm_control_target_device_pair_fixture: FmControlTargetDevicePair,
        plugin_manager_raise,
        expected_raise,
    ):
        """test plugin raise error case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", side_effect=plugin_manager_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            FmController.disconnect(device_pair=test_device_pair)

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device object
                    # host_cpu parameter
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "host_cpu_switch_port_type": constants.SwitchPortType.USP.value,
                    "host_cpu_fm_manager_id": "test_fm_manager_id",
                    # target_device parameter
                    "target_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "target_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "target_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            # plugin raise Unexpected Exception case
            (RuntimeError, exc.UnexpectedExceptionHwControlError),
            (Exception, exc.UnexpectedExceptionHwControlError),
            # plugin raise expected Exception case
            (exc.FmConnectFailureHwControlError, exc.FmConnectFailureHwControlError),
            (exc.AuthenticationHwControlError, exc.AuthenticationHwControlError),
        ],
    )
    def test_plugin_raise(
        self,
        mocker: MockFixture,
        fm_control_target_device_pair_fixture: FmControlTargetDevicePair,
        plugin_raise,
        expected_raise,
    ):
        """test plugin raise error case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())
        mocker.patch.object(test_util.DummyPlugin, "disconnect", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            FmController.disconnect(device_pair=test_device_pair)

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device object
                    # host_cpu parameter
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "host_cpu_switch_port_type": constants.SwitchPortType.USP.value,
                    "host_cpu_fm_manager_id": "test_fm_manager_id",
                    # target_device parameter
                    "target_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "target_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "target_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise, expected_error_message",
        [
            # plugin raise expected Exception case
            (
                exc.HostCpuAndDeviceNotFoundHwControlError,
                exc.HostCpuAndDeviceNotFoundHwControlError,
                (
                    "The specified Host CPU and target device are not found. The target Device IDs are follow: "
                    f"{test_util.DummyCpuInfo.DEVICE_ID.value}, {test_util.DummyDeviceInfo.DEVICE_ID.value}"
                ),
            ),
            (
                exc.HostCpuNotFoundHwControlError,
                exc.HostCpuNotFoundHwControlError,
                (
                    "The specified Host CPU is not found."
                    f" The target Device ID is follow: {test_util.DummyCpuInfo.DEVICE_ID.value}"
                ),
            ),
            (
                exc.DeviceNotFoundHwControlError,
                exc.DeviceNotFoundHwControlError,
                (
                    "The specified target device is not found."
                    f" The target Device ID is follow: {test_util.DummyDeviceInfo.DEVICE_ID.value}"
                ),
            ),
        ],
    )
    def test_plugin_raise_not_found_error(  # pylint: disable=R0913
        self,
        mocker: MockFixture,
        fm_control_target_device_pair_fixture: FmControlTargetDevicePair,
        plugin_raise: exc.DeviceNotFoundHwControlError,
        expected_raise: exc.DeviceNotFoundHwControlError,
        expected_error_message: str,
    ):
        """Test plugin raise error device not found case error."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_plugin", return_value=test_util.DummyPlugin())
        mocker.patch.object(test_util.DummyPlugin, "disconnect", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise) as e:
            FmController.disconnect(device_pair=test_device_pair)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        raised_exception = cast(exc.DeviceNotFoundHwControlError, e.value)
        assert raised_exception.message == expected_error_message

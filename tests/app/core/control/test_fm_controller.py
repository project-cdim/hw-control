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

"""Unit test module for FMController class ."""

import logging
from typing import cast

import pytest
from pytest import LogCaptureFixture
from pytest_mock import MockFixture

from tests.app.core.control import test_util


import app.common.basic_exceptions as exc
from app.common import constants
from app.common.utils import plugin_manager
from app.core.control.fm_control import FMControlTargetDevicePair
from app.core.control import fm_control

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++#
from app.core.control.fm_control import FMController

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestConnect:
    """Unit test class for FMController.power_control.connect"""

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device pair object
                    # upstream_device parameter
                    "upstream_device_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "upstream_device_switch_port_type": constants.SwitchPortType.USP.value,
                    "upstream_device_fm_manager_id": "test_fm_manager_id",
                    # downstream_device parameter
                    "downstream_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "downstream_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "downstream_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    def test_successful_case(
        self,
        caplog: LogCaptureFixture,
        mocker: MockFixture,
        fm_control_target_device_pair_fixture: FMControlTargetDevicePair,
    ):
        """test successful case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_fm_plugin", return_value=test_util.DummyFMPlugin())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=fm_control.__name__):
            FMController.connect(device_pair=test_device_pair)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        # Inspection: Check the plugin call log
        plugin_call_log = caplog.records[0]
        assert plugin_call_log.levelname == "INFO"
        assert plugin_call_log.getMessage() == "Request connect upstream device and downstream device to FM plugin."

        assert hasattr(plugin_call_log, "manager_type"), "manager_type should be present in the log record"
        assert getattr(plugin_call_log, "manager_type") == "FM"

        assert hasattr(plugin_call_log, "manager_id"), "manager_id should be present in the log record"
        assert getattr(plugin_call_log, "manager_id") == test_device_pair.upstream_device.fm_manager_id

        assert hasattr(plugin_call_log, "class_name"), "class_name should be present in the log record"
        assert getattr(plugin_call_log, "class_name") == test_util.DummyFMPlugin.__name__

        assert hasattr(plugin_call_log, "method_name"), "method_name should be present in the log record"
        assert getattr(plugin_call_log, "method_name") == "connect"

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (  # upstream_device.switch_port_type is not "USP"
                {  # input device pair object
                    # upstream_device parameter
                    "upstream_device_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "upstream_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "upstream_device_fm_manager_id": "test_fm_manager_id",
                    # downstream_device parameter
                    "downstream_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "downstream_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "downstream_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
            (  # downstream_device.switch_port_type is not "DSP"
                {  # input device pair object
                    # upstream_device parameter
                    "upstream_device_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "upstream_device_switch_port_type": constants.SwitchPortType.USP.value,
                    "upstream_device_fm_manager_id": "test_fm_manager_id",
                    # downstream_device parameter
                    "downstream_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "downstream_device_switch_port_type": constants.SwitchPortType.USP.value,
                    "downstream_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
            (  # upstream_device.fm_manager_id not match downstream_device.fm_manager_id
                {  # input device pair object
                    # upstream_device parameter
                    "upstream_device_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "upstream_device_switch_port_type": constants.SwitchPortType.USP.value,
                    "upstream_device_fm_manager_id": "foo",
                    # downstream_device parameter
                    "downstream_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "downstream_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "downstream_device_fm_manager_id": "bar",
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    def test_invalid_device_pair_input(
        self,
        fm_control_target_device_pair_fixture: FMControlTargetDevicePair,
    ):
        """test plugin raise error case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            FMController.connect(device_pair=test_device_pair)

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device pair object
                    # upstream_device parameter
                    "upstream_device_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "upstream_device_switch_port_type": constants.SwitchPortType.USP.value,
                    "upstream_device_fm_manager_id": "test_fm_manager_id",
                    # downstream_device parameter
                    "downstream_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "downstream_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "downstream_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
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
        fm_control_target_device_pair_fixture: FMControlTargetDevicePair,
        plugin_manager_raise,
        expected_raise,
    ):
        """test plugin raise error case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_fm_plugin", side_effect=plugin_manager_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            FMController.connect(device_pair=test_device_pair)

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device object
                    # upstream_device parameter
                    "upstream_device_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "upstream_device_switch_port_type": constants.SwitchPortType.USP.value,
                    "upstream_device_fm_manager_id": "test_fm_manager_id",
                    # downstream_device parameter
                    "downstream_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "downstream_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "downstream_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            # plugin raise Unexpected Exception case
            (RuntimeError, exc.UnexpectedExceptionHWControlError),
            (Exception, exc.UnexpectedExceptionHWControlError),
            # plugin raise expected Exception case
            (exc.FMConnectFailureHWControlError, exc.FMConnectFailureHWControlError),
            (exc.AuthenticationHWControlError, exc.AuthenticationHWControlError),
        ],
    )
    def test_plugin_raise(
        self,
        mocker: MockFixture,
        fm_control_target_device_pair_fixture: FMControlTargetDevicePair,
        plugin_raise,
        expected_raise,
    ):
        """test plugin raise error case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_fm_plugin", return_value=test_util.DummyFMPlugin())
        mocker.patch.object(test_util.DummyFMPlugin, "connect", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            FMController.connect(device_pair=test_device_pair)

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device object
                    # upstream_device parameter
                    "upstream_device_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "upstream_device_switch_port_type": constants.SwitchPortType.USP.value,
                    "upstream_device_fm_manager_id": "test_fm_manager_id",
                    # downstream_device parameter
                    "downstream_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "downstream_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "downstream_device_fm_manager_id": "test_fm_manager_id",
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
                exc.HostCPUAndDeviceNotFoundHWControlError,
                exc.HostCPUAndDeviceNotFoundHWControlError,
                (
                    "The specified Host CPU and target device are not found. The target Device IDs are follow: "
                    f"{test_util.DummyCPUInfo.DEVICE_ID.value}, {test_util.DummyDeviceInfo.DEVICE_ID.value}"
                ),
            ),
            (
                exc.HostCPUNotFoundHWControlError,
                exc.HostCPUNotFoundHWControlError,
                (
                    "The specified Host CPU is not found."
                    f" The target Device ID is follow: {test_util.DummyCPUInfo.DEVICE_ID.value}"
                ),
            ),
            (
                exc.DeviceNotFoundHWControlError,
                exc.DeviceNotFoundHWControlError,
                (
                    "The specified target device is not found."
                    f" The target Device ID is follow: {test_util.DummyDeviceInfo.DEVICE_ID.value}"
                ),
            ),
            (
                exc.UpstreamDeviceNotFoundHWControlError,
                exc.UpstreamDeviceNotFoundHWControlError,
                (
                    "The specified target device is not found."
                    f" The target Device ID is follow: {test_util.DummyCPUInfo.DEVICE_ID.value}"
                ),
            ),
            (
                exc.DownstreamDeviceNotFoundHWControlError,
                exc.DownstreamDeviceNotFoundHWControlError,
                (
                    "The specified target device is not found."
                    f" The target Device ID is follow: {test_util.DummyDeviceInfo.DEVICE_ID.value}"
                ),
            ),
        ],
    )
    def test_plugin_raise_not_found_error(  # pylint: disable=R0913, R0917
        self,
        mocker: MockFixture,
        fm_control_target_device_pair_fixture: FMControlTargetDevicePair,
        plugin_raise: type[exc.DeviceNotFoundHWControlError],
        expected_raise: type[exc.DeviceNotFoundHWControlError],
        expected_error_message: str,
    ):
        """Test plugin raise error device not found case error."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_fm_plugin", return_value=test_util.DummyFMPlugin())
        mocker.patch.object(test_util.DummyFMPlugin, "connect", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise) as e:
            FMController.connect(device_pair=test_device_pair)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        raised_exception = cast(exc.DeviceNotFoundHWControlError, e.value)
        assert raised_exception.message == expected_error_message


class TestDisconnect:
    """Unit test class for FMController.power_control.disconnect"""

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device pair object
                    # upstream_device parameter
                    "upstream_device_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "upstream_device_switch_port_type": constants.SwitchPortType.USP.value,
                    "upstream_device_fm_manager_id": "test_fm_manager_id",
                    # downstream_device parameter
                    "downstream_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "downstream_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "downstream_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    def test_successful_case(
        self,
        caplog: LogCaptureFixture,
        mocker: MockFixture,
        fm_control_target_device_pair_fixture: FMControlTargetDevicePair,
    ):
        """test successful case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_fm_plugin", return_value=test_util.DummyFMPlugin())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=fm_control.__name__):
            FMController.disconnect(device_pair=test_device_pair)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        # Inspection: Check the plugin call log
        plugin_call_log = caplog.records[0]
        assert plugin_call_log.levelname == "INFO"
        assert plugin_call_log.getMessage() == "Request disconnect upstream device and downstream device to FM plugin."

        assert hasattr(plugin_call_log, "manager_type"), "manager_type should be present in the log record"
        assert getattr(plugin_call_log, "manager_type") == "FM"

        assert hasattr(plugin_call_log, "manager_id"), "manager_id should be present in the log record"
        assert getattr(plugin_call_log, "manager_id") == test_device_pair.upstream_device.fm_manager_id

        assert hasattr(plugin_call_log, "class_name"), "class_name should be present in the log record"
        assert getattr(plugin_call_log, "class_name") == test_util.DummyFMPlugin.__name__

        assert hasattr(plugin_call_log, "method_name"), "method_name should be present in the log record"
        assert getattr(plugin_call_log, "method_name") == "disconnect"

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (  # upstream_device.switch_port_type is not "USP"
                {  # input device pair object
                    # upstream_device parameter
                    "upstream_device_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "upstream_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "upstream_device_fm_manager_id": "test_fm_manager_id",
                    # downstream_device parameter
                    "downstream_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "downstream_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "downstream_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
            (  # downstream_device.switch_port_type is not "DSP"
                {  # input device pair object
                    # upstream_device parameter
                    "upstream_device_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "upstream_device_switch_port_type": constants.SwitchPortType.USP.value,
                    "upstream_device_fm_manager_id": "test_fm_manager_id",
                    # downstream_device parameter
                    "downstream_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "downstream_device_switch_port_type": constants.SwitchPortType.USP.value,
                    "downstream_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
            (  # upstream_device.fm_manager_id not match downstream_device.fm_manager_id
                {  # input device pair object
                    # upstream_device parameter
                    "upstream_device_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "upstream_device_switch_port_type": constants.SwitchPortType.USP.value,
                    "upstream_device_fm_manager_id": "foo",
                    # downstream_device parameter
                    "downstream_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "downstream_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "downstream_device_fm_manager_id": "bar",
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    def test_invalid_device_pair_input(
        self,
        fm_control_target_device_pair_fixture: FMControlTargetDevicePair,
    ):
        """test plugin raise error case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            FMController.disconnect(device_pair=test_device_pair)

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device pair object
                    # upstream_device parameter
                    "upstream_device_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "upstream_device_switch_port_type": constants.SwitchPortType.USP.value,
                    "upstream_device_fm_manager_id": "test_fm_manager_id",
                    # downstream_device parameter
                    "downstream_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "downstream_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "downstream_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
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
        fm_control_target_device_pair_fixture: FMControlTargetDevicePair,
        plugin_manager_raise,
        expected_raise,
    ):
        """test plugin raise error case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_fm_plugin", side_effect=plugin_manager_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            FMController.disconnect(device_pair=test_device_pair)

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device object
                    # upstream_device parameter
                    "upstream_device_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "upstream_device_switch_port_type": constants.SwitchPortType.USP.value,
                    "upstream_device_fm_manager_id": "test_fm_manager_id",
                    # downstream_device parameter
                    "downstream_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "downstream_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "downstream_device_fm_manager_id": "test_fm_manager_id",
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    @pytest.mark.parametrize(
        "plugin_raise, expected_raise",
        [
            # plugin raise Unexpected Exception case
            (RuntimeError, exc.UnexpectedExceptionHWControlError),
            (Exception, exc.UnexpectedExceptionHWControlError),
            # plugin raise expected Exception case
            (exc.FMConnectFailureHWControlError, exc.FMConnectFailureHWControlError),
            (exc.AuthenticationHWControlError, exc.AuthenticationHWControlError),
        ],
    )
    def test_plugin_raise(
        self,
        mocker: MockFixture,
        fm_control_target_device_pair_fixture: FMControlTargetDevicePair,
        plugin_raise,
        expected_raise,
    ):
        """test plugin raise error case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_fm_plugin", return_value=test_util.DummyFMPlugin())
        mocker.patch.object(test_util.DummyFMPlugin, "disconnect", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise):
            FMController.disconnect(device_pair=test_device_pair)

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device object
                    # upstream_device parameter
                    "upstream_device_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "upstream_device_switch_port_type": constants.SwitchPortType.USP.value,
                    "upstream_device_fm_manager_id": "test_fm_manager_id",
                    # downstream_device parameter
                    "downstream_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "downstream_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "downstream_device_fm_manager_id": "test_fm_manager_id",
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
                exc.HostCPUAndDeviceNotFoundHWControlError,
                exc.HostCPUAndDeviceNotFoundHWControlError,
                (
                    "The specified Host CPU and target device are not found. The target Device IDs are follow: "
                    f"{test_util.DummyCPUInfo.DEVICE_ID.value}, {test_util.DummyDeviceInfo.DEVICE_ID.value}"
                ),
            ),
            (
                exc.HostCPUNotFoundHWControlError,
                exc.HostCPUNotFoundHWControlError,
                (
                    "The specified Host CPU is not found."
                    f" The target Device ID is follow: {test_util.DummyCPUInfo.DEVICE_ID.value}"
                ),
            ),
            (
                exc.DeviceNotFoundHWControlError,
                exc.DeviceNotFoundHWControlError,
                (
                    "The specified target device is not found."
                    f" The target Device ID is follow: {test_util.DummyDeviceInfo.DEVICE_ID.value}"
                ),
            ),
            (
                exc.UpstreamDeviceNotFoundHWControlError,
                exc.UpstreamDeviceNotFoundHWControlError,
                (
                    "The specified target device is not found."
                    f" The target Device ID is follow: {test_util.DummyCPUInfo.DEVICE_ID.value}"
                ),
            ),
            (
                exc.DownstreamDeviceNotFoundHWControlError,
                exc.DownstreamDeviceNotFoundHWControlError,
                (
                    "The specified target device is not found."
                    f" The target Device ID is follow: {test_util.DummyDeviceInfo.DEVICE_ID.value}"
                ),
            ),
        ],
    )
    def test_plugin_raise_not_found_error(  # pylint: disable=R0913, R0917
        self,
        mocker: MockFixture,
        fm_control_target_device_pair_fixture: FMControlTargetDevicePair,
        plugin_raise: type[exc.DeviceNotFoundHWControlError],
        expected_raise: type[exc.DeviceNotFoundHWControlError],
        expected_error_message: str,
    ):
        """Test plugin raise error device not found case error."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input value.
        test_device_pair = fm_control_target_device_pair_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_fm_plugin", return_value=test_util.DummyFMPlugin())
        mocker.patch.object(test_util.DummyFMPlugin, "disconnect", side_effect=plugin_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_raise) as e:
            FMController.disconnect(device_pair=test_device_pair)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        raised_exception = cast(exc.DeviceNotFoundHWControlError, e.value)
        assert raised_exception.message == expected_error_message

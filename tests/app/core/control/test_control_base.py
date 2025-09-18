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

"""Unit test module for control_base.py module ."""

import logging
from typing import cast

import pytest
from pytest import LogCaptureFixture
from pytest_mock import MockFixture

from tests.app.core.control import test_util

import app.common.basic_exceptions as exc
from app.common.dim import device_id_base as dim
from app.common.utils.device_exclusive import DeviceExclusive
from app.common import constants
from app.common.utils import plugin_manager
from app.core.control import control_base

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.core.control.control_base import ControlTargetDevice, PowerControlTargetDevice

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestControlTargetDevice:
    """Unit test class for ControlTargetDevice."""

    def test_lock_successful(self):
        """Test for lock successful case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        test_device = ControlTargetDevice(device_id=target_device_id)
        test_device.get_lock()

        # ++++ clean up +++++++++++++++++++++++++++++++++++++++++++++++#
        test_device.release_lock()

    def test_target_device_busy(self, mocker: MockFixture):
        """Test for target device busy case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input value.
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Set up the expected value.
        expected_error_message = f"The specified device is busy. The target Device ID is follow: {target_device_id}"

        # Set up the mock.
        mocker.patch.object(DeviceExclusive, "lock", return_value=False)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        test_device = ControlTargetDevice(device_id=target_device_id)
        with pytest.raises(exc.DeviceBusyHWControlError) as e:
            test_device.get_lock()

        raised_exception = cast(exc.DeviceBusyHWControlError, e.value)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert raised_exception.message == expected_error_message

    def test_unlock_successful(self):
        """Test for unlock successful case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        test_device = ControlTargetDevice(device_id=target_device_id)
        test_device.get_lock()
        test_device.release_lock()


class TestPowerControlTargetDeviceGenerate:
    """Unit test class for PowerControlTargetDevice generate."""

    @pytest.mark.parametrize(
        "device_id_manager_return_device_type",
        [
            constants.DeviceType.CPU.value,
            constants.DeviceType.MEMORY.value,
            constants.DeviceType.STORAGE.value,
            constants.DeviceType.NIC.value,
            constants.DeviceType.GPU.value,
            constants.DeviceType.GC.value,
            constants.DeviceType.SWITCH.value,
            constants.DeviceType.VM.value,
        ],
    )
    @pytest.mark.parametrize(
        "device_id_manager_return_manager_ids",
        [{"fm": "test_fm_manager_id", "oob": "test_oob_manager_id"}, {"fm": None, "oob": "test_oob_manager_id"}],
    )
    @pytest.mark.parametrize(
        "device_id_manager_return_oob_device_id",
        ["CPU-001"],
    )
    def test_instance_generate_successful(
        self,
        mocker: MockFixture,
        device_id_manager_return_device_type,
        device_id_manager_return_manager_ids,
        device_id_manager_return_oob_device_id,
    ):
        """Test for PowerControlTargetDevice instance generate successful."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Expected results:
        expected_device_type = device_id_manager_return_device_type
        expected_oob_manager_id = device_id_manager_return_manager_ids["oob"]
        expected_oob_device_id = device_id_manager_return_oob_device_id

        # Set up the mock.
        mocker.patch.object(dim, "device_id_to_device_type", return_value=device_id_manager_return_device_type)
        mocker.patch.object(dim, "device_id_to_manager_id", return_value=device_id_manager_return_manager_ids)
        mocker.patch.object(dim, "device_id_to_oob_device_id", return_value=device_id_manager_return_oob_device_id)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        test_device = PowerControlTargetDevice(device_id=target_device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert test_device.oob_device_id == expected_oob_device_id
        assert test_device.device_type == expected_device_type
        assert test_device.oob_manager_id == expected_oob_manager_id

    def test_to_device_type_return_none(self, mocker: MockFixture):
        """Test for device_id_to_device_type return None case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Set up the mock.
        mocker.patch.object(dim, "device_id_to_device_type", return_value=None)
        mocker.patch.object(
            dim,
            "device_id_to_manager_id",
            return_value={"fm": "test_fm_manager_id", "oob": "test_oob_manager_id"},
        )
        mocker.patch.object(dim, "device_id_to_oob_device_id", return_value="CPU-001")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            _ = PowerControlTargetDevice(device_id=target_device_id)

    @pytest.mark.parametrize(
        "device_id_manager_raise, expected_exception",
        [
            (exc.DeviceIDFileIncorrectHWControlError, exc.DeviceIDFileIncorrectHWControlError),
            (exc.DeviceIDFileNotFoundHWControlError, exc.DeviceIDFileNotFoundHWControlError),
        ],
    )
    def test_to_device_type_raise(self, mocker: MockFixture, device_id_manager_raise, expected_exception):
        """Test for device_id_to_device_type raise case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Set up the mock.
        mocker.patch.object(dim, "device_id_to_device_type", side_effect=device_id_manager_raise)
        mocker.patch.object(
            dim,
            "device_id_to_manager_id",
            return_value={"fm": "test_fm_manager_id", "oob": "test_oob_manager_id"},
        )
        mocker.patch.object(dim, "device_id_to_oob_device_id", return_value="CPU-001")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            _ = PowerControlTargetDevice(device_id=target_device_id)

    @pytest.mark.parametrize(
        "device_id_manager_raise, expected_exception",
        [
            (exc.APIUsageHWControlError, exc.DeviceNotFoundHWControlError),
            (exc.DeviceIDNotFoundHWControlError, exc.DeviceNotFoundHWControlError),
        ],
    )
    def test_to_device_type_raise_not_found_error(
        self,
        mocker: MockFixture,
        device_id_manager_raise: type[exc.BaseHWControlError],
        expected_exception: type[exc.DeviceNotFoundHWControlError],
    ):
        """Test for device_id_to_device_type raise device not found case error."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input value.
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Set up the expected value.
        expected_error_message = (
            f"The specified target device is not found. The target Device ID is follow: {target_device_id}"
        )

        # Set up the mock.
        mocker.patch.object(dim, "device_id_to_device_type", side_effect=device_id_manager_raise)
        mocker.patch.object(
            dim,
            "device_id_to_manager_id",
            return_value={"fm": "test_fm_manager_id", "oob": "test_oob_manager_id"},
        )
        mocker.patch.object(dim, "device_id_to_oob_device_id", return_value="CPU-001")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception) as e:
            _ = PowerControlTargetDevice(device_id=target_device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        raised_exception = cast(exc.DeviceNotFoundHWControlError, e.value)
        assert raised_exception.message == expected_error_message

    def test_to_oob_device_id_return_none(self, mocker: MockFixture):
        """Test for device_id_to_oob_device_id return None case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Set up the mock.
        mocker.patch.object(dim, "device_id_to_device_type", return_value=constants.DeviceType.CPU.value)
        mocker.patch.object(
            dim,
            "device_id_to_manager_id",
            return_value={"fm": "test_fm_manager_id", "oob": "test_oob_manager_id"},
        )
        mocker.patch.object(dim, "device_id_to_oob_device_id", return_value=None)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            _ = PowerControlTargetDevice(device_id=target_device_id)

    @pytest.mark.parametrize(
        "device_id_manager_raise, expected_exception",
        [
            (exc.DeviceIDFileIncorrectHWControlError, exc.DeviceIDFileIncorrectHWControlError),
            (exc.DeviceIDFileNotFoundHWControlError, exc.DeviceIDFileNotFoundHWControlError),
        ],
    )
    def test_to_oob_device_id_raise(self, mocker: MockFixture, device_id_manager_raise, expected_exception):
        """Test for device_id_to_oob_device_id raise case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Set up the mock.
        mocker.patch.object(dim, "device_id_to_device_type", return_value=constants.DeviceType.CPU.value)
        mocker.patch.object(
            dim,
            "device_id_to_manager_id",
            return_value={"fm": "test_fm_manager_id", "oob": "test_oob_manager_id"},
        )
        mocker.patch.object(dim, "device_id_to_oob_device_id", side_effect=device_id_manager_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            _ = PowerControlTargetDevice(device_id=target_device_id)

    @pytest.mark.parametrize(
        "device_id_manager_raise, expected_exception",
        [
            (exc.APIUsageHWControlError, exc.DeviceNotFoundHWControlError),
            (exc.DeviceIDNotFoundHWControlError, exc.DeviceNotFoundHWControlError),
        ],
    )
    def test_to_oob_device_id_raise_not_found_error(
        self,
        mocker: MockFixture,
        device_id_manager_raise: type[exc.BaseHWControlError],
        expected_exception: type[exc.DeviceNotFoundHWControlError],
    ):
        """Test for device_id_to_oob_device_id raise device not found case error."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input value.
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Set up the expected value.
        expected_error_message = (
            f"The specified target device is not found. The target Device ID is follow: {target_device_id}"
        )

        # Set up the mock.
        mocker.patch.object(dim, "device_id_to_device_type", return_value=constants.DeviceType.CPU.value)
        mocker.patch.object(
            dim,
            "device_id_to_manager_id",
            return_value={"fm": "test_fm_manager_id", "oob": "test_oob_manager_id"},
        )
        mocker.patch.object(dim, "device_id_to_oob_device_id", side_effect=device_id_manager_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception) as e:
            _ = PowerControlTargetDevice(device_id=target_device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        raised_exception = cast(exc.DeviceNotFoundHWControlError, e.value)
        assert raised_exception.message == expected_error_message

    @pytest.mark.parametrize(
        "device_id_manager_raise, expected_exception",
        [
            (exc.DeviceIDFileIncorrectHWControlError, exc.DeviceIDFileIncorrectHWControlError),
            (exc.DeviceIDFileNotFoundHWControlError, exc.DeviceIDFileNotFoundHWControlError),
        ],
    )
    def test_to_oob_manager_id_raise(
        self,
        mocker: MockFixture,
        device_id_manager_raise: type[exc.BaseHWControlError],
        expected_exception: type[exc.BaseHWControlError],
    ):
        """Test for device_id_to_manager_id raise case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Set up the mock.
        mocker.patch.object(dim, "device_id_to_device_type", return_value=constants.DeviceType.CPU.value)
        mocker.patch.object(dim, "device_id_to_manager_id", side_effect=device_id_manager_raise)
        mocker.patch.object(dim, "device_id_to_oob_device_id", return_value="CPU-001")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            _ = PowerControlTargetDevice(device_id=target_device_id)

    @pytest.mark.parametrize(
        "device_id_manager_raise, expected_exception",
        [
            (exc.APIUsageHWControlError, exc.DeviceNotFoundHWControlError),
            (exc.DeviceIDNotFoundHWControlError, exc.DeviceNotFoundHWControlError),
        ],
    )
    def test_to_oob_manager_id_raise_not_found(
        self,
        mocker: MockFixture,
        device_id_manager_raise: type[exc.BaseHWControlError],
        expected_exception: type[exc.DeviceNotFoundHWControlError],
    ):
        """Test for device_id_to_manager_id raise device not found case error."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input value.
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Set up the expected value.
        expected_error_message = (
            f"The specified target device is not found. The target Device ID is follow: {target_device_id}"
        )

        # Set up the mock.
        mocker.patch.object(dim, "device_id_to_device_type", return_value=constants.DeviceType.CPU.value)
        mocker.patch.object(dim, "device_id_to_manager_id", side_effect=device_id_manager_raise)
        mocker.patch.object(dim, "device_id_to_oob_device_id", return_value="CPU-001")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception) as e:
            _ = PowerControlTargetDevice(device_id=target_device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        raised_exception = cast(exc.DeviceNotFoundHWControlError, e.value)
        assert raised_exception.message == expected_error_message

    @pytest.mark.parametrize(
        "device_id_manager_return_manager_ids",
        [{"fm": "test_fm_manager_id", "oob": None}, {"fm": None, "oob": None}],
    )
    def test_to_oob_manager_id_return_invalid(self, mocker: MockFixture, device_id_manager_return_manager_ids):
        """Test for device_id_to_manager_id return None case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Set up the mock.
        mocker.patch.object(dim, "device_id_to_device_type", return_value=constants.DeviceType.CPU.value)
        mocker.patch.object(
            dim,
            "device_id_to_manager_id",
            return_value=device_id_manager_return_manager_ids,
        )  # return invalid value
        mocker.patch.object(dim, "device_id_to_oob_device_id", return_value="CPU-001")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            _ = PowerControlTargetDevice(device_id=target_device_id)


class TestSetPowerState:
    """Unit test class for ControlTargetDevice.set_oob_device_id."""

    @pytest.mark.parametrize(
        "power_control_target_device_fixture, plugin_return_spec_info, expected_power_state",
        [
            (  # device_type is "CPU" and "powerState" in spec_info is "On"
                {  # input device object
                    "device_id": "Foo",
                    "device_type": constants.DeviceType.CPU.value,
                    "power_state": constants.DevicePowerState.UNKNOWN,
                },
                {  # plugin_return
                    "devices": [
                        {
                            "deviceID": "0001",
                            "type": constants.DeviceType.CPU.value,
                            "powerState": constants.DevicePowerState.ON.value,
                            "time": "2006-01-02T15:04:05Z",
                        }
                    ]
                },
                constants.DevicePowerState.ON,
            ),
            (  # device_type is "CPU" and "powerState" in spec_info is "Off"
                {  # input device object
                    "device_id": "Foo",
                    "device_type": constants.DeviceType.CPU.value,
                    "power_state": constants.DevicePowerState.UNKNOWN.value,
                },
                {  # plugin_return
                    "devices": [
                        {
                            "deviceID": "0001",
                            "type": constants.DeviceType.CPU.value,
                            "powerState": constants.DevicePowerState.OFF.value,
                            "time": "2006-01-02T15:04:05Z",
                        }
                    ]
                },
                constants.DevicePowerState.OFF,
            ),
            (  # device_type is "CPU" and "powerState" in spec_info is "PoweringOn"
                {  # input device object
                    "device_id": "Foo",
                    "device_type": constants.DeviceType.CPU.value,
                    "power_state": constants.DevicePowerState.UNKNOWN.value,
                },
                {  # plugin_return
                    "devices": [
                        {
                            "deviceID": "0001",
                            "type": constants.DeviceType.CPU.value,
                            "powerState": constants.DevicePowerState.POWERING_ON.value,
                            "time": "2006-01-02T15:04:05Z",
                        }
                    ]
                },
                constants.DevicePowerState.POWERING_ON,
            ),
            (  # device_type is "CPU" and "powerState" in spec_info is "PoweringOff"
                {  # input device object
                    "device_id": "Foo",
                    "device_type": constants.DeviceType.CPU.value,
                    "power_state": constants.DevicePowerState.UNKNOWN.value,
                },
                {  # plugin_return
                    "devices": [
                        {
                            "deviceID": "0001",
                            "type": constants.DeviceType.CPU.value,
                            "powerState": constants.DevicePowerState.POWERING_OFF.value,
                            "time": "2006-01-02T15:04:05Z",
                        }
                    ]
                },
                constants.DevicePowerState.POWERING_OFF,
            ),
            (  # device_type is "CPU" and "powerState" in spec_info is "Paused"
                {  # input device object
                    "device_id": "Foo",
                    "device_type": constants.DeviceType.CPU.value,
                    "power_state": constants.DevicePowerState.UNKNOWN.value,
                },
                {  # plugin_return
                    "devices": [
                        {
                            "deviceID": "0001",
                            "type": constants.DeviceType.CPU.value,
                            "powerState": constants.DevicePowerState.PAUSED.value,
                            "time": "2006-01-02T15:04:05Z",
                        }
                    ]
                },
                constants.DevicePowerState.PAUSED,
            ),
            (  # device_type is "CPU" and "powerState" in spec_info is "Unknown"
                {  # input device object
                    "device_id": "Foo",
                    "device_type": constants.DeviceType.CPU.value,
                    "power_state": constants.DevicePowerState.UNKNOWN.value,
                },
                {  # plugin_return
                    "devices": [
                        {
                            "deviceID": "0001",
                            "type": constants.DeviceType.CPU.value,
                            "powerState": constants.DevicePowerState.UNKNOWN.value,
                            "time": "2006-01-02T15:04:05Z",
                        }
                    ]
                },
                constants.DevicePowerState.UNKNOWN,
            ),
            (  # device_type is "GPU" and "powerState" in spec_info is "Off"
                {  # input device object
                    "device_id": "Foo",
                    "device_type": constants.DeviceType.GPU.value,
                    "power_state": constants.DevicePowerState.UNKNOWN.value,
                },
                {  # plugin_return
                    "devices": [
                        {
                            "deviceID": "0001",
                            "type": constants.DeviceType.GPU.value,
                            "powerState": constants.DevicePowerState.OFF.value,
                            "time": "2006-01-02T15:04:05Z",
                        }
                    ]
                },
                constants.DevicePowerState.OFF,
            ),
            (  # device_type is "memory" and "powerState" in spec_info is "PoweringOn"
                {  # input device object
                    "device_id": "Foo",
                    "device_type": constants.DeviceType.MEMORY.value,
                    "power_state": constants.DevicePowerState.UNKNOWN.value,
                },
                {  # plugin_return
                    "devices": [
                        {
                            "deviceID": "0001",
                            "type": constants.DeviceType.MEMORY.value,
                            "powerState": constants.DevicePowerState.POWERING_ON.value,
                            "time": "2006-01-02T15:04:05Z",
                        }
                    ]
                },
                constants.DevicePowerState.POWERING_ON,
            ),
            (  # device_type is "storage" and "powerState" in spec_info is "PoweringOff"
                {  # input device object
                    "device_id": "Foo",
                    "device_type": constants.DeviceType.STORAGE.value,
                    "power_state": constants.DevicePowerState.UNKNOWN.value,
                },
                {  # plugin_return
                    "devices": [
                        {
                            "deviceID": "0001",
                            "type": constants.DeviceType.STORAGE.value,
                            "powerState": constants.DevicePowerState.POWERING_OFF.value,
                            "time": "2006-01-02T15:04:05Z",
                        }
                    ]
                },
                constants.DevicePowerState.POWERING_OFF,
            ),
            (  # device_type is "networkInterface" and "powerState" in spec_info is "On"
                {  # input device object
                    "device_id": "Foo",
                    "device_type": constants.DeviceType.NIC.value,
                    "power_state": constants.DevicePowerState.UNKNOWN.value,
                },
                {  # plugin_return
                    "devices": [
                        {
                            "deviceID": "0001",
                            "type": constants.DeviceType.NIC.value,
                            "powerState": constants.DevicePowerState.ON.value,
                            "time": "2006-01-02T15:04:05Z",
                        }
                    ]
                },
                constants.DevicePowerState.ON,
            ),
        ],
        indirect=["power_control_target_device_fixture"],
    )
    def test_set_power_state(  # pylint: disable=R0913, R0917
        self,
        mocker: MockFixture,
        caplog: LogCaptureFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        plugin_return_spec_info,
        expected_power_state,
    ):
        """Test for set_power_state successful."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", return_value=test_util.DummyOOBPlugin())
        mocker.patch.object(test_util.DummyOOBPlugin, "get_power_state", return_value=plugin_return_spec_info)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=control_base.__name__):
            target_device.set_power_state()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert target_device.power_state == expected_power_state

        assert len(caplog.records) == 1

        # Inspection: Check the plugin call log
        plugin_call_log = caplog.records[0]
        assert plugin_call_log.levelname == "INFO"
        assert plugin_call_log.getMessage() == "Request get device power state to OOB plugin."
        assert hasattr(plugin_call_log, "manager_type"), "manager_type should be present in the log record"
        assert getattr(plugin_call_log, "manager_type") == "OOB"

        assert hasattr(plugin_call_log, "manager_id"), "manager_id should be present in the log record"
        assert getattr(plugin_call_log, "manager_id") == target_device.oob_manager_id

        assert hasattr(plugin_call_log, "class_name"), "class_name should be present in the log record"
        assert getattr(plugin_call_log, "class_name") == test_util.DummyOOBPlugin.__name__

        assert hasattr(plugin_call_log, "method_name"), "method_name should be present in the log record"
        assert getattr(plugin_call_log, "method_name") == "get_power_state"

    @pytest.mark.parametrize(
        "power_control_target_device_fixture, plugin_return_spec_info, expected_power_state",
        [
            (  # device_type is "CPU" and PowerState in spec_info is "Unknown"
                {  # input device object
                    "device_id": "Foo",
                    "device_type": constants.DeviceType.CPU.value,
                    "power_state": constants.DevicePowerState.UNKNOWN.value,
                },
                {  # plugin_return
                    "devices": [
                        {
                            "deviceID": "0001",
                            "type": constants.DeviceType.CPU.value,
                            "powerState": "UnknownUnknownUnknownTestPowerState",
                            "time": "2006-01-02T15:04:05Z",
                        }
                    ]
                },
                constants.DevicePowerState.UNKNOWN,
            ),
        ],
        indirect=["power_control_target_device_fixture"],
    )
    def test_set_unknown_power_state_str(  # pylint: disable=R0913, R0917
        self,
        mocker: MockFixture,
        caplog: LogCaptureFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        plugin_return_spec_info,
        expected_power_state,
    ):
        """Test for set_power_state successful."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", return_value=test_util.DummyOOBPlugin())
        mocker.patch.object(test_util.DummyOOBPlugin, "get_power_state", return_value=plugin_return_spec_info)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=control_base.__name__):
            target_device.set_power_state()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert target_device.power_state == expected_power_state

        assert len(caplog.records) == 2

        # Inspection: Check the plugin call log
        plugin_call_log = caplog.records[0]
        assert plugin_call_log.levelname == "INFO"
        assert plugin_call_log.getMessage() == "Request get device power state to OOB plugin."
        assert hasattr(plugin_call_log, "manager_type"), "manager_type should be present in the log record"
        assert getattr(plugin_call_log, "manager_type") == "OOB"

        assert hasattr(plugin_call_log, "manager_id"), "manager_id should be present in the log record"
        assert getattr(plugin_call_log, "manager_id") == target_device.oob_manager_id

        assert hasattr(plugin_call_log, "class_name"), "class_name should be present in the log record"
        assert getattr(plugin_call_log, "class_name") == test_util.DummyOOBPlugin.__name__

        assert hasattr(plugin_call_log, "method_name"), "method_name should be present in the log record"
        assert getattr(plugin_call_log, "method_name") == "get_power_state"

        # Inspection: Check the unexpected power state log
        unexpected_power_log = caplog.records[1]
        assert unexpected_power_log.levelname == "WARNING"
        assert unexpected_power_log.getMessage() == "The obtained power state is not a valid DevicePowerState."

        assert hasattr(
            unexpected_power_log, "obtained_power_state"
        ), "obtained_power_state should be present in the log record"
        assert getattr(unexpected_power_log, "obtained_power_state") == "UnknownUnknownUnknownTestPowerState"

    @pytest.mark.parametrize(
        "power_control_target_device_fixture, plugin_return_spec_info, expected_exception",
        [
            (  # spec_info TypeError, expected_exception is InternalHWControlError
                {  # input device object
                    "device_id": "Foo",
                    "device_type": constants.DeviceType.CPU.value,
                    "power_state": constants.DevicePowerState.UNKNOWN.value,
                },
                {"devices": [None, "other_device_data"]},  # plugin_return
                TypeError,
            ),
            (  # spec_info KeyError, expected_exception is KeyError
                {  # input device object
                    "device_id": "Foo",
                    "device_type": constants.DeviceType.CPU.value,
                    "power_state": constants.DevicePowerState.UNKNOWN.value,
                },
                {  # plugin_return
                    "devices": [
                        {
                            "deviceID": "0001",
                            "type": constants.DeviceType.CPU.value,
                            "PPPPower": constants.DevicePowerState.ON.value,  # Correct is "powerState"
                            "time": "2006-01-02T15:04:05Z",
                        }
                    ]
                },
                KeyError,
            ),
            (  # spec_info PowerState is None, expected_exception is ValueError
                {  # input device object
                    "device_id": "Foo",
                    "device_type": constants.DeviceType.CPU.value,
                    "power_state": constants.DevicePowerState.UNKNOWN.value,
                },
                {  # plugin_return
                    "devices": [
                        {
                            "deviceID": "0001",
                            "type": constants.DeviceType.CPU.value,
                            "powerState": None,  # "powerState" must not None.
                            "time": "2006-01-02T15:04:05Z",
                        }
                    ]
                },
                ValueError,
            ),
        ],
        indirect=["power_control_target_device_fixture"],
    )
    def test_set_power_state_error_case(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture,
        plugin_return_spec_info,
        expected_exception,
    ):
        """test error case of set device power-state."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", return_value=test_util.DummyOOBPlugin())
        mocker.patch.object(
            test_util.DummyOOBPlugin,
            "get_power_state",
            return_value=plugin_return_spec_info,
        )

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            target_device.set_power_state()

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {  # input device object
                "device_id": "Foo",
                "device_type": constants.DeviceType.CPU.value,
                "power_state": constants.DevicePowerState.UNKNOWN.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise_exception, expected_exception",
        [
            (exc.BaseHWControlError, exc.BaseHWControlError),
            (RuntimeError, exc.UnexpectedExceptionHWControlError),
        ],
    )
    def test_raise_hw_control_error(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        plugin_raise_exception: type[exc.BaseHWControlError],
        expected_exception: type[exc.BaseHWControlError],
    ):
        """test plugin raise expected exception case.

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.

        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input value.
        target_device = power_control_target_device_fixture

        # Set up the mock.
        mocker.patch.object(plugin_manager, "get_oob_plugin", return_value=test_util.DummyOOBPlugin())
        mocker.patch.object(test_util.DummyOOBPlugin, "get_power_state", side_effect=plugin_raise_exception)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            target_device.set_power_state()

    @pytest.mark.parametrize(
        "power_control_target_device_fixture",
        [
            {  # input device object
                "device_id": "Foo",
                "device_type": constants.DeviceType.CPU.value,
                "power_state": constants.DevicePowerState.UNKNOWN.value,
            },
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "plugin_raise_exception, expected_exception",
        [
            (exc.DeviceNotFoundHWControlError, exc.DeviceNotFoundHWControlError),
        ],
    )
    def test_raise_not_found_error(
        self,
        mocker: MockFixture,
        power_control_target_device_fixture: PowerControlTargetDevice,
        plugin_raise_exception: type[exc.DeviceNotFoundHWControlError],
        expected_exception: type[exc.DeviceNotFoundHWControlError],
    ):
        """test plugin raise expected exception case.

        Args:
            mocker (MockFixture):
                Fixture for creating mock objects.

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
        mocker.patch.object(test_util.DummyOOBPlugin, "get_power_state", side_effect=plugin_raise_exception)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception) as e:
            target_device.set_power_state()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        raised_exception = cast(exc.DeviceNotFoundHWControlError, e.value)
        assert raised_exception.message == expected_error_message

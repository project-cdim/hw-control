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

"""Unit test module for FmControlTargetDevicePair class ."""

from typing import cast

import pytest
from pytest_mock import MockFixture

from tests.app.core.control import test_util

import app.common.basic_exceptions as exc  # type: ignore
from app.common import constants
from app.common.utils.device_exclusive import DeviceExclusive  # type: ignore
from app.core.control import fm_control  # type: ignore

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.core.control.fm_control import FmControlTargetDevicePair  # type: ignore

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestGenerateInstance:
    """Unit test class for FmControlTargetDevice generate."""

    @pytest.mark.parametrize(
        "host_cpu_parameter, target_device_parameter",
        [
            (
                {  # input host cpu parameter
                    "device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "switch_port_type": constants.SwitchPortType.USP.value,
                    "fm_manager_id": "foo",
                    "fm_port_id": "bar",
                },
                {  # input target device parameter
                    "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "switch_port_type": constants.SwitchPortType.USP.value,
                    "fm_manager_id": "Foo",
                    "fm_port_id": "bar",
                },
            ),
        ],
    )
    def test_instance_generate_successful(self, mocker: MockFixture, host_cpu_parameter, target_device_parameter):
        """Unit test for FmControlTargetDevice instance generate successful."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock.
        mocker.patch.object(
            fm_control.FmControlTargetDevice,
            "model_post_init",
            return_value=None,
        )

        # Set up the input value.
        host_cpu = fm_control.FmControlTargetDevice(
            device_id=host_cpu_parameter["device_id"],
            switch_port_type=host_cpu_parameter["switch_port_type"],
            fm_manager_id=host_cpu_parameter["fm_manager_id"],
            fm_port_id=host_cpu_parameter["fm_port_id"],
        )
        target_device = fm_control.FmControlTargetDevice(
            device_id=target_device_parameter["device_id"],
            switch_port_type=target_device_parameter["switch_port_type"],
            fm_manager_id=target_device_parameter["fm_manager_id"],
            fm_port_id=target_device_parameter["fm_port_id"],
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        _ = FmControlTargetDevicePair(host_cpu=host_cpu, target_device=target_device)

    @pytest.mark.parametrize(
        "host_cpu_parameter, target_device_parameter",
        [
            (  # device_id of host_cpu and target_device are the same case.
                {  # input host cpu parameter
                    "device_id": "ec020a7c-5014-4c2d-8682-45f69c936e3a",
                    "switch_port_type": constants.SwitchPortType.USP.value,
                    "fm_manager_id": "foo",
                    "fm_port_id": "bar",
                },
                {  # input target device parameter
                    "device_id": "ec020a7c-5014-4c2d-8682-45f69c936e3a",
                    "switch_port_type": constants.SwitchPortType.USP.value,
                    "fm_manager_id": "foo",
                    "fm_port_id": "bar",
                },
            ),
        ],
    )
    def test_instance_generate_error(self, mocker: MockFixture, host_cpu_parameter, target_device_parameter):
        """Unit test for FmControlTargetDevice instance generate successful."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock.
        mocker.patch.object(
            fm_control.FmControlTargetDevice,
            "model_post_init",
            return_value=None,
        )

        # Set up the input value.
        host_cpu = fm_control.FmControlTargetDevice(
            device_id=host_cpu_parameter["device_id"],
            switch_port_type=host_cpu_parameter["switch_port_type"],
            fm_manager_id=host_cpu_parameter["fm_manager_id"],
            fm_port_id=host_cpu_parameter["fm_port_id"],
        )
        target_device = fm_control.FmControlTargetDevice(
            device_id=target_device_parameter["device_id"],
            switch_port_type=target_device_parameter["switch_port_type"],
            fm_manager_id=target_device_parameter["fm_manager_id"],
            fm_port_id=target_device_parameter["fm_port_id"],
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHwControlError):
            _ = FmControlTargetDevicePair(host_cpu=host_cpu, target_device=target_device)


class TestGetLock:
    """Unit test class for FmControlTargetDevicePair.get_lock ."""

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "target_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    def test_lock_successful(self, fm_control_target_device_pair_fixture: FmControlTargetDevicePair):
        """Test for lock successful case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_pair = fm_control_target_device_pair_fixture

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        test_device_pair.get_lock()

        # ++++ clean up +++++++++++++++++++++++++++++++++++++++++++++++#

        DeviceExclusive.unlock(device_id=test_device_pair.target_device.device_id)
        DeviceExclusive.unlock(device_id=test_device_pair.host_cpu.device_id)

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture, busy_device_device_id",
        [
            (
                {  # input device object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "target_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                },
                test_util.DummyCpuInfo.DEVICE_ID.value,
            )
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    def test_target_busy(self, fm_control_target_device_pair_fixture: FmControlTargetDevicePair, busy_device_device_id):
        """Test for host_cpu or target_device busy case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_pair = fm_control_target_device_pair_fixture

        DeviceExclusive.lock(device_id=busy_device_device_id)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.DeviceBusyHwControlError) as e:
            test_device_pair.get_lock()

        raised_exception = cast(exc.DeviceBusyHwControlError, e.value)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert (
            raised_exception.message
            == f"The specified device is busy. The target Device ID is follow: {busy_device_device_id}"
        )

        # ++++ clean up +++++++++++++++++++++++++++++++++++++++++++++++#
        DeviceExclusive.unlock(device_id=busy_device_device_id)

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "target_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                }
            )
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    def test_target_cpu_and_device_busy(self, fm_control_target_device_pair_fixture: FmControlTargetDevicePair):
        """Test for host_cpu and target_device both busy case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_pair = fm_control_target_device_pair_fixture

        DeviceExclusive.lock(device_id=test_device_pair.target_device.device_id)
        DeviceExclusive.lock(device_id=test_device_pair.host_cpu.device_id)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.DeviceBusyHwControlError) as e:
            test_device_pair.get_lock()

        raised_exception = cast(exc.DeviceBusyHwControlError, e.value)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert raised_exception.message == (
            f"The specified device is busy. The target Device ID is follow: {test_device_pair.target_device.device_id}"
        )

        # ++++ clean up +++++++++++++++++++++++++++++++++++++++++++++++#
        DeviceExclusive.unlock(device_id=test_device_pair.host_cpu.device_id)
        DeviceExclusive.unlock(device_id=test_device_pair.target_device.device_id)


class TestReleaseLock:  # pylint: disable=R0903
    """Unit test class for FmControlTargetDevicePair.release_lock."""

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device object
                    "host_cpu_device_id": test_util.DummyCpuInfo.DEVICE_ID.value,
                    "target_device_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    def test_can_release_lock(self, fm_control_target_device_pair_fixture: FmControlTargetDevicePair):
        """Test for lock successful case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_pair = fm_control_target_device_pair_fixture

        DeviceExclusive.lock(device_id=test_device_pair.target_device.device_id)
        DeviceExclusive.lock(device_id=test_device_pair.host_cpu.device_id)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        test_device_pair.release_lock()

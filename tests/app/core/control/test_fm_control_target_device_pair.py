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

"""Unit test module for FMControlTargetDevicePair class ."""

from typing import cast

import pytest
from pytest_mock import MockFixture

from tests.app.core.control import test_util

import app.common.basic_exceptions as exc
from app.common import constants
from app.common.utils.device_exclusive import DeviceExclusive
from app.core.control import fm_control

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.core.control.fm_control import FMControlTargetDevicePair

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestGenerateInstance:
    """Unit test class for FMControlTargetDevice generate."""

    @pytest.mark.parametrize(
        "upstream_device_parameter, downstream_device_parameter",
        [
            (
                {  # input upstream device parameter
                    "device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "switch_port_type": constants.SwitchPortType.USP.value,
                    "fm_manager_id": "foo",
                    "fm_port_id": "bar",
                },
                {  # input downstream device parameter
                    "device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                    "switch_port_type": constants.SwitchPortType.USP.value,
                    "fm_manager_id": "Foo",
                    "fm_port_id": "bar",
                },
            ),
        ],
    )
    def test_instance_generate_successful(
        self, mocker: MockFixture, upstream_device_parameter, downstream_device_parameter
    ):
        """Unit test for FMControlTargetDevice instance generate successful."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock.
        mocker.patch.object(
            fm_control.FMControlTargetDevice,
            "model_post_init",
            return_value=None,
        )

        # Set up the input value.
        upstream_device = fm_control.FMControlTargetDevice(**upstream_device_parameter)
        downstream_device = fm_control.FMControlTargetDevice(**downstream_device_parameter)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        _ = FMControlTargetDevicePair(upstream_device=upstream_device, downstream_device=downstream_device)

    @pytest.mark.parametrize(
        "upstream_device_parameter, downstream_device_parameter",
        [
            (  # device_id of upstream device and downstream device are the same case.
                {  # input upstream device parameter
                    "device_id": "ec020a7c-5014-4c2d-8682-45f69c936e3a",
                    "switch_port_type": constants.SwitchPortType.USP.value,
                    "fm_manager_id": "foo",
                    "fm_port_id": "bar",
                },
                {  # input downstream device parameter
                    "device_id": "ec020a7c-5014-4c2d-8682-45f69c936e3a",
                    "switch_port_type": constants.SwitchPortType.USP.value,
                    "fm_manager_id": "foo",
                    "fm_port_id": "bar",
                },
            ),
        ],
    )
    def test_instance_generate_error(self, mocker: MockFixture, upstream_device_parameter, downstream_device_parameter):
        """Unit test for FMControlTargetDevice instance generate successful."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock.
        mocker.patch.object(
            fm_control.FMControlTargetDevice,
            "model_post_init",
            return_value=None,
        )

        # Set up the input value.
        upstream_device = fm_control.FMControlTargetDevice(**upstream_device_parameter)
        downstream_device = fm_control.FMControlTargetDevice(**downstream_device_parameter)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            _ = FMControlTargetDevicePair(upstream_device=upstream_device, downstream_device=downstream_device)


class TestGetLock:
    """Unit test class for FMControlTargetDevicePair.get_lock ."""

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device object
                    "upstream_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "downstream_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    def test_lock_successful(self, fm_control_target_device_pair_fixture: FMControlTargetDevicePair):
        """Test for lock successful case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_pair = fm_control_target_device_pair_fixture

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        test_device_pair.get_lock()

        # ++++ clean up +++++++++++++++++++++++++++++++++++++++++++++++#

        DeviceExclusive.unlock(device_id=test_device_pair.upstream_device.device_id)
        DeviceExclusive.unlock(device_id=test_device_pair.downstream_device.device_id)

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture, busy_device_device_id",
        [
            (
                {  # input device object
                    "upstream_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "downstream_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                },
                test_util.DummyCPUInfo.DEVICE_ID.value,
            )
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    def test_target_busy(self, fm_control_target_device_pair_fixture: FMControlTargetDevicePair, busy_device_device_id):
        """Test for upstream_device or target_device busy case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_pair = fm_control_target_device_pair_fixture

        DeviceExclusive.lock(device_id=busy_device_device_id)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.DeviceBusyHWControlError) as e:
            test_device_pair.get_lock()

        raised_exception = cast(exc.DeviceBusyHWControlError, e.value)

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
            {  # input device object
                "upstream_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                "downstream_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
            }
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    def test_target_cpu_and_device_busy(self, fm_control_target_device_pair_fixture: FMControlTargetDevicePair):
        """Test for host_cpu and target_device both busy case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_pair = fm_control_target_device_pair_fixture

        DeviceExclusive.lock(device_id=test_device_pair.downstream_device.device_id)
        DeviceExclusive.lock(device_id=test_device_pair.upstream_device.device_id)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.DeviceBusyHWControlError) as e:
            test_device_pair.get_lock()

        raised_exception = cast(exc.DeviceBusyHWControlError, e.value)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert raised_exception.message == (
            "The specified device is busy."
            f" The target Device ID is follow: {test_device_pair.downstream_device.device_id}"
        )

        # ++++ clean up +++++++++++++++++++++++++++++++++++++++++++++++#
        DeviceExclusive.unlock(device_id=test_device_pair.upstream_device.device_id)
        DeviceExclusive.unlock(device_id=test_device_pair.downstream_device.device_id)


class TestReleaseLock:  # pylint: disable=R0903
    """Unit test class for FMControlTargetDevicePair.release_lock."""

    @pytest.mark.parametrize(
        "fm_control_target_device_pair_fixture",
        [
            (
                {  # input device object
                    "upstream_device_id": test_util.DummyCPUInfo.DEVICE_ID.value,
                    "downstream_device_id": test_util.DummyDeviceInfo.DEVICE_ID.value,
                }
            ),
        ],
        indirect=["fm_control_target_device_pair_fixture"],
    )
    def test_can_release_lock(self, fm_control_target_device_pair_fixture: FMControlTargetDevicePair):
        """Test for lock successful case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        test_device_pair = fm_control_target_device_pair_fixture

        DeviceExclusive.lock(device_id=test_device_pair.downstream_device.device_id)
        DeviceExclusive.lock(device_id=test_device_pair.upstream_device.device_id)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        test_device_pair.release_lock()

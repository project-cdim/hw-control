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

"""Unit test module for FMControlTargetDevice class ."""

from typing import cast

import pytest
from pytest_mock import MockFixture

import app.common.basic_exceptions as exc
from app.common import constants
from app.common.dim import device_id_base as dim
from app.core.control.fm_control import FMControlTargetDevice
from tests.app.core.control import test_util


class TestFMControlTargetDeviceGenerate:
    """Unit test class for FMControlTargetDevice generate."""

    @pytest.mark.parametrize(
        "device_id_manager_return_switch_port_type",
        [
            constants.SwitchPortType.USP.value,
            constants.SwitchPortType.DSP.value,
        ],
    )
    @pytest.mark.parametrize(
        "device_id_manager_return_manager_ids",
        [{"fm": "test_fm_manager_id", "oob": "test_oob_manager_id"}, {"fm": "test_fm_manager_id", "oob": None}],
    )
    @pytest.mark.parametrize(
        "device_id_manager_return_fm_port_id",
        ["852f416b-a6e7-4d32-b9c4-238901544d48"],
    )
    def test_instance_generate_successful(
        self,
        mocker: MockFixture,
        device_id_manager_return_switch_port_type,
        device_id_manager_return_manager_ids,
        device_id_manager_return_fm_port_id,
    ):
        """Unit test for FMControlTargetDevice instance generate successful."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Expected results:
        expected_switch_port_type = device_id_manager_return_switch_port_type
        expected_fm_manager_id = device_id_manager_return_manager_ids["fm"]
        expected_fm_port_id = device_id_manager_return_fm_port_id

        # Set up the mock.
        mocker.patch.object(
            dim, "device_id_to_switch_port_type", return_value=device_id_manager_return_switch_port_type
        )
        mocker.patch.object(dim, "device_id_to_manager_id", return_value=device_id_manager_return_manager_ids)
        mocker.patch.object(dim, "device_id_to_fm_port_id", return_value=device_id_manager_return_fm_port_id)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        test_device = FMControlTargetDevice(device_id=target_device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert test_device.switch_port_type == expected_switch_port_type
        assert test_device.fm_port_id == expected_fm_port_id
        assert test_device.fm_manager_id == expected_fm_manager_id

    def test_to_switch_port_type_return_none(self, mocker: MockFixture):
        """Unit test for device_id_to_switch_port_type return None case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Set up the mock.
        mocker.patch.object(dim, "device_id_to_switch_port_type", return_value=None)
        mocker.patch.object(
            dim,
            "device_id_to_manager_id",
            return_value={"fm": "test_fm_manager_id", "oob": "test_oob_manager_id"},
        )
        mocker.patch.object(dim, "device_id_to_fm_port_id", return_value="852f416b-a6e7-4d32-b9c4-238901544d48")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            _ = FMControlTargetDevice(device_id=target_device_id)

    @pytest.mark.parametrize(
        ("device_id_manager_raise", "expected_exception"),
        [
            (exc.APIUsageHWControlError, exc.DeviceNotFoundHWControlError),
            (exc.DeviceIDNotFoundHWControlError, exc.DeviceNotFoundHWControlError),
            (exc.DeviceIDFileIncorrectHWControlError, exc.DeviceIDFileIncorrectHWControlError),
            (exc.DeviceIDFileNotFoundHWControlError, exc.DeviceIDFileNotFoundHWControlError),
        ],
    )
    def test_to_switch_port_type_raise(
        self,
        mocker: MockFixture,
        device_id_manager_raise,
        expected_exception,
    ):
        """Unit test for device_id_to_switch_port_type return None case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Set up the mock.
        mocker.patch.object(dim, "device_id_to_switch_port_type", side_effect=device_id_manager_raise)
        mocker.patch.object(
            dim,
            "device_id_to_manager_id",
            return_value={"fm": "test_fm_manager_id", "oob": "test_oob_manager_id"},
        )
        mocker.patch.object(dim, "device_id_to_fm_port_id", return_value="852f416b-a6e7-4d32-b9c4-238901544d48")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception) as e:
            _ = FMControlTargetDevice(device_id=target_device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        if isinstance(e.value, exc.DeviceNotFoundHWControlError):
            raised_exception = cast(exc.DeviceNotFoundHWControlError, e.value)
            assert raised_exception.message == (
                f"The specified target device is not found. The target Device ID is follow: {target_device_id}"
            )

    @pytest.mark.parametrize(
        "device_id_manager_return_switch_port_type",
        [
            constants.SwitchPortType.USP.value,
            constants.SwitchPortType.DSP.value,
        ],
    )
    @pytest.mark.parametrize(
        "device_id_manager_return_manager_ids",
        [{"fm": None, "oob": "test_oob_manager_id"}, {"fm": None, "oob": None}],
    )
    def test_to_manager_id_return_none(
        self, mocker: MockFixture, device_id_manager_return_switch_port_type, device_id_manager_return_manager_ids
    ):
        """Unit test for device_id_to_manager_id return None case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Set up the mock.
        mocker.patch.object(
            dim, "device_id_to_switch_port_type", return_value=device_id_manager_return_switch_port_type
        )
        mocker.patch.object(
            dim,
            "device_id_to_manager_id",
            return_value=device_id_manager_return_manager_ids,
        )
        mocker.patch.object(dim, "device_id_to_fm_port_id", return_value="852f416b-a6e7-4d32-b9c4-238901544d48")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            _ = FMControlTargetDevice(device_id=target_device_id)

    @pytest.mark.parametrize(
        "device_id_manager_return_switch_port_type",
        [
            constants.SwitchPortType.USP.value,
            constants.SwitchPortType.DSP.value,
        ],
    )
    @pytest.mark.parametrize(
        ("device_id_manager_raise", "expected_exception"),
        [
            (exc.APIUsageHWControlError, exc.DeviceNotFoundHWControlError),
            (exc.DeviceIDNotFoundHWControlError, exc.DeviceNotFoundHWControlError),
            (exc.DeviceIDFileIncorrectHWControlError, exc.DeviceIDFileIncorrectHWControlError),
            (exc.DeviceIDFileNotFoundHWControlError, exc.DeviceIDFileNotFoundHWControlError),
        ],
    )
    def test_to_manager_id_raise(
        self,
        mocker: MockFixture,
        device_id_manager_return_switch_port_type,
        device_id_manager_raise,
        expected_exception,
    ):
        """Unit test for device_id_to_manager_id return None case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Set up the mock.
        mocker.patch.object(
            dim, "device_id_to_switch_port_type", return_value=device_id_manager_return_switch_port_type
        )
        mocker.patch.object(dim, "device_id_to_manager_id", side_effect=device_id_manager_raise)
        mocker.patch.object(dim, "device_id_to_fm_port_id", return_value="852f416b-a6e7-4d32-b9c4-238901544d48")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception) as e:
            _ = FMControlTargetDevice(device_id=target_device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        if isinstance(e.value, exc.DeviceNotFoundHWControlError):
            raised_exception = cast(exc.DeviceNotFoundHWControlError, e.value)
            assert raised_exception.message == (
                f"The specified target device is not found. The target Device ID is follow: {target_device_id}"
            )

    @pytest.mark.parametrize(
        "device_id_manager_return_switch_port_type",
        [
            constants.SwitchPortType.USP.value,
            constants.SwitchPortType.DSP.value,
        ],
    )
    @pytest.mark.parametrize(
        "device_id_manager_return_manager_ids",
        [{"fm": None, "oob": "test_oob_manager_id"}, {"fm": None, "oob": None}],
    )
    def test_to_fm_port_id_return_none(
        self, mocker: MockFixture, device_id_manager_return_switch_port_type, device_id_manager_return_manager_ids
    ):
        """Unit test for device_id_to_fm_port_id return None case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Set up the mock.
        mocker.patch.object(
            dim, "device_id_to_switch_port_type", return_value=device_id_manager_return_switch_port_type
        )
        mocker.patch.object(
            dim,
            "device_id_to_manager_id",
            return_value=device_id_manager_return_manager_ids,
        )
        mocker.patch.object(dim, "device_id_to_fm_port_id", return_value=None)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            _ = FMControlTargetDevice(device_id=target_device_id)

    @pytest.mark.parametrize(
        "device_id_manager_return_switch_port_type",
        [
            constants.SwitchPortType.USP.value,
            constants.SwitchPortType.DSP.value,
        ],
    )
    @pytest.mark.parametrize(
        "device_id_manager_return_manager_ids",
        [{"fm": None, "oob": "test_oob_manager_id"}, {"fm": None, "oob": None}],
    )
    @pytest.mark.parametrize(
        ("device_id_manager_raise", "expected_exception"),
        [
            (exc.APIUsageHWControlError, exc.DeviceNotFoundHWControlError),
            (exc.DeviceIDNotFoundHWControlError, exc.DeviceNotFoundHWControlError),
            (exc.DeviceIDFileIncorrectHWControlError, exc.DeviceIDFileIncorrectHWControlError),
            (exc.DeviceIDFileNotFoundHWControlError, exc.DeviceIDFileNotFoundHWControlError),
            (exc.InvalidTypeDeviceIDHWControlError, exc.RequestNotSupportedHWControlError),
        ],
    )
    def test_to_fm_port_id_raise(
        self,
        mocker: MockFixture,
        device_id_manager_return_switch_port_type,
        device_id_manager_return_manager_ids,
        device_id_manager_raise,
        expected_exception,
    ):
        """Unit test for device_id_to_fm_port_id raise case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Set up the mock.
        mocker.patch.object(
            dim, "device_id_to_switch_port_type", return_value=device_id_manager_return_switch_port_type
        )
        mocker.patch.object(
            dim,
            "device_id_to_manager_id",
            return_value=device_id_manager_return_manager_ids,
        )
        mocker.patch.object(dim, "device_id_to_fm_port_id", side_effect=device_id_manager_raise)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception) as e:
            _ = FMControlTargetDevice(device_id=target_device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        if isinstance(e.value, exc.DeviceNotFoundHWControlError):
            raised_exception = cast(exc.DeviceNotFoundHWControlError, e.value)
            assert raised_exception.message == (
                f"The specified target device is not found. The target Device ID is follow: {target_device_id}"
            )

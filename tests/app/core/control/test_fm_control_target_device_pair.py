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

import pytest
from pytest_mock import MockFixture

import app.common.basic_exceptions as exc
from app.common import constants
from app.core.control import fm_control
from app.core.control.fm_control import FMControlTargetDevicePair
from tests.app.core.control import test_util


class TestGenerateInstance:
    """Unit test class for FMControlTargetDevice generate."""

    @pytest.mark.parametrize(
        ("upstream_device_parameter", "downstream_device_parameter"),
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
        ("upstream_device_parameter", "downstream_device_parameter"),
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

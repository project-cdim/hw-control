# Copyright 2026 NEC Corporation
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

"""Unit test module for control_api._get_true_device_ids"""

import pytest

from pytest_mock import MockFixture

import app.common.basic_exceptions as exc

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#

from app.routers.control import control_api

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

DUMMY_UPSTREAM_DEVICE_ID = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"
DUMMY_DOWNSTREAM_DEVICE_ID = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"

DUMMY_TRUE_UPSTREAM_DEVICE_ID = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"
DUMMY_TRUE_DOWNSTREAM_DEVICE_ID = "852f416b-a6e7-4d32-b9c4-238901544d48"


class TestGetTrueDeviceIds:
    """Unit test class for control_api._get_true_device_ids."""

    def test_success(self, mocker: MockFixture):
        """
        Success case: Both IDs are obtained correctly.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        dummy_dim = mocker.patch(
            "app.common.dim.device_id_base.get_device_id_of_switch_port_type",
            side_effect=[DUMMY_TRUE_UPSTREAM_DEVICE_ID, DUMMY_TRUE_DOWNSTREAM_DEVICE_ID],
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = control_api._get_true_device_ids(  # pylint: disable=W0212
            DUMMY_UPSTREAM_DEVICE_ID, DUMMY_DOWNSTREAM_DEVICE_ID
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result == (DUMMY_TRUE_UPSTREAM_DEVICE_ID, DUMMY_TRUE_DOWNSTREAM_DEVICE_ID)

        assert dummy_dim.call_count == 2

    def test_upstream_none(self, mocker: MockFixture):
        """
        If upstream is None, DeviceNotFoundHWControlError should be raised.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock.
        dummy_dim = mocker.patch(
            "app.common.dim.device_id_base.get_device_id_of_switch_port_type",
            side_effect=[None, DUMMY_TRUE_DOWNSTREAM_DEVICE_ID],
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = control_api._get_true_device_ids(  # pylint: disable=W0212
            DUMMY_UPSTREAM_DEVICE_ID, DUMMY_DOWNSTREAM_DEVICE_ID
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result == (DUMMY_UPSTREAM_DEVICE_ID, DUMMY_TRUE_DOWNSTREAM_DEVICE_ID)

        assert dummy_dim.call_count == 2

    def test_downstream_none(self, mocker: MockFixture):
        """
        If downstream is None, DeviceNotFoundHWControlError should be raised.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock.
        dummy_dim = mocker.patch(
            "app.common.dim.device_id_base.get_device_id_of_switch_port_type",
            side_effect=[DUMMY_TRUE_UPSTREAM_DEVICE_ID, None],
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = control_api._get_true_device_ids(  # pylint: disable=W0212
            DUMMY_UPSTREAM_DEVICE_ID, DUMMY_DOWNSTREAM_DEVICE_ID
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result == (DUMMY_TRUE_UPSTREAM_DEVICE_ID, DUMMY_DOWNSTREAM_DEVICE_ID)

        assert dummy_dim.call_count == 2

    @pytest.mark.parametrize(
        "dim_raise",
        [
            exc.DeviceIDFileIncorrectHWControlError,
            exc.DeviceIDFileNotFoundHWControlError,
        ],
    )
    def test_upstream_dim_error(
        self,
        mocker: MockFixture,
        dim_raise: type[exc.BaseHWControlError],
    ):
        """
        If get_device_id_of_switch_port_type raises
        DeviceIDFileIncorrectHWControlError or
        DeviceIDFileNotFoundHWControlError for upstream.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock.
        dummy_dim = mocker.patch(
            "app.common.dim.device_id_base.get_device_id_of_switch_port_type",
            side_effect=dim_raise,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(dim_raise):
            control_api._get_true_device_ids(  # pylint: disable=W0212
                DUMMY_UPSTREAM_DEVICE_ID, DUMMY_DOWNSTREAM_DEVICE_ID
            )

        assert dummy_dim.call_count == 1

    @pytest.mark.parametrize(
        "dim_raise",
        [
            exc.DeviceIDFileIncorrectHWControlError,
            exc.DeviceIDFileNotFoundHWControlError,
        ],
    )
    def test_downstream_dim_error(self, mocker: MockFixture, dim_raise: type[exc.BaseHWControlError]):
        """
        If get_device_id_of_switch_port_type raises
        DeviceIDFileIncorrectHWControlError or
        DeviceIDFileNotFoundHWControlError for downstream.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock.
        dummy_dim = mocker.patch(
            "app.common.dim.device_id_base.get_device_id_of_switch_port_type",
            side_effect=[DUMMY_TRUE_UPSTREAM_DEVICE_ID, dim_raise],
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(dim_raise):
            control_api._get_true_device_ids(  # pylint: disable=W0212
                DUMMY_UPSTREAM_DEVICE_ID, DUMMY_DOWNSTREAM_DEVICE_ID
            )

        assert dummy_dim.call_count == 2

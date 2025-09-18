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

"""Unit test module for control.control_api request models class."""

import uuid

from pydantic import ValidationError
import pytest

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#

from app.routers.control import control_api

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


DUMMY_DEVICE_ID = uuid.UUID("d62e98bf-6c50-4b88-95f9-49c609d2fdc9")


class TestAggregationControlRequestModel:
    """Unit test class for AggregationControlRequestModel."""

    @pytest.mark.parametrize(
        "action", [control_api.AggregationControlAction.CONNECT, control_api.AggregationControlAction.DISCONNECT]
    )
    def test_valid_value_input_case(self, action):
        """Test valid AggregationControlRequestModel creation."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        device_id = DUMMY_DEVICE_ID

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_instance = control_api.AggregationControlRequestModel(deviceID=device_id, action=action)
        dumped_actual_instance = actual_instance.model_dump(by_alias=True)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_instance.device_id == device_id
        assert actual_instance.action == action

        # test for key name alias
        assert dumped_actual_instance == {
            "deviceID": device_id,
            "action": action,
        }

    @pytest.mark.parametrize(
        "input_data",
        [
            # deviceID is None (type error)
            {"deviceID": None, "action": control_api.AggregationControlAction.CONNECT},
            # action is None (type error)
            {"deviceID": DUMMY_DEVICE_ID, "action": None},
            # deviceID is missing
            {"action": control_api.AggregationControlAction.CONNECT},
            # action is missing
            {"deviceID": DUMMY_DEVICE_ID},
            # both are missing
            {},
        ],
    )
    def test_invalid_value_input_case(self, input_data: dict):
        """Test invalid value input and validation errors."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            _ = control_api.AggregationControlRequestModel(**input_data)


class TestDeviceAggregationControlRequestModel:
    """Unit test class for DeviceAggregationControlRequestModel."""

    @pytest.mark.parametrize(
        "action", [control_api.AggregationControlAction.CONNECT, control_api.AggregationControlAction.DISCONNECT]
    )
    def test_valid_value_input_case(self, action):
        """Test valid DeviceAggregationControlRequestModel creation."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        device_id = DUMMY_DEVICE_ID

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_instance = control_api.DeviceAggregationControlRequestModel(destinationDeviceID=device_id, action=action)
        dumped_actual_instance = actual_instance.model_dump(by_alias=True)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_instance.downstream_device_id == device_id
        assert actual_instance.action == action

        # test for key name alias
        assert dumped_actual_instance == {
            "destinationDeviceID": device_id,
            "action": action,
        }

    def test_input_with_alias_key_creates_instance_correctly(self):
        """Test creation of instance with alias key."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Key name alias
        input_data = {"destinationDeviceID": DUMMY_DEVICE_ID, "action": control_api.AggregationControlAction.CONNECT}

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_instance = control_api.DeviceAggregationControlRequestModel(**input_data)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_instance.downstream_device_id == input_data["destinationDeviceID"]
        assert actual_instance.action == input_data["action"]

    @pytest.mark.parametrize(
        "input_data",
        [
            # deviceID is None (type error)
            {"destinationDeviceID": None, "action": control_api.AggregationControlAction.CONNECT},
            # action is None (type error)
            {"destinationDeviceID": DUMMY_DEVICE_ID, "action": None},
            # deviceID is missing
            {"action": control_api.AggregationControlAction.CONNECT},
            # action is missing
            {"destinationDeviceID": DUMMY_DEVICE_ID},
            # both are missing
            {},
        ],
    )
    def test_invalid_value_input_case(self, input_data: dict):
        """Test invalid value input and validation errors."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            _ = control_api.DeviceAggregationControlRequestModel(**input_data)


class TestPowerControlRequestModel:
    """Unit test class for PowerControlRequestModel."""

    @pytest.mark.parametrize(
        "action",
        [
            control_api.PowerControlAction.ON,
            control_api.PowerControlAction.OFF,
            control_api.PowerControlAction.RESET,
            control_api.PowerControlAction.FORCE_OFF,
        ],
    )
    def test_valid_value_input_case(self, action):
        """Test valid PowerControlRequestModel creation."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_instance = control_api.PowerControlRequestModel(action=action)
        dumped_actual_instance = actual_instance.model_dump(by_alias=True)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_instance.action == action

        # test for key name alias
        assert dumped_actual_instance == {"action": action}

    @pytest.mark.parametrize(
        "input_data",
        [
            # action is None (type error)
            {"action": None},
            # action is missing
            {},
        ],
    )
    def test_invalid_value_input_case(self, input_data: dict):
        """Test invalid value input and validation errors."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            _ = control_api.PowerControlRequestModel(**input_data)

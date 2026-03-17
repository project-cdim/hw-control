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

"""Unit test module for control.response_models module ."""

from pydantic import ValidationError
import pytest

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#

from app.routers.control import response_models

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#

DUMMY_UPSTREAM_DEVICE_ID = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"
DUMMY_DOWNSTREAM_DEVICE_ID = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"


class TestDeviceAggregationControlResponseModel:
    """Unit test class for DeviceAggregationControlResponseModel."""

    def test_valid_value_input_case(self):
        """Test valid DeviceAggregationControlResponseModel creation."""

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        upstream_device_id = "451b0faf-b70d-4476-832a-4c93f0e6e1ce"
        downstream_device_id = "123e4567-e89b-12d3-a456-426614174000"

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_instance = response_models.DeviceAggregationControlResponseModel(
            upstream_device_id=upstream_device_id,
            downstream_device_id=downstream_device_id,
        )
        dumped_actual_instance = actual_instance.model_dump(by_alias=True)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_instance.upstream_device_id == upstream_device_id
        assert actual_instance.downstream_device_id == downstream_device_id
        # test for key name alias
        assert dumped_actual_instance == {
            "sourceDeviceID": upstream_device_id,
            "destinationDeviceID": downstream_device_id,
        }

    @pytest.mark.parametrize(
        "input_data",
        [
            # upstream_device_id is None (type error)
            {"upstream_device_id": None, "downstream_device_id": "123e4567-e89b-12d3-a456-426614174000"},
            # downstream_device_id is None (type error)
            {"upstream_device_id": "451b0faf-b70d-4476-832a-4c93f0e6e1ce", "downstream_device_id": None},
            # upstream_device_id is missing (missing required field)
            {"downstream_device_id": "123e4567-e89b-12d3-a456-426614174000"},
            # downstream_device_id is missing (missing required field)
            {"upstream_device_id": "451b0faf-b70d-4476-832a-4c93f0e6e1ce"},
            # both are missing (missing required fields)
            {},
        ],
    )
    def test_invalid_value_input_case(self, input_data: dict):
        """Test invalid value input and validation errors."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            _ = response_models.DeviceAggregationControlResponseModel(**input_data)


class TestPowerControlResponseModel:
    """Unit test class for PowerControlResponseModel."""

    def test_valid_value_input_case(self):
        """Test valid PowerControlResponseModel creation."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        device_id = "451b0faf-b70d-4476-832a-4c93f0e6e1ce"

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_instance = response_models.PowerControlResponseModel(device_id=device_id)
        dumped_actual_instance = actual_instance.model_dump(by_alias=True)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_instance.device_id == device_id

        # test for key name alias
        assert dumped_actual_instance == {"deviceID": device_id}

    @pytest.mark.parametrize(
        "input_data",
        [
            # device_id is None (type error)
            {"device_id": None},
            # device_id is missing (missing required field)
            {},
        ],
    )
    def test_invalid_value_input_case(self, input_data: dict):
        """Test invalid value input and validation errors."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            _ = response_models.PowerControlResponseModel(**input_data)


class TestIsOSReadyResponseModel:
    """Unit test class for IsOSReadyResponseModel."""

    def test_valid_value_input_case(self):
        """Test valid IsOSReadyResponseModel creation."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        status = True
        ip_address = "192.168.1.100"

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_instance = response_models.IsOSReadyResponseModel(status=status, ip_address=ip_address)
        dumped_actual_instance = actual_instance.model_dump(by_alias=True)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_instance.status is True
        assert actual_instance.ip_address == ip_address

        # test for key name alias
        assert dumped_actual_instance == {"status": True, "IPAddress": ip_address}

    @pytest.mark.parametrize(
        "input_data",
        [
            # status is None (type error)
            {"status": None, "ip_address": "192.168.1.100"},
            # ip_address is None (type error)
            {"status": True, "ip_address": None},
            # ip_address is missing (missing required field)
            {"status": True},
            # status is missing (missing required field)
            {"ip_address": "192.168.1.100"},
            # both are missing (missing required fields)
            {},
        ],
    )
    def test_invalid_value_input_case(self, input_data: dict):
        """Test invalid value input and validation errors."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            _ = response_models.IsOSReadyResponseModel(**input_data)

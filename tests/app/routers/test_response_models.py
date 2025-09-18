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

"""Unit test module for routers.response_models module."""

import pytest

from pydantic import ValidationError

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#

from app.routers import response_models

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestErrorResponseModel:
    """Unit test class for ErrorResponseModel."""

    @pytest.mark.parametrize(
        "input_data",
        [  # code: str, message: str
            {"code": "Foo", "message": "bar"},
            # message can be any type (e.g., dict)
            {"code": "Foo", "message": {"detail": "error detail"}},
        ],
    )
    def test_valid_value_input_case(self, input_data: dict):
        """Test valid ErrorResponseModel creation."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        code = input_data["code"]
        message = input_data["message"]

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_instance = response_models.ErrorResponseModel(code=code, message=message)
        assert actual_instance.code == code
        assert actual_instance.message == message

    @pytest.mark.parametrize(
        "input_data",
        [
            # code is None (type error)
            {"code": None, "message": "msg"},
            # code is missing (missing required field)
            {"message": "msg"},
            # message is missing (missing required field)
            {"code": "E001"},
            # both are missing (missing required fields)
            {},
        ],
    )
    def test_invalid_value_input_case(self, input_data: dict):
        """Test invalid value input and validation errors."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            _ = response_models.ErrorResponseModel(**input_data)

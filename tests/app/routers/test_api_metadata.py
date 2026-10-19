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

"""Unit test module for api_metadata.py module."""

from app.routers import api_metadata, response_models


class TestErrorExampleFactory:
    """Test class for error_example_factory function."""

    def test_can_set_error_case_spec(self):
        """
        Test that the function returns the correct dictionary structure.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        input_case_description = "Test error case."

        expected_error_example = {
            "description": input_case_description,
            "model": response_models.ErrorResponseModel,
            "content": {
                "application/json": {
                    "example": {
                        "code": "< An error code will be provided here >",
                        "message": "< A detailed error message will be provided here >",
                    },
                }
            },
        }

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual = api_metadata.error_case_spec_factory(input_case_description)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual == expected_error_example


class TestValidationErrorExampleFactory:
    """Test class for validation_error_case_spec_factory function."""

    def test_can_set_error_case_spec(self):
        """
        Test that the function returns the correct dictionary structure.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        input_case_description = "Test validation error case."

        expected_error_example = {
            "description": input_case_description,
            "model": response_models.ValidationErrorResponseModel,
            "content": {
                "application/json": {
                    "example": {
                        "code": "< An error code will be provided here >",
                        "message": "< A detailed error message will be provided here >",
                        "detail": [
                            {
                                "type": "< The type of the validation error will be provided here >",
                                "loc": ["< The location of the invalid request parameter will be provided here >"],
                                "msg": "< A message describing the validation error will be provided here >",
                                "input": "< The invalid input value will be provided here >",
                            },
                        ],
                    },
                }
            },
        }

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual = api_metadata.validation_error_case_spec_factory(input_case_description)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual == expected_error_example


class TestErrorExamplesFactory:
    """Test class for error_example_factory function."""

    def test_can_set_error_case_spec(self):
        """
        Test that the function returns the correct dictionary structure.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        input_case_description = "Test error case."
        input_sub_case_descriptions = ["Test sub error case 01.", "Test sub error case 02.", "Test sub error case 03."]

        expected_error_example = {
            "description": input_case_description,
            "model": response_models.ErrorResponseModel,
            "content": {
                "application/json": {
                    "examples": {
                        "error case0": {
                            "summary": input_sub_case_descriptions[0],
                            "value": {
                                "code": "< An error code will be provided here >",
                                "message": "< A detailed error message will be provided here >",
                            },
                        },
                        "error case1": {
                            "summary": input_sub_case_descriptions[1],
                            "value": {
                                "code": "< An error code will be provided here >",
                                "message": "< A detailed error message will be provided here >",
                            },
                        },
                        "error case2": {
                            "summary": input_sub_case_descriptions[2],
                            "value": {
                                "code": "< An error code will be provided here >",
                                "message": "< A detailed error message will be provided here >",
                            },
                        },
                    }
                }
            },
        }

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual = api_metadata.error_cases_spec_factory(
            case_description=input_case_description, sub_case_descriptions=input_sub_case_descriptions
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#

        assert actual == expected_error_example

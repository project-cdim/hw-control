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

"""Tests Basic Exceptions module."""
import pytest

import app.common.basic_exceptions as exc  # type: ignore


class TestBaseHwControlError:
    """Test BaseHwControlError class

    This class tests BaseHwControlError class
    """

    def test_set_error_values_methods(self):
        """Test set default error information."""
        # preparation
        expected_status_code = 500
        expected_error_code = "CF000BAS000"
        expected_error_message = "The server encountered an internal error and was unable to complete your request."

        # execution
        try:
            raise exc.BaseHwControlError
        except exc.BaseHwControlError as error_object:
            actual_status_code = error_object.http_code
            actual_error_code = error_object.error_code
            actual_error_message = error_object.message
            # inspection
            assert actual_status_code == expected_status_code
            assert actual_error_code == expected_error_code
            assert actual_error_message == expected_error_message

    def test_append_error_message(self):
        """test BaseHwControlError.append_error_message"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        expected_error_message_01 = (
            "The server encountered an internal error and was unable to complete your request."
            " test_additional_message_01"
        )
        expected_error_message_02 = (
            "The server encountered an internal error and was unable to complete your request."
            " test_additional_message_01 test_additional_message_02"
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        error_instance = exc.BaseHwControlError()

        error_instance.append_error_message(additional_message="test_additional_message_01")
        actual_error_message_01 = error_instance.message

        error_instance.append_error_message(additional_message="test_additional_message_02")
        actual_error_message_02 = error_instance.message

        # ++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert expected_error_message_01 == actual_error_message_01
        assert expected_error_message_02 == actual_error_message_02

    def test_to_error_dict(self):
        """test BaseHwControlError.to_error_dict"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        expected_error_message = "The server encountered an internal error and was unable to complete your request."

        expected_error_dict = {"errorCode": "CF000BAS000", "errorMessage": expected_error_message}

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_error_instance = exc.BaseHwControlError()
        actual_error_dict = actual_error_instance.to_error_dict()

        # ++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_error_dict == expected_error_dict

    def test_generate_api_response(self):
        """test generate_api_response

        This method tests generate_api_response methods.
        """
        # preparation
        expected_error_message = "The server encountered an internal error and was unable to complete your request."

        expected_status_code = 500
        expected_response_body = f'{{"code":"CF000BAS000","message":"{expected_error_message}"}}'
        # execution
        try:
            raise exc.BaseHwControlError
        except exc.BaseHwControlError as error_object:
            actual = error_object.generate_api_response()
            # inspection
            assert actual.status_code == expected_status_code
            assert actual.body.decode("utf-8") == expected_response_body

    @pytest.mark.parametrize(
        "error_information",
        [
            (  # str
                "test_error_information_01",
                "test_error_information_01",
            ),
            (  # int, float, bool
                1,
                3.14,
                True,
                None,
            ),
            (  # tuple, list, dict
                (1, "test", None),
                [3.14, "test", None, True],
                {"is_valid": True, "pi": 3.14},
            ),
            ((), [], {}),  # empty
        ],
    )
    def test_can_set_error_information(self, error_information: tuple):
        """test can set error information for BaseException.args."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++++++++++#
        expected_error_information = error_information

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        sut = exc.BaseHwControlError(*error_information)
        actual_error_information = sut.args

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_error_information == expected_error_information


@pytest.mark.parametrize(
    "exception_class, expected_status_code, expected_error_code, expected_error_message",
    [
        (
            exc.BaseHwControlError,
            500,
            "CF000BAS000",
            (
                "The server encountered an internal error and was unable to complete your request."
                " test_additional_message_01 test_additional_message_02"
            ),
        ),
        (
            exc.UnknownHwControlError,
            500,
            "CF001BAS000",
            (
                "The server encountered an internal error and was unable to complete your request."
                " test_additional_message_01 test_additional_message_02"
            ),
        ),
        (
            exc.AuthenticationHwControlError,
            401,
            "EF002BAS000",
            ("Authentication failed. test_additional_message_01 test_additional_message_02"),
        ),
        (
            exc.BadRequestHwControlError,
            400,
            "EF003BAS000",
            ("Your request is invalid. test_additional_message_01 test_additional_message_02"),
        ),
        (
            exc.ControlObjectHwControlError,
            500,
            "EF004BAS000",
            ("Failed to operate the specified device. test_additional_message_01 test_additional_message_02"),
        ),
        (
            exc.ResourceBusyHwControlError,
            503,
            "ER005BAS000",
            ("The specified resource is busy. test_additional_message_01 test_additional_message_02"),
        ),
        (
            exc.ConfigurationHwControlError,
            500,
            "EF007BAS000",
            (
                "Your request failed due to the missing required system configuration."
                " test_additional_message_01 test_additional_message_02"
            ),
        ),
        (
            exc.InternalHwControlError,
            500,
            "EF010BAS000",
            ("The server encountered an internal error. test_additional_message_01 test_additional_message_02"),
        ),
        (
            exc.RequestConflictHwControlError,
            409,
            "EF011BAS000",
            (
                "The request conflicts with the current resource state."
                " test_additional_message_01 test_additional_message_02"
            ),
        ),
        (
            exc.DependencyServiceHwControlError,
            500,
            "EF012BAS000",
            (
                "Operation could not be completed due to a failure in external dependencies."
                " test_additional_message_01 test_additional_message_02"
            ),
        ),
        (
            exc.DeviceNotFoundHwControlError,
            404,
            "EF013BAS000",
            "The specified target device is not found. test_additional_message_01 test_additional_message_02",
        ),
    ],
)
def test_initialize_instance_and_set_additional_message(
    exception_class,
    expected_status_code,
    expected_error_code,
    expected_error_message,
):
    """Test can initialize instance and generate response.

    This test checks that the BaseHwControlError various derived
    exception classes are correctly initialized with the expected status code,
    error code, error message, and additional message.
    It also ensures that the generated API response
    from the exception object matches the expected format and content.

    Args:
        exception_class: The exception class to be tested.
        expected_status_code: The HTTP status code expected from the exception.
        expected_error_code: The specific error code expected from the exception.
        expected_error_message: The expected error message generate by exception class.

    """
    # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
    expected_response_body = f'{{"code":"{expected_error_code}","message":"{expected_error_message}"}}'
    expected_error_dict = {"errorCode": expected_error_code, "errorMessage": expected_error_message}

    # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#

    try:
        raise exception_class("test_error_information", additional_message="test_additional_message_01")
    except exc.BaseHwControlError as error_object:
        error_object.append_error_message(additional_message="test_additional_message_02")

        actual_response_object = error_object.generate_api_response()
        actual_error_information = error_object.args
        actual_error_dict = error_object.to_error_dict()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++#
        assert error_object.http_code == expected_status_code
        assert error_object.error_code == expected_error_code
        assert error_object.message == expected_error_message
        assert actual_error_information == ("test_error_information",)

        assert actual_error_dict == expected_error_dict

        assert actual_response_object.status_code == expected_status_code
        assert actual_response_object.body.decode("utf-8") == expected_response_body

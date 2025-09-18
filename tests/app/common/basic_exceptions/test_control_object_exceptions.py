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

"""Tests control_object_exceptions module."""
import pytest


import app.common.basic_exceptions as exc


@pytest.mark.parametrize(
    "exception_class, expected_status_code, expected_error_code, expected_error_message",
    [
        (
            exc.FMConnectFailureHWControlError,
            500,
            "EF004BAS001",
            (
                "The Fabric Manager failed to establish a connection between the specified Host CPU and target device."
                " test_additional_message_01 test_additional_message_02"
            ),
        ),
        (
            exc.FMDisconnectFailureHWControlError,
            500,
            "EF004BAS002",
            (
                "The Fabric Manager failed to disconnect a connection between the specified Host CPU"
                " and the target device."
                " test_additional_message_01 test_additional_message_02"
            ),
        ),
        (
            exc.PowerOnFailureHWControlError,
            500,
            "EF004BAS003",
            (
                "The Out-of-Band Controller failed to power on the specified device."
                " test_additional_message_01 test_additional_message_02"
            ),
        ),
        (
            exc.PowerOffFailureHWControlError,
            500,
            "EF004BAS004",
            (
                "The Out-of-Band Controller failed to power off the specified device."
                " test_additional_message_01 test_additional_message_02"
            ),
        ),
        (
            exc.CPUResetFailureHWControlError,
            500,
            "EF004BAS005",
            (
                "The Out-of-Band Controller failed to reset the specified Host CPU."
                " test_additional_message_01 test_additional_message_02"
            ),
        ),
        (
            exc.AgentConnectFailureHWControlError,
            500,
            "EF004BAS006",
            "Failed to connect to the HW Control Agent. test_additional_message_01 test_additional_message_02",
        ),
        (
            exc.AgentGetInformationFailureHWControlError,
            500,
            "EF004BAS007",
            (
                "The HW Control Agent failed to get information from the Host OS."
                " test_additional_message_01 test_additional_message_02"
            ),
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

    This test checks that the ControlObjectHWControlError various derived
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
    except exc.ControlObjectHWControlError as error_object:
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

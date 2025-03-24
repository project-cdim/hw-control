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

"""Test module for resource_not_found_exceptions.py."""

import pytest

import app.common.basic_exceptions as exc  # type: ignore


@pytest.mark.parametrize(
    "exception_class, expected_status_code, expected_error_code, expected_error_message",
    [
        (
            exc.HostCpuNotFoundHwControlError,
            404,
            "EF013BAS001",
            "The specified Host CPU is not found. test_additional_message_01 test_additional_message_02",
        ),
        (
            exc.HostCpuAndDeviceNotFoundHwControlError,
            404,
            "EF013BAS002",
            (
                "The specified Host CPU and target device are not found."
                " test_additional_message_01 test_additional_message_02"
            ),
        ),
        (
            exc.ResourceNotFoundHwControlError,
            404,
            "EF013BAS003",
            "The specified resource is not found. test_additional_message_01 test_additional_message_02",
        ),
        (
            exc.SwitchNotFoundHwControlError,
            404,
            "EF013BAS004",
            "The specified switch is not found. test_additional_message_01 test_additional_message_02",
        ),
        (
            exc.DeviceIdNotFoundHwControlError,
            404,
            "EF013BAS005",
            "The specified Device ID is not found. test_additional_message_01 test_additional_message_02",
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

    This test checks that the DeviceNotFoundHwControlError various derived
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
    except exc.DeviceNotFoundHwControlError as error_object:
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

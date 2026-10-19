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

"""This is a test program."""

from app.common.basic_exceptions import ERROR_CODE, ERROR_MESSAGE
from app.common.utils import error_utils


def test_remove_duplicates_none():
    """Remove error duplicate none"""
    errors_input = []

    errors_output = []

    errors = error_utils.remove_duplicates(errors_input)

    assert errors == errors_output


def test_remove_duplicates():
    """Remove error duplicate"""
    errors_input = [
        {ERROR_CODE: "001", ERROR_MESSAGE: "error_message_001"},
        {ERROR_CODE: "002", ERROR_MESSAGE: "error_message_002"},
        {ERROR_CODE: "001", ERROR_MESSAGE: "error_message_001_1"},
        {ERROR_CODE: "003", ERROR_MESSAGE: "error_message_003"},
        {ERROR_CODE: "001", ERROR_MESSAGE: "error_message_001"},
    ]

    errors_output = [
        {ERROR_CODE: "001", ERROR_MESSAGE: "error_message_001"},
        {ERROR_CODE: "002", ERROR_MESSAGE: "error_message_002"},
        {ERROR_CODE: "001", ERROR_MESSAGE: "error_message_001_1"},
        {ERROR_CODE: "003", ERROR_MESSAGE: "error_message_003"},
    ]

    errors = error_utils.remove_duplicates(errors_input)

    assert errors == errors_output

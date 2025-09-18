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

"""Unit test module for request_id_utilities.py"""

import uuid

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.common import request_id_utilities

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestGetRequestID:
    """Test class for request_id.get_request_id."""

    def test_get_request_id(self):
        """Test get_request_id can get request_id value."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        input_request_id = str(uuid.uuid4())
        expected_request_id = input_request_id

        token = request_id_utilities._request_id.set(input_request_id)  # pylint: disable=W0212

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_request_id = request_id_utilities.get_request_id()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_request_id == expected_request_id

        # ++++ clean up +++++++++++++++++++++++++++++++++++++++++++++++#
        request_id_utilities._request_id.reset(token)  # pylint: disable=W0212

    def test_get_request_id_returns_empty_string_if_not_set(self):
        """Test get_request_id returns an empty string when the request_id is not set."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        expected_request_id = ""

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_request_id = request_id_utilities.get_request_id()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_request_id == expected_request_id

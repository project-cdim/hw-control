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

"""Unit test module for custom_filters.py ."""

import logging

import pytest
from pytest_mock import MockFixture

from app.common import request_id_utilities

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.common.log.filters import RequestIDFilter

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestRequestIDFilter:
    """Test class for RequestIDFilter."""

    @pytest.mark.parametrize(
        "dummy_request_id",
        [
            "test request id",
            "",
        ],
    )
    def test_request_id_filter_adds_request_id(
        self,
        mocker: MockFixture,
        dummy_request_id: str,
    ):
        """Test that RequestIDFilter adds the request_id to the log record."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set up the mock.
        mocker.patch.object(request_id_utilities, "get_request_id", return_value=dummy_request_id)

        # Create a dummy LogRecord
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        expected_request_id = dummy_request_id

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        # Apply the filter
        filter_instance = RequestIDFilter()
        result = filter_instance.filter(record)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # Assert that filter returns True and request_id is set correctly
        assert result is True
        assert hasattr(record, "request_id")
        assert getattr(record, "request_id") == expected_request_id

    def test_filter_overwrites_existing_request_id(
        self,
        mocker: MockFixture,
    ):
        """Test that RequestIDFilter overwrites existing request_id attribute.

        This test verifies that when a LogRecord already has a request_id attribute
        (simulating the case where it was set via `extra` parameters in logger.log()),
        the RequestIDFilter will overwrite it with the value obtained from
        request_id_utilities.get_request_id().

        Args:
            mocker (MockFixture): Pytest mock fixture for patching dependencies.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        filter_set_request_id = "filter set request ID"

        # Set up the mock.
        mocker.patch.object(request_id_utilities, "get_request_id", return_value=filter_set_request_id)

        # Create a dummy LogRecord
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # Manually set request_id to simulate it being set by `extra` parameters
        existing_request_id = "existing Request ID from Logger.log extra parameter"
        record.request_id = existing_request_id

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        # Apply the filter
        filter_instance = RequestIDFilter()
        result = filter_instance.filter(record)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result is True
        assert hasattr(record, "request_id")
        assert getattr(record, "request_id") == filter_set_request_id

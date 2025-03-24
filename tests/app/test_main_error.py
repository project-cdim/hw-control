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

"""Unit test module for hw_control_main.py."""

import unittest
from unittest.mock import patch
from app import hw_control_main


class TestHwControlMain(unittest.TestCase):
    """Unit test class for hw_control_main."""

    def test_main(self):
        """Test execution of hw_control_main."""

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        actual = hw_control_main

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++++++++++#
        # The test method will stop if an error occurs.
        print(actual)

    @patch("src.app.hw_control_main.FastAPI.include_router")
    def test_library_not_install(self, start_hw_control_mock):
        """Test library not install."""

        start_hw_control_mock.side_effect = ImportError("hogehoge")
        actual = None
        try:
            actual = hw_control_main.start_hw_control()
        except SystemExit:  # NOSONAR
            pass

        assert actual is None

    @patch("src.app.hw_control_main.FastAPI.include_router")
    def test_not_log_folder(self, start_hw_control_mock):
        """Test not log folder."""

        start_hw_control_mock.side_effect = Exception("hogehoge")
        actual = None
        try:
            actual = hw_control_main.start_hw_control()
        except SystemExit:  # NOSONAR
            pass

        assert actual is None

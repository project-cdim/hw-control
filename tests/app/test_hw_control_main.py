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

from app import hw_control_main  # type: ignore


class TestHwControlMain:
    """Unit test class for hw_control_main."""

    def test_main(self):
        """Test execution of hw_control_main."""

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        actual = hw_control_main

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++++++++++#
        # The test method will stop if an error occurs.
        print(actual)
        assert True

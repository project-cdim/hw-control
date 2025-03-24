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

"""This is a test program."""


class TestPlugin:  # pylint: disable=R0903
    """UT plugin"""

    def __init__(self, value):
        print(f"value = {value}")
        self.test_value = value
        print(f"test1 value = {self.test_value}")
        print("init test1")

    def get_port_info(self):
        """get_port_info

        displays test_value for the get_port_info.
        """
        print(f"get_port_info test1 value = {self.test_value}")


class InvalidPlugin:  # pylint: disable=R0903
    """UT Invalid plugin"""

    def __init__(self, value):
        """raise Unexpected exception"""
        raise ZeroDivisionError

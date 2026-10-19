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

from app.common.utils.plugin_base import ManagerPluginBase


class NoInitPlugin(ManagerPluginBase):
    """UT plugin that does not define its own __init__.

    A legacy plugin may omit __init__ and rely on ManagerPluginBase, so
    the constructor must accept the None passed when the plugin
    configuration file has no specific_data.
    """


class TestPlugin:
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


class InvalidPlugin:
    """UT Invalid plugin"""

    def __init__(self, _value):
        """raise Unexpected exception"""
        raise ZeroDivisionError

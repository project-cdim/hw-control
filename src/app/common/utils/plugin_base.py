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

"""Module that defined the base class of Manager plug-in.

File: hw-control/src/app/common/utils/plugin_base.py
"""


class ManagerPluginBase:
    """Base class of Manager plug-in.

    Common API definition for plugins, including constructors

    """

    def __init__(self, specific_data: dict | None) -> None:
        """Initialize the plugin with plugin-specific data.

        `None` is accepted because the plugin configuration file may omit
        `specific_data`, and because the plugin framework may call the
        constructor with `None` to check the plugin interface.

        Args:
            specific_data (dict | None): Plugin-specific configuration or
                data. `None` when it is not configured.
        """
        self.specific_data = specific_data

# Copyright 2026 NEC Corporation
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
# under the License.

"""Unit test module for app/common/utils/plugin_base.py."""

import pytest

from app.common.utils.plugin_base import ManagerPluginBase


class TestManagerPluginBase:
    """Test ManagerPluginBase.__init__."""

    def test_valid_dict_is_kept(self):
        """A dict is accepted and stored as-is."""
        instance = ManagerPluginBase({"test_key": "test_value"})
        assert instance.specific_data == {"test_key": "test_value"}

    def test_none_is_accepted(self):
        """None is accepted and stored as-is.

        The plugin configuration file may omit `specific_data`, and the
        plugin framework may pass None to check the plugin interface.
        """
        instance = ManagerPluginBase(None)
        assert instance.specific_data is None

    def test_missing_argument_raises_type_error(self):
        """`specific_data` has no default value, so it must be given."""
        with pytest.raises(TypeError):
            ManagerPluginBase()  # type: ignore[call-arg]

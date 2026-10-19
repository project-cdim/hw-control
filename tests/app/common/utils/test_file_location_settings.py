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

"""Unit test module for file_location_settings.py ."""

from app.common.utils import file_location_settings


class TestFileLocationSettings:
    """Unit test class for FileLocationSettings"""

    def test_instance_generate_default_value(self, monkeypatch):
        """test for FileLocationSettings instance generate default value"""
        # Set up the expected value.
        expected_conf = "/opt/cdim/hw-control/config/"
        expected_data = "/opt/cdim/hw-control/data/"
        expected_plugin = "/opt/cdim/hw-control/data/plugins"

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_CONFIG_FILE_DIR", raising=False)
        monkeypatch.delenv("HW_CONTROL_DATA_FILE_DIR", raising=False)
        monkeypatch.delenv("HW_CONTROL_PLUGIN_FILE_DIR", raising=False)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_setting = file_location_settings.FileLocationSettings()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_setting.config_file_dir == expected_conf
        assert actual_setting.data_file_dir == expected_data
        assert actual_setting.plugin_file_dir == expected_plugin

    def test_env_case_sensitive(self, monkeypatch):
        """Test environment case sensitive."""

        # Set up the expected value.
        expected_conf = "/opt/cdim/hw-control/config/"
        expected_data = "/opt/cdim/hw-control/data/"
        expected_plugin = "/opt/cdim/hw-control/data/plugins"

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_CONFIG_FILE_DIR", raising=False)
        monkeypatch.delenv("HW_CONTROL_DATA_FILE_DIR", raising=False)
        monkeypatch.delenv("HW_CONTROL_PLUGIN_FILE_DIR", raising=False)

        # Set up the mock.
        monkeypatch.setenv("hw_control_config_file_dir", "/dev/null")
        monkeypatch.setenv("hw_control_data_file_dir", "/dev/null")
        monkeypatch.setenv("hw_control_plugin_file_dir", "/dev/null")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_setting = file_location_settings.FileLocationSettings()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # The initial values of the class are expected to be set.
        assert actual_setting.config_file_dir == expected_conf
        assert actual_setting.data_file_dir == expected_data
        assert actual_setting.plugin_file_dir == expected_plugin

    def test_instance_generate_from_env(self, monkeypatch):
        """Test environment variables set case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set up the expected value.
        expected_conf = "/dev/null"
        expected_data = "/tmp/"
        expected_plugin = "/tmp/plugin"

        # Set up the mock.
        monkeypatch.setenv("HW_CONTROL_CONFIG_FILE_DIR", "/dev/null")
        monkeypatch.setenv("HW_CONTROL_DATA_FILE_DIR", "/tmp/")
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", "/tmp/plugin")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_setting = file_location_settings.FileLocationSettings()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_setting.config_file_dir == expected_conf
        assert actual_setting.data_file_dir == expected_data
        assert actual_setting.plugin_file_dir == expected_plugin

    def test_instance_generate_from_env_relative_path(self, monkeypatch):
        """Test environment variables set case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set up the expected value.
        expected_conf = "./config"
        expected_data = "./data"
        expected_plugin = "./plugin"

        # Set up the mock.
        monkeypatch.setenv("HW_CONTROL_CONFIG_FILE_DIR", "./config")
        monkeypatch.setenv("HW_CONTROL_DATA_FILE_DIR", "./data")
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", "./plugin")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_setting = file_location_settings.FileLocationSettings()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_setting.config_file_dir == expected_conf
        assert actual_setting.data_file_dir == expected_data
        assert actual_setting.plugin_file_dir == expected_plugin

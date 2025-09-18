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

"""Unit test module for secret_management_settings.py ."""

import pytest
from pytest import MonkeyPatch
from pydantic import ValidationError

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.common.utils.secret_management_utilities import secret_management_settings

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestSecretManagementSettings:
    """Unit test class for SecretManagementSettings"""

    def test_instance_generate_default_value(self, monkeypatch: MonkeyPatch):
        """test for SecretManagementSettings instance generate default value"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_SECRET_API_HOST", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PORT", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PATH", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_TIMEOUT", raising=False)

        expected_host = "localhost"
        expected_port = 3500
        expected_path = "/v1.0/secrets/"
        expected_timeout = 3

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_setting = secret_management_settings.SecretManagementSettings()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_setting.host == expected_host
        assert actual_setting.port == expected_port
        assert actual_setting.path == expected_path
        assert actual_setting.timeout == expected_timeout

    def test_env_case_sensitive(self, monkeypatch: MonkeyPatch):
        """Test environment case sensitive."""

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_SECRET_API_HOST", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PORT", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PATH", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_TIMEOUT", raising=False)

        # Set up the mock.
        monkeypatch.setenv("hw_control_secret_api_host", "example.com")
        monkeypatch.setenv("hw_control_secret_api_port", str(8000))
        monkeypatch.setenv("hw_control_secret_api_path", "/foo/var")
        monkeypatch.setenv("hw_control_secret_api_timeout", str(4))

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_setting = secret_management_settings.SecretManagementSettings()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # The initial values of the class are expected to be set.
        assert actual_setting.host == "localhost"  # default value
        assert actual_setting.port == 3500  # default value
        assert actual_setting.path == "/v1.0/secrets/"  # default value
        assert actual_setting.timeout == 3  # default value

    def test_instance_generate_from_env(self, monkeypatch: MonkeyPatch):
        """Test environment variables set case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set up the expected value.
        expected_host = "example.com"
        expected_port = 8080
        expected_path = "/secrets"
        expected_timeout = 5

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_SECRET_API_HOST", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PORT", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PATH", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_TIMEOUT", raising=False)

        # Set up the mock.
        monkeypatch.setenv("HW_CONTROL_SECRET_API_HOST", expected_host)
        monkeypatch.setenv("HW_CONTROL_SECRET_API_PORT", str(expected_port))
        monkeypatch.setenv("HW_CONTROL_SECRET_API_PATH", expected_path)
        monkeypatch.setenv("HW_CONTROL_SECRET_API_TIMEOUT", str(expected_timeout))

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_setting = secret_management_settings.SecretManagementSettings()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_setting.host == expected_host
        assert actual_setting.port == expected_port
        assert actual_setting.path == expected_path
        assert actual_setting.timeout == expected_timeout

    @pytest.mark.parametrize(
        "env_key, env_value",
        [
            ("HW_CONTROL_SECRET_API_PORT", "test_str"),  # port must be int
            ("HW_CONTROL_SECRET_API_PORT", -1),  # port must be greater than 0.
            ("HW_CONTROL_SECRET_API_PORT", 65536),  # port must be less than 65535.
            ("HW_CONTROL_SECRET_API_TIMEOUT", "test_str"),  # timeout must be int
            ("HW_CONTROL_SECRET_API_TIMEOUT", 0),  # timeout must be greater than 1.
            ("HW_CONTROL_SECRET_API_TIMEOUT", 11),  # timeout must be less than 10.
        ],
    )
    def test_invalid_env(self, monkeypatch: MonkeyPatch, env_key, env_value):
        """Test invalid environment variables set case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_SECRET_API_HOST", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PORT", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PATH", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_TIMEOUT", raising=False)

        # Set up the mock.
        monkeypatch.setenv(env_key, str(env_value))

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            _ = secret_management_settings.SecretManagementSettings()

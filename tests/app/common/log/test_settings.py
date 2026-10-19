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

"""Unit test class for settings.py."""

import pytest
from pydantic import ValidationError

from app.common.log import settings


class TestLoggingSettings:
    """Unit test class for LoggingSettings"""

    def test_instance_generate_default_value(self, monkeypatch: pytest.MonkeyPatch):
        """test for LoggingSettings instance generate default value"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_LOGGING_RAISE_EXCEPTIONS", raising=False)

        expected_logging_raise_exceptions = False

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_setting = settings.LoggingSettings()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_setting.logging_raise_exceptions == expected_logging_raise_exceptions

    def test_env_case_sensitive(self, monkeypatch: pytest.MonkeyPatch):
        """Test environment variable case sensitivity."""

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_LOGGING_RAISE_EXCEPTIONS", raising=False)

        # Set up the mock.
        monkeypatch.setenv("hw_control_logging_raise_exceptions", "True")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_setting = settings.LoggingSettings()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # The initial values of the class are expected to be set.
        assert actual_setting.logging_raise_exceptions is False, "Expected logging_raise_exceptions to be default."

    @pytest.mark.parametrize(
        ("env_key", "input_env", "expected_value"),
        [
            ("HW_CONTROL_LOGGING_RAISE_EXCEPTIONS", "True", True),
            ("HW_CONTROL_LOGGING_RAISE_EXCEPTIONS", "true", True),
            ("HW_CONTROL_LOGGING_RAISE_EXCEPTIONS", "1", True),
            ("HW_CONTROL_LOGGING_RAISE_EXCEPTIONS", "False", False),
            ("HW_CONTROL_LOGGING_RAISE_EXCEPTIONS", "false", False),
            ("HW_CONTROL_LOGGING_RAISE_EXCEPTIONS", "0", False),
        ],
    )
    def test_instance_generate_from_env(
        self, monkeypatch: pytest.MonkeyPatch, env_key: str, input_env: str, expected_value: bool
    ):
        """Test environment variables set case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv(env_key, raising=False)

        # Set up the mock.
        monkeypatch.setenv("HW_CONTROL_LOGGING_RAISE_EXCEPTIONS", input_env)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_setting = settings.LoggingSettings()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # The initial values of the class are expected to be set.
        assert actual_setting.logging_raise_exceptions is expected_value

    @pytest.mark.parametrize(
        ("env_key", "env_value"),
        [
            ("HW_CONTROL_LOGGING_RAISE_EXCEPTIONS", ""),
            ("HW_CONTROL_LOGGING_RAISE_EXCEPTIONS", "None"),
            ("HW_CONTROL_LOGGING_RAISE_EXCEPTIONS", "-1"),
            ("HW_CONTROL_LOGGING_RAISE_EXCEPTIONS", "2"),
        ],
    )
    def test_invalid_env(self, monkeypatch: pytest.MonkeyPatch, env_key: str, env_value):
        """Test invalid environment variables set case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv(env_key, raising=False)

        # Set up the mock.
        monkeypatch.setenv(env_key, env_value)

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            _ = settings.LoggingSettings()

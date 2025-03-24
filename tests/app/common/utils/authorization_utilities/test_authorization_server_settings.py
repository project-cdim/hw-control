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

"""Unit test module for authorization_server_settings.py ."""

import pytest
from pydantic import ValidationError

from tests import test_util

from app.common.messages import message  # type: ignore

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.common.utils.authorization_utilities import authorization_server_settings  # type: ignore

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestLogMessageModel:
    """Unit test class for Log Message Class"""

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "log_message_class, expected_default_value",
        [
            (
                authorization_server_settings.AuthorizationServerSettingsLog,
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": None,
                    "action": "Get Authorization Server settings form environment variables.",
                    "token_endpoint": None,
                    "timeout": None,
                },
            ),
        ],
    )
    def test_default_values(self, log_message_class: message.BaseLogMessage, expected_default_value):
        """test create instance default values."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_log_message = log_message_class().to_json_encodable()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_log_message == expected_default_value

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "log_message_class, logging_contents, expected_contents",
        [
            (
                authorization_server_settings.AuthorizationServerSettingsLog,
                {
                    "detail": "test_string",
                    "token_endpoint": "https://authorization-server.example.com/path/to/access_token_endpoint",
                    "timeout": 10,
                },
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "Get Authorization Server settings form environment variables.",
                    "token_endpoint": "https://authorization-server.example.com/path/to/access_token_endpoint",
                    "timeout": 10,
                },
            ),
        ],
    )
    def test_custom_values(
        self, log_message_class: message.BaseLogMessage, logging_contents: dict, expected_contents: dict
    ):
        """test create instance custom values."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        log_message = log_message_class(**logging_contents).to_json_encodable()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert log_message == expected_contents


class TestSecretManagementSettings:
    """Unit test class for AuthorizationServerSettings"""

    def test_instance_generate_default_value(self, monkeypatch):
        """test for AuthorizationServerSettings instance generate default value"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the expected value.
        expected_token_endpoint = "https://authorization-server.example.com/path/to/access_token_endpoint"
        expected_timeout = 3  # Test AuthorizationServerSettings can set default value.

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT", raising=False)
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT", raising=False)

        # Set up the mock.
        monkeypatch.setenv(
            "HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT",
            "https://authorization-server.example.com/path/to/access_token_endpoint",
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_setting = authorization_server_settings.AuthorizationServerSettings()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert str(actual_setting.token_endpoint) == expected_token_endpoint
        assert actual_setting.timeout == expected_timeout

    def test_env_case_sensitive(self, monkeypatch):
        """Test environment case sensitive."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT", raising=False)
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT", raising=False)

        # Set up the mock.
        monkeypatch.setenv(
            "hw_control_authorization_server_token_endpoint",
            "https://authorization-server.example.com/path/to/access_token_endpoint",
        )

        monkeypatch.setenv(
            "hw_control_authorization_server_timeout",
            str(4),
        )

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            _ = authorization_server_settings.AuthorizationServerSettings()

    def test_instance_generate_from_env(self, monkeypatch):
        """Test environment variables set case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set up the expected value.
        expected_token_endpoint = "http://example.com:8000/realms/"
        expected_timeout = 5

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT", raising=False)
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT", raising=False)

        # Set up the mock.
        monkeypatch.setenv("HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT", expected_token_endpoint)
        monkeypatch.setenv("HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT", str(expected_timeout))

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_setting = authorization_server_settings.AuthorizationServerSettings()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert str(actual_setting.token_endpoint) == expected_token_endpoint
        assert actual_setting.timeout == expected_timeout

    @pytest.mark.parametrize(
        "env_settings",
        [
            [
                ("HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT", "invalid_token_endpoint"),
                ("HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT", 5),
            ],  # token endpoint must be URL
            [
                (
                    "HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT",
                    "https://authorization-server.example.com/path/to/access_token_endpoint",
                ),
                ("HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT", 11),
            ],  # timeout must be less than 10.
            [
                (
                    "HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT",
                    "https://authorization-server.example.com/path/to/access_token_endpoint",
                ),
                ("HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT", 0),
            ],  # timeout must be greater than 1.
        ],
    )
    def test_invalid_env(self, monkeypatch, env_settings):
        """Test invalid environment variables set case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT", raising=False)
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT", raising=False)

        # Set up the mock.
        for env_name, env_value in env_settings:
            monkeypatch.setenv(env_name, str(env_value))

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            _ = authorization_server_settings.AuthorizationServerSettings()

    @pytest.mark.parametrize(
        "env_settings",
        [
            [
                ("HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT", 5),
            ],  # The token endpoint env not set case.
        ],
    )
    def test_unset_env_error_case(
        self,
        monkeypatch,
        env_settings: list,
    ):
        """Test environment variables not set case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT", raising=False)
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT", raising=False)

        # Set up the mock.
        for env_name, env_value in env_settings:
            monkeypatch.setenv(env_name, str(env_value))

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            _ = authorization_server_settings.AuthorizationServerSettings()

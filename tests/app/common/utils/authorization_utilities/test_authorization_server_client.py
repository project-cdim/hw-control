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

"""Unit test module for secret_management_client.py ."""

import logging
from http import HTTPStatus

import pytest
from pytest import MonkeyPatch, LogCaptureFixture
from pytest_mock import MockFixture

from pydantic import ValidationError
import requests

from tests import test_util

import app.common.basic_exceptions as exc
from app.common.utils.secret_management_utilities import secret_management_client

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.common.utils.authorization_utilities import authorization_server_client

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestClientCredential:
    """Unit test class for ClientCredential"""

    def test_valid_client_credential(self):
        """Test valid client credential case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set up the input value.
        client_credential = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
        }

        # Set up the expected value.
        expected_client_id = "test_client_id"
        expected_client_secret = "test_client_secret"

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual_instance = authorization_server_client.ClientCredential(**client_credential)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_instance.client_id == expected_client_id
        assert actual_instance.client_secret == expected_client_secret

    @pytest.mark.parametrize(
        "client_credential",
        [
            {},  # client_id and client_secret is required parameter.
            {
                "client_secret": "test_client_secret",
            },  # client_id is required parameter.
            {
                "client_id": "test_client_id",
            },  # client_secret is required parameter.
            {
                "client_id": 0,
                "client_secret": "test_client_secret",
            },  # client_id must be str.
            {
                "client_id": "test_client_id",
                "client_secret": 0,
            },  # client_secret must be str.
        ],
    )
    def test_invalid_client_credential(self, client_credential):
        """Test valid client credential case."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            _ = authorization_server_client.ClientCredential(**client_credential)


class TestGetSecret:
    """Unit test class for get_agent_access_token"""

    def test_success(
        self,
        caplog: LogCaptureFixture,
        monkeypatch: MonkeyPatch,
        mocker: MockFixture,
    ):
        """Test success case.

        Args:
            caplog (LogCaptureFixture): The pytest fixture for capturing log messages.
            monkeypatch (MonkeyPatch): The pytest fixture for modifying environment variables.
            mocker (MockFixture): The pytest fixture for mocking objects and functions.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set up the expected value.
        expected_access_token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
            "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        )

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT", raising=False)
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT", raising=False)

        # Set up the mock.
        dummy_agent_response = test_util.generate_dummy_http_response(
            status_code=HTTPStatus.OK.value,
            content={
                "access_token": expected_access_token,
                "expires_in": 650,
                "refresh_expires_in": 0,
                "token_type": "Bearer",
                "not-before-policy": 0,
            },
        )
        mocker.patch.object(requests, "post", return_value=dummy_agent_response)

        mocker.patch.object(
            secret_management_client,
            "get_secret",
            return_value={
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            },
        )

        monkeypatch.setenv(
            "HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT",
            "https://authorization-server.example.com/path/to/access_token_endpoint",
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=authorization_server_client.__name__):
            actual_access_token = authorization_server_client.get_agent_access_token()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_access_token == expected_access_token

        assert len(caplog.records) == 3

        # Inspection: Check the Authorization Server Settings Log
        settings_log = caplog.records[0]
        assert settings_log.levelname == "INFO"
        assert settings_log.getMessage() == "Get Authorization Server settings form environment variables."

        assert hasattr(settings_log, "token_endpoint"), "token_endpoint should be present in the log record"
        assert (
            getattr(settings_log, "token_endpoint")
            == "https://authorization-server.example.com/path/to/access_token_endpoint"
        )

        assert hasattr(settings_log, "timeout"), "timeout should be present in the log record"
        assert getattr(settings_log, "timeout") == 3

        # Inspection: Check the Authorization Server Request Log
        request_log = caplog.records[1]
        assert request_log.levelname == "INFO"
        assert request_log.getMessage() == "Request to the Authorization Server."

        assert hasattr(request_log, "url"), "url should be present in the log record"
        assert getattr(request_log, "url") == "https://authorization-server.example.com/path/to/access_token_endpoint"

        assert hasattr(request_log, "timeout"), "timeout should be present in the log record"
        assert getattr(request_log, "timeout") == 3

        # Inspection: Check the Authorization Server Response Log
        response_log = caplog.records[-1]
        assert response_log.levelname == "INFO"
        assert response_log.getMessage() == "Receive the Authorization Server response."

        assert hasattr(response_log, "status_code"), "status_code should be present in the log record"
        assert getattr(response_log, "status_code") == 200

    @pytest.mark.parametrize(
        "secret_client_raise_exception, expected_exception",
        [
            (exc.DependencyServiceHWControlError, exc.DependencyServiceHWControlError),
            (exc.InternalHWControlError, exc.InternalHWControlError),
            (exc.ConfigurationHWControlError, exc.ConfigurationHWControlError),
        ],
    )
    def test_secret_client_raise(
        self, monkeypatch: MonkeyPatch, mocker: MockFixture, secret_client_raise_exception, expected_exception
    ):
        """test secret management client raise case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT", raising=False)
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT", raising=False)

        # Set up the mock.
        mocker.patch.object(secret_management_client, "get_secret", side_effect=secret_client_raise_exception)

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            _ = authorization_server_client.get_agent_access_token()

    def test_invalid_secret_client(self, monkeypatch, mocker: MockFixture):
        """test secret management client return invalid secret client."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT", raising=False)
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT", raising=False)

        # Set up the mock.
        invalid_secret_client = {"invalid_key": "invalid_value"}
        mocker.patch.object(secret_management_client, "get_secret", return_value=invalid_secret_client)

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#

        with pytest.raises(exc.InternalHWControlError):
            _ = authorization_server_client.get_agent_access_token()

    def test_setting_invalid(self, mocker: MockFixture, monkeypatch: MonkeyPatch):
        """test invalid env setting case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set up the expected value.
        expected_exception = exc.ConfigurationHWControlError

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT", raising=False)
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT", raising=False)

        # Setting an invalid value to the setting value obtained from the environment variable
        # will cause a ValidationError to be raised when creating an instance of AuthorizationServerSettings.
        monkeypatch.setenv("HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT", "test_str")

        # Set up the mock.
        mocker.patch.object(
            secret_management_client,
            "get_secret",
            return_value={
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            },
        )

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            _ = authorization_server_client.get_agent_access_token()

    @pytest.mark.parametrize(
        "requests_raise_exception, expected_exception",
        [
            (requests.exceptions.ReadTimeout, exc.InternalHWControlError),
            (requests.exceptions.ConnectTimeout, exc.InternalHWControlError),
            (requests.exceptions.ConnectionError, exc.InternalHWControlError),
            (requests.exceptions.RequestException, exc.InternalHWControlError),
        ],
    )
    def test_requests_raised(
        self, monkeypatch: MonkeyPatch, mocker: MockFixture, requests_raise_exception, expected_exception
    ):
        """test requests raise case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT", raising=False)
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT", raising=False)

        # Set up the mock.
        mocker.patch.object(requests, "post", side_effect=requests_raise_exception)

        mocker.patch.object(
            secret_management_client,
            "get_secret",
            return_value={
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            },
        )

        monkeypatch.setenv(
            "HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT",
            "https://authorization-server.example.com/path/to/access_token_endpoint",
        )

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            _ = authorization_server_client.get_agent_access_token()

    @pytest.mark.parametrize(
        "auth_server_response_headers, auth_server_response_body",
        [
            (
                {"Content-Type": "text/plain"},
                "",
            ),  # json() raise requests.exceptions.JSONDecodeError cause Content-Type != application/json
            ({"Content-Type": "application/json"}, {"test_key": "test_value"}),  # KeyError case
        ],
    )
    def test_auth_server_return_invalid_data(
        self, monkeypatch: MonkeyPatch, mocker: MockFixture, auth_server_response_headers, auth_server_response_body
    ):
        """test Authorization Server return invalid data case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set up the expected value.
        expected_exception = exc.InternalHWControlError

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT", raising=False)
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT", raising=False)

        # Set up the mock.
        dummy_agent_response = test_util.generate_dummy_http_response(
            status_code=HTTPStatus.OK.value, headers=auth_server_response_headers, content=auth_server_response_body
        )
        mocker.patch.object(requests, "post", return_value=dummy_agent_response)

        mocker.patch.object(
            secret_management_client,
            "get_secret",
            return_value={
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            },
        )

        monkeypatch.setenv(
            "HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT",
            "https://authorization-server.example.com/path/to/access_token_endpoint",
        )

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            _ = authorization_server_client.get_agent_access_token()

    @pytest.mark.parametrize(
        "auth_server_response_status_code, auth_server_response_body,expected_exception",
        [
            (HTTPStatus.BAD_REQUEST.value, {"error": "invalid_client"}, exc.AuthenticationHWControlError),
            (HTTPStatus.UNAUTHORIZED.value, {"error": "invalid_client"}, exc.AuthenticationHWControlError),
            (HTTPStatus.BAD_REQUEST.value, {"error": "invalid_request"}, exc.InternalHWControlError),
            (HTTPStatus.BAD_REQUEST.value, {"error": "invalid_grant"}, exc.InternalHWControlError),
            (HTTPStatus.BAD_REQUEST.value, {"error": "unauthorized_client"}, exc.AuthenticationHWControlError),
            (HTTPStatus.BAD_REQUEST.value, {"error": "unsupported_grant_type"}, exc.InternalHWControlError),
            (
                HTTPStatus.NOT_FOUND.value,
                {"test_key": "test_value"},
                exc.DependencyServiceHWControlError,
            ),  # Unexpected HTTP status code was returned case.
        ],
    )
    def test_secret_manager_return_error(  # pylint: disable=R0913, R0917
        self,
        monkeypatch: MonkeyPatch,
        mocker: MockFixture,
        auth_server_response_status_code,
        auth_server_response_body,
        expected_exception,
    ):
        """test Authorization Server return error case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT", raising=False)
        monkeypatch.delenv("HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT", raising=False)

        # Set up the mock.
        dummy_agent_response = test_util.generate_dummy_http_response(
            status_code=auth_server_response_status_code, content=auth_server_response_body
        )
        mocker.patch.object(requests, "post", return_value=dummy_agent_response)

        mocker.patch.object(
            secret_management_client,
            "get_secret",
            return_value={
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
            },
        )

        monkeypatch.setenv(
            "HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT",
            "https://authorization-server.example.com/path/to/access_token_endpoint",
        )

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        # _ = authorization_server_client.get_agent_access_token()

        with pytest.raises(expected_exception):
            _ = authorization_server_client.get_agent_access_token()

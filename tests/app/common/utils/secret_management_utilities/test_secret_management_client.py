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

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.common.utils.secret_management_utilities import secret_management_client

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestGetSecret:
    """Unit test class for get_secret"""

    @pytest.mark.parametrize(
        "input_secret_store, secret_api_response_body",
        [
            (
                secret_management_client.SecretStore.FM,
                {
                    "user_id": "test_user",
                    "password:": "test_password_01",
                },
            ),
            (
                secret_management_client.SecretStore.OOB,
                {
                    "user": "foo_user",
                    "password": "foo_pwd",
                },
            ),
            (
                secret_management_client.SecretStore.AGENT,
                {
                    "client_id": "test_client_id",
                    "client_secret": "test_client_secret",
                },
            ),
        ],
    )
    def test_success(  # pylint: disable=R0913, R0917
        self,
        caplog: LogCaptureFixture,
        monkeypatch: MonkeyPatch,
        mocker: MockFixture,
        input_secret_store,
        secret_api_response_body,
    ):
        """test success case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set up the input value.
        input_secret_name = "dummy_manager_id"

        # Set up the expected value.
        expected_secret = secret_api_response_body

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_SECRET_API_HOST", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PORT", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PATH", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_TIMEOUT", raising=False)

        # Set up the mock.
        dummy_agent_response = test_util.generate_dummy_http_response(
            status_code=HTTPStatus.OK.value, content=secret_api_response_body
        )
        mocker.patch.object(requests, "get", return_value=dummy_agent_response)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=secret_management_client.__name__):
            actual_secret = secret_management_client.get_secret(
                secret_store=input_secret_store, secret_name=input_secret_name
            )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_secret == expected_secret

        assert len(caplog.records) == 3

        # Inspection: Check the Secret Management Settings log
        setting_log = caplog.records[0]
        assert setting_log.levelname == "INFO"
        assert setting_log.getMessage() == "Get secret API settings form environment variables."

        assert hasattr(setting_log, "host"), "host should be present in the log record"
        assert getattr(setting_log, "host") == "localhost"

        assert hasattr(setting_log, "port"), "port should be present in the log record"
        assert getattr(setting_log, "port") == 3500

        assert hasattr(setting_log, "path"), "path should be present in the log record"
        assert getattr(setting_log, "path") == "/v1.0/secrets/"

        assert hasattr(setting_log, "timeout"), "timeout should be present in the log record"
        assert getattr(setting_log, "timeout") == 3

        # Inspection: Check the Secret API Request log
        request_log = caplog.records[1]
        assert request_log.levelname == "INFO"
        assert request_log.getMessage() == "Request to secret API"

        assert hasattr(request_log, "secret_store_name"), "secret_store_name should be present in the log record"
        assert getattr(request_log, "secret_store_name") == input_secret_store.value

        assert hasattr(request_log, "secret_name"), "secret_name should be present in the log record"
        assert getattr(request_log, "secret_name") == input_secret_name

        assert hasattr(request_log, "ip_address"), "ip_address should be present in the log record"
        assert getattr(request_log, "ip_address") == "localhost"

        assert hasattr(request_log, "port"), "port should be present in the log record"
        assert getattr(request_log, "port") == 3500

        assert hasattr(request_log, "url"), "url should be present in the log record"
        assert (
            getattr(request_log, "url")
            == f"http://localhost:3500/v1.0/secrets/{input_secret_store.value}/{input_secret_name}"
        )

        assert hasattr(request_log, "http_method"), "http_method should be present in the log record"
        assert getattr(request_log, "http_method") == "GET"

        assert hasattr(request_log, "time_out"), "time_out should be present in the log record"
        assert getattr(request_log, "time_out") == 3

        # Inspection: Check the Secret API Response log
        response_log = caplog.records[2]
        assert response_log.levelname == "INFO"
        assert response_log.getMessage() == "Get secret from the secret API."

        assert hasattr(response_log, "status_code"), "status_code should be present in the log record"
        assert getattr(response_log, "status_code") == HTTPStatus.OK.value

    @pytest.mark.parametrize(
        "input_secret_store, input_secret",
        [
            (secret_management_client.SecretStore.FM, 0),  # The type of 'secret_name' is invalid case.
            (secret_management_client.SecretStore.OOB, None),  # The type of 'secret_name' is invalid case.
            ("FM", "dummy_fm_manager_id"),  # The type of 'secret_store' is invalid case.
            (0, "dummy_fm_manager_id"),  # The type of 'secret_store' is invalid case.
        ],
    )
    def test_invalid_request_parameter(self, monkeypatch: MonkeyPatch, input_secret_store, input_secret):
        """test invalid request parameter case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set up the expected value.
        expected_exception = ValidationError

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_SECRET_API_HOST", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PORT", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PATH", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_TIMEOUT", raising=False)

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            _ = secret_management_client.get_secret(secret_store=input_secret_store, secret_name=input_secret)

    @pytest.mark.parametrize(
        "input_secret_store",
        [
            secret_management_client.SecretStore.FM,
            secret_management_client.SecretStore.OOB,
            secret_management_client.SecretStore.AGENT,
        ],
    )
    def test_setting_invalid(self, monkeypatch: MonkeyPatch, input_secret_store):
        """test invalid env setting case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set up the input value.
        input_secret_name = "dummy_manager_id"

        # Set up the expected value.
        expected_exception = exc.ConfigurationHWControlError

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_SECRET_API_HOST", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PORT", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PATH", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_TIMEOUT", raising=False)

        # Setting an invalid value to the setting value obtained from the environment variable
        # will cause a ValidationError to be raised when creating an instance of SecretManagementSettings.
        monkeypatch.setenv("HW_CONTROL_SECRET_API_TIMEOUT", "test_str")

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            _ = secret_management_client.get_secret(secret_store=input_secret_store, secret_name=input_secret_name)

    @pytest.mark.parametrize(
        "input_secret_store",
        [
            secret_management_client.SecretStore.FM,
            secret_management_client.SecretStore.OOB,
            secret_management_client.SecretStore.AGENT,
        ],
    )
    @pytest.mark.parametrize(
        "requests_raise_exception, expected_exception",
        [
            (requests.exceptions.ReadTimeout, exc.InternalHWControlError),
            (requests.exceptions.ConnectTimeout, exc.InternalHWControlError),
            (requests.exceptions.ConnectionError, exc.InternalHWControlError),
            (requests.exceptions.RequestException, exc.InternalHWControlError),
        ],
    )
    def test_requests_raised(  # pylint: disable=R0913, R0917
        self,
        monkeypatch: MonkeyPatch,
        mocker: MockFixture,
        input_secret_store,
        requests_raise_exception,
        expected_exception,
    ):
        """test requests raise case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set up the input value.
        input_secret_name = "dummy_manager_id"

        # Set up the mock.
        mocker.patch.object(requests, "get", side_effect=requests_raise_exception)

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_SECRET_API_HOST", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PORT", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PATH", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_TIMEOUT", raising=False)

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            _ = secret_management_client.get_secret(secret_store=input_secret_store, secret_name=input_secret_name)

    @pytest.mark.parametrize(
        "input_secret_store",
        [
            secret_management_client.SecretStore.FM,
            secret_management_client.SecretStore.OOB,
            secret_management_client.SecretStore.AGENT,
        ],
    )
    def test_secret_manager_return_invalid_data(
        self,
        monkeypatch: MonkeyPatch,
        mocker: MockFixture,
        input_secret_store,
    ):
        """test secret manager return invalid data case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set up the expected exception.
        expected_exception = exc.DependencyServiceHWControlError

        # Set up the input value.
        input_secret_name = "dummy_manager_id"

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_SECRET_API_HOST", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PORT", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PATH", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_TIMEOUT", raising=False)

        # Set up the mock.
        dummy_agent_response = test_util.generate_dummy_http_response(
            status_code=HTTPStatus.OK.value, content="invalid body content", headers={"Content-Type": "text/plain"}
        )
        mocker.patch.object(
            requests, "get", return_value=dummy_agent_response
        )  # requests.Response.json raise requests.exceptions.JSONDecodeError cause Content-Type != application/json

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(expected_exception):
            _ = secret_management_client.get_secret(secret_store=input_secret_store, secret_name=input_secret_name)

    @pytest.mark.parametrize(
        "input_secret_store",
        [
            secret_management_client.SecretStore.FM,
            secret_management_client.SecretStore.OOB,
            secret_management_client.SecretStore.AGENT,
        ],
    )
    @pytest.mark.parametrize(
        "secret_api_response_status_code, expected_exception",
        [
            (HTTPStatus.NO_CONTENT.value, exc.DependencyServiceHWControlError),
            (HTTPStatus.BAD_REQUEST.value, exc.DependencyServiceHWControlError),
            (HTTPStatus.FORBIDDEN.value, exc.DependencyServiceHWControlError),
            (HTTPStatus.INTERNAL_SERVER_ERROR.value, exc.DependencyServiceHWControlError),
            (HTTPStatus.NOT_FOUND.value, exc.DependencyServiceHWControlError),
        ],
    )
    def test_secret_manager_return_error(  # pylint: disable=R0913, R0917
        self,
        caplog: LogCaptureFixture,
        monkeypatch: MonkeyPatch,
        mocker: MockFixture,
        input_secret_store,
        secret_api_response_status_code,
        expected_exception,
    ):
        """test secret manager return case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set up the input value.
        input_secret_name = "dummy_manager_id"

        # Clean up the environment variables in the current test environment.
        monkeypatch.delenv("HW_CONTROL_SECRET_API_HOST", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PORT", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_PATH", raising=False)
        monkeypatch.delenv("HW_CONTROL_SECRET_API_TIMEOUT", raising=False)

        # Set up the mock.
        dummy_response_body: dict = {
            "errorCode": "dummy_error_code",
            "message": "dummy_error_message",
        }
        dummy_response = test_util.generate_dummy_http_response(
            status_code=secret_api_response_status_code,
            content=dummy_response_body,
        )
        mocker.patch.object(requests, "get", return_value=dummy_response)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with pytest.raises(expected_exception):
            with caplog.at_level(logging.INFO, logger=secret_management_client.__name__):
                _ = secret_management_client.get_secret(secret_store=input_secret_store, secret_name=input_secret_name)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#

        assert len(caplog.records) == 3

        # Inspection: Check the Secret Management Settings log
        error_response_log = caplog.records[-1]
        assert error_response_log.levelname == "ERROR"
        assert error_response_log.getMessage() == "Return error from the secret API."

        assert hasattr(error_response_log, "status_code"), "status_code should be present in the log record"
        assert getattr(error_response_log, "status_code") == secret_api_response_status_code

        assert hasattr(error_response_log, "response_body"), "response_body should be present in the log record"
        assert getattr(error_response_log, "response_body") == dummy_response_body

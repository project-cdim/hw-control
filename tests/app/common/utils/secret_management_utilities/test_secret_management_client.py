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

import json
import logging
from http import HTTPStatus

import pytest
from pytest_mock import MockFixture

from pydantic import ValidationError
import requests

from tests import test_util

import app.common.basic_exceptions as exc  # type: ignore
from app.common.messages import message  # type: ignore

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.common.utils.secret_management_utilities import secret_management_client  # type: ignore

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestLogMessageModel:
    """Unit test class for Log Message Model Class."""

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "log_message_class, expected_default_value",
        [
            (
                secret_management_client.SecretAPIRequestLog,
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": None,
                    "action": "Request to secret API",
                    "secret_store_name": None,
                    "secret_name": None,
                    "ip_address": None,
                    "port": None,
                    "url": None,
                    "http_method": None,
                    "time_out": None,
                },
            ),
            (
                secret_management_client.SecretAPIResponseLog,
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": None,
                    "action": "Receive secret API response",
                    "status_code": None,
                },
            ),
            (
                secret_management_client.SecretAPIErrorResponseLog,
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": None,
                    "action": "Receive secret API response",
                    "status_code": None,
                    "response_body": None,
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
                secret_management_client.SecretAPIRequestLog,
                {
                    "detail": "test_string",
                    "secret_store_name": secret_management_client.SecretStore.AGENT.value,
                    "secret_name": "test_manager_id",
                    "ip_address": "example.com",
                    "port": 80,
                    "url": "http://example.com:80/v1.0/secrets/{test_secret_store/test_secret_name",
                    "http_method": "POST",
                    "time_out": 5,
                },
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "Request to secret API",
                    "secret_store_name": "cdim-hw-control-agent",
                    "secret_name": "test_manager_id",
                    "ip_address": "example.com",
                    "port": 80,
                    "url": "http://example.com:80/v1.0/secrets/{test_secret_store/test_secret_name",
                    "http_method": "POST",
                    "time_out": 5,
                },
            ),
            (
                secret_management_client.SecretAPIResponseLog,
                {
                    "detail": "test_string",
                    "status_code": 200,
                },
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "Receive secret API response",
                    "status_code": 200,
                },
            ),
            (
                secret_management_client.SecretAPIErrorResponseLog,
                {
                    "detail": "test_string",
                    "status_code": 500,
                    "response_body": {"Foo": "bar"},
                },
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "Receive secret API response",
                    "status_code": 500,
                    "response_body": {"Foo": "bar"},
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


class TestGetSecret:
    """Unit test class for get_secret"""

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
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
    def test_success(
        self,
        caplog,
        monkeypatch,
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
        with caplog.at_level(logging.INFO, logger="LOGGER"):
            actual_secret = secret_management_client.get_secret(
                secret_store=input_secret_store, secret_name=input_secret_name
            )

        # SecretManagementSettingsLog
        setting_log_message = json.loads(caplog.records[0].getMessage())

        # SecretAPIRequestLog
        request_log_message = json.loads(caplog.records[1].getMessage())

        # SecretAPIResponseLog
        response_log_message = json.loads(caplog.records[-1].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_secret == expected_secret
        assert len(caplog.records) == 3

        assert caplog.records[0].levelname == "INFO"
        assert setting_log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert setting_log_message["message"]["detail"] is None
        assert setting_log_message["message"]["action"] == "Get secret API settings form environment variables."
        assert setting_log_message["message"]["host"] == "localhost"
        assert setting_log_message["message"]["port"] == 3500
        assert setting_log_message["message"]["path"] == "/v1.0/secrets/"
        assert setting_log_message["message"]["timeout"] == 3

        assert caplog.records[1].levelname == "INFO"
        assert request_log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert request_log_message["message"]["detail"] is None
        assert request_log_message["message"]["action"] == "Request to secret API"
        assert request_log_message["message"]["secret_store_name"] == input_secret_store.value
        assert request_log_message["message"]["secret_name"] == input_secret_name
        assert request_log_message["message"]["ip_address"] == "localhost"
        assert request_log_message["message"]["port"] == 3500
        assert (
            request_log_message["message"]["url"]
            == f"http://localhost:3500/v1.0/secrets/{input_secret_store.value}/{input_secret_name}"
        )
        assert request_log_message["message"]["http_method"] == "GET"
        assert request_log_message["message"]["time_out"] == 3

        assert caplog.records[-1].levelname == "INFO"
        assert response_log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert response_log_message["message"]["detail"] is None
        assert response_log_message["message"]["action"] == "Receive secret API response"
        assert response_log_message["message"]["status_code"] == 200

    @pytest.mark.parametrize(
        "input_secret_store, input_secret",
        [
            (secret_management_client.SecretStore.FM, 0),  # The type of 'secret_name' is invalid case.
            (secret_management_client.SecretStore.OOB, None),  # The type of 'secret_name' is invalid case.
            ("FM", "dummy_fm_manager_id"),  # The type of 'secret_store' is invalid case.
            (0, "dummy_fm_manager_id"),  # The type of 'secret_store' is invalid case.
        ],
    )
    def test_invalid_request_parameter(self, monkeypatch, input_secret_store, input_secret):
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
    def test_setting_invalid(self, monkeypatch, input_secret_store):
        """test invalid env setting case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set up the input value.
        input_secret_name = "dummy_manager_id"

        # Set up the expected value.
        expected_exception = exc.ConfigurationHwControlError

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
            (requests.exceptions.ReadTimeout, exc.InternalHwControlError),
            (requests.exceptions.ConnectTimeout, exc.InternalHwControlError),
            (requests.exceptions.ConnectionError, exc.InternalHwControlError),
            (requests.exceptions.RequestException, exc.InternalHwControlError),
        ],
    )
    def test_requests_raised(
        self,
        monkeypatch,
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
        monkeypatch,
        mocker: MockFixture,
        input_secret_store,
    ):
        """test secret manager return invalid data case"""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Set up the expected exception.
        expected_exception = exc.DependencyServiceHwControlError

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

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
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
            (HTTPStatus.NO_CONTENT.value, exc.DependencyServiceHwControlError),
            (HTTPStatus.BAD_REQUEST.value, exc.DependencyServiceHwControlError),
            (HTTPStatus.FORBIDDEN.value, exc.DependencyServiceHwControlError),
            (HTTPStatus.INTERNAL_SERVER_ERROR.value, exc.DependencyServiceHwControlError),
            (HTTPStatus.NOT_FOUND.value, exc.DependencyServiceHwControlError),
        ],
    )
    def test_secret_manager_return_error(  # pylint: disable=R0913
        self,
        caplog,
        monkeypatch,
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
            with caplog.at_level(logging.INFO, logger="LOGGER"):
                _ = secret_management_client.get_secret(secret_store=input_secret_store, secret_name=input_secret_name)

        # SecretAPIErrorResponseLog
        error_response_log_message = json.loads(caplog.records[-1].getMessage())

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert caplog.records[-1].levelname == "ERROR"
        assert error_response_log_message["message"]["request_id"] == test_util.CONSTANT_REQUEST_ID
        assert error_response_log_message["message"]["detail"] is None
        assert error_response_log_message["message"]["action"] == "Receive secret API response"
        assert error_response_log_message["message"]["status_code"] == secret_api_response_status_code
        assert error_response_log_message["message"]["response_body"] == dummy_response_body

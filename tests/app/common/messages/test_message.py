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

"""Unit test module for message module ."""

import traceback
from http import HTTPMethod, HTTPStatus
import pytest

from starlette.requests import Request
from starlette.datastructures import Headers
from starlette.datastructures import QueryParams
from fastapi.responses import JSONResponse

from tests import test_util
from tests.test_util import generate_dummy_agent_response

from app.routers.control import control_api  # type: ignore

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++#
from app.common.messages import message  # type: ignore

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestLogMessageModel:
    """Unit test class for LogMessageModel class."""

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "log_message_class, expected_default_value",
        [
            (
                message.BaseLogMessage,
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": None,
                },
            ),
            (
                message.HttpRequestLog,
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": None,
                    "action": "receive http request",
                    "url": None,
                    "http_method": None,
                    "client_ip_address": None,
                    "client_port": None,
                    "path_parameter": None,
                    "query_parameter": None,
                    "body_parameter": None,
                },
            ),
            (
                message.HttpResponseLog,
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": None,
                    "action": "return http response",
                    "status_code": None,
                    "response_body": None,
                },
            ),
            (
                message.AgentRequestLog,
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": None,
                    "action": "request to Agent",
                    "ip_address": None,
                    "port": None,
                    "url": None,
                    "http_method": None,
                    "time_out": None,
                    "request_body": None,
                },
            ),
            (
                message.AgentResponseLog,
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": None,
                    "action": "receive Agent response",
                    "status_code": None,
                    "content_type_header": None,
                    "response_body": None,
                },
            ),
            (
                message.PluginCallLog,
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": None,
                    "action": "plugin call",
                    "manager_type": None,
                    "manager_id": None,
                    "class_name": None,
                    "method_name": None,
                },
            ),
            (
                message.DeviceLockLog,
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": None,
                    "action": "acquire lock",
                    "target_device": None,
                },
            ),
            (
                message.DeviceLockReleasedLog,
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": None,
                    "action": "release lock",
                    "target_device": None,
                },
            ),
            (
                message.DeviceLockFailedLog,
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": None,
                    "action": "failed to acquire lock",
                    "target_device": None,
                },
            ),
            (
                message.ExceptionLog,
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": None,
                    "action": "exception raised",
                    "trace_back": None,
                },
            ),
            (
                message.DeviceLockReleaseFailedLog,
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": None,
                    "action": "failed to release lock",
                    "target_device": None,
                },
            ),
        ],
    )
    def test_default_values(self, log_message_class, expected_default_value):
        """test create instance default values."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        actual_log_message = log_message_class().to_json_encodable()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_log_message == expected_default_value

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "log_message_class, logging_contents, expected_contents",
        [
            (
                message.BaseLogMessage,
                {"detail": "test_string"},
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                },
            ),
            (
                message.HttpRequestLog,
                {  # input logging_contents
                    "detail": "test_string",
                    "url": "http://example.com",
                    "http_method": HTTPMethod.GET,
                    "client_ip_address": "127.0.0.1",
                    "client_port": 49152,
                    "path_parameter": {"CPUDeviceID": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9", "action": "on"},
                    "query_parameter": QueryParams({"q": "test_query", "skip": "5", "limit": "20"}),
                    "body_parameter": {"deviceID": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9", "action": "off"},
                },
                {  # expected_contents
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "receive http request",
                    "url": "http://example.com",
                    "http_method": HTTPMethod.GET,
                    "client_ip_address": "127.0.0.1",
                    "client_port": 49152,
                    "path_parameter": {"CPUDeviceID": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9", "action": "on"},
                    "query_parameter": {"q": "test_query", "skip": "5", "limit": "20"},
                    "body_parameter": {"deviceID": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9", "action": "off"},
                },
            ),
            (
                message.HttpResponseLog,
                {  # input logging_contents
                    "detail": "test_string",
                    "status_code": HTTPStatus.OK.value,
                    "response_body": {"status": True, "IPAddress": "127.0.0.1"},
                },
                {  # expected_contents
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "return http response",
                    "status_code": HTTPStatus.OK.value,
                    "response_body": {"status": True, "IPAddress": "127.0.0.1"},
                },
            ),
            (
                message.AgentRequestLog,
                {  # input logging_contents
                    "detail": "test_string",
                    "ip_address": "127.0.0.1",
                    "port": 49152,
                    "url": "https://example.com",
                    "http_method": HTTPMethod.PATCH,
                    "time_out": 600,
                    "request_body": {"status": True, "IPAddress": "127.0.0.1"},
                },
                {  # expected_contents
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "request to Agent",
                    "ip_address": "127.0.0.1",
                    "port": 49152,
                    "url": "https://example.com",
                    "http_method": HTTPMethod.PATCH,
                    "time_out": 600,
                    "request_body": {"status": True, "IPAddress": "127.0.0.1"},
                },
            ),
            (
                message.AgentResponseLog,
                {  # input logging_contents
                    "detail": "test_string",
                    "status_code": HTTPStatus.NOT_FOUND.value,
                    "content_type_header": "application/json",
                    "response_body": {"status": True, "IPAddress": "127.0.0.1"},
                },
                {  # expected_contents
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "receive Agent response",
                    "status_code": HTTPStatus.NOT_FOUND.value,
                    "content_type_header": "application/json",
                    "response_body": {"status": True, "IPAddress": "127.0.0.1"},
                },
            ),
            (
                message.PluginCallLog,
                {  # input logging_contents
                    "detail": "test_string",
                    "manager_type": "FM",
                    "manager_id": "example_manager_id",
                    "class_name": "example_class_name",
                    "method_name": "example_method_name",
                },
                {  # expected_contents
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "plugin call",
                    "manager_type": "FM",
                    "manager_id": "example_manager_id",
                    "class_name": "example_class_name",
                    "method_name": "example_method_name",
                },
            ),
            (
                message.DeviceLockLog,
                {  # input logging_contents
                    "detail": "test_string",
                    "target_device": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
                },
                {  # expected_contents
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "acquire lock",
                    "target_device": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
                },
            ),
            (
                message.DeviceLockReleasedLog,
                {  # input logging_contents
                    "detail": "test_string",
                    "target_device": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
                },
                {  # expected_contents
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "release lock",
                    "target_device": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
                },
            ),
            (
                message.DeviceLockFailedLog,
                {  # input logging_contents
                    "detail": "test_string",
                    "target_device": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
                },
                {  # expected_contents
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "failed to acquire lock",
                    "target_device": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
                },
            ),
            (
                message.ExceptionLog,
                {  # input logging_contents
                    "detail": "test_string",
                    "trace_back": traceback.format_exc(),
                },
                {  # expected_contents
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "exception raised",
                    "trace_back": traceback.format_exc(),
                },
            ),
            (
                message.DeviceLockReleaseFailedLog,
                {  # input logging_contents
                    "detail": "test_string",
                    "target_device": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
                },
                {  # expected_contents
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "failed to release lock",
                    "target_device": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9",
                },
            ),
        ],
    )
    def test_custom_values(
        self, log_message_class: message.BaseLogMessage, logging_contents: dict, expected_contents: dict
    ):
        """test create instance custom values."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++++++++++#

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        log_message = log_message_class(**logging_contents).to_json_encodable()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++++++++++#
        assert log_message == expected_contents


class TestHttpHttpRequestLog:
    """Unit test class for HttpRequestLog class."""

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "expected_contents",
        [
            {
                "request_id": test_util.CONSTANT_REQUEST_ID,
                "detail": "test_string",
                "action": "receive http request",
                "url": "http://testserver/items/?q=5",
                "http_method": HTTPMethod.POST,
                "client_ip_address": "testclient",
                "client_port": 50000,
                "path_parameter": {"CPUDeviceID": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"},
                "query_parameter": {"q": "5"},
                "body_parameter": {"action": "off"},
            },
        ],
    )
    def test_create_from_json_response(self, expected_contents):
        """test create instance from json response object."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++++++++++#
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/items/",
            "headers": Headers({"content-type": "application/json"}).raw,
            "query_string": "q=5".encode("ascii"),  # query_string should be bytes
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
            "path_params": {"CPUDeviceID": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"},
        }

        request_object = Request(scope)

        body_parameter_object = control_api.PowerControlRequestBody(action="off")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        log_message_model = message.HttpRequestLog.create_from_request(
            detail="test_string", request=request_object, body_parameter=body_parameter_object
        )
        actual_log_message = log_message_model.to_json_encodable()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_log_message == expected_contents

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "expected_contents",
        [
            {
                "request_id": test_util.CONSTANT_REQUEST_ID,
                "detail": "test_string",
                "action": "receive http request",
                "url": "http://testserver/items/?q=5",
                "http_method": HTTPMethod.POST,
                "client_ip_address": None,
                "client_port": None,
                "path_parameter": {"CPUDeviceID": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"},
                "query_parameter": {"q": "5"},
                "body_parameter": {"action": "off"},
            },
        ],
    )
    def test_client_is_none(self, expected_contents):
        """test create instance from json response object."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++++++++++#
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": "/items/",
            "headers": Headers({"content-type": "application/json"}).raw,
            "query_string": "q=5".encode("ascii"),  # query_string should be bytes
            "server": ("testserver", 80),
            "path_params": {"CPUDeviceID": "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"},
        }

        request_object = Request(scope)

        body_parameter_object = control_api.PowerControlRequestBody(action="off")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        log_message_model = message.HttpRequestLog.create_from_request(
            detail="test_string", request=request_object, body_parameter=body_parameter_object
        )
        actual_log_message = log_message_model.to_json_encodable()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++++++++++#
        assert actual_log_message == expected_contents


class TestHttpResponseLog:
    """Unit test class for HttpResponseLog class."""

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "input_status_code, input_body, expected_contents",
        [
            (  # normal JSON response object case
                HTTPStatus.OK.value,
                {"Foo": "Bar"},
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "return http response",
                    "status_code": HTTPStatus.OK.value,
                    "response_body": {"Foo": "Bar"},
                },
            ),
            (  # body is None
                HTTPStatus.NOT_FOUND.value,
                None,
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "return http response",
                    "status_code": HTTPStatus.NOT_FOUND.value,
                    "response_body": None,
                },
            ),
            (  # body is empty json
                HTTPStatus.NOT_FOUND.value,
                {},
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "return http response",
                    "status_code": HTTPStatus.NOT_FOUND.value,
                    "response_body": {},
                },
            ),
            (  # body is empty json
                HTTPStatus.NOT_FOUND.value,
                "Plain Text",
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "return http response",
                    "status_code": HTTPStatus.NOT_FOUND.value,
                    "response_body": "Plain Text",
                },
            ),
        ],
    )
    def test_create_from_json_response(self, input_status_code, input_body, expected_contents):
        """test create instance from json response object."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++++++++++#
        response_object = JSONResponse(status_code=input_status_code, content=input_body)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        log_message_model = message.HttpResponseLog.create_from_json_response(
            response=response_object, detail="test_string"
        )
        log_message = log_message_model.to_json_encodable()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++++++++++#
        assert log_message == expected_contents


class TestAgentResponseLog:
    """Unit test class for AgentResponseLog class."""

    @pytest.mark.usefixtures("set_dummy_constant_request_id")
    @pytest.mark.parametrize(
        "input_status_code, input_body, input_headers, expected_contents",
        [
            (  # normal response object case
                HTTPStatus.OK.value,
                {"Foo": "Bar"},
                {"Content-Type": "application/json", "Content-Length": 348, "Content-Language": "en-US"},
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "receive Agent response",
                    "status_code": HTTPStatus.OK.value,
                    "content_type_header": "application/json",
                    "response_body": {"Foo": "Bar"},
                },
            ),
            (  # header is empty and body is empty
                HTTPStatus.NOT_FOUND.value,
                None,
                None,
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "receive Agent response",
                    "status_code": HTTPStatus.NOT_FOUND.value,
                    "content_type_header": None,
                    "response_body": None,
                },
            ),
            (  # header is empty and body is JSON
                HTTPStatus.NOT_FOUND.value,
                {"Foo": "Bar"},
                None,
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "receive Agent response",
                    "status_code": HTTPStatus.NOT_FOUND.value,
                    "content_type_header": None,
                    "response_body": {"notice": "Unexpected Content-Type"},
                },
            ),
            (  # header is Unexpected and body is plain text
                HTTPStatus.NOT_FOUND.value,
                "test_string",
                {"Content-Type": "text/plain"},
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "receive Agent response",
                    "status_code": HTTPStatus.NOT_FOUND.value,
                    "content_type_header": "text/plain",
                    "response_body": {"notice": "Unexpected Content-Type"},
                },
            ),
            (  # header is "application/json" and body is plain text
                HTTPStatus.NOT_FOUND.value,
                "test_string",
                {"Content-Type": "application/json"},
                {
                    "request_id": test_util.CONSTANT_REQUEST_ID,
                    "detail": "test_string",
                    "action": "receive Agent response",
                    "status_code": HTTPStatus.NOT_FOUND.value,
                    "content_type_header": "application/json",
                    "response_body": {"notice": "Invalid JSON format"},
                },
            ),
        ],
    )
    def test_create_from_response(self, input_status_code, input_body, input_headers, expected_contents):
        """test create instance from requests Response object."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++++++++++#
        response_object = generate_dummy_agent_response(
            status_code=input_status_code,
            headers=input_headers,
            content=input_body,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++++++++++#
        log_message_model = message.AgentResponseLog.create_from_response(
            response=response_object, detail="test_string"
        )
        log_message = log_message_model.to_json_encodable()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++++++++++#
        assert log_message == expected_contents

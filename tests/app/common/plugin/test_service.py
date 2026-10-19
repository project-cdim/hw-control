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

"""Unit test module for app/common/plugin/service.py."""

import json

import pytest
import requests
from pydantic import ValidationError
from pytest_mock import MockerFixture

import app.common.basic_exceptions as exc
from app.common.plugin.models import (
    ElementResponseModel,
    PowerStateModel,
    ProcessorElementModel,
    ProcessorMetricModel,
    TimeStampModel,
)
from app.common.plugin.service import ServicePlugin, ServicePluginConfig
from app.common.settings import settings

_ELEMENT_DICT = {
    "id": "elem-1",
    "deviceType": "CPU",
    "hardwareID": {"CPUIdentity": {"CPUManufacturer": "NEC", "CPUModel": "m1", "CPUSerialNumber": "sn1"}},
    "schema": {"DevicePortList": []},
}


def _make_config(supported_features: list[str] | None = None, timeout: int = 3) -> ServicePluginConfig:
    return ServicePluginConfig(
        base_url="http://localhost:3500/v1.0/invoke/plugin-service/method",
        version="v1",
        supported_features=supported_features if supported_features is not None else ["metric"],
        timeout=timeout,
    )


def _make_plugin(supported_features: list[str] | None = None) -> ServicePlugin:
    plugin = ServicePlugin(_make_config(supported_features))
    plugin.manager_id = "mgr1"
    return plugin


class _MockResponse:
    """Minimal stand-in for the streamed requests.Response used by the tests."""

    def __init__(
        self,
        status_code: int,
        json_data: object = None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
        read_error: Exception | None = None,
    ):
        self.status_code = status_code
        self.headers = headers if headers is not None else {}
        self.content = content if content is not None else json.dumps(json_data).encode()
        self._read_error = read_error
        self.closed = False
        self.read_size = 0

    def iter_content(self, chunk_size: int):
        if self._read_error is not None:
            raise self._read_error
        for start in range(0, len(self.content), chunk_size):
            chunk = self.content[start : start + chunk_size]
            self.read_size += len(chunk)
            yield chunk

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.closed = True


class TestServicePluginConfig:
    """Test the ServicePluginConfig model."""

    def test_valid_config(self):
        """A valid configuration is accepted."""
        config = ServicePluginConfig(
            base_url="http://localhost:3500/v1.0/invoke/plugin-service/method",
            version="v1",
            supported_features=["metric", "power"],
        )
        assert config.version == "v1"
        assert config.timeout == 3

    def test_invalid_supported_features_value_raises(self):
        """An unsupported function name in `supported_features` raises ValidationError."""
        with pytest.raises(ValidationError):
            _make_config(["unknown"])

    def test_empty_supported_features_raises(self):
        """An empty `supported_features` raises ValidationError; at least one is required."""
        with pytest.raises(ValidationError):
            _make_config([])

    def test_invalid_version_raises(self):
        """A version other than 'v1' raises ValidationError."""
        with pytest.raises(ValidationError):
            ServicePluginConfig(
                base_url="http://localhost:3500/v1.0/invoke/plugin-service/method",
                version="v2",
                supported_features=["metric"],
            )

    @pytest.mark.parametrize("timeout", [0, 61])
    def test_timeout_out_of_range_raises(self, timeout: int):
        """A timeout outside 1-60 raises ValidationError."""
        with pytest.raises(ValidationError):
            _make_config(["metric"], timeout=timeout)

    @pytest.mark.parametrize(
        ("base_url", "message"),
        [
            ("https://localhost:3500/method", 'must start with "http://"'),
            ("localhost:3500/method", 'must start with "http://"'),
            ("", 'must start with "http://"'),
            ("http://localhost:3500/me thod", "must not contain control characters or whitespace"),
            ("http://localhost:3500/me\x01thod", "must not contain control characters or whitespace"),
            ("http://localhost:3500/me\x7fthod", "must not contain control characters or whitespace"),
            ("http://localhost:3500/method?a=b", "must not contain a query or a fragment"),
            ("http://localhost:3500/method#frag", "must not contain a query or a fragment"),
            ("http://localhost:3500/../method", 'must not contain a "." or ".." path segment'),
            ("http://localhost:3500/./method", 'must not contain a "." or ".." path segment'),
        ],
    )
    def test_invalid_base_url_raises(self, base_url: str, message: str):
        """A base_url that violates the spec raises ValidationError with the reason."""
        with pytest.raises(ValidationError, match=message):
            ServicePluginConfig(base_url=base_url, version="v1", supported_features=["metric"])

    @pytest.mark.parametrize(
        "base_url",
        [
            "http://localhost:3500",
            "http://localhost:3500/",
            "http://localhost:3500/v1.0/invoke/plugin-service/method",
            "http://192.0.2.1:3500/a..b/c.d",
        ],
    )
    def test_valid_base_url_accepted(self, base_url: str):
        """A base_url that satisfies the spec is kept unchanged."""
        config = ServicePluginConfig(base_url=base_url, version="v1", supported_features=["metric"])
        assert config.base_url == base_url


class TestServicePluginInit:
    """Test ServicePlugin.__init__."""

    def test_none_config_raises(self):
        """A None config raises ConfigurationHWControlError."""
        with pytest.raises(exc.ConfigurationHWControlError):
            ServicePlugin(None)

    def test_builds_base_url_from_config(self):
        """The base URL is built directly from config.base_url and config.version."""
        plugin = ServicePlugin(_make_config(["metric"]))
        assert (
            plugin._baseurl == "http://localhost:3500/v1.0/invoke/plugin-service/method/hw-control-plugin/v1/inventory"
        )
        assert plugin.manager_id == ""

    def test_builds_base_url_strips_trailing_slash(self):
        """A trailing "/" on config.base_url is removed before building the base URL."""
        config = ServicePluginConfig(
            base_url="http://localhost:3500/v1.0/invoke/plugin-service/method/",
            version="v1",
            supported_features=["metric"],
        )
        plugin = ServicePlugin(config)
        assert (
            plugin._baseurl == "http://localhost:3500/v1.0/invoke/plugin-service/method/hw-control-plugin/v1/inventory"
        )

    def test_uses_configured_timeout(self):
        """The instance timeout is taken from config.timeout."""
        plugin = ServicePlugin(_make_config(["metric"], timeout=10))
        assert plugin._timeout == 10


class TestServicePluginGetElements:
    """Test ServicePlugin.get_elements."""

    def test_returns_list_of_response_model(self, mocker: MockerFixture):
        """A successful response is converted to a list of ResponseModel."""
        plugin = _make_plugin()
        mocker.patch(
            "requests.request",
            return_value=_MockResponse(200, [{"kind": "element", "data": _ELEMENT_DICT}]),
        )
        result = plugin.get_elements()
        assert len(result) == 1
        assert isinstance(result[0], ElementResponseModel)

    def test_requests_the_collection_without_trailing_slash(self, mocker: MockerFixture):
        """The request URL is the collection path itself, with no trailing "/"."""
        plugin = _make_plugin()
        mock_request = mocker.patch(
            "requests.request",
            return_value=_MockResponse(200, [{"kind": "element", "data": _ELEMENT_DICT}]),
        )
        plugin.get_elements()
        assert (
            mock_request.call_args.kwargs["url"]
            == "http://localhost:3500/v1.0/invoke/plugin-service/method/hw-control-plugin/v1/inventory"
        )

    def test_empty_list_raises(self, mocker: MockerFixture):
        """An empty list response raises InternalHWControlError."""
        plugin = _make_plugin()
        mocker.patch("requests.request", return_value=_MockResponse(200, []))
        with pytest.raises(exc.InternalHWControlError):
            plugin.get_elements()

    def test_invalid_item_raises(self, mocker: MockerFixture):
        """An item that cannot be converted to ResponseModel raises the same error."""
        plugin = _make_plugin()
        mocker.patch("requests.request", return_value=_MockResponse(200, [{"kind": "unexpected"}]))
        with pytest.raises(exc.InternalHWControlError):
            plugin.get_elements()

    def test_non_list_response_raises(self, mocker: MockerFixture):
        """A response of the wrong shape (dict instead of list) raises InternalHWControlError."""
        plugin = _make_plugin()
        mocker.patch("requests.request", return_value=_MockResponse(200, {"not": "a list"}))
        with pytest.raises(exc.InternalHWControlError):
            plugin.get_elements()


class TestServicePluginGetElement:
    """Test ServicePlugin.get_element."""

    def test_returns_element_model(self, mocker: MockerFixture):
        """A successful response is converted to ElementModel."""
        plugin = _make_plugin()
        mocker.patch("requests.request", return_value=_MockResponse(200, _ELEMENT_DICT))
        result = plugin.get_element("elem-1")
        assert isinstance(result, ProcessorElementModel)
        assert result.id == "elem-1"

    def test_requests_the_element_path(self, mocker: MockerFixture):
        """The element path is the collection path plus "/{element_id}"."""
        plugin = _make_plugin()
        mock_request = mocker.patch("requests.request", return_value=_MockResponse(200, _ELEMENT_DICT))
        plugin.get_element("elem-1")
        assert (
            mock_request.call_args.kwargs["url"]
            == "http://localhost:3500/v1.0/invoke/plugin-service/method/hw-control-plugin/v1/inventory/elem-1"
        )

    def test_invalid_response_raises(self, mocker: MockerFixture):
        """A response that cannot be converted to ElementModel raises InternalHWControlError."""
        plugin = _make_plugin()
        mocker.patch("requests.request", return_value=_MockResponse(200, {"not": "an element"}))
        with pytest.raises(exc.InternalHWControlError):
            plugin.get_element("elem-1")

    def test_path_traversal_element_id_raises_without_sending_request(self, mocker: MockerFixture):
        """An element_id outside the ElementID charset is rejected before it reaches the URL."""
        plugin = _make_plugin()
        mock_request = mocker.patch("requests.request")
        with pytest.raises(ValidationError):
            plugin.get_element("../admin/shutdown")
        mock_request.assert_not_called()


class TestServicePluginGetPowerState:
    """Test ServicePlugin.get_power_state."""

    def test_not_supported_raises(self):
        """RequestNotSupportedHWControlError is raised when 'power' is not supported."""
        plugin = _make_plugin(supported_features=["metric"])
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            plugin.get_power_state("elem-1")

    def test_returns_power_state_model(self, mocker: MockerFixture):
        """A successful response is converted to PowerStateModel."""
        plugin = _make_plugin(supported_features=["power"])
        mocker.patch(
            "requests.request",
            return_value=_MockResponse(200, {"powerState": "On", "time": "2026-01-01T00:00:00Z"}),
        )
        result = plugin.get_power_state("elem-1")
        assert isinstance(result, PowerStateModel)

    def test_path_traversal_element_id_raises_without_sending_request(self, mocker: MockerFixture):
        """An element_id outside the ElementID charset is rejected before it reaches the URL."""
        plugin = _make_plugin(supported_features=["power"])
        mock_request = mocker.patch("requests.request")
        with pytest.raises(ValidationError):
            plugin.get_power_state("../admin/shutdown")
        mock_request.assert_not_called()

    def test_invalid_response_raises(self, mocker: MockerFixture):
        """A response that cannot be converted to PowerStateModel raises InternalHWControlError."""
        plugin = _make_plugin(supported_features=["power"])
        mocker.patch("requests.request", return_value=_MockResponse(200, {"not": "a power state"}))
        with pytest.raises(exc.InternalHWControlError):
            plugin.get_power_state("elem-1")


class TestServicePluginGetMetric:
    """Test ServicePlugin.get_metric."""

    def test_not_supported_raises(self):
        """RequestNotSupportedHWControlError is raised when 'metric' is not supported."""
        plugin = _make_plugin(supported_features=["power"])
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            plugin.get_metric("elem-1")

    def test_returns_metric_model(self, mocker: MockerFixture):
        """A successful response is converted to MetricModel."""
        plugin = _make_plugin(supported_features=["metric"])
        mocker.patch(
            "requests.request", return_value=_MockResponse(200, {"deviceType": "CPU", "time": "2026-01-01T00:00:00Z"})
        )
        result = plugin.get_metric("elem-1")
        assert isinstance(result, ProcessorMetricModel)

    def test_invalid_response_raises(self, mocker: MockerFixture):
        """A response that cannot be converted to MetricModel raises InternalHWControlError."""
        plugin = _make_plugin(supported_features=["metric"])
        mocker.patch("requests.request", return_value=_MockResponse(200, {"not": "a metric"}))
        with pytest.raises(exc.InternalHWControlError):
            plugin.get_metric("elem-1")

    def test_path_traversal_element_id_raises_without_sending_request(self, mocker: MockerFixture):
        """An element_id outside the ElementID charset is rejected before it reaches the URL."""
        plugin = _make_plugin(supported_features=["metric"])
        mock_request = mocker.patch("requests.request")
        with pytest.raises(ValidationError):
            plugin.get_metric("../admin/shutdown")
        mock_request.assert_not_called()


class _ElementActionTestBase:
    """Shared test bodies for the four element-action methods.

    Subclasses set `method_name`, `required_feature` and `expected_action`.
    """

    method_name: str
    required_feature: str
    expected_action: str

    def _call(self, plugin: ServicePlugin, element_id: str):
        return getattr(plugin, self.method_name)(element_id)

    def test_not_supported_raises(self):
        """RequestNotSupportedHWControlError is raised when the required function is unsupported."""
        plugin = _make_plugin(supported_features=["metric"])
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            self._call(plugin, "elem-1")

    def test_returns_time_stamp_model(self, mocker: MockerFixture):
        """A successful response is converted to TimeStampModel, sending the expected action."""
        plugin = _make_plugin(supported_features=[self.required_feature])
        mock_request = mocker.patch(
            "requests.request", return_value=_MockResponse(200, {"time": "2026-01-01T00:00:00Z"})
        )
        result = self._call(plugin, "elem-1")
        assert isinstance(result, TimeStampModel)
        assert mock_request.call_args.kwargs["data"] == f'{{"action": "{self.expected_action}"}}'

    def test_path_traversal_element_id_raises_without_sending_request(self, mocker: MockerFixture):
        """An element_id outside the ElementID charset is rejected before it reaches the URL."""
        plugin = _make_plugin(supported_features=[self.required_feature])
        mock_request = mocker.patch("requests.request")
        with pytest.raises(ValidationError):
            self._call(plugin, "../admin/shutdown")
        mock_request.assert_not_called()


class TestServicePluginPowerOn(_ElementActionTestBase):
    """Test ServicePlugin.power_on."""

    method_name = "power_on"
    required_feature = "power"
    expected_action = "power-on"


class TestServicePluginPowerOff(_ElementActionTestBase):
    """Test ServicePlugin.power_off."""

    method_name = "power_off"
    required_feature = "power"
    expected_action = "power-off"


class TestServicePluginOsShutdown(_ElementActionTestBase):
    """Test ServicePlugin.os_shutdown."""

    method_name = "os_shutdown"
    required_feature = "shutdown"
    expected_action = "os-shutdown"


class TestServicePluginCpuReset(_ElementActionTestBase):
    """Test ServicePlugin.cpu_reset."""

    method_name = "cpu_reset"
    required_feature = "reset"
    expected_action = "cpu-reset"


class _ConnectionActionTestBase:
    """Shared test bodies for add_connection/remove_connection.

    Subclasses set `method_name` and `expected_action`.
    """

    method_name: str
    expected_action: str

    def _call(self, plugin: ServicePlugin, uid: str, did: str):
        return getattr(plugin, self.method_name)(uid, did)

    def test_not_supported_raises(self):
        """RequestNotSupportedHWControlError is raised when 'connection' is not supported."""
        plugin = _make_plugin(supported_features=["metric"])
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            self._call(plugin, "u1", "d1")

    def test_returns_time_stamp_model(self, mocker: MockerFixture):
        """A successful response is converted to TimeStampModel."""
        plugin = _make_plugin(supported_features=["connection"])
        mocker.patch("requests.request", return_value=_MockResponse(200, {"time": "2026-01-01T00:00:00Z"}))
        result = self._call(plugin, "u1", "d1")
        assert isinstance(result, TimeStampModel)

    def test_path_traversal_uid_raises_without_sending_request(self, mocker: MockerFixture):
        """A uid outside the ElementID charset is rejected before it reaches the URL."""
        plugin = _make_plugin(supported_features=["connection"])
        mock_request = mocker.patch("requests.request")
        with pytest.raises(ValidationError):
            self._call(plugin, "../admin/shutdown", "d1")
        mock_request.assert_not_called()

    def test_path_traversal_did_raises_without_sending_request(self, mocker: MockerFixture):
        """A did outside the ElementID charset is rejected before it reaches the URL."""
        plugin = _make_plugin(supported_features=["connection"])
        mock_request = mocker.patch("requests.request")
        with pytest.raises(ValidationError):
            self._call(plugin, "u1", "../admin/shutdown")
        mock_request.assert_not_called()


class TestServicePluginAddConnection(_ConnectionActionTestBase):
    """Test ServicePlugin.add_connection."""

    method_name = "add_connection"
    expected_action = "connect"


class TestServicePluginRemoveConnection(_ConnectionActionTestBase):
    """Test ServicePlugin.remove_connection."""

    method_name = "remove_connection"
    expected_action = "disconnect"


class TestServicePluginRequestErrorHandling:
    """Test ServicePlugin._request's status-code-based error handling."""

    def test_invalid_method_raises_internal_error(self):
        """An invalid HTTP method raises InternalHWControlError."""
        plugin = _make_plugin()
        with pytest.raises(exc.InternalHWControlError):
            plugin._request("not-a-method", "/")

    def test_request_exception_raises_configuration_error(self, mocker: MockerFixture):
        """A transport-level failure raises ConfigurationHWControlError."""
        plugin = _make_plugin()
        mocker.patch("requests.request", side_effect=requests.exceptions.ConnectionError("boom"))
        with pytest.raises(exc.ConfigurationHWControlError):
            plugin._request("get", "/")

    def test_streams_the_response(self, mocker: MockerFixture):
        """The request is streamed and the response is closed after it is read."""
        plugin = _make_plugin()
        response = _MockResponse(200, {"time": "2026-01-01T00:00:00Z"})
        mock_request = mocker.patch("requests.request", return_value=response)
        plugin._request("get", "/")
        assert mock_request.call_args.kwargs["stream"] is True
        assert response.closed is True

    def test_undecodable_response_raises(self, mocker: MockerFixture):
        """A response body that cannot be decoded as JSON raises InternalHWControlError."""
        plugin = _make_plugin()
        mocker.patch("requests.request", return_value=_MockResponse(200, content=b"not json"))
        with pytest.raises(exc.InternalHWControlError) as err:
            plugin._request("get", "/")
        assert "Expecting value" in err.value.message

    def test_undecodable_bytes_response_raises(self, mocker: MockerFixture):
        """A response body that is not valid UTF-8 raises InternalHWControlError."""
        plugin = _make_plugin()
        mocker.patch("requests.request", return_value=_MockResponse(200, content=b'{"a": "\xff"}'))
        with pytest.raises(exc.InternalHWControlError) as err:
            plugin._request("get", "/")
        assert "utf-8" in err.value.message

    def test_oversized_response_raises(self, mocker: MockerFixture):
        """A body larger than the configured maximum size raises InternalHWControlError."""
        plugin = _make_plugin()
        oversize = settings.plugin_max_response_size + 1
        mocker.patch("requests.request", return_value=_MockResponse(200, content=b"x" * oversize))
        with pytest.raises(exc.InternalHWControlError) as err:
            plugin._request("get", "/")
        assert err.value.message.endswith(f"response data size is too large {oversize}")

    def test_body_at_maximum_size_is_accepted(self, mocker: MockerFixture):
        """A body of exactly the maximum size is decoded."""
        plugin = _make_plugin()
        body = b'{"time": "2026-01-01T00:00:00Z"}'
        content = body[:-1] + b" " * (settings.plugin_max_response_size - len(body)) + body[-1:]
        mocker.patch("requests.request", return_value=_MockResponse(200, content=content))
        assert plugin._request("get", "/") == {"time": "2026-01-01T00:00:00Z"}

    def test_oversized_content_length_stops_before_reading_the_body(self, mocker: MockerFixture):
        """A Content-Length over the maximum size raises without reading the body."""
        plugin = _make_plugin()
        declared = settings.plugin_max_response_size + 1
        response = _MockResponse(200, content=b"x" * declared, headers={"Content-Length": str(declared)})
        mocker.patch("requests.request", return_value=response)
        with pytest.raises(exc.InternalHWControlError) as err:
            plugin._request("get", "/")
        assert err.value.message.endswith(f"response data size is too large {declared}")
        assert response.read_size == 0
        assert response.closed is True

    def test_content_length_at_maximum_size_is_accepted(self, mocker: MockerFixture):
        """A Content-Length of exactly the maximum size is not rejected."""
        plugin = _make_plugin()
        headers = {"Content-Length": str(settings.plugin_max_response_size)}
        response = _MockResponse(200, {"time": "2026-01-01T00:00:00Z"}, headers=headers)
        mocker.patch("requests.request", return_value=response)
        assert plugin._request("get", "/") == {"time": "2026-01-01T00:00:00Z"}

    # "\xb2" (superscript two) satisfies str.isdigit() but not int(), so it
    # must be treated as non-numeric rather than crashing.
    @pytest.mark.parametrize("declared", ["not-a-number", "-1", "\xb2"])
    def test_non_numeric_content_length_falls_back_to_the_actual_size(self, mocker: MockerFixture, declared: str):
        """A non-numeric Content-Length is ignored and the body is read as usual."""
        plugin = _make_plugin()
        oversize = settings.plugin_max_response_size + 1
        response = _MockResponse(200, content=b"x" * oversize, headers={"Content-Length": declared})
        mocker.patch("requests.request", return_value=response)
        with pytest.raises(exc.InternalHWControlError) as err:
            plugin._request("get", "/")
        assert err.value.message.endswith(f"response data size is too large {oversize}")
        assert response.read_size > 0

    def test_read_failure_raises_configuration_error(self, mocker: MockerFixture):
        """A transport failure while reading the body raises ConfigurationHWControlError."""
        plugin = _make_plugin()
        response = _MockResponse(200, read_error=requests.exceptions.ChunkedEncodingError("boom"))
        mocker.patch("requests.request", return_value=response)
        with pytest.raises(exc.ConfigurationHWControlError):
            plugin._request("get", "/")
        assert response.closed is True

    def test_undecodable_error_response_raises(self, mocker: MockerFixture):
        """An undecodable body on a non-200 response also raises InternalHWControlError."""
        plugin = _make_plugin()
        mocker.patch("requests.request", return_value=_MockResponse(500, content=b"not json"))
        with pytest.raises(exc.InternalHWControlError):
            plugin._request("get", "/")

    def test_status_405_raises_not_supported(self, mocker: MockerFixture):
        """Status 405 raises RequestNotSupportedHWControlError."""
        plugin = _make_plugin()
        mocker.patch("requests.request", return_value=_MockResponse(405, {"detail": "nope"}))
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            plugin._request("get", "/")

    def test_status_409_raises_conflict(self, mocker: MockerFixture):
        """Status 409 raises RequestConflictHWControlError."""
        plugin = _make_plugin()
        mocker.patch("requests.request", return_value=_MockResponse(409, {"detail": "conflict"}))
        with pytest.raises(exc.RequestConflictHWControlError):
            plugin._request("get", "/")

    def test_status_502_with_error_status_401_raises_authentication_error(self, mocker: MockerFixture):
        """Status 502 with an 'error' dict holding status 401 raises AuthenticationHWControlError."""
        plugin = _make_plugin()
        mocker.patch(
            "requests.request",
            return_value=_MockResponse(502, {"detail": "unauthorized", "error": {"status": 401}}),
        )
        with pytest.raises(exc.AuthenticationHWControlError):
            plugin._request("get", "/")

    @pytest.mark.parametrize(
        "error",
        [
            401,
            {},
            {"status": "401"},
            {"status": 403},
        ],
    )
    def test_status_502_with_unmatched_error_falls_back_to_action(self, mocker: MockerFixture, error: object):
        """Status 502 falls back to the action-based exception unless 'error' holds status 401."""
        plugin = _make_plugin()
        mocker.patch(
            "requests.request",
            return_value=_MockResponse(502, {"detail": "failed", "error": error}),
        )
        with pytest.raises(exc.FMConnectFailureHWControlError):
            plugin._request("post", "/", body={"action": "connect"})

    @pytest.mark.parametrize(
        ("action", "expected_exception"),
        [
            ("connect", exc.FMConnectFailureHWControlError),
            ("disconnect", exc.FMDisconnectFailureHWControlError),
            ("power-on", exc.PowerOnFailureHWControlError),
            ("power-off", exc.PowerOffFailureHWControlError),
            ("cpu-reset", exc.CPUResetFailureHWControlError),
            ("os-shutdown", exc.ControlObjectHWControlError),
            ("something-else", exc.ControlObjectHWControlError),
        ],
    )
    def test_status_502_by_action(self, mocker: MockerFixture, action: str, expected_exception: type):
        """Status 502 raises the exception matching the request body's action."""
        plugin = _make_plugin()
        mocker.patch("requests.request", return_value=_MockResponse(502, {"detail": "failed"}))
        with pytest.raises(expected_exception):
            plugin._request("post", "/", body={"action": action})

    def test_status_502_without_action_raises_control_object_error(self, mocker: MockerFixture):
        """Status 502 with no action in the request body raises ControlObjectHWControlError."""
        plugin = _make_plugin()
        mocker.patch("requests.request", return_value=_MockResponse(502, {"detail": "failed"}))
        with pytest.raises(exc.ControlObjectHWControlError):
            plugin._request("get", "/")

    @pytest.mark.parametrize("status_code", [201, 202, 204])
    def test_success_status_is_only_200(self, mocker: MockerFixture, status_code: int):
        """A 2xx status code other than 200 raises InternalHWControlError."""
        plugin = _make_plugin()
        mocker.patch("requests.request", return_value=_MockResponse(status_code, {"detail": "created"}))
        with pytest.raises(exc.InternalHWControlError):
            plugin._request("get", "/")

    def test_other_status_raises_internal_error(self, mocker: MockerFixture):
        """A status code outside the documented set raises InternalHWControlError."""
        plugin = _make_plugin()
        mocker.patch("requests.request", return_value=_MockResponse(500, {"detail": "boom"}))
        with pytest.raises(exc.InternalHWControlError):
            plugin._request("get", "/")

    def test_error_message_includes_detail_and_additional_message(self, mocker: MockerFixture):
        """The exception message combines 'detail' and 'additional_message'."""
        plugin = _make_plugin()
        mocker.patch(
            "requests.request",
            return_value=_MockResponse(409, {"detail": "conflict detail", "additional_message": "extra info"}),
        )
        with pytest.raises(exc.RequestConflictHWControlError) as exc_info:
            plugin._request("get", "/")
        assert "conflict detail" in exc_info.value.message
        assert "extra info" in exc_info.value.message

    def test_null_additional_message_is_accepted(self, mocker: MockerFixture):
        """A null 'additional_message' is treated as absent, not as a malformed body."""
        plugin = _make_plugin()
        mocker.patch(
            "requests.request",
            return_value=_MockResponse(409, {"detail": "conflict detail", "additional_message": None}),
        )
        with pytest.raises(exc.RequestConflictHWControlError) as exc_info:
            plugin._request("get", "/")
        assert "conflict detail" in exc_info.value.message

    def test_non_dict_error_body_raises_internal_error(self, mocker: MockerFixture):
        """A non-2xx response whose JSON body decodes to a list (not a dict) is rejected."""
        plugin = _make_plugin()
        mocker.patch("requests.request", return_value=_MockResponse(500, [1, 2, 3]))
        with pytest.raises(exc.InternalHWControlError):
            plugin._request("get", "/")

    def test_non_string_detail_raises_internal_error(self, mocker: MockerFixture):
        """A non-2xx response whose 'detail' is not a string is rejected up front."""
        plugin = _make_plugin()
        mocker.patch("requests.request", return_value=_MockResponse(409, {"detail": 12345}))
        with pytest.raises(exc.InternalHWControlError):
            plugin._request("get", "/")

    def test_non_string_additional_message_raises_internal_error(self, mocker: MockerFixture):
        """A non-2xx response whose 'additional_message' is not a string is rejected."""
        plugin = _make_plugin()
        mocker.patch(
            "requests.request",
            return_value=_MockResponse(409, {"detail": "conflict", "additional_message": 12345}),
        )
        with pytest.raises(exc.InternalHWControlError):
            plugin._request("get", "/")

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

"""Plugin execution class, and the type of the plugin configuration file.

File: hw-control/src/app/common/plugin/service.py
"""

import json
import logging
import re
from http import HTTPMethod, HTTPStatus
from typing import Annotated, Any, TypeVar

import requests
from pydantic import AfterValidator, BaseModel, Field, TypeAdapter, ValidationError, validate_call

import app.common.basic_exceptions as exc
from app.common.plugin.models import (
    ElementID,
    ElementModel,
    ExecuteConnectionAction,
    ExecuteElementAction,
    MetricModel,
    PluginFunctionName,
    PluginInterfaceVersion,
    PowerStateModel,
    ResponseModel,
    TimeStampModel,
)
from app.common.settings import settings

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT", bound=BaseModel)

_element_type_adapter: TypeAdapter[ElementModel] = TypeAdapter(ElementModel)
_metric_type_adapter: TypeAdapter[MetricModel] = TypeAdapter(MetricModel)
_response_type_adapter: TypeAdapter[ResponseModel] = TypeAdapter(ResponseModel)

_VALID_HTTP_METHODS = {method.value for method in HTTPMethod}
# Per spec 2.2.1.12, only 200 is a success; any other status code (including
# other 2xx codes) is turned into an exception.
_SUCCESS_STATUS = HTTPStatus.OK.value

# Size of the chunks the response body is read in. It bounds how much of an
# oversized body is read before the read is stopped.
_RESPONSE_CHUNK_SIZE = 8192

# Mapping from the "action" value of the request body to the exception raised
# when the plugin responds with status code 502. Actions not listed here
# (e.g. "os-shutdown") fall back to ControlObjectHWControlError.
_ACTION_TO_BAD_GATEWAY_EXCEPTION: dict[str, type[exc.BaseHWControlError]] = {
    "connect": exc.FMConnectFailureHWControlError,
    "disconnect": exc.FMDisconnectFailureHWControlError,
    "power-on": exc.PowerOnFailureHWControlError,
    "power-off": exc.PowerOffFailureHWControlError,
    "cpu-reset": exc.CPUResetFailureHWControlError,
}

# Characters that must not appear anywhere in base_url: control characters
# (U+0000-U+001F, U+007F-U+009F) and whitespace.
_BASE_URL_FORBIDDEN_CHARS_PATTERN = re.compile(r"[\x00-\x1F\x7F-\x9F\s]")

_BASE_URL_SCHEME = "http://"


def _validate_base_url(value: str) -> str:
    """Reject base URLs that the plugin configuration spec disallows.

    pydantic.AnyHttpUrl is not used here because it accepts values the spec
    forbids (https, query, fragment) and silently normalizes or escapes
    others (relative path segments, whitespace, control characters) instead
    of rejecting them.

    Args:
        value (str): The base_url value read from the configuration file.

    Returns:
        str: `value` unchanged, when it satisfies the spec.

    Raises:
        ValueError: `value` violates the spec.
    """
    if not value.startswith(_BASE_URL_SCHEME):
        raise ValueError(f'must start with "{_BASE_URL_SCHEME}"')
    if _BASE_URL_FORBIDDEN_CHARS_PATTERN.search(value):
        raise ValueError("must not contain control characters or whitespace")
    if "?" in value or "#" in value:
        raise ValueError("must not contain a query or a fragment")
    if any(segment in {".", ".."} for segment in value.removeprefix(_BASE_URL_SCHEME).split("/")):
        raise ValueError('must not contain a "." or ".." path segment')
    return value


# URL of a remote plugin service, as written in the plugin configuration file.
# Per spec, it starts with "http://" and contains no query, fragment, control
# character, whitespace or relative path segment.
PluginBaseUrl = Annotated[str, AfterValidator(_validate_base_url)]


class ServicePluginConfig(BaseModel):
    """Type of the plugin configuration file for a remote plugin.

    Raises:
        pydantic.ValidationError
    """

    base_url: PluginBaseUrl
    version: PluginInterfaceVersion
    supported_features: list[PluginFunctionName] = Field(min_length=1)
    timeout: int = Field(default=3, ge=1, le=60)


class ServicePlugin:
    """Plugin execution class that calls a remote plugin over REST API.

    Attributes:
        manager_id (str): Manager ID. This is set by the get_plugin function
            after the instance is created; it is empty until then.
    """

    def __init__(self, config: ServicePluginConfig | None) -> None:
        """Initialize the endpoint and the supported functions from config.

        Args:
            config (ServicePluginConfig | None): Settings read from the
                plugin configuration file.

        Raises:
            ConfigurationHWControlError: `config` is None.
        """
        if config is None:
            raise exc.ConfigurationHWControlError(additional_message="The Plugin Configuration File is incorrect.")

        base_url = config.base_url.removesuffix("/")
        self._baseurl = f"{base_url}/hw-control-plugin/{config.version}/inventory"
        self._timeout = config.timeout
        self._supported_features = config.supported_features
        self.manager_id: str = ""

    def get_elements(self) -> list[ResponseModel]:
        """Get the information of all elements managed by the plugin.

        Returns:
            list[ResponseModel]: The information of all elements.

        Raises:
            InternalHWControlError: The response could not be converted to
                ResponseModel, or the converted list was empty.
            See `_request`.
        """
        # The plugin API exposes the collection as "/inventory" without a
        # trailing "/", which is a distinct path from "/inventory/{element_id}".
        data = self._request("get", "")
        if not isinstance(data, list):
            raise exc.InternalHWControlError
        try:
            elements = [_response_type_adapter.validate_python(item) for item in data]
        except ValidationError as err:
            raise exc.InternalHWControlError from err
        if not elements:
            raise exc.InternalHWControlError
        return elements

    @validate_call
    def get_element(self, element_id: ElementID) -> ElementModel:
        """Get the information of the specified element.

        Args:
            element_id (ElementID): ID of the element to get.

        Returns:
            ElementModel: The information of the specified element.

        Raises:
            pydantic.ValidationError: `element_id` is not a valid ElementID.
            See `_request`.
        """
        data = self._request("get", f"/{element_id}")
        try:
            return _element_type_adapter.validate_python(data)
        except ValidationError as err:
            raise exc.InternalHWControlError from err

    @validate_call
    def get_power_state(self, element_id: ElementID) -> PowerStateModel:
        """Get the power state of the specified element.

        Args:
            element_id (ElementID): ID of the element to get.

        Returns:
            PowerStateModel: The power state of the specified element.

        Raises:
            pydantic.ValidationError: `element_id` is not a valid ElementID.
            RequestNotSupportedHWControlError: The plugin does not support
                power operations.
            See `_request`.
        """
        self._check_support(PluginFunctionName.POWER)
        data = self._request("get", f"/{element_id}/power")
        return self._to_model(data, PowerStateModel)

    @validate_call
    def get_metric(self, element_id: ElementID) -> MetricModel:
        """Get the metric information of the specified element.

        Args:
            element_id (ElementID): ID of the element to get.

        Returns:
            MetricModel: The metric information of the specified element.

        Raises:
            pydantic.ValidationError: `element_id` is not a valid ElementID.
            RequestNotSupportedHWControlError: The plugin does not support
                metric retrieval.
            See `_request`.
        """
        self._check_support(PluginFunctionName.METRIC)
        data = self._request("get", f"/{element_id}/metric")
        try:
            return _metric_type_adapter.validate_python(data)
        except ValidationError as err:
            raise exc.InternalHWControlError from err

    @validate_call
    def power_on(self, element_id: ElementID) -> TimeStampModel:
        """Execute a power-on operation on the specified element.

        Args:
            element_id (ElementID): ID of the element to operate on.

        Returns:
            TimeStampModel: The date and time the action was executed.

        Raises:
            pydantic.ValidationError: `element_id` is not a valid ElementID.
            RequestNotSupportedHWControlError: The plugin does not support
                power operations.
            See `_request`.
        """
        self._check_support(PluginFunctionName.POWER)
        data = self._request("post", f"/{element_id}", body={"action": ExecuteElementAction.POWER_ON.value})
        return self._to_model(data, TimeStampModel)

    @validate_call
    def power_off(self, element_id: ElementID) -> TimeStampModel:
        """Execute a power-off operation on the specified element.

        Args:
            element_id (ElementID): ID of the element to operate on.

        Returns:
            TimeStampModel: The date and time the action was executed.

        Raises:
            pydantic.ValidationError: `element_id` is not a valid ElementID.
            RequestNotSupportedHWControlError: The plugin does not support
                power operations.
            See `_request`.
        """
        self._check_support(PluginFunctionName.POWER)
        data = self._request("post", f"/{element_id}", body={"action": ExecuteElementAction.POWER_OFF.value})
        return self._to_model(data, TimeStampModel)

    @validate_call
    def os_shutdown(self, element_id: ElementID) -> TimeStampModel:
        """Execute an OS shutdown operation on the specified element.

        Args:
            element_id (ElementID): ID of the element to operate on.

        Returns:
            TimeStampModel: The date and time the action was executed.

        Raises:
            pydantic.ValidationError: `element_id` is not a valid ElementID.
            RequestNotSupportedHWControlError: The plugin does not support
                OS shutdown.
            See `_request`.
        """
        self._check_support(PluginFunctionName.SHUTDOWN)
        data = self._request("post", f"/{element_id}", body={"action": ExecuteElementAction.OS_SHUTDOWN.value})
        return self._to_model(data, TimeStampModel)

    @validate_call
    def cpu_reset(self, element_id: ElementID) -> TimeStampModel:
        """Execute a CPU reset operation on the specified element.

        Args:
            element_id (ElementID): ID of the element to operate on.

        Returns:
            TimeStampModel: The date and time the action was executed.

        Raises:
            pydantic.ValidationError: `element_id` is not a valid ElementID.
            RequestNotSupportedHWControlError: The plugin does not support
                CPU reset.
            See `_request`.
        """
        self._check_support(PluginFunctionName.RESET)
        data = self._request("post", f"/{element_id}", body={"action": ExecuteElementAction.CPU_RESET.value})
        return self._to_model(data, TimeStampModel)

    @validate_call
    def add_connection(self, uid: ElementID, did: ElementID) -> TimeStampModel:
        """Connect the specified USP-side and DSP-side elements.

        Args:
            uid (ElementID): ID of the USP-side element.
            did (ElementID): ID of the DSP-side element.

        Returns:
            TimeStampModel: The date and time the connection succeeded.
                If already connected, the current time.

        Raises:
            pydantic.ValidationError: `uid` or `did` is not a valid ElementID.
            RequestNotSupportedHWControlError: The plugin does not support
                connection operations.
            See `_request`.
        """
        self._check_support(PluginFunctionName.CONNECTION)
        data = self._request(
            "post", f"/{uid}/connection", body={"action": ExecuteConnectionAction.CONNECT.value, "target": did}
        )
        return self._to_model(data, TimeStampModel)

    @validate_call
    def remove_connection(self, uid: ElementID, did: ElementID) -> TimeStampModel:
        """Disconnect the specified USP-side and DSP-side elements.

        Args:
            uid (ElementID): ID of the USP-side element.
            did (ElementID): ID of the DSP-side element.

        Returns:
            TimeStampModel: The date and time the disconnection succeeded.
                If already disconnected, the current time.

        Raises:
            pydantic.ValidationError: `uid` or `did` is not a valid ElementID.
            RequestNotSupportedHWControlError: The plugin does not support
                connection operations.
            See `_request`.
        """
        self._check_support(PluginFunctionName.CONNECTION)
        data = self._request(
            "post", f"/{uid}/connection", body={"action": ExecuteConnectionAction.DISCONNECT.value, "target": did}
        )
        return self._to_model(data, TimeStampModel)

    def _check_support(self, function_name: PluginFunctionName) -> None:
        """Raise RequestNotSupportedHWControlError unless the function is supported."""
        if function_name not in self._supported_features:
            raise exc.RequestNotSupportedHWControlError

    @staticmethod
    def _to_model(data: object, model_type: type[ModelT]) -> ModelT:
        """Convert `data` to `model_type`, raising on failure."""
        try:
            return model_type.model_validate(data)
        except ValidationError as err:
            raise exc.InternalHWControlError from err

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict | None = None,
        body: dict | None = None,
    ) -> Any:
        """Send a request to the remote plugin and return the decoded response.

        Args:
            method (str): HTTP method, e.g. "get", "post".
            endpoint (str): Path of the API endpoint, relative to the base URL.
            params (dict | None): Query parameters.
            body (dict | None): Request body.

        Returns:
            Any: The plugin's JSON response, decoded into a Python data type.

        Raises:
            InternalHWControlError: `method` is not an HTTP method, the
                response body could not be decoded as JSON, or the plugin
                responded with a status code other than 200, 405, 409 or 502.
            ConfigurationHWControlError: Sending the HTTP request, or
                receiving the response body, failed.
            RequestNotSupportedHWControlError: The plugin responded with
                status code 405.
            RequestConflictHWControlError: The plugin responded with status
                code 409.
            AuthenticationHWControlError: The plugin responded with status
                code 502 and an upstream status of 401.
            FMConnectFailureHWControlError: The plugin responded with status
                code 502 while connecting elements.
            FMDisconnectFailureHWControlError: The plugin responded with
                status code 502 while disconnecting elements.
            PowerOnFailureHWControlError: The plugin responded with status
                code 502 while powering on an element.
            PowerOffFailureHWControlError: The plugin responded with status
                code 502 while powering off an element.
            CPUResetFailureHWControlError: The plugin responded with status
                code 502 while resetting a CPU.
            ControlObjectHWControlError: The plugin responded with status
                code 502 for any other action.
        """
        response = self._send_request(method, endpoint, params, body)
        data, failure_detail = self._decode_response(response)

        if response.status_code != _SUCCESS_STATUS:
            self._raise_for_error_status(response.status_code, data, failure_detail, body)

        if failure_detail is not None:
            # Unlike the non-200 path, nothing logs the response here, so the
            # reason has to travel with the exception. It reports the size or
            # the parse position only, never the response body itself.
            raise exc.InternalHWControlError(additional_message=failure_detail)
        return data

    def _send_request(self, method: str, endpoint: str, params: dict | None, body: dict | None) -> requests.Response:
        """Send the HTTP request, translating transport errors to HWControlError.

        The request is streamed, so the returned response holds the status code
        and the headers only. `_decode_response` reads the body.
        """
        method_upper = method.upper()
        if method_upper not in _VALID_HTTP_METHODS:
            raise exc.InternalHWControlError(additional_message=f"'{method}' is not a valid HTTP method.")
        try:
            return requests.request(
                method=method_upper,
                url=self._baseurl + endpoint,
                headers={"Content-Type": "application/json; charset=utf-8"},
                params=params,
                data=json.dumps(body) if body is not None else None,
                timeout=self._timeout,
                stream=True,
            )
        except requests.exceptions.RequestException as err:
            raise exc.ConfigurationHWControlError(
                additional_message="Failed to send the request to the Plugin."
            ) from err

    @staticmethod
    def _decode_response(response: requests.Response) -> tuple[object, str | None]:
        """Decode the response body as JSON, rejecting an oversized body.

        The body is read only up to `settings.plugin_max_response_size`, so an
        oversized body is never held in full.

        The body is required to be UTF-8: it is decoded by json.loads(), not
        by requests, so a 'charset' other than UTF-8 in the Content-Type
        header is not honoured and makes the decoding fail. The plugin API
        is defined as UTF-8 only, so such a response is a protocol
        violation.

        Args:
            response (requests.Response): Streamed response to decode.

        Returns:
            tuple[object, str | None]: The decoded data (or a placeholder dict
                describing the failure), and the reason decoding failed, or
                None when it succeeded. The decoded data may be any JSON
                type, not only a dict, since the remote plugin is not
                trusted to conform to the schema.

        Raises:
            ConfigurationHWControlError: Receiving the response body failed.
        """
        max_size = settings.plugin_max_response_size
        with response:
            declared_size = response.headers.get("Content-Length")
            # isascii() guards int(): str.isdigit() also accepts characters
            # such as "\xb2" (superscript two), which int() rejects.
            if declared_size is not None and declared_size.isascii() and declared_size.isdigit():
                if int(declared_size) > max_size:
                    # The plugin declares an oversized body, so stop before
                    # reading any of it.
                    detail = f"response data size is too large {declared_size}"
                    return {"detail": detail}, detail
            content, content_size = ServicePlugin._read_body(response, max_size)
            if content is None:
                # The size reported here is the number of bytes read before
                # the read was stopped, not the full length of the body.
                detail = f"response data size is too large {content_size}"
                return {"detail": detail}, detail
        try:
            return json.loads(content), None
        except (json.JSONDecodeError, UnicodeDecodeError) as err:
            detail = str(err)
            return {"detail": detail}, detail

    @staticmethod
    def _read_body(response: requests.Response, max_size: int) -> tuple[bytes | None, int]:
        """Read the response body, stopping once it exceeds `max_size`.

        Args:
            response (requests.Response): Streamed response to read from.
            max_size (int): Maximum number of bytes allowed in the body.

        Returns:
            tuple[bytes | None, int]: The body, or None when reading stopped
                because it exceeds `max_size`, and the number of bytes read.
                When reading stopped, the count is the number of bytes read
                up to that point, not the full length of the body, which is
                never determined.
                A Content-Length header is not trusted here: the declared and
                the actual length can differ, and a compressed body is
                decompressed while it is read.

        Raises:
            ConfigurationHWControlError: Reading the body failed.
        """
        chunks: list[bytes] = []
        size = 0
        try:
            for chunk in response.iter_content(chunk_size=_RESPONSE_CHUNK_SIZE):
                size += len(chunk)
                if size > max_size:
                    return None, size
                chunks.append(chunk)
        except requests.exceptions.RequestException as err:
            raise exc.ConfigurationHWControlError(
                additional_message="Failed to receive the response from the Plugin."
            ) from err
        return b"".join(chunks), size

    def _raise_for_error_status(
        self, status_code: int, data: object, failure_detail: str | None, body: dict | None
    ) -> None:
        """Raise the HWControlError matching a non-200 response."""
        logger.warning("Received an error response from the Plugin.", extra={"status_code": status_code, "data": data})
        error_body = self._as_well_formed_error_body(data)
        if failure_detail is not None or error_body is None:
            raise exc.InternalHWControlError

        action = body.get("action", "-") if isinstance(body, dict) else "-"
        detail = error_body["detail"]
        additional_message = error_body["additional_message"]

        error = self._resolve_error_exception(status_code, error_body, action)(additional_message=detail)
        if additional_message:
            error.append_error_message(additional_message)
        raise error

    @staticmethod
    def _as_well_formed_error_body(data: object) -> dict[str, str] | None:
        """Return `data` if 'detail'/'additional_message' are strings, else None.

        A null 'additional_message' is accepted and normalized to an empty
        string, since the spec allows the key to be null.

        The remote plugin is an untrusted external component; without this
        check, a non-dict body or a non-string value in these keys would
        cause an AttributeError or TypeError instead of a well-formed
        HWControlError.
        """
        if not isinstance(data, dict):
            return None
        detail = data.get("detail", "")
        additional_message = data.get("additional_message", "")
        # The spec allows 'additional_message' to be null; treat it as absent.
        if additional_message is None:
            additional_message = ""
        if not isinstance(detail, str) or not isinstance(additional_message, str):
            return None
        return {**data, "detail": detail, "additional_message": additional_message}

    @staticmethod
    def _resolve_error_exception(status_code: int, data: dict, action: str) -> type[exc.BaseHWControlError]:
        """Resolve the exception class matching a non-200 status code."""
        if status_code == HTTPStatus.METHOD_NOT_ALLOWED.value:
            return exc.RequestNotSupportedHWControlError
        if status_code == HTTPStatus.CONFLICT.value:
            return exc.RequestConflictHWControlError
        if status_code == HTTPStatus.BAD_GATEWAY.value:
            error = data.get("error")
            if isinstance(error, dict) and error.get("status") == HTTPStatus.UNAUTHORIZED.value:
                return exc.AuthenticationHWControlError
            return _ACTION_TO_BAD_GATEWAY_EXCEPTION.get(action, exc.ControlObjectHWControlError)
        return exc.InternalHWControlError

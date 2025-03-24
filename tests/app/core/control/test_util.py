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

"""This module define Utilities for app.core.control."""

from enum import Enum
import json
from typing import Dict, Any

from requests.models import Response as requests_Response

from app.common import constants  # type: ignore

# ++++ test data ++++++++++++++++++++++++++++++++++++++++++++++++++++++#

CONSTANT_REQUEST_ID = "test_request_id"


class DummyCpuInfo(Enum):
    """Define a collection of name/plugin_type value pairs."""

    DEVICE_ID = "d62e98bf-6c50-4b88-95f9-49c609d2fdc9"
    DEVICE_TYPE = constants.DeviceType.CPU.value
    FM_PORT_ID = "852f416b-a6e7-4d32-b9c4-238901544d48"
    OOB_DEVICE_ID = "0001"
    FM_MANAGER_ID = "7_77-abc777"
    OOB_MANAGER_ID = "1111111_abc"
    UP_DOWN = constants.SwitchPortType.USP.value
    SWITCH_PORT_TYPE = constants.SwitchPortType.USP.value
    IP_ADDRESS = "11.11.11.11"


class DummyDeviceInfo(Enum):
    """Define a collection of name/plugin_type value pairs."""

    DEVICE_ID = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"
    DEVICE_TYPE = constants.DeviceType.MEMORY.value
    FM_PORT_ID = "eed37ccf-293e-4da4-aeef-f42843192f53"
    OOB_DEVICE_ID = "0002"
    FM_MANAGER_ID = "7_77-abc777"
    OOB_MANAGER_ID = "1111111_abc"
    UP_DOWN = constants.SwitchPortType.DSP.value
    SWITCH_PORT_TYPE = constants.SwitchPortType.DSP.value


# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


# ++++ side effect of mock ++++++++++++++++++++++++++++++++++++++++++++#
class DummyPlugin:
    """
    dummy plugin for UT
    """

    def __init__(self) -> None:
        """The constructor of dummy plugin for UT."""

    def connect(self, uid: str, did: str) -> None:
        """dummy method of connect."""

    def disconnect(self, uid: str, did: str) -> None:
        """dummy method of disconnect."""

    def post_power_on(self, key_values: list) -> None:
        """dummy method of post_power_on."""

    def post_power_off(self, key_values: list) -> None:
        """dummy method of post_power_off."""

    def post_cpu_reset(self, key_values: list) -> None:
        """dummy method of post_power_off."""

    def post_os_shutdown(self, key_values: list) -> None:
        """dummy method of post_os_shutdown."""

    def get_spec_info(self, key_values: list) -> None:
        """dummy method of get_spec_info."""

    def get_power_state(self, key_values: list) -> None:
        """dummy method of get_power_state."""


def generate_dummy_agent_response(
    status_code: int, content: str | dict | None = None, headers: Dict[str, Any] | None = None
):
    """Generates a dummy response object for testing purposes.

    Args:
        status_code (int):
            The HTTP status code for the dummy response.

        content (str | None):
            The response body content. Can be a string or a dictionary which will be converted to JSON.
            Defaults to None.

        headers (Dict[str, Any] | None):
            Optional HTTP headers to include in the response. Defaults to None.

    Returns:
        requests.models.Response: A dummy `Response` object with the specified attributes.
    """

    dummy_response = requests_Response()

    dummy_response.status_code = status_code

    if headers is None:
        headers = {}

    # Setup the content of the response
    if isinstance(content, dict):
        dummy_response._content = json.dumps(content).encode("utf-8")  # pylint: disable=W0212
        headers["Content-Type"] = "application/json"
    elif isinstance(content, str):
        dummy_response._content = content.encode("utf-8")  # pylint: disable=W0212
    else:
        dummy_response._content = b""  # pylint: disable=W0212

    dummy_response.headers.update(headers)
    dummy_response.encoding = "utf-8"

    return dummy_response

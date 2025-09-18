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

"""This is a test program."""

import os
from pathlib import Path
import logging
import requests
import requests.exceptions
import pytest
from app.core.info.metric_agent import InfoMetricAgent
from app.common.basic_exceptions import (
    AgentConnectFailureHWControlError,
    AgentGetInformationFailureHWControlError,
)
import app.core.info.metric_agent
from app.common.utils.authorization_utilities import authorization_server_client

# Device Attribute Information File Name (Generated)
TEST_DEVICE_DATA_FILE = "test_metric_agent_device_attribute1.yaml"

# Agent CPU
AGENT_DATA_CPU = {
    "data": [{"type": "CPU", "usageRate": 123.45, "user": 67.89, "system": 1.23, "wait": 4.56, "idle": 7.89}]
}

# Agent memory
AGENT_DATA_MEMORY = {
    "data": [
        {
            "type": "memory",
            "usedMemory": 123.45,
            "swap": 65.789,
        }
    ]
}

# Agent storage
AGENT_DATA_STORAGE = {
    "data": [
        {"type": "storage", "disk": [{"diskId": "C3AFD15A-65C2-4802-81F6-ABD7019098CF", "amountUsedDisk": 123456}]}
    ]
}

# Agent networkInterface
AGENT_DATA_NIC = {
    "data": [
        {
            "type": "networkInterface",
            "networkPackets": [{"macaddress": "00:50:56:b7:8c:f4", "receivePackets": 123456, "transmitPackets": 7890}],
        }
    ]
}


def _log_contains(record, level, message) -> bool:
    """Comparing log contents"""
    return next(filter(lambda x: (x[1] == level) and (message in x[2]), record), None) is not None


def _set_device_data_file(mocker, monkeypatch, trailing_slash: bool = True):
    """set device data file"""
    # Current path
    current_path = Path(os.path.dirname(os.path.abspath(__file__)))
    # Replace the environment variable setting file directory with the current path.
    config_path = str(current_path)
    if trailing_slash:
        config_path += "/"
    monkeypatch.setenv("HW_CONTROL_CONFIG_FILE_DIR", config_path)
    # Replace the device attribute information file name with the test device attribute information file name.
    mocker.patch.object(app.core.info.metric_agent, "DEVICE_DATA_FILE", TEST_DEVICE_DATA_FILE)


def _get_metric_agent(
    mocker, monkeypatch, status_code, return_value, device_id, device_type, cpu_device_id, trailing_slash: bool = True
):  # pylint: disable=R0913,R0917
    """request get mock"""
    mock_get = mocker.patch("requests.get")
    mock_get.return_value.status_code = status_code
    mock_get.return_value.json.return_value = return_value

    _set_device_data_file(mocker, monkeypatch, trailing_slash)
    mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

    get_metric_info = InfoMetricAgent()
    return get_metric_info.get_metric_agent(device_id, device_type, cpu_device_id)


def test_get_metric_agent_cpu(mocker, caplog, monkeypatch):
    """metric CPU"""
    caplog.set_level(logging.INFO)
    assert AGENT_DATA_CPU == _get_metric_agent(mocker, monkeypatch, 200, AGENT_DATA_CPU, "0001", "CPU", "0001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00005: device_id: 0001,  Agent Call.")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00006: device_id: 0001,  Agent Respond.")


def test_get_metric_agent_cpu_no_slash(mocker, monkeypatch):
    """metric CPU. No trailing slash in configuration path."""
    assert AGENT_DATA_CPU == _get_metric_agent(mocker, monkeypatch, 200, AGENT_DATA_CPU, "0001", "CPU", "0001", False)


def test_get_metric_agent_request_connect_exception(mocker, caplog, monkeypatch):
    """metric request exception"""
    caplog.set_level(logging.INFO)
    mock_get = mocker.patch("requests.get")
    mock_get.side_effect = requests.exceptions.ConnectionError("Error")

    _set_device_data_file(mocker, monkeypatch)
    mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

    get_metric_info = InfoMetricAgent()
    # Raising a ConnectionError with a request will trigger an AgentConnectFailureHWControlError.
    with pytest.raises(AgentConnectFailureHWControlError):
        # Specify the CPU as a representative.
        get_metric_info.get_metric_agent("0001", "CPU", "0001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00005: device_id: 0001,  Agent Call.")
    assert _log_contains(caplog.record_tuples, logging.WARNING, "W00013: Failed to connect Agent:")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00006: device_id: 0001,  Agent Respond.")


def test_get_metric_agent_request_exception(mocker, caplog, monkeypatch):
    """metric request exception"""
    caplog.set_level(logging.INFO)
    mock_get = mocker.patch("requests.get")
    mock_get.side_effect = requests.exceptions.RequestException("Error")

    _set_device_data_file(mocker, monkeypatch)
    mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

    get_metric_info = InfoMetricAgent()
    # By causing a RequestException in the request, an AgentConnectFailureHWControlError will be thrown.
    with pytest.raises(AgentConnectFailureHWControlError):
        # Specify the CPU as a representative.
        get_metric_info.get_metric_agent("0001", "CPU", "0001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00005: device_id: 0001,  Agent Call.")
    assert _log_contains(caplog.record_tuples, logging.WARNING, "W00013: Failed to connect Agent:")


def test_get_metric_agent_request_timeout_exception(mocker, caplog, monkeypatch):
    """metric request exception"""
    caplog.set_level(logging.INFO)
    mock_get = mocker.patch("requests.get")
    mock_get.side_effect = requests.exceptions.Timeout("Error")

    _set_device_data_file(mocker, monkeypatch)
    mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

    get_metric_info = InfoMetricAgent()
    # By causing a Timeout on the Request, an AgentConnectFailureHWControlError will be triggered.
    with pytest.raises(AgentConnectFailureHWControlError):
        # Specify the CPU as a representative.
        get_metric_info.get_metric_agent("0001", "CPU", "0001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00005: device_id: 0001,  Agent Call.")
    assert _log_contains(caplog.record_tuples, logging.WARNING, "W00013: Failed to connect Agent:")


def test_get_metric_agent_request_http_exception(mocker, caplog, monkeypatch):
    """metric request exception"""
    caplog.set_level(logging.INFO)
    custom_resp = requests.Response()
    custom_resp.status_code = 404
    custom_resp._content = b'{"code": "ERROR0001", "message": "Error Message"}'  # pylint: disable=W0212

    http_error = requests.exceptions.HTTPError()
    http_error.response = custom_resp

    mocker.patch("requests.get", side_effect=http_error)

    _set_device_data_file(mocker, monkeypatch)
    mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

    get_metric_info = InfoMetricAgent()
    # By raising an HTTPError in the request, an AgentGetInformationFailureHWControlError is thrown.
    with pytest.raises(AgentGetInformationFailureHWControlError):
        # Specify the CPU as a representative.
        get_metric_info.get_metric_agent("0001", "CPU", "0001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00005: device_id: 0001,  Agent Call.")
    assert _log_contains(caplog.record_tuples, logging.WARNING, "W00014: Failed to get Agent Response:")


def test_get_metric_agent_request_http_exception_non_response(mocker, caplog, monkeypatch):
    """metric request exception"""
    caplog.set_level(logging.INFO)
    http_error = requests.exceptions.HTTPError()
    http_error.response = None

    mocker.patch("requests.get", side_effect=http_error)

    _set_device_data_file(mocker, monkeypatch)
    mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

    get_metric_info = InfoMetricAgent()
    # By raising an HTTPError in the request, an AgentGetInformationFailureHWControlError is thrown.
    with pytest.raises(AgentGetInformationFailureHWControlError):
        # Specify the CPU as a representative.
        get_metric_info.get_metric_agent("0001", "CPU", "0001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00005: device_id: 0001,  Agent Call.")
    assert _log_contains(caplog.record_tuples, logging.WARNING, "W00014: Failed to get Agent Response:")
    assert _log_contains(
        caplog.record_tuples, logging.WARNING, "Agent error code Unknown message No detailed error message available."
    )


def test_get_metric_agent_request_http_exception_response_json_error(mocker, caplog, monkeypatch):
    """metric request exception"""
    caplog.set_level(logging.INFO)
    http_error = requests.exceptions.HTTPError()
    http_error.response = '{"key":'

    mocker.patch("requests.get", side_effect=http_error)

    _set_device_data_file(mocker, monkeypatch)
    mocker.patch.object(authorization_server_client, "get_agent_access_token", return_value="dummy_access_token")

    get_metric_info = InfoMetricAgent()
    # By raising an HTTPError in the request, an AgentGetInformationFailureHWControlError is thrown.
    with pytest.raises(AgentGetInformationFailureHWControlError):
        # Specify the CPU as a representative.
        get_metric_info.get_metric_agent("0001", "CPU", "0001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00005: device_id: 0001,  Agent Call.")
    assert _log_contains(caplog.record_tuples, logging.WARNING, "Failed to parse error Agent response JSON:")
    assert _log_contains(caplog.record_tuples, logging.WARNING, "W00014: Failed to get Agent Response:")
    assert _log_contains(
        caplog.record_tuples, logging.WARNING, "Agent error code Unknown message No detailed error message available."
    )


def test_get_metric_agent_memory(mocker, monkeypatch):
    """metric memory"""
    assert AGENT_DATA_MEMORY == _get_metric_agent(mocker, monkeypatch, 200, AGENT_DATA_MEMORY, "1001", "memory", "0001")


def test_get_metric_agent_storage(mocker, monkeypatch):
    """metric storage"""
    assert AGENT_DATA_STORAGE == _get_metric_agent(
        mocker, monkeypatch, 200, AGENT_DATA_STORAGE, "2001", "storage", "0001"
    )


def test_get_metric_agent_nic(mocker, monkeypatch):
    """metric networkInterface"""
    assert AGENT_DATA_NIC == _get_metric_agent(
        mocker, monkeypatch, 200, AGENT_DATA_NIC, "3001", "networkInterface", "0001"
    )

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

"""HW independent section - Get Agent(OS) Information

Get metric information for the specified Device ID.

"""
import logging
import fcntl
from typing import Any
import copy
from pathlib import Path
import requests
import requests.exceptions
import yaml
from app.common.messages import message
from app.common.basic_exceptions import (
    AgentConnectFailureHWControlError,
    AgentGetInformationFailureHWControlError,
)
import app.common.constants as const
from app.common.utils.file_location_settings import FileLocationSettings
from app.common.utils.authorization_utilities import authorization_server_client

logger = logging.getLogger(__name__)

# Device attribute information file name (stub data)
DEVICE_DATA_FILE = "device_attribute.yaml"

# Device attribute setting file name (stub data)
DEVICE_DATA_SETTING_FILE = "device_attribute_setting.yaml"

# Device list information item name
DEVICE_LIST_ITEM_NAME_DEVICE_ID = "deviceID"  # Device ID
DEVICE_LIST_ITEM_NAME_DEVICE_TYPE = "type"  # Device Type


class InfoMetricAgent:
    """Get metric information

    Get metric information from agent.
    """

    def get_metric_agent(self, device_id: str, device_type: str, cpu_device_id: str) -> dict:
        """Get metric information

        Get metric information for the specified Device ID and Device Type

        Args:
            device_id (str): Device ID
            device_type (str): Device Type
            cpu_device_id (str): CPU Device ID

        Returns:
            dict: metric info

        Examples:
            >>> get_info = GetMetricInfoAgent()
                metric_info = get_info.get_metric_agent("0001", "CPU")
        """
        resp = None
        url = None
        param = {}

        settings = FileLocationSettings()
        # Read device attribute information file. (stub data)
        file_path = Path(settings.data_file_dir) / DEVICE_DATA_FILE
        with open(file_path, encoding="utf-8") as device_file:
            devices = yaml.safe_load(device_file)
            url = devices[cpu_device_id]["agent"]["url"] + const.BASE_URL + "/v1/agent/info?deviceType=" + device_type
            timeout_seconds = devices[device_id]["agent"]["timeout"]
            param = devices[device_id].get("specific_data", None)

        # Get data from Agent.
        resp = self._get_agent_data(url, timeout_seconds, param, device_id)

        return resp

    def _get_agent_data(self, url: str, timeout_seconds: int, param: dict, device_id: str) -> dict | Any:
        """Get agent data

        Request to agent and get metric information.

        Args:
            url (str): agent url
            timeout_seconds (int): agent request timeout time (seconds)
            param (dict): request parameter
            device_id (str): Device ID

        Returns:
            dict | Any: metric info
        """
        log_param = f"device_id: {device_id}, "

        access_token = authorization_server_client.get_agent_access_token()
        requests_header = {"Authorization": f"Bearer {access_token}"}

        try:
            logger.info(message.get_log_message(message.I00005, [log_param]))
            req = requests.get(
                url,
                params=param,
                timeout=timeout_seconds,
                headers=requests_header,
            )
            req.raise_for_status()
            return req.json()

        except requests.exceptions.HTTPError as http_err:
            error_code = "Unknown"
            error_message = "No detailed error message available."
            if http_err.response is not None:
                try:
                    error_data = http_err.response.json()
                    error_code = error_data.get("code", error_code)
                    error_message = error_data.get("message", error_message)
                except (ValueError, TypeError, AttributeError) as ex:
                    logger.warning("Failed to parse error Agent response JSON: %s", ex)
            logger.warning(
                message.get_log_message(
                    message.W00014,
                    [
                        f"Failed to get information on Agent: \
                                device_id {device_id} url {url} \
                                Agent error code {error_code} message {error_message}"
                    ],
                )
            )
            raise AgentGetInformationFailureHWControlError from http_err

        except requests.exceptions.RequestException as requests_err:
            logger.warning(
                message.get_log_message(message.W00013, [f"Request to Agent failed: device_id {device_id} url {url}"])
            )
            raise AgentConnectFailureHWControlError from requests_err

        finally:
            logger.info(message.get_log_message(message.I00006, [log_param]))

    def create_device_attribute(self, device_list: list) -> None:
        """Create device attribute file

        Create device attribute file based on setting file

        Args:
            device_list (list): Device ID list

        Examples:
            >>> get_info = GetMetricInfoAgent()
                get_info.create_device_attribute(device_list)
        """
        settings = FileLocationSettings()
        # Read device attribute setting file.
        setting_file_path = Path(settings.config_file_dir) / DEVICE_DATA_SETTING_FILE
        with open(setting_file_path, encoding="utf-8") as setting_file:
            setting_data = yaml.safe_load(setting_file)

        # Generate device attribute information for the number of Device IDs in the device list.
        attribute_data: dict = {}
        for device_item in device_list:
            device_id = device_item.get(DEVICE_LIST_ITEM_NAME_DEVICE_ID)
            # If the Device ID has already been set in the device attribute information, set that information.
            if device_id in setting_data:
                attribute_data[device_id] = copy.deepcopy(setting_data.get(device_id))
            else:
                # If the Device ID does not exist in the device attribute information, set the default value.
                attribute_data[device_id] = copy.deepcopy(setting_data["DEFAULT"])
                # Delete unnecessary data according to Device Type.
                device_type = device_item.get(DEVICE_LIST_ITEM_NAME_DEVICE_TYPE)
                if device_type == const.DeviceType.STORAGE.value:
                    attribute_data[device_id]["specific_data"].pop("macAddress", None)
                elif device_type == const.DeviceType.NIC.value:
                    attribute_data[device_id]["specific_data"].pop("diskID", None)
                else:
                    attribute_data[device_id].pop("specific_data", None)

        # Only if there is data to write.
        if attribute_data:
            # Read device attribute information file.
            data_file_path = Path(settings.data_file_dir) / DEVICE_DATA_FILE
            old_data: dict = {}
            if data_file_path.exists():
                with open(data_file_path, encoding="utf-8") as data_file:
                    old_data = yaml.safe_load(data_file) or {}

            # Output file only if data has changed.
            if old_data != attribute_data:
                # Write device attribute information file.
                with open(data_file_path, "w", encoding="utf-8") as write_data_file:
                    # Exclusive lock.
                    fcntl.flock(write_data_file, fcntl.LOCK_EX)
                    # Output file.
                    yaml.dump(
                        attribute_data,
                        write_data_file,
                        default_flow_style=False,
                        explicit_start=True,
                        explicit_end=True,
                    )
                    # Release exclusive lock.
                    fcntl.flock(write_data_file, fcntl.LOCK_UN)

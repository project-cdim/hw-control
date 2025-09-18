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

"""os ipaddress
file_path: /app/common/utils/os_ipaddress.py

Obtain the IP address of the operating system running on the CPU.

"""

import logging
import os
import yaml

import app.common.basic_exceptions as exc
from app.common.dim import device_id_base
from app.common.utils.file_location_settings import FileLocationSettings

BASE_PATH = os.path.dirname(__file__)

logger = logging.getLogger(__name__)


def get_os_ipaddress(cpu_device_id: str) -> tuple[str | None, bool]:
    """get_os_ipaddress

    Get the IP address of the OS corresponding to the CPU.

    Args:
        cpu_device_id (str): Device ID of the CPU.

    Returns:
        str | None : OS IP address if found. None if not found.
        bool : True if the IP Address is found, otherwise False.

    Raises:
        None.

    """
    ip_address: str | None = None  # If the Agent on CPU cannot be found, return None
    is_agent_exist: bool = False
    try:
        fm_port_id = device_id_base.device_id_to_fm_port_id(cpu_device_id)
        config_file_dir = FileLocationSettings().config_file_dir
        logger.debug("[get_os_ipaddress] config_file_dir=%s", config_file_dir)

        with open(os.path.join(config_file_dir, "os_ipaddress.yaml"), encoding="utf-8") as file:
            ipaddr_data = yaml.safe_load(file)

        for item in ipaddr_data["OS_IPAddress"]:
            if item["fmPortID"] == fm_port_id:
                ip_address = item["IPAddress"]
                is_agent_exist = True
                break

    except (FileNotFoundError, yaml.YAMLError, AttributeError, KeyError, exc.BaseHWControlError):
        logger.debug("[get_os_ipaddress] cpu_device_id=%s", cpu_device_id, exc_info=True)

    return ip_address, is_agent_exist

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

"""test module"""
from typing import Any

CPU_RESPONSE = {
    "device": [{"deviceID": "0001", "type": "CPU", "ret": "200", "powerState": "ON", "powerCapability": "true"}]
}
MEMORY_RESPONSE = {
    "device": [{"deviceID": "1001", "type": "memory", "ret": "200", "powerState": "ON", "powerCapability": "true"}]
}
STORAGE_RESPONSE = {
    "device": [{"deviceID": "2001", "type": "storage", "ret": "200", "powerState": "ON", "powerCapability": "true"}]
}
NIC_RESPONSE = {
    "device": [
        {"deviceID": "3001", "type": "networkInterface", "ret": "200", "powerState": "ON", "powerCapability": "false"}
    ]
}


class OOBRedfishPlugin:
    """test class"""

    def get_spec_info(self, key_values: list[dict]) -> dict[str, Any]:
        """test function"""
        for param in key_values:
            for key, value in param.items():
                print(f"{key} = {value}")

            device_type = param["device_type"]
            if device_type.startswith("CPU"):
                return CPU_RESPONSE
            if device_type.startswith("memory"):
                return MEMORY_RESPONSE
            if device_type.startswith("storage"):
                return STORAGE_RESPONSE
            if device_type.startswith("networkInterface"):
                return NIC_RESPONSE

        return {}

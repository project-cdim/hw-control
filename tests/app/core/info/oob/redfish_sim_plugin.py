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

""" test module """
from typing import Any

CPU_RESPONSE = {'device': [
    {
        'deviceID': '0001',
        'type': 'CPU',
        'ret': '200',
        'powerState': 'ON',
        'powerCapability': 'true'
    }
]}
MEMORY_RESPONSE = {'device': [
    {
        'deviceID': '1001',
        'type': 'memory',
        'ret': '200',
        'powerState': 'ON',
        'powerCapability': 'true'
    }
]}
STORAGE_RESPONSE = {'device': [
    {
        'deviceID': '2001',
        'type': 'storage',
        'ret': '200',
        'powerState': 'ON',
        'powerCapability': 'true'
    }
]}
NIC_RESPONSE = {'device': [
    {
        'deviceID': '3001',
        'type': 'networkInterface',
        'ret': '200',
        'powerState': 'ON',
        'powerCapability': 'false'
    }
]}


class OobRedfishPlugin:
    """ test class """
    def get_spec_info(self, key_values: list) -> dict[str, Any]:
        """ test function """
        for key, value in key_values.items():
            print(f"{key} = {value}")

        device_type = key_values['device_type']
        rest_key_value: dict = {}
        if device_type.startswith("CPU"):
            rest_key_value = CPU_RESPONSE
        elif device_type.startswith("memory"):
            rest_key_value = MEMORY_RESPONSE
        elif device_type.startswith("storage"):
            rest_key_value = STORAGE_RESPONSE
        elif device_type.startswith("networkInterface"):
            rest_key_value = NIC_RESPONSE
        return rest_key_value

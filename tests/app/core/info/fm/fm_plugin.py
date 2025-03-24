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

"""FMPlugin Stub
"""

CPU_DATA = {
    "id": "0001",
    "switchSerialNumber": "001",
    "switchPortNumber": 1,
    "upDown": "up",
    "link": [],
    "deviceType": "PCIe",
    "PCIeVendorId": None,
    "PCIeDeviceId": None,
    "PCIeDeviceSerialNumber": None,
    "serialNumber": "0001"
}

STORAGE_DATA = {
    "id": "1001",
    "switchSerialNumber": "001",
    "switchPortNumber": 2,
    "upDown": "down",
    "link": [],
    "deviceType": "PCIe",
    "PCIeVendorId": "xxxx",
    "PCIeDeviceId": "1001",
    "PCIeDeviceSerialNumber": "x1001",
    "serialNumber": None
}

NIC_DATA = {
    "id": "2001",
    "switchSerialNumber": "001",
    "switchPortNumber": 3,
    "upDown": "down",
    "link": [],
    "deviceType": "PCIe",
    "PCIeVendorId": "xxxx",
    "PCIeDeviceId": "2001",
    "PCIeDeviceSerialNumber": "x2001",
    "serialNumber": None
}


class FmPlugin:
    """FMPlugin
    """
    def __init__(self, obj):
        self.info = obj

    def show(self, target=None):
        """port acquisition
        """
        ret = None

        if not target:
            ret = (0, [CPU_DATA, STORAGE_DATA, NIC_DATA])

        elif target == "0001":
            ret = (0, CPU_DATA)

        elif target == "1001":
            ret = (0, STORAGE_DATA)

        elif target == "2001":
            ret = (0, NIC_DATA)

        return ret

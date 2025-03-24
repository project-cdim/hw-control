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

"""
Unit tests of oob_plugin_base module.
"""

import pytest
from pydantic import ValidationError

from app.common.utils.oob_plugin_base import OOBDeviceListItem


def test_oob_device_list_item_all_attributes_set():
    """Check OOBDeviceListItem: normal case."""
    item_dict = {
        "PCIeVendorId": "PCI_E_VENDOR_ID",
        "PCIeDeviceId": "PCI_E_DEVICE_ID",
        "PCIeDeviceSerialNumber": "PCI_E_DEVICE_SERIAL_NUMBER",
        "CPUSerialNumber": "CPU_SERIAL_NUMBER",
        "CPUManufacturer": "CPU_MANUFACTURER",
        "CPUModel": "CPU_MODEL",
        "portKeys": {"portKey1": "PORT_KEY_1"},
        "deviceKeys": {"deviceKey1": "DEVICE_KEY_1"},
        "deviceType": "DEVICE_TYPE",
        "oobDeviceID": "OOB_DEVICE_ID",
    }
    item = OOBDeviceListItem(**item_dict)

    assert item.model_dump(by_alias=True) == item_dict


def test_oob_device_list_item_required_attributes_set():
    """Check OOBDeviceListItem: normal case."""
    item_dict = {
        "PCIeVendorId": None,
        "PCIeDeviceId": None,
        "PCIeDeviceSerialNumber": None,
        "CPUSerialNumber": None,
        "CPUManufacturer": None,
        "CPUModel": None,
        "portKeys": None,
        "deviceKeys": None,
        "deviceType": "DEVICE_TYPE",
        "oobDeviceID": "OOB_DEVICE_ID",
    }
    item = OOBDeviceListItem(**item_dict)

    assert item.model_dump(by_alias=True) == item_dict


def test_oob_device_list_item_required_attribute_device_type_not_set():
    """Check OOBDeviceListItem: normal case."""
    item_dict = {
        "PCIeVendorId": "PCI_E_VENDOR_ID",
        "PCIeDeviceId": "PCI_E_DEVICE_ID",
        "PCIeDeviceSerialNumber": "PCI_E_DEVICE_SERIAL_NUMBER",
        "CPUSerialNumber": "CPU_SERIAL_NUMBER",
        "CPUManufacturer": "CPU_MANUFACTURER",
        "CPUModel": "CPU_MODEL",
        "portKeys": {"portKey1": "PORT_KEY_1"},
        "deviceKeys": {"deviceKey1": "DEVICE_KEY_1"},
        "deviceType": None,
        "oobDeviceID": "OOB_DEVICE_ID",
    }
    with pytest.raises(ValidationError):
        OOBDeviceListItem(**item_dict)


def test_oob_device_list_item_required_attribute_oob_device_id_not_set():
    """Check OOBDeviceListItem: normal case."""
    item_dict = {
        "PCIeVendorId": "PCI_E_VENDOR_ID",
        "PCIeDeviceId": "PCI_E_DEVICE_ID",
        "PCIeDeviceSerialNumber": "PCI_E_DEVICE_SERIAL_NUMBER",
        "CPUSerialNumber": "CPU_SERIAL_NUMBER",
        "CPUManufacturer": "CPU_MANUFACTURER",
        "CPUModel": "CPU_MODEL",
        "portKeys": {"portKey1": "PORT_KEY_1"},
        "deviceKeys": {"deviceKey1": "DEVICE_KEY_1"},
        "deviceType": "DEVICE_TYPE",
        "oobDeviceID": None,
    }
    with pytest.raises(ValidationError):
        OOBDeviceListItem(**item_dict)

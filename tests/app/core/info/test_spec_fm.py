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


"""This is a test program."""

import logging

import pytest

import app.common.basic_exceptions as exc
import app.common.constants as const
from app.common.dim import device_id_base as dim
from app.common.utils.fm_plugin_base import FMPortData
from app.core.info.spec_fm import GetSpecFMInfo

PLUGIN_RETURN_CPU_1_1 = [
    FMPortData(
        id="2a79d931-9c8b-4674-94ad-f6d9b00ba50c",
        switchId="1f2cb78b-088e-4b33-b077-d784942feb2a",
        switchPortNumber="1",
        switchPortType="USP",
        fabricId="NEC-fmmodel-fmsw-01",
        link=["4f4de979-ad99-498b-ade5-1cb404e462fa", "46376548-47e8-40f8-99de-a6f31d10f626"],
        deviceType="PCIe",
        PCIClassCode=None,
        PCIeVendorId=None,
        PCIeDeviceId=None,
        PCIeDeviceSerialNumber=None,
        CPUManufacturer="corp.A",
        CPUModel="Xo1",
        CPUSerialNumber="0001",
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
PLUGIN_RETURN_CPU_1_2 = [
    FMPortData(
        id="eee64be1-d07e-4e78-b82a-3f05ec8d10e8",
        switchId="bbce65be-7054-4fea-a0e2-8f9a0b0fb6a1",
        switchPortNumber="1",
        switchPortType="USP",
        fabricId="NEC-fmmodel-fmsw-02",
        link=["ba123bd1-04bd-40a5-9773-6a647a3f5c01", "af312740-e804-4d11-a9a7-3f5496a80a2f"],
        deviceType="PCIe",
        PCIClassCode=None,
        PCIeVendorId=None,
        PCIeDeviceId=None,
        PCIeDeviceSerialNumber=None,
        CPUManufacturer="corp.A",
        CPUModel="Xo1",
        CPUSerialNumber="0001",
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
PLUGIN_RETURN_CPU_2_1 = [
    FMPortData(
        id="7f132823-f6f5-40bb-abc0-12c878cb180e",
        switchId="1f2cb78b-088e-4b33-b077-d784942feb2a",
        switchPortNumber="2",
        switchPortType="USP",
        fabricId="NEC-fmmodel-fmsw-01",
        link=["dc29e83e-26ad-45ae-93dd-0ee9f69245a3", "3d109460-c789-461a-bf52-30cae9c86d1d"],
        deviceType="PCIe",
        PCIClassCode=None,
        PCIeVendorId=None,
        PCIeDeviceId=None,
        PCIeDeviceSerialNumber=None,
        CPUManufacturer="corp.A",
        CPUModel="Xo1",
        CPUSerialNumber="0002",
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
PLUGIN_RETURN_CPU_2_2 = [
    FMPortData(
        id="6e4f020f-ebcF-4432-9820-e2c364df391b",
        switchId="bbce65be-7054-4fea-a0e2-8f9a0b0fb6a1",
        switchPortNumber="2",
        switchPortType="USP",
        fabricId="NEC-fmmodel-fmsw-02",
        link=["971b59b0-b4fa-4f32-b54b-9fded3034e0b", "30c15d32-44fd-4c80-993c-8ee51b68e0c7"],
        deviceType="PCIe",
        PCIClassCode=None,
        PCIeVendorId=None,
        PCIeDeviceId=None,
        PCIeDeviceSerialNumber=None,
        CPUManufacturer="corp.A",
        CPUModel="Xo1",
        CPUSerialNumber="0002",
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
CPU_EXPECTED_1_1: dict[str, object] = {
    "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c",
    "type": "CPU",
    "devicePortList": [
        {
            "deviceSwitchInfo": "7e31d0fb-42c5-4cd5-84c7-b37f5fa8e82c",
            "fabricId": "NEC-fmmodel-fmsw-01",
            "fmPortId": "2a79d931-9c8b-4674-94ad-f6d9b00ba50c",
            "LTSSMState": "L0",
            "switchId": "1f2cb78b-088e-4b33-b077-d784942feb2a",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        }
    ],
    "link": [
        {"type": "storage", "deviceID": "ee9e4718-df31-4bd8-b37b-455e0e0672f6"},
        {"type": "networkInterface", "deviceID": "00029c15-bccb-4f9a-a251-51c9d307a097"},
    ],
    "fmDeviceType": "PCIe",
    "PCIClassCode": None,
    "PCIeVendorId": None,
    "PCIeDeviceId": None,
    "PCIeDeviceSerialNumber": None,
    "CPUManufacturer": "corp.A",
    "CPUModel": "Xo1",
    "CPUSerialNumber": "0001",
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}
CPU_EXPECTED_1_2: dict[str, object] = {
    "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c",
    "type": "CPU",
    "devicePortList": [
        {
            "deviceSwitchInfo": "11a1f26b-acd9-4c69-b1d7-ac92b0b49aed",
            "fabricId": "NEC-fmmodel-fmsw-02",
            "fmPortId": "eee64be1-d07e-4e78-b82a-3f05ec8d10e8",
            "LTSSMState": "L0",
            "switchId": "bbce65be-7054-4fea-a0e2-8f9a0b0fb6a1",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        }
    ],
    "link": [
        {"type": "memory", "deviceID": "1c440d70-ae46-42f6-b03b-6df28d0913af"},
        {"type": "GPU", "deviceID": "e15a736e-ea75-4f5f-8c8d-970e0705bb20"},
    ],
    "fmDeviceType": "PCIe",
    "PCIClassCode": None,
    "PCIeVendorId": None,
    "PCIeDeviceId": None,
    "PCIeDeviceSerialNumber": None,
    "CPUManufacturer": "corp.A",
    "CPUModel": "Xo1",
    "CPUSerialNumber": "0001",
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}
CPU_EXPECTED_2_1: dict[str, object] = {
    "deviceID": "de99f86c-f32e-4bb1-a3eb-026fe2154350",
    "type": "CPU",
    "devicePortList": [
        {
            "deviceSwitchInfo": "7e31d0fb-42c5-4cd5-84c7-b37f5fa8e82c",
            "fabricId": "NEC-fmmodel-fmsw-01",
            "fmPortId": "7f132823-f6f5-40bb-abc0-12c878cb180e",
            "LTSSMState": "L0",
            "switchId": "1f2cb78b-088e-4b33-b077-d784942feb2a",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        }
    ],
    "link": [
        {"type": "storage", "deviceID": "7aac1f83-1c10-4b98-8e7f-42119969676a"},
        {"type": "networkInterface", "deviceID": "651ea7b7-b35e-4146-9ed4-d395d2f59068"},
    ],
    "fmDeviceType": "PCIe",
    "PCIClassCode": None,
    "PCIeVendorId": None,
    "PCIeDeviceId": None,
    "PCIeDeviceSerialNumber": None,
    "CPUManufacturer": "corp.A",
    "CPUModel": "Xo1",
    "CPUSerialNumber": "0002",
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}
CPU_EXPECTED_2_2: dict[str, object] = {
    "deviceID": "de99f86c-f32e-4bb1-a3eb-026fe2154350",
    "type": "CPU",
    "devicePortList": [
        {
            "deviceSwitchInfo": "11a1f26b-acd9-4c69-b1d7-ac92b0b49aed",
            "fabricId": "NEC-fmmodel-fmsw-02",
            "fmPortId": "6e4f020f-ebcF-4432-9820-e2c364df391b",
            "LTSSMState": "L0",
            "switchId": "bbce65be-7054-4fea-a0e2-8f9a0b0fb6a1",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        }
    ],
    "link": [
        {"type": "memory", "deviceID": "aa1fbae7-b8ad-4368-b5e6-156040d47d11"},
        {"type": "GPU", "deviceID": "7bb5e10d-48d6-4c83-af4a-986be83ba1bd"},
    ],
    "fmDeviceType": "PCIe",
    "PCIClassCode": None,
    "PCIeVendorId": None,
    "PCIeDeviceId": None,
    "PCIeDeviceSerialNumber": None,
    "CPUManufacturer": "corp.A",
    "CPUModel": "Xo1",
    "CPUSerialNumber": "0002",
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}

PLUGIN_RETURN_STORAGE_1 = [
    FMPortData(
        id="4f4de979-ad99-498b-ade5-1cb404e462fa",
        switchId="1f2cb78b-088e-4b33-b077-d784942feb2a",
        switchPortNumber="11",
        switchPortType="DSP",
        fabricId="NEC-fmmodel-fmsw-01",
        link=["2a79d931-9c8b-4674-94ad-f6d9b00ba50c"],
        deviceType="PCIe",
        PCIClassCode={"base": 0, "sub": 0, "prog": 0},
        PCIeVendorId="8086",
        PCIeDeviceId="2001",
        PCIeDeviceSerialNumber="2000000000002001",
        CPUManufacturer=None,
        CPUModel=None,
        CPUSerialNumber=None,
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
PLUGIN_RETURN_STORAGE_2 = [
    FMPortData(
        id="dc29e83e-26ad-45ae-93dd-0ee9f69245a3",
        switchId="1f2cb78b-088e-4b33-b077-d784942feb2a",
        switchPortNumber="12",
        switchPortType="DSP",
        fabricId="NEC-fmmodel-fmsw-01",
        link=["7f132823-f6f5-40bb-abc0-12c878cb180e"],
        deviceType="PCIe",
        PCIClassCode={"base": 0, "sub": 0, "prog": 0},
        PCIeVendorId="8086",
        PCIeDeviceId="2002",
        PCIeDeviceSerialNumber="2000000000002002",
        CPUManufacturer=None,
        CPUModel=None,
        CPUSerialNumber=None,
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
STORAGE_EXPECTED_1: dict[str, object] = {
    "deviceID": "ee9e4718-df31-4bd8-b37b-455e0e0672f6",
    "type": "storage",
    "devicePortList": [
        {
            "deviceSwitchInfo": "7e31d0fb-42c5-4cd5-84c7-b37f5fa8e82c",
            "fmPortId": "4f4de979-ad99-498b-ade5-1cb404e462fa",
            "fabricId": "NEC-fmmodel-fmsw-01",
            "LTSSMState": "L0",
            "switchId": "1f2cb78b-088e-4b33-b077-d784942feb2a",
            "switchPortNumber": "11",
            "switchPortType": "DSP",
        }
    ],
    "link": [{"type": "CPU", "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c"}],
    "fmDeviceType": "PCIe",
    "PCIClassCode": {"base": 0, "sub": 0, "prog": 0},
    "PCIeVendorId": "8086",
    "PCIeDeviceId": "2001",
    "PCIeDeviceSerialNumber": "2000000000002001",
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}
STORAGE_EXPECTED_2: dict[str, object] = {
    "deviceID": "7aac1f83-1c10-4b98-8e7f-42119969676a",
    "type": "storage",
    "devicePortList": [
        {
            "deviceSwitchInfo": "7e31d0fb-42c5-4cd5-84c7-b37f5fa8e82c",
            "fmPortId": "dc29e83e-26ad-45ae-93dd-0ee9f69245a3",
            "fabricId": "NEC-fmmodel-fmsw-01",
            "LTSSMState": "L0",
            "switchId": "1f2cb78b-088e-4b33-b077-d784942feb2a",
            "switchPortNumber": "12",
            "switchPortType": "DSP",
        }
    ],
    "link": [{"type": "CPU", "deviceID": "de99f86c-f32e-4bb1-a3eb-026fe2154350"}],
    "fmDeviceType": "PCIe",
    "PCIClassCode": {"base": 0, "sub": 0, "prog": 0},
    "PCIeVendorId": "8086",
    "PCIeDeviceId": "2002",
    "PCIeDeviceSerialNumber": "2000000000002002",
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}

PLUGIN_RETURN_NETWORKINTERFACE_1 = [
    FMPortData(
        id="46376548-47e8-40f8-99de-a6f31d10f626",
        switchId="1f2cb78b-088e-4b33-b077-d784942feb2a",
        switchPortNumber="21",
        switchPortType="DSP",
        fabricId="NEC-fmmodel-fmsw-01",
        link=["2a79d931-9c8b-4674-94ad-f6d9b00ba50c"],
        deviceType="PCIe",
        PCIClassCode={"base": 0, "sub": 0, "prog": 0},
        PCIeVendorId="8086",
        PCIeDeviceId="3001",
        PCIeDeviceSerialNumber="2000000000003001",
        CPUManufacturer=None,
        CPUModel=None,
        CPUSerialNumber=None,
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
PLUGIN_RETURN_NETWORKINTERFACE_2 = [
    FMPortData(
        id="3d109460-c789-461a-bf52-30cae9c86d1d",
        switchId="1f2cb78b-088e-4b33-b077-d784942feb2a",
        switchPortNumber="22",
        switchPortType="DSP",
        fabricId="NEC-fmmodel-fmsw-01",
        link=["7f132823-f6f5-40bb-abc0-12c878cb180e"],
        deviceType="PCIe",
        PCIClassCode={"base": 0, "sub": 0, "prog": 0},
        PCIeVendorId="8086",
        PCIeDeviceId="3002",
        PCIeDeviceSerialNumber="2000000000003002",
        CPUManufacturer=None,
        CPUModel=None,
        CPUSerialNumber=None,
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
NETWORKINTERFACE_EXPECTED_1: dict[str, object] = {
    "deviceID": "00029c15-bccb-4f9a-a251-51c9d307a097",
    "type": "networkInterface",
    "devicePortList": [
        {
            "deviceSwitchInfo": "7e31d0fb-42c5-4cd5-84c7-b37f5fa8e82c",
            "fmPortId": "46376548-47e8-40f8-99de-a6f31d10f626",
            "fabricId": "NEC-fmmodel-fmsw-01",
            "LTSSMState": "L0",
            "switchId": "1f2cb78b-088e-4b33-b077-d784942feb2a",
            "switchPortNumber": "21",
            "switchPortType": "DSP",
        }
    ],
    "link": [{"type": "CPU", "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c"}],
    "fmDeviceType": "PCIe",
    "PCIClassCode": {"base": 0, "sub": 0, "prog": 0},
    "PCIeVendorId": "8086",
    "PCIeDeviceId": "3001",
    "PCIeDeviceSerialNumber": "2000000000003001",
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}
NETWORKINTERFACE_EXPECTED_2: dict[str, object] = {
    "deviceID": "651ea7b7-b35e-4146-9ed4-d395d2f59068",
    "type": "networkInterface",
    "devicePortList": [
        {
            "deviceSwitchInfo": "7e31d0fb-42c5-4cd5-84c7-b37f5fa8e82c",
            "fmPortId": "3d109460-c789-461a-bf52-30cae9c86d1d",
            "fabricId": "NEC-fmmodel-fmsw-01",
            "LTSSMState": "L0",
            "switchId": "1f2cb78b-088e-4b33-b077-d784942feb2a",
            "switchPortNumber": "22",
            "switchPortType": "DSP",
        }
    ],
    "link": [{"type": "CPU", "deviceID": "de99f86c-f32e-4bb1-a3eb-026fe2154350"}],
    "fmDeviceType": "PCIe",
    "PCIClassCode": {"base": 0, "sub": 0, "prog": 0},
    "PCIeVendorId": "8086",
    "PCIeDeviceId": "3002",
    "PCIeDeviceSerialNumber": "2000000000003002",
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}

PLUGIN_RETURN_MEMORY_1 = [
    FMPortData(
        id="ba123bd1-04bd-40a5-9773-6a647a3f5c01",
        switchId="bbce65be-7054-4fea-a0e2-8f9a0b0fb6a1",
        switchPortNumber="11",
        switchPortType="DSP",
        fabricId="NEC-fmmodel-fmsw-02",
        link=["eee64be1-d07e-4e78-b82a-3f05ec8d10e8"],
        deviceType="CXL-Type3",
        PCIClassCode={"base": 0, "sub": 0, "prog": 0},
        PCIeVendorId="8086",
        PCIeDeviceId="1001",
        PCIeDeviceSerialNumber="2000000000001001",
        CPUManufacturer=None,
        CPUModel=None,
        CPUSerialNumber=None,
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity={"volatile": 1073741824, "persistent": 0, "total": 1073741824},
    )
]
PLUGIN_RETURN_MEMORY_2 = [
    FMPortData(
        id="971b59b0-b4fa-4f32-b54b-9fded3034e0b",
        switchId="bbce65be-7054-4fea-a0e2-8f9a0b0fb6a1",
        switchPortNumber="12",
        switchPortType="DSP",
        fabricId="NEC-fmmodel-fmsw-02",
        link=["6e4f020f-ebcF-4432-9820-e2c364df391b"],
        deviceType="CXL-Type3",
        PCIClassCode={"base": 0, "sub": 0, "prog": 0},
        PCIeVendorId="8086",
        PCIeDeviceId="1002",
        PCIeDeviceSerialNumber="2000000000001002",
        CPUManufacturer=None,
        CPUModel=None,
        CPUSerialNumber=None,
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity={"volatile": 1073741824, "persistent": 0, "total": 1073741824},
    )
]
MEMORY_EXPECTED_1: dict[str, object] = {
    "deviceID": "1c440d70-ae46-42f6-b03b-6df28d0913af",
    "type": "memory",
    "devicePortList": [
        {
            "deviceSwitchInfo": "11a1f26b-acd9-4c69-b1d7-ac92b0b49aed",
            "fmPortId": "ba123bd1-04bd-40a5-9773-6a647a3f5c01",
            "fabricId": "NEC-fmmodel-fmsw-02",
            "LTSSMState": "L0",
            "switchId": "bbce65be-7054-4fea-a0e2-8f9a0b0fb6a1",
            "switchPortNumber": "11",
            "switchPortType": "DSP",
        }
    ],
    "link": [{"type": "CPU", "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c"}],
    "fmDeviceType": "CXL-Type3",
    "PCIClassCode": {"base": 0, "sub": 0, "prog": 0},
    "PCIeVendorId": "8086",
    "PCIeDeviceId": "1001",
    "PCIeDeviceSerialNumber": "2000000000001001",
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "deviceKeys": {},
    "portKeys": {},
    "capacity": {"volatile": 1073741824, "persistent": 0, "total": 1073741824},
}
MEMORY_EXPECTED_2: dict[str, object] = {
    "deviceID": "aa1fbae7-b8ad-4368-b5e6-156040d47d11",
    "type": "memory",
    "devicePortList": [
        {
            "deviceSwitchInfo": "11a1f26b-acd9-4c69-b1d7-ac92b0b49aed",
            "fmPortId": "971b59b0-b4fa-4f32-b54b-9fded3034e0b",
            "fabricId": "NEC-fmmodel-fmsw-02",
            "LTSSMState": "L0",
            "switchId": "bbce65be-7054-4fea-a0e2-8f9a0b0fb6a1",
            "switchPortNumber": "12",
            "switchPortType": "DSP",
        }
    ],
    "link": [{"type": "CPU", "deviceID": "de99f86c-f32e-4bb1-a3eb-026fe2154350"}],
    "fmDeviceType": "CXL-Type3",
    "PCIClassCode": {"base": 0, "sub": 0, "prog": 0},
    "PCIeVendorId": "8086",
    "PCIeDeviceId": "1002",
    "PCIeDeviceSerialNumber": "2000000000001002",
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "deviceKeys": {},
    "portKeys": {},
    "capacity": {"volatile": 1073741824, "persistent": 0, "total": 1073741824},
}

PLUGIN_RETURN_GPU_1 = [
    FMPortData(
        id="af312740-e804-4d11-a9a7-3f5496a80a2f",
        switchId="bbce65be-7054-4fea-a0e2-8f9a0b0fb6a1",
        switchPortNumber="21",
        switchPortType="DSP",
        fabricId="NEC-fmmodel-fmsw-02",
        link=["eee64be1-d07e-4e78-b82a-3f05ec8d10e8"],
        deviceType="PCIe",
        PCIClassCode={"base": 0, "sub": 0, "prog": 0},
        PCIeVendorId="8086",
        PCIeDeviceId="5001",
        PCIeDeviceSerialNumber="2000000000005001",
        CPUManufacturer=None,
        CPUModel=None,
        CPUSerialNumber=None,
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
PLUGIN_RETURN_GPU_2 = [
    FMPortData(
        id="30c15d32-44fd-4c80-993c-8ee51b68e0c7",
        switchId="bbce65be-7054-4fea-a0e2-8f9a0b0fb6a1",
        switchPortNumber="22",
        switchPortType="DSP",
        fabricId="NEC-fmmodel-fmsw-02",
        link=["6e4f020f-ebcF-4432-9820-e2c364df391b"],
        deviceType="PCIe",
        PCIClassCode={"base": 0, "sub": 0, "prog": 0},
        PCIeVendorId="8086",
        PCIeDeviceId="5002",
        PCIeDeviceSerialNumber="2000000000005002",
        CPUManufacturer=None,
        CPUModel=None,
        CPUSerialNumber=None,
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
PLUGIN_RETURN_GPU_3 = [
    FMPortData(
        id="af312740-e804-4d11-a9a7-3f5496a80a2f",
        switchId="bbce65be-7054-4fea-a0e2-8f9a0b0fb6a1",
        switchPortNumber="21",
        switchPortType="DSP",
        fabricId="NEC-fmmodel-fmsw-02",
        link=["553ec090-adde-a0e1-b7ea-d98d35197a27"],
        deviceType="PCIe",
        PCIClassCode={"base": 0, "sub": 0, "prog": 0},
        PCIeVendorId="8086",
        PCIeDeviceId="5001",
        PCIeDeviceSerialNumber="2000000000005001",
        CPUManufacturer=None,
        CPUModel=None,
        CPUSerialNumber=None,
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
GPU_EXPECTED_1: dict[str, object] = {
    "deviceID": "e15a736e-ea75-4f5f-8c8d-970e0705bb20",
    "type": "GPU",
    "devicePortList": [
        {
            "deviceSwitchInfo": "11a1f26b-acd9-4c69-b1d7-ac92b0b49aed",
            "fmPortId": "af312740-e804-4d11-a9a7-3f5496a80a2f",
            "fabricId": "NEC-fmmodel-fmsw-02",
            "LTSSMState": "L0",
            "switchId": "bbce65be-7054-4fea-a0e2-8f9a0b0fb6a1",
            "switchPortNumber": "21",
            "switchPortType": "DSP",
        }
    ],
    "link": [{"type": "CPU", "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c"}],
    "fmDeviceType": "PCIe",
    "PCIClassCode": {"base": 0, "sub": 0, "prog": 0},
    "PCIeVendorId": "8086",
    "PCIeDeviceId": "5001",
    "PCIeDeviceSerialNumber": "2000000000005001",
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}
GPU_EXPECTED_2: dict[str, object] = {
    "deviceID": "7bb5e10d-48d6-4c83-af4a-986be83ba1bd",
    "type": "GPU",
    "devicePortList": [
        {
            "deviceSwitchInfo": "11a1f26b-acd9-4c69-b1d7-ac92b0b49aed",
            "fmPortId": "30c15d32-44fd-4c80-993c-8ee51b68e0c7",
            "fabricId": "NEC-fmmodel-fmsw-02",
            "LTSSMState": "L0",
            "switchId": "bbce65be-7054-4fea-a0e2-8f9a0b0fb6a1",
            "switchPortNumber": "22",
            "switchPortType": "DSP",
        }
    ],
    "link": [{"type": "CPU", "deviceID": "de99f86c-f32e-4bb1-a3eb-026fe2154350"}],
    "fmDeviceType": "PCIe",
    "PCIClassCode": {"base": 0, "sub": 0, "prog": 0},
    "PCIeVendorId": "8086",
    "PCIeDeviceId": "5002",
    "PCIeDeviceSerialNumber": "2000000000005002",
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}
GPU_EXPECTED_3: dict[str, object] = {
    "deviceID": "e15a736e-ea75-4f5f-8c8d-970e0705bb20",
    "type": "GPU",
    "devicePortList": [
        {
            "deviceSwitchInfo": "11a1f26b-acd9-4c69-b1d7-ac92b0b49aed",
            "fmPortId": "af312740-e804-4d11-a9a7-3f5496a80a2f",
            "fabricId": "NEC-fmmodel-fmsw-02",
            "LTSSMState": "L0",
            "switchId": "bbce65be-7054-4fea-a0e2-8f9a0b0fb6a1",
            "switchPortNumber": "21",
            "switchPortType": "DSP",
        }
    ],
    "link": [{"type": "destinationFabricAdapter", "deviceID": "3ae0c4a1-a9a6-8bb3-b2ab-9afdbebb18cc"}],
    "fmDeviceType": "PCIe",
    "PCIClassCode": {"base": 0, "sub": 0, "prog": 0},
    "PCIeVendorId": "8086",
    "PCIeDeviceId": "5001",
    "PCIeDeviceSerialNumber": "2000000000005001",
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}

PLUGIN_RETURN_USP_PORT = [
    FMPortData(
        id="553ec090-adde-a0e1-b7ea-d98d35197a27",
        switchId="bbce65be-7054-4fea-a0e2-8f9a0b0fb6a1",
        switchPortNumber="06",
        switchPortType="DSP",
        fabricId="NEC-fmmodel-fmsw-02",
        link=["af312740-e804-4d11-a9a7-3f5496a80a2f"],
        deviceType="PCIe",
        PCIClassCode={"base": 0, "sub": 0, "prog": 0},
        PCIeVendorId="8086",
        PCIeDeviceId="3101",
        PCIeDeviceSerialNumber="2000000000003101",
        CPUManufacturer=None,
        CPUModel=None,
        CPUSerialNumber=None,
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
PLUGIN_RETURN_DFA = [
    FMPortData(
        id="2fdfc812-a665-ded8-0619-36a9144adf57",
        switchId="5e60a865-5cee-e562-f9db-8337d6ad411c",
        switchPortNumber="01",
        switchPortType="DSP",
        fabricId="NEC-fmmodel-fmsw-03",
        link=["0e8db7f6-7e08-dd56-7f59-9981b1c792fe"],
        deviceType="PCIe",
        PCIClassCode={"base": 0, "sub": 0, "prog": 0},
        PCIeVendorId="8086",
        PCIeDeviceId="3301",
        PCIeDeviceSerialNumber="2000000000003301",
        CPUManufacturer=None,
        CPUModel=None,
        CPUSerialNumber=None,
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
PLUGIN_RETURN_SFA = [
    FMPortData(
        id="0e8db7f6-7e08-dd56-7f59-9981b1c792fe",
        switchId="5e60a865-5cee-e562-f9db-8337d6ad411c",
        switchPortNumber="02",
        switchPortType="DSP",
        fabricId="NEC-fmmodel-fmsw-03",
        link=["2fdfc812-a665-ded8-0619-36a9144adf57"],
        deviceType="PCIe",
        PCIClassCode={"base": 0, "sub": 0, "prog": 0},
        PCIeVendorId="8086",
        PCIeDeviceId="3301",
        PCIeDeviceSerialNumber="2000000000003301",
        CPUManufacturer=None,
        CPUModel=None,
        CPUSerialNumber=None,
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
USP_PORT_EXPECTED: dict[str, object] = {
    "deviceID": "706faead-6d42-7916-2e05-cbb917398fab",
    "type": "networkInterface",
    "devicePortList": [
        {
            "deviceSwitchInfo": "11a1f26b-acd9-4c69-b1d7-ac92b0b49aed",
            "fmPortId": "553ec090-adde-a0e1-b7ea-d98d35197a27",
            "fabricId": "NEC-fmmodel-fmsw-02",
            "LTSSMState": "L0",
            "switchId": "bbce65be-7054-4fea-a0e2-8f9a0b0fb6a1",
            "switchPortNumber": "06",
            "switchPortType": "DSP",
        }
    ],
    "link": [{"type": "GPU", "deviceID": "e15a736e-ea75-4f5f-8c8d-970e0705bb20"}],
    "fmDeviceType": "PCIe",
    "PCIClassCode": {"base": 0, "sub": 0, "prog": 0},
    "PCIeVendorId": "8086",
    "PCIeDeviceId": "3101",
    "PCIeDeviceSerialNumber": "2000000000003101",
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}
DFA_EXPECTED: dict[str, object] = {
    "deviceID": "3ae0c4a1-a9a6-8bb3-b2ab-9afdbebb18cc",
    "type": "destinationFabricAdapter",
    "devicePortList": [
        {
            "deviceSwitchInfo": "aa77c091-5d7e-90c9-6a22-e96db45a035b",
            "fmPortId": "2fdfc812-a665-ded8-0619-36a9144adf57",
            "fabricId": "NEC-fmmodel-fmsw-03",
            "LTSSMState": "L0",
            "switchId": "5e60a865-5cee-e562-f9db-8337d6ad411c",
            "switchPortNumber": "01",
            "switchPortType": "DSP",
        }
    ],
    "link": [{"type": "sourceFabricAdapter", "deviceID": "83effa21-2fb6-a339-be34-0916564e7ce5"}],
    "fmDeviceType": "PCIe",
    "PCIClassCode": {"base": 0, "sub": 0, "prog": 0},
    "PCIeVendorId": "8086",
    "PCIeDeviceId": "3301",
    "PCIeDeviceSerialNumber": "2000000000003301",
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}
SFA_EXPECTED: dict[str, object] = {
    "deviceID": "83effa21-2fb6-a339-be34-0916564e7ce5",
    "type": "sourceFabricAdapter",
    "devicePortList": [
        {
            "deviceSwitchInfo": "5e60a865-5cee-e562-f9db-8337d6ad411c",
            "fmPortId": "0e8db7f6-7e08-dd56-7f59-9981b1c792fe",
            "fabricId": "NEC-fmmodel-fmsw-03",
            "LTSSMState": "L0",
            "switchId": "aa77c091-5d7e-90c9-6a22-e96db45a035b",
            "switchPortNumber": "02",
            "switchPortType": "USP",
        }
    ],
    "link": [{"type": "destinationFabricAdapter", "deviceID": "3ae0c4a1-a9a6-8bb3-b2ab-9afdbebb18cc"}],
    "fmDeviceType": "PCIe",
    "PCIClassCode": {"base": 0, "sub": 0, "prog": 0},
    "PCIeVendorId": "8086",
    "PCIeDeviceId": "3201",
    "PCIeDeviceSerialNumber": "2000000000003201",
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}

PLUGIN_RETURN_REQUIRED_ONLY_1 = [
    FMPortData(
        id="2a79d931-9c8b-4674-94ad-f6d9b00ba50c",
        switchId=None,
        switchPortNumber=None,
        switchPortType=None,
        fabricId=None,
        link=None,
        deviceType=None,
        PCIClassCode=None,
        PCIeVendorId=None,
        PCIeDeviceId=None,
        PCIeDeviceSerialNumber=None,
        CPUManufacturer=None,
        CPUModel=None,
        CPUSerialNumber=None,
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
PLUGIN_RETURN_REQUIRED_ONLY_2 = [
    FMPortData(
        id="eee64be1-d07e-4e78-b82a-3f05ec8d10e8",
        switchId=None,
        switchPortNumber=None,
        switchPortType=None,
        fabricId=None,
        link=None,
        deviceType=None,
        PCIClassCode=None,
        PCIeVendorId=None,
        PCIeDeviceId=None,
        PCIeDeviceSerialNumber=None,
        CPUManufacturer=None,
        CPUModel=None,
        CPUSerialNumber=None,
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
REQUIRED_ONLY_EXPECTED_1: dict[str, object] = {
    "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c",
    "type": "CPU",
    "devicePortList": [
        {
            "deviceSwitchInfo": None,
            "fmPortId": "2a79d931-9c8b-4674-94ad-f6d9b00ba50c",
            "fabricId": None,
            "LTSSMState": "L0",
            "switchId": None,
            "switchPortNumber": None,
            "switchPortType": None,
        }
    ],
    "fmDeviceType": None,
    "PCIClassCode": None,
    "PCIeVendorId": None,
    "PCIeDeviceId": None,
    "PCIeDeviceSerialNumber": None,
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}
REQUIRED_ONLY_EXPECTED_2: dict[str, object] = {
    "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c",
    "type": "CPU",
    "devicePortList": [
        {
            "deviceSwitchInfo": None,
            "fmPortId": "eee64be1-d07e-4e78-b82a-3f05ec8d10e8",
            "fabricId": None,
            "LTSSMState": "L0",
            "switchId": None,
            "switchPortNumber": None,
            "switchPortType": None,
        }
    ],
    "fmDeviceType": None,
    "PCIClassCode": None,
    "PCIeVendorId": None,
    "PCIeDeviceId": None,
    "PCIeDeviceSerialNumber": None,
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}


def _log_contains(record, level, message) -> bool:
    return next(filter(lambda x: (x[1] == level) and (message in x[2]), record), None) is not None


def _mock_device_id_to_manager_id_multi_hostport(device_id) -> dict[str, list[str] | None]:
    table: dict[str, dict[str, list[str] | None]] = {
        "28c2318b-6b69-4f41-9865-166906ca2e1c": {"fm": ["qemu-001", "qemu-002"], "oob": []},  # CPU
        "ee9e4718-df31-4bd8-b37b-455e0e0672f6": {"fm": ["qemu-001"], "oob": []},  # storage
        "7aac1f83-1c10-4b98-8e7f-42119969676a": {"fm": ["qemu-001"], "oob": []},  # storage
        "00029c15-bccb-4f9a-a251-51c9d307a097": {"fm": ["qemu-001"], "oob": []},  # networkInterface
        "651ea7b7-b35e-4146-9ed4-d395d2f59068": {"fm": ["qemu-001"], "oob": []},  # networkInterface
        "de99f86c-f32e-4bb1-a3eb-026fe2154350": {"fm": ["qemu-001", "qemu-002"], "oob": []},  # CPU
        "1c440d70-ae46-42f6-b03b-6df28d0913af": {"fm": ["qemu-002"], "oob": []},  # memory
        "aa1fbae7-b8ad-4368-b5e6-156040d47d11": {"fm": ["qemu-002"], "oob": []},  # memory
        "e15a736e-ea75-4f5f-8c8d-970e0705bb20": {"fm": ["qemu-002"], "oob": []},  # GPU
        "7bb5e10d-48d6-4c83-af4a-986be83ba1bd": {"fm": ["qemu-002"], "oob": []},  # GPU
        "706faead-6d42-7916-2e05-cbb917398fab": {"fm": ["qemu-002"], "oob": []},  # networkInterface
        "3ae0c4a1-a9a6-8bb3-b2ab-9afdbebb18cc": {"fm": ["fabric-001"], "oob": []},  # destinationFabricAdapter
        "83effa21-2fb6-a339-be34-0916564e7ce5": {"fm": ["fabric-001"], "oob": []},  # sourceFabricAdapter
        "1e13e51c-80fb-4751-84b3-126e33793ec4": {"fm": [], "oob": []},
    }

    if device_id in table:
        return table[device_id]

    raise exc.ConfigurationHWControlError


def _mock_device_id_to_fm_port_id_multi_hostport(device_id, fm_manager_id) -> list[str]:
    table_001 = {
        "28c2318b-6b69-4f41-9865-166906ca2e1c": ["2a79d931-9c8b-4674-94ad-f6d9b00ba50c"],
        "de99f86c-f32e-4bb1-a3eb-026fe2154350": ["7f132823-f6f5-40bb-abc0-12c878cb180e"],
        "ee9e4718-df31-4bd8-b37b-455e0e0672f6": ["4f4de979-ad99-498b-ade5-1cb404e462fa"],
        "7aac1f83-1c10-4b98-8e7f-42119969676a": ["dc29e83e-26ad-45ae-93dd-0ee9f69245a3"],
        "00029c15-bccb-4f9a-a251-51c9d307a097": ["46376548-47e8-40f8-99de-a6f31d10f626"],
        "651ea7b7-b35e-4146-9ed4-d395d2f59068": ["3d109460-c789-461a-bf52-30cae9c86d1d"],
    }
    table_002 = {
        "28c2318b-6b69-4f41-9865-166906ca2e1c": ["eee64be1-d07e-4e78-b82a-3f05ec8d10e8"],
        "de99f86c-f32e-4bb1-a3eb-026fe2154350": ["6e4f020f-ebcF-4432-9820-e2c364df391b"],
        "1c440d70-ae46-42f6-b03b-6df28d0913af": ["ba123bd1-04bd-40a5-9773-6a647a3f5c01"],
        "aa1fbae7-b8ad-4368-b5e6-156040d47d11": ["971b59b0-b4fa-4f32-b54b-9fded3034e0b"],
        "e15a736e-ea75-4f5f-8c8d-970e0705bb20": ["af312740-e804-4d11-a9a7-3f5496a80a2f"],
        "7bb5e10d-48d6-4c83-af4a-986be83ba1bd": ["30c15d32-44fd-4c80-993c-8ee51b68e0c7"],
        "706faead-6d42-7916-2e05-cbb917398fab": ["553ec090-adde-a0e1-b7ea-d98d35197a27"],
    }
    table_003 = {
        "3ae0c4a1-a9a6-8bb3-b2ab-9afdbebb18cc": ["2fdfc812-a665-ded8-0619-36a9144adf57"],
        "83effa21-2fb6-a339-be34-0916564e7ce5": ["0e8db7f6-7e08-dd56-7f59-9981b1c792fe"],
    }

    if fm_manager_id == "qemu-001" and device_id in table_001:
        return table_001[device_id]
    if fm_manager_id == "qemu-002" and device_id in table_002:
        return table_002[device_id]
    if fm_manager_id == "fabric-001" and device_id in table_003:
        return table_003[device_id]

    raise exc.ConfigurationHWControlError


def _mock_device_id_to_device_type(device_id) -> str:
    table = {
        "28c2318b-6b69-4f41-9865-166906ca2e1c": "CPU",
        "de99f86c-f32e-4bb1-a3eb-026fe2154350": "CPU",
        "ee9e4718-df31-4bd8-b37b-455e0e0672f6": "storage",
        "7aac1f83-1c10-4b98-8e7f-42119969676a": "storage",
        "00029c15-bccb-4f9a-a251-51c9d307a097": "networkInterface",
        "651ea7b7-b35e-4146-9ed4-d395d2f59068": "networkInterface",
        "706faead-6d42-7916-2e05-cbb917398fab": "networkInterface",
        "3ae0c4a1-a9a6-8bb3-b2ab-9afdbebb18cc": "destinationFabricAdapter",
        "83effa21-2fb6-a339-be34-0916564e7ce5": "sourceFabricAdapter",
        "1c440d70-ae46-42f6-b03b-6df28d0913af": "memory",
        "aa1fbae7-b8ad-4368-b5e6-156040d47d11": "memory",
        "e15a736e-ea75-4f5f-8c8d-970e0705bb20": "GPU",
        "7bb5e10d-48d6-4c83-af4a-986be83ba1bd": "GPU",
    }

    if device_id in table:
        return table[device_id]

    raise exc.ConfigurationHWControlError


def _mock_fm_port_id_to_device_id(fm_port_id, fm_manager_id) -> str | None:
    table_001 = {
        "2a79d931-9c8b-4674-94ad-f6d9b00ba50c": "28c2318b-6b69-4f41-9865-166906ca2e1c",
        "7f132823-f6f5-40bb-abc0-12c878cb180e": "de99f86c-f32e-4bb1-a3eb-026fe2154350",
        "4f4de979-ad99-498b-ade5-1cb404e462fa": "ee9e4718-df31-4bd8-b37b-455e0e0672f6",
        "dc29e83e-26ad-45ae-93dd-0ee9f69245a3": "7aac1f83-1c10-4b98-8e7f-42119969676a",
        "46376548-47e8-40f8-99de-a6f31d10f626": "00029c15-bccb-4f9a-a251-51c9d307a097",
        "3d109460-c789-461a-bf52-30cae9c86d1d": "651ea7b7-b35e-4146-9ed4-d395d2f59068",
    }
    table_002 = {
        "eee64be1-d07e-4e78-b82a-3f05ec8d10e8": "28c2318b-6b69-4f41-9865-166906ca2e1c",
        "6e4f020f-ebcF-4432-9820-e2c364df391b": "de99f86c-f32e-4bb1-a3eb-026fe2154350",
        "ba123bd1-04bd-40a5-9773-6a647a3f5c01": "1c440d70-ae46-42f6-b03b-6df28d0913af",
        "971b59b0-b4fa-4f32-b54b-9fded3034e0b": "aa1fbae7-b8ad-4368-b5e6-156040d47d11",
        "af312740-e804-4d11-a9a7-3f5496a80a2f": "e15a736e-ea75-4f5f-8c8d-970e0705bb20",
        "30c15d32-44fd-4c80-993c-8ee51b68e0c7": "7bb5e10d-48d6-4c83-af4a-986be83ba1bd",
        "553ec090-adde-a0e1-b7ea-d98d35197a27": "706faead-6d42-7916-2e05-cbb917398fab",
    }
    table_003 = {
        "2fdfc812-a665-ded8-0619-36a9144adf57": "3ae0c4a1-a9a6-8bb3-b2ab-9afdbebb18cc",
        "0e8db7f6-7e08-dd56-7f59-9981b1c792fe": "83effa21-2fb6-a339-be34-0916564e7ce5",
    }

    if fm_manager_id == "qemu-001" and fm_port_id in table_001:
        return table_001[fm_port_id]
    if fm_manager_id == "qemu-002" and fm_port_id in table_002:
        return table_002[fm_port_id]
    if fm_manager_id == "fabric-001" and fm_port_id in table_003:
        return table_003[fm_port_id]

    raise exc.ConfigurationHWControlError


def _mock_fm_switch_id_to_device_id(fm_port_id, fm_manager_id):
    table = {
        "1f2cb78b-088e-4b33-b077-d784942feb2a": "7e31d0fb-42c5-4cd5-84c7-b37f5fa8e82c",
        "bbce65be-7054-4fea-a0e2-8f9a0b0fb6a1": "11a1f26b-acd9-4c69-b1d7-ac92b0b49aed",
        "5e60a865-5cee-e562-f9db-8337d6ad411c": "aa77c091-5d7e-90c9-6a22-e96db45a035b",
    }

    if fm_manager_id == "qemu-001" and fm_port_id in table:
        return table[fm_port_id]
    if fm_manager_id == "qemu-002" and fm_port_id in table:
        return table[fm_port_id]
    if fm_manager_id == "fabric-001" and fm_port_id in table:
        return table[fm_port_id]

    return None


def _mock_device_id_to_switch_port_type(device_id: str) -> str | None:
    table = {
        "706faead-6d42-7916-2e05-cbb917398fab": "USP",
        "3ae0c4a1-a9a6-8bb3-b2ab-9afdbebb18cc": "DSP",
        "83effa21-2fb6-a339-be34-0916564e7ce5": "USP",
        "e15a736e-ea75-4f5f-8c8d-970e0705bb20": "DSP",
        "7bb5e10d-48d6-4c83-af4a-986be83ba1bd": "DSP",
    }

    return table.get(device_id)


def _mock_get_device_id_of_switch_port_type(
    device_id: str, switch_port_type: const.SwitchPortType | None
) -> str | None:
    table = {
        "706faead-6d42-7916-2e05-cbb917398fab": {
            const.SwitchPortType.USP: None,
            const.SwitchPortType.DSP: "3ae0c4a1-a9a6-8bb3-b2ab-9afdbebb18cc",
            None: None,
        },
        "3ae0c4a1-a9a6-8bb3-b2ab-9afdbebb18cc": {
            const.SwitchPortType.USP: "706faead-6d42-7916-2e05-cbb917398fab",
            const.SwitchPortType.DSP: None,
            None: None,
        },
    }

    return table.get(device_id, {}).get(switch_port_type)


def test_spec_fm_cpu_1(mocker, caplog):
    """FM Information Acquisition Test CPU"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "2a79d931-9c8b-4674-94ad-f6d9b00ba50c":
                return {"data": PLUGIN_RETURN_CPU_1_1}
            if target_id == "eee64be1-d07e-4e78-b82a-3f05ec8d10e8":
                return {"data": PLUGIN_RETURN_CPU_1_2}
            if target_id == "7f132823-f6f5-40bb-abc0-12c878cb180e":
                return {"data": PLUGIN_RETURN_CPU_2_1}
            if target_id == "6e4f020f-ebcF-4432-9820-e2c364df391b":
                return {"data": PLUGIN_RETURN_CPU_2_2}
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [CPU_EXPECTED_1_1, CPU_EXPECTED_1_2]}
    actual = spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-001,"
        " device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c,"
        " fm_port_id: 2a79d931-9c8b-4674-94ad-f6d9b00ba50c Plugin Respond.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-002,"
        " device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c,"
        " fm_port_id: eee64be1-d07e-4e78-b82a-3f05ec8d10e8 Plugin Respond.",
    )
    assert expected == actual


def test_spec_fm_cpu_2(mocker, caplog):
    """FM Information Acquisition Test CPU"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "2a79d931-9c8b-4674-94ad-f6d9b00ba50c":
                return {"data": PLUGIN_RETURN_CPU_1_1}
            if target_id == "eee64be1-d07e-4e78-b82a-3f05ec8d10e8":
                return {"data": PLUGIN_RETURN_CPU_1_2}
            if target_id == "7f132823-f6f5-40bb-abc0-12c878cb180e":
                return {"data": PLUGIN_RETURN_CPU_2_1}
            if target_id == "6e4f020f-ebcF-4432-9820-e2c364df391b":
                return {"data": PLUGIN_RETURN_CPU_2_2}
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [CPU_EXPECTED_2_1, CPU_EXPECTED_2_2]}
    actual = spec_fm.get_spec_fm("de99f86c-f32e-4bb1-a3eb-026fe2154350", "CPU")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-001,"
        " device_id: de99f86c-f32e-4bb1-a3eb-026fe2154350,"
        " fm_port_id: 7f132823-f6f5-40bb-abc0-12c878cb180e Plugin Respond.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-002,"
        " device_id: de99f86c-f32e-4bb1-a3eb-026fe2154350,"
        " fm_port_id: 6e4f020f-ebcF-4432-9820-e2c364df391b Plugin Respond.",
    )
    assert expected == actual


def test_spec_fm_cpu_link_is_none(mocker, caplog):
    """FM Information Acquisition Test CPU  link is None"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "2a79d931-9c8b-4674-94ad-f6d9b00ba50c":
                test_data = PLUGIN_RETURN_CPU_1_1.copy()
                test_data[0].link = None
                return {"data": test_data}
            if target_id == "eee64be1-d07e-4e78-b82a-3f05ec8d10e8":
                test_data = PLUGIN_RETURN_CPU_1_2.copy()
                test_data[0].link = None
                return {"data": test_data}
            if target_id == "7f132823-f6f5-40bb-abc0-12c878cb180e":
                test_data = PLUGIN_RETURN_CPU_2_1.copy()
                test_data[0].link = None
                return {"data": test_data}
            if target_id == "6e4f020f-ebcF-4432-9820-e2c364df391b":
                test_data = PLUGIN_RETURN_CPU_2_2.copy()
                test_data[0].link = None
                return {"data": test_data}
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

    spec_fm = GetSpecFMInfo()
    expected_data_1 = CPU_EXPECTED_1_1.copy()
    expected_data_1.pop("link", None)
    expected_data_2 = CPU_EXPECTED_1_2.copy()
    expected_data_2.pop("link", None)
    expected = {"data": [expected_data_1, expected_data_2]}
    actual = spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-001,"
        " device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c,"
        " fm_port_id: 2a79d931-9c8b-4674-94ad-f6d9b00ba50c Plugin Respond.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-002,"
        " device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c,"
        " fm_port_id: eee64be1-d07e-4e78-b82a-3f05ec8d10e8 Plugin Respond.",
    )
    assert expected == actual


def test_spec_fm_cpu_link_is_empty(mocker, caplog):
    """FM Information Acquisition Test CPU link is empty array"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "2a79d931-9c8b-4674-94ad-f6d9b00ba50c":
                test_data = PLUGIN_RETURN_CPU_1_1.copy()
                test_data[0].link = []
                return {"data": test_data}
            if target_id == "eee64be1-d07e-4e78-b82a-3f05ec8d10e8":
                test_data = PLUGIN_RETURN_CPU_1_2.copy()
                test_data[0].link = []
                return {"data": test_data}
            if target_id == "7f132823-f6f5-40bb-abc0-12c878cb180e":
                test_data = PLUGIN_RETURN_CPU_2_1.copy()
                test_data[0].link = []
                return {"data": test_data}
            if target_id == "6e4f020f-ebcF-4432-9820-e2c364df391b":
                test_data = PLUGIN_RETURN_CPU_2_2.copy()
                test_data[0].link = []
                return {"data": test_data}
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

    spec_fm = GetSpecFMInfo()
    expected_data_1 = CPU_EXPECTED_2_1.copy()
    expected_data_1.pop("link", None)
    expected_data_2 = CPU_EXPECTED_2_2.copy()
    expected_data_2.pop("link", None)
    expected = {"data": [expected_data_1, expected_data_2]}
    actual = spec_fm.get_spec_fm("de99f86c-f32e-4bb1-a3eb-026fe2154350", "CPU")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-001,"
        " device_id: de99f86c-f32e-4bb1-a3eb-026fe2154350,"
        " fm_port_id: 7f132823-f6f5-40bb-abc0-12c878cb180e Plugin Respond.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-002,"
        " device_id: de99f86c-f32e-4bb1-a3eb-026fe2154350,"
        " fm_port_id: 6e4f020f-ebcF-4432-9820-e2c364df391b Plugin Respond.",
    )
    assert expected == actual


def test_spec_fm_storage(mocker, caplog):
    """FM Information Acquisition Test Storage"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "4f4de979-ad99-498b-ade5-1cb404e462fa":
                return {"data": PLUGIN_RETURN_STORAGE_1}
            if target_id == "dc29e83e-26ad-45ae-93dd-0ee9f69245a3":
                return {"data": PLUGIN_RETURN_STORAGE_2}
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [STORAGE_EXPECTED_1]}
    actual = spec_fm.get_spec_fm("ee9e4718-df31-4bd8-b37b-455e0e0672f6", "storage")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: manager_id: qemu-001,"
        " device_id: ee9e4718-df31-4bd8-b37b-455e0e0672f6,"
        " fm_port_id: 4f4de979-ad99-498b-ade5-1cb404e462fa Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-001,"
        " device_id: ee9e4718-df31-4bd8-b37b-455e0e0672f6,"
        " fm_port_id: 4f4de979-ad99-498b-ade5-1cb404e462fa Plugin Respond.",
    )
    assert expected == actual


def test_spec_fm_network_interface(mocker, caplog):
    """FM Information Acquisition Test networkInterface"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "46376548-47e8-40f8-99de-a6f31d10f626":
                return {"data": PLUGIN_RETURN_NETWORKINTERFACE_1}
            if target_id == "3d109460-c789-461a-bf52-30cae9c86d1d":
                return {"data": PLUGIN_RETURN_NETWORKINTERFACE_2}
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [NETWORKINTERFACE_EXPECTED_1]}
    actual = spec_fm.get_spec_fm("00029c15-bccb-4f9a-a251-51c9d307a097", "networkInterface")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: manager_id: qemu-001,"
        " device_id: 00029c15-bccb-4f9a-a251-51c9d307a097,"
        " fm_port_id: 46376548-47e8-40f8-99de-a6f31d10f626 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-001,"
        " device_id: 00029c15-bccb-4f9a-a251-51c9d307a097,"
        " fm_port_id: 46376548-47e8-40f8-99de-a6f31d10f626 Plugin Respond.",
    )
    assert expected == actual


def test_spec_fm_memory(mocker, caplog):
    """FM Information Acquisition Test memory"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "ba123bd1-04bd-40a5-9773-6a647a3f5c01":
                return {"data": PLUGIN_RETURN_MEMORY_1}
            if target_id == "971b59b0-b4fa-4f32-b54b-9fded3034e0b":
                return {"data": PLUGIN_RETURN_MEMORY_2}
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [MEMORY_EXPECTED_1]}
    actual = spec_fm.get_spec_fm("1c440d70-ae46-42f6-b03b-6df28d0913af", "memory")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: manager_id: qemu-002,"
        " device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af,"
        " fm_port_id: ba123bd1-04bd-40a5-9773-6a647a3f5c01 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-002,"
        " device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af,"
        " fm_port_id: ba123bd1-04bd-40a5-9773-6a647a3f5c01 Plugin Respond.",
    )
    assert expected == actual


def test_spec_fm_memory_not_cxl(mocker):
    """FM Information Acquisition Test Non Functional memory by FM"""
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [{"deviceID": "1e13e51c-80fb-4751-84b3-126e33793ec4", "type": "memory"}]}
    actual = spec_fm.get_spec_fm("1e13e51c-80fb-4751-84b3-126e33793ec4", "memory")

    assert expected == actual


def test_spec_fm_gpu(mocker, caplog):
    """FM Information Acquisition Test GPU"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "af312740-e804-4d11-a9a7-3f5496a80a2f":
                return {"data": PLUGIN_RETURN_GPU_1}
            if target_id == "30c15d32-44fd-4c80-993c-8ee51b68e0c7":
                return {"data": PLUGIN_RETURN_GPU_2}
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [GPU_EXPECTED_2]}
    actual = spec_fm.get_spec_fm("7bb5e10d-48d6-4c83-af4a-986be83ba1bd", "GPU")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: manager_id: qemu-002,"
        " device_id: 7bb5e10d-48d6-4c83-af4a-986be83ba1bd,"
        " fm_port_id: 30c15d32-44fd-4c80-993c-8ee51b68e0c7 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-002,"
        " device_id: 7bb5e10d-48d6-4c83-af4a-986be83ba1bd,"
        " fm_port_id: 30c15d32-44fd-4c80-993c-8ee51b68e0c7 Plugin Respond.",
    )
    assert expected == actual


def test_spec_fm_graphic_controller(mocker):
    """FM Information Acquisition Test Non Functional graphicController by FM"""

    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [{"deviceID": "6bc966fd-4b11-458e-8264-b7b5b4297c15", "type": "graphicController"}]}
    actual = spec_fm.get_spec_fm("6bc966fd-4b11-458e-8264-b7b5b4297c15", "graphicController")

    assert expected == actual


def test_spec_fm_virtualmedia(mocker):
    """FM Information Acquisition Test Non Functional virtualmedia by FM"""
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [{"deviceID": "6bc966fd-4b11-458e-8264-b7b5b4297c15", "type": "virtualMedia"}]}
    actual = spec_fm.get_spec_fm("6bc966fd-4b11-458e-8264-b7b5b4297c15", "virtualMedia")

    assert expected == actual


def test_spec_fm_switch(mocker):
    """FM Information Acquisition Test Non Functional switch by FM"""
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [{"deviceID": "1e13e51c-80fb-4751-84b3-126e33793ec4", "type": "switch"}]}
    actual = spec_fm.get_spec_fm("1e13e51c-80fb-4751-84b3-126e33793ec4", "switch")

    assert expected == actual


def test_spec_fm_no_data(mocker):
    """FM Information Acquisition Test GPU"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "af312740-e804-4d11-a9a7-3f5496a80a2f":
                return {"data": PLUGIN_RETURN_GPU_1}
            if target_id == "30c15d32-44fd-4c80-993c-8ee51b68e0c7":
                return {"data": PLUGIN_RETURN_GPU_2}
            return None

    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch("app.core.info.info_utils.get_combination_match_device", return_value=(None, None))
    mocker.patch.object(GetSpecFMInfo, "_get_spec", return_value=[])
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [{"deviceID": "7bb5e10d-48d6-4c83-af4a-986be83ba1bd", "type": "GPU"}]}
    actual = spec_fm.get_spec_fm("7bb5e10d-48d6-4c83-af4a-986be83ba1bd", "GPU")

    assert expected == actual


def test_spec_fm_no_type(mocker, caplog):
    """FM Information Acquisition Test Device check error"""

    class MockPlugin:
        """Classes for mocks"""

    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)

    spec_fm = GetSpecFMInfo()
    with pytest.raises(exc.InternalHWControlError) as error:
        spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "InvalidType")

    assert _log_contains(caplog.record_tuples, logging.WARNING, "W00002: Unexpected DeviceType: InvalidType")
    assert isinstance(error.value, exc.InternalHWControlError)


def test_spec_fm_not_error_un_required_fields_is_none(mocker, caplog):
    """FM Information Acquisition Test No error with None"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return invalid value"""
            if target_id == "2a79d931-9c8b-4674-94ad-f6d9b00ba50c":
                test_data = PLUGIN_RETURN_REQUIRED_ONLY_1.copy()
                test_data[0].link = []
                return {"data": test_data}
            if target_id == "eee64be1-d07e-4e78-b82a-3f05ec8d10e8":
                test_data = PLUGIN_RETURN_REQUIRED_ONLY_2.copy()
                test_data[0].link = []
                return {"data": test_data}
            if target_id == "7f132823-f6f5-40bb-abc0-12c878cb180e":
                test_data = PLUGIN_RETURN_REQUIRED_ONLY_1.copy()
                test_data[0].link = []
                return {"data": test_data}
            if target_id == "6e4f020f-ebcF-4432-9820-e2c364df391b":
                test_data = PLUGIN_RETURN_REQUIRED_ONLY_2.copy()
                test_data[0].link = []
                return {"data": test_data}
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [REQUIRED_ONLY_EXPECTED_1, REQUIRED_ONLY_EXPECTED_2]}
    actual = spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-001,"
        " device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c,"
        " fm_port_id: 2a79d931-9c8b-4674-94ad-f6d9b00ba50c Plugin Respond.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-002,"
        " device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c,"
        " fm_port_id: eee64be1-d07e-4e78-b82a-3f05ec8d10e8 Plugin Respond.",
    )
    assert expected == actual


def test_spec_fm_plugin_error(mocker, caplog):
    """FM Information Acquisition Test An exception occurs at plugin"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            raise exc.ConfigurationHWControlError

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)

    spec_fm = GetSpecFMInfo()
    with pytest.raises(exc.ConfigurationHWControlError) as error:
        spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: manager_id: qemu-001,"
        " device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c,"
        " fm_port_id: 2a79d931-9c8b-4674-94ad-f6d9b00ba50c Plugin Call.",
    )
    assert not _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-001,"
        " device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c,"
        " fm_port_id: 2a79d931-9c8b-4674-94ad-f6d9b00ba50c Plugin Respond.",
    )
    assert isinstance(error.value, exc.ConfigurationHWControlError)


def test_spec_fm_plugin_unknown_exception(mocker, caplog):
    """FM Information Acquisition Test An exception occurs at plugin"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            raise AttributeError

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)

    spec_fm = GetSpecFMInfo()
    with pytest.raises(AttributeError) as error:
        spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: manager_id: qemu-001,"
        " device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c,"
        " fm_port_id: 2a79d931-9c8b-4674-94ad-f6d9b00ba50c Plugin Call.",
    )
    assert not _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-001,"
        " device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c,"
        " fm_port_id: 2a79d931-9c8b-4674-94ad-f6d9b00ba50c Plugin Respond.",
    )
    assert _log_contains(caplog.record_tuples, logging.WARNING, "W00001: Unexpected Exception: ")
    assert isinstance(error.value, AttributeError)


def test_spec_fm_get_plugin_error(mocker):
    """FM Information Acquisition Test An exception occurs at plugin"""
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", side_effect=exc.APIUsageHWControlError)
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)

    spec_fm = GetSpecFMInfo()
    with pytest.raises(exc.APIUsageHWControlError) as error:
        spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert isinstance(error.value, exc.APIUsageHWControlError)


def test_spec_fm_get_plugin_one_side_error(mocker):
    """FM Information Acquisition Test An exception occurs at plugin"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return invalid value"""
            if target_id == "2a79d931-9c8b-4674-94ad-f6d9b00ba50c":
                test_data = PLUGIN_RETURN_REQUIRED_ONLY_1.copy()
                return {"data": test_data}
            if target_id == "eee64be1-d07e-4e78-b82a-3f05ec8d10e8":
                test_data = PLUGIN_RETURN_REQUIRED_ONLY_2.copy()
                return {"data": test_data}
            if target_id == "7f132823-f6f5-40bb-abc0-12c878cb180e":
                test_data = PLUGIN_RETURN_REQUIRED_ONLY_1.copy()
                return {"data": test_data}
            if target_id == "6e4f020f-ebcF-4432-9820-e2c364df391b":
                test_data = PLUGIN_RETURN_REQUIRED_ONLY_2.copy()
                return {"data": test_data}
            return None

    def _mock_get_fm_plugin(manager_id: str):
        if manager_id == "qemu-001":
            return MockPlugin()

        raise exc.ManagerIDHWControlError

    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", side_effect=_mock_get_fm_plugin)
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

    spec_fm = GetSpecFMInfo()
    with pytest.raises(exc.ManagerIDHWControlError):
        spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")


def test_spec_fm_get_plugin_unknown_exception(mocker, caplog):
    """FM Information Acquisition Test An exception occurs at plugin"""
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", side_effect=TypeError)
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)

    spec_fm = GetSpecFMInfo()
    with pytest.raises(TypeError) as error:
        spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert _log_contains(caplog.record_tuples, logging.WARNING, "W00001: Unexpected Exception: ")
    assert isinstance(error.value, TypeError)


def test_spec_fm_unknown_exception_in_transport_fm_plugin_result_to_port_data(mocker, caplog):
    """FM Information Acquisition Test An exception occurs at plugin"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "2a79d931-9c8b-4674-94ad-f6d9b00ba50c":
                return {"data": PLUGIN_RETURN_CPU_1_1}
            if target_id == "eee64be1-d07e-4e78-b82a-3f05ec8d10e8":
                return {"data": PLUGIN_RETURN_CPU_1_2}
            if target_id == "7f132823-f6f5-40bb-abc0-12c878cb180e":
                return {"data": PLUGIN_RETURN_CPU_2_1}
            if target_id == "6e4f020f-ebcF-4432-9820-e2c364df391b":
                return {"data": PLUGIN_RETURN_CPU_2_2}
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)
    mocker.patch.object(dim, "fm_port_id_to_device_id", side_effect=IndexError)

    spec_fm = GetSpecFMInfo()
    with pytest.raises(IndexError) as error:
        spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: manager_id: qemu-001,"
        " device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c,"
        " fm_port_id: 2a79d931-9c8b-4674-94ad-f6d9b00ba50c Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-001,"
        " device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c,"
        " fm_port_id: 2a79d931-9c8b-4674-94ad-f6d9b00ba50c Plugin Respond.",
    )
    assert _log_contains(caplog.record_tuples, logging.WARNING, "W00001: Unexpected Exception: ")
    assert isinstance(error.value, IndexError)


def test_spec_fm_hw_control_error_in_transport_fm_plugin_result_to_port_data(mocker, caplog):
    """FM Information Acquisition Test Exception occurred during item check"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "2a79d931-9c8b-4674-94ad-f6d9b00ba50c":
                return {"data": PLUGIN_RETURN_CPU_1_1}
            if target_id == "eee64be1-d07e-4e78-b82a-3f05ec8d10e8":
                return {"data": PLUGIN_RETURN_CPU_1_2}
            if target_id == "7f132823-f6f5-40bb-abc0-12c878cb180e":
                return {"data": PLUGIN_RETURN_CPU_2_1}
            if target_id == "6e4f020f-ebcF-4432-9820-e2c364df391b":
                return {"data": PLUGIN_RETURN_CPU_2_2}
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)
    mocker.patch.object(dim, "fm_port_id_to_device_id", side_effect=exc.ConfigurationHWControlError)

    spec_fm = GetSpecFMInfo()
    with pytest.raises(exc.ConfigurationHWControlError) as error:
        spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: manager_id: qemu-001,"
        " device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c,"
        " fm_port_id: 2a79d931-9c8b-4674-94ad-f6d9b00ba50c Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-001,"
        " device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c,"
        " fm_port_id: 2a79d931-9c8b-4674-94ad-f6d9b00ba50c Plugin Respond.",
    )
    assert isinstance(error.value, exc.ConfigurationHWControlError)


def test_spec_fm_unknown_exception_in_get_spec(mocker):
    """FM Information Acquisition Test An exception occurs at Device information"""

    class MockPlugin:
        """Classes for mocks"""

    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", side_effect=ValueError)

    spec_fm = GetSpecFMInfo()
    with pytest.raises(ValueError, match=r"^$") as error:
        spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert isinstance(error.value, ValueError)


def test_spec_fm_unknown_exception_in_get_spec_fm(mocker):
    """FM Information Acquisition Test An exception occurs at FM information"""

    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", side_effect=PermissionError)
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    spec_fm = GetSpecFMInfo()
    with pytest.raises(PermissionError) as error:
        spec_fm.get_spec_fm("ee9e4718-df31-4bd8-b37b-455e0e0672f6", "storage")

    assert isinstance(error.value, PermissionError)


def test_spec_fm_gpu_connect_network_adapter(mocker, caplog):
    """FM Information Acquisition Test CPU"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "af312740-e804-4d11-a9a7-3f5496a80a2f":
                return {"data": PLUGIN_RETURN_GPU_3}
            if target_id == "553ec090-adde-a0e1-b7ea-d98d35197a27":
                return {"data": PLUGIN_RETURN_USP_PORT}
            if target_id == "2fdfc812-a665-ded8-0619-36a9144adf57":
                return {"data": PLUGIN_RETURN_DFA}
            if target_id == "7f132823-f6f5-40bb-abc0-12c878cb180e":
                return {"data": PLUGIN_RETURN_SFA}
            raise exc.ConfigurationHWControlError

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [GPU_EXPECTED_3]}
    actual = spec_fm.get_spec_fm("e15a736e-ea75-4f5f-8c8d-970e0705bb20", "GPU")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-002,"
        " device_id: e15a736e-ea75-4f5f-8c8d-970e0705bb20,"
        " fm_port_id: af312740-e804-4d11-a9a7-3f5496a80a2f Plugin Respond.",
    )
    assert expected == actual


def test_spec_fm_network_adapter(mocker, caplog):
    """FM Information Acquisition Test CPU"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "af312740-e804-4d11-a9a7-3f5496a80a2f":
                return {"data": PLUGIN_RETURN_GPU_3}
            if target_id == "553ec090-adde-a0e1-b7ea-d98d35197a27":
                return {"data": PLUGIN_RETURN_USP_PORT}
            if target_id == "2fdfc812-a665-ded8-0619-36a9144adf57":
                return {"data": PLUGIN_RETURN_DFA}
            if target_id == "7f132823-f6f5-40bb-abc0-12c878cb180e":
                return {"data": PLUGIN_RETURN_SFA}
            raise exc.ConfigurationHWControlError

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch("app.core.info.info_utils.get_combination_match_device", return_value=(None, None))
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [DFA_EXPECTED]}
    actual = spec_fm.get_spec_fm("3ae0c4a1-a9a6-8bb3-b2ab-9afdbebb18cc", "destinationFabricAdapter")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: fabric-001,"
        " device_id: 3ae0c4a1-a9a6-8bb3-b2ab-9afdbebb18cc,"
        " fm_port_id: 2fdfc812-a665-ded8-0619-36a9144adf57 Plugin Respond.",
    )
    assert expected == actual


def test_spec_fm_network_adapter_connect_gpu(mocker, caplog):
    """FM Information Acquisition Test CPU"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "af312740-e804-4d11-a9a7-3f5496a80a2f":
                return {"data": PLUGIN_RETURN_GPU_3}
            if target_id == "553ec090-adde-a0e1-b7ea-d98d35197a27":
                return {"data": PLUGIN_RETURN_USP_PORT}
            if target_id == "2fdfc812-a665-ded8-0619-36a9144adf57":
                return {"data": PLUGIN_RETURN_DFA}
            if target_id == "7f132823-f6f5-40bb-abc0-12c878cb180e":
                return {"data": PLUGIN_RETURN_SFA}
            raise exc.ConfigurationHWControlError

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [DFA_EXPECTED, USP_PORT_EXPECTED]}
    actual = spec_fm.get_spec_fm("3ae0c4a1-a9a6-8bb3-b2ab-9afdbebb18cc", "destinationFabricAdapter")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: fabric-001,"
        " device_id: 3ae0c4a1-a9a6-8bb3-b2ab-9afdbebb18cc,"
        " fm_port_id: 2fdfc812-a665-ded8-0619-36a9144adf57 Plugin Respond.",
    )
    assert expected == actual


def test_spec_fm_network_adapter_connect_gpu_no_manager(mocker, caplog):
    """FM Information Acquisition Test CPU"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "af312740-e804-4d11-a9a7-3f5496a80a2f":
                return {"data": PLUGIN_RETURN_GPU_3}
            if target_id == "553ec090-adde-a0e1-b7ea-d98d35197a27":
                return {"data": PLUGIN_RETURN_USP_PORT}
            if target_id == "2fdfc812-a665-ded8-0619-36a9144adf57":
                return {"data": PLUGIN_RETURN_DFA}
            if target_id == "7f132823-f6f5-40bb-abc0-12c878cb180e":
                return {"data": PLUGIN_RETURN_SFA}
            raise exc.ConfigurationHWControlError

    def mock_device_id_to_manager_id_multi_hostport(device_id) -> dict[str, list[str] | None]:
        table: dict[str, dict[str, list[str] | None]] = {
            "28c2318b-6b69-4f41-9865-166906ca2e1c": {"fm": ["qemu-001", "qemu-002"], "oob": []},  # CPU
            "ee9e4718-df31-4bd8-b37b-455e0e0672f6": {"fm": ["qemu-001"], "oob": []},  # storage
            "7aac1f83-1c10-4b98-8e7f-42119969676a": {"fm": ["qemu-001"], "oob": []},  # storage
            "00029c15-bccb-4f9a-a251-51c9d307a097": {"fm": ["qemu-001"], "oob": []},  # networkInterface
            "651ea7b7-b35e-4146-9ed4-d395d2f59068": {"fm": ["qemu-001"], "oob": []},  # networkInterface
            "de99f86c-f32e-4bb1-a3eb-026fe2154350": {"fm": ["qemu-001", "qemu-002"], "oob": []},  # CPU
            "1c440d70-ae46-42f6-b03b-6df28d0913af": {"fm": ["qemu-002"], "oob": []},  # memory
            "aa1fbae7-b8ad-4368-b5e6-156040d47d11": {"fm": ["qemu-002"], "oob": []},  # memory
            "e15a736e-ea75-4f5f-8c8d-970e0705bb20": {"fm": ["qemu-002"], "oob": []},  # GPU
            "7bb5e10d-48d6-4c83-af4a-986be83ba1bd": {"fm": ["qemu-002"], "oob": []},  # GPU
            "706faead-6d42-7916-2e05-cbb917398fab": {"fm": [], "oob": []},  # networkInterface
            "3ae0c4a1-a9a6-8bb3-b2ab-9afdbebb18cc": {"fm": ["fabric-001"], "oob": []},  # destinationFabricAdapter
            "83effa21-2fb6-a339-be34-0916564e7ce5": {"fm": ["fabric-001"], "oob": []},  # sourceFabricAdapter
            "1e13e51c-80fb-4751-84b3-126e33793ec4": {"fm": [], "oob": []},
        }

        return table[device_id]

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_fm.plugin_loader.get_fm", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_fm_port_id_multi_hostport", _mock_device_id_to_fm_port_id_multi_hostport)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [DFA_EXPECTED]}
    actual = spec_fm.get_spec_fm("3ae0c4a1-a9a6-8bb3-b2ab-9afdbebb18cc", "destinationFabricAdapter")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: fabric-001,"
        " device_id: 3ae0c4a1-a9a6-8bb3-b2ab-9afdbebb18cc,"
        " fm_port_id: 2fdfc812-a665-ded8-0619-36a9144adf57 Plugin Respond.",
    )
    assert expected == actual

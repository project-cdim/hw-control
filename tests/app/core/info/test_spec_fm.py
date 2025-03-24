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

import logging
import pytest
from app.core.info.spec_fm import GetSpecFMInfo
import app.common.basic_exceptions as exc
from app.common.utils.fm_plugin_base import FmPortData
from app.common.deviceIdManager import device_id_base as dim


PLUGIN_RETURN_CPU = [
    FmPortData(
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
CPU_EXPECTED = {
    "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c",
    "type": "CPU",
    "fmPortId": "2a79d931-9c8b-4674-94ad-f6d9b00ba50c",
    "deviceSwitchInfo": "7e31d0fb-42c5-4cd5-84c7-b37f5fa8e82c",
    "switchId": "1f2cb78b-088e-4b33-b077-d784942feb2a",
    "switchPortNumber": "1",
    "switchPortType": "USP",
    "fabricId": "NEC-fmmodel-fmsw-01",
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
    "LTSSMState": "L0",
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}
PLUGIN_RETURN_STORAGE = [
    FmPortData(
        id="4f4de979-ad99-498b-ade5-1cb404e462fa",
        switchId="1f2cb78b-088e-4b33-b077-d784942feb2a",
        switchPortNumber="2",
        switchPortType="DSP",
        fabricId="NEC-fmmodel-fmsw-01",
        link=["2a79d931-9c8b-4674-94ad-f6d9b00ba50c"],
        deviceType="PCIe",
        PCIClassCode={"base": 0, "sub": 0, "prog": 0},
        PCIeVendorId="8086",
        PCIeDeviceId="1001",
        PCIeDeviceSerialNumber="2000000000000000",
        CPUManufacturer=None,
        CPUModel=None,
        CPUSerialNumber=None,
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
STORAGE_EXPECTED = {
    "deviceID": "ee9e4718-df31-4bd8-b37b-455e0e0672f6",
    "type": "storage",
    "fmPortId": "4f4de979-ad99-498b-ade5-1cb404e462fa",
    "deviceSwitchInfo": "7e31d0fb-42c5-4cd5-84c7-b37f5fa8e82c",
    "switchId": "1f2cb78b-088e-4b33-b077-d784942feb2a",
    "switchPortNumber": "2",
    "switchPortType": "DSP",
    "fabricId": "NEC-fmmodel-fmsw-01",
    "link": [{"type": "CPU", "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c"}],
    "fmDeviceType": "PCIe",
    "PCIClassCode": {"base": 0, "sub": 0, "prog": 0},
    "PCIeVendorId": "8086",
    "PCIeDeviceId": "1001",
    "PCIeDeviceSerialNumber": "2000000000000000",
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "LTSSMState": "L0",
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}
PLUGIN_RETURN_NETWORKINTERFACE = [
    FmPortData(
        id="46376548-47e8-40f8-99de-a6f31d10f626",
        switchId="1f2cb78b-088e-4b33-b077-d784942feb2a",
        switchPortNumber="3",
        switchPortType="DSP",
        fabricId="NEC-fmmodel-fmsw-01",
        link=["2a79d931-9c8b-4674-94ad-f6d9b00ba50c"],
        deviceType="PCIe",
        PCIClassCode={"base": 0, "sub": 0, "prog": 0},
        PCIeVendorId="8086",
        PCIeDeviceId="2001",
        PCIeDeviceSerialNumber="2000000000000000",
        CPUManufacturer=None,
        CPUModel=None,
        CPUSerialNumber=None,
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
NETWORKINTERFACE_EXPECTED = {
    "deviceID": "00029c15-bccb-4f9a-a251-51c9d307a097",
    "type": "networkInterface",
    "fmPortId": "46376548-47e8-40f8-99de-a6f31d10f626",
    "deviceSwitchInfo": "7e31d0fb-42c5-4cd5-84c7-b37f5fa8e82c",
    "switchId": "1f2cb78b-088e-4b33-b077-d784942feb2a",
    "switchPortNumber": "3",
    "switchPortType": "DSP",
    "fabricId": "NEC-fmmodel-fmsw-01",
    "link": [{"type": "CPU", "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c"}],
    "fmDeviceType": "PCIe",
    "PCIClassCode": {"base": 0, "sub": 0, "prog": 0},
    "PCIeVendorId": "8086",
    "PCIeDeviceId": "2001",
    "PCIeDeviceSerialNumber": "2000000000000000",
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "LTSSMState": "L0",
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}
PLUGIN_RETURN_MEMORY = [
    FmPortData(
        id="ba123bd1-04bd-40a5-9773-6a647a3f5c01",
        switchId="1f2cb78b-088e-4b33-b077-d784942feb2a",
        switchPortNumber="4",
        switchPortType="DSP",
        fabricId="NEC-fmmodel-fmsw-01",
        link=["2a79d931-9c8b-4674-94ad-f6d9b00ba50c"],
        deviceType="CXL-Type3",
        PCIClassCode={"base": 0, "sub": 0, "prog": 0},
        PCIeVendorId="8086",
        PCIeDeviceId="2001",
        PCIeDeviceSerialNumber="2000000000000000",
        CPUManufacturer=None,
        CPUModel=None,
        CPUSerialNumber=None,
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity={"volatile": 1073741824, "persistent": 0, "total": 1073741824},
    )
]
MEMORY_EXPECTED = {
    "deviceID": "1c440d70-ae46-42f6-b03b-6df28d0913af",
    "type": "memory",
    "fmPortId": "ba123bd1-04bd-40a5-9773-6a647a3f5c01",
    "deviceSwitchInfo": "7e31d0fb-42c5-4cd5-84c7-b37f5fa8e82c",
    "switchId": "1f2cb78b-088e-4b33-b077-d784942feb2a",
    "switchPortNumber": "4",
    "switchPortType": "DSP",
    "fabricId": "NEC-fmmodel-fmsw-01",
    "link": [{"type": "CPU", "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c"}],
    "fmDeviceType": "CXL-Type3",
    "PCIClassCode": {"base": 0, "sub": 0, "prog": 0},
    "PCIeVendorId": "8086",
    "PCIeDeviceId": "2001",
    "PCIeDeviceSerialNumber": "2000000000000000",
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "LTSSMState": "L0",
    "deviceKeys": {},
    "portKeys": {},
    "capacity": {"volatile": 1073741824, "persistent": 0, "total": 1073741824},
}
PLUGIN_RETURN_GPU = [
    FmPortData(
        id="af312740-e804-4d11-a9a7-3f5496a80a2f",
        switchId="1f2cb78b-088e-4b33-b077-d784942feb2a",
        switchPortNumber="3",
        switchPortType="DSP",
        fabricId="NEC-fmmodel-fmsw-01",
        link=["2a79d931-9c8b-4674-94ad-f6d9b00ba50c"],
        deviceType="PCIe",
        PCIClassCode={"base": 0, "sub": 0, "prog": 0},
        PCIeVendorId="8086",
        PCIeDeviceId="2001",
        PCIeDeviceSerialNumber="2000000000000000",
        CPUManufacturer=None,
        CPUModel=None,
        CPUSerialNumber=None,
        LTSSMState="L0",
        deviceKeys={},
        portKeys={},
        capacity=None,
    )
]
GPU_EXPECTED = {
    "deviceID": "e15a736e-ea75-4f5f-8c8d-970e0705bb20",
    "type": "GPU",
    "fmPortId": "af312740-e804-4d11-a9a7-3f5496a80a2f",
    "deviceSwitchInfo": "7e31d0fb-42c5-4cd5-84c7-b37f5fa8e82c",
    "switchId": "1f2cb78b-088e-4b33-b077-d784942feb2a",
    "switchPortNumber": "3",
    "switchPortType": "DSP",
    "fabricId": "NEC-fmmodel-fmsw-01",
    "link": [{"type": "CPU", "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c"}],
    "fmDeviceType": "PCIe",
    "PCIClassCode": {"base": 0, "sub": 0, "prog": 0},
    "PCIeVendorId": "8086",
    "PCIeDeviceId": "2001",
    "PCIeDeviceSerialNumber": "2000000000000000",
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "LTSSMState": "L0",
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}
PLUGIN_RETURN_REQUIRED_ONLY = [
    FmPortData(
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
REQUIRED_ONLY_EXPECTED = {
    "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c",
    "type": "CPU",
    "fmPortId": "2a79d931-9c8b-4674-94ad-f6d9b00ba50c",
    "deviceSwitchInfo": None,
    "switchId": None,
    "switchPortNumber": None,
    "switchPortType": None,
    "fabricId": None,
    "fmDeviceType": None,
    "PCIClassCode": None,
    "PCIeVendorId": None,
    "PCIeDeviceId": None,
    "PCIeDeviceSerialNumber": None,
    "CPUManufacturer": None,
    "CPUModel": None,
    "CPUSerialNumber": None,
    "LTSSMState": "L0",
    "deviceKeys": {},
    "portKeys": {},
    "capacity": None,
}


def _log_contains(record, level, message) -> bool:
    return next(filter(lambda x: (x[1] == level) and (message in x[2]), record), None) is not None


def _mock_device_id_to_manager_id(device_id):
    table = {
        "28c2318b-6b69-4f41-9865-166906ca2e1c": {"fm": "qemu-001", "oob": ""},
        "ee9e4718-df31-4bd8-b37b-455e0e0672f6": {"fm": "qemu-001", "oob": ""},
        "00029c15-bccb-4f9a-a251-51c9d307a097": {"fm": "qemu-001", "oob": ""},
        "1c440d70-ae46-42f6-b03b-6df28d0913af": {"fm": "qemu-001", "oob": ""},
        "e15a736e-ea75-4f5f-8c8d-970e0705bb20": {"fm": "qemu-001", "oob": ""},
        "1e13e51c-80fb-4751-84b3-126e33793ec4": {"fm": "", "oob": ""},
    }

    if device_id in table:
        return table[device_id]
    else:
        raise exc.ConfigurationHwControlError


def _mock_device_id_to_fm_port_id(device_id):
    table = {
        "28c2318b-6b69-4f41-9865-166906ca2e1c": "2a79d931-9c8b-4674-94ad-f6d9b00ba50c",
        "ee9e4718-df31-4bd8-b37b-455e0e0672f6": "4f4de979-ad99-498b-ade5-1cb404e462fa",
        "00029c15-bccb-4f9a-a251-51c9d307a097": "46376548-47e8-40f8-99de-a6f31d10f626",
        "1c440d70-ae46-42f6-b03b-6df28d0913af": "ba123bd1-04bd-40a5-9773-6a647a3f5c01",
        "e15a736e-ea75-4f5f-8c8d-970e0705bb20": "af312740-e804-4d11-a9a7-3f5496a80a2f",
    }

    if device_id in table:
        return table[device_id]
    else:
        raise exc.ConfigurationHwControlError


def _mock_device_id_to_device_type(device_id):
    table = {
        "28c2318b-6b69-4f41-9865-166906ca2e1c": "CPU",
        "ee9e4718-df31-4bd8-b37b-455e0e0672f6": "storage",
        "00029c15-bccb-4f9a-a251-51c9d307a097": "networkInterface",
        "1c440d70-ae46-42f6-b03b-6df28d0913af": "memory",
        "e15a736e-ea75-4f5f-8c8d-970e0705bb20": "GPU",
    }

    if device_id in table:
        return table[device_id]
    else:
        raise exc.ConfigurationHwControlError


def _mock_fm_port_id_to_device_id(fm_port_id, fm_manager_id):
    table = {
        "2a79d931-9c8b-4674-94ad-f6d9b00ba50c": "28c2318b-6b69-4f41-9865-166906ca2e1c",
        "4f4de979-ad99-498b-ade5-1cb404e462fa": "ee9e4718-df31-4bd8-b37b-455e0e0672f6",
        "46376548-47e8-40f8-99de-a6f31d10f626": "00029c15-bccb-4f9a-a251-51c9d307a097",
        "ba123bd1-04bd-40a5-9773-6a647a3f5c01": "1c440d70-ae46-42f6-b03b-6df28d0913af",
        "af312740-e804-4d11-a9a7-3f5496a80a2f": "e15a736e-ea75-4f5f-8c8d-970e0705bb20",
    }

    if fm_manager_id == "qemu-001" and fm_port_id in table:
        return table[fm_port_id]
    else:
        return None


def _mock_fm_switch_id_to_device_id(fm_port_id, fm_manager_id):
    table = {"1f2cb78b-088e-4b33-b077-d784942feb2a": "7e31d0fb-42c5-4cd5-84c7-b37f5fa8e82c"}

    if fm_manager_id == "qemu-001" and fm_port_id in table:
        return table[fm_port_id]
    else:
        return None


def test_spec_fm_cpu(mocker, caplog):
    """FM Information Acquisition Test CPU"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "2a79d931-9c8b-4674-94ad-f6d9b00ba50c":
                return {"data": PLUGIN_RETURN_CPU}

    mocker.patch("app.core.info.spec_fm.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_fm_port_id", _mock_device_id_to_fm_port_id)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [CPU_EXPECTED]}
    actual = spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

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

    assert expected == actual


def test_spec_fm_cpu_link_is_none(mocker, caplog):
    """FM Information Acquisition Test CPU  link is None"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "2a79d931-9c8b-4674-94ad-f6d9b00ba50c":
                test_data = PLUGIN_RETURN_CPU.copy()
                test_data[0].link = None
                return {"data": test_data}

    mocker.patch("app.core.info.spec_fm.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_fm_port_id", _mock_device_id_to_fm_port_id)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)

    spec_fm = GetSpecFMInfo()
    expected_data = CPU_EXPECTED.copy()
    expected_data.pop("link", None)
    expected = {"data": [expected_data]}
    actual = spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

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
    assert expected == actual


def test_spec_fm_cpu_link_is_empty(mocker, caplog):
    """FM Information Acquisition Test CPU link is empty array"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "2a79d931-9c8b-4674-94ad-f6d9b00ba50c":
                test_data = PLUGIN_RETURN_CPU.copy()
                test_data[0].link = []
                return {"data": test_data}

    mocker.patch("app.core.info.spec_fm.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_fm_port_id", _mock_device_id_to_fm_port_id)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)

    spec_fm = GetSpecFMInfo()
    expected_data = CPU_EXPECTED.copy()
    expected_data.pop("link", None)
    expected = {"data": [expected_data]}
    actual = spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

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
    assert expected == actual


def test_spec_fm_storage(mocker, caplog):
    """FM Information Acquisition Test Storage"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "4f4de979-ad99-498b-ade5-1cb404e462fa":
                return {"data": PLUGIN_RETURN_STORAGE}

    mocker.patch("app.core.info.spec_fm.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_fm_port_id", _mock_device_id_to_fm_port_id)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [STORAGE_EXPECTED]}
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
                return {"data": PLUGIN_RETURN_NETWORKINTERFACE}

    mocker.patch("app.core.info.spec_fm.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_fm_port_id", _mock_device_id_to_fm_port_id)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [NETWORKINTERFACE_EXPECTED]}
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
                return {"data": PLUGIN_RETURN_MEMORY}

    mocker.patch("app.core.info.spec_fm.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_fm_port_id", _mock_device_id_to_fm_port_id)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [MEMORY_EXPECTED]}
    actual = spec_fm.get_spec_fm("1c440d70-ae46-42f6-b03b-6df28d0913af", "memory")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: manager_id: qemu-001,"
        " device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af,"
        " fm_port_id: ba123bd1-04bd-40a5-9773-6a647a3f5c01 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-001,"
        " device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af,"
        " fm_port_id: ba123bd1-04bd-40a5-9773-6a647a3f5c01 Plugin Respond.",
    )
    assert expected == actual


def test_spec_fm_memory_not_cxl(mocker):
    """FM Information Acquisition Test Non Functional memory by FM"""
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)

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
                return {"data": PLUGIN_RETURN_GPU}

    mocker.patch("app.core.info.spec_fm.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_fm_port_id", _mock_device_id_to_fm_port_id)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [GPU_EXPECTED]}
    actual = spec_fm.get_spec_fm("e15a736e-ea75-4f5f-8c8d-970e0705bb20", "GPU")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: manager_id: qemu-001,"
        " device_id: e15a736e-ea75-4f5f-8c8d-970e0705bb20,"
        " fm_port_id: af312740-e804-4d11-a9a7-3f5496a80a2f Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: manager_id: qemu-001,"
        " device_id: e15a736e-ea75-4f5f-8c8d-970e0705bb20,"
        " fm_port_id: af312740-e804-4d11-a9a7-3f5496a80a2f Plugin Respond.",
    )
    assert expected == actual


def test_spec_fm_graphic_controller(mocker):
    """FM Information Acquisition Test Non Functional graphicController by FM"""

    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [{"deviceID": "6bc966fd-4b11-458e-8264-b7b5b4297c15", "type": "graphicController"}]}
    actual = spec_fm.get_spec_fm("6bc966fd-4b11-458e-8264-b7b5b4297c15", "graphicController")

    assert expected == actual


def test_spec_fm_virtualmedia(mocker):
    """FM Information Acquisition Test Non Functional virtualmedia by FM"""
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [{"deviceID": "6bc966fd-4b11-458e-8264-b7b5b4297c15", "type": "virtualMedia"}]}
    actual = spec_fm.get_spec_fm("6bc966fd-4b11-458e-8264-b7b5b4297c15", "virtualMedia")

    assert expected == actual


def test_spec_fm_switch(mocker):
    """FM Information Acquisition Test Non Functional switch by FM"""
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [{"deviceID": "1e13e51c-80fb-4751-84b3-126e33793ec4", "type": "switch"}]}
    actual = spec_fm.get_spec_fm("1e13e51c-80fb-4751-84b3-126e33793ec4", "switch")

    assert expected == actual


def test_spec_fm_no_type(mocker, caplog):
    """FM Information Acquisition Test Device check error"""

    class MockPlugin:
        """Classes for mocks"""

    mocker.patch("app.core.info.spec_fm.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)

    spec_fm = GetSpecFMInfo()
    with pytest.raises(exc.InternalHwControlError) as error:
        spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "InvalidType")

    assert _log_contains(caplog.record_tuples, logging.WARN, "W00002: Unexpected DeviceType: InvalidType")
    assert error.type == exc.InternalHwControlError


def test_spec_fm_not_error_unrequired_fields_is_none(mocker, caplog):
    """FM Information Acquisition Test No error with None"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return invalid value"""
            if target_id == "2a79d931-9c8b-4674-94ad-f6d9b00ba50c":
                test_data = PLUGIN_RETURN_REQUIRED_ONLY.copy()
                test_data[0].id = target_id
                return {"data": test_data}

    mocker.patch("app.core.info.spec_fm.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_fm_port_id", _mock_device_id_to_fm_port_id)
    mocker.patch.object(dim, "fm_port_id_to_device_id", _mock_fm_port_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "fm_switch_id_to_device_id", _mock_fm_switch_id_to_device_id)

    spec_fm = GetSpecFMInfo()
    expected = {"data": [REQUIRED_ONLY_EXPECTED]}
    actual = spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

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
    assert expected == actual


def test_spec_fm_plugin_error(mocker, caplog):
    """FM Information Acquisition Test An exception occurs at plugin"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            raise exc.ConfigurationHwControlError

    mocker.patch("app.core.info.spec_fm.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_fm_port_id", _mock_device_id_to_fm_port_id)

    spec_fm = GetSpecFMInfo()
    with pytest.raises(exc.ConfigurationHwControlError) as error:
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
    assert error.type == exc.ConfigurationHwControlError


def test_spec_fm_plugin_unknown_exception(mocker, caplog):
    """FM Information Acquisition Test An exception occurs at plugin"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            raise AttributeError

    mocker.patch("app.core.info.spec_fm.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_fm_port_id", _mock_device_id_to_fm_port_id)

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
    assert _log_contains(caplog.record_tuples, logging.WARN, "W00001: Unexpected Exception: ")
    assert error.type == AttributeError


def test_spec_fm_get_plugin_error(mocker):
    """FM Information Acquisition Test An exception occurs at plugin"""
    mocker.patch("app.core.info.spec_fm.get_plugin", side_effect=exc.ApiUsageHwControlError)
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)

    spec_fm = GetSpecFMInfo()
    with pytest.raises(exc.ApiUsageHwControlError) as error:
        spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert error.type == exc.ApiUsageHwControlError


def test_spec_fm_get_plugin_unknown_exception(mocker, caplog):
    """FM Information Acquisition Test An exception occurs at plugin"""
    mocker.patch("app.core.info.spec_fm.get_plugin", side_effect=TypeError)
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)

    spec_fm = GetSpecFMInfo()
    with pytest.raises(TypeError) as error:
        spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert _log_contains(caplog.record_tuples, logging.WARN, "W00001: Unexpected Exception: ")
    assert error.type == TypeError


def test_spec_fm_unknown_exception_in_transport_fm_plugin_result_to_port_data(mocker, caplog):
    """FM Information Acquisition Test An exception occurs at plugin"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "2a79d931-9c8b-4674-94ad-f6d9b00ba50c":
                return {"data": PLUGIN_RETURN_CPU}

    mocker.patch("app.core.info.spec_fm.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_fm_port_id", _mock_device_id_to_fm_port_id)
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
    assert _log_contains(caplog.record_tuples, logging.WARN, "W00001: Unexpected Exception: ")
    assert error.type == IndexError


def test_spec_fm_hw_control_error_in_transport_fm_plugin_result_to_port_data(mocker, caplog):
    """FM Information Acquisition Test Exception occurred during item check"""

    class MockPlugin:
        """Classes for mocks"""

        def get_port_info(self, target_id):
            """return mock value"""
            if target_id == "2a79d931-9c8b-4674-94ad-f6d9b00ba50c":
                return {"data": PLUGIN_RETURN_CPU}

    mocker.patch("app.core.info.spec_fm.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_fm_port_id", _mock_device_id_to_fm_port_id)
    mocker.patch.object(dim, "fm_port_id_to_device_id", side_effect=exc.ConfigurationHwControlError)

    spec_fm = GetSpecFMInfo()
    with pytest.raises(exc.ConfigurationHwControlError) as error:
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
    assert error.type == exc.ConfigurationHwControlError


def test_spec_fm_unknown_exception_in_get_spec(mocker):
    """FM Information Acquisition Test An exception occurs at Device information"""

    class MockPlugin:
        """Classes for mocks"""

    mocker.patch("app.core.info.spec_fm.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_fm_port_id", side_effect=ValueError)

    spec_fm = GetSpecFMInfo()
    with pytest.raises(ValueError) as error:
        spec_fm.get_spec_fm("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert error.type == ValueError


def test_spec_fm_unknown_exception_in_get_spec_fm(mocker):
    """FM Information Acquisition Test An exception occurs at FM information"""
    mocker.patch.object(GetSpecFMInfo, "_import_plugin", side_effect=PermissionError)
    spec_fm = GetSpecFMInfo()
    with pytest.raises(PermissionError) as error:
        spec_fm.get_spec_fm("ee9e4718-df31-4bd8-b37b-455e0e0672f6", "storage")

    assert error.type == PermissionError

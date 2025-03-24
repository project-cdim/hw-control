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
import app.common.basic_exceptions as exc
from app.core.info.spec_oob import GetSpecOOBInfo
from app.common.deviceIdManager import device_id_base as dim

MOCK_PLUGIN_CPU_RESPONSE = {
    "devices": [
        {
            "deviceID": "0001",
            "type": "CPU",
            "schema": {"PowerState": "on", "PowerCapability": "True"},
            "link": [{"type": "memory", "deviceID": "1001"}],
            "time": "2000-01-01T01:00:00Z",
        }
    ]
}
MOCK_PLUGIN_CPU_METRIC = {
    "devices": [
        {
            "deviceID": "0001",
            "type": "CPU",
            "schema": {"PowerState": "on", "PowerCapability": "True"},
            "link": [{"type": "memory", "deviceID": "1001"}],
            "time": "2000-01-01T01:00:00Z",
        }
    ]
}
EXPECTED_CPU_RESPONSE = {
    "devices": [
        {
            "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c",
            "type": "CPU",
            "schema": {"PowerState": "on", "PowerCapability": "True"},
            "link": [{"type": "memory", "deviceID": "1c440d70-ae46-42f6-b03b-6df28d0913af"}],
            "time": "2000-01-01T01:00:00Z",
        }
    ]
}
MOCK_PLUGIN_MEMORY_RESPONSE = {
    "devices": [
        {
            "deviceID": "1001",
            "type": "memory",
            "schema": {"PowerState": "on", "PowerCapability": "True"},
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "powerState": "ON",
            "powerCapability": "true",
        }
    ]
}
MOCK_PLUGIN_MEMORY_METRIC = {
    "devices": [
        {
            "deviceID": "1001",
            "type": "memory",
            "schema": {"PowerState": "on", "PowerCapability": "True"},
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "powerState": "ON",
            "powerCapability": "true",
        }
    ]
}
EXPECTED_MEMORY_RESPONSE = {
    "devices": [
        {
            "deviceID": "1c440d70-ae46-42f6-b03b-6df28d0913af",
            "type": "memory",
            "schema": {"PowerState": "on", "PowerCapability": "True"},
            "link": [{"type": "CPU", "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c"}],
            "powerState": "ON",
            "powerCapability": "true",
        }
    ]
}
MOCK_PLUGIN_STORAGE_RESPONSE = {
    "devices": [{"deviceID": "2001", "type": "storage", "powerState": "ON", "powerCapability": "true"}]
}
MOCK_PLUGIN_STORAGE_METRIC = {
    "devices": [{"deviceID": "2001", "type": "storage", "powerState": "ON", "powerCapability": "true"}]
}
EXPECTED_STORAGE_RESPONSE = {
    "devices": [
        {
            "deviceID": "ee9e4718-df31-4bd8-b37b-455e0e0672f6",
            "type": "storage",
            "powerState": "ON",
            "powerCapability": "true",
        }
    ]
}
MOCK_PLUGIN_NIC_RESPONSE = {
    "devices": [{"deviceID": "3001", "type": "networkInterface", "powerState": "ON", "powerCapability": "false"}]
}
MOCK_PLUGIN_NIC_METRIC = {
    "devices": [{"deviceID": "3001", "type": "networkInterface", "powerState": "ON", "powerCapability": "false"}]
}
EXPECTED_NIC_RESPONSE = {
    "devices": [
        {
            "deviceID": "00029c15-bccb-4f9a-a251-51c9d307a097",
            "type": "networkInterface",
            "powerState": "ON",
            "powerCapability": "false",
        }
    ]
}
MOCK_PLUGIN_GPU_RESPONSE = {
    "devices": [{"deviceID": "4001", "type": "GPU", "powerState": "ON", "powerCapability": "false"}]
}
MOCK_PLUGIN_GPU_METRIC = {
    "devices": [{"deviceID": "4001", "type": "GPU", "powerState": "ON", "powerCapability": "false"}]
}
EXPECTED_GPU_RESPONSE = {
    "devices": [
        {
            "deviceID": "11056940-fd5c-4f37-87e2-9e6c18b65828",
            "type": "GPU",
            "powerState": "ON",
            "powerCapability": "false",
        }
    ]
}
MOCK_PLUGIN_GRAPHIC_CONTROLLER_RESPONSE = {
    "devices": [{"deviceID": "5001", "type": "graphicController", "powerState": "ON", "powerCapability": "false"}]
}
MOCK_PLUGIN_GRAPHIC_CONTROLLER_METRIC = {
    "devices": [{"deviceID": "5001", "type": "graphicController", "powerState": "ON", "powerCapability": "false"}]
}
EXPECTED_GRAPHIC_CONTROLLER_RESPONSE = {
    "devices": [
        {
            "deviceID": "c1599cc2-d225-429a-8dd9-0862f1e29bcb",
            "type": "graphicController",
            "powerState": "ON",
            "powerCapability": "false",
        }
    ]
}
MOCK_PLUGIN_MISSING_DEVICE_ID = {
    "devices": [{"type": "graphicController", "powerState": "ON", "powerCapability": "false"}]
}
EXPECTED_MISSING_DEVICE_ID = {
    "devices": [{"type": "graphicController", "powerState": "ON", "powerCapability": "false"}]
}
EXPECTED_NODATA_RESPONSE = {}


def _log_contains(record, level, message) -> bool:
    return next(filter(lambda x: (x[1] == level) and (message in x[2]), record), None) is not None


def _mock_device_id_to_manager_id(device_id):
    table = {
        "28c2318b-6b69-4f41-9865-166906ca2e1c": {"fm": None, "oob": "BMC-1"},
        "ee9e4718-df31-4bd8-b37b-455e0e0672f6": {"fm": None, "oob": "BMC-1"},
        "00029c15-bccb-4f9a-a251-51c9d307a097": {"fm": None, "oob": "BMC-1"},
        "1c440d70-ae46-42f6-b03b-6df28d0913af": {"fm": None, "oob": "BMC-1"},
        "11056940-fd5c-4f37-87e2-9e6c18b65828": {"fm": None, "oob": "BMC-1"},
        "c1599cc2-d225-429a-8dd9-0862f1e29bcb": {"fm": None, "oob": "BMC-1"},
        "1e13e51c-80fb-4751-84b3-126e33793ec4": {"fm": None, "oob": None},
    }

    if device_id in table:
        return table[device_id]

    raise exc.ConfigurationHwControlError


def _mock_device_id_to_oob_device_id(device_id):
    table = {
        "28c2318b-6b69-4f41-9865-166906ca2e1c": "0001",
        "1c440d70-ae46-42f6-b03b-6df28d0913af": "1001",
        "ee9e4718-df31-4bd8-b37b-455e0e0672f6": "2001",
        "00029c15-bccb-4f9a-a251-51c9d307a097": "3001",
        "11056940-fd5c-4f37-87e2-9e6c18b65828": "4001",
        "c1599cc2-d225-429a-8dd9-0862f1e29bcb": "5001",
    }

    if device_id in table:
        return table[device_id]

    raise exc.ConfigurationHwControlError


def _mock_device_id_to_device_type(device_id):
    table = {
        "28c2318b-6b69-4f41-9865-166906ca2e1c": "CPU",
        "1c440d70-ae46-42f6-b03b-6df28d0913af": "memory",
        "ee9e4718-df31-4bd8-b37b-455e0e0672f6": "storage",
        "00029c15-bccb-4f9a-a251-51c9d307a097": "networkInterface",
        "11056940-fd5c-4f37-87e2-9e6c18b65828": "GPU",
        "c1599cc2-d225-429a-8dd9-0862f1e29bcb": "graphicController",
    }

    if device_id in table:
        return table[device_id]

    raise exc.ConfigurationHwControlError


def _mock_oob_device_id_to_device_id(oob_device_id, oob_manager_id):
    table = {
        "0001": "28c2318b-6b69-4f41-9865-166906ca2e1c",
        "1001": "1c440d70-ae46-42f6-b03b-6df28d0913af",
        "2001": "ee9e4718-df31-4bd8-b37b-455e0e0672f6",
        "3001": "00029c15-bccb-4f9a-a251-51c9d307a097",
        "4001": "11056940-fd5c-4f37-87e2-9e6c18b65828",
        "5001": "c1599cc2-d225-429a-8dd9-0862f1e29bcb",
    }

    if oob_manager_id == "BMC-1" and oob_device_id in table:
        return table[oob_device_id]

    return None


def test_get_spec_oob_cpu(mocker, caplog):
    """OOB Information Acquisition Test CPU"""

    class MockPlugin:
        """Classes for mocks"""

        param_key_value: list = []
        pardic_key_value: dict = {}
        pardic_key_value["oob_device_id"] = "0001"
        pardic_key_value["device_type"] = "CPU"
        param_key_value.append(pardic_key_value)

        def get_spec_info(self, key_values):
            """return mock value"""
            if key_values == MockPlugin.param_key_value:
                return MOCK_PLUGIN_CPU_RESPONSE

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_spec_oob("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c"
        " oob_device_id: 0001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c"
        " oob_device_id: 0001 Plugin Respond.",
    )

    assert actual == EXPECTED_CPU_RESPONSE


def test_get_spec_oob_memory(mocker, caplog):
    """OOB Information Acquisition Test memory"""

    class MockPlugin:
        """Classes for mocks"""

        param_key_value: list = []
        pardic_key_value: dict = {}
        pardic_key_value["oob_device_id"] = "1001"
        pardic_key_value["device_type"] = "memory"
        param_key_value.append(pardic_key_value)

        def get_spec_info(self, key_values):
            """return mock value"""
            if key_values == MockPlugin.param_key_value:
                return MOCK_PLUGIN_MEMORY_RESPONSE

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_spec_oob("1c440d70-ae46-42f6-b03b-6df28d0913af", "memory")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Respond.",
    )
    assert actual == EXPECTED_MEMORY_RESPONSE


def test_get_spec_oob_storage(mocker, caplog):
    """OOB Information Acquisition Test Storage"""

    class MockPlugin:
        """Classes for mocks"""

        param_key_value: list = []
        pardic_key_value: dict = {}
        pardic_key_value["oob_device_id"] = "2001"
        pardic_key_value["device_type"] = "storage"
        param_key_value.append(pardic_key_value)

        def get_spec_info(self, key_values):
            """return mock value"""
            if key_values == MockPlugin.param_key_value:
                return MOCK_PLUGIN_STORAGE_RESPONSE

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_spec_oob("ee9e4718-df31-4bd8-b37b-455e0e0672f6", "storage")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: ee9e4718-df31-4bd8-b37b-455e0e0672f6"
        " oob_device_id: 2001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: ee9e4718-df31-4bd8-b37b-455e0e0672f6"
        " oob_device_id: 2001 Plugin Respond.",
    )
    assert actual == EXPECTED_STORAGE_RESPONSE


def test_get_spec_oob_nic(mocker, caplog):
    """OOB Information Acquisition Test Nic"""

    class MockPlugin:
        """Classes for mocks"""

        param_key_value: list = []
        pardic_key_value: dict = {}
        pardic_key_value["oob_device_id"] = "3001"
        pardic_key_value["device_type"] = "networkInterface"
        param_key_value.append(pardic_key_value)

        def get_spec_info(self, key_values):
            """return mock value"""
            if key_values == MockPlugin.param_key_value:
                return MOCK_PLUGIN_NIC_RESPONSE

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_spec_oob("00029c15-bccb-4f9a-a251-51c9d307a097", "networkInterface")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: 00029c15-bccb-4f9a-a251-51c9d307a097"
        " oob_device_id: 3001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: 00029c15-bccb-4f9a-a251-51c9d307a097"
        " oob_device_id: 3001 Plugin Respond.",
    )
    assert actual == EXPECTED_NIC_RESPONSE


def test_get_spec_oob_gpu(mocker, caplog):
    """OOB Information Acquisition Test GPU"""

    class MockPlugin:
        """Classes for mocks"""

        param_key_value: list = []
        pardic_key_value: dict = {}
        pardic_key_value["oob_device_id"] = "4001"
        pardic_key_value["device_type"] = "GPU"
        param_key_value.append(pardic_key_value)

        def get_spec_info(self, key_values):
            """return mock value"""
            if key_values == MockPlugin.param_key_value:
                return MOCK_PLUGIN_GPU_RESPONSE

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_spec_oob("11056940-fd5c-4f37-87e2-9e6c18b65828", "GPU")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: 11056940-fd5c-4f37-87e2-9e6c18b65828"
        " oob_device_id: 4001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: 11056940-fd5c-4f37-87e2-9e6c18b65828"
        " oob_device_id: 4001 Plugin Respond.",
    )
    assert actual == EXPECTED_GPU_RESPONSE


def test_get_spec_oob_graphic_controller(mocker, caplog):
    """OOB Information Acquisition Test Non Functional graphicController by OOB"""

    class MockPlugin:
        """Classes for mocks"""

        param_key_value: list = []
        pardic_key_value: dict = {}
        pardic_key_value["oob_device_id"] = "5001"
        pardic_key_value["device_type"] = "graphicController"
        param_key_value.append(pardic_key_value)

        def get_spec_info(self, key_values):
            """return mock value"""
            if key_values == MockPlugin.param_key_value:
                return MOCK_PLUGIN_GRAPHIC_CONTROLLER_RESPONSE

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_spec_oob("c1599cc2-d225-429a-8dd9-0862f1e29bcb", "graphicController")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: c1599cc2-d225-429a-8dd9-0862f1e29bcb"
        " oob_device_id: 5001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: c1599cc2-d225-429a-8dd9-0862f1e29bcb"
        " oob_device_id: 5001 Plugin Respond.",
    )
    assert actual == EXPECTED_GRAPHIC_CONTROLLER_RESPONSE


def test_get_spec_oob_no_oob_manager(mocker):
    """OOB Information Acquisition Test Information on devices not subject to collection"""
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    expected = {"devices": [{"deviceID": "1e13e51c-80fb-4751-84b3-126e33793ec4", "type": "GPU"}]}

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_spec_oob("1e13e51c-80fb-4751-84b3-126e33793ec4", "GPU")

    assert expected == actual


def test_get_spec_oob_empty_device_type(caplog):
    """OOB Information Acquisition Test Device check error"""
    spec_oob_info = GetSpecOOBInfo()

    with pytest.raises(exc.InternalHwControlError) as error:
        spec_oob_info.get_spec_oob("28c2318b-6b69-4f41-9865-166906ca2e1c", "")

    assert _log_contains(caplog.record_tuples, logging.WARN, "W00002: Unexpected DeviceType: ")
    assert error.type == exc.InternalHwControlError


def test_get_spec_oob_get_plugin_error(mocker):
    """OOB Information Acquisition Test An exception occurs at plugin"""
    mocker.patch("app.core.info.spec_oob.get_plugin", side_effect=exc.ApiUsageHwControlError)
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)

    spec_oob_info = GetSpecOOBInfo()
    with pytest.raises(exc.ApiUsageHwControlError) as error:
        spec_oob_info.get_spec_oob("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert error.type == exc.ApiUsageHwControlError


def test_get_spec_oob_get_plugin_unknown_exception(mocker, caplog):
    """OOB Information Acquisition Test An exception occurs at plugin"""
    mocker.patch("app.core.info.spec_oob.get_plugin", side_effect=AttributeError)
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)

    spec_oob_info = GetSpecOOBInfo()
    with pytest.raises(AttributeError) as error:
        spec_oob_info.get_spec_oob("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert _log_contains(caplog.record_tuples, logging.WARN, "W00001: Unexpected Exception: ")
    assert error.type == AttributeError


def test_get_spec_oob_no_device_data(mocker, caplog):
    """OOB Information Acquisition Test Device check error"""

    class MockPlugin:
        """Classes for mocks"""

        def get_spec_info(self, key_values):
            """return mock value"""
            return key_values

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)

    spec_oob_info = GetSpecOOBInfo()

    with pytest.raises(exc.InternalHwControlError) as error:
        spec_oob_info.get_spec_oob("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c"
        " oob_device_id: 0001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c"
        " oob_device_id: 0001 Plugin Respond.",
    )
    assert _log_contains(caplog.record_tuples, logging.WARN, "W00005: Plugin Response Unexpected None:")
    assert error.type == exc.InternalHwControlError


def test_get_spec_oob_no_device_key(mocker, caplog):
    """OOB Information Acquisition Test Device check error"""

    class MockPlugin:
        """Classes for mocks"""

        def get_spec_info(self, key_values):
            """return mock value"""
            return {"unexpectedDict": key_values}

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)

    spec_oob_info = GetSpecOOBInfo()

    with pytest.raises(exc.InternalHwControlError) as error:
        spec_oob_info.get_spec_oob("1c440d70-ae46-42f6-b03b-6df28d0913af", "memory")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Respond.",
    )
    assert _log_contains(caplog.record_tuples, logging.WARN, "W00005: Plugin Response Unexpected None:")
    assert error.type == exc.InternalHwControlError


def test_get_spec_oob_plugin_error(mocker, caplog):
    """OOB Information Acquisition Test An exception occurs at plugin"""

    class MockPlugin:
        """Classes for mocks"""

        def get_spec_info(self, key_values):
            """return mock value"""
            raise exc.ConfigurationHwControlError

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)

    spec_oob_info = GetSpecOOBInfo()

    with pytest.raises(exc.ConfigurationHwControlError) as error:
        spec_oob_info.get_spec_oob("1c440d70-ae46-42f6-b03b-6df28d0913af", "memory")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Call.",
    )
    assert not _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Respond.",
    )

    assert error.type == exc.ConfigurationHwControlError


def test_get_spec_oob_plugin_unknown_exception(mocker, caplog):
    """OOB Information Acquisition Test An exception occurs at plugin"""

    class MockPlugin:
        """Classes for mocks"""

        def get_spec_info(self, key_values):
            """return mock value"""
            raise TypeError

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)

    spec_oob_info = GetSpecOOBInfo()

    with pytest.raises(TypeError) as error:
        spec_oob_info.get_spec_oob("1c440d70-ae46-42f6-b03b-6df28d0913af", "memory")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Call.",
    )
    assert not _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Respond.",
    )
    assert _log_contains(caplog.record_tuples, logging.WARN, "W00001: Unexpected Exception: ")
    assert error.type == TypeError


def test_get_metric_oob_cpu(mocker, caplog):
    """OOB Metric Information Acquisition Test CPU"""

    class MockPlugin:
        """Classes for mocks"""

        param_key_value: list = []
        pardic_key_value: dict = {}
        pardic_key_value["oob_device_id"] = "0001"
        pardic_key_value["device_type"] = "CPU"
        param_key_value.append(pardic_key_value)

        def get_metric_info(self, key_values):
            """return mock value"""
            if key_values == MockPlugin.param_key_value:
                return MOCK_PLUGIN_CPU_METRIC

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_metric_oob("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c"
        " oob_device_id: 0001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: 28c2318b-6b69-4f41-9865-166906ca2e1c"
        " oob_device_id: 0001 Plugin Respond.",
    )
    assert actual == EXPECTED_CPU_RESPONSE


def test_get_metric_oob_memory(mocker, caplog):
    """OOB Metric Information Acquisition Test memory"""

    class MockPlugin:
        """Classes for mocks"""

        param_key_value: list = []
        pardic_key_value: dict = {}
        pardic_key_value["oob_device_id"] = "1001"
        pardic_key_value["device_type"] = "memory"
        param_key_value.append(pardic_key_value)

        def get_metric_info(self, key_values):
            """return mock value"""
            if key_values == MockPlugin.param_key_value:
                return MOCK_PLUGIN_MEMORY_METRIC

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_metric_oob("1c440d70-ae46-42f6-b03b-6df28d0913af", "memory")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Respond.",
    )
    assert actual == EXPECTED_MEMORY_RESPONSE


def test_get_metric_oob_storage(mocker, caplog):
    """OOB Metric Information Acquisition Test Storage"""

    class MockPlugin:
        """Classes for mocks"""

        param_key_value: list = []
        pardic_key_value: dict = {}
        pardic_key_value["oob_device_id"] = "2001"
        pardic_key_value["device_type"] = "storage"
        param_key_value.append(pardic_key_value)

        def get_metric_info(self, key_values):
            """return mock value"""
            if key_values == MockPlugin.param_key_value:
                return MOCK_PLUGIN_STORAGE_METRIC

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_metric_oob("ee9e4718-df31-4bd8-b37b-455e0e0672f6", "storage")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: ee9e4718-df31-4bd8-b37b-455e0e0672f6"
        " oob_device_id: 2001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: ee9e4718-df31-4bd8-b37b-455e0e0672f6"
        " oob_device_id: 2001 Plugin Respond.",
    )
    assert actual == EXPECTED_STORAGE_RESPONSE


def test_get_metric_oob_nic(mocker, caplog):
    """OOB Metric Information Acquisition Test NIC"""

    class MockPlugin:
        """Classes for mocks"""

        param_key_value: list = []
        pardic_key_value: dict = {}
        pardic_key_value["oob_device_id"] = "3001"
        pardic_key_value["device_type"] = "networkInterface"
        param_key_value.append(pardic_key_value)

        def get_metric_info(self, key_values):
            """return mock value"""
            if key_values == MockPlugin.param_key_value:
                return MOCK_PLUGIN_NIC_METRIC

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_metric_oob("00029c15-bccb-4f9a-a251-51c9d307a097", "networkInterface")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: 00029c15-bccb-4f9a-a251-51c9d307a097"
        " oob_device_id: 3001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: 00029c15-bccb-4f9a-a251-51c9d307a097"
        " oob_device_id: 3001 Plugin Respond.",
    )
    assert actual == EXPECTED_NIC_RESPONSE


def test_get_metric_oob_gpu(mocker, caplog):
    """OOB Metric Information Acquisition Test GPU"""

    class MockPlugin:
        """Classes for mocks"""

        param_key_value: list = []
        pardic_key_value: dict = {}
        pardic_key_value["oob_device_id"] = "4001"
        pardic_key_value["device_type"] = "GPU"
        param_key_value.append(pardic_key_value)

        def get_metric_info(self, key_values):
            """return mock value"""
            if key_values == MockPlugin.param_key_value:
                return MOCK_PLUGIN_GPU_METRIC

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_metric_oob("11056940-fd5c-4f37-87e2-9e6c18b65828", "GPU")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: 11056940-fd5c-4f37-87e2-9e6c18b65828"
        " oob_device_id: 4001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: 11056940-fd5c-4f37-87e2-9e6c18b65828"
        " oob_device_id: 4001 Plugin Respond.",
    )
    assert actual == EXPECTED_GPU_RESPONSE


def test_get_metric_oob_graphic_controller(mocker, caplog):
    """OOB Metric Information Acquisition Test graphicController"""

    class MockPlugin:
        """Classes for mocks"""

        param_key_value: list = []
        pardic_key_value: dict = {}
        pardic_key_value["oob_device_id"] = "5001"
        pardic_key_value["device_type"] = "graphicController"
        param_key_value.append(pardic_key_value)

        def get_metric_info(self, key_values):
            """return mock value"""
            if key_values == MockPlugin.param_key_value:
                return MOCK_PLUGIN_GRAPHIC_CONTROLLER_METRIC

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_metric_oob("c1599cc2-d225-429a-8dd9-0862f1e29bcb", "graphicController")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: c1599cc2-d225-429a-8dd9-0862f1e29bcb"
        " oob_device_id: 5001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: c1599cc2-d225-429a-8dd9-0862f1e29bcb"
        " oob_device_id: 5001 Plugin Respond.",
    )
    assert actual == EXPECTED_GRAPHIC_CONTROLLER_RESPONSE


def test_get_metric_oob_no_oob_manager(mocker):
    """OOB Metric Information Acquisition Test Information on devices not subject to collection"""
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    expected = {"devices": [{"deviceID": "1e13e51c-80fb-4751-84b3-126e33793ec4", "type": "GPU"}]}

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_metric_oob("1e13e51c-80fb-4751-84b3-126e33793ec4", "GPU")

    assert expected == actual


def test_get_metric_oob_empty_device_type(caplog):
    """OOB Metric Information Acquisition Test Device check error"""
    spec_oob_info = GetSpecOOBInfo()

    with pytest.raises(exc.InternalHwControlError) as error:
        spec_oob_info.get_metric_oob("1c440d70-ae46-42f6-b03b-6df28d0913af", "")

    assert not _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Call.",
    )
    assert not _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Respond.",
    )
    assert _log_contains(caplog.record_tuples, logging.WARN, "W00002: Unexpected DeviceType: ")
    assert error.type == exc.InternalHwControlError


def test_get_metric_oob_get_plugin_error(mocker):
    """OOB Metric Information Acquisition Test An exception occurs at plugin"""
    mocker.patch("app.core.info.spec_oob.get_plugin", side_effect=exc.ApiUsageHwControlError)
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)

    spec_oob_info = GetSpecOOBInfo()
    with pytest.raises(exc.ApiUsageHwControlError) as error:
        spec_oob_info.get_metric_oob("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert error.type == exc.ApiUsageHwControlError


def test_get_metric_oob_get_plugin_unknown_exception(mocker, caplog):
    """OOB Metric Information Acquisition Test An exception occurs at plugin"""
    mocker.patch("app.core.info.spec_oob.get_plugin", side_effect=FileNotFoundError)
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)

    spec_oob_info = GetSpecOOBInfo()
    with pytest.raises(FileNotFoundError) as error:
        spec_oob_info.get_metric_oob("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert _log_contains(caplog.record_tuples, logging.WARN, "W00001: Unexpected Exception: ")
    assert error.type == FileNotFoundError


def test_get_metric_oob_no_device_data(mocker, caplog):
    """OOB Metric Information Acquisition Test Device check error"""

    class MockPlugin:
        """Classes for mocks"""

        def get_metric_info(self, key_values):
            """return mock value"""
            return key_values

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)

    spec_oob_info = GetSpecOOBInfo()

    with pytest.raises(exc.InternalHwControlError) as error:
        spec_oob_info.get_metric_oob("1c440d70-ae46-42f6-b03b-6df28d0913af", "memory")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Respond.",
    )
    assert _log_contains(caplog.record_tuples, logging.WARN, "W00005: Plugin Response Unexpected None:")
    assert error.type == exc.InternalHwControlError


def test_get_metric_oob_no_device_key(mocker, caplog):
    """OOB Metric Information Acquisition Test Device check error"""

    class MockPlugin:
        """Classes for mocks"""

        def get_metric_info(self, key_values):
            """return mock value"""
            return {"unexpectedDict": key_values}

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)

    spec_oob_info = GetSpecOOBInfo()

    with pytest.raises(exc.InternalHwControlError) as error:
        spec_oob_info.get_metric_oob("1c440d70-ae46-42f6-b03b-6df28d0913af", "memory")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Respond.",
    )
    assert _log_contains(caplog.record_tuples, logging.WARN, "W00005: Plugin Response Unexpected None:")
    assert error.type == exc.InternalHwControlError


def test_get_metric_oob_plugin_error(mocker, caplog):
    """OOB Metric Information Acquisition Test An exception occurs at plugin"""

    class MockPlugin:
        """Classes for mocks"""

        def get_metric_info(self, key_values):
            """return mock value"""
            raise exc.ConfigurationHwControlError

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)

    spec_oob_info = GetSpecOOBInfo()

    with pytest.raises(exc.ConfigurationHwControlError) as error:
        spec_oob_info.get_metric_oob("1c440d70-ae46-42f6-b03b-6df28d0913af", "memory")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Call.",
    )
    assert not _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Respond.",
    )

    assert error.type == exc.ConfigurationHwControlError


def test_get_metric_oob_plugin_unknown_exception(mocker, caplog):
    """OOB Metric Information Acquisition Test An exception occurs at plugin"""

    class MockPlugin:
        """Classes for mocks"""

        def get_metric_info(self, key_values):
            """return mock value"""
            raise IndexError

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)

    spec_oob_info = GetSpecOOBInfo()

    with pytest.raises(IndexError) as error:
        spec_oob_info.get_metric_oob("1c440d70-ae46-42f6-b03b-6df28d0913af", "memory")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Call.",
    )
    assert not _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: 1c440d70-ae46-42f6-b03b-6df28d0913af"
        " oob_device_id: 1001 Plugin Respond.",
    )
    assert _log_contains(caplog.record_tuples, logging.WARN, "W00001: Unexpected Exception: ")
    assert error.type == IndexError


def test_get_oob_id_convert_error(mocker, caplog):
    """OOB Information Acquisition Test Device conversion error"""

    class MockPlugin:
        """Classes for mocks"""

        param_key_value: list = []
        pardic_key_value: dict = {}
        pardic_key_value["oob_device_id"] = "5001"
        pardic_key_value["device_type"] = "graphicController"
        param_key_value.append(pardic_key_value)

        def get_metric_info(self, key_values):
            """return mock value"""
            if key_values == MockPlugin.param_key_value:
                return MOCK_PLUGIN_GRAPHIC_CONTROLLER_METRIC

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", side_effect=exc.DeviceIdFileNotFoundHwControlError)

    spec_oob_info = GetSpecOOBInfo()
    with pytest.raises(exc.DeviceIdFileNotFoundHwControlError) as error:
        spec_oob_info.get_metric_oob("c1599cc2-d225-429a-8dd9-0862f1e29bcb", "graphicController")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: c1599cc2-d225-429a-8dd9-0862f1e29bcb"
        " oob_device_id: 5001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: c1599cc2-d225-429a-8dd9-0862f1e29bcb"
        " oob_device_id: 5001 Plugin Respond.",
    )
    assert error.type == exc.DeviceIdFileNotFoundHwControlError


def test_get_oob_id_convert_unknown_exception(mocker, caplog):
    """OOB Information Acquisition Test Device conversion exception"""

    class MockPlugin:
        """Classes for mocks"""

        param_key_value: list = []
        pardic_key_value: dict = {}
        pardic_key_value["oob_device_id"] = "5001"
        pardic_key_value["device_type"] = "graphicController"
        param_key_value.append(pardic_key_value)

        def get_metric_info(self, key_values):
            """return mock value"""
            if key_values == MockPlugin.param_key_value:
                return MOCK_PLUGIN_GRAPHIC_CONTROLLER_METRIC

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", side_effect=ValueError)

    spec_oob_info = GetSpecOOBInfo()
    with pytest.raises(ValueError) as error:
        spec_oob_info.get_metric_oob("c1599cc2-d225-429a-8dd9-0862f1e29bcb", "graphicController")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: c1599cc2-d225-429a-8dd9-0862f1e29bcb"
        " oob_device_id: 5001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: c1599cc2-d225-429a-8dd9-0862f1e29bcb"
        " oob_device_id: 5001 Plugin Respond.",
    )
    assert error.type == ValueError


def test_get_oob_convert_unknown_exception(mocker, caplog):
    """OOB Information Acquisition Test Device conversion exception"""

    class MockPlugin:
        """Classes for mocks"""

        param_key_value: list = []
        pardic_key_value: dict = {}
        pardic_key_value["oob_device_id"] = "5001"
        pardic_key_value["device_type"] = "graphicController"
        param_key_value.append(pardic_key_value)

        def get_metric_info(self, key_values):
            """return mock value"""
            if key_values == MockPlugin.param_key_value:
                return MOCK_PLUGIN_GRAPHIC_CONTROLLER_METRIC

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(GetSpecOOBInfo, "_change_to_device_id", side_effect=PermissionError)

    spec_oob_info = GetSpecOOBInfo()
    with pytest.raises(PermissionError) as error:
        spec_oob_info.get_metric_oob("c1599cc2-d225-429a-8dd9-0862f1e29bcb", "graphicController")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: c1599cc2-d225-429a-8dd9-0862f1e29bcb"
        " oob_device_id: 5001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: c1599cc2-d225-429a-8dd9-0862f1e29bcb"
        " oob_device_id: 5001 Plugin Respond.",
    )
    assert error.type == PermissionError


def test_get_oob_skip_convert(mocker, caplog):
    """OOB Information Acquisition Test Device conversion skip"""

    class MockPlugin:
        """Classes for mocks"""

        param_key_value: list = []
        pardic_key_value: dict = {}
        pardic_key_value["oob_device_id"] = "5001"
        pardic_key_value["device_type"] = "graphicController"
        param_key_value.append(pardic_key_value)

        def get_metric_info(self, key_values):
            """return mock value"""
            if key_values == MockPlugin.param_key_value:
                return MOCK_PLUGIN_MISSING_DEVICE_ID

    mocker.patch("app.core.info.spec_oob.get_plugin", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id", _mock_device_id_to_manager_id)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_metric_oob("c1599cc2-d225-429a-8dd9-0862f1e29bcb", "graphicController")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: c1599cc2-d225-429a-8dd9-0862f1e29bcb"
        " oob_device_id: 5001 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: c1599cc2-d225-429a-8dd9-0862f1e29bcb"
        " oob_device_id: 5001 Plugin Respond.",
    )
    assert actual == EXPECTED_MISSING_DEVICE_ID

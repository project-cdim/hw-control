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

# pylint: disable=R0801,R0903
"""This is a test program."""

import copy
import logging
import pytest
import app.common.basic_exceptions as exc
import app.common.constants as const
from app.core.info.spec_oob import GetSpecOOBInfo
from app.common.dim import device_id_base as dim

MOCK_PLUGIN_CPU_RESPONSE = {
    "devices": [
        {
            "deviceID": "0001",
            "type": "CPU",
            "schema": {"PowerState": "on", "PowerCapability": "True", "socketNum": 1},
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
            "schema": {"PowerState": "on", "PowerCapability": "True", "socketNum": 1},
            "link": [{"type": "memory", "deviceID": "1c440d70-ae46-42f6-b03b-6df28d0913af"}],
            "time": "2000-01-01T01:00:00Z",
        }
    ]
}
EXPECTED_CPU_RESPONSE_METRIC = {
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
        },
        {
            "deviceID": "11056940-fd5c-4f37-87e2-9e6c18b65828",
            "type": "GPU",
            "powerState": "ON",
            "powerCapability": "false",
        },
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
MOCK_PLUGIN_PCIE_DEVICE_RESPONSE_1 = {
    "devices": [
        {
            "deviceID": "3101",
            "type": "networkInterface",
            "schema": {"PowerState": "on", "PowerCapability": "False"},
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "powerState": "ON",
            "powerCapability": "false",
        }
    ]
}
MOCK_PLUGIN_PCIE_DEVICE_METRIC_1 = {
    "devices": [
        {
            "deviceID": "3101",
            "type": "networkInterface",
            "schema": {"PowerState": "on", "PowerCapability": "False"},
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "powerState": "ON",
            "powerCapability": "false",
        }
    ]
}
EXPECTED_PCIE_DEVICE_RESPONSE_1 = {
    "devices": [
        {
            "deviceID": "A13B98C9-2B42-4FDF-B47D-30696B613353",
            "type": "networkInterface",
            "schema": {"PowerState": "on", "PowerCapability": "False"},
            "link": [{"type": "CPU", "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c"}],
            "powerState": "ON",
            "powerCapability": "false",
        }
    ]
}
MOCK_PLUGIN_PCIE_DEVICE_RESPONSE_2 = {
    "devices": [
        {
            "deviceID": "3102",
            "type": "networkInterface",
            "schema": {"PowerState": "on", "PowerCapability": "False"},
            "link": [{"type": "GPU", "deviceID": "4001"}],
            "powerState": "ON",
            "powerCapability": "false",
        }
    ]
}
MOCK_PLUGIN_PCIE_DEVICE_METRIC_2 = {
    "devices": [
        {
            "deviceID": "3102",
            "type": "networkInterface",
            "schema": {"PowerState": "on", "PowerCapability": "False"},
            "link": [{"type": "GPU", "deviceID": "4001"}],
            "powerState": "ON",
            "powerCapability": "false",
        }
    ]
}
EXPECTED_PCIE_DEVICE_RESPONSE_2 = {
    "devices": [
        {
            "deviceID": "D362C392-564A-4C4A-A675-B50E1CA91A6C",
            "type": "networkInterface",
            "schema": {"PowerState": "on", "PowerCapability": "False"},
            "link": [{"type": "GPU", "deviceID": "11056940-fd5c-4f37-87e2-9e6c18b65828"}],
            "powerState": "ON",
            "powerCapability": "false",
        }
    ]
}
MOCK_PLUGIN_SFA_RESPONSE = {
    "devices": [
        {
            "deviceID": "3201",
            "type": "sourceFabricAdapter",
            "schema": {"PowerState": "on", "PowerCapability": "False"},
            "link": [{"type": "destinationFabricAdapter", "deviceID": "3301"}],
            "powerState": "ON",
            "powerCapability": "false",
        }
    ]
}
MOCK_PLUGIN_SFA_RESPONSE_IGNORE = {
    "devices": [
        {
            "deviceID": "3201",
            "type": "sourceFabricAdapter",
            "schema": {"PowerState": "on", "PowerCapability": "False"},
            "link": [{"type": "CPU", "deviceID": "0001"}, {"type": "destinationFabricAdapter", "deviceID": "3301"}],
            "powerState": "ON",
            "powerCapability": "false",
        }
    ]
}
MOCK_PLUGIN_SFA_METRIC = {
    "devices": [
        {
            "deviceID": "3201",
            "type": "sourceFabricAdapter",
            "schema": {"PowerState": "on", "PowerCapability": "False"},
            "link": [{"type": "destinationFabricAdapter", "deviceID": "3301"}],
            "powerState": "ON",
            "powerCapability": "false",
        }
    ]
}
EXPECTED_SFA_RESPONSE = {
    "devices": [
        {
            "deviceID": "938bbddd-551f-64d5-c434-ac6946dd3aa2",
            "type": "sourceFabricAdapter",
            "schema": {"PowerState": "on", "PowerCapability": "False"},
            "link": [{"type": "destinationFabricAdapter", "deviceID": "6AE03D96-C47A-4396-8136-A8590B675339"}],
            "powerState": "ON",
            "powerCapability": "false",
        }
    ]
}
EXPECTED_SFA_CONNECT_CPU_RESPONSE = {
    "devices": [
        {
            "deviceID": "938bbddd-551f-64d5-c434-ac6946dd3aa2",
            "type": "sourceFabricAdapter",
            "schema": {"PowerState": "on", "PowerCapability": "False"},
            "link": [
                {"type": "destinationFabricAdapter", "deviceID": "6AE03D96-C47A-4396-8136-A8590B675339"},
            ],
            "powerState": "ON",
            "powerCapability": "false",
        },
        {
            "deviceID": "A13B98C9-2B42-4FDF-B47D-30696B613353",
            "type": "networkInterface",
            "schema": {"PowerState": "on", "PowerCapability": "False"},
            "link": [
                {"type": "CPU", "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c"},
            ],
            "powerState": "ON",
            "powerCapability": "false",
        },
    ]
}
MOCK_PLUGIN_DFA_ADAPTER_RESPONSE = {
    "devices": [
        {
            "deviceID": "3301",
            "type": "destinationFabricAdapter",
            "schema": {"PowerState": "on", "PowerCapability": "False"},
            "link": [{"type": "sourceFabricAdapter", "deviceID": "3201"}],
            "powerState": "ON",
            "powerCapability": "false",
        }
    ]
}
MOCK_PLUGIN_DFA_ADAPTER_METRIC = {
    "devices": [
        {
            "deviceID": "3301",
            "type": "destinationFabricAdapter",
            "schema": {"PowerState": "on", "PowerCapability": "False"},
            "link": [{"type": "sourceFabricAdapter", "deviceID": "3201"}],
            "powerState": "ON",
            "powerCapability": "false",
        }
    ]
}
EXPECTED_DFA_ADAPTER_RESPONSE = {
    "devices": [
        {
            "deviceID": "6AE03D96-C47A-4396-8136-A8590B675339",
            "type": "destinationFabricAdapter",
            "schema": {"PowerState": "on", "PowerCapability": "False"},
            "link": [{"type": "sourceFabricAdapter", "deviceID": "938bbddd-551f-64d5-c434-ac6946dd3aa2"}],
            "powerState": "ON",
            "powerCapability": "false",
        }
    ]
}
EXPECTED_DFA_ADAPTER_CONNECT_GPU_RESPONSE = {
    "devices": [
        {
            "deviceID": "6AE03D96-C47A-4396-8136-A8590B675339",
            "type": "destinationFabricAdapter",
            "schema": {"PowerState": "on", "PowerCapability": "False"},
            "link": [
                {"type": "sourceFabricAdapter", "deviceID": "938bbddd-551f-64d5-c434-ac6946dd3aa2"},
            ],
            "powerState": "ON",
            "powerCapability": "false",
        },
        {
            "deviceID": "D362C392-564A-4C4A-A675-B50E1CA91A6C",
            "type": "networkInterface",
            "schema": {"PowerState": "on", "PowerCapability": "False"},
            "link": [
                {"type": "GPU", "deviceID": "11056940-fd5c-4f37-87e2-9e6c18b65828"},
            ],
            "powerState": "ON",
            "powerCapability": "false",
        },
    ]
}
MOCK_PLUGIN_CPU_SFA_RESPONSE = {
    "devices": [
        {
            "deviceID": "0001",
            "type": "CPU",
            "schema": {"PowerState": "on", "PowerCapability": "True", "socketNum": 1},
            "link": [
                {"type": "memory", "deviceID": "1001"},
                {"type": "storage", "deviceID": "2001"},
                {"type": "networkInterface", "deviceID": "3101"},
            ],
            "time": "2000-01-01T01:00:00Z",
        }
    ]
}
MOCK_PLUGIN_CPU_SFA_RESPONSE_IGNORE = {
    "devices": [
        {
            "deviceID": "0001",
            "type": "CPU",
            "schema": {"PowerState": "on", "PowerCapability": "True", "socketNum": 1},
            "link": [
                {"type": "memory", "deviceID": "1001"},
                {"type": "networkInterface", "deviceID": "3101"},
                {"type": "networkInterface", "deviceID": "3102"},
                {"type": "storage", "deviceID": "2001"},
            ],
            "time": "2000-01-01T01:00:00Z",
        }
    ]
}
MOCK_PLUGIN_CPU_SFA_METRIC = {
    "devices": [
        {
            "deviceID": "0001",
            "type": "CPU",
            "schema": {"PowerState": "on", "PowerCapability": "True"},
            "link": [
                {"type": "memory", "deviceID": "1001"},
                {"type": "storage", "deviceID": "2001"},
                {"type": "networkInterface", "deviceID": "3101"},
            ],
            "time": "2000-01-01T01:00:00Z",
        }
    ]
}
EXPECTED_CPU_SFA_RESPONSE = {
    "devices": [
        {
            "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c",
            "type": "CPU",
            "schema": {"PowerState": "on", "PowerCapability": "True", "socketNum": 1},
            "link": [
                {"type": "memory", "deviceID": "1c440d70-ae46-42f6-b03b-6df28d0913af"},
                {"type": "storage", "deviceID": "ee9e4718-df31-4bd8-b37b-455e0e0672f6"},
                {"type": "sourceFabricAdapter", "deviceID": "938bbddd-551f-64d5-c434-ac6946dd3aa2"},
                {"type": "destinationFabricAdapter", "deviceID": "6AE03D96-C47A-4396-8136-A8590B675339"},
            ],
            "time": "2000-01-01T01:00:00Z",
        }
    ]
}
EXPECTED_CPU_SFA_RESPONSE_IGNORE = {
    "devices": [
        {
            "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c",
            "type": "CPU",
            "schema": {"PowerState": "on", "PowerCapability": "True", "socketNum": 1},
            "link": [
                {"type": "memory", "deviceID": "1c440d70-ae46-42f6-b03b-6df28d0913af"},
                {"type": "sourceFabricAdapter", "deviceID": "938bbddd-551f-64d5-c434-ac6946dd3aa2"},
                {"type": "destinationFabricAdapter", "deviceID": "6AE03D96-C47A-4396-8136-A8590B675339"},
                {"type": "destinationFabricAdapter", "deviceID": "6AE03D96-C47A-4396-8136-A8590B675339"},
                {"type": "storage", "deviceID": "ee9e4718-df31-4bd8-b37b-455e0e0672f6"},
            ],
            "time": "2000-01-01T01:00:00Z",
        }
    ]
}
EXPECTED_CPU_SFA_RESPONSE_IGNORE_2 = {
    "devices": [
        {
            "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c",
            "type": "CPU",
            "schema": {"PowerState": "on", "PowerCapability": "True", "socketNum": 1},
            "link": [
                {"type": "memory", "deviceID": "1c440d70-ae46-42f6-b03b-6df28d0913af"},
                {"type": "storage", "deviceID": "ee9e4718-df31-4bd8-b37b-455e0e0672f6"},
                {"type": "sourceFabricAdapter", "deviceID": "938bbddd-551f-64d5-c434-ac6946dd3aa2"},
                {"type": "destinationFabricAdapter", "deviceID": "6AE03D96-C47A-4396-8136-A8590B675339"},
            ],
            "time": "2000-01-01T01:00:00Z",
        }
    ]
}
EXPECTED_CPU_SFA_METIC = {
    "devices": [
        {
            "deviceID": "28c2318b-6b69-4f41-9865-166906ca2e1c",
            "type": "CPU",
            "schema": {"PowerState": "on", "PowerCapability": "True"},
            "link": [
                {"type": "memory", "deviceID": "1c440d70-ae46-42f6-b03b-6df28d0913af"},
                {"type": "storage", "deviceID": "ee9e4718-df31-4bd8-b37b-455e0e0672f6"},
                {"type": "networkInterface", "deviceID": "A13B98C9-2B42-4FDF-B47D-30696B613353"},
            ],
            "time": "2000-01-01T01:00:00Z",
        }
    ]
}
MOCK_PLUGIN_MISSING_DEVICE_ID = {
    "devices": [{"type": "graphicController", "powerState": "ON", "powerCapability": "false"}]
}
EXPECTED_MISSING_DEVICE_ID = {
    "devices": [{"type": "graphicController", "powerState": "ON", "powerCapability": "false"}]
}


def _log_contains(record, level, message) -> bool:
    return next(filter(lambda x: (x[1] == level) and (message in x[2]), record), None) is not None


def _mock_device_id_to_manager_id_multi_hostport(device_id):
    table = {
        "28c2318b-6b69-4f41-9865-166906ca2e1c": {"fm": [], "oob": ["BMC-1"]},
        "1c440d70-ae46-42f6-b03b-6df28d0913af": {"fm": [], "oob": ["BMC-1"]},
        "ee9e4718-df31-4bd8-b37b-455e0e0672f6": {"fm": [], "oob": ["BMC-1"]},
        "00029c15-bccb-4f9a-a251-51c9d307a097": {"fm": [], "oob": ["BMC-1"]},
        "A13B98C9-2B42-4FDF-B47D-30696B613353": {"fm": [], "oob": ["BMC-1"]},
        "D362C392-564A-4C4A-A675-B50E1CA91A6C": {"fm": [], "oob": ["BMC-1"]},
        "938bbddd-551f-64d5-c434-ac6946dd3aa2": {"fm": [], "oob": ["BMC-1"]},
        "6AE03D96-C47A-4396-8136-A8590B675339": {"fm": [], "oob": ["BMC-1"]},
        "11056940-fd5c-4f37-87e2-9e6c18b65828": {"fm": [], "oob": ["BMC-1", "BMC-2"]},
        "c1599cc2-d225-429a-8dd9-0862f1e29bcb": {"fm": [], "oob": ["BMC-1"]},
        "1e13e51c-80fb-4751-84b3-126e33793ec4": {"fm": [], "oob": None},
    }

    if device_id in table:
        return table[device_id]

    raise exc.ConfigurationHWControlError


def _mock_device_id_to_oob_device_id(device_id):
    table = {
        "28c2318b-6b69-4f41-9865-166906ca2e1c": "0001",
        "1c440d70-ae46-42f6-b03b-6df28d0913af": "1001",
        "ee9e4718-df31-4bd8-b37b-455e0e0672f6": "2001",
        "00029c15-bccb-4f9a-a251-51c9d307a097": "3001",
        "A13B98C9-2B42-4FDF-B47D-30696B613353": "3101",
        "D362C392-564A-4C4A-A675-B50E1CA91A6C": "3102",
        "938bbddd-551f-64d5-c434-ac6946dd3aa2": "3201",
        "6AE03D96-C47A-4396-8136-A8590B675339": "3301",
        "11056940-fd5c-4f37-87e2-9e6c18b65828": "4001",
        "c1599cc2-d225-429a-8dd9-0862f1e29bcb": "5001",
    }

    if device_id in table:
        return table[device_id]

    raise exc.ConfigurationHWControlError


def _mock_device_id_to_device_type(device_id):
    table = {
        "28c2318b-6b69-4f41-9865-166906ca2e1c": "CPU",
        "1c440d70-ae46-42f6-b03b-6df28d0913af": "memory",
        "ee9e4718-df31-4bd8-b37b-455e0e0672f6": "storage",
        "00029c15-bccb-4f9a-a251-51c9d307a097": "networkInterface",
        "A13B98C9-2B42-4FDF-B47D-30696B613353": "networkInterface",
        "D362C392-564A-4C4A-A675-B50E1CA91A6C": "networkInterface",
        "938bbddd-551f-64d5-c434-ac6946dd3aa2": "sourceFabricAdapter",
        "6AE03D96-C47A-4396-8136-A8590B675339": "destinationFabricAdapter",
        "11056940-fd5c-4f37-87e2-9e6c18b65828": "GPU",
        "c1599cc2-d225-429a-8dd9-0862f1e29bcb": "graphicController",
    }

    if device_id in table:
        return table[device_id]

    raise exc.ConfigurationHWControlError


def _mock_oob_device_id_to_device_id(oob_device_id, oob_manager_id):
    table_001 = {
        "0001": "28c2318b-6b69-4f41-9865-166906ca2e1c",
        "1001": "1c440d70-ae46-42f6-b03b-6df28d0913af",
        "2001": "ee9e4718-df31-4bd8-b37b-455e0e0672f6",
        "3001": "00029c15-bccb-4f9a-a251-51c9d307a097",
        "3101": "A13B98C9-2B42-4FDF-B47D-30696B613353",
        "3102": "D362C392-564A-4C4A-A675-B50E1CA91A6C",
        "3201": "938bbddd-551f-64d5-c434-ac6946dd3aa2",
        "3301": "6AE03D96-C47A-4396-8136-A8590B675339",
        "4001": "11056940-fd5c-4f37-87e2-9e6c18b65828",
        "5001": "c1599cc2-d225-429a-8dd9-0862f1e29bcb",
    }
    table_002 = {
        "0001": "28c2318b-6b69-4f41-9865-166906ca2e1c",
        "1001": "1c440d70-ae46-42f6-b03b-6df28d0913af",
        "2001": "ee9e4718-df31-4bd8-b37b-455e0e0672f6",
        "3001": "00029c15-bccb-4f9a-a251-51c9d307a097",
        "3101": "A13B98C9-2B42-4FDF-B47D-30696B613353",
        "3102": "D362C392-564A-4C4A-A675-B50E1CA91A6C",
        "3201": "938bbddd-551f-64d5-c434-ac6946dd3aa2",
        "3301": "6AE03D96-C47A-4396-8136-A8590B675339",
        "4001": "11056940-fd5c-4f37-87e2-9e6c18b65828",
        "5001": "c1599cc2-d225-429a-8dd9-0862f1e29bcb",
    }

    if oob_manager_id == "BMC-1" and oob_device_id in table_001:
        return table_001[oob_device_id]

    if oob_manager_id == "BMC-2" and oob_device_id in table_002:
        return table_002[oob_device_id]

    raise exc.ConfigurationHWControlError


def _mock_device_id_to_switch_port_type(device_id: str) -> str | None:
    table = {
        "D362C392-564A-4C4A-A675-B50E1CA91A6C": "USP",
        "938bbddd-551f-64d5-c434-ac6946dd3aa2": "USP",
        "6AE03D96-C47A-4396-8136-A8590B675339": "DSP",
        "11056940-fd5c-4f37-87e2-9e6c18b65828": "DSP",
        "c1599cc2-d225-429a-8dd9-0862f1e29bcb": "DSP",
    }

    return table.get(device_id)


def _mock_get_device_id_of_switch_port_type(
    device_id: str, switch_port_type: const.SwitchPortType | None
) -> str | None:
    table = {
        "A13B98C9-2B42-4FDF-B47D-30696B613353": {
            const.SwitchPortType.USP: "938bbddd-551f-64d5-c434-ac6946dd3aa2",
            const.SwitchPortType.DSP: None,
            None: None,
        },
        "D362C392-564A-4C4A-A675-B50E1CA91A6C": {
            const.SwitchPortType.USP: None,
            const.SwitchPortType.DSP: "6AE03D96-C47A-4396-8136-A8590B675339",
            None: None,
        },
        "938bbddd-551f-64d5-c434-ac6946dd3aa2": {
            const.SwitchPortType.USP: None,
            const.SwitchPortType.DSP: None,
            None: "A13B98C9-2B42-4FDF-B47D-30696B613353",
        },
        "6AE03D96-C47A-4396-8136-A8590B675339": {
            const.SwitchPortType.USP: "D362C392-564A-4C4A-A675-B50E1CA91A6C",
            const.SwitchPortType.DSP: None,
            None: None,
        },
    }

    return table.get(device_id, {}).get(switch_port_type)


def test_get_spec_oob_cpu(mocker, caplog) -> None:
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
                return copy.deepcopy(MOCK_PLUGIN_CPU_RESPONSE)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

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


def test_get_spec_oob_memory(mocker, caplog) -> None:
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
                return copy.deepcopy(MOCK_PLUGIN_MEMORY_RESPONSE)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

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


def test_get_spec_oob_storage(mocker, caplog) -> None:
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
                return copy.deepcopy(MOCK_PLUGIN_STORAGE_RESPONSE)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

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


def test_get_spec_oob_nic(mocker, caplog) -> None:
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
                return copy.deepcopy(MOCK_PLUGIN_NIC_RESPONSE)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

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


def test_get_spec_oob_gpu(mocker, caplog) -> None:
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
                return copy.deepcopy(MOCK_PLUGIN_GPU_RESPONSE)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

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


def test_get_spec_oob_graphic_controller(mocker, caplog) -> None:
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
                return copy.deepcopy(MOCK_PLUGIN_GRAPHIC_CONTROLLER_RESPONSE)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

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
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

    expected = {"devices": [{"deviceID": "1e13e51c-80fb-4751-84b3-126e33793ec4", "type": "GPU"}]}

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_spec_oob("1e13e51c-80fb-4751-84b3-126e33793ec4", "GPU")

    assert expected == actual


def test_get_spec_oob_empty_device_type(caplog):
    """OOB Information Acquisition Test Device check error"""
    spec_oob_info = GetSpecOOBInfo()

    with pytest.raises(exc.InternalHWControlError) as error:
        spec_oob_info.get_spec_oob("28c2318b-6b69-4f41-9865-166906ca2e1c", "")

    assert _log_contains(caplog.record_tuples, logging.WARN, "W00002: Unexpected DeviceType: ")
    assert isinstance(error.value, exc.InternalHWControlError)


def test_get_spec_oob_get_plugin_error(mocker):
    """OOB Information Acquisition Test An exception occurs at Plugin"""
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", side_effect=exc.APIUsageHWControlError)
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)

    spec_oob_info = GetSpecOOBInfo()
    with pytest.raises(exc.APIUsageHWControlError) as error:
        spec_oob_info.get_spec_oob("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert isinstance(error.value, exc.APIUsageHWControlError)


def test_get_spec_oob_get_plugin_unknown_exception(mocker, caplog):
    """OOB Information Acquisition Test An exception occurs at Plugin"""
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", side_effect=AttributeError)
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)

    spec_oob_info = GetSpecOOBInfo()
    with pytest.raises(AttributeError) as error:
        spec_oob_info.get_spec_oob("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert _log_contains(caplog.record_tuples, logging.WARN, "W00001: Unexpected Exception: ")
    assert isinstance(error.value, AttributeError)


def test_get_spec_oob_no_device_data(mocker, caplog):
    """OOB Information Acquisition Test Device check error"""

    class MockPlugin:
        """Classes for mocks"""

        def get_spec_info(self, key_values):
            """return mock value"""
            return key_values

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)

    spec_oob_info = GetSpecOOBInfo()

    with pytest.raises(exc.InternalHWControlError) as error:
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
    assert isinstance(error.value, exc.InternalHWControlError)


def test_get_spec_oob_no_device_key(mocker, caplog):
    """OOB Information Acquisition Test Device check error"""

    class MockPlugin:
        """Classes for mocks"""

        def get_spec_info(self, key_values):
            """return mock value"""
            return {"unexpectedDict": key_values}

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)

    spec_oob_info = GetSpecOOBInfo()

    with pytest.raises(exc.InternalHWControlError) as error:
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
    assert isinstance(error.value, exc.InternalHWControlError)


def test_get_spec_oob_plugin_error(mocker, caplog):
    """OOB Information Acquisition Test An exception occurs at Plugin"""

    class MockPlugin:
        """Classes for mocks"""

        def get_spec_info(self, key_values):
            """return mock value"""
            raise exc.ConfigurationHWControlError

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)

    spec_oob_info = GetSpecOOBInfo()

    with pytest.raises(exc.ConfigurationHWControlError) as error:
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

    assert isinstance(error.value, exc.ConfigurationHWControlError)


def test_get_spec_oob_plugin_unknown_exception(mocker, caplog):
    """OOB Information Acquisition Test An exception occurs at Plugin"""

    class MockPlugin:
        """Classes for mocks"""

        def get_spec_info(self, key_values):
            """return mock value"""
            raise TypeError

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
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
    assert isinstance(error.value, TypeError)


def test_get_metric_oob_cpu(mocker, caplog) -> None:
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
                return copy.deepcopy(MOCK_PLUGIN_CPU_METRIC)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

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
    assert actual == EXPECTED_CPU_RESPONSE_METRIC


def test_get_metric_oob_memory(mocker, caplog) -> None:
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
                return copy.deepcopy(MOCK_PLUGIN_MEMORY_METRIC)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

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


def test_get_metric_oob_storage(mocker, caplog) -> None:
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
                return copy.deepcopy(MOCK_PLUGIN_STORAGE_METRIC)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

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


def test_get_metric_oob_nic(mocker, caplog) -> None:
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
                return copy.deepcopy(MOCK_PLUGIN_NIC_METRIC)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

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


def test_get_metric_oob_gpu(mocker, caplog) -> None:
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
                return copy.deepcopy(MOCK_PLUGIN_GPU_METRIC)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

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


def test_get_metric_oob_graphic_controller(mocker, caplog) -> None:
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
                return copy.deepcopy(MOCK_PLUGIN_GRAPHIC_CONTROLLER_METRIC)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

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
    mocker.patch("app.core.info.info_utils.get_combination_match_device", return_value=(None, None))
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)

    expected = {"devices": [{"deviceID": "1e13e51c-80fb-4751-84b3-126e33793ec4", "type": "GPU"}]}

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_metric_oob("1e13e51c-80fb-4751-84b3-126e33793ec4", "GPU")

    assert expected == actual


def test_get_metric_oob_empty_device_type(caplog):
    """OOB Metric Information Acquisition Test Device check error"""
    spec_oob_info = GetSpecOOBInfo()

    with pytest.raises(exc.InternalHWControlError) as error:
        spec_oob_info.get_metric_oob("1c440d70-ae46-42f6-b03b-6df28d0913af", "")

    caplog.set_level(logging.INFO)
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
    assert isinstance(error.value, exc.InternalHWControlError)


def test_get_metric_oob_get_plugin_error(mocker):
    """OOB Metric Information Acquisition Test An exception occurs at Plugin"""
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", side_effect=exc.APIUsageHWControlError)
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)

    spec_oob_info = GetSpecOOBInfo()
    with pytest.raises(exc.APIUsageHWControlError) as error:
        spec_oob_info.get_metric_oob("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert isinstance(error.value, exc.APIUsageHWControlError)


def test_get_metric_oob_get_plugin_unknown_exception(mocker, caplog):
    """OOB Metric Information Acquisition Test An exception occurs at Plugin"""
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", side_effect=FileNotFoundError)
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)

    spec_oob_info = GetSpecOOBInfo()
    with pytest.raises(FileNotFoundError) as error:
        spec_oob_info.get_metric_oob("28c2318b-6b69-4f41-9865-166906ca2e1c", "CPU")

    assert _log_contains(caplog.record_tuples, logging.WARN, "W00001: Unexpected Exception: ")
    assert isinstance(error.value, FileNotFoundError)


def test_get_metric_oob_no_device_data(mocker, caplog):
    """OOB Metric Information Acquisition Test Device check error"""

    class MockPlugin:
        """Classes for mocks"""

        def get_metric_info(self, key_values):
            """return mock value"""
            return key_values

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)

    spec_oob_info = GetSpecOOBInfo()

    with pytest.raises(exc.InternalHWControlError) as error:
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
    assert isinstance(error.value, exc.InternalHWControlError)


def test_get_metric_oob_no_device_key(mocker, caplog):
    """OOB Metric Information Acquisition Test Device check error"""

    class MockPlugin:
        """Classes for mocks"""

        def get_metric_info(self, key_values):
            """return mock value"""
            return {"unexpectedDict": key_values}

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)

    spec_oob_info = GetSpecOOBInfo()

    with pytest.raises(exc.InternalHWControlError) as error:
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
    assert isinstance(error.value, exc.InternalHWControlError)


def test_get_metric_oob_plugin_error(mocker, caplog):
    """OOB Metric Information Acquisition Test An exception occurs at Plugin"""

    class MockPlugin:
        """Classes for mocks"""

        def get_metric_info(self, key_values):
            """return mock value"""
            raise exc.ConfigurationHWControlError

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)

    spec_oob_info = GetSpecOOBInfo()

    with pytest.raises(exc.ConfigurationHWControlError) as error:
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

    assert isinstance(error.value, exc.ConfigurationHWControlError)


def test_get_metric_oob_plugin_unknown_exception(mocker, caplog):
    """OOB Metric Information Acquisition Test An exception occurs at Plugin"""

    class MockPlugin:
        """Classes for mocks"""

        def get_metric_info(self, key_values):
            """return mock value"""
            raise IndexError

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
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
    assert isinstance(error.value, IndexError)


def test_get_oob_id_convert_error(mocker, caplog) -> None:
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
                return copy.deepcopy(MOCK_PLUGIN_GRAPHIC_CONTROLLER_METRIC)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", side_effect=exc.DeviceIDFileNotFoundHWControlError)

    spec_oob_info = GetSpecOOBInfo()
    with pytest.raises(exc.DeviceIDFileNotFoundHWControlError) as error:
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
    assert isinstance(error.value, exc.DeviceIDFileNotFoundHWControlError)


def test_get_oob_id_convert_unknown_exception(mocker, caplog) -> None:
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
                return copy.deepcopy(MOCK_PLUGIN_GRAPHIC_CONTROLLER_METRIC)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
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
    assert isinstance(error.value, ValueError)


def test_get_oob_convert_unknown_exception(mocker, caplog) -> None:
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
                return copy.deepcopy(MOCK_PLUGIN_GRAPHIC_CONTROLLER_METRIC)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
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
    assert isinstance(error.value, PermissionError)


def test_get_oob_skip_convert(mocker, caplog) -> None:
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
                return copy.deepcopy(MOCK_PLUGIN_MISSING_DEVICE_ID)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

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


def test_get_spec_oob_source_fabric_adapter(mocker, caplog) -> None:
    """OOB Information Acquisition Test Non Functional source fabric adapter by OOB"""

    class MockPlugin:
        """Classes for mocks"""

        def get_spec_info(self, key_values):
            """return mock value"""
            if key_values == [{"oob_device_id": "3201", "device_type": "sourceFabricAdapter"}]:
                return copy.deepcopy(MOCK_PLUGIN_SFA_RESPONSE)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch("app.core.info.info_utils.get_combination_match_device", return_value=(None, None))
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_spec_oob("938bbddd-551f-64d5-c434-ac6946dd3aa2", "sourceFabricAdapter")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: 938bbddd-551f-64d5-c434-ac6946dd3aa2"
        " oob_device_id: 3201 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: 938bbddd-551f-64d5-c434-ac6946dd3aa2"
        " oob_device_id: 3201 Plugin Respond.",
    )
    assert actual == EXPECTED_SFA_RESPONSE


def test_get_spec_oob_source_fabric_adapter_connect_cpu(mocker, caplog) -> None:
    """OOB Information Acquisition Test Non Functional source fabric adapter by OOB"""

    class MockPlugin:
        """Classes for mocks"""

        def get_spec_info(self, key_values):
            """return mock value"""
            if key_values == [{"oob_device_id": "3201", "device_type": "sourceFabricAdapter"}]:
                return copy.deepcopy(MOCK_PLUGIN_SFA_RESPONSE)
            if key_values == [{"oob_device_id": "3101", "device_type": "networkInterface"}]:
                return copy.deepcopy(MOCK_PLUGIN_PCIE_DEVICE_RESPONSE_1)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_spec_oob("938bbddd-551f-64d5-c434-ac6946dd3aa2", "sourceFabricAdapter")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: 938bbddd-551f-64d5-c434-ac6946dd3aa2"
        " oob_device_id: 3201 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: A13B98C9-2B42-4FDF-B47D-30696B613353"
        " oob_device_id: 3101 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: 938bbddd-551f-64d5-c434-ac6946dd3aa2"
        " oob_device_id: 3201 Plugin Respond.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: A13B98C9-2B42-4FDF-B47D-30696B613353"
        " oob_device_id: 3101 Plugin Respond.",
    )
    assert actual == EXPECTED_SFA_CONNECT_CPU_RESPONSE


def test_get_spec_oob_destination_fabric_adapter(mocker, caplog) -> None:
    """OOB Information Acquisition Test Non Functional network adapter by OOB"""

    class MockPlugin:
        """Classes for mocks"""

        def get_spec_info(self, key_values):
            """return mock value"""
            if key_values == [{"oob_device_id": "3301", "device_type": "destinationFabricAdapter"}]:
                return copy.deepcopy(MOCK_PLUGIN_DFA_ADAPTER_RESPONSE)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch("app.core.info.info_utils.get_combination_match_device", return_value=(None, None))
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_spec_oob("6AE03D96-C47A-4396-8136-A8590B675339", "destinationFabricAdapter")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: 6AE03D96-C47A-4396-8136-A8590B675339"
        " oob_device_id: 3301 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: 6AE03D96-C47A-4396-8136-A8590B675339"
        " oob_device_id: 3301 Plugin Respond.",
    )
    assert actual == EXPECTED_DFA_ADAPTER_RESPONSE


def test_get_spec_oob_destination_fabric_adapter_connect_gpu(mocker, caplog) -> None:
    """OOB Information Acquisition Test Non Functional source fabric adapter by OOB"""

    class MockPlugin:
        """Classes for mocks"""

        def get_spec_info(self, key_values):
            """return mock value"""
            if key_values == [{"oob_device_id": "3301", "device_type": "destinationFabricAdapter"}]:
                return copy.deepcopy(MOCK_PLUGIN_DFA_ADAPTER_RESPONSE)
            if key_values == [{"oob_device_id": "3102", "device_type": "networkInterface"}]:
                return copy.deepcopy(MOCK_PLUGIN_PCIE_DEVICE_RESPONSE_2)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_spec_oob("6AE03D96-C47A-4396-8136-A8590B675339", "destinationFabricAdapter")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: 6AE03D96-C47A-4396-8136-A8590B675339"
        " oob_device_id: 3301 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: D362C392-564A-4C4A-A675-B50E1CA91A6C"
        " oob_device_id: 3102 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: 6AE03D96-C47A-4396-8136-A8590B675339"
        " oob_device_id: 3301 Plugin Respond.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: D362C392-564A-4C4A-A675-B50E1CA91A6C"
        " oob_device_id: 3102 Plugin Respond.",
    )
    assert actual == EXPECTED_DFA_ADAPTER_CONNECT_GPU_RESPONSE


def test_get_spec_oob_cpu_sfa(mocker, caplog) -> None:
    """OOB Information Acquisition Test Non Functional network adapter by OOB"""

    class MockPlugin:
        """Classes for mocks"""

        def get_spec_info(self, key_values):
            """return mock value"""
            if key_values == [{"oob_device_id": "0001", "device_type": "CPU"}]:
                return copy.deepcopy(MOCK_PLUGIN_CPU_SFA_RESPONSE)
            if key_values == [{"oob_device_id": "3201", "device_type": "sourceFabricAdapter"}]:
                return copy.deepcopy(MOCK_PLUGIN_SFA_RESPONSE)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

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
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: 938bbddd-551f-64d5-c434-ac6946dd3aa2"
        " oob_device_id: 3201 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: 938bbddd-551f-64d5-c434-ac6946dd3aa2"
        " oob_device_id: 3201 Plugin Respond.",
    )
    assert actual == EXPECTED_CPU_SFA_RESPONSE


def test_get_spec_oob_cpu_sfa_ignore(mocker, caplog) -> None:
    """OOB Information Acquisition Test Non Functional network adapter by OOB"""

    class MockPlugin:
        """Classes for mocks"""

        def get_spec_info(self, key_values):
            """return mock value"""
            if key_values == [{"oob_device_id": "0001", "device_type": "CPU"}]:
                return copy.deepcopy(MOCK_PLUGIN_CPU_SFA_RESPONSE_IGNORE)
            if key_values == [{"oob_device_id": "3201", "device_type": "sourceFabricAdapter"}]:
                return copy.deepcopy(MOCK_PLUGIN_SFA_RESPONSE)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

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
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: 938bbddd-551f-64d5-c434-ac6946dd3aa2"
        " oob_device_id: 3201 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: 938bbddd-551f-64d5-c434-ac6946dd3aa2"
        " oob_device_id: 3201 Plugin Respond.",
    )
    assert actual == EXPECTED_CPU_SFA_RESPONSE_IGNORE


def test_get_spec_oob_cpu_sfa_ignore_2(mocker, caplog) -> None:
    """OOB Information Acquisition Test Non Functional network adapter by OOB"""

    class MockPlugin:
        """Classes for mocks"""

        def get_spec_info(self, key_values):
            """return mock value"""
            if key_values == [{"oob_device_id": "0001", "device_type": "CPU"}]:
                return copy.deepcopy(MOCK_PLUGIN_CPU_SFA_RESPONSE)
            if key_values == [{"oob_device_id": "3201", "device_type": "sourceFabricAdapter"}]:
                return copy.deepcopy(MOCK_PLUGIN_SFA_RESPONSE_IGNORE)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

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
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_spec_info device_id: 938bbddd-551f-64d5-c434-ac6946dd3aa2"
        " oob_device_id: 3201 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_spec_info device_id: 938bbddd-551f-64d5-c434-ac6946dd3aa2"
        " oob_device_id: 3201 Plugin Respond.",
    )
    assert actual == EXPECTED_CPU_SFA_RESPONSE_IGNORE_2


def test_get_metric_oob_source_fabric_adapter(mocker, caplog) -> None:
    """OOB Information Acquisition Test Non Functional source fabric adapter by OOB"""

    class MockPlugin:
        """Classes for mocks"""

        def get_metric_info(self, key_values):
            """return mock value"""
            if key_values == [{"oob_device_id": "3201", "device_type": "sourceFabricAdapter"}]:
                return copy.deepcopy(MOCK_PLUGIN_SFA_METRIC)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch("app.core.info.info_utils.get_combination_match_device", return_value=(None, None))
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_metric_oob("938bbddd-551f-64d5-c434-ac6946dd3aa2", "sourceFabricAdapter")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: 938bbddd-551f-64d5-c434-ac6946dd3aa2"
        " oob_device_id: 3201 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: 938bbddd-551f-64d5-c434-ac6946dd3aa2"
        " oob_device_id: 3201 Plugin Respond.",
    )
    assert actual == EXPECTED_SFA_RESPONSE


def test_get_metric_oob_source_fabric_adapter_connect_cpu(mocker, caplog) -> None:
    """OOB Information Acquisition Test Non Functional source fabric adapter by OOB"""

    class MockPlugin:
        """Classes for mocks"""

        def get_metric_info(self, key_values):
            """return mock value"""
            if key_values == [{"oob_device_id": "3201", "device_type": "sourceFabricAdapter"}]:
                return copy.deepcopy(MOCK_PLUGIN_SFA_METRIC)
            if key_values == [{"oob_device_id": "3101", "device_type": "networkInterface"}]:
                return copy.deepcopy(MOCK_PLUGIN_PCIE_DEVICE_METRIC_1)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_metric_oob("938bbddd-551f-64d5-c434-ac6946dd3aa2", "sourceFabricAdapter")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: 938bbddd-551f-64d5-c434-ac6946dd3aa2"
        " oob_device_id: 3201 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: 938bbddd-551f-64d5-c434-ac6946dd3aa2"
        " oob_device_id: 3201 Plugin Respond.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: A13B98C9-2B42-4FDF-B47D-30696B613353"
        " oob_device_id: 3101 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: A13B98C9-2B42-4FDF-B47D-30696B613353"
        " oob_device_id: 3101 Plugin Respond.",
    )
    assert actual == EXPECTED_SFA_CONNECT_CPU_RESPONSE


def test_get_metric_oob_destination_fabric_adapter(mocker, caplog) -> None:
    """OOB Information Acquisition Test Non Functional network adapter by OOB"""

    class MockPlugin:
        """Classes for mocks"""

        def get_metric_info(self, key_values):
            """return mock value"""
            if key_values == [{"oob_device_id": "3301", "device_type": "destinationFabricAdapter"}]:
                return copy.deepcopy(MOCK_PLUGIN_DFA_ADAPTER_METRIC)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch("app.core.info.info_utils.get_combination_match_device", return_value=(None, None))
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_metric_oob("6AE03D96-C47A-4396-8136-A8590B675339", "destinationFabricAdapter")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: 6AE03D96-C47A-4396-8136-A8590B675339"
        " oob_device_id: 3301 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: 6AE03D96-C47A-4396-8136-A8590B675339"
        " oob_device_id: 3301 Plugin Respond.",
    )
    assert actual == EXPECTED_DFA_ADAPTER_RESPONSE


def test_get_metric_oob_destination_fabric_adapter_connect_gpu(mocker, caplog) -> None:
    """OOB Information Acquisition Test Non Functional source fabric adapter by OOB"""

    class MockPlugin:
        """Classes for mocks"""

        def get_metric_info(self, key_values):
            """return mock value"""
            if key_values == [{"oob_device_id": "3301", "device_type": "destinationFabricAdapter"}]:
                return copy.deepcopy(MOCK_PLUGIN_DFA_ADAPTER_METRIC)
            if key_values == [{"oob_device_id": "3102", "device_type": "networkInterface"}]:
                return copy.deepcopy(MOCK_PLUGIN_PCIE_DEVICE_METRIC_2)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

    spec_oob_info = GetSpecOOBInfo()
    actual = spec_oob_info.get_metric_oob("6AE03D96-C47A-4396-8136-A8590B675339", "destinationFabricAdapter")

    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: 6AE03D96-C47A-4396-8136-A8590B675339"
        " oob_device_id: 3301 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: 6AE03D96-C47A-4396-8136-A8590B675339"
        " oob_device_id: 3301 Plugin Respond.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00003: BMC-1 get_metric_info device_id: D362C392-564A-4C4A-A675-B50E1CA91A6C"
        " oob_device_id: 3102 Plugin Call.",
    )
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "I00004: BMC-1 get_metric_info device_id: D362C392-564A-4C4A-A675-B50E1CA91A6C"
        " oob_device_id: 3102 Plugin Respond.",
    )
    assert actual == EXPECTED_DFA_ADAPTER_CONNECT_GPU_RESPONSE


def test_get_metric_oob_cpu_sfa(mocker, caplog) -> None:
    """OOB Information Acquisition Test Non Functional network adapter by OOB"""

    class MockPlugin:
        """Classes for mocks"""

        def get_metric_info(self, key_values):
            """return mock value"""
            if key_values == [{"oob_device_id": "0001", "device_type": "CPU"}]:
                return copy.deepcopy(MOCK_PLUGIN_CPU_SFA_METRIC)
            if key_values == [{"oob_device_id": "3201", "device_type": "sourceFabricAdapter"}]:
                return copy.deepcopy(MOCK_PLUGIN_SFA_METRIC)
            return None

    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.spec_oob.plugin_loader.get_oob", return_value=MockPlugin())
    mocker.patch.object(dim, "device_id_to_manager_id_multi_hostport", _mock_device_id_to_manager_id_multi_hostport)
    mocker.patch.object(dim, "device_id_to_oob_device_id", _mock_device_id_to_oob_device_id)
    mocker.patch.object(dim, "oob_device_id_to_device_id", _mock_oob_device_id_to_device_id)
    mocker.patch.object(dim, "device_id_to_device_type", _mock_device_id_to_device_type)
    mocker.patch.object(dim, "device_id_to_switch_port_type", _mock_device_id_to_switch_port_type)
    mocker.patch.object(dim, "get_device_id_of_switch_port_type", _mock_get_device_id_of_switch_port_type)

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
    assert actual == EXPECTED_CPU_SFA_METIC

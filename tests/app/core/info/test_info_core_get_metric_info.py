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

import os
import logging
import datetime
import pytest
from app.common.settings import settings
from app.core.info.info_core import InformationCore
from app.common.constants import TIME_STAMP_FORMAT
from app.common.basic_exceptions import (
    BaseHwControlError,
    InternalHwControlError,
)
from app.core.info.info_utils import load_mapping_table


# Response Item Name Current Date and Time
RESP_ITEM_NAME_TIME_STAMP = "infoTimestamp"

# Agent CPU
AGENT_DATA_CPU = {
    "data": [
        {
            "type": "CPU",
            "usageRate": 123.45,
            "user": 67.89,
            "system": 1.23,
            "wait": 4.56,
            "idle": 7.89,
            "cpuWatts": 12345,
        }
    ]
}

# OOB CPU
OOB_DATA_CPU = {
    "devices": [
        {
            "type": "CPU",
            "deviceID": "0001",
            "schema": {"PowerState": "On", "PowerCapability": True, "Status": {"Health": "OK", "State": "Enabled"}},
            "metric": {
                "BandwidthPercent": 62,
                "OperatingSpeedMHz": 2400,
                "Cache": [
                    {
                        "CacheMiss": 0.12,
                        "CacheMissesPerInstruction": 0.00088,
                        "HitRatio": 0.719,
                        "OccupancyBytes": 3030144,
                        "OccupancyPercent": 90.1,
                    }
                ],
                "CoreMetrics": [
                    {
                        "CoreId": "core0",
                        "InstructionsPerCycle": 1.16,
                        "CoreCache": [{"OccupancyBytes": 198231, "OccupancyPercent": 77.4}],
                    }
                ],
                "LocalMemoryBandwidthBytes": 18253611008,
                "RemoteMemoryBandwidthBytes": 81788928,
            },
            "environment": {
                "Sensor": {
                    "SensorResetTime": "2023-11-20T04:14:00Z",  # NOSONAR
                    "SensingInterval": "PT5S",
                    "ReadingTime": "2023-11-20T05:15:00Z",  # NOSONAR
                },
                "EnergyJoules": {
                    "Reading": 25,
                },
            },
        }
    ]
}

# OOB CPU int value
OOB_DATA_CPU_INT = {
    "devices": [
        {
            "type": "CPU",
            "deviceID": "0001",
            "metric": {
                "BandwidthPercent": 10,
                "Cache": [{"CacheMiss": 0, "CacheMissesPerInstruction": 1, "HitRatio": 2, "OccupancyPercent": 3}],
                "CoreMetrics": [{"InstructionsPerCycle": 5, "CoreCache": [{"OccupancyPercent": 6}]}],
            },
            "environment": {"EnergyJoules": {"Reading": 7}},
        }
    ]
}

# OOB CPU float value
OOB_DATA_CPU_FLOAT = {
    "devices": [
        {
            "type": "CPU",
            "deviceID": "0001",
            "metric": {
                "BandwidthPercent": 0.01,
                "Cache": [
                    {"CacheMiss": 0.02, "CacheMissesPerInstruction": 0.03, "HitRatio": 0.04, "OccupancyPercent": 10.05}
                ],
                "CoreMetrics": [{"InstructionsPerCycle": 1.06, "CoreCache": [{"OccupancyPercent": 20.07}]}],
            },
            "environment": {"EnergyJoules": {"Reading": 30.08}},
        }
    ]
}

# FM_DATA CPU
FM_DATA_CPU = {"data": [{"deviceID": "0001", "type": "CPU", "LTSSMState": "L0"}]}

# RESP CPU
RESP_CPU = {
    "deviceID": "0001",
    "type": "CPU",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": True,
    "usageRate": 123.45,
    "user": 67.89,
    "system": 1.23,
    "wait": 4.56,
    "idle": 7.89,
    "CPUWatts": 12345,
    "metricBandwidthPercent": 62,
    "metricOperatingSpeedMHz": 2400,
    "metricCaches": [
        {
            "miss": 0.12,
            "missesPerInstruction": 0.00088,
            "hitRatio": 0.719,
            "occupancyBytes": 3030144,
            "occupancyPercent": 90.1,
        }
    ],
    "metricCoreMetrics": [
        {
            "coreID": "core0",
            "instructionsPerCycle": 1.16,
            "coreCaches": [{"occupancyBytes": 198231, "occupancyPercent": 77.4}],
        }
    ],
    "metricLocalMemoryBandwidthBytes": 18253611008,
    "metricRemoteMemoryBandwidthBytes": 81788928,
    "metricEnergyJoules": {
        "sensorResetTime": "2023-11-20T04:14:00Z",
        "sensingInterval": 5,
        "readingTime": "2023-11-20T05:15:00Z",
        "reading": 25,
    },
    "LTSSMState": "L0",
}

# RESP CPU int value
RESP_CPU_INT = {
    "deviceID": "0001",
    "type": "CPU",
    "metricBandwidthPercent": 10,
    "metricCaches": [{"miss": 0, "missesPerInstruction": 1, "hitRatio": 2, "occupancyPercent": 3}],
    "metricCoreMetrics": [{"instructionsPerCycle": 5, "coreCaches": [{"occupancyPercent": 6}]}],
    "metricEnergyJoules": {"reading": 7},
}

# RESP CPU float value
RESP_CPU_FLOAT = {
    "deviceID": "0001",
    "type": "CPU",
    "metricBandwidthPercent": 0.01,
    "metricCaches": [{"miss": 0.02, "missesPerInstruction": 0.03, "hitRatio": 0.04, "occupancyPercent": 10.05}],
    "metricCoreMetrics": [{"instructionsPerCycle": 1.06, "coreCaches": [{"occupancyPercent": 20.07}]}],
    "metricEnergyJoules": {"reading": 30.08},
}

# Agent memory
AGENT_DATA_MEMORY = {
    "data": [
        {
            "type": "memory",
            "usedMemory": 12345,
            "swap": 65789,
        }
    ]
}

# OOB memory
OOB_DATA_MEMORY = {
    "devices": [
        {
            "type": "memory",
            "deviceID": "0001",
            "schema": {"PowerState": "On", "PowerCapability": True, "Status": {"Health": "OK", "State": "Enabled"}},
            "metric": {
                "BandwidthPercent": 62,
                "BlockSizeBytes": 512,
                "OperatingSpeedMHz": 2400,
                "HealthData": {
                    "DataLossDetected": False,
                    "LastShutdownSuccess": True,
                    "PerformanceDegraded": False,
                    "PredictedMediaLifeLeftPercent": 50,
                },
            },
            "environment": {
                "Sensor": {
                    "SensorResetTime": "2023-11-20T04:14:00Z",
                    "SensingInterval": "PT5S",
                    "ReadingTime": "2023-11-20T05:15:00Z",
                },
                "EnergyJoules": {
                    "Reading": 25,
                },
            },
        }
    ]
}

# OOB memory int value
OOB_DATA_MEMORY_INT = {
    "devices": [
        {
            "type": "memory",
            "deviceID": "0001",
            "metric": {
                "BandwidthPercent": 10,
                "HealthData": {"PredictedMediaLifeLeftPercent": 20},
            },
            "environment": {"EnergyJoules": {"Reading": 30}},
        }
    ]
}

# OOB memory float value
OOB_DATA_MEMORY_FLOAT = {
    "devices": [
        {
            "type": "memory",
            "deviceID": "0001",
            "metric": {
                "BandwidthPercent": 10.01,
                "HealthData": {"PredictedMediaLifeLeftPercent": 20.02},
            },
            "environment": {"EnergyJoules": {"Reading": 30.03}},
        }
    ]
}

# FM_DATA memory
FM_DATA_MEMORY = {
    "data": [
        {
            "deviceID": "1001",
            "type": "memory",
            "LTSSMState": "L0",
            "capacity": {"volatile": 1073741824, "persistent": 0, "total": 1073741824},
        }
    ]
}

# RESP MEMORY
RESP_MEMORY = {
    "deviceID": "1001",
    "type": "memory",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": True,
    "usedMemory": 12345,
    "swap": 65789,
    "metricBandwidthPercent": 62,
    "metricBlockSizeBytes": 512,
    "metricOperatingSpeedMHz": 2400,
    "metricHealthData": {
        "dataLossDetected": False,
        "lastShutdownSuccess": True,
        "performanceDegraded": False,
        "predictedMediaLifeLeftPercent": 50,
    },
    "metricEnergyJoules": {
        "sensorResetTime": "2023-11-20T04:14:00Z",
        "sensingInterval": 5,
        "readingTime": "2023-11-20T05:15:00Z",
        "reading": 25,
    },
    "CXLCapacity": {"total": 1073741824, "volatile": 1073741824, "persistent": 0},
    "LTSSMState": "L0",
}

# RESP MEMORY int value
RESP_MEMORY_INT = {
    "deviceID": "1001",
    "type": "memory",
    "metricBandwidthPercent": 10,
    "metricHealthData": {"predictedMediaLifeLeftPercent": 20},
    "metricEnergyJoules": {"reading": 30},
}

# RESP MEMORY float value
RESP_MEMORY_FLOAT = {
    "deviceID": "1001",
    "type": "memory",
    "metricBandwidthPercent": 10.01,
    "metricHealthData": {"predictedMediaLifeLeftPercent": 20.02},
    "metricEnergyJoules": {"reading": 30.03},
}

# Agent storage
AGENT_DATA_STORAGE = {
    "data": [
        {
            "type": "storage",
            "disk": {
                "amountUsedDisk": 1,
                "usageIO": {
                    "readCount": 2,
                    "writeCount": 3,
                    "readBytes": 4,
                    "writeBytes": 5,
                    "readTime": 6,
                    "writeTime": 7,
                    "readMergedCount": 8,
                    "writeMergedCount": 9,
                    "busyRate": 10.5,
                },
            },
        }
    ]
}

# OOB_DATA storage
OOB_DATA_STORAGE = {
    "devices": [
        {
            "type": "storage",
            "deviceID": "2001",
            "schema": {
                "Volume": {
                    "Capacity": {
                        "Data": {"AllocatedBytes": 1, "ConsumedBytes": 2, "GuaranteedBytes": 3, "ProvisionedBytes": 4},
                        "Metadata": {
                            "AllocatedBytes": 5,
                            "ConsumedBytes": 6,
                            "GuaranteedBytes": 7,
                            "ProvisionedBytes": 8,
                        },
                        "Snapshot": {
                            "AllocatedBytes": 9,
                            "ConsumedBytes": 10,
                            "GuaranteedBytes": 11,
                            "ProvisionedBytes": 12,
                        },
                    },
                    "RemainingCapacityPercent": 50,
                },
                "Drive": {
                    "NegotiatedSpeedGbs": 12.24,
                    "PowerState": "On",
                    "PowerCapability": True,
                    "Status": {"Health": "OK", "State": "Enabled"},
                },
            },
            "environment": {
                "Sensor": {
                    "SensorResetTime": "2023-11-20T04:14:00Z",
                    "SensingInterval": "PT5S",
                    "ReadingTime": "2023-11-20T05:15:00Z",
                },
                "EnergyJoules": {
                    "Reading": 25,
                },
            },
        }
    ]
}

# OOB_DATA storage int value
OOB_DATA_STORAGE_INT = {
    "devices": [{"type": "storage", "deviceID": "2001", "environment": {"EnergyJoules": {"Reading": 10}}}]
}

# OOB_DATA storage float value
OOB_DATA_STORAGE_FLOAT = {
    "devices": [{"type": "storage", "deviceID": "2001", "environment": {"EnergyJoules": {"Reading": 10.01}}}]
}

# FM_DATA storage
FM_DATA_STORAGE = {"data": [{"deviceID": "2001", "type": "storage", "LTSSMState": "L0"}]}

# RESP STORAGE
RESP_STORAGE = {
    "deviceID": "2001",
    "type": "storage",
    "volumeCapacity": {
        "data": {"allocatedBytes": 1, "consumedBytes": 2, "guaranteedBytes": 3, "provisionedBytes": 4},
        "metadata": {"allocatedBytes": 5, "consumedBytes": 6, "guaranteedBytes": 7, "provisionedBytes": 8},
        "snapshot": {"allocatedBytes": 9, "consumedBytes": 10, "guaranteedBytes": 11, "provisionedBytes": 12},
    },
    "volumeRemainingCapacityPercent": 50,
    "driveNegotiatedSpeedGbs": 12.24,
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": True,
    "disk": {
        "amountUsedDisk": 1,
        "usageIO": {
            "readCount": 2,
            "writeCount": 3,
            "readBytes": 4,
            "writeBytes": 5,
            "readTime": 6,
            "writeTime": 7,
            "readMergedCount": 8,
            "writeMergedCount": 9,
            "busyRate": 10.5,
        },
    },
    "metricEnergyJoules": {
        "sensorResetTime": "2023-11-20T04:14:00Z",
        "sensingInterval": 5,
        "readingTime": "2023-11-20T05:15:00Z",
        "reading": 25,
    },
    "LTSSMState": "L0",
}

# RESP STORAGE int value
RESP_STORAGE_INT = {"deviceID": "2001", "type": "storage", "metricEnergyJoules": {"reading": 10}}

# RESP STORAGE float value
RESP_STORAGE_FLOAT = {"deviceID": "2001", "type": "storage", "metricEnergyJoules": {"reading": 10.01}}

# Agent NIC
AGENT_DATA_NIC = {
    "data": [
        {
            "type": "networkInterface",
            "networkInterfaceInformation": [
                {
                    "networkTraffic": {
                        "receivePackets": 2,
                        "transmitPackets": 3,
                        "bytesSent": 4,
                        "bytesRecv": 5,
                        "errin": 6,
                        "errout": 7,
                        "dropin": 8,
                        "dropout": 9,
                    },
                    "networkSpeed": 1,
                }
            ],
        }
    ]
}

# OOB_DATA NIC
OOB_DATA_NIC = {
    "devices": [
        {
            "type": "networkInterface",
            "deviceID": "3001",
            "schema": {
                "NetworkDeviceFunctions": {"DeviceEnabled": True},
                "Network": {
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "PowerState": "On",
                    "PowerCapability": False,
                },
            },
            "metric": {
                "Network": {"CPUCorePercent": 8.35, "HostBusRXPercent": 35.53, "HostBusTXPercent": 14.17},
                "NetworkDeviceFunctions": {
                    "RXAvgQueueDepthPercent": 21.2,
                    "TXAvgQueueDepthPercent": 13.7,
                    "RXBytes": 1,
                    "RXFrames": 2,
                    "TXBytes": 3,
                    "TXFrames": 4,
                },
            },
            "environment": {
                "Sensor": {
                    "SensorResetTime": "2023-11-20T04:14:00Z",
                    "SensingInterval": "PT5S",
                    "ReadingTime": "2023-11-20T05:15:00Z",
                },
                "EnergyJoules": {
                    "Reading": 25,
                },
            },
        }
    ]
}

# OOB_DATA NIC int value
OOB_DATA_NIC_INT = {
    "devices": [
        {
            "type": "networkInterface",
            "deviceID": "3001",
            "metric": {
                "Network": {"CPUCorePercent": 10, "HostBusRXPercent": 20, "HostBusTXPercent": 30},
                "NetworkDeviceFunctions": {"RXAvgQueueDepthPercent": 40, "TXAvgQueueDepthPercent": 50},
            },
            "environment": {"EnergyJoules": {"Reading": 60}},
        }
    ]
}

# OOB_DATA NIC float value
OOB_DATA_NIC_FLOAT = {
    "devices": [
        {
            "type": "networkInterface",
            "deviceID": "3001",
            "metric": {
                "Network": {"CPUCorePercent": 10.01, "HostBusRXPercent": 20.02, "HostBusTXPercent": 30.03},
                "NetworkDeviceFunctions": {"RXAvgQueueDepthPercent": 40.04, "TXAvgQueueDepthPercent": 50.05},
            },
            "environment": {"EnergyJoules": {"Reading": 60.06}},
        }
    ]
}

# FM_DATA networkInterface
FM_DATA_NIC = {"data": [{"deviceID": "3001", "type": "networkInterface", "LTSSMState": "L0"}]}

# RESP NIC
RESP_NIC = {
    "deviceID": "3001",
    "type": "networkInterface",
    "deviceEnabled": True,
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": False,
    "networkInterfaceInformation": [
        {
            "networkSpeed": 1,
            "networkTraffic": {
                "receivePackets": 2,
                "transmitPackets": 3,
                "bytesSent": 4,
                "bytesRecv": 5,
                "errin": 6,
                "errout": 7,
                "dropin": 8,
                "dropout": 9,
            },
        }
    ],
    "metricsCPUCorePercent": 8.35,
    "metricsHostBusRXPercent": 35.53,
    "metricsHostBusTXPercent": 14.17,
    "metricsRXAvgQueueDepthPercent": 21.2,
    "metricsTXAvgQueueDepthPercent": 13.7,
    "metricsRXBytes": 1,
    "metricsRXFrames": 2,
    "metricsTXBytes": 3,
    "metricsTXFrames": 4,
    "metricEnergyJoules": {
        "sensorResetTime": "2023-11-20T04:14:00Z",
        "sensingInterval": 5,
        "readingTime": "2023-11-20T05:15:00Z",
        "reading": 25,
    },
    "LTSSMState": "L0",
}

# RESP NIC int value
RESP_NIC_INT = {
    "deviceID": "3001",
    "type": "networkInterface",
    "metricsCPUCorePercent": 10,
    "metricsHostBusRXPercent": 20,
    "metricsHostBusTXPercent": 30,
    "metricsRXAvgQueueDepthPercent": 40,
    "metricsTXAvgQueueDepthPercent": 50,
    "metricEnergyJoules": {"reading": 60},
}

# RESP NIC float value
RESP_NIC_FLOAT = {
    "deviceID": "3001",
    "type": "networkInterface",
    "metricsCPUCorePercent": 10.01,
    "metricsHostBusRXPercent": 20.02,
    "metricsHostBusTXPercent": 30.03,
    "metricsRXAvgQueueDepthPercent": 40.04,
    "metricsTXAvgQueueDepthPercent": 50.05,
    "metricEnergyJoules": {"reading": 60.06},
}

# OOB GPU
OOB_DATA_GPU = {
    "devices": [
        {
            "type": "GPU",
            "deviceID": "4001",
            "schema": {"PowerState": "On", "PowerCapability": True, "Status": {"Health": "OK", "State": "Enabled"}},
            "metric": {
                "BandwidthPercent": 62,
                "OperatingSpeedMHz": 2400,
                "Cache": [
                    {
                        "CacheMiss": 0.12,
                        "CacheMissesPerInstruction": 0.00088,
                        "HitRatio": 0.719,
                        "OccupancyBytes": 3030144,
                        "OccupancyPercent": 90.1,
                    }
                ],
                "CoreMetrics": [
                    {
                        "CoreId": "core0",
                        "InstructionsPerCycle": 1.16,
                        "CoreCache": [{"OccupancyBytes": 198231, "OccupancyPercent": 77.4}],
                    }
                ],
                "LocalMemoryBandwidthBytes": 18253611008,
                "RemoteMemoryBandwidthBytes": 81788928,
            },
            "environment": {
                "Sensor": {
                    "SensorResetTime": "2023-11-20T04:14:00Z",  # NOSONAR
                    "SensingInterval": "PT5S",
                    "ReadingTime": "2023-11-20T05:15:00Z",  # NOSONAR
                },
                "EnergyJoules": {
                    "Reading": 25,
                },
            },
        }
    ]
}

# OOB GPU int value
OOB_DATA_GPU_INT = {
    "devices": [
        {
            "type": "GPU",
            "deviceID": "4001",
            "metric": {
                "BandwidthPercent": 10,
                "Cache": [{"CacheMiss": 0, "CacheMissesPerInstruction": 1, "HitRatio": 2, "OccupancyPercent": 3}],
                "CoreMetrics": [{"InstructionsPerCycle": 5, "CoreCache": [{"OccupancyPercent": 6}]}],
            },
            "environment": {"EnergyJoules": {"Reading": 7}},
        }
    ]
}

# OOB GPU float value
OOB_DATA_GPU_FLOAT = {
    "devices": [
        {
            "type": "GPU",
            "deviceID": "4001",
            "metric": {
                "BandwidthPercent": 0.01,
                "Cache": [
                    {"CacheMiss": 0.02, "CacheMissesPerInstruction": 0.03, "HitRatio": 0.04, "OccupancyPercent": 10.05}
                ],
                "CoreMetrics": [{"InstructionsPerCycle": 1.06, "CoreCache": [{"OccupancyPercent": 20.07}]}],
            },
            "environment": {"EnergyJoules": {"Reading": 30.08}},
        }
    ]
}

# FM_DATA GPU
FM_DATA_GPU = {"data": [{"deviceID": "4001", "type": "GPU", "LTSSMState": "L0"}]}

# RESP GPU
RESP_GPU = {
    "deviceID": "4001",
    "type": "GPU",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": True,
    "metricBandwidthPercent": 62,
    "metricOperatingSpeedMHz": 2400,
    "metricCaches": [
        {
            "miss": 0.12,
            "missesPerInstruction": 0.00088,
            "hitRatio": 0.719,
            "occupancyBytes": 3030144,
            "occupancyPercent": 90.1,
        }
    ],
    "metricCoreMetrics": [
        {
            "coreID": "core0",
            "instructionsPerCycle": 1.16,
            "coreCaches": [{"occupancyBytes": 198231, "occupancyPercent": 77.4}],
        }
    ],
    "metricLocalMemoryBandwidthBytes": 18253611008,
    "metricRemoteMemoryBandwidthBytes": 81788928,
    "metricEnergyJoules": {
        "sensorResetTime": "2023-11-20T04:14:00Z",
        "sensingInterval": 5,
        "readingTime": "2023-11-20T05:15:00Z",
        "reading": 25,
    },
    "LTSSMState": "L0",
}

# RESP GPU int value
RESP_GPU_INT = {
    "deviceID": "4001",
    "type": "GPU",
    "metricBandwidthPercent": 10,
    "metricCaches": [{"miss": 0, "missesPerInstruction": 1, "hitRatio": 2, "occupancyPercent": 3}],
    "metricCoreMetrics": [{"instructionsPerCycle": 5, "coreCaches": [{"occupancyPercent": 6}]}],
    "metricEnergyJoules": {"reading": 7},
}

# RESP GPU float value
RESP_GPU_FLOAT = {
    "deviceID": "4001",
    "type": "GPU",
    "metricBandwidthPercent": 0.01,
    "metricCaches": [{"miss": 0.02, "missesPerInstruction": 0.03, "hitRatio": 0.04, "occupancyPercent": 10.05}],
    "metricCoreMetrics": [{"instructionsPerCycle": 1.06, "coreCaches": [{"occupancyPercent": 20.07}]}],
    "metricEnergyJoules": {"reading": 30.08},
}

# RESP graphicController
RESP_GC = {"deviceID": "5001", "type": "graphicController"}

# Mapping table file
MAPPING_TABLE_FILE = {
    "fm": {"spec": "test_info_core_fm_spec_mapping.json", "metric": "test_info_core_fm_metric_mapping.json"},
    "oob": {"spec": "test_info_core_oob_spec_mapping.json", "metric": "test_info_core_oob_metric_mapping.json"},
    "agent": {"metric": "test_info_core_agent_metric_mapping.json"},
}


def _log_contains(record, level, message) -> bool:
    """Comparing log contents"""
    return next(filter(lambda x: (x[1] == level) and (message in x[2]), record), None) is not None


def _get_metric_info(mocker, device_id, device_type, agent_data, oob_data, fm_data, cut_timestamp):
    """Get Information"""

    def mock_device_id_to_device_type(_):
        return device_type

    def mock_agent(_, __, ___):
        return agent_data

    def mock_oob(_, __):
        return oob_data

    def mock_fm(_, __):
        return fm_data

    def mock_verify_agent_access(_, __, ___, ____):
        return True, "0001"

    # Current path
    current_path = os.path.dirname(os.path.abspath(__file__))

    # Replace the path of the mapping table file (constant) with the path of the test mapping table file.
    mapping_path = current_path
    mocker.patch.object(settings, "MAPPING_TABLE_PATH", mapping_path)

    mocker.patch.object(settings, "HW_CONTROL_AGENT_ENABLED", True)

    # Replace the mapping table file (constant) with the test mapping table file.
    mocker.patch.dict("app.core.info.info_const.MAPPING_TABLE_FILE", MAPPING_TABLE_FILE)
    # Reading the mapping table file used in the information retrieval process (response generation)
    load_mapping_table()

    # Replace the device information retrieval for device ID management.
    mocker.patch(
        "app.common.deviceIdManager.device_id_base.device_id_to_device_type",  # NOSONAR
        side_effect=mock_device_id_to_device_type,
    )

    # Replace obtaining agent information with a mock
    mocker.patch("app.core.info.metric_agent.InfoMetricAgent.get_metric_agent", side_effect=mock_agent)  # NOSONAR

    # Replace OOB metric information retrieval with a mock
    mocker.patch("app.core.info.spec_oob.GetSpecOOBInfo.get_metric_oob", side_effect=mock_oob)

    # Replace the acquisition of FM device information with a mock.
    mocker.patch("app.core.info.spec_fm.GetSpecFMInfo.get_spec_fm", side_effect=mock_fm)

    # Replace the Agent connection availability with a mock.
    mocker.patch("app.core.info.info_core.InformationCore._verify_agent_access", side_effect=mock_verify_agent_access)

    get_information = InformationCore()
    metric_data, errors = get_information.get_metric_info(device_id)

    # Return without the current date and time.
    if cut_timestamp:
        return {key: val for key, val in metric_data.items() if key != RESP_ITEM_NAME_TIME_STAMP}, errors
    else:
        return metric_data, errors


def test_get_metric_info_time_stamp(mocker):
    """Test infoTimestamp"""
    # Extract infoTimestamp (using 0001(CPU) as a representative)
    metric_data, _ = _get_metric_info(mocker, "0001", "CPU", AGENT_DATA_CPU, OOB_DATA_CPU, None, False)
    info_time_stamp_str = metric_data.get(RESP_ITEM_NAME_TIME_STAMP)

    # Convert to datetime.
    info_time_stamp_datetime = datetime.datetime.strptime(str(info_time_stamp_str), TIME_STAMP_FORMAT)

    # Difference from the current date and time
    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    diff_time = abs(now - info_time_stamp_datetime)

    # If the difference is within one minute, it is determined that the current date and time
    # have been correctly retrieved.
    assert diff_time <= datetime.timedelta(minutes=1)


def test_get_metric_info_cpu(mocker):
    """Test Get metric CPU"""
    metric_data, errors = _get_metric_info(mocker, "0001", "CPU", AGENT_DATA_CPU, OOB_DATA_CPU, FM_DATA_CPU, True)
    # Return value verification.
    assert (RESP_CPU, []) == (metric_data, errors)


def test_get_metric_info_cpu_int(mocker):
    """Test Get metric CPU int value"""
    metric_data, errors = _get_metric_info(mocker, "0001", "CPU", None, OOB_DATA_CPU_INT, None, True)
    # Return value verification.
    assert (RESP_CPU_INT, []) == (metric_data, errors)


def test_get_metric_info_cpu_float(mocker):
    """Test Get metric CPU float value"""
    metric_data, errors = _get_metric_info(mocker, "0001", "CPU", None, OOB_DATA_CPU_FLOAT, None, True)
    # Return value verification.
    assert (RESP_CPU_FLOAT, []) == (metric_data, errors)


def test_get_metric_info_memory(mocker):
    """Test Get metric memory"""
    metric_data, errors = _get_metric_info(
        mocker, "1001", "memory", AGENT_DATA_MEMORY, OOB_DATA_MEMORY, FM_DATA_MEMORY, True
    )
    # Return value verification.
    assert (RESP_MEMORY, []) == (metric_data, errors)


def test_get_metric_info_memory_int(mocker):
    """Test Get metric memory int value"""
    metric_data, errors = _get_metric_info(mocker, "1001", "memory", None, OOB_DATA_MEMORY_INT, None, True)
    # Return value verification.
    assert (RESP_MEMORY_INT, []) == (metric_data, errors)


def test_get_metric_info_memory_float(mocker):
    """Test Get metric memory float value"""
    metric_data, errors = _get_metric_info(mocker, "1001", "memory", None, OOB_DATA_MEMORY_FLOAT, None, True)
    # Return value verification.
    assert (RESP_MEMORY_FLOAT, []) == (metric_data, errors)


def test_get_metric_info_storage(mocker):
    """Test Get metric storage"""
    metric_data, errors = _get_metric_info(
        mocker, "2001", "storage", AGENT_DATA_STORAGE, OOB_DATA_STORAGE, FM_DATA_STORAGE, True
    )
    # Return value verification.
    assert (RESP_STORAGE, []) == (metric_data, errors)


def test_get_metric_info_storage_int(mocker):
    """Test Get metric storage int value"""
    metric_data, errors = _get_metric_info(mocker, "2001", "storage", None, OOB_DATA_STORAGE_INT, None, True)
    # Return value verification.
    assert (RESP_STORAGE_INT, []) == (metric_data, errors)


def test_get_metric_info_storage_float(mocker):
    """Test Get metric storage float value"""
    metric_data, errors = _get_metric_info(mocker, "2001", "storage", None, OOB_DATA_STORAGE_FLOAT, None, True)
    # Return value verification.
    assert (RESP_STORAGE_FLOAT, []) == (metric_data, errors)


def test_get_metric_info_nic(mocker):
    """Test Get metric NIC"""
    metric_data, errors = _get_metric_info(
        mocker, "3001", "networkInterface", AGENT_DATA_NIC, OOB_DATA_NIC, FM_DATA_NIC, True
    )
    # Return value verification.
    assert (RESP_NIC, []) == (metric_data, errors)


def test_get_metric_info_nic_int(mocker):
    """Test Get metric NIC int value"""
    metric_data, errors = _get_metric_info(mocker, "3001", "networkInterface", None, OOB_DATA_NIC_INT, None, True)
    # Return value verification.
    assert (RESP_NIC_INT, []) == (metric_data, errors)


def test_get_metric_info_nic_float(mocker):
    """Test Get metric NIC float value"""
    metric_data, errors = _get_metric_info(mocker, "3001", "networkInterface", None, OOB_DATA_NIC_FLOAT, None, True)
    # Return value verification.
    assert (RESP_NIC_FLOAT, []) == (metric_data, errors)


def test_get_metric_info_gpu(mocker):
    """Test Get metric GPU"""
    metric_data, errors = _get_metric_info(mocker, "4001", "GPU", None, OOB_DATA_GPU, FM_DATA_GPU, True)
    # Return value verification.
    assert (RESP_GPU, []) == (metric_data, errors)


def test_get_metric_info_gpu_int(mocker):
    """Test Get metric GPU int value"""
    metric_data, errors = _get_metric_info(mocker, "4001", "GPU", None, OOB_DATA_GPU_INT, None, True)
    # Return value verification.
    assert (RESP_GPU_INT, []) == (metric_data, errors)


def test_get_metric_info_gpu_float(mocker):
    """Test Get metric GPU float value"""
    metric_data, errors = _get_metric_info(mocker, "4001", "GPU", None, OOB_DATA_GPU_FLOAT, None, True)
    # Return value verification.
    assert (RESP_GPU_FLOAT, []) == (metric_data, errors)


def test_get_metric_info_gc(mocker):
    """Test Get metric graphicController"""
    metric_data, errors = _get_metric_info(mocker, "5001", "graphicController", None, None, None, False)
    # Return value verification.
    assert (None, []) == (metric_data, errors)


def test_get_metric_info_other_device_type(mocker, caplog):
    """Test Get metric Information other device type"""
    metric_data, errors = _get_metric_info(mocker, "9001", None, AGENT_DATA_CPU, OOB_DATA_CPU, FM_DATA_CPU, False)

    assert metric_data is None

    assert errors == [
        {
            "errorCode": "EF010BAS000",
            "errorMessage": "The server encountered an internal error. "
            "Unable to retrieve the device type corresponding to Device ID: 9001.",
        }
    ]

    assert _log_contains(
        caplog.record_tuples,
        logging.WARNING,
        "W00006: Device information not found: Unable to retrieve the device type corresponding to Device ID: 9001.",
    )


def test_get_metric_info_create_metric_info_create_resp_from_mapping_exception_oob(mocker, caplog):
    """create_metric_info create_resp_from_mapping exception oob"""

    oob_data = {"devices": [{"type": "CPU", "deviceID": "0001"}]}

    # Current path
    current_path = os.path.dirname(os.path.abspath(__file__))

    # Replace the path of the mapping table file (constant) with the path of the test mapping table file.
    mapping_path = current_path
    mocker.patch.object(settings, "MAPPING_TABLE_PATH", mapping_path)

    # Replace the mapping table file (constant) with the test mapping table file.
    mocker.patch.dict("app.core.info.info_const.MAPPING_TABLE_FILE", MAPPING_TABLE_FILE)
    # Loading the mapping table file used in the information retrieval process (response generation)
    load_mapping_table()

    mocker.patch("app.core.info.info_core.info_utils.create_resp_from_mapping", side_effect=InternalHwControlError)

    get_information = InformationCore()
    with pytest.raises(BaseHwControlError):
        # Specify the CPU as a representative.
        get_information._create_metric_info("0001", "CPU", None, oob_data, None)  # pylint: disable=protected-access
    assert _log_contains(caplog.record_tuples, logging.WARNING, "Device ID:0001")


def test_get_metric_info_create_metric_info_create_resp_from_mapping_exception_fm(mocker, caplog):
    """create_metric_info create_resp_from_mapping exception oob"""

    fm_data = {"data": [{"deviceID": "0001", "type": "CPU"}]}

    # Current path
    current_path = os.path.dirname(os.path.abspath(__file__))

    # Replace the path of the mapping table file (constant) with the path of the test mapping table file.
    mapping_path = current_path
    mocker.patch.object(settings, "MAPPING_TABLE_PATH", mapping_path)

    # Replace the mapping table file (constant) with the test mapping table file.
    mocker.patch.dict("app.core.info.info_const.MAPPING_TABLE_FILE", MAPPING_TABLE_FILE)
    # Loading the mapping table file used in the information retrieval process (response generation)
    load_mapping_table()

    mocker.patch("app.core.info.info_core.info_utils.create_resp_from_mapping", side_effect=InternalHwControlError)

    get_information = InformationCore()
    with pytest.raises(BaseHwControlError):
        # Specify the CPU as a representative.
        get_information._create_metric_info("0001", "CPU", None, None, fm_data)  # pylint: disable=protected-access
    assert _log_contains(caplog.record_tuples, logging.WARNING, "Device ID:0001")


def test_get_metric_info_create_metric_info_create_resp_from_mapping_exception_agent(mocker, caplog):
    """create_metric_info create_resp_from_mapping exception oob"""

    agent_data = {"data": [{"type": "CPU"}]}

    # Current path
    current_path = os.path.dirname(os.path.abspath(__file__))

    # Replace the path of the mapping table file (constant) with the path of the test mapping table file.
    mapping_path = current_path
    mocker.patch.object(settings, "MAPPING_TABLE_PATH", mapping_path)

    # Replace the mapping table file (constant) with the test mapping table file.
    mocker.patch.dict("app.core.info.info_const.MAPPING_TABLE_FILE", MAPPING_TABLE_FILE)
    # Loading the mapping table file used in the information retrieval process (response generation)
    load_mapping_table()

    mocker.patch("app.core.info.info_core.info_utils.create_resp_from_mapping", side_effect=InternalHwControlError)

    get_information = InformationCore()
    with pytest.raises(BaseHwControlError):
        # Specify the CPU as a representative.
        get_information._create_metric_info("0001", "CPU", agent_data, None, None)  # pylint: disable=protected-access
    assert _log_contains(caplog.record_tuples, logging.WARNING, "Device ID:0001")


def test_get_metric_info_base_exception(mocker):
    """metric exception"""

    def mock_device_id_to_device_type(_):
        return "CPU"

    # Replace device information retrieval for device ID management.
    mocker.patch(
        "app.common.deviceIdManager.device_id_base.device_id_to_device_type", side_effect=mock_device_id_to_device_type
    )

    mocker.patch("app.core.info.spec_oob.GetSpecOOBInfo.get_metric_oob", side_effect=BaseHwControlError)
    mocker.patch.object(settings, "HW_CONTROL_AGENT_ENABLED", True)
    get_information = InformationCore()
    _, errors = get_information.get_metric_info("0001")

    err_msg = "The server encountered an internal error and was unable to complete your request."
    assert {"errorCode": "CF000BAS000", "errorMessage": err_msg} in errors


def test_get_metric_info_verify_agent_access_base_exception(mocker):
    """metric exception"""

    def mock_device_id_to_device_type(_):
        return "CPU"

    # Replace the device information retrieval in device ID management.
    mocker.patch(
        "app.common.deviceIdManager.device_id_base.device_id_to_device_type", side_effect=mock_device_id_to_device_type
    )

    mocker.patch("app.core.info.info_core.InformationCore._verify_agent_access", side_effect=BaseHwControlError)

    mocker.patch.object(settings, "HW_CONTROL_AGENT_ENABLED", True)

    get_information = InformationCore()
    _, errors = get_information.get_metric_info("0001")

    err_msg = "The server encountered an internal error and was unable to complete your request."
    assert {"errorCode": "CF000BAS000", "errorMessage": err_msg} in errors


def test_get_metric_info_create_metric_info_base_exception(mocker):
    """metric exception"""
    mocker.patch("app.core.info.info_core.InformationCore._create_metric_info", side_effect=BaseHwControlError)

    _, errors = _get_metric_info(mocker, "0001", "CPU", AGENT_DATA_CPU, OOB_DATA_CPU, FM_DATA_CPU, False)

    err_msg = "The server encountered an internal error and was unable to complete your request."
    assert {"errorCode": "CF000BAS000", "errorMessage": err_msg} in errors


def test_get_metric_info_create_metric_info_device_type_none():
    """create_metric_info device type none"""
    get_information = InformationCore()
    resp = get_information._create_metric_info("0001", None, {}, {}, {})  # pylint: disable=protected-access
    assert {"deviceID": "0001", "type": None} == resp

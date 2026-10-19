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

import copy
import datetime
import json
import logging
import os

import pytest

from app.common.basic_exceptions import (
    BaseHWControlError,
    DeviceNotFoundHWControlError,
    InternalHWControlError,
)
from app.common.constants import TIME_STAMP_FORMAT
from app.common.settings import settings
from app.core.info.info_const import RESP_ITEM_NAME_CONSTRAINTS
from app.core.info.info_core import InformationCore
from app.core.info.info_utils import load_mapping_table

# Response Item Name Current Date and Time
RESP_ITEM_NAME_TIME_STAMP = "infoTimestamp"

# OOB_DATA CPU Link present
OOB_DATA_CPU_LINK = {
    "devices": [
        {
            "type": "CPU",
            "deviceID": "0001",
            "schema": {
                "Name": "Processor",
                "Id": "PROC-0001",
                "ProcessorType": "CPU",
                "ProcessorArchitecture": "x86",
                "InstructionSet": "x86-64",
                "Manufacturer": "Intel(R) Corporation",
                "Model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
                "ProcessorId": {
                    "VendorId": "GenuineIntel",
                    "IdentificationRegisters": "0x34AC34DC8901274A",
                    "EffectiveFamily": "0x42",
                    "EffectiveModel": "0x61",
                    "Step": "0x1",
                    "MicrocodeInfo": "0x429943",
                    "ProtectedIdentificationNumber": "123456",
                },
                "PowerState": "On",
                "PowerCapability": True,
                "ProcessorIndex": "xxx",
                "Replaceable": True,
                "SerialNumber": "PROCESSOR1",
                "Socket": "CPU 1",
                "socketNum": 1,
                "attribute": {
                    "deviceSpecificInformation": {
                        "hostName": "sv01",
                        "bmcHostName": "bmc-sv01",
                        "id": "0P96F00",
                        "name": "Quadro P400",
                        "firmwareversion": "86.07.6B.00.01",
                    },
                },
                "Links": {
                    "Chassis": {"@odata.id": "/redfish/v1/Chassis/Chassis-1"},
                    "ConnectedProcessors": {"@odata.id": "/redfish/v1/System/System-1/Processors/PROC-0001"},
                    "GraphicsController": {"@odata.id": "{rb}{suffix}/{suffix_id}/GraphicsControllers/{gs_id}"},
                    "NetworkDeviceFunctions": {
                        "@odata.id": "{rb}Chassis/{chassis_id}/NetworkAdapters/ \
                              {NetworkAdapterId}/NetworkDeviceFunctions/{NetworkDeviceFunctionId}"
                    },
                    "FabricAdapters": {"@odata.id": "{rb}Chassis/{chassis_id}/FabricAdapters/{FabricAdaptersId}"},
                    "PCIeDevice": {"@odata.id": "{rb}{suffix}/{suffix_id}/PCIeDevices/{PCIeDeviceId}"},
                    "Memory": [{"@odata.id": "/redfish/v1/Chassis/Chassis-1/Memory/MEM-1001"}],
                },
                "MaxSpeedMHz": 2200,
                "TotalCores": 8,
                "TotalThreads": 16,
                "TotalEnabledCores": 8,
                "BaseSpeedMHz": 1200,
                "OperatingSpeedMHz": 1000,
                "TDPWatts": 100,
                "ProcessorMemory": [
                    {"CapacityMiB": 123, "IntegratedMemory": True, "MemoryType": "DDR", "SpeedMHz": 1200}
                ],
                "MemorySummary": {
                    "MemoryMirroring": None,
                    "Metrics": {"@odata.id": "{rb}{suffix}/{suffix_id}/Memory/{memory_id}/MemoryMetrics"},
                    "Status": {},
                    "TotalCacheSizeMiB": 4096,
                    "TotalMemorySizeMiB": 8192,
                    "ECCModeEnabled": True,
                },
                "Metrics": {"@odata.id": "{rb}{suffix}/{suffix_id}/Processors/{ProcessorId}/ProcessorMetrics"},
                "EnvironmentMetrics": {
                    "@odata.id": "{rb}{suffix}/{suffix_id}/Processors/{ProcessorId}/EnvironmentMetrics"
                },
                "Status": {"Health": "OK", "State": "Enabled"},
            },
            "link": [{"type": "memory", "deviceID": "1001"}],
            "time": "2023-07-06T05:55:55Z",
        }
    ]
}

# OOB_DATA CPU No Link
OOB_DATA_CPU_NO_LINK = {
    "devices": [
        {
            "type": "CPU",
            "deviceID": "0001",
            "schema": {
                "@odata.context": "/redfish/v1/$metadata#Processor.Processor",
                "@odata.type": "#Processor.1_0_0.Processor",
                "@odata.id": "/redfish/v1/System/System-1/Processors/PROC-0001",
                "Name": "Processor",
                "Id": "PROC-0001",
                "ProcessorType": "CPU",
                "ProcessorArchitecture": "x86",
                "InstructionSet": "x86-64",
                "Manufacturer": "Intel(R) Corporation",
                "Model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
                "ProcessorId": {
                    "VendorId": "GenuineIntel",
                    "IdentificationRegisters": "0x34AC34DC8901274A",
                    "EffectiveFamily": "0x42",
                    "EffectiveModel": "0x61",
                    "Step": "0x1",
                    "MicrocodeInfo": "0x429943",
                    "ProtectedIdentificationNumber": "123456",
                },
                "PowerState": "On",
                "PowerCapability": True,
                "ProcessorIndex": "xxx",
                "Replaceable": True,
                "SerialNumber": "PROCESSOR1",
                "Socket": "CPU 1",
                "socketNum": 1,
                "attribute": {
                    "deviceSpecificInformation": {
                        "hostName": "sv01",
                        "bmcHostName": "bmc-sv01",
                        "id": "0P96F00",
                        "name": "Quadro P400",
                        "firmwareversion": "86.07.6B.00.01",
                    },
                },
                "MaxSpeedMHz": 2200,
                "TotalCores": 8,
                "TotalThreads": 16,
                "TotalEnabledCores": 8,
                "BaseSpeedMHz": 1200,
                "OperatingSpeedMHz": 1000,
                "TDPWatts": 100,
                "ProcessorMemory": [
                    {"CapacityMiB": 123, "IntegratedMemory": True, "MemoryType": "DDR", "SpeedMHz": 1200}
                ],
                "MemorySummary": {
                    "MemoryMirroring": None,
                    "Metrics": {"@odata.id": "{rb}{suffix}/{suffix_id}/Memory/{memory_id}/MemoryMetrics"},
                    "Status": {},
                    "TotalCacheSizeMiB": 4096,
                    "TotalMemorySizeMiB": 8192,
                    "ECCModeEnabled": True,
                },
                "Metrics": {"@odata.id": "{rb}{suffix}/{suffix_id}/Processors/{ProcessorId}/ProcessorMetrics"},
                "EnvironmentMetrics": {
                    "@odata.id": "{rb}{suffix}/{suffix_id}/Processors/{ProcessorId}/EnvironmentMetrics"
                },
                "Status": {"Health": "OK", "State": "Enabled"},
            },
            "time": "2023-07-06T05:55:55Z",
        }
    ]
}

# FM_DATA CPU Link present
FM_DATA_CPU_LINK = {
    "data": [
        {
            "deviceID": "0001",
            "type": "CPU",
            "link": [{"deviceID": "2001", "type": "storage"}, {"deviceID": "3001", "type": "networkInterface"}],
            "devicePortList": [
                {
                    "fabricId": "NEC-01",
                    "LTSSMState": "L0",
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "USP",
                },
                {
                    "fabricId": "NEC-02",
                    "LTSSMState": "L2",
                    "switchId": "fmsw-02",
                    "switchPortNumber": "2",
                    "switchPortType": "USP",
                },
            ],
        }
    ]
}

# FM_DATA CPU multi Link present
FM_DATA_CPU_MULTI_LINK = {
    "data": [
        {
            "deviceID": "0001",
            "type": "CPU",
            "link": [{"deviceID": "2001", "type": "storage"}, {"deviceID": "3001", "type": "networkInterface"}],
            "devicePortList": [
                {
                    "fabricId": "NEC-01",
                    "LTSSMState": "L0",
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "USP",
                }
            ],
        },
        {
            "deviceID": "0001",
            "type": "CPU",
            "link": [{"deviceID": "2002", "type": "storage"}, {"deviceID": "3002", "type": "networkInterface"}],
            "devicePortList": [
                {
                    "fabricId": "NEC-02",
                    "LTSSMState": "L2",
                    "switchId": "fmsw-02",
                    "switchPortNumber": "2",
                    "switchPortType": "USP",
                }
            ],
        },
    ]
}

# FM_DATA CPU Link CPU
FM_DATA_CPU_LINK_CPU = {
    "data": [
        {
            "deviceID": "0001",
            "type": "CPU",
            "link": [{"deviceID": "0002", "type": "CPU"}],
            "devicePortList": [
                {
                    "fabricId": "NEC-01",
                    "LTSSMState": "L0",
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "USP",
                },
                {
                    "fabricId": "NEC-02",
                    "LTSSMState": "L2",
                    "switchId": "fmsw-02",
                    "switchPortNumber": "2",
                    "switchPortType": "USP",
                },
            ],
        }
    ]
}

# FM_DATA CPU No Link
FM_DATA_CPU_NO_LINK = {
    "data": [
        {
            "deviceID": "0001",
            "type": "CPU",
            "devicePortList": [
                {
                    "fabricId": "NEC-01",
                    "LTSSMState": "L0",
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "USP",
                },
                {
                    "fabricId": "NEC-02",
                    "LTSSMState": "L2",
                    "switchId": "fmsw-02",
                    "switchPortNumber": "2",
                    "switchPortType": "USP",
                },
            ],
        }
    ]
}

# RESP CPU Link present
RESP_CPU_LINK = {
    "deviceID": "0001",
    "type": "CPU",
    "attribute": {
        "deviceSpecificInformation": {
            "hostName": "sv01",
            "bmcHostName": "bmc-sv01",
            "id": "0P96F00",
            "name": "Quadro P400",
            "firmware_version": "86.07.6B.00.01",
        },
    },
    "baseSpeedMHz": 1200,
    "operatingSpeedMHz": 1000,
    "TDPWatts": 100,
    "totalCores": 8,
    "totalEnabledCores": 8,
    "totalThreads": 16,
    "processorMemories": [{"capacityMiB": 123, "integrated": True, "type": "DDR", "speedMHz": 1200}],
    "memorySummary": {"ECCModeEnabled": True, "totalCacheSizeMiB": 4096, "totalMemorySizeMiB": 8192},
    "status": {"health": "OK", "state": "Enabled"},
    "powerState": "On",
    "powerCapability": True,
    "instructionSet": "x86-64",
    "processorArchitecture": "x86",
    "processorID": {
        "effectiveFamily": "0x42",
        "effectiveModel": "0x61",
        "identificationRegister": "0x34AC34DC8901274A",
        "microcodeInfo": "0x429943",
        "protectedIdentificationNumber": "123456",
        "step": "0x1",
        "vendorID": "GenuineIntel",
    },
    "links": [
        {"deviceID": "1001", "type": "memory"},
        {"deviceID": "2001", "type": "storage"},
        {"deviceID": "3001", "type": "networkInterface"},
    ],
    "serialNumber": "PROCESSOR1",
    "socketNum": 1,
    "manufacturer": "Intel(R) Corporation",
    "model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# RESP CPU multi Link present
RESP_CPU_MULTI_LINK = {
    "deviceID": "0001",
    "type": "CPU",
    "attribute": {
        "deviceSpecificInformation": {
            "hostName": "sv01",
            "bmcHostName": "bmc-sv01",
            "id": "0P96F00",
            "name": "Quadro P400",
            "firmware_version": "86.07.6B.00.01",
        },
    },
    "baseSpeedMHz": 1200,
    "operatingSpeedMHz": 1000,
    "TDPWatts": 100,
    "totalCores": 8,
    "totalEnabledCores": 8,
    "totalThreads": 16,
    "processorMemories": [{"capacityMiB": 123, "integrated": True, "type": "DDR", "speedMHz": 1200}],
    "memorySummary": {"ECCModeEnabled": True, "totalCacheSizeMiB": 4096, "totalMemorySizeMiB": 8192},
    "status": {"health": "OK", "state": "Enabled"},
    "powerState": "On",
    "powerCapability": True,
    "instructionSet": "x86-64",
    "processorArchitecture": "x86",
    "processorID": {
        "effectiveFamily": "0x42",
        "effectiveModel": "0x61",
        "identificationRegister": "0x34AC34DC8901274A",
        "microcodeInfo": "0x429943",
        "protectedIdentificationNumber": "123456",
        "step": "0x1",
        "vendorID": "GenuineIntel",
    },
    "links": [
        {"deviceID": "1001", "type": "memory"},
        {"deviceID": "2001", "type": "storage"},
        {"deviceID": "2002", "type": "storage"},
        {"deviceID": "3001", "type": "networkInterface"},
        {"deviceID": "3002", "type": "networkInterface"},
    ],
    "serialNumber": "PROCESSOR1",
    "socketNum": 1,
    "manufacturer": "Intel(R) Corporation",
    "model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# RESP CPU Link CPU
RESP_CPU_LINK_CPU = {
    "deviceID": "0001",
    "type": "CPU",
    "attribute": {
        "deviceSpecificInformation": {
            "hostName": "sv01",
            "bmcHostName": "bmc-sv01",
            "id": "0P96F00",
            "name": "Quadro P400",
            "firmware_version": "86.07.6B.00.01",
        },
    },
    "baseSpeedMHz": 1200,
    "operatingSpeedMHz": 1000,
    "TDPWatts": 100,
    "totalCores": 8,
    "totalEnabledCores": 8,
    "totalThreads": 16,
    "processorMemories": [{"capacityMiB": 123, "integrated": True, "type": "DDR", "speedMHz": 1200}],
    "memorySummary": {"ECCModeEnabled": True, "totalCacheSizeMiB": 4096, "totalMemorySizeMiB": 8192},
    "status": {"health": "OK", "state": "Enabled"},
    "powerState": "On",
    "powerCapability": True,
    "instructionSet": "x86-64",
    "processorArchitecture": "x86",
    "processorID": {
        "effectiveFamily": "0x42",
        "effectiveModel": "0x61",
        "identificationRegister": "0x34AC34DC8901274A",
        "microcodeInfo": "0x429943",
        "protectedIdentificationNumber": "123456",
        "step": "0x1",
        "vendorID": "GenuineIntel",
    },
    "links": [{"deviceID": "0002", "type": "CPU"}],
    "serialNumber": "PROCESSOR1",
    "socketNum": 1,
    "manufacturer": "Intel(R) Corporation",
    "model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# RESP CPU Link present
RESP_CPU_LINK_OOB_ONLY = {
    "deviceID": "0001",
    "type": "CPU",
    "attribute": {
        "deviceSpecificInformation": {
            "hostName": "sv01",
            "bmcHostName": "bmc-sv01",
            "id": "0P96F00",
            "name": "Quadro P400",
            "firmware_version": "86.07.6B.00.01",
        },
    },
    "baseSpeedMHz": 1200,
    "operatingSpeedMHz": 1000,
    "TDPWatts": 100,
    "totalCores": 8,
    "totalEnabledCores": 8,
    "totalThreads": 16,
    "processorMemories": [{"capacityMiB": 123, "integrated": True, "type": "DDR", "speedMHz": 1200}],
    "memorySummary": {"ECCModeEnabled": True, "totalCacheSizeMiB": 4096, "totalMemorySizeMiB": 8192},
    "status": {"health": "OK", "state": "Enabled"},
    "powerState": "On",
    "powerCapability": True,
    "instructionSet": "x86-64",
    "processorArchitecture": "x86",
    "processorID": {
        "effectiveFamily": "0x42",
        "effectiveModel": "0x61",
        "identificationRegister": "0x34AC34DC8901274A",
        "microcodeInfo": "0x429943",
        "protectedIdentificationNumber": "123456",
        "step": "0x1",
        "vendorID": "GenuineIntel",
    },
    "links": [{"deviceID": "1001", "type": "memory"}],
    "serialNumber": "PROCESSOR1",
    "socketNum": 1,
    "manufacturer": "Intel(R) Corporation",
    "model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# RESP CPU Link present
RESP_CPU_LINK_FM_ONLY = {
    "deviceID": "0001",
    "type": "CPU",
    "attribute": {
        "deviceSpecificInformation": {
            "hostName": "sv01",
            "bmcHostName": "bmc-sv01",
            "id": "0P96F00",
            "name": "Quadro P400",
            "firmware_version": "86.07.6B.00.01",
        },
    },
    "baseSpeedMHz": 1200,
    "operatingSpeedMHz": 1000,
    "TDPWatts": 100,
    "totalCores": 8,
    "totalEnabledCores": 8,
    "totalThreads": 16,
    "processorMemories": [{"capacityMiB": 123, "integrated": True, "type": "DDR", "speedMHz": 1200}],
    "memorySummary": {"ECCModeEnabled": True, "totalCacheSizeMiB": 4096, "totalMemorySizeMiB": 8192},
    "status": {"health": "OK", "state": "Enabled"},
    "powerState": "On",
    "powerCapability": True,
    "instructionSet": "x86-64",
    "processorArchitecture": "x86",
    "processorID": {
        "effectiveFamily": "0x42",
        "effectiveModel": "0x61",
        "identificationRegister": "0x34AC34DC8901274A",
        "microcodeInfo": "0x429943",
        "protectedIdentificationNumber": "123456",
        "step": "0x1",
        "vendorID": "GenuineIntel",
    },
    "links": [{"deviceID": "2001", "type": "storage"}, {"deviceID": "3001", "type": "networkInterface"}],
    "serialNumber": "PROCESSOR1",
    "socketNum": 1,
    "manufacturer": "Intel(R) Corporation",
    "model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# RESP CPU No Link
RESP_CPU_NO_LINK = {
    "deviceID": "0001",
    "type": "CPU",
    "attribute": {
        "deviceSpecificInformation": {
            "hostName": "sv01",
            "bmcHostName": "bmc-sv01",
            "id": "0P96F00",
            "name": "Quadro P400",
            "firmware_version": "86.07.6B.00.01",
        },
    },
    "baseSpeedMHz": 1200,
    "operatingSpeedMHz": 1000,
    "TDPWatts": 100,
    "totalCores": 8,
    "totalEnabledCores": 8,
    "totalThreads": 16,
    "processorMemories": [{"capacityMiB": 123, "integrated": True, "type": "DDR", "speedMHz": 1200}],
    "memorySummary": {"ECCModeEnabled": True, "totalCacheSizeMiB": 4096, "totalMemorySizeMiB": 8192},
    "status": {"health": "OK", "state": "Enabled"},
    "powerState": "On",
    "powerCapability": True,
    "instructionSet": "x86-64",
    "processorArchitecture": "x86",
    "processorID": {
        "effectiveFamily": "0x42",
        "effectiveModel": "0x61",
        "identificationRegister": "0x34AC34DC8901274A",
        "microcodeInfo": "0x429943",
        "protectedIdentificationNumber": "123456",
        "step": "0x1",
        "vendorID": "GenuineIntel",
    },
    "serialNumber": "PROCESSOR1",
    "socketNum": 1,
    "manufacturer": "Intel(R) Corporation",
    "model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# OOB_DATA memory Link present
OOB_DATA_MEMORY_LINK = {
    "devices": [
        {
            "type": "memory",
            "deviceID": "1001",
            "schema": {
                "@odata.context": "/redfish/v1/$metadata#Memory.Memory",
                "@odata.id": "/redfish/v1/Chassiss/Chassis-1/Memory/MEM-1001",
                "@odata.type": "#Memory.v1_2_0.Memory",
                "MaxTDPMilliWatts": [12000],
                "CapacityMiB": 1073741824,
                "LogicalSizeMiB": 0,
                "NonVolatileSizeMiB": 0,
                "PersistentRegionNumberLimit": 1,
                "PersistentRegionSizeLimitMiB": 8000,
                "PersistentRegionSizeMaxMiB": 8000,
                "VolatileRegionSizeLimitMiB": 8000,
                "VolatileRegionSizeMaxMiB": 8000,
                "AllocationAlignmentMiB": 123,
                "AllocationIncrementMiB": 50,
                "AllowedSpeedsMHz": [30],
                "OperatingSpeedMhz": 3200,
                "BusWidthBits": 72,
                "DataWidthBits": 64,
                "Enabled": True,
                "Name": "Memory",
                "Id": "MEM-1001",
                "Links": {
                    "Chassis": {"@odata.id": "/redfish/v1/Chassis/Chassis-1"},
                    "Processors": [{"@odata.id": "/redfish/v1/Processors/PROC-0001"}],
                },
                "Manufacturer": "Generic",
                "Model": "Modelxxx",
                "MemoryDeviceType": "DDR4",
                "MemoryType": "DRAM",
                "OperatingMemoryModes": ["Volatile"],
                "SerialNumber": "TJ27JXQY",
                "Status": {"Health": "OK", "State": "Enabled"},
                "PowerState": "On",
                "PowerCapability": True,
                "VendorID": "Generic",
                "MemoryMedia": ["DRAM"],
                "MemoryLocation": {"Socket": 4, "MemoryController": 2, "Channel": 1, "Slot": 3},
                "Metrics": {"@odata.id": "{rb}{suffix}/{suffix_id}/Processors/{ProcessorId}/ProcessorMetrics"},
                "EnvironmentMetrics": {
                    "@odata.id": "{rb}{suffix}/{suffix_id}/Processors/{ProcessorId}/EnvironmentMetrics"
                },
            },
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "time": "2023-07-06T05:55:55Z",
        }
    ]
}

# OOB_DATA memory No Link
OOB_DATA_MEMORY_NO_LINK = {
    "devices": [
        {
            "type": "memory",
            "deviceID": "1001",
            "schema": {
                "@odata.context": "/redfish/v1/$metadata#Memory.Memory",
                "@odata.id": "/redfish/v1/Chassiss/Chassis-1/Memory/MEM-1001",
                "@odata.type": "#Memory.v1_2_0.Memory",
                "MaxTDPMilliWatts": [12000],
                "CapacityMiB": 1073741824,
                "LogicalSizeMiB": 0,
                "NonVolatileSizeMiB": 0,
                "PersistentRegionNumberLimit": 1,
                "PersistentRegionSizeLimitMiB": 8000,
                "PersistentRegionSizeMaxMiB": 8000,
                "VolatileRegionSizeLimitMiB": 8000,
                "VolatileRegionSizeMaxMiB": 8000,
                "AllocationAlignmentMiB": 123,
                "AllocationIncrementMiB": 50,
                "AllowedSpeedsMHz": [30],
                "OperatingSpeedMhz": 3200,
                "BusWidthBits": 72,
                "DataWidthBits": 64,
                "Enabled": True,
                "Name": "Memory",
                "Id": "MEM-1001",
                "Links": {
                    "Chassis": {"@odata.id": "/redfish/v1/Chassis/Chassis-1"},
                    "Processors": [{"@odata.id": "/redfish/v1/Processors/PROC-0001"}],
                },
                "Manufacturer": "Generic",
                "Model": "Modelxxx",
                "MemoryDeviceType": "DDR4",
                "MemoryType": "DRAM",
                "OperatingMemoryModes": ["Volatile"],
                "SerialNumber": "TJ27JXQY",
                "Status": {"Health": "OK", "State": "Enabled"},
                "PowerState": "On",
                "PowerCapability": True,
                "VendorID": "Generic",
                "MemoryMedia": ["DRAM"],
                "MemoryLocation": {"Socket": 4, "MemoryController": 2, "Channel": 1, "Slot": 3},
                "Metrics": {"@odata.id": "{rb}{suffix}/{suffix_id}/Processors/{ProcessorId}/ProcessorMetrics"},
                "EnvironmentMetrics": {
                    "@odata.id": "{rb}{suffix}/{suffix_id}/Processors/{ProcessorId}/EnvironmentMetrics"
                },
            },
            "time": "2023-07-06T05:55:55Z",
        }
    ]
}

# FM_DATA memory Link present
FM_DATA_MEMORY_LINK = {
    "data": [
        {
            "deviceID": "1001",
            "type": "memory",
            "PCIeVendorId": "vendor001",
            "PCIeDeviceId": "device002",
            "PCIeDeviceSerialNumber": "serial003",
            "link": [{"deviceID": "0001", "type": "CPU"}],
            "devicePortList": [
                {
                    "fabricId": "NEC-01",
                    "LTSSMState": "L0",
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "USP",
                },
                {
                    "fabricId": "NEC-02",
                    "LTSSMState": "L2",
                    "switchId": "fmsw-02",
                    "switchPortNumber": "2",
                    "switchPortType": "USP",
                },
            ],
        }
    ]
}

# FM_DATA memory No Link
FM_DATA_MEMORY_NO_LINK = {
    "data": [
        {
            "deviceID": "1001",
            "type": "memory",
            "PCIeVendorId": "vendor001",
            "PCIeDeviceId": "device002",
            "PCIeDeviceSerialNumber": "serial003",
            "devicePortList": [
                {
                    "fabricId": "NEC-01",
                    "LTSSMState": "L0",
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "USP",
                },
                {
                    "fabricId": "NEC-02",
                    "LTSSMState": "L2",
                    "switchId": "fmsw-02",
                    "switchPortNumber": "2",
                    "switchPortType": "USP",
                },
            ],
        }
    ]
}

# RESP memory Link present
RESP_MEMORY_LINK = {
    "deviceID": "1001",
    "type": "memory",
    "capacityMiB": 1073741824,
    "logicalSizeMiB": 0,
    "nonVolatileSizeMiB": 0,
    "persistentRegionNumberLimit": 1,
    "persistentRegionSizeLimitMiB": 8000,
    "persistentRegionSizeMaxMiB": 8000,
    "volatileRegionSizeLimitMiB": 8000,
    "volatileRegionSizeMaxMiB": 8000,
    "allocationAlignmentMiB": 123,
    "allocationIncrementMiB": 50,
    "allowedSpeedsMHz": [30],
    "operatingSpeedMHz": 3200,
    "busWidthBits": 72,
    "dataWidthBits": 64,
    "maxTDPsMilliWatts": [12000],
    "enabled": True,
    "memoryMedia": ["DRAM"],
    "memoryType": "DRAM",
    "memoryDeviceType": "DDR4",
    "status": {"health": "OK", "state": "Enabled"},
    "powerState": "On",
    "powerCapability": True,
    "links": [{"type": "CPU", "deviceID": "0001"}],
    "memoryLocation": {"channel": 1, "memoryController": 2, "slot": 3, "socket": 4},
    "serialNumber": "TJ27JXQY",
    "manufacturer": "Generic",
    "model": "Modelxxx",
    "PCIeVendorID": "vendor001",
    "PCIeDeviceID": "device002",
    "PCIeDeviceSerialNumber": "serial003",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# RESP memory No Link
RESP_MEMORY_NO_LINK = {
    "deviceID": "1001",
    "type": "memory",
    "capacityMiB": 1073741824,
    "logicalSizeMiB": 0,
    "nonVolatileSizeMiB": 0,
    "persistentRegionNumberLimit": 1,
    "persistentRegionSizeLimitMiB": 8000,
    "persistentRegionSizeMaxMiB": 8000,
    "volatileRegionSizeLimitMiB": 8000,
    "volatileRegionSizeMaxMiB": 8000,
    "allocationAlignmentMiB": 123,
    "allocationIncrementMiB": 50,
    "allowedSpeedsMHz": [30],
    "operatingSpeedMHz": 3200,
    "busWidthBits": 72,
    "dataWidthBits": 64,
    "maxTDPsMilliWatts": [12000],
    "enabled": True,
    "memoryMedia": ["DRAM"],
    "memoryType": "DRAM",
    "memoryDeviceType": "DDR4",
    "status": {"health": "OK", "state": "Enabled"},
    "powerState": "On",
    "powerCapability": True,
    "memoryLocation": {"channel": 1, "memoryController": 2, "slot": 3, "socket": 4},
    "serialNumber": "TJ27JXQY",
    "manufacturer": "Generic",
    "model": "Modelxxx",
    "PCIeVendorID": "vendor001",
    "PCIeDeviceID": "device002",
    "PCIeDeviceSerialNumber": "serial003",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# OOB_DATA storage Link present
OOB_DATA_STORAGE_LINK = {
    "devices": [
        {
            "type": "storage",
            "deviceID": "2001",
            "schema": {
                "Drive": {
                    "@odata.type": "#Drive.v1_15_0.Drive",
                    "Id": "3D58ECBC375FD9F2",
                    "Name": "Drive Sample",
                    "LocationIndicatorActive": True,
                    "Model": "C123",
                    "Revision": "100A",
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "CapacityBytes": 899527000000,
                    "FailurePredicted": False,
                    "Protocol": "SAS",
                    "MediaType": "HDD",
                    "Manufacturer": "Contoso",
                    "SerialNumber": "1234568",
                    "PartNumber": "C123-1111",
                    "Identifiers": [{"DurableNameFormat": "NAA", "DurableName": "32ADF365C6C1B7BD"}],
                    "PowerState": "On",
                    "PowerCapability": True,
                    "SecureEraseCapability": True,
                    "HotspareType": "Chassis",
                    "EncryptionAbility": "SelfEncryptingDrive",
                    "EncryptionStatus": "Unlocked",
                    "RotationSpeedRPM": 15000,
                    "BlockSizeBytes": 512,
                    "CapableSpeedGbs": 12,
                    "NegotiatedSpeedGbs": 12,
                    "PredictedMediaLifeLeftPercent": 50,
                    "EnvironmentMetrics": {
                        "@odata.id": "{rb}{suffix}/{suffix_id}/Drives/{drive_id}/EnvironmentMetrics"
                    },
                    "Links": {
                        "Chassis": [{"@odata.id": "/redfish/v1/Chassis/{chassis_id}"}],
                        "NetworkDeviceFunctions": [],
                        "StoragePools": [],
                        "Volumes": [
                            {"@odata.id": "/redfish/v1/Systems/{suffix_id}/Storage/{storage_id}/Volumes/{vol_id}"}
                        ],
                        "Storage": [{"@odata.id": "/redfish/v1/Storage/STR-2001"}],
                    },
                    "@odata.id": "/redfish/v1/Chassis/Chassis-1/Drives/DRI-2001",
                },
                "Storage": {
                    "Redundancy": [
                        {
                            "RedundancyEnabled": True,
                            "Mode": "Failover",
                            "Name": "Redundancy",
                            "MaxNumSupported": 2,
                            "MinNumNeeded": 1,
                            "RedundancySet": [{"deviceID": "1234"}],
                        }
                    ]
                },
                "Volume": {
                    "AccessCapabilities": ["Append", "Read"],
                    "OptimumIOSizeBytes": 256,
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
                    "CapacityBytes": 20,
                    "MaxBlockSizeBytes": 30,
                    "RecoverableCapacitySourceCount": 40,
                    "RemainingCapacityPercent": 50,
                    "Manufacturer": "Contoso",
                    "Model": "Modelxx123",
                    "Identifiers": [
                        {"DurableNameFormat": "UUID", "DurableName": "0324c96c-8031-4f5e-886c-50cd90aca854"}
                    ],
                },
            },
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "time": "2023-07-06T05:55:55Z",
        }
    ]
}

# OOB_DATA storage No Link
OOB_DATA_STORAGE_NO_LINK = {
    "devices": [
        {
            "type": "storage",
            "deviceID": "2001",
            "schema": {
                "Drive": {
                    "@odata.type": "#Drive.v1_15_0.Drive",
                    "Id": "3D58ECBC375FD9F2",
                    "Name": "Drive Sample",
                    "LocationIndicatorActive": True,
                    "Model": "C123",
                    "Revision": "100A",
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "CapacityBytes": 899527000000,
                    "FailurePredicted": False,
                    "Protocol": "SAS",
                    "MediaType": "HDD",
                    "Manufacturer": "Contoso",
                    "SerialNumber": "1234568",
                    "PartNumber": "C123-1111",
                    "Identifiers": [{"DurableNameFormat": "NAA", "DurableName": "32ADF365C6C1B7BD"}],
                    "PowerState": "On",
                    "PowerCapability": True,
                    "SecureEraseCapability": True,
                    "HotspareType": "Chassis",
                    "EncryptionAbility": "SelfEncryptingDrive",
                    "EncryptionStatus": "Unlocked",
                    "RotationSpeedRPM": 15000,
                    "BlockSizeBytes": 512,
                    "CapableSpeedGbs": 12.24,
                    "NegotiatedSpeedGbs": 12.24,
                    "PredictedMediaLifeLeftPercent": 50,
                    "EnvironmentMetrics": {
                        "@odata.id": "{rb}{suffix}/{suffix_id}/Drives/{drive_id}/EnvironmentMetrics"
                    },
                    "Links": {
                        "Chassis": [{"@odata.id": "/redfish/v1/Chassis/{chassis_id}"}],
                        "NetworkDeviceFunctions": [],
                        "StoragePools": [],
                        "Volumes": [
                            {"@odata.id": "/redfish/v1/Systems/{suffix_id}/Storage/{storage_id}/Volumes/{vol_id}"}
                        ],
                        "Storage": [{"@odata.id": "/redfish/v1/Storage/STR-2001"}],
                    },
                    "@odata.id": "/redfish/v1/Chassis/Chassis-1/Drives/DRI-2001",
                },
                "Storage": {
                    "Redundancy": [
                        {
                            "RedundancyEnabled": True,
                            "Mode": "Failover",
                            "Name": "Redundancy",
                            "MaxNumSupported": 2,
                            "MinNumNeeded": 1,
                            "RedundancySet": [{"deviceID": "1234"}],
                        }
                    ]
                },
                "Volume": {
                    "AccessCapabilities": ["Append", "Read"],
                    "OptimumIOSizeBytes": 256,
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
                    "CapacityBytes": 20,
                    "MaxBlockSizeBytes": 30,
                    "RecoverableCapacitySourceCount": 40,
                    "RemainingCapacityPercent": 50,
                    "Manufacturer": "Contoso",
                    "Model": "Modelxx123",
                    "Identifiers": [
                        {"DurableNameFormat": "UUID", "DurableName": "0324c96c-8031-4f5e-886c-50cd90aca854"}
                    ],
                },
            },
            "time": "2023-07-06T05:55:55Z",
        }
    ]
}

# OOB_DATA storage int value
OOB_DATA_STORAGE_INT = {
    "devices": [
        {
            "type": "storage",
            "deviceID": "2001",
            "schema": {"Drive": {"CapableSpeedGbs": 12, "NegotiatedSpeedGbs": 56, "PredictedMediaLifeLeftPercent": 23}},
        }
    ]
}

# OOB_DATA storage float value
OOB_DATA_STORAGE_FLOAT = {
    "devices": [
        {
            "type": "storage",
            "deviceID": "2001",
            "schema": {
                "Drive": {"CapableSpeedGbs": 12.34, "NegotiatedSpeedGbs": 56.78, "PredictedMediaLifeLeftPercent": 23.4}
            },
        }
    ]
}

# FM_DATA storage Link present
FM_DATA_STORAGE_LINK = {
    "data": [
        {
            "deviceID": "2001",
            "type": "storage",
            "PCIeVendorId": "vendor001",
            "PCIeDeviceId": "device002",
            "PCIeDeviceSerialNumber": "serial003",
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "devicePortList": [
                {
                    "fabricId": "NEC-01",
                    "LTSSMState": "L0",
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "USP",
                },
                {
                    "fabricId": "NEC-02",
                    "LTSSMState": "L2",
                    "switchId": "fmsw-02",
                    "switchPortNumber": "2",
                    "switchPortType": "USP",
                },
            ],
        }
    ]
}

# FM_DATA storage No Link
FM_DATA_STORAGE_NO_LINK = {
    "data": [
        {
            "deviceID": "2001",
            "type": "storage",
            "PCIeVendorId": "vendor001",
            "PCIeDeviceId": "device002",
            "PCIeDeviceSerialNumber": "serial003",
            "devicePortList": [
                {
                    "fabricId": "NEC-01",
                    "LTSSMState": "L0",
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "USP",
                },
                {
                    "fabricId": "NEC-02",
                    "LTSSMState": "L2",
                    "switchId": "fmsw-02",
                    "switchPortNumber": "2",
                    "switchPortType": "USP",
                },
            ],
        }
    ]
}

# RESP storage Link present
RESP_STORAGE_LINK = {
    "deviceID": "2001",
    "type": "storage",
    "storageRedundancies": [
        {
            "enabled": True,
            "mode": "Failover",
            "name": "Redundancy",
            "maxNumSupported": 2,
            "minNumNeeded": 1,
            "sets": [{"deviceID": "1234"}],
        }
    ],
    "volumeAccessCapabilities": ["Append", "Read"],
    "volumeOptimumIOSizeBytes": 256,
    "volumeCapacity": {
        "data": {"allocatedBytes": 1, "consumedBytes": 2, "guaranteedBytes": 3, "provisionedBytes": 4},
        "metadata": {"allocatedBytes": 5, "consumedBytes": 6, "guaranteedBytes": 7, "provisionedBytes": 8},
        "snapshot": {"allocatedBytes": 9, "consumedBytes": 10, "guaranteedBytes": 11, "provisionedBytes": 12},
    },
    "volumeCapacityBytes": 20,
    "volumeMaxBlockSizeBytes": 30,
    "volumeRecoverableCapacitySourceCount": 40,
    "volumeRemainingCapacityPercent": 50,
    "drivePredictedMediaLifeLeftPercent": 50,
    "driveCapacityBytes": 899527000000,
    "driveCapableSpeedGbs": 12,
    "driveNegotiatedSpeedGbs": 12,
    "driveHotspareType": "Chassis",
    "status": {"health": "OK", "state": "Enabled"},
    "powerState": "On",
    "powerCapability": True,
    "secureEraseCapability": True,
    "links": [{"type": "CPU", "deviceID": "0001"}],
    "driveSerialNumber": "1234568",
    "driveManufacturer": "Contoso",
    "driveModel": "C123",
    "driveIdentifiers": [{"durableNameFormat": "NAA", "durableName": "32ADF365C6C1B7BD"}],
    "volumeManufacturer": "Contoso",
    "volumeModel": "Modelxx123",
    "volumeIdentifiers": [{"durableNameFormat": "UUID", "durableName": "0324c96c-8031-4f5e-886c-50cd90aca854"}],
    "PCIeVendorID": "vendor001",
    "PCIeDeviceID": "device002",
    "PCIeDeviceSerialNumber": "serial003",
    "model": "C123",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# RESP storage No Link
RESP_STORAGE_NO_LINK = {
    "deviceID": "2001",
    "type": "storage",
    "storageRedundancies": [
        {
            "enabled": True,
            "mode": "Failover",
            "name": "Redundancy",
            "maxNumSupported": 2,
            "minNumNeeded": 1,
            "sets": [{"deviceID": "1234"}],
        }
    ],
    "volumeAccessCapabilities": ["Append", "Read"],
    "volumeOptimumIOSizeBytes": 256,
    "volumeCapacity": {
        "data": {"allocatedBytes": 1, "consumedBytes": 2, "guaranteedBytes": 3, "provisionedBytes": 4},
        "metadata": {"allocatedBytes": 5, "consumedBytes": 6, "guaranteedBytes": 7, "provisionedBytes": 8},
        "snapshot": {"allocatedBytes": 9, "consumedBytes": 10, "guaranteedBytes": 11, "provisionedBytes": 12},
    },
    "volumeCapacityBytes": 20,
    "volumeMaxBlockSizeBytes": 30,
    "volumeRecoverableCapacitySourceCount": 40,
    "volumeRemainingCapacityPercent": 50,
    "drivePredictedMediaLifeLeftPercent": 50,
    "driveCapacityBytes": 899527000000,
    "driveCapableSpeedGbs": 12.24,
    "driveNegotiatedSpeedGbs": 12.24,
    "driveHotspareType": "Chassis",
    "status": {"health": "OK", "state": "Enabled"},
    "powerState": "On",
    "powerCapability": True,
    "secureEraseCapability": True,
    "driveSerialNumber": "1234568",
    "driveManufacturer": "Contoso",
    "driveModel": "C123",
    "driveIdentifiers": [{"durableNameFormat": "NAA", "durableName": "32ADF365C6C1B7BD"}],
    "volumeManufacturer": "Contoso",
    "volumeModel": "Modelxx123",
    "volumeIdentifiers": [{"durableNameFormat": "UUID", "durableName": "0324c96c-8031-4f5e-886c-50cd90aca854"}],
    "PCIeVendorID": "vendor001",
    "PCIeDeviceID": "device002",
    "PCIeDeviceSerialNumber": "serial003",
    "model": "C123",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# RESP storage int value
RESP_STORAGE_INT = {
    "deviceID": "2001",
    "type": "storage",
    "drivePredictedMediaLifeLeftPercent": 23,
    "driveCapableSpeedGbs": 12,
    "driveNegotiatedSpeedGbs": 56,
}

# RESP storage float value
RESP_STORAGE_FLOAT = {
    "deviceID": "2001",
    "type": "storage",
    "drivePredictedMediaLifeLeftPercent": 23.4,
    "driveCapableSpeedGbs": 12.34,
    "driveNegotiatedSpeedGbs": 56.78,
}

# OOB_DATA NIC Link present
OOB_DATA_NIC_LINK = {
    "devices": [
        {
            "type": "networkInterface",
            "deviceID": "3001",
            "schema": {
                "attribute": {
                    "deviceSpecificInformation": {
                        "type": "eeCard",
                        "id": "12345",
                        "status": "sfa",
                        "groupId": 16,
                        "linkStatus0": "up",
                        "linkStatus1": "down",
                        "switchName": "AD102GL",
                    },
                },
                "SerialInterfaces": {"BitRate": "115200"},
                "Network": {
                    "@odata.type": "#NetworkAdapter.v1_9_0.NetworkAdapter",
                    "Id": "9fa725a1",
                    "Name": "Network Adapter View",
                    "Manufacturer": "Contoso",
                    "Model": "599TPS-T",
                    "SKU": "Contoso TPS-Net 2-Port Base-T",
                    "SerialNumber": "003BFLRT00023234",
                    "PartNumber": "975421-B20",
                    "Ports": [],
                    "NetworkDeviceFunctions": [],
                    "PowerState": "On",
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "PowerCapability": False,
                    "Controllers": [
                        {
                            "FirmwarePackageVersion": "7.4.10",
                            "ControllerCapabilities": {
                                "NetworkPortCount": 2,
                                "NetworkDeviceFunctionCount": 8,
                                "DataCenterBridging": {"Capable": True},
                                "VirtualizationOffload": {
                                    "VirtualFunction": {
                                        "DeviceMaxCount": 256,
                                        "NetworkPortMaxCount": 128,
                                        "MinAssignmentGroupSize": 4,
                                    },
                                    "SRIOV": {"SRIOVVEPACapable": True},
                                },
                                "NPIV": {"MaxDeviceLogins": 4, "MaxPortLogins": 2},
                                "NPAR": {"NparCapable": True, "NparEnabled": False},
                            },
                            "PCIeInterface": {
                                "PCIeType": "Gen2",
                                "MaxPCIeType": "Gen3",
                                "LanesInUse": 1,
                                "MaxLanes": 4,
                            },
                            "Identifiers": [{"DurableNameFormat": "NAA", "DurableName": "345C59DBD970859C"}],
                            "Location": {
                                "PartLocation": {
                                    "ServiceLabel": "Slot 1",
                                    "LocationType": "Slot",
                                    "LocationOrdinalValue": 0,
                                    "Reference": "Rear",
                                    "Orientation": "LeftToRight",
                                }
                            },
                        }
                    ],
                    "@odata.id": "/redfish/v1/Chassis/Chassis-1/NetworkAdapters/NIC-3001",
                },
                "PCIeDevice": {
                    "SerialNumber": "serial003",
                },
                "PCIeFunction": {
                    "DeviceId": "device002",
                    "VendorId": "vendor001",
                },
                "NetworkDeviceFunctions": {
                    "DeviceEnabled": True,
                    "Ethernet": {
                        "MACAddress": "00:0C:29:9A:98:ED",
                        "MTUSize": 1500,
                        "MTUSizeMaximum": 2500,
                        "PermanentMACAddress": "00:0C:29:9A:98:ED",
                        "VLAN": {"VLANEnable": True, "VLANId": 101},
                    },
                    "Limits": [
                        {
                            "BurstBytesPerSecond": 1,
                            "BurstPacketsPerSecond": 2,
                            "Direction": "Ingress",
                            "SustainedBytesPerSecond": 3,
                            "SustainedPacketsPerSecond": 4,
                        }
                    ],
                },
                "Port": {
                    "FunctionMaxBandwidth": [{"AllocationPercent": 80}],
                    "FunctionMinBandwidth": [{"AllocationPercent": 80}],
                    "MaxSpeedGbps": 48,
                    "LinkConfiguration": [{"CapableLinkSpeedGbps": [1, 2.2, 3]}],
                },
            },
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "time": "2023-07-06T05:55:55Z",
        }
    ]
}

# OOB_DATA NIC No Link
OOB_DATA_NIC_NO_LINK = {
    "devices": [
        {
            "type": "networkInterface",
            "deviceID": "3001",
            "schema": {
                "attribute": {
                    "deviceSpecificInformation": {
                        "type": "eeCard",
                        "id": "12345",
                        "status": "sfa",
                        "groupId": 16,
                        "linkStatus0": "up",
                        "linkStatus1": "down",
                        "switchName": "AD102GL",
                    },
                },
                "SerialInterfaces": {"BitRate": "115200"},
                "Network": {
                    "@odata.type": "#NetworkAdapter.v1_9_0.NetworkAdapter",
                    "Id": "9fa725a1",
                    "Name": "Network Adapter View",
                    "Manufacturer": "Contoso",
                    "Model": "599TPS-T",
                    "SKU": "Contoso TPS-Net 2-Port Base-T",
                    "SerialNumber": "003BFLRT00023234",
                    "PartNumber": "975421-B20",
                    "Ports": [],
                    "NetworkDeviceFunctions": [],
                    "PowerState": "On",
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "PowerCapability": False,
                    "Controllers": [
                        {
                            "FirmwarePackageVersion": "7.4.10",
                            "ControllerCapabilities": {
                                "NetworkPortCount": 2,
                                "NetworkDeviceFunctionCount": 8,
                                "DataCenterBridging": {"Capable": True},
                                "VirtualizationOffload": {
                                    "VirtualFunction": {
                                        "DeviceMaxCount": 256,
                                        "NetworkPortMaxCount": 128,
                                        "MinAssignmentGroupSize": 4,
                                    },
                                    "SRIOV": {"SRIOVVEPACapable": True},
                                },
                                "NPIV": {"MaxDeviceLogins": 4, "MaxPortLogins": 2},
                                "NPAR": {"NparCapable": True, "NparEnabled": False},
                            },
                            "PCIeInterface": {
                                "PCIeType": "Gen2",
                                "MaxPCIeType": "Gen3",
                                "LanesInUse": 1,
                                "MaxLanes": 4,
                            },
                            "Identifiers": [{"DurableNameFormat": "NAA", "DurableName": "345C59DBD970859C"}],
                            "Location": {
                                "PartLocation": {
                                    "ServiceLabel": "Slot 1",
                                    "LocationType": "Slot",
                                    "LocationOrdinalValue": 0,
                                    "Reference": "Rear",
                                    "Orientation": "LeftToRight",
                                }
                            },
                        }
                    ],
                    "@odata.id": "/redfish/v1/Chassis/Chassis-1/NetworkAdapters/NIC-3001",
                },
                "PCIeDevice": {
                    "SerialNumber": "serial005",
                },
                "PCIeFunction": {
                    "DeviceId": None,
                    "VendorId": "",
                },
                "NetworkDeviceFunctions": {
                    "DeviceEnabled": True,
                    "Ethernet": {
                        "MACAddress": "00:0C:29:9A:98:ED",
                        "MTUSize": 1500,
                        "MTUSizeMaximum": 2500,
                        "PermanentMACAddress": "00:0C:29:9A:98:ED",
                        "VLAN": {"VLANEnable": True, "VLANId": 101},
                    },
                    "Limits": [
                        {
                            "BurstBytesPerSecond": 1,
                            "BurstPacketsPerSecond": 2,
                            "Direction": "Ingress",
                            "SustainedBytesPerSecond": 3,
                            "SustainedPacketsPerSecond": 4,
                        }
                    ],
                },
                "Port": {
                    "FunctionMaxBandwidth": [{"AllocationPercent": 80}],
                    "FunctionMinBandwidth": [{"AllocationPercent": 80}],
                    "MaxSpeedGbps": 48,
                    "LinkConfiguration": [{"CapableLinkSpeedGbps": [1, 2.2, 3]}],
                },
            },
            "time": "2023-07-06T05:55:55Z",
        }
    ]
}

# OOB_DATA NIC int value
OOB_DATA_NIC_INT = {
    "devices": [{"type": "networkInterface", "deviceID": "3001", "schema": {"Port": {"MaxSpeedGbps": 12}}}]
}

# OOB_DATA NIC float value
OOB_DATA_NIC_FLOAT = {
    "devices": [{"type": "networkInterface", "deviceID": "3001", "schema": {"Port": {"MaxSpeedGbps": 34.56}}}]
}

# FM_DATA networkInterface Link present
FM_DATA_NIC_LINK = {
    "data": [
        {
            "deviceID": "3001",
            "type": "networkInterface",
            "PCIeVendorId": "",
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": "serial005",
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "devicePortList": [
                {
                    "fabricId": "NEC-01",
                    "LTSSMState": "L0",
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "USP",
                },
                {
                    "fabricId": "NEC-02",
                    "LTSSMState": "L2",
                    "switchId": "fmsw-02",
                    "switchPortNumber": "2",
                    "switchPortType": "USP",
                },
            ],
        }
    ]
}

# FM_DATA networkInterface No Link
FM_DATA_NIC_NO_LINK = {
    "data": [
        {
            "deviceID": "3001",
            "type": "networkInterface",
            "PCIeVendorId": "vendor001",
            "PCIeDeviceId": "device002",
            "PCIeDeviceSerialNumber": "serial003",
            "devicePortList": [
                {
                    "fabricId": "NEC-01",
                    "LTSSMState": "L0",
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "USP",
                },
                {
                    "fabricId": "NEC-02",
                    "LTSSMState": "L2",
                    "switchId": "fmsw-02",
                    "switchPortNumber": "2",
                    "switchPortType": "USP",
                },
            ],
        }
    ]
}

# RESP NIC Link present
RESP_NIC_LINK = {
    "deviceID": "3001",
    "type": "networkInterface",
    "attribute": {
        "deviceSpecificInformation": {
            "type": "eeCard",
            "id": "12345",
            "status": "sfa",
            "groupId": 16,
            "linkStatus0": "up",
            "linkStatus1": "down",
            "switchName": "AD102GL",
        }
    },
    "bitRate": "115200",
    "controllers": [
        {
            "capability": {
                "dataCenterBridging": {"capable": True},
                "networkDeviceFunctionCount": 8,
                "networkPortCount": 2,
                "npar": {"capable": True, "enabled": False},
                "npiv": {"maxDeviceLogins": 4, "maxPortLogins": 2},
                "virtualizationOffload": {
                    "virtualFunction": {"deviceMaxCount": 256, "networkPortMaxCount": 128, "minAssignmentGroupSize": 4},
                    "sriov": {"VEPACapable": True},
                },
            },
            "firmwarePackageVersion": "7.4.10",
            "identifiers": [{"durableNameFormat": "NAA", "durableName": "345C59DBD970859C"}],
            "location": {
                "partLocation": {
                    "serviceLabel": "Slot 1",
                    "type": "Slot",
                    "ordinalValue": 0,
                    "reference": "Rear",
                    "orientation": "LeftToRight",
                }
            },
            "PCIeInterface": {"lanesInUse": 1, "maxLanes": 4, "PCIeType": "Gen2", "maxPCIeType": "Gen3"},
        }
    ],
    "deviceEnabled": True,
    "ethernet": {
        "MACAddress": "00:0C:29:9A:98:ED",
        "MTUSize": 1500,
        "MTUSizeMaximum": 2500,
        "permanentMACAddress": "00:0C:29:9A:98:ED",
        "vlan": {"enable": True, "id": 101},
    },
    "limits": [
        {
            "burstBytesPerSecond": 1,
            "burstPacketsPerSecond": 2,
            "direction": "Ingress",
            "sustainedBytesPerSecond": 3,
            "sustainedPacketsPerSecond": 4,
        }
    ],
    "functionMaxBandwidths": [{"allocationPercent": 80}],
    "functionMinBandwidths": [{"allocationPercent": 80}],
    "maxSpeedGbps": 48,
    "linkConfigurations": [{"capableLinkSpeedsGbps": [1, 2.2, 3]}],
    "links": [{"type": "CPU", "deviceID": "0001"}],
    "networkAdapterSerialNumber": "003BFLRT00023234",
    "networkAdapterManufacturer": "Contoso",
    "networkAdapterModel": "599TPS-T",
    "fabricAdapterSerialNumber": "003BFLRT00023234",
    "fabricAdapterManufacturer": "Contoso",
    "fabricAdapterModel": "599TPS-T",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": False,
    "PCIeVendorID": "vendor001",
    "PCIeDeviceID": "device002",
    "PCIeDeviceSerialNumber": "serial005",
    "model": "599TPS-T",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# RESP NIC No Link
RESP_NIC_NO_LINK = {
    "deviceID": "3001",
    "type": "networkInterface",
    "attribute": {
        "deviceSpecificInformation": {
            "type": "eeCard",
            "id": "12345",
            "status": "sfa",
            "groupId": 16,
            "linkStatus0": "up",
            "linkStatus1": "down",
            "switchName": "AD102GL",
        }
    },
    "bitRate": "115200",
    "controllers": [
        {
            "capability": {
                "dataCenterBridging": {"capable": True},
                "networkDeviceFunctionCount": 8,
                "networkPortCount": 2,
                "npar": {"capable": True, "enabled": False},
                "npiv": {"maxDeviceLogins": 4, "maxPortLogins": 2},
                "virtualizationOffload": {
                    "virtualFunction": {"deviceMaxCount": 256, "networkPortMaxCount": 128, "minAssignmentGroupSize": 4},
                    "sriov": {"VEPACapable": True},
                },
            },
            "firmwarePackageVersion": "7.4.10",
            "identifiers": [{"durableNameFormat": "NAA", "durableName": "345C59DBD970859C"}],
            "location": {
                "partLocation": {
                    "serviceLabel": "Slot 1",
                    "type": "Slot",
                    "ordinalValue": 0,
                    "reference": "Rear",
                    "orientation": "LeftToRight",
                }
            },
            "PCIeInterface": {"lanesInUse": 1, "maxLanes": 4, "PCIeType": "Gen2", "maxPCIeType": "Gen3"},
        }
    ],
    "deviceEnabled": True,
    "ethernet": {
        "MACAddress": "00:0C:29:9A:98:ED",
        "MTUSize": 1500,
        "MTUSizeMaximum": 2500,
        "permanentMACAddress": "00:0C:29:9A:98:ED",
        "vlan": {"enable": True, "id": 101},
    },
    "limits": [
        {
            "burstBytesPerSecond": 1,
            "burstPacketsPerSecond": 2,
            "direction": "Ingress",
            "sustainedBytesPerSecond": 3,
            "sustainedPacketsPerSecond": 4,
        }
    ],
    "functionMaxBandwidths": [{"allocationPercent": 80}],
    "functionMinBandwidths": [{"allocationPercent": 80}],
    "maxSpeedGbps": 48,
    "linkConfigurations": [{"capableLinkSpeedsGbps": [1, 2.2, 3]}],
    "networkAdapterSerialNumber": "003BFLRT00023234",
    "networkAdapterManufacturer": "Contoso",
    "networkAdapterModel": "599TPS-T",
    "fabricAdapterSerialNumber": "003BFLRT00023234",
    "fabricAdapterManufacturer": "Contoso",
    "fabricAdapterModel": "599TPS-T",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": False,
    "PCIeVendorID": "vendor001",
    "PCIeDeviceID": "device002",
    "PCIeDeviceSerialNumber": "serial003",
    "model": "599TPS-T",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# RESP NIC int value
RESP_NIC_INT = {"deviceID": "3001", "type": "networkInterface", "maxSpeedGbps": 12}

# RESP NIC float value
RESP_NIC_FLOAT = {"deviceID": "3001", "type": "networkInterface", "maxSpeedGbps": 34.56}

# OOB_DATA FA Link present
OOB_DATA_FA_LINK = {
    "devices": [
        {
            "type": "sourceFabricAdapter",
            "deviceID": "3101",
            "schema": {
                "attribute": {
                    "deviceSpecificInformation": {
                        "type": "eeCard",
                        "id": "12345",
                        "status": "sfa",
                        "groupId": 16,
                        "linkStatus0": "up",
                        "linkStatus1": "down",
                        "notificationStatus0": ["up", "down"],
                        "notificationStatus1": ["down", "down"],
                        "switchName": "AD102GL",
                    },
                },
                "SerialInterfaces": {"BitRate": "115200"},
                "Network": {
                    "@odata.type": "#NetworkAdapter.v1_9_0.NetworkAdapter",
                    "Id": "9fa725a1",
                    "Name": "Network Adapter View",
                    "Manufacturer": "Contoso",
                    "Model": "599TPS-T",
                    "SKU": "Contoso TPS-Net 2-Port Base-T",
                    "SerialNumber": "003BFLRT00023234",
                    "PartNumber": "975421-B20",
                    "Ports": [],
                    "NetworkDeviceFunctions": [],
                    "PowerState": "On",
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "PowerCapability": False,
                    "Controllers": [
                        {
                            "FirmwarePackageVersion": "7.4.10",
                            "ControllerCapabilities": {
                                "NetworkPortCount": 2,
                                "NetworkDeviceFunctionCount": 8,
                                "DataCenterBridging": {"Capable": True},
                                "VirtualizationOffload": {
                                    "VirtualFunction": {
                                        "DeviceMaxCount": 256,
                                        "NetworkPortMaxCount": 128,
                                        "MinAssignmentGroupSize": 4,
                                    },
                                    "SRIOV": {"SRIOVVEPACapable": True},
                                },
                                "NPIV": {"MaxDeviceLogins": 4, "MaxPortLogins": 2},
                                "NPAR": {"NparCapable": True, "NparEnabled": False},
                            },
                            "PCIeInterface": {
                                "PCIeType": "Gen2",
                                "MaxPCIeType": "Gen3",
                                "LanesInUse": 1,
                                "MaxLanes": 4,
                            },
                            "Identifiers": [{"DurableNameFormat": "NAA", "DurableName": "345C59DBD970859C"}],
                            "Location": {
                                "PartLocation": {
                                    "ServiceLabel": "Slot 1",
                                    "LocationType": "Slot",
                                    "LocationOrdinalValue": 0,
                                    "Reference": "Rear",
                                    "Orientation": "LeftToRight",
                                }
                            },
                        }
                    ],
                    "@odata.id": "/redfish/v1/Chassis/Chassis-1/NetworkAdapters/NIC-3001",
                },
                "PCIeDevice": {
                    "SerialNumber": "serial003",
                },
                "PCIeFunction": {
                    "DeviceId": "device002",
                    "VendorId": "vendor001",
                },
                "NetworkDeviceFunctions": {
                    "DeviceEnabled": True,
                    "Ethernet": {
                        "MACAddress": "00:0C:29:9A:98:ED",
                        "MTUSize": 1500,
                        "MTUSizeMaximum": 2500,
                        "PermanentMACAddress": "00:0C:29:9A:98:ED",
                        "VLAN": {"VLANEnable": True, "VLANId": 101},
                    },
                    "Limits": [
                        {
                            "BurstBytesPerSecond": 1,
                            "BurstPacketsPerSecond": 2,
                            "Direction": "Ingress",
                            "SustainedBytesPerSecond": 3,
                            "SustainedPacketsPerSecond": 4,
                        }
                    ],
                },
                "Port": {
                    "FunctionMaxBandwidth": [{"AllocationPercent": 80}],
                    "FunctionMinBandwidth": [{"AllocationPercent": 80}],
                    "MaxSpeedGbps": 48,
                    "LinkConfiguration": [{"CapableLinkSpeedGbps": [1, 2.2, 3]}],
                },
            },
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "time": "2023-07-06T05:55:55Z",
        }
    ]
}

# OOB_DATA FA No Link
OOB_DATA_FA_NO_LINK = {
    "devices": [
        {
            "type": "sourceFabricAdapter",
            "deviceID": "3101",
            "schema": {
                "attribute": {
                    "deviceSpecificInformation": {
                        "type": "eeCard",
                        "id": "12345",
                        "status": "sfa",
                        "groupId": 16,
                        "linkStatus0": "up",
                        "linkStatus1": "down",
                        "notificationStatus0": ["up", "down"],
                        "notificationStatus1": ["down", "down"],
                        "switchName": "AD102GL",
                    },
                },
                "SerialInterfaces": {"BitRate": "115200"},
                "Network": {
                    "@odata.type": "#NetworkAdapter.v1_9_0.NetworkAdapter",
                    "Id": "9fa725a1",
                    "Name": "Network Adapter View",
                    "Manufacturer": "Contoso",
                    "Model": "599TPS-T",
                    "SKU": "Contoso TPS-Net 2-Port Base-T",
                    "SerialNumber": "003BFLRT00023234",
                    "PartNumber": "975421-B20",
                    "Ports": [],
                    "NetworkDeviceFunctions": [],
                    "PowerState": "On",
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "PowerCapability": False,
                    "Controllers": [
                        {
                            "FirmwarePackageVersion": "7.4.10",
                            "ControllerCapabilities": {
                                "NetworkPortCount": 2,
                                "NetworkDeviceFunctionCount": 8,
                                "DataCenterBridging": {"Capable": True},
                                "VirtualizationOffload": {
                                    "VirtualFunction": {
                                        "DeviceMaxCount": 256,
                                        "NetworkPortMaxCount": 128,
                                        "MinAssignmentGroupSize": 4,
                                    },
                                    "SRIOV": {"SRIOVVEPACapable": True},
                                },
                                "NPIV": {"MaxDeviceLogins": 4, "MaxPortLogins": 2},
                                "NPAR": {"NparCapable": True, "NparEnabled": False},
                            },
                            "PCIeInterface": {
                                "PCIeType": "Gen2",
                                "MaxPCIeType": "Gen3",
                                "LanesInUse": 1,
                                "MaxLanes": 4,
                            },
                            "Identifiers": [{"DurableNameFormat": "NAA", "DurableName": "345C59DBD970859C"}],
                            "Location": {
                                "PartLocation": {
                                    "ServiceLabel": "Slot 1",
                                    "LocationType": "Slot",
                                    "LocationOrdinalValue": 0,
                                    "Reference": "Rear",
                                    "Orientation": "LeftToRight",
                                }
                            },
                        }
                    ],
                    "@odata.id": "/redfish/v1/Chassis/Chassis-1/NetworkAdapters/NIC-3001",
                },
                "PCIeDevice": {
                    "SerialNumber": "serial003",
                },
                "PCIeFunction": {
                    "DeviceId": "device002",
                    "VendorId": "vendor001",
                },
                "NetworkDeviceFunctions": {
                    "DeviceEnabled": True,
                    "Ethernet": {
                        "MACAddress": "00:0C:29:9A:98:ED",
                        "MTUSize": 1500,
                        "MTUSizeMaximum": 2500,
                        "PermanentMACAddress": "00:0C:29:9A:98:ED",
                        "VLAN": {"VLANEnable": True, "VLANId": 101},
                    },
                    "Limits": [
                        {
                            "BurstBytesPerSecond": 1,
                            "BurstPacketsPerSecond": 2,
                            "Direction": "Ingress",
                            "SustainedBytesPerSecond": 3,
                            "SustainedPacketsPerSecond": 4,
                        }
                    ],
                },
                "Port": {
                    "FunctionMaxBandwidth": [{"AllocationPercent": 80}],
                    "FunctionMinBandwidth": [{"AllocationPercent": 80}],
                    "MaxSpeedGbps": 48,
                    "LinkConfiguration": [{"CapableLinkSpeedGbps": [1, 2.2, 3]}],
                },
            },
            "time": "2023-07-06T05:55:55Z",
        }
    ]
}

# OOB_DATA FA int value
OOB_DATA_FA_INT = {
    "devices": [{"type": "sourceFabricAdapter", "deviceID": "3101", "schema": {"Port": {"MaxSpeedGbps": 12}}}]
}

# OOB_DATA FA float value
OOB_DATA_FA_FLOAT = {
    "devices": [{"type": "sourceFabricAdapter", "deviceID": "3101", "schema": {"Port": {"MaxSpeedGbps": 34.56}}}]
}

# FM_DATA networkInterface Link present
FM_DATA_FA_LINK = {
    "data": [
        {
            "deviceID": "3101",
            "type": "sourceFabricAdapter",
            "PCIeVendorId": "vendor001",
            "PCIeDeviceId": "device002",
            "PCIeDeviceSerialNumber": "serial003",
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "devicePortList": [
                {
                    "fabricId": "NEC-01",
                    "LTSSMState": "L0",
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "USP",
                },
                {
                    "fabricId": "NEC-02",
                    "LTSSMState": "L2",
                    "switchId": "fmsw-02",
                    "switchPortNumber": "2",
                    "switchPortType": "USP",
                },
            ],
        }
    ]
}

# FM_DATA networkInterface No Link
FM_DATA_FA_NO_LINK = {
    "data": [
        {
            "deviceID": "3101",
            "type": "sourceFabricAdapter",
            "PCIeVendorId": "vendor001",
            "PCIeDeviceId": "device002",
            "PCIeDeviceSerialNumber": "serial003",
            "devicePortList": [
                {
                    "fabricId": "NEC-01",
                    "LTSSMState": "L0",
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "USP",
                },
                {
                    "fabricId": "NEC-02",
                    "LTSSMState": "L2",
                    "switchId": "fmsw-02",
                    "switchPortNumber": "2",
                    "switchPortType": "USP",
                },
            ],
        }
    ]
}

# RESP FA Link present
RESP_FA_LINK = {
    "deviceID": "3101",
    "type": "sourceFabricAdapter",
    "attribute": {
        "deviceSpecificInformation": {
            "type": "eeCard",
            "id": "12345",
            "status": "sfa",
            "groupId": 16,
            "linkStatus0": "up",
            "linkStatus1": "down",
            "notificationStatus0": ["up", "down"],
            "notificationStatus1": ["down", "down"],
            "switchName": "AD102GL",
        }
    },
    "bitRate": "115200",
    "controllers": [
        {
            "capability": {
                "dataCenterBridging": {"capable": True},
                "networkDeviceFunctionCount": 8,
                "networkPortCount": 2,
                "npar": {"capable": True, "enabled": False},
                "npiv": {"maxDeviceLogins": 4, "maxPortLogins": 2},
                "virtualizationOffload": {
                    "virtualFunction": {"deviceMaxCount": 256, "networkPortMaxCount": 128, "minAssignmentGroupSize": 4},
                    "sriov": {"VEPACapable": True},
                },
            },
            "firmwarePackageVersion": "7.4.10",
            "identifiers": [{"durableNameFormat": "NAA", "durableName": "345C59DBD970859C"}],
            "location": {
                "partLocation": {
                    "serviceLabel": "Slot 1",
                    "type": "Slot",
                    "ordinalValue": 0,
                    "reference": "Rear",
                    "orientation": "LeftToRight",
                }
            },
            "PCIeInterface": {"lanesInUse": 1, "maxLanes": 4, "PCIeType": "Gen2", "maxPCIeType": "Gen3"},
        }
    ],
    "constraints": {
        "nonRemovableDevices": [
            {
                "deviceID": "0001",
            },
        ],
    },
    "deviceEnabled": True,
    "ethernet": {
        "MACAddress": "00:0C:29:9A:98:ED",
        "MTUSize": 1500,
        "MTUSizeMaximum": 2500,
        "permanentMACAddress": "00:0C:29:9A:98:ED",
        "vlan": {"enable": True, "id": 101},
    },
    "limits": [
        {
            "burstBytesPerSecond": 1,
            "burstPacketsPerSecond": 2,
            "direction": "Ingress",
            "sustainedBytesPerSecond": 3,
            "sustainedPacketsPerSecond": 4,
        }
    ],
    "functionMaxBandwidths": [{"allocationPercent": 80}],
    "functionMinBandwidths": [{"allocationPercent": 80}],
    "maxSpeedGbps": 48,
    "linkConfigurations": [{"capableLinkSpeedsGbps": [1, 2.2, 3]}],
    "links": [{"type": "CPU", "deviceID": "0001"}],
    "networkAdapterSerialNumber": "003BFLRT00023234",
    "networkAdapterManufacturer": "Contoso",
    "networkAdapterModel": "599TPS-T",
    "fabricAdapterSerialNumber": "003BFLRT00023234",
    "fabricAdapterManufacturer": "Contoso",
    "fabricAdapterModel": "599TPS-T",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": False,
    "PCIeVendorID": "vendor001",
    "PCIeDeviceID": "device002",
    "PCIeDeviceSerialNumber": "serial003",
    "model": "599TPS-T",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# RESP FA No Link
RESP_FA_NO_LINK = {
    "deviceID": "3101",
    "type": "sourceFabricAdapter",
    "attribute": {
        "deviceSpecificInformation": {
            "type": "eeCard",
            "id": "12345",
            "status": "sfa",
            "groupId": 16,
            "linkStatus0": "up",
            "linkStatus1": "down",
            "notificationStatus0": ["up", "down"],
            "notificationStatus1": ["down", "down"],
            "switchName": "AD102GL",
        }
    },
    "bitRate": "115200",
    "controllers": [
        {
            "capability": {
                "dataCenterBridging": {"capable": True},
                "networkDeviceFunctionCount": 8,
                "networkPortCount": 2,
                "npar": {"capable": True, "enabled": False},
                "npiv": {"maxDeviceLogins": 4, "maxPortLogins": 2},
                "virtualizationOffload": {
                    "virtualFunction": {"deviceMaxCount": 256, "networkPortMaxCount": 128, "minAssignmentGroupSize": 4},
                    "sriov": {"VEPACapable": True},
                },
            },
            "firmwarePackageVersion": "7.4.10",
            "identifiers": [{"durableNameFormat": "NAA", "durableName": "345C59DBD970859C"}],
            "location": {
                "partLocation": {
                    "serviceLabel": "Slot 1",
                    "type": "Slot",
                    "ordinalValue": 0,
                    "reference": "Rear",
                    "orientation": "LeftToRight",
                }
            },
            "PCIeInterface": {"lanesInUse": 1, "maxLanes": 4, "PCIeType": "Gen2", "maxPCIeType": "Gen3"},
        }
    ],
    "deviceEnabled": True,
    "ethernet": {
        "MACAddress": "00:0C:29:9A:98:ED",
        "MTUSize": 1500,
        "MTUSizeMaximum": 2500,
        "permanentMACAddress": "00:0C:29:9A:98:ED",
        "vlan": {"enable": True, "id": 101},
    },
    "limits": [
        {
            "burstBytesPerSecond": 1,
            "burstPacketsPerSecond": 2,
            "direction": "Ingress",
            "sustainedBytesPerSecond": 3,
            "sustainedPacketsPerSecond": 4,
        }
    ],
    "functionMaxBandwidths": [{"allocationPercent": 80}],
    "functionMinBandwidths": [{"allocationPercent": 80}],
    "maxSpeedGbps": 48,
    "linkConfigurations": [{"capableLinkSpeedsGbps": [1, 2.2, 3]}],
    "networkAdapterSerialNumber": "003BFLRT00023234",
    "networkAdapterManufacturer": "Contoso",
    "networkAdapterModel": "599TPS-T",
    "fabricAdapterSerialNumber": "003BFLRT00023234",
    "fabricAdapterManufacturer": "Contoso",
    "fabricAdapterModel": "599TPS-T",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": False,
    "PCIeVendorID": "vendor001",
    "PCIeDeviceID": "device002",
    "PCIeDeviceSerialNumber": "serial003",
    "model": "599TPS-T",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# RESP FA int value
RESP_FA_INT = {"deviceID": "3101", "type": "sourceFabricAdapter", "maxSpeedGbps": 12}

# RESP FA float value
RESP_FA_FLOAT = {"deviceID": "3101", "type": "sourceFabricAdapter", "maxSpeedGbps": 34.56}

# OOB_DATA NA Link present
OOB_DATA_NA_LINK = {
    "devices": [
        {
            "type": "destinationFabricAdapter",
            "deviceID": "3201",
            "schema": {
                "attribute": {
                    "deviceSpecificInformation": {
                        "type": "eeCard",
                        "id": "12345",
                        "status": "dfa",
                        "groupId": 16,
                        "linkStatus0": "up",
                        "linkStatus1": "down",
                        "notificationStatus0": ["up", "down"],
                        "notificationStatus1": ["down", "down"],
                        "switchName": "AD102GL",
                    },
                },
                "SerialInterfaces": {"BitRate": "115200"},
                "Network": {
                    "@odata.type": "#NetworkAdapter.v1_9_0.NetworkAdapter",
                    "Id": "9fa725a1",
                    "Name": "Network Adapter View",
                    "Manufacturer": "Contoso",
                    "Model": "599TPS-T",
                    "SKU": "Contoso TPS-Net 2-Port Base-T",
                    "SerialNumber": "003BFLRT00023234",
                    "PartNumber": "975421-B20",
                    "Ports": [],
                    "NetworkDeviceFunctions": [],
                    "PowerState": "On",
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "PowerCapability": False,
                    "Controllers": [
                        {
                            "FirmwarePackageVersion": "7.4.10",
                            "ControllerCapabilities": {
                                "NetworkPortCount": 2,
                                "NetworkDeviceFunctionCount": 8,
                                "DataCenterBridging": {"Capable": True},
                                "VirtualizationOffload": {
                                    "VirtualFunction": {
                                        "DeviceMaxCount": 256,
                                        "NetworkPortMaxCount": 128,
                                        "MinAssignmentGroupSize": 4,
                                    },
                                    "SRIOV": {"SRIOVVEPACapable": True},
                                },
                                "NPIV": {"MaxDeviceLogins": 4, "MaxPortLogins": 2},
                                "NPAR": {"NparCapable": True, "NparEnabled": False},
                            },
                            "PCIeInterface": {
                                "PCIeType": "Gen2",
                                "MaxPCIeType": "Gen3",
                                "LanesInUse": 1,
                                "MaxLanes": 4,
                            },
                            "Identifiers": [{"DurableNameFormat": "NAA", "DurableName": "345C59DBD970859C"}],
                            "Location": {
                                "PartLocation": {
                                    "ServiceLabel": "Slot 1",
                                    "LocationType": "Slot",
                                    "LocationOrdinalValue": 0,
                                    "Reference": "Rear",
                                    "Orientation": "LeftToRight",
                                }
                            },
                        }
                    ],
                    "@odata.id": "/redfish/v1/Chassis/Chassis-1/NetworkAdapters/NIC-3001",
                },
                "PCIeDevice": {
                    "SerialNumber": "serial003",
                },
                "PCIeFunction": {
                    "DeviceId": "device002",
                    "VendorId": "vendor001",
                },
                "NetworkDeviceFunctions": {
                    "DeviceEnabled": True,
                    "Ethernet": {
                        "MACAddress": "00:0C:29:9A:98:ED",
                        "MTUSize": 1500,
                        "MTUSizeMaximum": 2500,
                        "PermanentMACAddress": "00:0C:29:9A:98:ED",
                        "VLAN": {"VLANEnable": True, "VLANId": 101},
                    },
                    "Limits": [
                        {
                            "BurstBytesPerSecond": 1,
                            "BurstPacketsPerSecond": 2,
                            "Direction": "Ingress",
                            "SustainedBytesPerSecond": 3,
                            "SustainedPacketsPerSecond": 4,
                        }
                    ],
                },
                "Port": {
                    "FunctionMaxBandwidth": [{"AllocationPercent": 80}],
                    "FunctionMinBandwidth": [{"AllocationPercent": 80}],
                    "MaxSpeedGbps": 48,
                    "LinkConfiguration": [{"CapableLinkSpeedGbps": [1, 2.2, 3]}],
                },
            },
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "time": "2023-07-06T05:55:55Z",
        }
    ]
}

# OOB_DATA NA No Link
OOB_DATA_NA_NO_LINK = {
    "devices": [
        {
            "type": "destinationFabricAdapter",
            "deviceID": "3201",
            "schema": {
                "attribute": {
                    "deviceSpecificInformation": {
                        "type": "eeCard",
                        "id": "12345",
                        "status": "dfa",
                        "groupId": 16,
                        "linkStatus0": "up",
                        "linkStatus1": "down",
                        "notificationStatus0": ["up", "down"],
                        "notificationStatus1": ["down", "down"],
                        "switchName": "AD102GL",
                    },
                },
                "SerialInterfaces": {"BitRate": "115200"},
                "Network": {
                    "@odata.type": "#NetworkAdapter.v1_9_0.NetworkAdapter",
                    "Id": "9fa725a1",
                    "Name": "Network Adapter View",
                    "Manufacturer": "Contoso",
                    "Model": "599TPS-T",
                    "SKU": "Contoso TPS-Net 2-Port Base-T",
                    "SerialNumber": "003BFLRT00023234",
                    "PartNumber": "975421-B20",
                    "Ports": [],
                    "NetworkDeviceFunctions": [],
                    "PowerState": "On",
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "PowerCapability": False,
                    "Controllers": [
                        {
                            "FirmwarePackageVersion": "7.4.10",
                            "ControllerCapabilities": {
                                "NetworkPortCount": 2,
                                "NetworkDeviceFunctionCount": 8,
                                "DataCenterBridging": {"Capable": True},
                                "VirtualizationOffload": {
                                    "VirtualFunction": {
                                        "DeviceMaxCount": 256,
                                        "NetworkPortMaxCount": 128,
                                        "MinAssignmentGroupSize": 4,
                                    },
                                    "SRIOV": {"SRIOVVEPACapable": True},
                                },
                                "NPIV": {"MaxDeviceLogins": 4, "MaxPortLogins": 2},
                                "NPAR": {"NparCapable": True, "NparEnabled": False},
                            },
                            "PCIeInterface": {
                                "PCIeType": "Gen2",
                                "MaxPCIeType": "Gen3",
                                "LanesInUse": 1,
                                "MaxLanes": 4,
                            },
                            "Identifiers": [{"DurableNameFormat": "NAA", "DurableName": "345C59DBD970859C"}],
                            "Location": {
                                "PartLocation": {
                                    "ServiceLabel": "Slot 1",
                                    "LocationType": "Slot",
                                    "LocationOrdinalValue": 0,
                                    "Reference": "Rear",
                                    "Orientation": "LeftToRight",
                                }
                            },
                        }
                    ],
                    "@odata.id": "/redfish/v1/Chassis/Chassis-1/NetworkAdapters/NIC-3001",
                },
                "PCIeDevice": {
                    "SerialNumber": "serial003",
                },
                "PCIeFunction": {
                    "DeviceId": "device002",
                    "VendorId": "vendor001",
                },
                "NetworkDeviceFunctions": {
                    "DeviceEnabled": True,
                    "Ethernet": {
                        "MACAddress": "00:0C:29:9A:98:ED",
                        "MTUSize": 1500,
                        "MTUSizeMaximum": 2500,
                        "PermanentMACAddress": "00:0C:29:9A:98:ED",
                        "VLAN": {"VLANEnable": True, "VLANId": 101},
                    },
                    "Limits": [
                        {
                            "BurstBytesPerSecond": 1,
                            "BurstPacketsPerSecond": 2,
                            "Direction": "Ingress",
                            "SustainedBytesPerSecond": 3,
                            "SustainedPacketsPerSecond": 4,
                        }
                    ],
                },
                "Port": {
                    "FunctionMaxBandwidth": [{"AllocationPercent": 80}],
                    "FunctionMinBandwidth": [{"AllocationPercent": 80}],
                    "MaxSpeedGbps": 48,
                    "LinkConfiguration": [{"CapableLinkSpeedGbps": [1, 2.2, 3]}],
                },
            },
            "time": "2023-07-06T05:55:55Z",
        }
    ]
}

# OOB_DATA NA int value
OOB_DATA_NA_INT = {
    "devices": [{"type": "destinationFabricAdapter", "deviceID": "3201", "schema": {"Port": {"MaxSpeedGbps": 12}}}]
}

# OOB_DATA NA float value
OOB_DATA_NA_FLOAT = {
    "devices": [{"type": "destinationFabricAdapter", "deviceID": "3201", "schema": {"Port": {"MaxSpeedGbps": 34.56}}}]
}

# FM_DATA networkInterface Link present
FM_DATA_NA_LINK = {
    "data": [
        {
            "deviceID": "3201",
            "type": "destinationFabricAdapter",
            "PCIeVendorId": "vendor001",
            "PCIeDeviceId": "device002",
            "PCIeDeviceSerialNumber": "serial003",
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "devicePortList": [
                {
                    "fabricId": "NEC-01",
                    "LTSSMState": "L0",
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "USP",
                },
                {
                    "fabricId": "NEC-02",
                    "LTSSMState": "L2",
                    "switchId": "fmsw-02",
                    "switchPortNumber": "2",
                    "switchPortType": "USP",
                },
            ],
        }
    ]
}

# FM_DATA networkInterface No Link
FM_DATA_NA_NO_LINK = {
    "data": [
        {
            "deviceID": "3201",
            "type": "destinationFabricAdapter",
            "PCIeVendorId": "vendor001",
            "PCIeDeviceId": "device002",
            "PCIeDeviceSerialNumber": "serial003",
            "devicePortList": [
                {
                    "fabricId": "NEC-01",
                    "LTSSMState": "L0",
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "USP",
                },
                {
                    "fabricId": "NEC-02",
                    "LTSSMState": "L2",
                    "switchId": "fmsw-02",
                    "switchPortNumber": "2",
                    "switchPortType": "USP",
                },
            ],
        }
    ]
}

# RESP NA Link present
RESP_NA_LINK = {
    "deviceID": "3201",
    "type": "destinationFabricAdapter",
    "attribute": {
        "deviceSpecificInformation": {
            "type": "eeCard",
            "id": "12345",
            "status": "dfa",
            "groupId": 16,
            "linkStatus0": "up",
            "linkStatus1": "down",
            "notificationStatus0": ["up", "down"],
            "notificationStatus1": ["down", "down"],
            "switchName": "AD102GL",
        }
    },
    "bitRate": "115200",
    "controllers": [
        {
            "capability": {
                "dataCenterBridging": {"capable": True},
                "networkDeviceFunctionCount": 8,
                "networkPortCount": 2,
                "npar": {"capable": True, "enabled": False},
                "npiv": {"maxDeviceLogins": 4, "maxPortLogins": 2},
                "virtualizationOffload": {
                    "virtualFunction": {"deviceMaxCount": 256, "networkPortMaxCount": 128, "minAssignmentGroupSize": 4},
                    "sriov": {"VEPACapable": True},
                },
            },
            "firmwarePackageVersion": "7.4.10",
            "identifiers": [{"durableNameFormat": "NAA", "durableName": "345C59DBD970859C"}],
            "location": {
                "partLocation": {
                    "serviceLabel": "Slot 1",
                    "type": "Slot",
                    "ordinalValue": 0,
                    "reference": "Rear",
                    "orientation": "LeftToRight",
                }
            },
            "PCIeInterface": {"lanesInUse": 1, "maxLanes": 4, "PCIeType": "Gen2", "maxPCIeType": "Gen3"},
        }
    ],
    "deviceEnabled": True,
    "ethernet": {
        "MACAddress": "00:0C:29:9A:98:ED",
        "MTUSize": 1500,
        "MTUSizeMaximum": 2500,
        "permanentMACAddress": "00:0C:29:9A:98:ED",
        "vlan": {"enable": True, "id": 101},
    },
    "limits": [
        {
            "burstBytesPerSecond": 1,
            "burstPacketsPerSecond": 2,
            "direction": "Ingress",
            "sustainedBytesPerSecond": 3,
            "sustainedPacketsPerSecond": 4,
        }
    ],
    "functionMaxBandwidths": [{"allocationPercent": 80}],
    "functionMinBandwidths": [{"allocationPercent": 80}],
    "maxSpeedGbps": 48,
    "linkConfigurations": [{"capableLinkSpeedsGbps": [1, 2.2, 3]}],
    "links": [{"type": "CPU", "deviceID": "0001"}],
    "networkAdapterSerialNumber": "003BFLRT00023234",
    "networkAdapterManufacturer": "Contoso",
    "networkAdapterModel": "599TPS-T",
    "fabricAdapterSerialNumber": "003BFLRT00023234",
    "fabricAdapterManufacturer": "Contoso",
    "fabricAdapterModel": "599TPS-T",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": False,
    "PCIeVendorID": "vendor001",
    "PCIeDeviceID": "device002",
    "PCIeDeviceSerialNumber": "serial003",
    "model": "599TPS-T",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# RESP NA No Link
RESP_NA_NO_LINK = {
    "deviceID": "3201",
    "type": "destinationFabricAdapter",
    "attribute": {
        "deviceSpecificInformation": {
            "type": "eeCard",
            "id": "12345",
            "status": "dfa",
            "groupId": 16,
            "linkStatus0": "up",
            "linkStatus1": "down",
            "notificationStatus0": ["up", "down"],
            "notificationStatus1": ["down", "down"],
            "switchName": "AD102GL",
        }
    },
    "bitRate": "115200",
    "controllers": [
        {
            "capability": {
                "dataCenterBridging": {"capable": True},
                "networkDeviceFunctionCount": 8,
                "networkPortCount": 2,
                "npar": {"capable": True, "enabled": False},
                "npiv": {"maxDeviceLogins": 4, "maxPortLogins": 2},
                "virtualizationOffload": {
                    "virtualFunction": {"deviceMaxCount": 256, "networkPortMaxCount": 128, "minAssignmentGroupSize": 4},
                    "sriov": {"VEPACapable": True},
                },
            },
            "firmwarePackageVersion": "7.4.10",
            "identifiers": [{"durableNameFormat": "NAA", "durableName": "345C59DBD970859C"}],
            "location": {
                "partLocation": {
                    "serviceLabel": "Slot 1",
                    "type": "Slot",
                    "ordinalValue": 0,
                    "reference": "Rear",
                    "orientation": "LeftToRight",
                }
            },
            "PCIeInterface": {"lanesInUse": 1, "maxLanes": 4, "PCIeType": "Gen2", "maxPCIeType": "Gen3"},
        }
    ],
    "deviceEnabled": True,
    "ethernet": {
        "MACAddress": "00:0C:29:9A:98:ED",
        "MTUSize": 1500,
        "MTUSizeMaximum": 2500,
        "permanentMACAddress": "00:0C:29:9A:98:ED",
        "vlan": {"enable": True, "id": 101},
    },
    "limits": [
        {
            "burstBytesPerSecond": 1,
            "burstPacketsPerSecond": 2,
            "direction": "Ingress",
            "sustainedBytesPerSecond": 3,
            "sustainedPacketsPerSecond": 4,
        }
    ],
    "functionMaxBandwidths": [{"allocationPercent": 80}],
    "functionMinBandwidths": [{"allocationPercent": 80}],
    "maxSpeedGbps": 48,
    "linkConfigurations": [{"capableLinkSpeedsGbps": [1, 2.2, 3]}],
    "networkAdapterSerialNumber": "003BFLRT00023234",
    "networkAdapterManufacturer": "Contoso",
    "networkAdapterModel": "599TPS-T",
    "fabricAdapterSerialNumber": "003BFLRT00023234",
    "fabricAdapterManufacturer": "Contoso",
    "fabricAdapterModel": "599TPS-T",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": False,
    "PCIeVendorID": "vendor001",
    "PCIeDeviceID": "device002",
    "PCIeDeviceSerialNumber": "serial003",
    "model": "599TPS-T",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# RESP NA int value
RESP_NA_INT = {"deviceID": "3201", "type": "destinationFabricAdapter", "maxSpeedGbps": 12}

# RESP NA float value
RESP_NA_FLOAT = {"deviceID": "3201", "type": "destinationFabricAdapter", "maxSpeedGbps": 34.56}

# OOB_DATA GPU Link present
OOB_DATA_GPU_LINK = {
    "devices": [
        {
            "type": "GPU",
            "deviceID": "4001",
            "schema": {
                "Name": "Processor",
                "Id": "PROC-0001",
                "ProcessorType": "GPU",
                "ProcessorArchitecture": "x86",
                "InstructionSet": "x86-64",
                "Manufacturer": "Intel(R) Corporation",
                "Model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
                "ProcessorId": {
                    "VendorId": "GenuineIntel",
                    "IdentificationRegisters": "0x34AC34DC8901274A",
                    "EffectiveFamily": "0x42",
                    "EffectiveModel": "0x61",
                    "Step": "0x1",
                    "MicrocodeInfo": "0x429943",
                    "ProtectedIdentificationNumber": "123456",
                },
                "PowerState": "On",
                "PowerCapability": True,
                "ProcessorIndex": "xxx",
                "Replaceable": True,
                "SerialNumber": "GPU1",
                "Socket": "CPU 1",
                "Links": {
                    "Chassis": {"@odata.id": "/redfish/v1/Chassis/Chassis-1"},
                    "ConnectedProcessors": {"@odata.id": "/redfish/v1/System/System-1/Processors/PROC-0001"},
                    "GraphicsController": {"@odata.id": "{rb}{suffix}/{suffix_id}/GraphicsControllers/{gs_id}"},
                    "NetworkDeviceFunctions": {
                        "@odata.id": "{rb}Chassis/{chassis_id}/NetworkAdapters/ \
                              {NetworkAdapterId}/NetworkDeviceFunctions/{NetworkDeviceFunctionId}"
                    },
                    "FabricAdapters": {"@odata.id": "{rb}Chassis/{chassis_id}/FabricAdapters/{FabricAdaptersId}"},
                    "PCIeDevice": {"@odata.id": "{rb}{suffix}/{suffix_id}/PCIeDevices/{PCIeDeviceId}"},
                    "Memory": [{"@odata.id": "/redfish/v1/Chassis/Chassis-1/Memory/MEM-1001"}],
                },
                "MaxSpeedMHz": 2200,
                "TotalCores": 8,
                "TotalThreads": 16,
                "TotalEnabledCores": 8,
                "BaseSpeedMHz": 1200,
                "OperatingSpeedMHz": 1000,
                "TDPWatts": 100,
                "ProcessorMemory": [
                    {"CapacityMiB": 123, "IntegratedMemory": True, "MemoryType": "DDR", "SpeedMHz": 1200}
                ],
                "MemorySummary": {
                    "MemoryMirroring": None,
                    "Metrics": {"@odata.id": "{rb}{suffix}/{suffix_id}/Memory/{memory_id}/MemoryMetrics"},
                    "Status": {},
                    "TotalCacheSizeMiB": 4096,
                    "TotalMemorySizeMiB": 8192,
                    "ECCModeEnabled": True,
                },
                "Metrics": {"@odata.id": "{rb}{suffix}/{suffix_id}/Processors/{ProcessorId}/ProcessorMetrics"},
                "EnvironmentMetrics": {
                    "@odata.id": "{rb}{suffix}/{suffix_id}/Processors/{ProcessorId}/EnvironmentMetrics"
                },
                "Status": {"Health": "OK", "State": "Enabled"},
            },
            "link": [{"type": "graphicController", "deviceID": "5001"}],
            "time": "2023-07-06T05:55:55Z",
        }
    ]
}

# OOB_DATA GPU No Link
OOB_DATA_GPU_NO_LINK = {
    "devices": [
        {
            "type": "GPU",
            "deviceID": "4001",
            "schema": {
                "@odata.context": "/redfish/v1/$metadata#Processor.Processor",
                "@odata.type": "#Processor.1_0_0.Processor",
                "@odata.id": "/redfish/v1/System/System-1/Processors/PROC-0001",
                "Name": "Processor",
                "Id": "PROC-0001",
                "ProcessorType": "GPU",
                "ProcessorArchitecture": "x86",
                "InstructionSet": "x86-64",
                "Manufacturer": "Intel(R) Corporation",
                "Model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
                "ProcessorId": {
                    "VendorId": "GenuineIntel",
                    "IdentificationRegisters": "0x34AC34DC8901274A",
                    "EffectiveFamily": "0x42",
                    "EffectiveModel": "0x61",
                    "Step": "0x1",
                    "MicrocodeInfo": "0x429943",
                    "ProtectedIdentificationNumber": "123456",
                },
                "PowerState": "On",
                "PowerCapability": True,
                "ProcessorIndex": "xxx",
                "Replaceable": True,
                "SerialNumber": "GPU1",
                "Socket": "CPU 1",
                "MaxSpeedMHz": 2200,
                "TotalCores": 8,
                "TotalThreads": 16,
                "TotalEnabledCores": 8,
                "BaseSpeedMHz": 1200,
                "OperatingSpeedMHz": 1000,
                "TDPWatts": 100,
                "ProcessorMemory": [
                    {"CapacityMiB": 123, "IntegratedMemory": True, "MemoryType": "DDR", "SpeedMHz": 1200}
                ],
                "MemorySummary": {
                    "MemoryMirroring": None,
                    "Metrics": {"@odata.id": "{rb}{suffix}/{suffix_id}/Memory/{memory_id}/MemoryMetrics"},
                    "Status": {},
                    "TotalCacheSizeMiB": 4096,
                    "TotalMemorySizeMiB": 8192,
                    "ECCModeEnabled": True,
                },
                "Metrics": {"@odata.id": "{rb}{suffix}/{suffix_id}/Processors/{ProcessorId}/ProcessorMetrics"},
                "EnvironmentMetrics": {
                    "@odata.id": "{rb}{suffix}/{suffix_id}/Processors/{ProcessorId}/EnvironmentMetrics"
                },
                "Status": {"Health": "OK", "State": "Enabled"},
            },
            "time": "2023-07-06T05:55:55Z",
        }
    ]
}

# FM_DATA GPU Link present
FM_DATA_GPU_LINK = {
    "data": [
        {
            "deviceID": "4001",
            "type": "GPU",
            "PCIeVendorId": "vendor001",
            "PCIeDeviceId": "device002",
            "PCIeDeviceSerialNumber": "serial003",
            "link": [{"deviceID": "2001", "type": "storage"}, {"deviceID": "3001", "type": "networkInterface"}],
            "devicePortList": [
                {
                    "fabricId": "NEC-01",
                    "LTSSMState": "L0",
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "USP",
                },
                {
                    "fabricId": "NEC-02",
                    "LTSSMState": "L2",
                    "switchId": "fmsw-02",
                    "switchPortNumber": "2",
                    "switchPortType": "USP",
                },
            ],
        }
    ]
}

# FM_DATA GPU No Link
FM_DATA_GPU_NO_LINK = {
    "data": [
        {
            "deviceID": "4001",
            "type": "GPU",
            "PCIeVendorId": "vendor001",
            "PCIeDeviceId": "device002",
            "PCIeDeviceSerialNumber": "serial003",
            "devicePortList": [
                {
                    "fabricId": "NEC-01",
                    "LTSSMState": "L0",
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "USP",
                },
                {
                    "fabricId": "NEC-02",
                    "LTSSMState": "L2",
                    "switchId": "fmsw-02",
                    "switchPortNumber": "2",
                    "switchPortType": "USP",
                },
            ],
        }
    ]
}

# RESP GPU Link present
RESP_GPU_LINK = {
    "deviceID": "4001",
    "type": "GPU",
    "baseSpeedMHz": 1200,
    "operatingSpeedMHz": 1000,
    "TDPWatts": 100,
    "totalCores": 8,
    "totalEnabledCores": 8,
    "totalThreads": 16,
    "processorMemories": [{"capacityMiB": 123, "integrated": True, "type": "DDR", "speedMHz": 1200}],
    "memorySummary": {"ECCModeEnabled": True, "totalCacheSizeMiB": 4096, "totalMemorySizeMiB": 8192},
    "status": {"health": "OK", "state": "Enabled"},
    "powerState": "On",
    "powerCapability": True,
    "instructionSet": "x86-64",
    "processorArchitecture": "x86",
    "processorID": {
        "effectiveFamily": "0x42",
        "effectiveModel": "0x61",
        "identificationRegister": "0x34AC34DC8901274A",
        "microcodeInfo": "0x429943",
        "protectedIdentificationNumber": "123456",
        "step": "0x1",
        "vendorID": "GenuineIntel",
    },
    "links": [
        {"deviceID": "2001", "type": "storage"},
        {"deviceID": "3001", "type": "networkInterface"},
        {"deviceID": "5001", "type": "graphicController"},
    ],
    "serialNumber": "GPU1",
    "manufacturer": "Intel(R) Corporation",
    "model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
    "PCIeVendorID": "vendor001",
    "PCIeDeviceID": "device002",
    "PCIeDeviceSerialNumber": "serial003",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# RESP GPU Link present
RESP_GPU_LINK_OOB_ONLY = {
    "deviceID": "4001",
    "type": "GPU",
    "baseSpeedMHz": 1200,
    "operatingSpeedMHz": 1000,
    "TDPWatts": 100,
    "totalCores": 8,
    "totalEnabledCores": 8,
    "totalThreads": 16,
    "processorMemories": [{"capacityMiB": 123, "integrated": True, "type": "DDR", "speedMHz": 1200}],
    "memorySummary": {"ECCModeEnabled": True, "totalCacheSizeMiB": 4096, "totalMemorySizeMiB": 8192},
    "status": {"health": "OK", "state": "Enabled"},
    "powerState": "On",
    "powerCapability": True,
    "instructionSet": "x86-64",
    "processorArchitecture": "x86",
    "processorID": {
        "effectiveFamily": "0x42",
        "effectiveModel": "0x61",
        "identificationRegister": "0x34AC34DC8901274A",
        "microcodeInfo": "0x429943",
        "protectedIdentificationNumber": "123456",
        "step": "0x1",
        "vendorID": "GenuineIntel",
    },
    "links": [{"deviceID": "5001", "type": "graphicController"}],
    "serialNumber": "GPU1",
    "manufacturer": "Intel(R) Corporation",
    "model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
    "PCIeVendorID": "vendor001",
    "PCIeDeviceID": "device002",
    "PCIeDeviceSerialNumber": "serial003",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# RESP GPU No Link
RESP_GPU_NO_LINK = {
    "deviceID": "4001",
    "type": "GPU",
    "baseSpeedMHz": 1200,
    "operatingSpeedMHz": 1000,
    "TDPWatts": 100,
    "totalCores": 8,
    "totalEnabledCores": 8,
    "totalThreads": 16,
    "processorMemories": [{"capacityMiB": 123, "integrated": True, "type": "DDR", "speedMHz": 1200}],
    "memorySummary": {"ECCModeEnabled": True, "totalCacheSizeMiB": 4096, "totalMemorySizeMiB": 8192},
    "status": {"health": "OK", "state": "Enabled"},
    "powerState": "On",
    "powerCapability": True,
    "instructionSet": "x86-64",
    "processorArchitecture": "x86",
    "processorID": {
        "effectiveFamily": "0x42",
        "effectiveModel": "0x61",
        "identificationRegister": "0x34AC34DC8901274A",
        "microcodeInfo": "0x429943",
        "protectedIdentificationNumber": "123456",
        "step": "0x1",
        "vendorID": "GenuineIntel",
    },
    "serialNumber": "GPU1",
    "manufacturer": "Intel(R) Corporation",
    "model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
    "PCIeVendorID": "vendor001",
    "PCIeDeviceID": "device002",
    "PCIeDeviceSerialNumber": "serial003",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}

# OOB_DATA graphicController
OOB_DATA_GC = {
    "devices": [
        {
            "type": "graphicController",
            "deviceID": "5001",
            "schema": {
                "BiosVersion": "1.0",
                "DriverVersion": "2.0",
                "SerialNumber": "GC1",
                "Manufacturer": "Intel(R) Corporation",
                "Model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
                "Status": {"Health": "OK", "State": "Enabled"},
            },
            "link": [{"type": "GPU", "deviceID": "4001"}],
            "time": "2023-07-06T05:55:55Z",
        }
    ]
}

# FM_DATA graphicController
FM_DATA_GC = {"data": [{"deviceID": "5001", "type": "graphicController"}]}

# RESP graphicController
RESP_GC = {
    "deviceID": "5001",
    "type": "graphicController",
    "biosVersion": "1.0",
    "driverVersion": "2.0",
    "status": {"health": "OK", "state": "Enabled"},
    "links": [{"deviceID": "4001", "type": "GPU"}],
    "serialNumber": "GC1",
    "manufacturer": "Intel(R) Corporation",
    "model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
}

# OOB unknown device Link present
OOB_DATA_UNKNOWN_LINK = {
    "devices": [
        {
            "type": "unknown",
            "deviceID": "7001",
            "schema": {
                "attribute": {
                    "deviceSpecificInformation": {
                        "id": "12345",
                        "firmwareversion": "86.07.6B.00.01",
                        "name": "Quadro P400",
                    },
                },
                "SerialNumber": "TJ27JXQY",
                "Manufacturer": "Generic",
                "Model": "Modelxxx",
                "Status": {"Health": "OK", "State": "Enabled"},
                "PowerState": "On",
                "PowerCapability": False,
            },
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "time": "2023-07-06T05:55:55Z",
        }
    ]
}

# OOB unknown device no Link
OOB_DATA_UNKNOWN_NO_LINK = {
    "devices": [
        {
            "type": "unknown",
            "deviceID": "7001",
            "schema": {
                "attribute": {
                    "deviceSpecificInformation": {
                        "id": "12345",
                        "firmwareversion": "86.07.6B.00.01",
                        "name": "Quadro P400",
                    },
                },
                "SerialNumber": "TJ27JXQY",
                "Manufacturer": "Generic",
                "Model": "Modelxxx",
                "Status": {"Health": "OK", "State": "Enabled"},
                "PowerState": "On",
                "PowerCapability": True,
            },
            "time": "2023-07-06T05:55:55Z",
        }
    ]
}

# FM_DATA unknown Link present
FM_DATA_UNKNOWN_LINK = {
    "data": [
        {
            "deviceID": "7001",
            "type": "unknown",
            "link": [{"type": "GPU", "deviceID": "4001"}],
            "devicePortList": [
                {
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "DSP",
                },
            ],
        }
    ]
}

# FM_DATA unknown no Link
FM_DATA_UNKNOWN_NO_LINK = {
    "data": [
        {
            "deviceID": "7001",
            "type": "unknown",
            "devicePortList": [
                {
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "DSP",
                },
            ],
        }
    ]
}

# RESP unknown Link present
RESP_UNKNOWN_LINK = {
    "deviceID": "7001",
    "type": "unknown",
    "attribute": {
        "deviceSpecificInformation": {
            "id": "12345",
            "firmware_version": "86.07.6B.00.01",
            "name": "Quadro P400",
        }
    },
    "links": [{"type": "CPU", "deviceID": "0001"}, {"type": "GPU", "deviceID": "4001"}],
    "serialNumber": "TJ27JXQY",
    "manufacturer": "Generic",
    "model": "Modelxxx",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": False,
    "devicePortList": [
        {
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "DSP",
        },
    ],
}

# RESP unknown Link present
RESP_UNKNOWN_FMVALID_TRUE_LINK = {
    "deviceID": "7001",
    "type": "unknown",
    "attribute": {
        "deviceSpecificInformation": {
            "id": "12345",
            "firmware_version": "86.07.6B.00.01",
            "name": "Quadro P400",
        }
    },
    "links": [{"type": "CPU", "deviceID": "0001"}],
    "serialNumber": "TJ27JXQY",
    "manufacturer": "Generic",
    "model": "Modelxxx",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": False,
    "devicePortList": [
        {
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "DSP",
        },
    ],
}

# RESP unknown Link present
RESP_UNKNOWN_FMVALID_FALSE_LINK = {
    "deviceID": "7001",
    "type": "unknown",
    "attribute": {
        "deviceSpecificInformation": {
            "id": "12345",
            "firmware_version": "86.07.6B.00.01",
            "name": "Quadro P400",
        }
    },
    "links": [{"type": "GPU", "deviceID": "4001"}],
    "serialNumber": "TJ27JXQY",
    "manufacturer": "Generic",
    "model": "Modelxxx",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": True,
    "devicePortList": [
        {
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "DSP",
        },
    ],
}

# RESP unknown No Link
RESP_UNKNOWN_NO_LINK = {
    "deviceID": "7001",
    "type": "unknown",
    "attribute": {
        "deviceSpecificInformation": {
            "id": "12345",
            "firmware_version": "86.07.6B.00.01",
            "name": "Quadro P400",
        }
    },
    "serialNumber": "TJ27JXQY",
    "manufacturer": "Generic",
    "model": "Modelxxx",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": True,
    "devicePortList": [
        {
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "DSP",
        },
    ],
}

# OOB_DATA FA and PCIe device Link present
OOB_DATA_FA_PCIE_DEVICE_1 = {
    "devices": [
        {
            "type": "sourceFabricAdapter",
            "deviceID": "3101",
            "schema": {
                "attribute": {
                    "deviceSpecificInformation": {
                        "type": "eeCard",
                        "id": "12345",
                        "status": "sfa",
                        "groupId": 16,
                        "linkStatus0": "up",
                        "linkStatus1": "down",
                        "notificationStatus0": ["up", "down"],
                        "notificationStatus1": ["down", "down"],
                        "switchName": "AD102GL",
                    },
                },
                "SerialInterfaces": {"BitRate": ""},
                "Network": {
                    "@odata.type": "#NetworkAdapter.v1_9_0.NetworkAdapter",
                    "Id": "9fa725a1",
                    "Name": "Network Adapter View",
                    "Manufacturer": None,
                    "Model": "599TPS-T",
                    "SKU": "Contoso TPS-Net 2-Port Base-T",
                    "SerialNumber": "003BFLRT00023234",
                    "PartNumber": "975421-B20",
                    "Ports": [],
                    "NetworkDeviceFunctions": [],
                    "PowerState": "On",
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "PowerCapability": False,
                    "Controllers": [
                        {
                            "FirmwarePackageVersion": "7.4.10",
                            "ControllerCapabilities": {
                                "NetworkPortCount": 2,
                                "NetworkDeviceFunctionCount": 8,
                                "DataCenterBridging": {"Capable": True},
                                "VirtualizationOffload": {
                                    "VirtualFunction": {
                                        "DeviceMaxCount": 256,
                                        "NetworkPortMaxCount": 128,
                                        "MinAssignmentGroupSize": 4,
                                    },
                                    "SRIOV": {"SRIOVVEPACapable": True},
                                },
                                "NPIV": {"MaxDeviceLogins": 4, "MaxPortLogins": 2},
                                "NPAR": {"NparCapable": True, "NparEnabled": False},
                            },
                            "PCIeInterface": {
                                "PCIeType": "Gen2",
                                "MaxPCIeType": "Gen3",
                                "LanesInUse": 1,
                                "MaxLanes": 4,
                            },
                            "Identifiers": [{"DurableNameFormat": "NAA", "DurableName": "345C59DBD970859C"}],
                            "Location": {
                                "PartLocation": {
                                    "ServiceLabel": "Slot 1",
                                    "LocationType": "Slot",
                                    "LocationOrdinalValue": 0,
                                    "Reference": "Rear",
                                    "Orientation": "LeftToRight",
                                }
                            },
                        }
                    ],
                    "@odata.id": "/redfish/v1/Chassis/Chassis-1/NetworkAdapters/NIC-3001",
                },
                "PCIeDevice": {
                    "SerialNumber": "serial003",
                },
                "PCIeFunction": {
                    "DeviceId": "device002",
                    "VendorId": "vendor001",
                },
                "NetworkDeviceFunctions": {
                    "DeviceEnabled": True,
                    "Ethernet": {
                        "MACAddress": "00:0C:29:9A:98:FF",
                        "MTUSize": 1500,
                        "MTUSizeMaximum": 2500,
                        "PermanentMACAddress": "00:0C:29:9A:98:FF",
                        "VLAN": {"VLANEnable": True, "VLANId": 100},
                    },
                    "Limits": [
                        {
                            "BurstBytesPerSecond": 1,
                            "BurstPacketsPerSecond": 2,
                            "Direction": "Ingress",
                            "SustainedBytesPerSecond": 3,
                            "SustainedPacketsPerSecond": 4,
                        }
                    ],
                },
                "Port": {
                    "FunctionMaxBandwidth": [{"AllocationPercent": 80}],
                    "FunctionMinBandwidth": [{"AllocationPercent": 80}],
                    "MaxSpeedGbps": 48,
                    "LinkConfiguration": [{"CapableLinkSpeedGbps": [1, 2.2, 3]}],
                },
            },
            "time": "2023-07-06T05:55:55Z",
        },
        {
            "type": "networkInterface",
            "deviceID": "3001",
            "schema": {
                "SerialInterfaces": {"BitRate": "115200"},
                "Network": {
                    "@odata.type": "#NetworkAdapter.v1_9_0.NetworkAdapter",
                    "Id": "9fa725a1",
                    "Name": "Network Adapter View",
                    "Manufacturer": "Contoso",
                    "Model": "599TPS-T",
                    "SKU": "Contoso TPS-Net 2-Port Base-T",
                    "SerialNumber": "003BFLRT00023234",
                    "PartNumber": "975421-B20",
                    "Ports": [],
                    "NetworkDeviceFunctions": [],
                    "PowerState": "On",
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "PowerCapability": False,
                    "Controllers": [
                        {
                            "FirmwarePackageVersion": "7.4.10",
                            "ControllerCapabilities": {
                                "NetworkPortCount": 2,
                                "NetworkDeviceFunctionCount": 8,
                                "DataCenterBridging": {"Capable": True},
                                "VirtualizationOffload": {
                                    "VirtualFunction": {
                                        "DeviceMaxCount": 256,
                                        "NetworkPortMaxCount": 128,
                                        "MinAssignmentGroupSize": 4,
                                    },
                                    "SRIOV": {"SRIOVVEPACapable": True},
                                },
                                "NPIV": {"MaxDeviceLogins": 4, "MaxPortLogins": 2},
                                "NPAR": {"NparCapable": True, "NparEnabled": False},
                            },
                            "PCIeInterface": {
                                "PCIeType": "Gen2",
                                "MaxPCIeType": "Gen3",
                                "LanesInUse": 1,
                                "MaxLanes": 4,
                            },
                            "Identifiers": [{"DurableNameFormat": "NAA", "DurableName": "345C59DBD970859C"}],
                            "Location": {
                                "PartLocation": {
                                    "ServiceLabel": "Slot 1",
                                    "LocationType": "Slot",
                                    "LocationOrdinalValue": 0,
                                    "Reference": "Rear",
                                    "Orientation": "LeftToRight",
                                }
                            },
                        }
                    ],
                    "@odata.id": "/redfish/v1/Chassis/Chassis-1/NetworkAdapters/NIC-3001",
                },
                "PCIeDevice": {
                    "SerialNumber": "serial003",
                },
                "PCIeFunction": {
                    "DeviceId": "device002",
                    "VendorId": "vendor001",
                },
                "NetworkDeviceFunctions": {
                    "DeviceEnabled": True,
                    "Ethernet": {
                        "MACAddress": "00:0C:29:9A:98:ED",
                        "MTUSize": 1500,
                        "MTUSizeMaximum": 2500,
                        "PermanentMACAddress": "00:0C:29:9A:98:ED",
                        "VLAN": {"VLANEnable": True, "VLANId": 101},
                    },
                    "Limits": [
                        {
                            "BurstBytesPerSecond": 1,
                            "BurstPacketsPerSecond": 2,
                            "Direction": "Ingress",
                            "SustainedBytesPerSecond": 3,
                            "SustainedPacketsPerSecond": 4,
                        }
                    ],
                },
                "Port": {
                    "FunctionMaxBandwidth": [{"AllocationPercent": 80}],
                    "FunctionMinBandwidth": [{"AllocationPercent": 80}],
                    "MaxSpeedGbps": 48,
                    "LinkConfiguration": [{"CapableLinkSpeedGbps": [1, 2.2, 3]}],
                },
            },
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "time": "2023-07-06T05:55:55Z",
        },
    ]
}

# OOB_DATA FA and PCIe device Link present
OOB_DATA_FA_PCIE_DEVICE_2 = {
    "devices": [
        {
            "type": "networkInterface",
            "deviceID": "3001",
            "schema": {
                "SerialInterfaces": {"BitRate": "115200"},
                "Network": {
                    "@odata.type": "#NetworkAdapter.v1_9_0.NetworkAdapter",
                    "Id": "9fa725a1",
                    "Name": "Network Adapter View",
                    "Manufacturer": "Contoso",
                    "Model": "599TPS-T",
                    "SKU": "Contoso TPS-Net 2-Port Base-T",
                    "SerialNumber": "003BFLRT00023234",
                    "PartNumber": "975421-B20",
                    "Ports": [],
                    "NetworkDeviceFunctions": [],
                    "PowerState": "On",
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "PowerCapability": False,
                    "Controllers": [
                        {
                            "FirmwarePackageVersion": "7.4.10",
                            "ControllerCapabilities": {
                                "NetworkPortCount": 2,
                                "NetworkDeviceFunctionCount": 8,
                                "DataCenterBridging": {"Capable": True},
                                "VirtualizationOffload": {
                                    "VirtualFunction": {
                                        "DeviceMaxCount": 256,
                                        "NetworkPortMaxCount": 128,
                                        "MinAssignmentGroupSize": 4,
                                    },
                                    "SRIOV": {"SRIOVVEPACapable": True},
                                },
                                "NPIV": {"MaxDeviceLogins": 4, "MaxPortLogins": 2},
                                "NPAR": {"NparCapable": True, "NparEnabled": False},
                            },
                            "PCIeInterface": {
                                "PCIeType": "Gen2",
                                "MaxPCIeType": "Gen3",
                                "LanesInUse": 1,
                                "MaxLanes": 4,
                            },
                            "Identifiers": [{"DurableNameFormat": "NAA", "DurableName": "345C59DBD970859C"}],
                            "Location": {
                                "PartLocation": {
                                    "ServiceLabel": "Slot 1",
                                    "LocationType": "Slot",
                                    "LocationOrdinalValue": 0,
                                    "Reference": "Rear",
                                    "Orientation": "LeftToRight",
                                }
                            },
                        }
                    ],
                    "@odata.id": "/redfish/v1/Chassis/Chassis-1/NetworkAdapters/NIC-3001",
                },
                "PCIeDevice": {
                    "SerialNumber": "serial003",
                },
                "PCIeFunction": {
                    "DeviceId": "device002",
                    "VendorId": "vendor001",
                },
                "NetworkDeviceFunctions": {
                    "DeviceEnabled": True,
                    "Ethernet": {
                        "MACAddress": "00:0C:29:9A:98:ED",
                        "MTUSize": 1500,
                        "MTUSizeMaximum": 2500,
                        "PermanentMACAddress": "00:0C:29:9A:98:ED",
                        "VLAN": {"VLANEnable": True, "VLANId": 101},
                    },
                    "Limits": [
                        {
                            "BurstBytesPerSecond": 1,
                            "BurstPacketsPerSecond": 2,
                            "Direction": "Ingress",
                            "SustainedBytesPerSecond": 3,
                            "SustainedPacketsPerSecond": 4,
                        }
                    ],
                },
                "Port": {
                    "FunctionMaxBandwidth": [{"AllocationPercent": 80}],
                    "FunctionMinBandwidth": [{"AllocationPercent": 80}],
                    "MaxSpeedGbps": 48,
                    "LinkConfiguration": [{"CapableLinkSpeedGbps": [1, 2.2, 3]}],
                },
            },
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "time": "2023-07-06T05:55:55Z",
        },
        {
            "type": "sourceFabricAdapter",
            "deviceID": "3101",
            "schema": {
                "attribute": {
                    "deviceSpecificInformation": {
                        "type": "eeCard",
                        "id": "12345",
                        "status": "sfa",
                        "groupId": 16,
                        "linkStatus0": "up",
                        "linkStatus1": "down",
                        "switchName": "AD102GL",
                    },
                },
                "SerialInterfaces": {"BitRate": "115200"},
                "Network": {
                    "@odata.type": "#NetworkAdapter.v1_9_0.NetworkAdapter",
                    "Id": "9fa725a1",
                    "Name": "ExpEther SV",
                    "Manufacturer": "Contoso",
                    "Model": "599TPS-T",
                    "SKU": "Contoso TPS-Net 2-Port Base-T",
                    "SerialNumber": "003BFLRT00023234",
                    "PartNumber": "975421-B20",
                    "Ports": [],
                    "NetworkDeviceFunctions": [],
                    "PowerState": "On",
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "PowerCapability": False,
                    "Controllers": [
                        {
                            "FirmwarePackageVersion": "7.4.10",
                            "ControllerCapabilities": {
                                "NetworkPortCount": 2,
                                "NetworkDeviceFunctionCount": 8,
                                "DataCenterBridging": {"Capable": True},
                                "VirtualizationOffload": {
                                    "VirtualFunction": {
                                        "DeviceMaxCount": 256,
                                        "NetworkPortMaxCount": 128,
                                        "MinAssignmentGroupSize": 4,
                                    },
                                    "SRIOV": {"SRIOVVEPACapable": True},
                                },
                                "NPIV": {"MaxDeviceLogins": 4, "MaxPortLogins": 2},
                                "NPAR": {"NparCapable": True, "NparEnabled": False},
                            },
                            "PCIeInterface": {
                                "PCIeType": "Gen2",
                                "MaxPCIeType": "Gen3",
                                "LanesInUse": 1,
                                "MaxLanes": 4,
                            },
                            "Identifiers": [{"DurableNameFormat": "NAA", "DurableName": "345C59DBD970859C"}],
                            "Location": {
                                "PartLocation": {
                                    "ServiceLabel": "Slot 1",
                                    "LocationType": "Slot",
                                    "LocationOrdinalValue": 0,
                                    "Reference": "Rear",
                                    "Orientation": "LeftToRight",
                                }
                            },
                        }
                    ],
                    "@odata.id": "/redfish/v1/Chassis/Chassis-1/NetworkAdapters/NIC-3001",
                },
                "PCIeDevice": {
                    "SerialNumber": "serial003",
                },
                "PCIeFunction": {
                    "DeviceId": "device002",
                    "VendorId": "vendor001",
                },
                "NetworkDeviceFunctions": {
                    "DeviceEnabled": True,
                    "Ethernet": {
                        "MACAddress": "00:0C:29:9A:98:FF",
                        "MTUSize": 1500,
                        "MTUSizeMaximum": 2500,
                        "PermanentMACAddress": "00:0C:29:9A:98:FF",
                        "VLAN": {"VLANEnable": True, "VLANId": 100},
                    },
                    "Limits": [
                        {
                            "BurstBytesPerSecond": 1,
                            "BurstPacketsPerSecond": 2,
                            "Direction": "Ingress",
                            "SustainedBytesPerSecond": 3,
                            "SustainedPacketsPerSecond": 4,
                        }
                    ],
                },
                "Port": {
                    "FunctionMaxBandwidth": [{"AllocationPercent": 80}],
                    "FunctionMinBandwidth": [{"AllocationPercent": 80}],
                    "MaxSpeedGbps": 48,
                    "LinkConfiguration": [{"CapableLinkSpeedGbps": [1, 2.2, 3]}],
                },
            },
            "time": "2023-07-06T05:55:55Z",
        },
    ]
}

# FM_DATA FA and PCIe device Link present
FM_DATA_FA_PCIE_DEVICE_1 = {
    "data": [
        {
            "deviceID": "3101",
            "type": "sourceFabricAdapter",
            "PCIeVendorId": "vendor001",
            "PCIeDeviceId": "device002",
            "PCIeDeviceSerialNumber": "serial003",
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "devicePortList": [
                {
                    "fabricId": "NEC-01",
                    "LTSSMState": "L0",
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "USP",
                }
            ],
        },
        {
            "deviceID": "3001",
            "type": "networkInterface",
            "PCIeVendorId": "",
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": "serial005",
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "devicePortList": [
                {
                    "fabricId": "NEC-02",
                    "LTSSMState": "L2",
                    "switchId": "fmsw-02",
                    "switchPortNumber": "2",
                    "switchPortType": "USP",
                },
            ],
        },
    ]
}

# FM_DATA FA and PCIe device Link present
FM_DATA_FA_PCIE_DEVICE_2 = {
    "data": [
        {
            "deviceID": "3001",
            "type": "networkInterface",
            "PCIeVendorId": "",
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": "serial005",
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "devicePortList": [
                {
                    "fabricId": "NEC-02",
                    "LTSSMState": "L2",
                    "switchId": "fmsw-02",
                    "switchPortNumber": "2",
                    "switchPortType": "USP",
                },
            ],
        },
        {
            "deviceID": "3101",
            "type": "sourceFabricAdapter",
            "PCIeVendorId": "vendor001",
            "PCIeDeviceId": "device002",
            "PCIeDeviceSerialNumber": "serial003",
            "link": [{"type": "CPU", "deviceID": "0001"}],
            "devicePortList": [
                {
                    "fabricId": "NEC-01",
                    "LTSSMState": "L0",
                    "switchId": "fmsw-01",
                    "switchPortNumber": "1",
                    "switchPortType": "USP",
                }
            ],
        },
    ]
}

# RESP FA and PCIe device Link present
RESP_FA_PCIE_DEVICE_1 = {
    "deviceID": "3101",
    "type": "sourceFabricAdapter",
    "attribute": {
        "deviceSpecificInformation": {
            "type": "eeCard",
            "id": "12345",
            "status": "sfa",
            "groupId": 16,
            "linkStatus0": "up",
            "linkStatus1": "down",
            "notificationStatus0": ["up", "down"],
            "notificationStatus1": ["down", "down"],
            "switchName": "AD102GL",
        }
    },
    "bitRate": "115200",
    "controllers": [
        {
            "capability": {
                "dataCenterBridging": {"capable": True},
                "networkDeviceFunctionCount": 8,
                "networkPortCount": 2,
                "npar": {"capable": True, "enabled": False},
                "npiv": {"maxDeviceLogins": 4, "maxPortLogins": 2},
                "virtualizationOffload": {
                    "virtualFunction": {"deviceMaxCount": 256, "networkPortMaxCount": 128, "minAssignmentGroupSize": 4},
                    "sriov": {"VEPACapable": True},
                },
            },
            "firmwarePackageVersion": "7.4.10",
            "identifiers": [{"durableNameFormat": "NAA", "durableName": "345C59DBD970859C"}],
            "location": {
                "partLocation": {
                    "serviceLabel": "Slot 1",
                    "type": "Slot",
                    "ordinalValue": 0,
                    "reference": "Rear",
                    "orientation": "LeftToRight",
                }
            },
            "PCIeInterface": {"lanesInUse": 1, "maxLanes": 4, "PCIeType": "Gen2", "maxPCIeType": "Gen3"},
        }
    ],
    "constraints": {
        "nonRemovableDevices": [
            {
                "deviceID": "0001",
            },
        ],
    },
    "deviceEnabled": True,
    "ethernet": {
        "MACAddress": "00:0C:29:9A:98:FF",
        "MTUSize": 1500,
        "MTUSizeMaximum": 2500,
        "permanentMACAddress": "00:0C:29:9A:98:FF",
        "vlan": {"enable": True, "id": 100},
    },
    "limits": [
        {
            "burstBytesPerSecond": 1,
            "burstPacketsPerSecond": 2,
            "direction": "Ingress",
            "sustainedBytesPerSecond": 3,
            "sustainedPacketsPerSecond": 4,
        }
    ],
    "functionMaxBandwidths": [{"allocationPercent": 80}],
    "functionMinBandwidths": [{"allocationPercent": 80}],
    "maxSpeedGbps": 48,
    "linkConfigurations": [{"capableLinkSpeedsGbps": [1, 2.2, 3]}],
    "links": [{"type": "CPU", "deviceID": "0001"}],
    "networkAdapterSerialNumber": "003BFLRT00023234",
    "networkAdapterManufacturer": "Contoso",
    "networkAdapterModel": "599TPS-T",
    "fabricAdapterSerialNumber": "003BFLRT00023234",
    "fabricAdapterManufacturer": "Contoso",
    "fabricAdapterModel": "599TPS-T",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": False,
    "PCIeVendorID": "vendor001",
    "PCIeDeviceID": "device002",
    "PCIeDeviceSerialNumber": "serial003",
    "model": "599TPS-T",
    "devicePortList": [
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
    ],
}


# RESP FA and PCIe device Link present
RESP_FA_PCIE_DEVICE_2 = {
    "deviceID": "3101",
    "type": "sourceFabricAdapter",
    "attribute": {
        "deviceSpecificInformation": {
            "type": "eeCard",
            "id": "12345",
            "status": "sfa",
            "groupId": 16,
            "linkStatus0": "up",
            "linkStatus1": "down",
            "switchName": "AD102GL",
        }
    },
    "bitRate": "115200",
    "controllers": [
        {
            "capability": {
                "dataCenterBridging": {"capable": True},
                "networkDeviceFunctionCount": 8,
                "networkPortCount": 2,
                "npar": {"capable": True, "enabled": False},
                "npiv": {"maxDeviceLogins": 4, "maxPortLogins": 2},
                "virtualizationOffload": {
                    "virtualFunction": {"deviceMaxCount": 256, "networkPortMaxCount": 128, "minAssignmentGroupSize": 4},
                    "sriov": {"VEPACapable": True},
                },
            },
            "firmwarePackageVersion": "7.4.10",
            "identifiers": [{"durableNameFormat": "NAA", "durableName": "345C59DBD970859C"}],
            "location": {
                "partLocation": {
                    "serviceLabel": "Slot 1",
                    "type": "Slot",
                    "ordinalValue": 0,
                    "reference": "Rear",
                    "orientation": "LeftToRight",
                }
            },
            "PCIeInterface": {"lanesInUse": 1, "maxLanes": 4, "PCIeType": "Gen2", "maxPCIeType": "Gen3"},
        }
    ],
    "deviceEnabled": True,
    "ethernet": {
        "MACAddress": "00:0C:29:9A:98:FF",
        "MTUSize": 1500,
        "MTUSizeMaximum": 2500,
        "permanentMACAddress": "00:0C:29:9A:98:FF",
        "vlan": {"enable": True, "id": 100},
    },
    "limits": [
        {
            "burstBytesPerSecond": 1,
            "burstPacketsPerSecond": 2,
            "direction": "Ingress",
            "sustainedBytesPerSecond": 3,
            "sustainedPacketsPerSecond": 4,
        }
    ],
    "functionMaxBandwidths": [{"allocationPercent": 80}],
    "functionMinBandwidths": [{"allocationPercent": 80}],
    "maxSpeedGbps": 48,
    "linkConfigurations": [{"capableLinkSpeedsGbps": [1, 2.2, 3]}],
    "links": [{"type": "CPU", "deviceID": "0001"}],
    "networkAdapterSerialNumber": "003BFLRT00023234",
    "networkAdapterManufacturer": "Contoso",
    "networkAdapterModel": "599TPS-T",
    "fabricAdapterSerialNumber": "003BFLRT00023234",
    "fabricAdapterManufacturer": "Contoso",
    "fabricAdapterModel": "599TPS-T",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": False,
    "PCIeVendorID": "vendor001",
    "PCIeDeviceID": "device002",
    "PCIeDeviceSerialNumber": "serial003",
    "model": "599TPS-T",
    "devicePortList": [
        {
            "fabricID": "NEC-02",
            "LTSSMState": "L2",
            "switchID": "fmsw-02",
            "switchPortNumber": "2",
            "switchPortType": "USP",
        },
        {
            "fabricID": "NEC-01",
            "LTSSMState": "L0",
            "switchID": "fmsw-01",
            "switchPortNumber": "1",
            "switchPortType": "USP",
        },
    ],
}

# Mapping table file
MAPPING_TABLE_FILE1 = {
    "fm": {"spec": "test_info_core_fm_spec_mapping.json"},
    "oob": {"spec": "test_info_core_oob_spec_mapping.json", "metric": "test_info_core_oob_metric_mapping.json"},
    "agent": {"metric": "test_info_core_agent_metric_mapping.json"},
}

MAPPING_TABLE_FILE2 = {"agent": {"metric": "test_info_core_test_mapping.json"}}


def _log_contains(record, level, message) -> bool:
    """Comparing log contents"""
    return next(filter(lambda x: (x[1] == level) and (message in x[2]), record), None) is not None


def _link_sort(source):
    """Sort link"""
    link = source.get("links", None)
    if link is not None and len(link) > 1:
        link = sorted(link, key=lambda x: x["deviceID"])
        source["links"] = link
    return source


def _constraints_nonremovable_sort(source):
    """Sort nonRemovableDevices"""
    constraints = source.get("constraints", None)
    if constraints is not None and len(constraints) > 0:
        non_removable = constraints.get("nonRemovableDevices", None)
        if non_removable is not None and len(non_removable) > 1:
            non_removable = sorted(non_removable, key=lambda x: x["deviceID"])
            source["constraints"]["nonRemovableDevices"] = non_removable
    return source


def _get_spec_info(mocker, device_id, device_type, oob_data, fm_data, cut_timestamp, fm_valid: bool | None = True):
    """Get Information"""

    def mock_device_id_to_device_type(_):
        return device_type

    def mock_oob(_, __):
        return oob_data

    def mock_fm(_, __):
        return fm_data

    def mock_device_id_to_fm_valid(_):
        return fm_valid

    # Current path
    current_path = os.path.dirname(os.path.abspath(__file__))

    # Replace the path of the mapping table file (constant) with the path of the test mapping table file.
    mapping_path = current_path
    mocker.patch.object(settings, "mapping_table_path", mapping_path)

    # Replace the mapping table file (constant) with the test mapping table file.
    mocker.patch.dict("app.core.info.info_const.MAPPING_TABLE_FILE", MAPPING_TABLE_FILE1)
    # Loading the mapping table file used in the information retrieval process (response generation)
    load_mapping_table()

    # Replace device information retrieval for Device ID management.
    mocker.patch("app.common.dim.device_id_base.device_id_to_device_type", side_effect=mock_device_id_to_device_type)

    # Replace OOB device information retrieval with mock
    mocker.patch("app.core.info.spec_oob.GetSpecOOBInfo.get_spec_oob", side_effect=mock_oob)
    # Replace fetching FM device information with a mock.
    mocker.patch("app.core.info.spec_fm.GetSpecFMInfo.get_spec_fm", side_effect=mock_fm)

    # Replace the retrieval of the FM information enable flag for Device ID management.
    if fm_valid is not None:
        mocker.patch("app.common.dim.device_id_base.device_id_to_fm_valid", side_effect=mock_device_id_to_fm_valid)

    get_information = InformationCore()

    spec_info, errors = get_information.get_spec_info(device_id)
    # Return excluding the current date and time.
    if cut_timestamp:
        return {key: val for key, val in spec_info.items() if key != RESP_ITEM_NAME_TIME_STAMP}, errors
    else:
        return spec_info, errors


def test_get_spec_info_cpu_link(mocker):
    """Test Get Information CPU"""
    spec_data, _ = _get_spec_info(mocker, "0001", "CPU", OOB_DATA_CPU_LINK, FM_DATA_CPU_LINK, True)
    # Link present
    assert RESP_CPU_LINK == _link_sort(spec_data)


def test_get_spec_info_cpu_link_oob_only(mocker):
    """Test Get Information CPU"""
    spec_data, _ = _get_spec_info(mocker, "0001", "CPU", OOB_DATA_CPU_LINK, FM_DATA_CPU_NO_LINK, True)
    # Link present
    assert RESP_CPU_LINK_OOB_ONLY == _link_sort(spec_data)


def test_get_spec_info_cpu_link_fm_only(mocker):
    """Test Get Information CPU"""
    spec_data, _ = _get_spec_info(mocker, "0001", "CPU", OOB_DATA_CPU_NO_LINK, FM_DATA_CPU_LINK, True)
    # Link present
    assert RESP_CPU_LINK_FM_ONLY == _link_sort(spec_data)


def test_get_spec_info_cpu_multi_links(mocker):
    """Test Get Information CPU multi links"""
    spec_data, _ = _get_spec_info(mocker, "0001", "CPU", OOB_DATA_CPU_LINK, FM_DATA_CPU_MULTI_LINK, True)
    # Link present
    assert RESP_CPU_MULTI_LINK == _link_sort(spec_data)


def test_get_spec_info_cpu_multi_links_error(mocker, caplog):
    """Test Get Information CPU multi links on error"""
    fm_data = copy.deepcopy(FM_DATA_CPU_MULTI_LINK)
    fm_data["data"][1]["deviceID"] = "0002"
    spec_data, errors = _get_spec_info(mocker, "0001", "CPU", OOB_DATA_CPU_LINK, fm_data, False)

    assert spec_data is None

    assert errors == [
        {
            "errorCode": "EF010BAS000",
            "errorMessage": "The server encountered an internal error. "
            "The target device cannot merged. Device ID 1: 0001,CPU, Device ID 2: 0002,CPU.",
        }
    ]

    assert _log_contains(
        caplog.record_tuples,
        logging.WARNING,
        "W00001: Unexpected Exception: The target device cannot merged. Device ID 1: 0001,CPU, Device ID 2: 0002,CPU.",
    )


def test_get_spec_info_cpu_no_link(mocker):
    """Test Get Information CPU"""
    spec_data, errors = _get_spec_info(mocker, "0001", "CPU", OOB_DATA_CPU_NO_LINK, FM_DATA_CPU_NO_LINK, True)
    # No Link
    assert (RESP_CPU_NO_LINK, []) == (spec_data, errors)


def test_get_spec_info_memory_link(mocker):
    """Test Get Information memory"""
    spec_data, _ = _get_spec_info(mocker, "1001", "memory", OOB_DATA_MEMORY_LINK, FM_DATA_MEMORY_LINK, True)
    # Link present
    assert RESP_MEMORY_LINK == _link_sort(spec_data)


def test_get_spec_info_memory_no_link(mocker):
    """Test Get Information memory"""
    spec_data, errors = _get_spec_info(mocker, "1001", "memory", OOB_DATA_MEMORY_NO_LINK, FM_DATA_MEMORY_NO_LINK, True)
    # No Link
    assert (RESP_MEMORY_NO_LINK, []) == (spec_data, errors)


def test_get_spec_info_storage_link(mocker):
    """Test Get Information storage"""
    spec_data, _ = _get_spec_info(mocker, "2001", "storage", OOB_DATA_STORAGE_LINK, FM_DATA_STORAGE_LINK, True)
    # Link present
    assert RESP_STORAGE_LINK == _link_sort(spec_data)


def test_get_spec_info_storage_no_link(mocker):
    """Test Get Information storage"""
    spec_data, errors = _get_spec_info(
        mocker, "2001", "storage", OOB_DATA_STORAGE_NO_LINK, FM_DATA_STORAGE_NO_LINK, True
    )
    # No Link
    assert (RESP_STORAGE_NO_LINK, []) == (spec_data, errors)


def test_get_spec_info_storage_int(mocker):
    """Test Get Information storage int value"""
    spec_data, _ = _get_spec_info(mocker, "2001", "storage", OOB_DATA_STORAGE_INT, None, True)
    # int value
    assert RESP_STORAGE_INT == spec_data


def test_get_spec_info_storage_float(mocker):
    """Test Get Information storage float value"""
    spec_data, _ = _get_spec_info(mocker, "2001", "storage", OOB_DATA_STORAGE_FLOAT, None, True)
    # float value
    assert RESP_STORAGE_FLOAT == spec_data


def test_get_spec_info_nic_link(mocker):
    """Test Get Information networkInterface"""
    spec_data, _ = _get_spec_info(mocker, "3001", "networkInterface", OOB_DATA_NIC_LINK, FM_DATA_NIC_LINK, True)
    # Link present
    assert RESP_NIC_LINK == _link_sort(spec_data)


def test_get_spec_info_nic_no_link(mocker):
    """Test Get Information networkInterface"""
    # No Link
    spec_data, errors = _get_spec_info(
        mocker, "3001", "networkInterface", OOB_DATA_NIC_NO_LINK, FM_DATA_NIC_NO_LINK, True
    )
    assert (RESP_NIC_NO_LINK, []) == (spec_data, errors)


def test_get_spec_info_nic_int(mocker):
    """Test Get Information networkInterface int value"""
    spec_data, _ = _get_spec_info(mocker, "3001", "networkInterface", OOB_DATA_NIC_INT, None, True)
    # int value
    assert RESP_NIC_INT == spec_data


def test_get_spec_info_nic_float(mocker):
    """Test Get Information networkInterface float value"""
    spec_data, _ = _get_spec_info(mocker, "3001", "networkInterface", OOB_DATA_NIC_FLOAT, None, True)
    # float value
    assert RESP_NIC_FLOAT == spec_data


def test_get_spec_info_fa_link(mocker):
    """Test Get Information sourceFabricAdapter"""
    spec_data, _ = _get_spec_info(mocker, "3101", "sourceFabricAdapter", OOB_DATA_FA_LINK, FM_DATA_FA_LINK, True)
    # Link present
    assert RESP_FA_LINK == _link_sort(spec_data)


def test_get_spec_info_fa_no_link(mocker):
    """Test Get Information sourceFabricAdapter"""
    # No Link
    spec_data, errors = _get_spec_info(
        mocker, "3101", "sourceFabricAdapter", OOB_DATA_FA_NO_LINK, FM_DATA_FA_NO_LINK, True
    )
    assert (RESP_FA_NO_LINK, []) == (spec_data, errors)


def test_get_spec_info_fa_int(mocker):
    """Test Get Information sourceFabricAdapter int value"""
    spec_data, _ = _get_spec_info(mocker, "3101", "sourceFabricAdapter", OOB_DATA_FA_INT, None, True)
    # int value
    assert RESP_FA_INT == spec_data


def test_get_spec_info_fa_float(mocker):
    """Test Get Information sourceFabricAdapter float value"""
    spec_data, _ = _get_spec_info(mocker, "3101", "sourceFabricAdapter", OOB_DATA_FA_FLOAT, None, True)
    # float value
    assert RESP_FA_FLOAT == spec_data


def test_get_spec_info_na_link(mocker):
    """Test Get Information destinationFabricAdapter"""
    spec_data, _ = _get_spec_info(mocker, "3201", "destinationFabricAdapter", OOB_DATA_NA_LINK, FM_DATA_NA_LINK, True)
    # Link present
    assert RESP_NA_LINK == _link_sort(spec_data)


def test_get_spec_info_na_no_link(mocker):
    """Test Get Information destinationFabricAdapter"""
    # No Link
    spec_data, errors = _get_spec_info(
        mocker, "3201", "destinationFabricAdapter", OOB_DATA_NA_NO_LINK, FM_DATA_NA_NO_LINK, True
    )
    assert (RESP_NA_NO_LINK, []) == (spec_data, errors)


def test_get_spec_info_na_int(mocker):
    """Test Get Information destinationFabricAdapter int value"""
    spec_data, _ = _get_spec_info(mocker, "3201", "destinationFabricAdapter", OOB_DATA_NA_INT, None, True)
    # int value
    assert RESP_NA_INT == spec_data


def test_get_spec_info_na_float(mocker):
    """Test Get Information destinationFabricAdapter float value"""
    spec_data, _ = _get_spec_info(mocker, "3201", "destinationFabricAdapter", OOB_DATA_NA_FLOAT, None, True)
    # float value
    assert RESP_NA_FLOAT == spec_data


def test_get_spec_info_other_device_type(mocker, caplog):
    """Test Get Information other Device Type"""
    spec_data, errors = _get_spec_info(mocker, "5001", None, {}, {}, False)

    assert spec_data is None

    assert errors == [
        {
            "errorCode": "EF010BAS000",
            "errorMessage": "The server encountered an internal error. "
            "Unable to retrieve the Device Type corresponding to Device ID: 5001.",
        }
    ]

    assert _log_contains(
        caplog.record_tuples,
        logging.WARNING,
        "W00006: Device information not found: Unable to retrieve the Device Type corresponding to Device ID: 5001.",
    )


def test_get_spec_info_gpu_link(mocker):
    """Test Get Information GPU"""
    spec_data, _ = _get_spec_info(mocker, "4001", "GPU", OOB_DATA_GPU_LINK, FM_DATA_GPU_LINK, True)
    # Link present
    assert RESP_GPU_LINK == _link_sort(spec_data)


def test_get_spec_info_gpu_link_oob_only(mocker):
    """Test Get Information GPU"""
    spec_data, _ = _get_spec_info(mocker, "4001", "GPU", OOB_DATA_GPU_LINK, FM_DATA_GPU_NO_LINK, True)
    # Link present
    assert RESP_GPU_LINK_OOB_ONLY == _link_sort(spec_data)


def test_get_spec_info_gpu_no_link(mocker):
    """Test Get Information GPU"""
    # No Link
    spec_data, errors = _get_spec_info(mocker, "4001", "GPU", OOB_DATA_GPU_NO_LINK, FM_DATA_GPU_NO_LINK, True)
    assert (RESP_GPU_NO_LINK, []) == (spec_data, errors)


def test_get_spec_info_gc(mocker):
    """Test Get Information graphicController"""
    spec_data, _ = _get_spec_info(mocker, "5001", "graphicController", OOB_DATA_GC, FM_DATA_GC, True)
    assert RESP_GC == _link_sort(spec_data)


def test_get_spec_info_get_spec_fm_base_exception(mocker):
    """spec exception"""

    def mock_device_id_to_device_type(_):
        return "CPU"

    # Replace device information retrieval in Device ID management.
    mocker.patch("app.common.dim.device_id_base.device_id_to_device_type", side_effect=mock_device_id_to_device_type)

    # By forcibly triggering an BaseHWControlError in get_spec_fm, a BaseHWControlError is raised.
    mocker.patch("app.core.info.spec_fm.GetSpecFMInfo.get_spec_fm", side_effect=BaseHWControlError)
    get_information = InformationCore()
    _, errors = get_information.get_spec_info("0001")

    err_msg = "The server encountered an internal error and was unable to complete your request."
    assert {"errorCode": "CF000BAS000", "errorMessage": err_msg} in errors


def test_get_spec_info_create_spec_info_device_type_none():
    """create_spec_info Device Type none"""
    get_information = InformationCore()
    resp = get_information._create_spec_info("0001", None, {}, {})
    assert {"deviceID": "0001", "type": None} == resp


def test_get_spec_info_create_spec_info_remove_empty_item_none(mocker):
    """create_spec_info remove_empty_item return none"""

    def get_mapping_table(_, __, ___):
        return {}

    # Replace get mapping table.
    mocker.patch("app.core.info.info_utils.get_mapping_table", side_effect=get_mapping_table)

    def create_resp_from_mapping(_, __):
        return {}

    # Replace create resp from mapping.
    mocker.patch("app.core.info.info_utils.create_resp_from_mapping", side_effect=create_resp_from_mapping)

    def remove_empty_item(_):
        return None

    # Replace remove empty items.
    mocker.patch("app.core.info.info_utils.remove_empty_item", side_effect=remove_empty_item)

    def _create_constraints(_, __, ___):
        return {RESP_ITEM_NAME_CONSTRAINTS: {}}

    # Replace create constraints.
    mocker.patch("app.core.info.info_core.InformationCore._create_constraints", side_effect=_create_constraints)

    get_information = InformationCore()
    resp = get_information._create_spec_info("0001", "CPU", FM_DATA_CPU_LINK, OOB_DATA_CPU_LINK)
    assert {"deviceID": "0001", "type": "CPU"} == resp


def test_get_spec_info_create_spec_info_create_resp_from_mapping_exception_oob(mocker, caplog):
    """create_spec_info create_resp_from_mapping exception oob"""

    oob_data = {"devices": [{"type": "CPU", "deviceID": "0001"}]}

    # Current path
    current_path = os.path.dirname(os.path.abspath(__file__))

    # Replace the path of the mapping table file (constant) with the path of the test mapping table file.
    mapping_path = current_path
    mocker.patch.object(settings, "mapping_table_path", mapping_path)

    # Replace the mapping table file (constant) with the test mapping table file.
    mocker.patch.dict("app.core.info.info_const.MAPPING_TABLE_FILE", MAPPING_TABLE_FILE1)
    # Loading the mapping table file used in the information retrieval process (response generation)
    load_mapping_table()

    mocker.patch("app.core.info.info_core.info_utils.create_resp_from_mapping", side_effect=InternalHWControlError)

    get_information = InformationCore()
    with pytest.raises(BaseHWControlError):
        # Specify the CPU as a representative.
        get_information._create_spec_info("0001", "CPU", None, oob_data)
    assert _log_contains(caplog.record_tuples, logging.WARNING, "Device ID:0001")


def test_get_spec_info_create_spec_info_create_resp_from_mapping_exception_fm(mocker, caplog):
    """create_spec_info create_resp_from_mapping exception oob"""

    fm_data = {"data": [{"deviceID": "0001", "type": "CPU"}]}

    # Current path
    current_path = os.path.dirname(os.path.abspath(__file__))

    # Replace the path of the mapping table file (constant) with the path of the test mapping table file.
    mapping_path = current_path
    mocker.patch.object(settings, "mapping_table_path", mapping_path)

    # Replace the mapping table file (constant) with the test mapping table file.
    mocker.patch.dict("app.core.info.info_const.MAPPING_TABLE_FILE", MAPPING_TABLE_FILE1)
    # Loading the mapping table file used in the information retrieval process (response generation)
    load_mapping_table()

    mocker.patch("app.core.info.info_core.info_utils.create_resp_from_mapping", side_effect=InternalHWControlError)

    get_information = InformationCore()
    with pytest.raises(BaseHWControlError):
        # Specify the CPU as a representative.
        get_information._create_spec_info("0001", "CPU", fm_data, None)
    assert _log_contains(caplog.record_tuples, logging.WARNING, "Device ID:0001")


def test_get_spec_info_create_spec_info_get_mapping_table_none(mocker):
    """create_spec_info get_mapping_table none"""

    oob_data = {"devices": [{"type": "CPU", "deviceID": "0001"}]}
    fm_data = {"data": [{"deviceID": "0001", "type": "CPU"}]}

    def mock_get_mapping_table(_, __, ___):
        return None

    def mock_create_constraints(_, __, ___):
        return {"constraints": None}

    mocker.patch("app.core.info.info_utils.get_mapping_table", side_effect=mock_get_mapping_table)
    mocker.patch("app.core.info.info_core.InformationCore._create_constraints", side_effect=mock_create_constraints)

    get_information = InformationCore()
    resp = get_information._create_spec_info("0001", "CPU", fm_data, oob_data)
    assert {"deviceID": "0001", "type": "CPU"} == resp


def test_get_spec_info_time_stamp(mocker):
    """Test infoTimestamp"""
    # Retrieve infoTimestamp (using 0001 (CPU) as a representative)
    spec_data, _ = _get_spec_info(mocker, "0001", "CPU", OOB_DATA_CPU_LINK, FM_DATA_CPU_LINK, False)
    info_time_stamp_str = spec_data.get(RESP_ITEM_NAME_TIME_STAMP)

    # Convert to datetime.
    info_time_stamp_datetime = datetime.datetime.strptime(str(info_time_stamp_str), TIME_STAMP_FORMAT)

    # Difference from the current date and time.
    now = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
    difftime = abs(now - info_time_stamp_datetime)

    # If the difference is within 1 minute, it is determined that the current date and time
    # have been correctly obtained.
    assert difftime <= datetime.timedelta(minutes=1)


def test_get_spec_info_cpu_constraints_nonremovable(mocker):
    """Test Get CPU device constraints"""
    resp_cpu_constraints_dict = dict(RESP_CPU_LINK)
    constraints = {
        "constraints": {"nonRemovableDevices": [{"deviceID": "1001"}, {"deviceID": "2001"}, {"deviceID": "3001"}]}
    }
    resp_cpu_constraints_dict.update(constraints)
    resp_cpu_constraints = json.dumps(resp_cpu_constraints_dict)

    resp, errors = _get_spec_info(mocker, "0001", "CPU", OOB_DATA_CPU_LINK, FM_DATA_CPU_LINK, True, False)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert json.loads(resp_cpu_constraints) == ret


def test_get_spec_info_built_in_cpu_constraints_nonremovable(mocker):
    """Test Get CPU device constraints"""
    resp_cpu_constraints_dict = dict(RESP_CPU_LINK_CPU)
    constraints = {"constraints": {"nonRemovableDevices": [{"deviceID": "0002"}]}}
    resp_cpu_constraints_dict.update(constraints)
    resp_cpu_constraints = json.dumps(resp_cpu_constraints_dict)

    mocker.patch("app.common.dim.device_id_base.device_id_to_fm_valid", side_effect=[False, True])

    resp, errors = _get_spec_info(mocker, "0001", "CPU", OOB_DATA_CPU_NO_LINK, FM_DATA_CPU_LINK_CPU, True, None)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert json.loads(resp_cpu_constraints) == ret


def test_get_spec_info_cpu_no_constraints_nonremovable(mocker):
    """Test Get CPU device no constraints"""
    resp, errors = _get_spec_info(mocker, "0001", "CPU", OOB_DATA_CPU_LINK, FM_DATA_CPU_LINK, True, True)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert RESP_CPU_LINK == ret


def test_get_spec_info_memory_constraints_nonremovable(mocker):
    """Test Get Information memory"""
    resp_memory_constraints_dict = dict(RESP_MEMORY_LINK)
    constraints = {"constraints": {"nonRemovableDevices": [{"deviceID": "0001"}]}}
    resp_memory_constraints_dict.update(constraints)
    resp_memory_constraints = json.dumps(resp_memory_constraints_dict)
    resp, errors = _get_spec_info(mocker, "1001", "memory", OOB_DATA_MEMORY_LINK, FM_DATA_MEMORY_LINK, True, False)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert json.loads(resp_memory_constraints) == ret


def test_get_spec_info_built_in_memory_constraints_nonremovable(mocker):
    """Test Get Information memory"""
    resp_memory_constraints_dict = dict(RESP_MEMORY_LINK)
    constraints = {"constraints": {"nonRemovableDevices": [{"deviceID": "0001"}]}}
    resp_memory_constraints_dict.update(constraints)
    resp_memory_constraints = json.dumps(resp_memory_constraints_dict)

    mocker.patch("app.common.dim.device_id_base.device_id_to_fm_valid", side_effect=[False, True])

    resp, errors = _get_spec_info(mocker, "1001", "memory", OOB_DATA_MEMORY_LINK, FM_DATA_MEMORY_LINK, True, None)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert json.loads(resp_memory_constraints) == ret


def test_get_spec_info_cxl_memory_constraints_nonremovable(mocker):
    """Test Get Information memory"""
    mocker.patch("app.common.dim.device_id_base.device_id_to_fm_valid", side_effect=[True, True])

    resp, errors = _get_spec_info(mocker, "1001", "memory", OOB_DATA_MEMORY_LINK, FM_DATA_MEMORY_LINK, True, None)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert RESP_MEMORY_LINK == ret


def test_get_spec_info_memory_no_constraints_nonremovable(mocker):
    """Test Get Information memory"""
    # No Link
    resp, errors = _get_spec_info(
        mocker, "1001", "memory", OOB_DATA_MEMORY_NO_LINK, FM_DATA_MEMORY_NO_LINK, True, False
    )
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert RESP_MEMORY_NO_LINK == ret


def test_get_spec_info_storage_constraints_nonremovable(mocker):
    """Test Get Information storage"""
    resp_constraints_dict = dict(RESP_STORAGE_LINK)
    constraints = {"constraints": {"nonRemovableDevices": [{"deviceID": "0001"}]}}
    resp_constraints_dict.update(constraints)
    resp_constraints = json.dumps(resp_constraints_dict)

    resp, errors = _get_spec_info(mocker, "2001", "storage", OOB_DATA_STORAGE_LINK, FM_DATA_STORAGE_LINK, True, False)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert json.loads(resp_constraints) == ret


def test_get_spec_info_built_in_storage_constraints_nonremovable(mocker):
    """Test Get Information storage"""
    resp_constraints_dict = dict(RESP_STORAGE_LINK)
    constraints = {"constraints": {"nonRemovableDevices": [{"deviceID": "0001"}]}}
    resp_constraints_dict.update(constraints)
    resp_constraints = json.dumps(resp_constraints_dict)

    mocker.patch("app.common.dim.device_id_base.device_id_to_fm_valid", side_effect=[False, True])

    resp, errors = _get_spec_info(mocker, "2001", "storage", OOB_DATA_STORAGE_LINK, FM_DATA_STORAGE_LINK, True, None)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert json.loads(resp_constraints) == ret


def test_get_spec_info_cxl_storage_constraints_nonremovable(mocker):
    """Test Get Information storage"""
    mocker.patch("app.common.dim.device_id_base.device_id_to_fm_valid", side_effect=[True, True])

    resp, errors = _get_spec_info(mocker, "2001", "storage", OOB_DATA_STORAGE_LINK, FM_DATA_STORAGE_LINK, True, None)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert RESP_STORAGE_LINK == ret


def test_get_spec_info_storage_no_constraints_nonremovable(mocker):
    """Test Get Information storage"""
    # No Link
    resp, errors = _get_spec_info(
        mocker, "2001", "storage", OOB_DATA_STORAGE_NO_LINK, FM_DATA_STORAGE_NO_LINK, True, False
    )
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert RESP_STORAGE_NO_LINK == ret


def test_get_spec_info_nic_constraints_nonremovable(mocker):
    """Test Get Information networkInterface"""
    resp_constraints_dict = dict(RESP_NIC_LINK)
    constraints = {"constraints": {"nonRemovableDevices": [{"deviceID": "0001"}]}}
    resp_constraints_dict.update(constraints)
    resp_constraints = json.dumps(resp_constraints_dict)

    resp, errors = _get_spec_info(mocker, "3001", "networkInterface", OOB_DATA_NIC_LINK, FM_DATA_NIC_LINK, True, False)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert json.loads(resp_constraints) == ret


def test_get_spec_info_built_in_nic_constraints_nonremovable(mocker):
    """Test Get Information networkInterface"""
    resp_constraints_dict = dict(RESP_NIC_LINK)
    constraints = {"constraints": {"nonRemovableDevices": [{"deviceID": "0001"}]}}
    resp_constraints_dict.update(constraints)
    resp_constraints = json.dumps(resp_constraints_dict)

    mocker.patch("app.common.dim.device_id_base.device_id_to_fm_valid", side_effect=[False, True])

    resp, errors = _get_spec_info(mocker, "3001", "networkInterface", OOB_DATA_NIC_LINK, FM_DATA_NIC_LINK, True, None)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert json.loads(resp_constraints) == ret


def test_get_spec_info_cxl_nic_constraints_nonremovable(mocker):
    """Test Get Information networkInterface"""
    mocker.patch("app.common.dim.device_id_base.device_id_to_fm_valid", side_effect=[True, True])

    resp, errors = _get_spec_info(mocker, "3001", "networkInterface", OOB_DATA_NIC_LINK, FM_DATA_NIC_LINK, True, None)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert RESP_NIC_LINK == ret


def test_get_spec_info_nic_no_constraints_nonremovable(mocker):
    """Test Get Information networkInterface"""
    # No Link
    resp, errors = _get_spec_info(
        mocker, "3001", "networkInterface", OOB_DATA_NIC_NO_LINK, FM_DATA_NIC_NO_LINK, True, False
    )
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert RESP_NIC_NO_LINK == ret


def test_get_spec_info_fa_constraints_nonremovable(mocker):
    """Test Get Information sourceFabricAdapter"""
    resp_constraints_dict = dict(RESP_FA_LINK)
    constraints = {"constraints": {"nonRemovableDevices": [{"deviceID": "0001"}]}}
    resp_constraints_dict.update(constraints)
    resp_constraints = json.dumps(resp_constraints_dict)

    resp, errors = _get_spec_info(mocker, "3101", "sourceFabricAdapter", OOB_DATA_FA_LINK, FM_DATA_FA_LINK, True, False)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert json.loads(resp_constraints) == ret


def test_get_spec_info_built_in_fa_constraints_nonremovable(mocker):
    """Test Get Information sourceFabricAdapter"""
    resp_constraints_dict = dict(RESP_FA_LINK)
    constraints = {"constraints": {"nonRemovableDevices": [{"deviceID": "0001"}]}}
    resp_constraints_dict.update(constraints)
    resp_constraints = json.dumps(resp_constraints_dict)

    mocker.patch("app.common.dim.device_id_base.device_id_to_fm_valid", side_effect=[False, True])

    resp, errors = _get_spec_info(mocker, "3101", "sourceFabricAdapter", OOB_DATA_FA_LINK, FM_DATA_FA_LINK, True, None)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert json.loads(resp_constraints) == ret


def test_get_spec_info_cxl_fa_constraints_nonremovable(mocker):
    """Test Get Information sourceFabricAdapter"""
    mocker.patch("app.common.dim.device_id_base.device_id_to_fm_valid", side_effect=[True, True])

    resp, errors = _get_spec_info(mocker, "3101", "sourceFabricAdapter", OOB_DATA_FA_LINK, FM_DATA_FA_LINK, True, None)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert RESP_FA_LINK == ret


def test_get_spec_info_fa_no_constraints_nonremovable(mocker):
    """Test Get Information sourceFabricAdapter"""
    # No Link
    resp, errors = _get_spec_info(
        mocker, "3101", "sourceFabricAdapter", OOB_DATA_FA_NO_LINK, FM_DATA_FA_NO_LINK, True, False
    )
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert RESP_FA_NO_LINK == ret


def test_get_spec_info_na_constraints_nonremovable(mocker):
    """Test Get Information destinationFabricAdapter"""
    resp_constraints_dict = dict(RESP_NA_LINK)
    constraints = {"constraints": {"nonRemovableDevices": [{"deviceID": "0001"}]}}
    resp_constraints_dict.update(constraints)
    resp_constraints = json.dumps(resp_constraints_dict)

    resp, errors = _get_spec_info(
        mocker, "3201", "destinationFabricAdapter", OOB_DATA_NA_LINK, FM_DATA_NA_LINK, True, False
    )
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert json.loads(resp_constraints) == ret


def test_get_spec_info_built_in_na_constraints_nonremovable(mocker):
    """Test Get Information destinationFabricAdapter"""
    resp_constraints_dict = dict(RESP_NA_LINK)
    constraints = {"constraints": {"nonRemovableDevices": [{"deviceID": "0001"}]}}
    resp_constraints_dict.update(constraints)
    resp_constraints = json.dumps(resp_constraints_dict)

    mocker.patch("app.common.dim.device_id_base.device_id_to_fm_valid", side_effect=[False, True])

    resp, errors = _get_spec_info(
        mocker, "3201", "destinationFabricAdapter", OOB_DATA_NA_LINK, FM_DATA_NA_LINK, True, None
    )
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert json.loads(resp_constraints) == ret


def test_get_spec_info_cxl_na_constraints_nonremovable(mocker):
    """Test Get Information destinationFabricAdapter"""
    mocker.patch("app.common.dim.device_id_base.device_id_to_fm_valid", side_effect=[True, True])

    resp, errors = _get_spec_info(
        mocker, "3201", "destinationFabricAdapter", OOB_DATA_NA_LINK, FM_DATA_NA_LINK, True, None
    )
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert RESP_NA_LINK == ret


def test_get_spec_info_na_no_constraints_nonremovable(mocker):
    """Test Get Information destinationFabricAdapter"""
    # No Link
    resp, errors = _get_spec_info(
        mocker, "3201", "destinationFabricAdapter", OOB_DATA_NA_NO_LINK, FM_DATA_NA_NO_LINK, True, False
    )
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert RESP_NA_NO_LINK == ret


def test_get_spec_info_gpu_constraints_nonremovable(mocker):
    """Test Get Information GPU"""
    resp_constraints_dict = dict(RESP_GPU_LINK)
    constraints = {
        "constraints": {"nonRemovableDevices": [{"deviceID": "2001"}, {"deviceID": "3001"}, {"deviceID": "5001"}]}
    }
    resp_constraints_dict.update(constraints)
    resp_constraints = json.dumps(resp_constraints_dict)
    resp, errors = _get_spec_info(mocker, "4001", "GPU", OOB_DATA_GPU_LINK, FM_DATA_GPU_LINK, True, False)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert json.loads(resp_constraints) == ret


def test_get_spec_info_gpu_constraints_nonremovable_oob_only(mocker):
    """Test Get Information GPU"""
    resp_constraints_dict = dict(RESP_GPU_LINK_OOB_ONLY)
    constraints = {"constraints": {"nonRemovableDevices": [{"deviceID": "5001"}]}}
    resp_constraints_dict.update(constraints)
    resp_constraints = json.dumps(resp_constraints_dict)
    resp, errors = _get_spec_info(mocker, "4001", "GPU", OOB_DATA_GPU_LINK, FM_DATA_GPU_NO_LINK, True, False)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert json.loads(resp_constraints) == ret


def test_get_spec_info_gpu_no_constraints_nonremovable(mocker):
    """Test Get Information GPU"""
    # No Link
    resp, errors = _get_spec_info(mocker, "4001", "GPU", OOB_DATA_GPU_NO_LINK, FM_DATA_GPU_NO_LINK, True, False)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert RESP_GPU_NO_LINK == ret


def test_get_spec_info_gc_constraints_nonremovable(mocker):
    """Test Get Information graphicController"""
    resp_constraints_dict = dict(RESP_GC)
    constraints = {"constraints": {"nonRemovableDevices": [{"deviceID": "4001"}]}}
    resp_constraints_dict.update(constraints)
    resp_constraints = json.dumps(resp_constraints_dict)
    resp, errors = _get_spec_info(mocker, "5001", "graphicController", OOB_DATA_GC, FM_DATA_GC, True, False)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert json.loads(resp_constraints) == ret


def test_get_spec_info_unknown_link(mocker):
    """Test Get Information unknown device type"""
    spec_data, _ = _get_spec_info(mocker, "7001", "unknown", OOB_DATA_UNKNOWN_LINK, FM_DATA_UNKNOWN_LINK, True)
    # Link present
    assert RESP_UNKNOWN_LINK == _link_sort(spec_data)


def test_get_spec_info_unknown_no_link(mocker):
    """Test Get Information unknown device type"""
    spec_data, errors = _get_spec_info(
        mocker,
        "7001",
        "unknown",
        OOB_DATA_UNKNOWN_NO_LINK,
        FM_DATA_UNKNOWN_NO_LINK,
        True,
    )
    # No Link
    assert (RESP_UNKNOWN_NO_LINK, []) == (spec_data, errors)


def test_get_spec_info_unknown_constraints_nonremovable(mocker):
    """Test Get Information unknown device type"""
    resp_constraints_dict = dict(RESP_UNKNOWN_LINK)
    constraints = {"constraints": {"nonRemovableDevices": [{"deviceID": "0001"}, {"deviceID": "4001"}]}}
    resp_constraints_dict.update(constraints)
    resp_constraints = json.dumps(resp_constraints_dict)

    resp, errors = _get_spec_info(mocker, "7001", "unknown", OOB_DATA_UNKNOWN_LINK, FM_DATA_UNKNOWN_LINK, True, False)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert json.loads(resp_constraints) == ret


def test_get_spec_info_built_in_unknown_constraints_nonremovable(mocker):
    """Test Get Information unknown device type"""
    resp_constraints_dict = dict(RESP_UNKNOWN_FMVALID_TRUE_LINK)
    constraints = {"constraints": {"nonRemovableDevices": [{"deviceID": "0001"}]}}
    resp_constraints_dict.update(constraints)
    resp_constraints = json.dumps(resp_constraints_dict)

    mocker.patch("app.common.dim.device_id_base.device_id_to_fm_valid", side_effect=[False, True])

    resp, errors = _get_spec_info(mocker, "7001", "unknown", OOB_DATA_UNKNOWN_LINK, FM_DATA_UNKNOWN_NO_LINK, True, None)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert json.loads(resp_constraints) == ret


def test_get_spec_info_cxl_unknown_constraints_nonremovable(mocker):
    """Test Get Information unknown device type"""
    mocker.patch("app.common.dim.device_id_base.device_id_to_fm_valid", side_effect=[True, True])

    resp, errors = _get_spec_info(mocker, "7001", "unknown", OOB_DATA_UNKNOWN_NO_LINK, FM_DATA_UNKNOWN_LINK, True, None)
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert RESP_UNKNOWN_FMVALID_FALSE_LINK == ret


def test_get_spec_info_unknown_no_constraints_nonremovable(mocker):
    """Test Get Information unknown device type"""
    # No Link
    resp, errors = _get_spec_info(
        mocker, "7001", "unknown", OOB_DATA_UNKNOWN_NO_LINK, FM_DATA_UNKNOWN_NO_LINK, True, False
    )
    ret = _constraints_nonremovable_sort(_link_sort(resp))

    assert len(errors) == 0
    assert RESP_UNKNOWN_NO_LINK == ret


def test_get_spec_info_create_constraints_exception_devicenotfound(mocker):
    """Test create_constraints_exception_devicenotfound"""
    # Current path
    current_path = os.path.dirname(os.path.abspath(__file__))

    # Replace the path of the mapping table file (constant) with the test mapping table file path.
    mapping_path = current_path
    mocker.patch.object(settings, "mapping_table_path", mapping_path)

    # Replace the mapping table file (constant) with the test mapping table file.
    mocker.patch.dict("app.core.info.info_const.MAPPING_TABLE_FILE", MAPPING_TABLE_FILE1)
    # Loading the mapping table file used in the information retrieval process (response generation)
    load_mapping_table()

    # Replace device information retrieval in Device ID management.
    mocker.patch("app.common.dim.device_id_base.device_id_to_device_type", return_value="CPU")

    # Replace obtaining OOB device information with a mock.
    mocker.patch("app.core.info.spec_oob.GetSpecOOBInfo.get_spec_oob", return_value=OOB_DATA_CPU_LINK)
    # Replace FM device information retrieval with a mock.
    mocker.patch("app.core.info.spec_fm.GetSpecFMInfo.get_spec_fm", return_value=FM_DATA_CPU_LINK)

    # Replace the acquisition of the FM information enable flag for Device ID management.
    mocker.patch("app.common.dim.device_id_base.device_id_to_fm_valid", side_effect=DeviceNotFoundHWControlError)
    get_information = InformationCore()

    _, errors = get_information.get_spec_info("0001")
    assert len(errors) > 0
    assert errors[0] == {"errorCode": "EF013BAS000", "errorMessage": "The specified target device is not found."}


def test_get_spec_info_fa_and_pcie_device_1(mocker):
    """Test Get Information sourceFabricAdapter and PCIe device value"""
    spec_data, _ = _get_spec_info(
        mocker, "3101", "sourceFabricAdapter", OOB_DATA_FA_PCIE_DEVICE_1, FM_DATA_FA_PCIE_DEVICE_1, True
    )

    assert RESP_FA_PCIE_DEVICE_1 == spec_data


def test_get_spec_info_fa_and_pcie_device_2(mocker):
    """Test Get Information sourceFabricAdapter and PCIe device value"""
    spec_data, _ = _get_spec_info(
        mocker, "3001", "networkInterface", OOB_DATA_FA_PCIE_DEVICE_2, FM_DATA_FA_PCIE_DEVICE_2, True
    )

    assert RESP_FA_PCIE_DEVICE_2 == spec_data

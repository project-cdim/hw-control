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

# pylint: disable=C0302

"""This is a test program."""

import logging
import datetime
import pytest
from fastapi.testclient import TestClient
from app.hw_control_main import app
from app.common.basic_exceptions import BaseHWControlError
from app.common.basic_exceptions import DeviceIDFileNotFoundHWControlError
from app.common.basic_exceptions import DeviceIDFileIncorrectHWControlError
from app.common.basic_exceptions import InternalHWControlError
from app.routers.info.devices import _get_individually_specified_device_info

from app.common.constants import TIME_STAMP_FORMAT

# Device list information, item name, current date and time
DEVICE_LIST_ITEM_NAME_TIME_STAMP = "infoTimestamp"

client = TestClient(app)

MOCK_LIST_RET = {
    "deviceList": [
        {"type": "CPU", "deviceID": "0001"},
        {"type": "CPU", "deviceID": "0002"},
        {"type": "memory", "deviceID": "1001"},
        {"type": "memory", "deviceID": "1002"},
        {"type": "memory", "deviceID": "1003"},
        {"type": "storage", "deviceID": "2001"},
        {"type": "storage", "deviceID": "2002"},
        {"type": "networkInterface", "deviceID": "3001"},
        {"type": "networkInterface", "deviceID": "3002"},
    ],
    "infoTimestamp": "2023-10-14T12:25:00-05:00",
}

MOCK_LIST_DEVICE_RET = {
    "deviceList": ["CPU", "memory", "storage", "networkInterface"],
    "infoTimestamp": "2023-10-14T13:25:00-05:00",
}

MOCK_LIST_NO_LIST_RET = {"deviceList": [], "infoTimestamp": "2023-10-14T13:25:00-05:00"}

MOCK_LIST_NOT_LIST_RET = {"deviceList": "CPU", "infoTimestamp": "2023-10-14T13:25:00-05:00"}

MOCK_LIST_NONE_RET = {"infoTimestamp": "2023-10-14T14:25:00-05:00"}

MOCK_LIST_CPU_RET = {
    "deviceList": [
        {"type": "CPU", "deviceID": "0001"},
        {"type": "CPU", "deviceID": "0002"},
        {"type": "CPU", "deviceID": ""},
    ],
    "infoTimestamp": "2023-10-14T13:25:00-05:00",
}

MOCK_LIST_MEM_RET = {
    "deviceList": [
        {"type": "memory", "deviceID": "1001"},
        {"type": "memory", "deviceID": "1002"},
        {"type": "memory", "deviceID": "1003"},
    ],
    "infoTimestamp": "2023-10-14T14:25:00-05:00",
}

MOCK_LIST_RESOURCE_RET = {
    "deviceList": [
        {"type": "CPU", "deviceID": "0001"},
        {"type": "memory", "deviceID": "1001"},
        {"type": "storage", "deviceID": "2001"},
        {"type": "networkInterface", "deviceID": "3001"},
        {"type": "nic", "deviceID": ""},
    ],
    "infoTimestamp": "2023-10-14T12:25:00-05:00",
}

MOCK_LIST_RESOURCE_MULTIPLE_RET = {
    "deviceList": [
        {"type": "CPU", "deviceID": "0001"},
        {"type": "memory", "deviceID": "1001"},
        {"type": "storage", "deviceID": "2001"},
        {"type": "networkInterface", "deviceID": "3001"},
        {"type": "nic", "deviceID": ""},
    ],
    "infoTimestamp": "2023-10-14T12:25:00-05:00",
}

mock_cpu_ret = {
    "deviceID": "0001",
    "type": "CPU",
    "baseSpeedMHz": 1200,
    "operatingSpeedMHz": 2400,
    "tdpWatts": 100,
    "totalCores": 8,
    "totalEnabledCores": 8,
    "totalThreads": 16,
    "processorMemory": [{"CapacityMiB": 123, "IntegratedMemory": True, "MemoryType": "DDR", "SpeedMHz": 1200}],
    "memorySummary": {"ECCModeEnabled": True, "totalCacheSizeMiB": 4096, "totalMemorySizeMiB": 8192},
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": True,
    "instructionSet": "x86-64",
    "processorArchitecture": "x86",
    "processorId": {
        "vendorId": "GenuineIntel",
        "identificationRegisters": "0x34AC34DC8901274A",
        "effectiveFamily": "0x42",
        "effectiveModel": "0x61",
        "step": "0x1",
        "microcodeInfo": "0x429943",
        "protectedIdentificationNumber": "123456",
    },
    "link": [
        {"type": "memory", "deviceID": "1001"},
        {"type": "storage", "deviceID": "2001"},
        {"type": "networkInterface", "deviceID": "3001"},
    ],
    "serialNumber": "PROCESSOR1",
    "socketNum": "CPU 1",
    "manufacturer": "Intel(R) Corporation",
    "model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
    "infoTimestamp": "2023-10-14T01:36:16Z",
}

mock_cpu_002_ret = {
    "deviceID": "0002",
    "type": "CPU",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": True,
    "infoTimestamp": "2023-10-14T01:36:16Z",
}

mock_memory_ret = {
    "deviceID": "1001",
    "type": "memory",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": True,
    "infoTimestamp": "2023-10-14T01:36:16Z",
}

mock_storage_ret = {
    "deviceID": "2001",
    "type": "storage",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": True,
    "infoTimestamp": "2023-10-14T01:36:16Z",
}

mock_networkInterface_ret = {  # pylint: disable=invalid-name
    "deviceID": "3001",
    "type": "networkInterface",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": True,
    "infoTimestamp": "2023-10-14T01:36:16Z",
}

mock_all_resource_list_ret = {
    "deviceList": [mock_cpu_ret, mock_memory_ret, mock_storage_ret, mock_networkInterface_ret],
    "infoTimestamp": "2023-10-14T19:00:00Z",
}

mock_all_resource_ret = {"deviceList": [mock_cpu_ret, mock_cpu_002_ret], "infoTimestamp": "2023-10-14T20:00:00Z"}

mock_cpu_err_info_ret = {
    "errorInfo": [
        {
            "errorCode": "xxxxx1",
            "errorMessage": "errorMessage1",
        },
        {
            "errorCode": "xxxxx2",
            "errorMessage": "errorMessage2",
        },
    ],
    "deviceID": "0001",
    "type": "CPU",
    "baseSpeedMHz": 1200,
    "operatingSpeedMHz": 2400,
    "tdpWatts": 100,
    "totalCores": 8,
    "totalEnabledCores": 8,
    "totalThreads": 16,
    "processorMemory": [{"CapacityMiB": 123, "IntegratedMemory": True, "MemoryType": "DDR", "SpeedMHz": 1200}],
    "memorySummary": {"ECCModeEnabled": True, "totalCacheSizeMiB": 4096, "totalMemorySizeMiB": 8192},
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": True,
    "instructionSet": "x86-64",
    "processorArchitecture": "x86",
    "processorId": {
        "vendorId": "GenuineIntel",
        "identificationRegisters": "0x34AC34DC8901274A",
        "effectiveFamily": "0x42",
        "effectiveModel": "0x61",
        "step": "0x1",
        "microcodeInfo": "0x429943",
        "protectedIdentificationNumber": "123456",
    },
    "link": [
        {"type": "memory", "deviceID": "1001"},
        {"type": "storage", "deviceID": "2001"},
        {"type": "networkInterface", "deviceID": "3001"},
    ],
    "serialNumber": "PROCESSOR1",
    "socketNum": "CPU 1",
    "manufacturer": "Intel(R) Corporation",
    "model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
    "infoTimestamp": "2023-10-14T01:36:16Z",
}

mock_cpu_err_info_multiple_ret = {
    "errorInfo": [
        {
            "errorCode": "xxxxx1",
            "errorMessage": "errorMessage1",
        },
        {
            "errorCode": "xxxxx2",
            "errorMessage": "errorMessage2",
        },
        {
            "errorCode": "xxxxx3",
            "errorMessage": "errorMessage3",
        },
    ],
    "deviceID": "0001",
    "type": "CPU",
    "baseSpeedMHz": 1200,
    "operatingSpeedMHz": 2400,
    "tdpWatts": 100,
    "totalCores": 8,
    "totalEnabledCores": 8,
    "totalThreads": 16,
    "processorMemory": [{"CapacityMiB": 123, "IntegratedMemory": True, "MemoryType": "DDR", "SpeedMHz": 1200}],
    "memorySummary": {"ECCModeEnabled": True, "totalCacheSizeMiB": 4096, "totalMemorySizeMiB": 8192},
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": True,
    "instructionSet": "x86-64",
    "processorArchitecture": "x86",
    "processorId": {
        "vendorId": "GenuineIntel",
        "identificationRegisters": "0x34AC34DC8901274A",
        "effectiveFamily": "0x42",
        "effectiveModel": "0x61",
        "step": "0x1",
        "microcodeInfo": "0x429943",
        "protectedIdentificationNumber": "123456",
    },
    "link": [
        {"type": "memory", "deviceID": "1001"},
        {"type": "storage", "deviceID": "2001"},
        {"type": "networkInterface", "deviceID": "3001"},
    ],
    "serialNumber": "PROCESSOR1",
    "socketNum": "CPU 1",
    "manufacturer": "Intel(R) Corporation",
    "model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
    "infoTimestamp": "2023-10-14T01:36:16Z",
}

mock_cpu_002_err_info_ret = {
    "errorInfo": [
        {
            "errorCode": "xxxxx1",
            "errorMessage": "errorMessage1",
        },
        {
            "errorCode": "xxxxx2",
            "errorMessage": "errorMessage2",
        },
    ],
    "deviceID": "0002",
    "type": "CPU",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": True,
    "infoTimestamp": "2023-10-14T01:36:16Z",
}

mock_cpu2_err_info_ret = {
    "errorInfo": [
        {
            "errorCode": "xxxxx1",
            "errorMessage": "errorMessage1",
        },
        {
            "errorCode": "xxxxx2",
            "errorMessage": "errorMessage2",
        },
    ],
    "deviceID": "0001",
}

mock_incomplete_list_ret = {
    "incompleteDeviceList": [mock_cpu_err_info_ret, mock_cpu_002_err_info_ret],
    "infoTimestamp": "2023-10-14T19:00:00Z",
}

mock_incomplete_list_mismatch_ret = {
    "incompleteDeviceList": [mock_cpu2_err_info_ret, mock_cpu_002_err_info_ret],
    "infoTimestamp": "2023-10-14T19:00:00Z",
}

mock_no_device_err_info_ret = {
    "errorInfo": [
        {
            "errorCode": "xxxxx1",
            "errorMessage": "errorMessage1",
        },
        {
            "errorCode": "xxxxx2",
            "errorMessage": "errorMessage2",
        },
    ],
    "deviceID": "0001",
}

mock_no_device_2_err_info_ret = {
    "errorInfo": [
        {
            "errorCode": "xxxxx1",
            "errorMessage": "errorMessage1",
        },
        {
            "errorCode": "xxxxx3",
            "errorMessage": "errorMessage3",
        },
    ],
    "deviceID": "0002",
}

mock_no_device_mix_err_info_ret = {
    "errorInfo": [
        {
            "errorCode": "xxxxx1",
            "errorMessage": "errorMessage1",
        },
        {
            "errorCode": "xxxxx2",
            "errorMessage": "errorMessage2",
        },
        {
            "errorCode": "xxxxx3",
            "errorMessage": "errorMessage3",
        },
    ],
    "deviceID": "0001",
}

mock_incomplete_list_no_data_ret = {
    "incompleteDeviceList": [mock_no_device_err_info_ret, mock_no_device_2_err_info_ret],
    "infoTimestamp": "2023-10-14T19:00:00Z",
}

mock_metric_ret = {
    "deviceID": "0001",
    "type": "CPU",
    "usageRate": 20,
    "user": 20,
    "system": 10,
    "wait": 0,
    "idle": 50,
    "infoTimestamp": "2023-10-14T20:00:00Z",
}

mock_metric_err_info_ret = {
    "errorInfo": [
        {
            "errorCode": "xxxxx1",
            "errorMessage": "errorMessage1",
        },
        {
            "errorCode": "xxxxx2",
            "errorMessage": "errorMessage2",
        },
    ],
    "deviceID": "0001",
    "type": "CPU",
    "usageRate": 20,
    "user": 20,
    "system": 10,
    "wait": 0,
    "idle": 50,
    "infoTimestamp": "2023-10-14T20:00:00Z",
}

mock_resource_ret = {
    "deviceID": "0001",
    "type": "CPU",
    "baseSpeedMHz": 1200,
    "operatingSpeedMHz": 2400,
    "tdpWatts": 100,
    "totalCores": 8,
    "totalEnabledCores": 8,
    "totalThreads": 16,
    "processorMemory": [{"CapacityMiB": 123, "IntegratedMemory": True, "MemoryType": "DDR", "SpeedMHz": 1200}],
    "memorySummary": {"ECCModeEnabled": True, "totalCacheSizeMiB": 4096, "totalMemorySizeMiB": 8192},
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": True,
    "instructionSet": "x86-64",
    "processorArchitecture": "x86",
    "processorId": {
        "vendorId": "GenuineIntel",
        "identificationRegisters": "0x34AC34DC8901274A",
        "effectiveFamily": "0x42",
        "effectiveModel": "0x61",
        "step": "0x1",
        "microcodeInfo": "0x429943",
        "protectedIdentificationNumber": "123456",
    },
    "link": [
        {"type": "memory", "deviceID": "1001"},
        {"type": "storage", "deviceID": "2001"},
        {"type": "networkInterface", "deviceID": "3001"},
    ],
    "serialNumber": "PROCESSOR1",
    "socketNum": "CPU 1",
    "manufacturer": "Intel(R) Corporation",
    "model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
    "usageRate": 20,
    "user": 20,
    "system": 10,
    "wait": 0,
    "idle": 50,
    "infoTimestamp": "2023-10-14T20:00:00Z",
}

mock_resource_err_info_ret = {
    "errorInfo": [
        {
            "errorCode": "xxxxx1",
            "errorMessage": "errorMessage1",
        },
        {
            "errorCode": "xxxxx2",
            "errorMessage": "errorMessage2",
        },
    ],
    "deviceID": "0001",
    "type": "CPU",
    "baseSpeedMHz": 1200,
    "operatingSpeedMHz": 2400,
    "tdpWatts": 100,
    "totalCores": 8,
    "totalEnabledCores": 8,
    "totalThreads": 16,
    "processorMemory": [{"CapacityMiB": 123, "IntegratedMemory": True, "MemoryType": "DDR", "SpeedMHz": 1200}],
    "memorySummary": {"ECCModeEnabled": True, "totalCacheSizeMiB": 4096, "totalMemorySizeMiB": 8192},
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": True,
    "instructionSet": "x86-64",
    "processorArchitecture": "x86",
    "processorId": {
        "vendorId": "GenuineIntel",
        "identificationRegisters": "0x34AC34DC8901274A",
        "effectiveFamily": "0x42",
        "effectiveModel": "0x61",
        "step": "0x1",
        "microcodeInfo": "0x429943",
        "protectedIdentificationNumber": "123456",
    },
    "link": [
        {"type": "memory", "deviceID": "1001"},
        {"type": "storage", "deviceID": "2001"},
        {"type": "networkInterface", "deviceID": "3001"},
    ],
    "serialNumber": "PROCESSOR1",
    "socketNum": "CPU 1",
    "manufacturer": "Intel(R) Corporation",
    "model": "Multi-Core Intel(R) Xeon(R) processor 7500 Series",
    "usageRate": 20,
    "user": 20,
    "system": 10,
    "wait": 0,
    "idle": 50,
    "infoTimestamp": "2023-10-14T20:00:00Z",
}

mock_cpu2_ret = {
    "type": "CPU",
    "status": {"state": "Enabled", "health": "OK"},
    "powerState": "On",
    "powerCapability": True,
    "infoTimestamp": "2023-10-14T01:36:16Z",
}

mock_metric2_ret = {
    "type": "CPU",
    "usageRate": 20,
    "user": 20,
    "system": 10,
    "wait": 0,
    "idle": 50,
    "infoTimestamp": "2023-10-14T20:00:00Z",
}

mock_cpu_invalid_ret = {"deviceID": "0001", "infoTimestamp": "2023-10-14T01:36:16Z"}

mock_metric_invalid_ret = {"type": "CPU", "infoTimestamp": "2023-10-14T20:00:00Z"}

mock_cpu_invalid2_ret = {
    "deviceID": "0001",
    "type": "CPU",
}

mock_metric_invalid2_ret = {
    "deviceID": "0001",
    "type": "CPU",
}

mock_device_invalid_ret = {"deviceID": "0010", "type": "CPU", "infoTimestamp": "2023-10-14T01:36:16Z"}

mock_errors_ret = [
    {
        "errorCode": "xxxxx1",
        "errorMessage": "errorMessage1",
    },
    {
        "errorCode": "xxxxx2",
        "errorMessage": "errorMessage2",
    },
]

mock_errors_multiple_ret = [
    {
        "errorCode": "xxxxx1",
        "errorMessage": "errorMessage1",
    },
    {
        "errorCode": "xxxxx3",
        "errorMessage": "errorMessage3",
    },
]

mock_all_resource_list_multiple_ret = {
    "incompleteDeviceList": [mock_cpu_err_info_ret],
    "deviceList": [mock_memory_ret, mock_storage_ret, mock_networkInterface_ret],
    "infoTimestamp": "2023-10-14T19:00:00Z",
}


def _log_contains(record, level, message) -> bool:
    return next(filter(lambda x: (x[1] == level) and (message in x[2]), record), None) is not None


def _freeze_datetime(mocker):
    datetime_mock = mocker.MagicMock(wraps=datetime.datetime)
    datetime_mock.now.return_value = datetime.datetime.now(datetime.UTC)
    mocker.patch.object(datetime, "datetime", datetime_mock)


def test_device_ids_all(mocker, caplog):
    """Get Device ID list information(all)"""
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_RET)

    # Compare and evaluate the results of the Web API execution with the results of the mock JSON data.

    response = client.get("/cdim/api/v1/device-ids")
    assert response.status_code == 200
    assert response.json() == MOCK_LIST_RET

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/device-ids")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Success")


def test_device_ids(mocker, caplog):
    """Get Device ID list information(memory)"""
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_MEM_RET)

    # Compare and evaluate the results of the Web API execution with the results of the mock JSON data.

    response = client.get("/cdim/api/v1/device-ids?deviceType=memory")
    assert response.status_code == 200
    assert response.json() == MOCK_LIST_MEM_RET

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/device-ids?deviceType=memory"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Success")


def test_devices_all(mocker, caplog):
    """Get all resource information at once(all)"""
    caplog.set_level(logging.INFO)

    def _mock_device_id_to_deviceinfo(device_id):
        if device_id == "0001":
            return mock_cpu_ret, ""
        if device_id == "1001":
            return mock_memory_ret, ""
        if device_id == "2001":
            return mock_storage_ret, ""
        if device_id == "3001":
            return mock_networkInterface_ret, ""
        return None, ""

    _freeze_datetime(mocker)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_RESOURCE_RET)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", side_effect=_mock_device_id_to_deviceinfo)
    # Compare and evaluate the results of the Web API execution with the results of the mock JSON data.

    response = client.get("/cdim/api/v1/devices")

    # Update current date and time
    mock_all_resource_list_ret["infoTimestamp"] = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

    assert response.status_code == 200
    assert response.json() == mock_all_resource_list_ret

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Success")


def test_devices(mocker, caplog):
    """Get all resource information at once(CPU)"""
    caplog.set_level(logging.INFO)

    def _mock_device_id_to_deviceinfo(device_id):
        if device_id == "0001":
            return mock_cpu_ret, ""
        if device_id == "0002":
            return mock_cpu_002_ret, ""
        return None, ""

    _freeze_datetime(mocker)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_CPU_RET)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", side_effect=_mock_device_id_to_deviceinfo)

    # Compare and evaluate the results of the Web API execution with the results of the mock JSON data.

    response = client.get("/cdim/api/v1/devices?deviceType=CPU")

    # Update current date and time
    mock_all_resource_ret["infoTimestamp"] = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

    assert response.status_code == 200
    assert response.json() == mock_all_resource_ret

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices?deviceType=CPU"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Success")


def test_devices_invalid(mocker, caplog) -> None:
    """Get all resource information at once(CPU failure)
    No data obtained(status_code == 404)

    """
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_tuple_ret = mock_device_invalid_ret, mock_error_ret

    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_CPU_RET)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    # Compare and evaluate the results of the Web API execution with the results of the mock JSON data.

    response = client.get("/cdim/api/v1/devices?deviceType=CPU")

    # Update current date and time
    mock_all_resource_ret["infoTimestamp"] = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

    assert response.status_code == 404
    assert response.json() == {"code": "EF013BAS000", "message": "The specified target device is not found."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices?deviceType=CPU"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_devices_information(mocker, caplog) -> None:
    """Get device information(deviceID=0001)"""
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_tuple_ret = mock_cpu_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    # Compare and evaluate the results of the Web API execution with the results of the mock JSON data.

    response = client.get("/cdim/api/v1/devices/0001/specs")
    assert response.status_code == 200
    assert response.json() == mock_cpu_ret

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/0001/specs"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Success")


def test_metrics_information(mocker, caplog) -> None:
    """Get metric information(deviceID=0001)"""
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_tuple_ret = mock_metric_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    # Compare and evaluate the results of the Web API execution with the results of the mock JSON data.

    response = client.get("/cdim/api/v1/devices/0001/metrics")
    assert response.status_code == 200
    assert response.json() == mock_metric_ret

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/0001/metrics"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Success")


def test_resources_information(mocker, caplog) -> None:
    """Get resource information(deviceID=0001)"""
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_tuple_ret = mock_cpu_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    mock_tuple_ret = mock_metric_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    # Compare and evaluate the results of the Web API execution with the results of the mock JSON data.

    response = client.get("/cdim/api/v1/devices/0001")
    assert response.status_code == 200
    assert response.json() == mock_resource_ret

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/0001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Success")


def test_devices_invalid_information(mocker, caplog) -> None:
    """Get device information(deviceID=0001 failure)
    The return value is only the Device ID.
    """
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_tuple_ret = mock_cpu_invalid_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    # Compare and evaluate the results of the Web API execution with the results of the mock JSON data.

    response = client.get("/cdim/api/v1/devices/0001/specs")
    assert response.status_code == 200
    assert response.json() == mock_cpu_invalid_ret

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/0001/specs"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Success")


def test_metrics_invalid_information(mocker, caplog) -> None:
    """Get metric information(deviceID=0001 failure)
    There is no Device ID in the return value.(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_tuple_ret = mock_metric_invalid_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    # Compare and evaluate the results of the Web API execution with the results of the mock JSON data.

    response = client.get("/cdim/api/v1/devices/0001/metrics")
    assert response.status_code == 500
    assert response.json() == {"code": "EF010BAS000", "message": "The server encountered an internal error."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/0001/metrics"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_resources_invalid_information(mocker, caplog) -> None:
    """Get resource information(deviceID=0001 failure)
    The return value is only the Device ID.
    """
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_tuple_ret = mock_cpu_invalid2_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    mock_tuple_ret = mock_metric_invalid2_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    # Compare and evaluate the results of the Web API execution with the results of the mock JSON data.

    response = client.get("/cdim/api/v1/devices/0001")
    assert response.status_code == 200
    assert response.json() == {**mock_cpu_invalid2_ret, **mock_metric_invalid2_ret}

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/0001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Success")


def test_device_ids_err400(mocker, caplog):
    """Get Device ID list information
    No data obtained(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value="")

    response = client.get("/cdim/api/v1/device-ids?deviceType=nic")
    assert response.status_code == 500
    assert response.json() == {"code": "EF010BAS000", "message": "The server encountered an internal error."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/device-ids?deviceType=nic"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_device_ids_err400none(mocker, caplog):
    """Get Device ID list information
    No data obtained(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=None)

    response = client.get("/cdim/api/v1/device-ids?deviceType=nic")
    assert response.status_code == 500
    assert response.json() == {"code": "EF010BAS000", "message": "The server encountered an internal error."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/device-ids?deviceType=nic"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_device_ids_err404_no_list(mocker, caplog):
    """Get Device ID list information
    No data obtained(status_code == 404)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_NO_LIST_RET)

    response = client.get("/cdim/api/v1/device-ids?deviceType=CPU")
    assert response.status_code == 404
    assert response.json() == {"code": "EF013BAS000", "message": "The specified target device is not found."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/device-ids?deviceType=CPU"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_device_ids_err400_none_list(mocker, caplog):
    """Get Device ID list information
    No data obtained(status_code == 404)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_NONE_RET)

    response = client.get("/cdim/api/v1/device-ids?deviceType=CPU")
    assert response.status_code == 404
    assert response.json() == {"code": "EF013BAS000", "message": "The specified target device is not found."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/device-ids?deviceType=CPU"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_device_ids_err500(mocker, caplog):
    """Get Device ID list information
    Request Error(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", side_effect=BaseHWControlError)

    response = client.get("/cdim/api/v1/device-ids?deviceType=nic")
    assert response.status_code == 500
    err_msg = "The server encountered an internal error and was unable to complete your request."
    assert response.json() == {"code": "CF000BAS000", "message": err_msg}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/device-ids?deviceType=nic"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_device_ids_error(mocker):
    """Get Device ID list information

    Switched general exceptions to custom_exception_handler handling
      (The handling of unexpected exceptions implemented in each process has been deleted.)
    """
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", side_effect=Exception)


def test_device_ids_dim_err010(mocker, caplog):
    """Get Device ID list information
    Information acquisition failure(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=DeviceIDFileNotFoundHWControlError)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", side_effect=None)

    response = client.get("/cdim/api/v1/device-ids?deviceType=memory")
    assert response.status_code == 500
    assert response.json() == {"code": "EF007BAS010", "message": "The Device ID Management File is not found."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/device-ids?deviceType=memory"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_device_ids_dim_err011(mocker, caplog):
    """Get Device ID list information
    Information acquisition failure(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=DeviceIDFileIncorrectHWControlError)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", side_effect=None)

    response = client.get("/cdim/api/v1/device-ids?deviceType=memory")
    assert response.status_code == 500
    assert response.json() == {"code": "EF007BAS011", "message": "The Device ID Management File is incorrect."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/device-ids?deviceType=memory"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_device_ids_dim_error(mocker):
    """Get Device ID list information

    Switched general exceptions to custom_exception_handler handling
      (The handling of unexpected exceptions implemented in each process has been deleted.)
    """
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=Exception)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", side_effect=None)


def test_device_information_err200none(mocker, caplog):
    """Get device information
    No data obtained, error information available(status_code == 200)
    """
    caplog.set_level(logging.INFO)
    mock_ret = ""
    mock_tuple_ret = mock_ret, mock_errors_ret

    _freeze_datetime(mocker)
    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/5001/specs")
    mock_no_device_err_info_ret["deviceID"] = "5001"
    # Update current date and time
    mock_no_device_err_info_ret["infoTimestamp"] = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

    assert response.status_code == 200
    assert response.json() == mock_no_device_err_info_ret

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001/specs"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Partial failure")


def test_device_information_err200(mocker, caplog):
    """Get device information
    Acquired data mismatch, error information valid(status_code == 200)
    """
    caplog.set_level(logging.INFO)
    mock_tuple_ret = mock_metric_ret, mock_errors_ret

    _freeze_datetime(mocker)
    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/5001/specs")
    mock_no_device_err_info_ret["deviceID"] = "5001"
    # Update current date and time
    mock_no_device_err_info_ret["infoTimestamp"] = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

    assert response.status_code == 200
    assert response.json() == mock_no_device_err_info_ret

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001/specs"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Partial failure")


def test_device_information_err200data(mocker, caplog):
    """Get device information
    Acquired data is valid, error information is valid(status_code == 200)
    """
    caplog.set_level(logging.INFO)
    mock_tuple_ret = mock_cpu_ret, mock_errors_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/0001/specs")
    assert response.status_code == 200
    assert response.json() == mock_cpu_err_info_ret

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/0001/specs"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Partial failure")


def test_device_information_err400mismatch(mocker, caplog) -> None:
    """Get device information
    No data obtained, no error information(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_tuple_ret = mock_metric_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/5001/specs")
    assert response.status_code == 500
    assert response.json() == {"code": "EF010BAS000", "message": "The server encountered an internal error."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001/specs"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_device_information_err400(mocker, caplog) -> None:
    """Get device information
    No data obtained(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_ret = ""
    mock_tuple_ret = mock_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/5001/specs")
    assert response.status_code == 500
    assert response.json() == {"code": "EF010BAS000", "message": "The server encountered an internal error."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001/specs"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_device_information_err400none(mocker, caplog) -> None:
    """Get device information
    No data obtained(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_ret = None
    mock_tuple_ret = mock_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/5001/specs")
    assert response.status_code == 500
    assert response.json() == {"code": "EF010BAS000", "message": "The server encountered an internal error."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001/specs"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_device_information_err500(mocker, caplog):
    """Get device information
    Request Error(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", side_effect=BaseHWControlError)

    response = client.get("/cdim/api/v1/devices/6001/specs")
    assert response.status_code == 500
    err_msg = "The server encountered an internal error and was unable to complete your request."
    assert response.json() == {"code": "CF000BAS000", "message": err_msg}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/6001/specs"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_device_information_error(mocker):
    """Get device information

    Switched general exceptions to custom_exception_handler handling
      (The handling of unexpected exceptions implemented in each process has been deleted.)
    """
    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", side_effect=Exception)


def test_devices_information_err200none(mocker, caplog):
    """Get all resource information at once
    No data obtained, error information available(status_code == 200)
    """
    caplog.set_level(logging.INFO)

    def _mock_device_id_to_deviceinfo(device_id):
        mock_ret = ""
        if device_id == "0001":
            return mock_ret, mock_errors_ret
        if device_id == "0002":
            return mock_ret, mock_errors_multiple_ret
        return None, ""

    _freeze_datetime(mocker)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_CPU_RET)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", side_effect=_mock_device_id_to_deviceinfo)

    response = client.get("/cdim/api/v1/devices")

    # Update current date and time
    tmp_time_stamp = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)
    mock_no_device_err_info_ret["deviceID"] = "0001"
    mock_no_device_err_info_ret["infoTimestamp"] = tmp_time_stamp
    mock_no_device_2_err_info_ret["infoTimestamp"] = tmp_time_stamp
    mock_incomplete_list_no_data_ret["infoTimestamp"] = tmp_time_stamp

    assert response.status_code == 200
    assert response.json() == mock_incomplete_list_no_data_ret

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Partial failure")


def test_devices_information_err200data(mocker, caplog):
    """Get all resource information at once
    Data obtained, error information available(status_code == 200)
    """
    caplog.set_level(logging.INFO)

    def _mock_device_id_to_deviceinfo(device_id):
        if device_id == "0001":
            return mock_cpu_ret, mock_errors_ret
        if device_id == "0002":
            return mock_cpu_002_ret, mock_errors_ret
        return None, ""

    _freeze_datetime(mocker)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_CPU_RET)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", side_effect=_mock_device_id_to_deviceinfo)

    response = client.get("/cdim/api/v1/devices?deviceType=CPU")

    # Update current date and time
    mock_incomplete_list_ret["infoTimestamp"] = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

    assert response.status_code == 200
    assert response.json() == mock_incomplete_list_ret

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices?deviceType=CPU"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Partial failure")


def test_devices_information_err200mismatch(mocker, caplog):
    """Get all resource information at once
    No Device ID in the return value, error information available(status_code == 200)
    """
    caplog.set_level(logging.INFO)

    def _mock_device_id_to_deviceinfo(device_id):
        if device_id == "0001":
            return mock_cpu2_ret, mock_errors_ret
        if device_id == "0002":
            return mock_cpu_002_ret, mock_errors_ret
        return None, ""

    _freeze_datetime(mocker)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_CPU_RET)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", side_effect=_mock_device_id_to_deviceinfo)

    response = client.get("/cdim/api/v1/devices?deviceType=CPU")

    # Update current date and time
    mock_cpu2_err_info_ret["infoTimestamp"] = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)
    mock_incomplete_list_mismatch_ret["infoTimestamp"] = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

    assert response.status_code == 200
    assert response.json() == mock_incomplete_list_mismatch_ret

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices?deviceType=CPU"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Partial failure")


def test_devices_err400(mocker, caplog):
    """Get all resource information at once
    No data obtained(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value="")

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value="")

    response = client.get("/cdim/api/v1/devices?deviceType=CPU")
    assert response.status_code == 500
    assert response.json() == {"code": "EF010BAS000", "message": "The server encountered an internal error."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices?deviceType=CPU"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_devices_err400none(mocker, caplog):
    """Get all resource information at once
    No data obtained(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=None)

    response = client.get("/cdim/api/v1/devices?deviceType=CPU")
    assert response.status_code == 500
    assert response.json() == {"code": "EF010BAS000", "message": "The server encountered an internal error."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices?deviceType=CPU"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_devices_err404(mocker, caplog):
    """Get all resource information at once
    No data obtained(status_code == 404)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_CPU_RET)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value="")

    response = client.get("/cdim/api/v1/devices?deviceType=CPU")
    assert response.status_code == 404
    assert response.json() == {"code": "EF013BAS000", "message": "The specified target device is not found."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices?deviceType=CPU"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_devices_err404none(mocker, caplog):
    """Get all resource information at once
    No data obtained(status_code == 404)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_CPU_RET)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=None)

    response = client.get("/cdim/api/v1/devices?deviceType=CPU")
    assert response.status_code == 404
    assert response.json() == {"code": "EF013BAS000", "message": "The specified target device is not found."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices?deviceType=CPU"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_devices_err404_no_list(mocker, caplog):
    """Get all resource information at once
    No data obtained(status_code == 404)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_NO_LIST_RET)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=None)

    response = client.get("/cdim/api/v1/devices?deviceType=CPU")
    assert response.status_code == 404
    assert response.json() == {"code": "EF013BAS000", "message": "The specified target device is not found."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices?deviceType=CPU"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_devices_err404_not_list(mocker, caplog):
    """Get all resource information at once
    No data obtained(status_code == 404)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_NOT_LIST_RET)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=None)

    response = client.get("/cdim/api/v1/devices?deviceType=CPU")
    assert response.status_code == 404
    assert response.json() == {"code": "EF013BAS000", "message": "The specified target device is not found."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices?deviceType=CPU"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_devices_err400_none_list(mocker, caplog):
    """Get all resource information at once
    No data obtained(status_code == 404)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_NONE_RET)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=None)

    response = client.get("/cdim/api/v1/devices?deviceType=CPU")
    assert response.status_code == 404
    assert response.json() == {"code": "EF013BAS000", "message": "The specified target device is not found."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices?deviceType=CPU"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_devices_err400_ng_list(mocker, caplog):
    """Get all resource information at once
    No data obtained(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_DEVICE_RET)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=None)

    response = client.get("/cdim/api/v1/devices?deviceType=CPU")
    assert response.status_code == 500
    assert response.json() == {"code": "EF010BAS000", "message": "The server encountered an internal error."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices?deviceType=CPU"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_devices_error404(mocker, caplog):
    """Get all resource information at once
    Invalid request(status_code == 404)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_CPU_RET)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", side_effect=BaseHWControlError)

    response = client.get("/cdim/api/v1/devices?deviceType=CPU")
    assert response.status_code == 404
    assert response.json() == {"code": "EF013BAS000", "message": "The specified target device is not found."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices?deviceType=CPU"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_devices_error500(mocker):
    """Get all resource information at once

    Switched general exceptions to custom_exception_handler handling
      (The handling of unexpected exceptions implemented in each process has been deleted.)
    """
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", side_effect=Exception)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", side_effect=Exception)


def test_devices_error(mocker, caplog):
    """Get all resource information at once
    Invalid request(status_code == 404)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_CPU_RET)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", side_effect=Exception)

    response = client.get("/cdim/api/v1/devices?deviceType=CPU")
    assert response.status_code == 404
    assert response.json() == {"code": "EF013BAS000", "message": "The specified target device is not found."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices?deviceType=CPU"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_devices_dim_err010(mocker, caplog):
    """Get all resource information at once
    Information acquisition failure(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=DeviceIDFileNotFoundHWControlError)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", side_effect=Exception)

    response = client.get("/cdim/api/v1/devices?deviceType=memory")
    assert response.status_code == 500
    assert response.json() == {"code": "EF007BAS010", "message": "The Device ID Management File is not found."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices?deviceType=memory"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_devices_dim_err011(mocker, caplog):
    """Get all resource information at once
    Information acquisition failure(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=DeviceIDFileIncorrectHWControlError)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", side_effect=Exception)

    response = client.get("/cdim/api/v1/devices?deviceType=memory")
    assert response.status_code == 500
    assert response.json() == {"code": "EF007BAS011", "message": "The Device ID Management File is incorrect."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices?deviceType=memory"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_devices_dim_error(mocker):
    """Get all resource information at once

    Switched general exceptions to custom_exception_handler handling
      (The handling of unexpected exceptions implemented in each process has been deleted.)
    """
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=Exception)

    mocker.patch("app.core.info.info_core.InformationCore.get_device_list", side_effect=None)

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", side_effect=Exception)


def test_metric_information_err200none(mocker, caplog):
    """Get metric information
    No data obtained, error information available(status_code == 200)
    """
    caplog.set_level(logging.INFO)
    mock_ret = ""
    mock_tuple_ret = mock_ret, mock_errors_ret

    _freeze_datetime(mocker)
    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/5001/metrics")
    mock_no_device_err_info_ret["deviceID"] = "5001"
    # Update current date and time
    mock_no_device_err_info_ret["infoTimestamp"] = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

    assert response.status_code == 200
    assert response.json() == mock_no_device_err_info_ret

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001/metrics"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Partial failure")


def test_metric_information_err200(mocker, caplog):
    """Get metric information
    Acquired data mismatch, error information valid(status_code == 200)
    """
    caplog.set_level(logging.INFO)
    mock_tuple_ret = mock_metric_ret, mock_errors_ret

    _freeze_datetime(mocker)
    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/5001/metrics")
    mock_no_device_err_info_ret["deviceID"] = "5001"
    # Update current date and time
    mock_no_device_err_info_ret["infoTimestamp"] = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

    assert response.status_code == 200
    assert response.json() == mock_no_device_err_info_ret

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001/metrics"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Partial failure")


def test_metric_information_err200data(mocker, caplog):
    """Get metric information
    Acquired data is valid, error information is valid(status_code == 200)
    """
    caplog.set_level(logging.INFO)
    mock_tuple_ret = mock_metric_ret, mock_errors_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/0001/metrics")
    assert response.status_code == 200
    assert response.json() == mock_metric_err_info_ret

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/0001/metrics"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Partial failure")


def test_metric_information_err400(mocker, caplog) -> None:
    """Get metric information
    No data obtained(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_ret = ""
    mock_tuple_ret = mock_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/5001/metrics")
    assert response.status_code == 500
    assert response.json() == {"code": "EF010BAS000", "message": "The server encountered an internal error."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001/metrics"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_metric_information_err400none(mocker, caplog) -> None:
    """Get metric information
    No data obtained(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_ret = None
    mock_tuple_ret = mock_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/5001/metrics")
    assert response.status_code == 500
    assert response.json() == {"code": "EF010BAS000", "message": "The server encountered an internal error."}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001/metrics"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_metric_information_err500(mocker, caplog):
    """Get metric information
    Request Error(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", side_effect=BaseHWControlError)

    response = client.get("/cdim/api/v1/devices/6001/metrics")
    assert response.status_code == 500
    err_msg = "The server encountered an internal error and was unable to complete your request."
    assert response.json() == {"code": "CF000BAS000", "message": err_msg}

    assert _log_contains(
        caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/6001/metrics"
    )
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_metric_information_error(mocker):
    """Get metric information

    Switched general exceptions to custom_exception_handler handling
      (The handling of unexpected exceptions implemented in each process has been deleted.)
    """
    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", side_effect=Exception)


def test_resources_information_err200none_sp(mocker, caplog) -> None:
    """Get resource information
    get_spec_info:No data obtained, error information available
    get_metric_info:No data obtained, no error information
    """
    caplog.set_level(logging.INFO)
    mock_ret = ""
    mock_tuple_ret = mock_ret, mock_errors_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    mock_error_ret: list = []
    mock_tuple_ret = mock_ret, mock_error_ret

    _freeze_datetime(mocker)
    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/5001")
    mock_no_device_err_info_ret["deviceID"] = "5001"
    # Update current date and time
    mock_no_device_err_info_ret["infoTimestamp"] = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

    assert response.status_code == 200
    assert response.json() == mock_no_device_err_info_ret

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Partial failure")


def test_resources_information_err200_sp(mocker, caplog) -> None:
    """Get resource information
    There is no Device ID in the return value.
    get_spec_info: error information available
    """
    caplog.set_level(logging.INFO)
    mock_tuple_ret = mock_cpu2_ret, mock_errors_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    mock_error_ret: list = []
    mock_tuple_ret = mock_metric2_ret, mock_error_ret

    _freeze_datetime(mocker)
    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/5001")
    mock_no_device_err_info_ret["deviceID"] = "5001"
    # Update current date and time
    mock_no_device_err_info_ret["infoTimestamp"] = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

    assert response.status_code == 200
    assert response.json() == mock_no_device_err_info_ret

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Partial failure")


def test_resources_information_err200none_mt(mocker, caplog) -> None:
    """Get resource information
    get_spec_info:No data obtained, no error information
    get_metric_info:No data obtained, error information available
    """
    caplog.set_level(logging.INFO)
    mock_ret = ""
    mock_error_ret: list = []
    mock_tuple_ret = mock_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    mock_tuple_ret = mock_ret, mock_errors_ret

    _freeze_datetime(mocker)
    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/5001")
    mock_no_device_err_info_ret["deviceID"] = "5001"
    # Update current date and time
    mock_no_device_err_info_ret["infoTimestamp"] = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

    assert response.status_code == 200
    assert response.json() == mock_no_device_err_info_ret

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Partial failure")


def test_resources_information_err200_mt(mocker, caplog) -> None:
    """Get resource information
    There is no Device ID in the return value.
    get_metric_info: error information available
    """
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_tuple_ret = mock_cpu2_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    mock_tuple_ret = mock_metric2_ret, mock_errors_ret

    _freeze_datetime(mocker)
    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/5001")
    mock_no_device_err_info_ret["deviceID"] = "5001"
    # Update current date and time
    mock_no_device_err_info_ret["infoTimestamp"] = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

    assert response.status_code == 200
    assert response.json() == mock_no_device_err_info_ret

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Partial failure")


def test_resources_information_err200_mix(mocker, caplog):
    """Get resource information
    get_spec_info:No data obtained, error information available
    get_metric_info:No data obtained, error information available
    """
    caplog.set_level(logging.INFO)
    mock_tuple_ret = mock_cpu2_ret, mock_errors_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    mock_tuple_ret = mock_metric2_ret, mock_errors_multiple_ret

    _freeze_datetime(mocker)
    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/5001")
    mock_no_device_mix_err_info_ret["deviceID"] = "5001"
    # Update current date and time
    mock_no_device_mix_err_info_ret["infoTimestamp"] = datetime.datetime.now(datetime.UTC).strftime(TIME_STAMP_FORMAT)

    assert response.status_code == 200
    assert response.json() == mock_no_device_mix_err_info_ret

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Partial failure")


def test_resources_information_err200data(mocker, caplog) -> None:
    """Get resource information
    get_spec_info:Data obtained, error information available
    get_metric_info:No data obtained, no error information
    """
    caplog.set_level(logging.INFO)
    mock_tuple_ret = mock_cpu_ret, mock_errors_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    mock_error_ret: list = []
    mock_tuple_ret = mock_metric2_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/0001")
    assert response.status_code == 200
    assert response.json() == mock_cpu_err_info_ret

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/0001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Partial failure")


def test_resources_information_multiple_err200data(mocker, caplog):
    """Get resource information
    get_spec_info:Data obtained, error information available
    get_metric_info:No data obtained, error information available
    """
    caplog.set_level(logging.INFO)
    mock_tuple_ret = mock_cpu_ret, mock_errors_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    mock_tuple_ret = mock_metric2_ret, mock_errors_multiple_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/0001")
    assert response.status_code == 200
    assert response.json() == mock_cpu_err_info_multiple_ret

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/0001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Partial failure")


def test_resources_information_devices(mocker, caplog) -> None:
    """Get resource information
    get_spec_info:Data obtained, no error information
    get_metric_info:No data obtained, no error information
    """
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_tuple_ret = mock_cpu_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    mock_tuple_ret = mock_metric2_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    # Compare and evaluate the results of the Web API execution with the results of the mock JSON data.

    response = client.get("/cdim/api/v1/devices/0001")
    assert response.status_code == 200
    assert response.json() == mock_cpu_ret

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/0001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Success")


def test_resources_information_metric(mocker, caplog) -> None:
    """Get resource information
    get_spec_info:No data obtained, no error information
    get_metric_info:Data obtained, no error information
    """
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_tuple_ret = mock_cpu2_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    mock_tuple_ret = mock_metric_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/0001")
    assert response.status_code == 200
    assert response.json() == mock_metric_ret

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/0001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Success")


def test_resources_information_error400(mocker, caplog) -> None:
    """Get resource information
    No data obtained(status_code == 500)

    """
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_ret = ""
    mock_tuple_ret = mock_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    mock_tuple_ret = mock_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/5001")
    assert response.status_code == 500
    assert response.json() == {"code": "EF010BAS000", "message": "The server encountered an internal error."}

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_resources_information_error400none(mocker, caplog) -> None:
    """Get resource information
    No data obtained(status_code == 500)

    """
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_ret = None
    mock_tuple_ret = mock_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    mock_tuple_ret = mock_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)

    response = client.get("/cdim/api/v1/devices/5001")
    assert response.status_code == 500
    assert response.json() == {"code": "EF010BAS000", "message": "The server encountered an internal error."}

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_resources_information_err400nu(mocker, caplog) -> None:
    """Get resource information
    No data obtained(status_code == 500)

    """
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_ret = ""
    mock_tuple_ret1 = mock_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret1)

    mock_tuple_ret2 = mock_metric_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret2)

    response = client.get("/cdim/api/v1/devices/5001")
    assert response.status_code == 500
    assert response.json() == {"code": "EF010BAS000", "message": "The server encountered an internal error."}

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_resources_information_err400no(mocker, caplog) -> None:
    """Get resource information
    No data obtained(status_code == 500)

    """
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_ret = None
    mock_tuple_ret1 = mock_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret1)

    mock_tuple_ret2 = mock_metric_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret2)

    response = client.get("/cdim/api/v1/devices/5001")
    assert response.status_code == 500
    assert response.json() == {"code": "EF010BAS000", "message": "The server encountered an internal error."}

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_resources_information_err400none(mocker, caplog) -> None:
    """Get resource information
    No data obtained(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_tuple_ret1 = mock_cpu_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret1)

    mock_ret = None
    mock_tuple_ret2 = mock_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret2)

    response = client.get("/cdim/api/v1/devices/5001")
    assert response.status_code == 500
    assert response.json() == {"code": "EF010BAS000", "message": "The server encountered an internal error."}

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_resources_information_err400null(mocker, caplog) -> None:
    """Get resource information
    No data obtained(status_code == 500)
    """
    caplog.set_level(logging.INFO)
    mock_error_ret: list = []
    mock_tuple_ret1 = mock_cpu_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret1)

    mock_ret = ""
    mock_tuple_ret2 = mock_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret2)

    response = client.get("/cdim/api/v1/devices/5001")
    assert response.status_code == 500
    assert response.json() == {"code": "EF010BAS000", "message": "The server encountered an internal error."}

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices/5001")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Failure")


def test_resources_information_err500metric(mocker) -> None:
    """Get resource information

    Switched general exceptions to custom_exception_handler handling
      (The handling of unexpected exceptions implemented in each process has been deleted.)
    """
    mock_error_ret: list = []
    mock_tuple_ret = mock_cpu_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", return_value=mock_tuple_ret)

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", side_effect=Exception)


def test_resources_information_err500spec(mocker) -> None:
    """Get resource information

    Switched general exceptions to custom_exception_handler handling
      (The handling of unexpected exceptions implemented in each process has been deleted.)
    """
    mock_error_ret: list = []
    mock_tuple_ret = mock_metric_ret, mock_error_ret

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", side_effect=Exception)

    mocker.patch("app.core.info.info_core.InformationCore.get_metric_info", return_value=mock_tuple_ret)


def test_devices_all_multiple_types(mocker, caplog):
    """Get all resource information at once"""
    caplog.set_level(logging.INFO)

    def _mock_device_id_to_deviceinfo(device_id):
        if device_id == "0001":
            return mock_cpu_ret, mock_errors_ret
        if device_id == "1001":
            return mock_memory_ret, ""
        if device_id == "2001":
            return mock_storage_ret, ""
        if device_id == "3001":
            return mock_networkInterface_ret, ""
        return None, ""

    _freeze_datetime(mocker)
    mocker.patch("app.common.dim.device_id_base.assign_device_id", side_effect=None)

    mocker.patch(
        "app.core.info.info_core.InformationCore.get_device_list", return_value=MOCK_LIST_RESOURCE_MULTIPLE_RET
    )

    mocker.patch("app.core.info.info_core.InformationCore.get_spec_info", side_effect=_mock_device_id_to_deviceinfo)

    # Compare and evaluate the results of the Web API execution with the results of the mock JSON data.

    response = client.get("/cdim/api/v1/devices")

    # Update current date and time
    mock_all_resource_list_multiple_ret["infoTimestamp"] = datetime.datetime.now(datetime.UTC).strftime(
        TIME_STAMP_FORMAT
    )

    assert response.status_code == 200
    assert response.json() == mock_all_resource_list_multiple_ret

    assert _log_contains(caplog.record_tuples, logging.INFO, "I00001: devices API Start /cdim/api/v1/devices")
    assert _log_contains(caplog.record_tuples, logging.INFO, "I00002: devices API Respond Success")


def test_get_individually_specified_device_info(caplog):
    """Get individual device information
    info_type Error
    """
    caplog.set_level(logging.WARNING)
    with pytest.raises(InternalHWControlError):
        _get_individually_specified_device_info("0001", "xxx")

    assert _log_contains(
        caplog.record_tuples,
        logging.WARNING,
        "W00006: Device information not found: _get_individually_specified_device_info"
        + "( device_id: 0001, info_type: xxx)",
    )

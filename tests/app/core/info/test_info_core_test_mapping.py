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

import os
import logging
import pytest
from app.common.settings import settings
from app.common.basic_exceptions import (
    InternalHWControlError,
)
from app.core.info.info_utils import load_mapping_table
import app.core.info.info_utils as info_utils
import app.core.info.info_conv_funcs as info_conv_funcs

# Response Item Name Current DateTime
RESP_ITEM_NAME_TIME_STAMP = "infoTimestamp"

# RESP Normal memory
RESP_NORMAL_MEMORY = {
    "deviceID": "1001",
    "type": "memory",
    "capacityMiB": 1073741824,
    "persistentRegionNumberLimit": 456.7,
    "allowedSpeedsMHz": [30, 40],
    "enabled": True,
}

# Normal memory
DATA_NORMAL_MEMORY = {
    "deviceID": "1001",
    "type": "memory",
    "schema": {
        "CapacityMiB": 1073741824,
        "LogicalSizeMiB": None,
        "NonVolatileSizeMiB": "",
        "PersistentRegionNumberLimit": 456.7,
        "AllowedSpeedsMHz": [30, 40],
        "Enabled": True,
    },
}

# RESP Normal NIC
RESP_NORMAL_NIC = {
    "deviceID": "3001",
    "type": "networkInterface",
    "linkConfigurations": [{"capableLinkSpeedsGbps": [1, 2.2, 3]}],
}

# Normal NIC
DATA_NORMAL_NIC = {
    "type": "networkInterface",
    "deviceID": "3001",
    "schema": {
        "Port": {
            "LinkConfiguration": [{"CapableLinkSpeedGbps": [1, 2.2, 3, None]}],
        },
    },
}

# required
DATA_REQUIRED1 = {
    "deviceID": "1001",
    "type": "",
    "schema": {
        "CapacityMiB": 1073741824,
        "LogicalSizeMiB": 1.23,
        "NonVolatileSizeMiB": "abc",
        "PersistentRegionNumberLimit": 456.7,
        "AllowedSpeedsMHz": [30, 40],
        "Enabled": True,
    },
}

DATA_REQUIRED2 = {
    "deviceID": "1001",
    "type": None,
    "schema": {
        "CapacityMiB": 1073741824,
        "LogicalSizeMiB": 1.23,
        "NonVolatileSizeMiB": "abc",
        "PersistentRegionNumberLimit": 456.7,
        "AllowedSpeedsMHz": [30, 40],
        "Enabled": True,
    },
}

DATA_REQUIRED3 = {
    "deviceID": "1001",
    "schema": {
        "CapacityMiB": 1073741824,
        "LogicalSizeMiB": 1.23,
        "NonVolatileSizeMiB": "abc",
        "PersistentRegionNumberLimit": 456.7,
        "AllowedSpeedsMHz": [30, 40],
        "Enabled": True,
    },
}

# list item type error
DATA_LIST_ITEM_TYPE_ERROR = {
    "deviceID": "1001",
    "type": "memory",
    "schema": {
        "CapacityMiB": 1073741824,
        "LogicalSizeMiB": 1.23,
        "NonVolatileSizeMiB": "abc",
        "PersistentRegionNumberLimit": 456.7,
        "AllowedSpeedsMHz": ["a", 40],
        "Enabled": True,
    },
}

# type error int
DATA_TYPE_ERROR_INT = {
    "deviceID": "1001",
    "type": "memory",
    "schema": {
        "CapacityMiB": 123.456,
        "LogicalSizeMiB": 1.23,
        "NonVolatileSizeMiB": "abc",
        "PersistentRegionNumberLimit": 456.7,
        "AllowedSpeedsMHz": [30, 40],
        "Enabled": True,
    },
}

# type error float
DATA_TYPE_ERROR_FLOAT = {
    "deviceID": "1001",
    "type": "memory",
    "schema": {
        "CapacityMiB": 1073741824,
        "LogicalSizeMiB": "1.23",
        "NonVolatileSizeMiB": "abc",
        "PersistentRegionNumberLimit": 456.7,
        "AllowedSpeedsMHz": [30, 40],
        "Enabled": True,
    },
}

# type error str
DATA_TYPE_ERROR_STR = {
    "deviceID": "1001",
    "type": "memory",
    "schema": {
        "CapacityMiB": 1073741824,
        "LogicalSizeMiB": 1.23,
        "NonVolatileSizeMiB": 123,
        "PersistentRegionNumberLimit": 456.7,
        "AllowedSpeedsMHz": [30, 40],
        "Enabled": True,
    },
}

# type error bool
DATA_TYPE_ERROR_BOOL = {
    "deviceID": "1001",
    "type": "memory",
    "schema": {
        "CapacityMiB": 1073741824,
        "LogicalSizeMiB": 1.23,
        "NonVolatileSizeMiB": "abc",
        "PersistentRegionNumberLimit": 456.7,
        "AllowedSpeedsMHz": [30, 40],
        "Enabled": "True",
    },
}

# type error int float
DATA_TYPE_ERROR_INT_FLOAT = {
    "deviceID": "1001",
    "type": "memory",
    "schema": {
        "CapacityMiB": 1073741824,
        "LogicalSizeMiB": 1.23,
        "NonVolatileSizeMiB": "abc",
        "PersistentRegionNumberLimit": "456.7",
        "AllowedSpeedsMHz": [30, 40],
        "Enabled": True,
    },
}

# item_type error int float
DATA_ITEM_TYPE_ERROR_INT_FLOAT = {
    "type": "networkInterface",
    "deviceID": "3001",
    "schema": {
        "Port": {
            "LinkConfiguration": [{"CapableLinkSpeedGbps": [1, 2.2, "3"]}],
        },
    },
}

# RESP convert function
RESP_CONVERT_FUNC = {
    "deviceID": "1001",
    "type": "memory",
    "sensingInterval": 5,
    "noneConvert": "T123",
}

# Convert data
CONVERT_DATA = {
    "deviceID": "1001",
    "type": "memory",
    "schema": {
        "SensingInterval": "PT5S",
        "NoneConvert": "T123",
    },
}

# Convert invalid data SensingInterval
CONVERT_INVALID_DATA_SENSING_INTERVAL = {
    "deviceID": "1001",
    "type": "memory",
    "schema": {"SensingInterval": "PTaS"},
}

# Mapping table file
MAPPING_TABLE_FILE1 = {
    "fm": {"spec": "test_info_core_fm_spec_mapping.json"},
    "oob": {"spec": "test_info_core_oob_spec_mapping.json"},
    "agent": {"metric": "test_info_core_test_mapping.json"},
}

# Mapping Table File (Error Map)
MAPPING_TABLE_FILE_ERROR = {
    "fm": {"spec": "test_info_core_fm_spec_mapping.json"},
    "oob": {"spec": "test_info_core_oob_spec_mapping.json"},
    "agent": {"metric": "test_info_core_test_mapping_error.json"},
}


def _log_contains(record, level, message) -> bool:
    """Comparing log contents"""
    return next(filter(lambda x: (x[1] == level) and (message in x[2]), record), None) is not None


def _create_resp(
    mocker, _, device_type, data_type, data_source_type, input_data, map_table=MAPPING_TABLE_FILE1
):  # pylint: disable=W0102
    """Create response"""
    # Current path
    current_path = os.path.dirname(os.path.abspath(__file__))

    # Replace the path of the mapping table file (constant) with the test mapping table file path.
    mapping_path = current_path
    mocker.patch.object(settings, "MAPPING_TABLE_PATH", mapping_path)

    # Replace the mapping table file (constant) with the test mapping table file.
    mocker.patch.dict("app.core.info.info_const.MAPPING_TABLE_FILE", map_table)
    # Loading the mapping table file used in the information retrieval process (response generation)
    load_mapping_table()

    resp = {}
    # Retrieve mapping table
    mapping = info_utils.get_mapping_table(device_type, data_type, data_source_type)  # pylint: disable=W0212
    if mapping is not None:
        # Response generation
        resp_agent = info_utils.create_resp_from_mapping(mapping, input_data)  # pylint: disable=W0212
        # Remove items with no values from the response.
        resp = info_utils.remove_empty_item(resp_agent)

    # Return without the current date and time.
    return {key: val for key, val in resp.items() if key != RESP_ITEM_NAME_TIME_STAMP}


def test_mapping_normal_memory(mocker):
    """Test mapping normal"""
    # Return value confirmation
    assert RESP_NORMAL_MEMORY == _create_resp(mocker, "1001", "memory", "agent", "metric", DATA_NORMAL_MEMORY)


def test_mapping_normal_nic(mocker):
    """Test mapping normal"""
    # Return value confirmation
    assert RESP_NORMAL_NIC == _create_resp(mocker, "3001", "networkInterface", "oob", "spec", DATA_NORMAL_NIC)


def test_mapping_required1(mocker, caplog):
    """Test mapping required"""
    with pytest.raises(InternalHWControlError):
        # Required field is an empty string.
        _create_resp(mocker, "1001", "memory", "agent", "metric", DATA_REQUIRED1)
    assert _log_contains(caplog.record_tuples, logging.WARNING, "W00008: Required item does not exist: key:type")


def test_mapping_required2(mocker, caplog):
    """Test mapping required"""
    with pytest.raises(InternalHWControlError):
        # Required field is None.
        _create_resp(mocker, "1001", "memory", "agent", "metric", DATA_REQUIRED2)
    assert _log_contains(caplog.record_tuples, logging.WARNING, "W00008: Required item does not exist: key:type")


def test_mapping_required3(mocker, caplog):
    """Test mapping required"""
    with pytest.raises(InternalHWControlError):
        # There is no required field itself.
        _create_resp(mocker, "1001", "memory", "agent", "metric", DATA_REQUIRED3)
    assert _log_contains(caplog.record_tuples, logging.WARNING, "W00008: Required item does not exist: key:type")


def test_mapping_list_item_data_type_error(mocker, caplog):
    """Test mapping list item data_type error"""
    with pytest.raises(InternalHWControlError):
        _create_resp(mocker, "1001", "memory", "agent", "metric", DATA_LIST_ITEM_TYPE_ERROR)
    assert _log_contains(
        caplog.record_tuples,
        logging.WARNING,
        "W00009: Invalid type value: Key:AllowedSpeedsMHz, Value:a, Value type:str, Target type:int",
    )


def test_mapping_data_type_error_int(mocker, caplog):
    """Test mapping type error int"""
    with pytest.raises(InternalHWControlError):
        _create_resp(mocker, "1001", "memory", "agent", "metric", DATA_TYPE_ERROR_INT)
    assert _log_contains(
        caplog.record_tuples,
        logging.WARNING,
        "W00009: Invalid type value: Key:CapacityMiB, Value:123.456, Value type:float, Target type:int",
    )


def test_mapping_data_type_error_float(mocker, caplog):
    """Test mapping type error float"""
    with pytest.raises(InternalHWControlError):
        _create_resp(mocker, "1001", "memory", "agent", "metric", DATA_TYPE_ERROR_FLOAT)
    assert _log_contains(
        caplog.record_tuples,
        logging.WARNING,
        "W00009: Invalid type value: Key:LogicalSizeMiB, Value:1.23, Value type:str, Target type:float",
    )


def test_mapping_data_type_error_str(mocker, caplog):
    """Test mapping type error str"""
    with pytest.raises(InternalHWControlError):
        _create_resp(mocker, "1001", "memory", "agent", "metric", DATA_TYPE_ERROR_STR)
    assert _log_contains(
        caplog.record_tuples,
        logging.WARNING,
        "W00009: Invalid type value: Key:NonVolatileSizeMiB, Value:123, Value type:int, Target type:str",
    )


def test_mapping_data_type_error_bool(mocker, caplog):
    """Test mapping type error bool"""
    with pytest.raises(InternalHWControlError):
        _create_resp(mocker, "1001", "memory", "agent", "metric", DATA_TYPE_ERROR_BOOL)
    assert _log_contains(
        caplog.record_tuples,
        logging.WARNING,
        "W00009: Invalid type value: Key:Enabled, Value:True, Value type:str, Target type:bool",
    )


def test_mapping_data_type_error_int_float(mocker, caplog):
    """Test mapping type error int float"""
    with pytest.raises(InternalHWControlError):
        _create_resp(mocker, "1001", "memory", "agent", "metric", DATA_TYPE_ERROR_INT_FLOAT)
    assert _log_contains(
        caplog.record_tuples,
        logging.WARNING,
        (
            "W00009: Invalid type value: Key:PersistentRegionNumberLimit,"
            " Value:456.7, Value type:str, Target type:int,float"
        ),
    )


def test_mapping_data_item_type_error_int_float(mocker, caplog):
    """Test mapping type error int float"""
    with pytest.raises(InternalHWControlError):
        _create_resp(mocker, "3001", "networkInterface", "oob", "spec", DATA_ITEM_TYPE_ERROR_INT_FLOAT)
    assert _log_contains(
        caplog.record_tuples,
        logging.WARNING,
        "W00009: Invalid type value: Key:CapableLinkSpeedGbps, Value:3, Value type:str, Target type:int,float",
    )


def test_mapping_convert_function(mocker):
    """Test mapping convert function"""
    assert RESP_CONVERT_FUNC == _create_resp(mocker, "1001", "memory", "agent", "metric", CONVERT_DATA)


def test_mapping_convert_function_returned_none_sensing_interval(mocker, caplog):
    """Test mapping convert function returned none SensingInterval"""
    with pytest.raises(InternalHWControlError):
        _create_resp(mocker, "1001", "memory", "agent", "metric", CONVERT_INVALID_DATA_SENSING_INTERVAL)
    assert _log_contains(
        caplog.record_tuples,
        logging.WARNING,
        "W00009: Invalid type value: Key:SensingInterval, Value:PTaS, Value type:str, "
        "Convert function:duration_to_seconds returned None.",
    )


def test_mapping_duration_to_seconds_normal():
    """Test mapping _duration_to_seconds normal input"""
    assert 86400 == info_conv_funcs.duration_to_seconds({}, "", "P1D")  # pylint: disable=W0212
    assert 3600 == info_conv_funcs.duration_to_seconds({}, "", "PT1H")  # pylint: disable=W0212
    assert 60 == info_conv_funcs.duration_to_seconds({}, "", "PT1M")  # pylint: disable=W0212
    assert 1 == info_conv_funcs.duration_to_seconds({}, "", "PT1S")  # pylint: disable=W0212
    assert pytest.approx(1.5) == info_conv_funcs.duration_to_seconds({}, "", "PT1.5S")  # pylint: disable=W0212
    assert 3660 == info_conv_funcs.duration_to_seconds({}, "", "PT1H1M")  # pylint: disable=W0212
    assert 3610 == info_conv_funcs.duration_to_seconds({}, "", "PT1H10S")  # pylint: disable=W0212
    assert 70 == info_conv_funcs.duration_to_seconds({}, "", "PT1M10S")  # pylint: disable=W0212
    assert 3670 == info_conv_funcs.duration_to_seconds({}, "", "PT1H1M10S")  # pylint: disable=W0212
    assert 183845 == info_conv_funcs.duration_to_seconds({}, "", "P2DT3H4M5S")  # pylint: disable=W0212
    assert 0 == info_conv_funcs.duration_to_seconds({}, "", "P0DT0H0M0S")  # pylint: disable=W0212
    assert 0 == info_conv_funcs.duration_to_seconds({}, "", "P0D")  # pylint: disable=W0212
    assert 0 == info_conv_funcs.duration_to_seconds({}, "", "PT0H")  # pylint: disable=W0212
    assert 0 == info_conv_funcs.duration_to_seconds({}, "", "PT0M")  # pylint: disable=W0212
    assert 0 == info_conv_funcs.duration_to_seconds({}, "", "PT0S")  # pylint: disable=W0212
    assert 183845 == info_conv_funcs.duration_to_seconds({"a": 1}, "b", "P2DT3H4M5S")  # pylint: disable=W0212


def test_mapping_duration_to_seconds_invalid():
    """Test mapping _duration_to_seconds invalid input"""
    assert info_conv_funcs.duration_to_seconds({}, "", "") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", None) is None  # type: ignore[arg-type]
    assert info_conv_funcs.duration_to_seconds({}, "", "T1S") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "PaDT3H4M5S") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "P2DTaH4M5S") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "P2DT3HaM5S") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "P2DT3H4MaS") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "P2DT3H4M5Sa") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "P2DT3H4M5S ") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", " P1D") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "P1D ") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "P1") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", 123) is None  # type: ignore[arg-type]
    assert info_conv_funcs.duration_to_seconds({}, "", "P") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "PT") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "PD") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "PDT") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "P-1D") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "PT-1H") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "PT-1M") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "PT-1S") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "P1.5D") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "PT1.5H") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "PT1.5M") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "P1Y1M1DT3H4M5S") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "P1M1DT3H4M5S") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "P1Y1DT3H4M5S") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "p2DT3H4M5S ") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "P2dT3H4M5S ") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "P2Dt3H4M5S ") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "P2DT3h4M5S ") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "P2DT3H4m5S ") is None  # pylint: disable=W0212
    assert info_conv_funcs.duration_to_seconds({}, "", "P2DT3H4M5s ") is None  # pylint: disable=W0212

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

"""HW independent section - Get Information process (Response generation)

Upon receiving a request from the information acquisition API,
make an information acquisition request for the specified Device ID to FM and OOB.
Merge the device information returned from FM and OOB for each device
type and return it to the information acquisition API.

"""

DATA_SOURCE_TYPE_FM = "fm"
DATA_SOURCE_TYPE_OOB = "oob"
DATA_SOURCE_TYPE_AGENT = "agent"

# Data type
DATA_TYPE_SPEC = "spec"
DATA_TYPE_METRIC = "metric"

# Mapping table (for memory retention)
MAPPING_TABLE: dict = {}

# Mapping item
MAPPING_ITEM_KEY = "key"
MAPPING_ITEM_TYPE = "vtype"
MAPPING_ITEM_PATH = "path"
MAPPING_ITEM_REQUIRED = "required"
MAPPING_ITEM_SUB_MAP = "sub_mapping"
MAPPING_ITEM_ITEM_TYPE = "item_type"
MAPPING_ITEM_CONVERT_FUNC = "convert_func"

# Mapping table file
MAPPING_TABLE_FILE = {
    DATA_SOURCE_TYPE_FM: {DATA_TYPE_SPEC: "fm_spec_mapping.json", DATA_TYPE_METRIC: "fm_metric_mapping.json"},
    DATA_SOURCE_TYPE_OOB: {DATA_TYPE_SPEC: "oob_spec_mapping.json", DATA_TYPE_METRIC: "oob_metric_mapping.json"},
    DATA_SOURCE_TYPE_AGENT: {DATA_TYPE_METRIC: "agent_metric_mapping.json"},
}

# Acquired data item
OOB_DATA_ITEM = "devices"
FM_DATA_ITEM = "data"
AGENT_DATA_ITEM = "data"

# Power status acquisition item
DATA_ITEM_INDEX = 0
DATA_ITEM_SCHEMA = "schema"
DATA_ITEM_POWER_STATE = "PowerState"
DATA_ITEM_DRIVE = "Drive"
DATA_ITEM_NETWORK = "Network"
DATA_ITEM_OOB_LINK = "link"
DATA_ITEM_FM_LINK = "link"
DATA_ITEM_DEVICE_ID = "deviceID"
DATA_ITEM_TYPE = "type"

# Power status
POWER_STATE_ON = "On"
POWER_STATE_OFF = "Off"

# JSON data type string conversion
TYPE_STRING_CONVERT_MAP = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
    "None": type(None),
}

# Conversion target from string data type to python data type
STRING_DATA_TYPE_TARGETS = [MAPPING_ITEM_TYPE, MAPPING_ITEM_ITEM_TYPE]

# Device list information item name
DEVICE_LIST_ITEM_NAME_DEVICE_LIST = "deviceList"  # Device Information Array
DEVICE_LIST_ITEM_NAME_DEVICE_ID = "deviceID"  # Device ID
DEVICE_LIST_ITEM_NAME_DEVICE_TYPE = "type"  # Device Type

# Response item name
RESP_ITEM_NAME_LINK = "links"
RESP_ITEM_NAME_INFO_TIMESTAMP = "infoTimestamp"
RESP_ITEM_NAME_DEVICE_ID = "deviceID"
RESP_ITEM_NAME_TYPE = "type"
RESP_ITEM_NAME_CONSTRAINTS = "constraints"
RESP_ITEM_NAME_NON_REMOVABLE_DEVICES = "nonRemovableDevices"
RESP_ITEM_NAME_MODEL = "model"
RESP_ITEM_NAME_DRIVE_MODEL = "driveModel"
RESP_ITEM_NAME_NETWORK_ADAPTER_MODEL = "networkAdapterModel"
RESP_ITEM_NAME_FABRIC_ADAPTER_MODEL = "fabricAdapterModel"

# Response initialization dictionary
RESP_INIT = {RESP_ITEM_NAME_DEVICE_ID: "", RESP_ITEM_NAME_TYPE: ""}

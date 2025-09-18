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

import datetime
from app.core.info.info_core import InformationCore
from app.common.constants import TIME_STAMP_FORMAT

# Read device information file
FUNC_LOAD_DEVICE_DATA = "app.core.info.info_core.GetInformation._load_device_data"
# Device list information Item name device list
DEVICE_LIST_ITEM_NAME_DEVICE_LIST = "deviceList"
# Device list information Item name Current date and time
DEVICE_LIST_ITEM_NAME_TIME_STAMP = "infoTimestamp"

# Device ID list
DEVICE_ID_LIST = ["0001", "0002", "1001", "1002", "1003", "2001", "2002", "3001", "3002", "9999"]

# Dvice List
DEVICE_ID_TYPE_LIST = [
    {"deviceID": "0001", "type": "CPU"},
    {"deviceID": "0002", "type": "CPU"},
    {"deviceID": "1001", "type": "memory"},
    {"deviceID": "1002", "type": "memory"},
    {"deviceID": "1003", "type": "memory"},
    {"deviceID": "2001", "type": "storage"},
    {"deviceID": "2002", "type": "storage"},
    {"deviceID": "3001", "type": "networkInterface"},
    {"deviceID": "3002", "type": "networkInterface"},
    {"deviceID": "9999", "type": None},
]

# Dvice List all
DEVICE_LIST_ALL = {
    "deviceList": [
        {"deviceID": "0001", "type": "CPU"},
        {"deviceID": "0002", "type": "CPU"},
        {"deviceID": "1001", "type": "memory"},
        {"deviceID": "1002", "type": "memory"},
        {"deviceID": "1003", "type": "memory"},
        {"deviceID": "2001", "type": "storage"},
        {"deviceID": "2002", "type": "storage"},
        {"deviceID": "3001", "type": "networkInterface"},
        {"deviceID": "3002", "type": "networkInterface"},
    ]
}

# Dvice List CPU
DEVICE_LIST_CPU = {"deviceList": [{"deviceID": "0001", "type": "CPU"}, {"deviceID": "0002", "type": "CPU"}]}

# Dvice List memory
DEVICE_LIST_MEMORY = {
    "deviceList": [
        {"deviceID": "1001", "type": "memory"},
        {"deviceID": "1002", "type": "memory"},
        {"deviceID": "1003", "type": "memory"},
    ]
}

# Dvice List storage
DEVICE_LIST_STORAGE = {"deviceList": [{"deviceID": "2001", "type": "storage"}, {"deviceID": "2002", "type": "storage"}]}

# Dvice List networkInterface
DEVICE_LIST_NETWORK_INTERFACE = {
    "deviceList": [{"deviceID": "3001", "type": "networkInterface"}, {"deviceID": "3002", "type": "networkInterface"}]
}


def _log_contains(record, level, message) -> bool:
    """Comparing log contents"""
    return next(filter(lambda x: (x[1] == level) and (message in x[2]), record), None) is not None


def _get_device_list(mocker, device_type, include_time_stamp) -> dict:
    """Get device list"""

    def mock_get_controllable_device_id_list():
        return DEVICE_ID_LIST

    def mock_device_id_to_device_type(device_id):
        return next((item["type"] for item in DEVICE_ID_TYPE_LIST if item["deviceID"] == device_id), None)

    def mock_create_device_attribute(_):
        return

    # Replace obtaining the Device Type for Device ID management.
    mocker.patch("app.common.dim.device_id_base.device_id_to_device_type", side_effect=mock_device_id_to_device_type)
    # Replace the retrieval of the Device ID list for Device ID management.
    mocker.patch(
        "app.common.dim.device_id_base.get_controllable_device_id_list",
        side_effect=mock_get_controllable_device_id_list,
    )
    # Replace create_device_attribute with mock
    mocker.patch(
        "app.core.info.metric_agent.InfoMetricAgent.create_device_attribute", side_effect=mock_create_device_attribute
    )

    get_information = InformationCore()

    resp = {}
    if include_time_stamp is False:
        # Return the list of obtained device information excluding the current date and time.
        resp = {
            key: val
            for key, val in (get_information.get_device_list(device_type)).items()
            if key != DEVICE_LIST_ITEM_NAME_TIME_STAMP
        }
    else:
        resp = get_information.get_device_list(device_type)

    return resp


def test_get_device_list_all(mocker):
    """Test Get device list all"""
    # device_type=None Device list information matches.
    assert DEVICE_LIST_ALL == _get_device_list(mocker, None, False)


def test_get_device_list_cpu(mocker):
    """Test Get device list CPU"""
    # device_type=CPU Device list information matches.
    assert DEVICE_LIST_CPU == _get_device_list(mocker, "CPU", False)


def test_get_device_list_memory(mocker):
    """Test Get device list memory"""
    # device_type=memory Device list information matches.
    assert DEVICE_LIST_MEMORY == _get_device_list(mocker, "memory", False)


def test_get_device_list_storage(mocker):
    """Test Get device list storage"""
    # device_type=storage Device list information matches.
    assert DEVICE_LIST_STORAGE == _get_device_list(mocker, "storage", False)


def test_get_device_list_network_interface(mocker):
    """Test Get device list networkInterface"""
    # device_type=networkInterface Device list information matches.
    assert DEVICE_LIST_NETWORK_INTERFACE == _get_device_list(mocker, "networkInterface", False)


def test_get_device_list_no_device_list(mocker):
    """Test Get device list No Device List"""
    # The device list information does not exist for the nonexistent Device Type device_type=test.
    assert _get_device_list(mocker, "test", False).get(DEVICE_LIST_ITEM_NAME_DEVICE_LIST) is None


def test_get_device_list_info_time_stamp(mocker):
    """Test device list infoTimestamp"""
    # get infoTimestamp
    info_time_stamp_str = (_get_device_list(mocker, "CPU", True)).get(DEVICE_LIST_ITEM_NAME_TIME_STAMP, None)

    if info_time_stamp_str:
        # Convert to datetime.
        info_time_stamp_datetime = datetime.datetime.strptime(info_time_stamp_str, TIME_STAMP_FORMAT)

        # Difference from the current date and time
        diff_time = abs(datetime.datetime.now(datetime.UTC).replace(tzinfo=None) - info_time_stamp_datetime)

        # If the difference is within one minute, it is determined that the current date
        # and time have been correctly obtained.
        assert diff_time <= datetime.timedelta(minutes=1)


def test_get_device_list_road_device_data_not_dict(mocker):
    """Test Read device data not dict"""

    def mock_get_controllable_device_id_list():
        return []

    # Replace the retrieval of the Device ID list in Device ID management.
    mocker.patch(
        "app.common.dim.device_id_base.get_controllable_device_id_list",
        side_effect=mock_get_controllable_device_id_list,
    )

    get_information = InformationCore()

    resp = get_information.get_device_list(None)
    # Empty data
    assert {key: val for key, val in resp.items() if key != DEVICE_LIST_ITEM_NAME_TIME_STAMP} == {}

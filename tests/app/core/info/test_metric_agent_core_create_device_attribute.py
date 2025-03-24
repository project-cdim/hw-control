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
from pathlib import Path
from typing import List, Dict
import yaml
import app.common
import app.common.utils
import app.common.utils.file_location_settings
import app.core.info.metric_agent
from app.core.info.metric_agent import InfoMetricAgent


# Device attribute configuration file name
TEST_DEVICE_DATA_SETTING_FILE1 = "test_metric_agent_device_attribute_setting1.yaml"
TEST_DEVICE_DATA_SETTING_FILE2 = "test_metric_agent_device_attribute_setting2.yaml"

# Device Attribute Information File Name (Generated)
TEST_DEVICE_DATA_CREATE_FILE = "test_metric_agent_device_attribute_create.yaml"

# Device attribute information file name (for verification)
TEST_DEVICE_DATA_FILE1 = "test_metric_agent_device_attribute1.yaml"
TEST_DEVICE_DATA_FILE2 = "test_metric_agent_device_attribute2.yaml"

# Device ID List
DEVICE_LIST1 = [
    {"deviceID": "0001", "type": "CPU"},
    {"deviceID": "1001", "type": "memory"},
    {"deviceID": "2001", "type": "storage"},
    {"deviceID": "2002", "type": "storage"},
    {"deviceID": "3001", "type": "networkInterface"},
    {"deviceID": "3002", "type": "networkInterface"},
    {"deviceID": "4001", "type": "GPU"},
    {"deviceID": "5001", "type": "graphicController"},
]

DEVICE_LIST2: List[Dict] = []


def _create_device_attribute(mocker, monkeypatch, clear, device_list, create_file, setting_file, comp_file):
    """Create device attribute"""
    # Current path
    current_path = Path(os.path.dirname(os.path.abspath(__file__)))

    # Replace the device attribute information file name with the test device attribute information file name.
    mocker.patch.object(app.core.info.metric_agent, "DEVICE_DATA_FILE", create_file)
    # Replace the device attribute configuration file name with the test device attribute configuration file name.
    mocker.patch.object(app.core.info.metric_agent, "DEVICE_DATA_SETTING_FILE", setting_file)
    # Replace the environment variable setting file directory with the current path.
    monkeypatch.setenv("HW_CONTROL_CONFIG_FILE_DIR", str(current_path) + "/")

    # Clear the generated files.
    if clear:
        file_path = current_path / TEST_DEVICE_DATA_CREATE_FILE
        with open(file_path, "w", encoding="utf-8") as write_file:
            yaml.dump(None, write_file, default_flow_style=False, explicit_start=True, explicit_end=True)

    # Device attribute file generation
    get_metric_info = InfoMetricAgent()
    get_metric_info.create_device_attribute(device_list)

    # Loading the generated data
    file_path = current_path / TEST_DEVICE_DATA_CREATE_FILE
    with open(file_path, "r", encoding="utf-8") as create_file:
        create_data = yaml.safe_load(create_file)

    # Loading verification data.
    file_path = current_path / comp_file
    with open(file_path, "r", encoding="utf-8") as ref_file:
        ref_data = yaml.safe_load(ref_file)

    # Return the generated data.
    return create_data, ref_data


def test_create_device_attribute(mocker, monkeypatch):
    """Test create device attribute data"""
    create_data, comp_data = _create_device_attribute(
        mocker,
        monkeypatch,
        True,
        DEVICE_LIST1,
        TEST_DEVICE_DATA_CREATE_FILE,
        TEST_DEVICE_DATA_SETTING_FILE1,
        TEST_DEVICE_DATA_FILE1,
    )
    # Verification of generated data
    assert create_data == comp_data


def test_create_device_attribute_not_create(mocker, monkeypatch):
    """Test Device attribute not create"""
    create_data, comp_data = _create_device_attribute(
        mocker,
        monkeypatch,
        True,
        DEVICE_LIST2,
        TEST_DEVICE_DATA_CREATE_FILE,
        TEST_DEVICE_DATA_SETTING_FILE1,
        TEST_DEVICE_DATA_FILE2,
    )
    # Verification of generated data
    assert create_data == comp_data


def test_create_device_attribute_skip_create(mocker, monkeypatch):
    """Test create device attribute data create file skip"""
    create_data, _ = _create_device_attribute(
        mocker,
        monkeypatch,
        True,
        DEVICE_LIST1,
        TEST_DEVICE_DATA_FILE1,
        TEST_DEVICE_DATA_SETTING_FILE1,
        TEST_DEVICE_DATA_FILE1,
    )
    # Verification of generated data
    assert create_data is None

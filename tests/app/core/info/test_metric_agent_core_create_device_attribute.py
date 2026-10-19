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

import fcntl
import os
import threading
import time
from pathlib import Path

import yaml

import app.core.info.metric_agent
from app.core.info.metric_agent import DEVICE_DATA_FILE, DEVICE_DATA_SETTING_FILE, InfoMetricAgent

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

DEVICE_LIST2: list[dict] = []


def _create_device_attribute(
    mocker, monkeypatch, clear, device_list, create_file, setting_file, comp_file, trailing_slash: bool = True
):
    """Create device attribute"""
    # Current path
    current_path = Path(os.path.dirname(os.path.abspath(__file__)))

    # Replace the device attribute information file name with the test device attribute information file name.
    mocker.patch.object(app.core.info.metric_agent, "DEVICE_DATA_FILE", create_file)
    # Replace the device attribute configuration file name with the test device attribute configuration file name.
    mocker.patch.object(app.core.info.metric_agent, "DEVICE_DATA_SETTING_FILE", setting_file)
    # Replace the environment variable setting file directory with the current path.
    config_path = str(current_path)
    if trailing_slash:
        config_path += "/"
    monkeypatch.setenv("HW_CONTROL_CONFIG_FILE_DIR", config_path)
    monkeypatch.setenv("HW_CONTROL_DATA_FILE_DIR", config_path)

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
    with open(file_path, encoding="utf-8") as test_file:
        create_data = yaml.safe_load(test_file)

    # Loading verification data.
    file_path = current_path / comp_file
    with open(file_path, encoding="utf-8") as ref_file:
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


def test_create_device_attribute_no_slash(mocker, monkeypatch):
    """Test create device attribute data. No trailing slash in configuration path."""
    create_data, comp_data = _create_device_attribute(
        mocker,
        monkeypatch,
        True,
        DEVICE_LIST1,
        TEST_DEVICE_DATA_CREATE_FILE,
        TEST_DEVICE_DATA_SETTING_FILE1,
        TEST_DEVICE_DATA_FILE1,
        False,
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


def test_create_device_attribute_file_lock_wait(tmp_path, monkeypatch):
    """
    Test that create_device_attribute waits for file lock to be released.

    This test verifies that when the device attribute file is locked by the main thread,
    the sub-thread calling create_device_attribute will wait until the lock is released.
    """
    # Test file path
    test_file = tmp_path / "device_attribute.yaml"
    # Write dummy data to simulate existing file
    with open(test_file, "w", encoding="utf-8") as f:
        yaml.dump({"existing_device": {"agent": {"url": "http://test", "timeout": 30}}}, f)

    # Set configuration file directory for testing
    monkeypatch.setenv("HW_CONTROL_CONFIG_FILE_DIR", str(tmp_path))
    monkeypatch.setenv("HW_CONTROL_DATA_FILE_DIR", str(tmp_path))
    monkeypatch.setattr("app.core.info.metric_agent.DEVICE_DATA_FILE", "device_attribute.yaml")
    monkeypatch.setattr("app.core.info.metric_agent.DEVICE_DATA_SETTING_FILE", "device_attribute_setting.yaml")

    # Dummy setting file
    setting_file = tmp_path / "device_attribute_setting.yaml"
    with open(setting_file, "w", encoding="utf-8") as f:
        yaml.dump(
            {
                "DEFAULT": {
                    "agent": {"url": "http://localhost:8080", "timeout": 30},
                    "specific_data": {"macAddress": "xx", "diskID": "yy"},
                }
            },
            f,
        )

    # Flag to check lock status and exception handling
    results = {"done": False, "exception": None}

    def _target():
        try:
            agent = InfoMetricAgent()
            # Create a device list that will cause file modification
            device_list = [{"deviceID": "new_device", "type": "storage"}]
            agent.create_device_attribute(device_list)
            results["done"] = True
        except (OSError, RuntimeError) as e:
            results["exception"] = e

    # Lock the file in the main thread with exclusive lock
    with open(test_file, "r+", encoding="utf-8") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)

        # Start sub-thread (should be waiting for lock)
        t = threading.Thread(target=_target)
        t.start()

        # Wait a bit and check if sub-thread is waiting for lock
        time.sleep(1)
        assert not results["done"]  # Not finished yet (waiting for lock)
        assert results["exception"] is None  # No exception should occur yet

        # Release lock
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    # Wait for sub-thread to finish
    t.join(timeout=10)

    # Verify the sub-thread completed successfully after lock was released
    assert results["done"], "Sub-thread should complete after lock is released"
    assert results["exception"] is None, f"Unexpected exception: {results['exception']}"

    # Verify that the file was actually modified
    with open(test_file, encoding="utf-8") as f:
        final_data = yaml.safe_load(f)
        assert "new_device" in final_data, "New device should be added to the file"


def test_create_device_attribute_file_not_exists(monkeypatch, tmp_path):
    """Test create_device_attribute when device attribute file doesn't exist"""
    # Set up temporary directories
    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    config_dir.mkdir()
    data_dir.mkdir()

    # Set environment variables
    monkeypatch.setenv("HW_CONTROL_CONFIG_FILE_DIR", str(config_dir))
    monkeypatch.setenv("HW_CONTROL_DATA_FILE_DIR", str(data_dir))

    # Create device attribute setting file
    setting_file = config_dir / DEVICE_DATA_SETTING_FILE
    setting_data = {
        "DEFAULT": {
            "agent": {"url": "http://localhost:8080", "timeout": 30},
            "specific_data": {"macAddress": "xx", "diskID": "yy"},
        }
    }
    with open(setting_file, "w", encoding="utf-8") as f:
        yaml.dump(setting_data, f)

    # Device list for testing
    device_list = [
        {"deviceID": "test001", "type": "CPU"},
        {"deviceID": "test002", "type": "storage"},
        {"deviceID": "test003", "type": "networkInterface"},
    ]

    # Ensure the device attribute file doesn't exist
    device_file = data_dir / DEVICE_DATA_FILE
    assert not device_file.exists()

    # Execute create_device_attribute
    agent = InfoMetricAgent()
    agent.create_device_attribute(device_list)

    # Verify the file was created
    assert device_file.exists()

    # Load and verify the created data
    with open(device_file, encoding="utf-8") as f:
        created_data = yaml.safe_load(f)

    # Expected data structure
    expected_data = {
        "test001": {
            "agent": {"url": "http://localhost:8080", "timeout": 30},
        },
        "test002": {
            "agent": {"url": "http://localhost:8080", "timeout": 30},
            "specific_data": {"diskID": "yy"},
        },
        "test003": {
            "agent": {"url": "http://localhost:8080", "timeout": 30},
            "specific_data": {"macAddress": "xx"},
        },
    }

    assert created_data == expected_data

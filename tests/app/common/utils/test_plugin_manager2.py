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

"""Unit test module for plugin_manager."""

import sys
import os
import importlib
from unittest.mock import mock_open, patch

import pytest
from pytest import MonkeyPatch
from pytest_mock import MockFixture
import yaml

from tests.app.common.utils import test1_plugin

import app.common.basic_exceptions as exc
from app.common.utils.plugin_manager import get_oob_plugin
from app.common.utils.plugin_manager import get_fm_plugin

from app.common.utils.secret_management_utilities import secret_management_client as smc

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# For log check
PLUGIN_MGR_MODULE_NAME = "app.common.utils.plugin_manager"
CONSTANT_REQUEST_ID = "test_request_id"


def mock_import(name, *args, **kwargs):  # pylint: disable=W0613
    """setting

    mock import

    """
    return test1_plugin


def test_get_oob_plugin_err_by_check_id():
    """failed

    Manager ID: 1aB 33
    Only alphanumeric characters, "_" and "-" can be used,
    no restrictions on number of digits

    """
    m_id = "1aB 33"
    result = None

    # Get plugin
    with pytest.raises(exc.ManagerIDHWControlError):
        result = get_oob_plugin(m_id)
    # Confirm that the instance cannot be obtained
    assert result is None


def test_get_oob_plugin_err_by_open():
    """failed

    file open failed(No such file or directory)

    """
    m_id = "1aB33"
    result = None

    # Get plugin
    with pytest.raises(exc.ConfigurationHWControlError):
        result = get_oob_plugin(m_id)
    # Confirm that the instance cannot be obtained
    assert result is None


def test_get_oob_plugin_err_by_open_yaml_err():
    """failed

    yamlErr failed

    """
    m_id = "1aB33"
    result = None

    # Mock Data
    mock_data = {"module": "oob_redfish.test1_plugin", "class": "TestPlugin2"}
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data)), create=True) as mock_file:
        mock_file.return_value.__enter__.return_value = yaml.YAMLError("test error")
        # Use monkeypatch to mock importlib.import_module
        with pytest.raises(exc.ConfigurationHWControlError):
            result = get_oob_plugin(m_id)
    # Confirm that the instance cannot be obtained
    assert result is None


def test_get_oob_plugin_err_by_get_class_instance(monkeypatch: MonkeyPatch):
    """failed

    _get_class_instance failed

    """
    m_id = "1aB33"
    result = None

    # Mock Data
    mock_data = {"module": "oob_redfish.test1_plugin", "class": "TestPlugin2"}
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        with pytest.raises(exc.PluginGetInstanceHWControlError):
            result = get_oob_plugin(m_id)
    # Confirm that the instance cannot be obtained
    assert result is None


def test_get_oob_plugin_ok_no_param(monkeypatch: MonkeyPatch):
    """success

    No specific_data information

    """
    m_id = "1aB33"
    result = None

    # Mock Data
    mock_data = {"module": "oob_redfish.test1_plugin", "class": "TestPlugin"}
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = get_oob_plugin(m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value is None


def test_get_oob_plugin_ok_no_param_only_key(monkeypatch: MonkeyPatch):
    """success

    specific_data information available (only key)

    """
    m_id = "1aB33"
    result = None

    # Mock Data
    mock_data = {"module": "oob_redfish.test1_plugin", "class": "TestPlugin", "specific_data": None}
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = get_oob_plugin(m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value is None


def test_get_oob_plugin_ok_with_param_1(monkeypatch: MonkeyPatch):
    """success

    specific_data information available

    """
    m_id = "1aB33"
    result = None

    # Mock Data
    mock_data = {
        "module": "oob_redfish.test1_plugin",
        "class": "TestPlugin",
        "specific_data": {"ip": "192.168.0.11", "port": 5678},
    }
    param = {"ip": "192.168.0.11", "port": 5678}

    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = get_oob_plugin(m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value == param


def test_get_oob_plugin_ok_with_param_2(monkeypatch: MonkeyPatch):
    """success

    specific_data information available(However, some are sub keys only)

    """
    m_id = "1aB33"
    result = None

    # Mock Data
    mock_data = {
        "module": "oob_redfish.test1_plugin",
        "class": "TestPlugin",
        "specific_data": {"ip": None, "port": 5678},
    }
    param = {"ip": None, "port": 5678}

    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = get_oob_plugin(m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value == param


def test_get_oob_plugin_ok_secret_on(mocker: MockFixture, monkeypatch: MonkeyPatch):
    """success

    With secret access

    """
    m_id = "1aB33"
    result = None

    smc_data = {"id": "test", "password": "test"}

    # Mock Data
    mock_data = {
        "module": "oob_redfish.test1_plugin",
        "class": "TestPlugin",
        "secret_access": True,
        "specific_data": {"ip": None, "port": 5678},
    }
    param = {"ip": None, "port": 5678, "secret": {"id": "test", "password": "test"}}
    mocker.patch.object(smc, "get_secret", return_value=smc_data)
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = get_oob_plugin(m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value == param


def test_get_fm_plugin_err_by_check_id():
    """failed

    Manager ID: 1aB 33
    Only alphanumeric characters, "_" and "-" can be used,
    no restrictions on number of digits

    """
    m_id = "1aB 33"
    result = None

    # Get plugin
    with pytest.raises(exc.ManagerIDHWControlError):
        result = get_fm_plugin(m_id)
    # Confirm that the instance cannot be obtained
    assert result is None


def test_get_fm_plugin_err_by_open():
    """failed

    file open failed(No such file or directory)

    """
    m_id = "1aB33"
    result = None

    # Get plugin
    with pytest.raises(exc.ConfigurationHWControlError):
        result = get_fm_plugin(m_id)
    # Confirm that the instance cannot be obtained
    assert result is None


def test_get_fm_plugin_err_by_open_yaml_err():
    """failed

    yamlErr failed

    """
    m_id = "1aB33"
    result = None

    # Mock Data
    mock_data = {"module": "fm_redfish.test1_plugin", "class": "TestPlugin2"}
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data)), create=True) as mock_file:
        mock_file.return_value.__enter__.return_value = yaml.YAMLError("test error")
        # Use monkeypatch to mock importlib.import_module
        with pytest.raises(exc.ConfigurationHWControlError):
            result = get_fm_plugin(m_id)
    # Confirm that the instance cannot be obtained
    assert result is None


def test_get_fm_plugin_err_by_get_class_instance(monkeypatch: MonkeyPatch):
    """failed

    _get_class_instance failed

    """
    m_id = "1aB33"
    result = None

    # Mock Data
    mock_data = {"module": "fm_redfish.test1_plugin", "class": "TestPlugin2"}
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        with pytest.raises(exc.PluginGetInstanceHWControlError):
            result = get_fm_plugin(m_id)
    # Confirm that the instance cannot be obtained
    assert result is None


def test_get_fm_plugin_ok_no_param(monkeypatch: MonkeyPatch):
    """success

    No specific_data information

    """
    m_id = "1aB33"
    result = None

    # Mock Data
    mock_data = {"module": "fm_redfish.test1_plugin", "class": "TestPlugin"}
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = get_fm_plugin(m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value is None


def test_get_fm_plugin_ok_no_param_only_key(monkeypatch: MonkeyPatch):
    """success

    specific_data information available (only key)

    """
    m_id = "1aB33"
    result = None

    # Mock Data
    mock_data = {"module": "fm_redfish.test1_plugin", "class": "TestPlugin", "specific_data": None}
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = get_fm_plugin(m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value is None


def test_get_fm_plugin_ok_with_param_1(monkeypatch: MonkeyPatch):
    """success

    specific_data information available

    """
    m_id = "1aB33"
    result = None

    # Mock Data
    mock_data = {
        "module": "fm_redfish.test1_plugin",
        "class": "TestPlugin",
        "specific_data": {"ip": "192.168.0.11", "port": 5678},
    }
    param = {"ip": "192.168.0.11", "port": 5678}

    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = get_fm_plugin(m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value == param


def test_get_fm_plugin_ok_with_param_2(monkeypatch: MonkeyPatch):
    """success

    specific_data information available(However, some are sub keys only)

    """
    m_id = "1aB33"
    result = None

    # Mock Data
    mock_data = {
        "module": "fm_redfish.test1_plugin",
        "class": "TestPlugin",
        "specific_data": {"ip": None, "port": 5678},
    }
    param = {"ip": None, "port": 5678}

    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = get_fm_plugin(m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value == param


def test_get_fm_plugin_ok_secret_on(mocker: MockFixture, monkeypatch: MonkeyPatch):
    """success

    With secret access

    """
    m_id = "1aB33"
    result = None

    smc_data = {"id": "test", "password": "test"}

    # Mock Data
    mock_data = {
        "module": "fm_redfish.test1_plugin",
        "class": "TestPlugin",
        "secret_access": True,
        "specific_data": {"ip": None, "port": 5678},
    }
    param = {"ip": None, "port": 5678, "secret": {"id": "test", "password": "test"}}
    mocker.patch.object(smc, "get_secret", return_value=smc_data)
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = get_fm_plugin(m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value == param

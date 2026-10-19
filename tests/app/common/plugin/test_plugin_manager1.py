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

"""Unit test module for plugin_manager."""

import importlib
import logging
import os
import sys
from unittest.mock import mock_open, patch

import pytest
import yaml
from pytest_mock import MockFixture

import app.common.basic_exceptions as exc
import app.common.plugin.plugin_manager as mng
from app.common.plugin.plugin_manager import _get_plugin, get_manager_list
from app.common.utils.secret_management_utilities import secret_management_client as smc
from tests.app.common.utils import test1_plugin

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# For log check
PLUGIN_MGR_MODULE_NAME = "app.common.plugin.plugin_manager"


def mock_import(_name, *_args, **_kwargs):
    """setting

    mock import

    """
    return test1_plugin


def test_get_class_instance_invalid_model_name(caplog: pytest.LogCaptureFixture):
    """failed

    Check the format of model_name (directory name.module name) failed

    """
    manager_id = "test_id"
    m_type = "oob"
    mod1 = "test1_plugin"
    cls = "TestPlugin"
    param1 = "param1"
    inst1 = None

    # Create a class instance with one parameter
    # with pytest.raises(exc.YamlFileError):
    caplog.clear()
    with caplog.at_level(logging.INFO, logger=mng.__name__):
        with pytest.raises(exc.ConfigurationHWControlError):
            inst1 = mng._get_class_instance(manager_id, m_type, mod1, cls, param1)

    # Confirm that the instance cannot be obtained
    assert inst1 is None

    assert len(caplog.records) == 1
    # Inspection: Check the error log
    error_log = caplog.records[0]
    assert error_log.levelname == "ERROR"
    assert error_log.getMessage() == "module name is invalid."


def test_get_class_instance_err(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
    """failed

    Internal Error

    """
    manager_id = "test_id"
    m_type = "oob"
    mod1 = "oob_redfish.test1_plugin"
    cls = "TestPlugin2"
    param1 = None
    inst1 = None

    # Use monkeypatch to mock importlib.import_module
    monkeypatch.setattr(importlib, "import_module", mock_import)

    # Create a class instance with one parameter
    caplog.clear()
    with caplog.at_level(logging.INFO, logger=mng.__name__):
        with pytest.raises(exc.PluginGetInstanceHWControlError):
            inst1 = mng._get_class_instance(manager_id, m_type, mod1, cls, param1)

    # Confirm that the instance cannot be obtained
    assert inst1 is None

    assert len(caplog.records) == 1
    # Inspection: Check the error log
    error_log = caplog.records[0]
    assert error_log.levelname == "ERROR"
    assert error_log.getMessage() == "Failed to create instance."


def test_get_class_instance_ok_none_param(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
    """success

    No parameters

    """
    manager_id = "test_id"
    m_type = "oob"
    mod1 = "oob_redfish.test1_plugin"
    cls = "TestPlugin"
    param1 = None
    inst1 = None

    # Use monkeypatch to mock importlib.import_module
    monkeypatch.setattr(importlib, "import_module", mock_import)

    caplog.clear()
    with caplog.at_level(logging.INFO, logger=mng.__name__):
        # Create a class instance with one parameter
        inst1 = mng._get_class_instance(manager_id, m_type, mod1, cls, param1)

    # Verify that an instance can be obtained
    assert inst1 is not None
    assert isinstance(inst1, test1_plugin.TestPlugin)
    assert inst1.test_value is None

    assert len(caplog.records) == 1
    # Inspection: Check the plugin create log
    plugin_create_log = caplog.records[0]
    assert plugin_create_log.levelname == "INFO"
    module_path = f"plugins.{m_type}.{mod1}"
    mod = importlib.import_module(module_path)
    cls2 = getattr(mod, cls)
    cls2_inst = cls2(param1)
    assert plugin_create_log.getMessage() == f"create {type(cls2_inst)} instance."


def test_get_class_instance_ok_with_param(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture):
    """success

    With parameters

    """
    manager_id = "test_id"
    m_type = "oob"
    mod1 = "oob_redfish.test1_plugin"
    cls = "TestPlugin"
    param1 = "param1"
    inst1 = None

    # Use monkeypatch to mock importlib.import_module
    monkeypatch.setattr(importlib, "import_module", mock_import)

    caplog.clear()
    with caplog.at_level(logging.INFO, logger=mng.__name__):
        # Create a class instance with one parameter
        inst1 = mng._get_class_instance(manager_id, m_type, mod1, cls, param1)

    # Verify that an instance can be obtained
    assert inst1 is not None
    # Check the parameters passed to the class constructor are set
    assert isinstance(inst1, test1_plugin.TestPlugin)
    assert inst1.test_value == param1

    # check log
    assert len(caplog.records) == 1
    # Inspection: Check the plugin create log
    plugin_create_log = caplog.records[0]
    assert plugin_create_log.levelname == "INFO"
    module_path = f"plugins.{m_type}.{mod1}"
    mod = importlib.import_module(module_path)
    cls2 = getattr(mod, cls)
    cls2_inst = cls2(param1)
    assert plugin_create_log.getMessage() == f"create {type(cls2_inst)} instance."


def test_get_class_plugin_init_raise_unexpected_exception(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    """plugin_init_raise
    Testing the case where the plugin constructor
    throws an unexpected exception.
    """
    manager_id = "test_id"
    m_type = "oob"
    mod1 = "oob_redfish.test1_plugin"
    cls = "InvalidPlugin"
    param1 = "param1"
    inst1 = None

    # Use monkeypatch to mock importlib.import_module
    monkeypatch.setattr(importlib, "import_module", mock_import)

    # Create a class instance with one parameter
    caplog.clear()
    with caplog.at_level(logging.INFO, logger=mng.__name__):
        with pytest.raises(exc.BaseHWControlError):
            inst1 = mng._get_class_instance(manager_id, m_type, mod1, cls, param1)

    assert inst1 is None

    # check log
    assert len(caplog.records) == 1
    # Inspection: Check the plugin create log
    plugin_create_log = caplog.records[0]
    assert plugin_create_log.levelname == "ERROR"

    assert (
        plugin_create_log.getMessage()
        == f"An unexpected exception occurred while getting the class instance, manager id is {manager_id}."
    )


def test_check_manager_id_err_1(caplog: pytest.LogCaptureFixture):
    """failed

    Manager ID: 1aB%&h33
    Only alphanumeric characters, "_" and "-" can be used,
    no digit limit

    """
    m_id = "1aB%&h33"

    # Check ID
    caplog.clear()
    with caplog.at_level(logging.INFO, logger=mng.__name__):
        with pytest.raises(exc.ManagerIDHWControlError):
            mng._check_manager_id(m_id)

    # check log
    assert len(caplog.records) == 1
    # Inspection: Check the check manager id error log
    check_manager_id_error_log = caplog.records[0]
    assert check_manager_id_error_log.levelname == "ERROR"

    assert check_manager_id_error_log.getMessage() == "id contains invalid characters."


def test_check_manager_id_err_2(caplog: pytest.LogCaptureFixture):
    """failed

    Manager ID: 1aB(33)
    Only alphanumeric characters, "_" and "-" can be used,
    no digit limit

    """
    m_id = "1aB(33)"

    # Check ID
    caplog.clear()
    with caplog.at_level(logging.INFO, logger=mng.__name__):
        with pytest.raises(exc.ManagerIDHWControlError):
            mng._check_manager_id(m_id)

    # check log
    assert len(caplog.records) == 1
    # Inspection: Check the plugin create log
    plugin_create_log = caplog.records[0]
    assert plugin_create_log.levelname == "ERROR"
    assert plugin_create_log.getMessage() == "id contains invalid characters."


def test_check_manager_id_err_4(caplog: pytest.LogCaptureFixture):
    """failed

    Manager ID: 1aB'33'
    Only alphanumeric characters, "_" and "-" can be used,
    no digit limit

    """
    m_id = "1aB'33'"

    # Check ID
    caplog.clear()
    with caplog.at_level(logging.INFO, logger=mng.__name__):
        with pytest.raises(exc.ManagerIDHWControlError):
            mng._check_manager_id(m_id)

    # check log
    assert len(caplog.records) == 1
    # Inspection: Check the plugin create log
    plugin_create_log = caplog.records[0]
    assert plugin_create_log.levelname == "ERROR"
    assert plugin_create_log.getMessage() == "id contains invalid characters."


def test_check_manager_id_err_5(caplog: pytest.LogCaptureFixture):
    """failed

    Manager ID: 1aB 33
    Only alphanumeric characters, "_" and "-" can be used,
    no restrictions on number of digits

    """
    m_id = "1aB 33"

    # Check ID
    caplog.clear()
    with caplog.at_level(logging.INFO, logger=mng.__name__):
        with pytest.raises(exc.ManagerIDHWControlError):
            mng._check_manager_id(m_id)

    # check log
    assert len(caplog.records) == 1
    # Inspection: Check the plugin create log
    plugin_create_log = caplog.records[0]
    assert plugin_create_log.levelname == "ERROR"
    assert plugin_create_log.getMessage() == "id contains invalid characters."


def test_check_manager_id_err_empty(caplog: pytest.LogCaptureFixture):
    """failed

    Manager ID: "" (empty string)
    An empty manager ID is rejected, matching the "_manager.yaml" file
    exclusion (a file literally named "_manager.yaml" has an empty ID).

    """
    m_id = ""

    # Check ID
    caplog.clear()
    with caplog.at_level(logging.INFO, logger=mng.__name__):
        with pytest.raises(exc.ManagerIDHWControlError):
            mng._check_manager_id(m_id)

    # check log
    assert len(caplog.records) == 1
    # Inspection: Check the plugin create log
    plugin_create_log = caplog.records[0]
    assert plugin_create_log.levelname == "ERROR"
    assert plugin_create_log.getMessage() == "id contains invalid characters."


def test_check_manager_id_ok_1(caplog: pytest.LogCaptureFixture):
    """success

    Manager ID: 12345679098644976
    Only alphanumeric characters, "_" and "-" can be used,
    no digit limit

    """
    m_id = "12345679098644976"

    caplog.clear()
    with caplog.at_level(logging.ERROR, logger=mng.__name__):
        # Check ID
        mng._check_manager_id(m_id)

        # check log
        assert len(caplog.records) == 0, "log should be empty."


def test_check_manager_id_ok_2(caplog: pytest.LogCaptureFixture):
    """success

    Manager ID: 1234a567DDFT9098B644fgjklk976
    Only alphanumeric characters, "_" and "-" can be used,
    no digit limit

    """
    m_id = "1234a567DDFT9098B644fgjklk976"

    caplog.clear()
    with caplog.at_level(logging.ERROR, logger=mng.__name__):
        # Check ID
        mng._check_manager_id(m_id)

        # check log
        assert len(caplog.records) == 0, "log should be empty."


def test_check_manager_id_ok_3():
    """success

    Manager ID: 1234a5_67DD-FT9098_B64-4fgj_klk976
    Only alphanumeric characters, "_" and "-" can be used,
    no digit limit

    """
    m_id = "1234a5_67DD-FT9098_B64-4fgj_klk976"

    # Check ID
    mng._check_manager_id(m_id)


def test_get_manager_list_err():
    """failed

    failed(No such file or directory)

    """
    m_type = "oOb"
    result = None
    check_list = []
    # Return the list
    result = get_manager_list(m_type)
    # Check the list
    assert result == check_list


def test_get_manager_list_err_not_file():
    """failed

    It's not a file, it's a directory

    """
    m_type = "oOb"
    result = None
    file_list = [
        "1111111_abc_manager",
        "2222-abc222_manager",
        "abc33333_abc_manager",
        "4444444_manager",
        "ab-cd_ef_manager",
        "6_66-abc666_manager",
    ]
    check_list = []
    # Return the list
    with patch("app.common.plugin.plugin_manager.os.listdir") as mock_listdir:
        mock_listdir.return_value = file_list
        with patch("app.common.plugin.plugin_manager.os.path.isfile") as mock_isfile:
            mock_isfile.return_value = False
            result = get_manager_list(m_type)
    # Check the list
    assert result == check_list


def test_get_manager_list_err_no_file():
    """failed

    Subordinate is empty

    """
    m_type = "oOb"
    result = None
    file_list = []
    check_list = []
    # Return the list
    with patch("app.common.plugin.plugin_manager.os.listdir") as mock_listdir:
        mock_listdir.return_value = file_list
        with patch("app.common.plugin.plugin_manager.os.path.isfile") as mock_isfile:
            mock_isfile.return_value = True
            result = get_manager_list(m_type)
    # Check the list
    assert result == check_list


def test_get_manager_list_ok():
    """success

    The list is returned

    """
    m_type = "oOb"
    result = None
    file_list = [
        "1111111_abc_manager.yaml",
        "2222-abc222_manager.yaml",
        "abc33333_abc_manager.yaml",
        "4444444_manager.yaml",
        "ab-cd_ef_manager.yaml",
        "6_66-abc666_manager.yaml",
    ]
    check_list = ["1111111_abc", "2222-abc222", "abc33333_abc", "4444444", "ab-cd_ef", "6_66-abc666"]

    # Return the list
    with patch("app.common.plugin.plugin_manager.os.listdir") as mock_listdir:
        mock_listdir.return_value = file_list
        with patch("app.common.plugin.plugin_manager.os.path.isfile") as mock_isfile:
            mock_isfile.return_value = True
            result = get_manager_list(m_type)

    # Check the list
    assert set(result) == set(check_list)


def test_get_manager_list_ok_not_id(caplog: pytest.LogCaptureFixture):
    """success

    The list will be returned. However,
    the folder contains files that do not comply with the file rules.

    """
    m_type = "oOb"
    result = None
    file_list = [
        "1111111_abc_manager_backup.yaml",
        "2222-abc222_manager.yaml",
        "abc33333_abc_manager.yaml",
        "4444444_manager.yaml",
        "ab-cd_ef_manager.yaml.back",
        "back.6_66-abc666_manager.yaml",
    ]
    check_list = ["2222-abc222", "abc33333_abc", "4444444"]
    caplog.clear()  # clear log
    # Return the list
    with patch("app.common.plugin.plugin_manager.os.listdir") as mock_listdir:
        mock_listdir.return_value = file_list
        with patch("app.common.plugin.plugin_manager.os.path.isfile") as mock_isfile:
            mock_isfile.return_value = True

            caplog.clear()
            with caplog.at_level(logging.INFO, logger=mng.__name__):
                result = get_manager_list(m_type)
    # Check the list
    assert result == check_list

    # check log
    file = file_list[5]
    err = ""

    # check log
    assert len(caplog.records) == 2
    # Inspection: Check the manager ID check error log
    manager_id_check_error_log = caplog.records[0]
    assert manager_id_check_error_log.levelname == "ERROR"
    assert manager_id_check_error_log.getMessage() == "id contains invalid characters."

    # Inspection: Check the skip error log
    skip_error_log = caplog.records[1]
    assert skip_error_log.levelname == "ERROR"
    assert skip_error_log.getMessage() == f"skip {file} because {err}."

    assert skip_error_log.exc_info is not None, "exc_info should be present in the log record"
    assert skip_error_log.exc_info[0] is not None
    assert skip_error_log.exc_info[0].__name__ == "ManagerIDHWControlError"


def test_get_manager_list_ok_not_yaml(caplog: pytest.LogCaptureFixture):
    """success

    A list is returned.
    However, the folder contains files that do not follow the file rules
    and files that are not YAML.

    """
    m_type = "oOb"
    result = None
    file_list = [
        "1111111_abc_manager.yaml",
        "2222-abc222_manager.yaml",
        "abc33333_abc_manager.txt",
        "4444444_manager.yaml",
        "ab-cd_ef_manager.yaml.back",
        "back.6_66-abc666_manager.yaml",
    ]
    check_list = ["1111111_abc", "2222-abc222", "4444444"]

    # Return the list
    with patch("app.common.plugin.plugin_manager.os.listdir") as mock_listdir:
        mock_listdir.return_value = file_list
        with patch("app.common.plugin.plugin_manager.os.path.isfile") as mock_isfile:
            mock_isfile.return_value = True

            caplog.clear()
            with caplog.at_level(logging.INFO, logger=mng.__name__):
                result = get_manager_list(m_type)

    # Check the list
    assert result == check_list

    # check log
    assert len(caplog.records) == 2
    # Inspection: Check the manager ID check error log
    manager_id_check_error_log = caplog.records[0]
    assert manager_id_check_error_log.levelname == "ERROR"
    assert manager_id_check_error_log.getMessage() == "id contains invalid characters."

    # Inspection: Check the skip error log
    file = file_list[5]
    err = ""
    skip_error_log = caplog.records[1]
    assert skip_error_log.levelname == "ERROR"
    assert skip_error_log.getMessage() == f"skip {file} because {err}."
    assert skip_error_log.exc_info is not None, "exc_info should be present in the log record"
    assert skip_error_log.exc_info[0] is not None
    assert skip_error_log.exc_info[0].__name__ == "ManagerIDHWControlError"


def test_get_plugin_err_none_type():
    """failed

    failed(No such file or directory)

    """
    m_type = None
    m_id = "1aB33"
    result = None
    with pytest.raises(exc.APIUsageHWControlError):
        result = _get_plugin(m_type, m_id)
    # Confirm that the instance cannot be obtained
    assert result is None


def test_get_plugin_err_by_check_id():
    """failed

    Manager ID: 1aB 33
    Only alphanumeric characters, "_" and "-" can be used,
    no restrictions on number of digits

    """
    m_type = "oOb"
    m_id = "1aB 33"
    result = None

    # Get plugin
    with pytest.raises(exc.ManagerIDHWControlError):
        result = _get_plugin(m_type, m_id)
    # Confirm that the instance cannot be obtained
    assert result is None


def test_get_plugin_err_by_open():
    """failed

    file open failed(No such file or directory)

    """
    m_type = "oOb"
    m_id = "1aB33"
    result = None

    # Get plugin
    with pytest.raises(exc.ConfigurationHWControlError):
        result = _get_plugin(m_type, m_id)
    # Confirm that the instance cannot be obtained
    assert result is None


def test_get_plugin_err_by_open_yaml_err():
    """failed

    yamlErr failed

    """
    m_type = "oOb"
    m_id = "1aB33"
    result = None

    # Mock Data
    mock_data = {"module": "oob_redfish.test1_plugin", "class": "TestPlugin2"}
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data)), create=True) as mock_file:
        mock_file.return_value.__enter__.return_value = yaml.YAMLError("test error")
        # Use monkeypatch to mock importlib.import_module
        with pytest.raises(exc.ConfigurationHWControlError):
            result = _get_plugin(m_type, m_id)
    # Confirm that the instance cannot be obtained
    assert result is None


def test_get_plugin_err_by_no_module(monkeypatch: pytest.MonkeyPatch):
    """failed

    _get_class_instance failed

    """
    m_type = "oOb"
    m_id = "1aB33"
    result = None

    # Mock Data
    mock_data = {"class": "TestPlugin2"}
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        with pytest.raises(exc.ConfigurationHWControlError):
            result = _get_plugin(m_type, m_id)
    # Confirm that the instance cannot be obtained
    assert result is None


def test_get_plugin_err_by_no_class(monkeypatch: pytest.MonkeyPatch):
    """failed

    _get_class_instance failed

    """
    m_type = "oOb"
    m_id = "1aB33"
    result = None

    # Mock Data
    mock_data = {"module": "oob_redfish.test1_plugin"}
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        with pytest.raises(exc.ConfigurationHWControlError):
            result = _get_plugin(m_type, m_id)
    # Confirm that the instance cannot be obtained
    assert result is None


def test_get_plugin_err_by_get_class_instance(monkeypatch: pytest.MonkeyPatch):
    """failed

    _get_class_instance failed

    """
    m_type = "oOb"
    m_id = "1aB33"
    result = None

    # Mock Data
    mock_data = {"module": "oob_redfish.test1_plugin", "class": "TestPlugin2"}
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        with pytest.raises(exc.PluginGetInstanceHWControlError):
            result = _get_plugin(m_type, m_id)
    # Confirm that the instance cannot be obtained
    assert result is None


def test_get_plugin_ok_no_param(monkeypatch: pytest.MonkeyPatch):
    """success

    No specific_data information

    """
    m_type = "oOb"
    m_id = "1aB33"
    result = None

    # Mock Data
    mock_data = {"module": "oob_redfish.test1_plugin", "class": "TestPlugin"}
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = _get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert isinstance(result, test1_plugin.TestPlugin)
    assert result.test_value is None


def test_get_plugin_ok_no_param_only_key(monkeypatch: pytest.MonkeyPatch):
    """success

    specific_data information available (only key)

    """
    m_type = "oOb"
    m_id = "1aB33"
    result = None

    # Mock Data
    mock_data = {"module": "oob_redfish.test1_plugin", "class": "TestPlugin", "specific_data": None}
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = _get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert isinstance(result, test1_plugin.TestPlugin)
    assert result.test_value is None


def test_get_plugin_ok_with_param_1(monkeypatch: pytest.MonkeyPatch):
    """success

    specific_data information available

    """
    m_type = "oOb"
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
        result = _get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert isinstance(result, test1_plugin.TestPlugin)
    assert result.test_value == param


def test_get_plugin_ok_with_param_2(monkeypatch: pytest.MonkeyPatch):
    """success

    specific_data information available(However, some are sub keys only)

    """
    m_type = "oOb"
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
        result = _get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert isinstance(result, test1_plugin.TestPlugin)
    assert result.test_value == param


def test_get_plugin_ok_secret_on(mocker: MockFixture, monkeypatch: pytest.MonkeyPatch):
    """success

    With secret access

    """
    m_type = "oOb"
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
        result = _get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert isinstance(result, test1_plugin.TestPlugin)
    assert result.test_value == param


def test_get_plugin_ok_secret_on_fm(mocker: MockFixture, monkeypatch: pytest.MonkeyPatch):
    """success

    With secret access

    """
    m_type = "FM"
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
        result = _get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert isinstance(result, test1_plugin.TestPlugin)
    assert result.test_value == param


def test_get_plugin_ok_secret_on_no_data(mocker: MockFixture, monkeypatch: pytest.MonkeyPatch):
    """success

    With secret access(no data)

    """
    m_type = "oOb"
    m_id = "1aB33"
    result = None

    smc_data: dict = {}

    # Mock Data
    mock_data = {
        "module": "oob_redfish.test1_plugin",
        "class": "TestPlugin",
        "secret_access": True,
        "specific_data": {"ip": None, "port": 5678},
    }
    param: dict = {"ip": None, "port": 5678, "secret": {}}
    mocker.patch.object(smc, "get_secret", return_value=smc_data)
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = _get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert isinstance(result, test1_plugin.TestPlugin)
    assert result.test_value == param


def test_get_plugin_ok_secret_on_no_specific_data(mocker: MockFixture, monkeypatch: pytest.MonkeyPatch):
    """success

    With secret access

    """
    m_type = "oOb"
    m_id = "1aB33"
    result = None

    smc_data = {"id": "test", "password": "test"}

    # Mock Data
    mock_data = {
        "module": "oob_redfish.test1_plugin",
        "class": "TestPlugin",
        "secret_access": True,
    }
    param = {"secret": {"id": "test", "password": "test"}}
    mocker.patch.object(smc, "get_secret", return_value=smc_data)
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = _get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert isinstance(result, test1_plugin.TestPlugin)
    assert result.test_value == param


def test_get_plugin_ok_secret_on_empty_specific_data(mocker: MockFixture, monkeypatch: pytest.MonkeyPatch):
    """success

    With secret access

    """
    m_type = "oOb"
    m_id = "1aB33"
    result = None

    smc_data = {"id": "test", "password": "test"}

    # Mock Data
    mock_data = {
        "module": "oob_redfish.test1_plugin",
        "class": "TestPlugin",
        "secret_access": True,
        "specific_data": None,
    }
    param = {"secret": {"id": "test", "password": "test"}}
    mocker.patch.object(smc, "get_secret", return_value=smc_data)
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = _get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert isinstance(result, test1_plugin.TestPlugin)
    assert result.test_value == param


def test_get_plugin_ok_secret_on_not_dict_specific_data(mocker: MockFixture, monkeypatch: pytest.MonkeyPatch, caplog):
    """success

    With secret access

    """
    m_type = "oOb"
    m_id = "1aB33"

    smc_data = {"id": "test", "password": "test"}

    # Mock Data
    mock_data = {
        "module": "oob_redfish.test1_plugin",
        "class": "TestPlugin",
        "secret_access": True,
        "specific_data": "test",
    }
    mocker.patch.object(smc, "get_secret", return_value=smc_data)
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=mng.__name__):
            with pytest.raises(exc.ConfigurationHWControlError):
                _get_plugin(m_type, m_id)

    # check log
    assert len(caplog.records) == 1
    # Inspection: Check the manager ID check error log
    plugin_instance_error_log = caplog.records[0]
    assert plugin_instance_error_log.levelname == "ERROR"
    assert (
        plugin_instance_error_log.getMessage()
        == f"The specific data in plugin configuration file is incorrect, manager id is {m_id}."
    )


def test_get_plugin_ok_secret_off_bool(mocker: MockFixture, monkeypatch: pytest.MonkeyPatch):
    """success

    No secret access(secret_access is bool(False))

    """
    m_type = "oOb"
    m_id = "1aB33"
    result = None

    smc_data = {"id": "test", "password": "test"}

    # Mock Data
    mock_data = {
        "module": "oob_redfish.test1_plugin",
        "class": "TestPlugin",
        "secret_access": False,
        "specific_data": {"ip": None, "port": 5678},
    }
    param = {"ip": None, "port": 5678}
    mocker.patch.object(smc, "get_secret", return_value=smc_data)
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = _get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert isinstance(result, test1_plugin.TestPlugin)
    assert result.test_value == param


def test_get_plugin_ok_secret_off_int(mocker: MockFixture, monkeypatch: pytest.MonkeyPatch):
    """success

    No secret access(secret_access is int)

    """
    m_type = "oOb"
    m_id = "1aB33"
    result = None

    smc_data = {"id": "test", "password": "test"}

    # Mock Data
    mock_data = {
        "module": "oob_redfish.test1_plugin",
        "class": "TestPlugin",
        "secret_access": 1234,
        "specific_data": {"ip": None, "port": 5678},
    }
    param = {"ip": None, "port": 5678}
    mocker.patch.object(smc, "get_secret", return_value=smc_data)
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = _get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert isinstance(result, test1_plugin.TestPlugin)
    assert result.test_value == param


def test_get_plugin_ok_secret_off_str(mocker: MockFixture, monkeypatch: pytest.MonkeyPatch):
    """success

    No secret access(secret_access is str)

    """
    m_type = "oOb"
    m_id = "1aB33"
    result = None

    smc_data = {"id": "test", "password": "test"}

    # Mock Data
    mock_data = {
        "module": "oob_redfish.test1_plugin",
        "class": "TestPlugin",
        "secret_access": "True",
        "specific_data": {"ip": None, "port": 5678},
    }
    param = {"ip": None, "port": 5678}
    mocker.patch.object(smc, "get_secret", return_value=smc_data)
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = _get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert isinstance(result, test1_plugin.TestPlugin)
    assert result.test_value == param


def test_get_plugin_ok_secret_off_none(mocker: MockFixture, monkeypatch: pytest.MonkeyPatch):
    """success

    No secret access(secret_access is None)

    """
    m_type = "oOb"
    m_id = "1aB33"
    result = None

    smc_data = {"id": "test", "password": "test"}

    # Mock Data
    mock_data = {
        "module": "oob_redfish.test1_plugin",
        "class": "TestPlugin",
        "secret_access": None,
        "specific_data": {"ip": None, "port": 5678},
    }
    param = {"ip": None, "port": 5678}
    mocker.patch.object(smc, "get_secret", return_value=smc_data)
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = _get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert isinstance(result, test1_plugin.TestPlugin)
    assert result.test_value == param


def test_get_plugin_ok_secret_off_no_key(mocker: MockFixture, monkeypatch: pytest.MonkeyPatch):
    """success

    No secret access(no secret_access key)

    """
    m_type = "oOb"
    m_id = "1aB33"
    result = None

    smc_data = {"id": "test", "password": "test"}

    # Mock Data
    mock_data = {
        "module": "oob_redfish.test1_plugin",
        "class": "TestPlugin",
        "specific_data": {"ip": None, "port": 5678},
    }
    param = {"ip": None, "port": 5678}
    mocker.patch.object(smc, "get_secret", return_value=smc_data)
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        result = _get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert isinstance(result, test1_plugin.TestPlugin)
    assert result.test_value == param


def test_get_plugin_ok_secret_on_dependency_service_hw_control_error(
    mocker: MockFixture, monkeypatch: pytest.MonkeyPatch
):
    """success

    secret access error(DependencyServiceHWControlError)

    """
    m_type = "oOb"
    m_id = "1aB33"

    mock_get_secret = mocker.patch("app.common.plugin.plugin_manager.smc.get_secret")
    mock_get_secret.side_effect = exc.DependencyServiceHWControlError

    # Mock Data
    mock_data = {
        "module": "oob_redfish.test1_plugin",
        "class": "TestPlugin",
        "secret_access": True,
        "specific_data": {"ip": None, "port": 5678},
    }
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        with pytest.raises(exc.DependencyServiceHWControlError):
            _get_plugin(m_type, m_id)


def test_get_plugin_ok_secret_on_other_error(mocker: MockFixture, monkeypatch: pytest.MonkeyPatch):
    """success

    secret access error(others)

    """
    m_type = "oOb"
    m_id = "1aB33"

    mock_get_secret = mocker.patch("app.common.plugin.plugin_manager.smc.get_secret")
    mock_get_secret.side_effect = exc.ConfigurationHWControlError

    # Mock Data
    mock_data = {
        "module": "oob_redfish.test1_plugin",
        "class": "TestPlugin",
        "secret_access": True,
        "specific_data": {"ip": None, "port": 5678},
    }
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        with pytest.raises(exc.ConfigurationHWControlError):
            _get_plugin(m_type, m_id)

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

import logging
import sys
import os
import importlib
import json

from unittest.mock import mock_open, patch
import pytest
from pytest import LogCaptureFixture, MonkeyPatch
from pytest_mock import MockFixture
import yaml

from tests.app.common.utils import test1_plugin

import app.common.basic_exceptions as exc
import app.common.utils.plugin_manager as mng
from app.common.utils.plugin_manager import check_plugin
from app.common.utils.plugin_manager import get_manager_list
from app.common.utils.plugin_manager import get_plugin

from app.common.utils.secret_management_utilities import secret_management_client as smc

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# For log check
PLUGIN_MGR_MODULE_NAME = "app.common.utils.plugin_manager"


def check_log_message(caplog: LogCaptureFixture, levelname, request_id, messages):
    """

    check log

    """
    index = 0
    for record in caplog.records:
        plugin_call_log_message = json.loads(record.getMessage())
        if record.levelname == levelname and plugin_call_log_message["message"]["request_id"] == request_id:
            assert plugin_call_log_message["message"]["detail"] == messages[index]
            index += 1
    assert len(messages) == index


def mock_import(name, *args, **kwargs):  # pylint: disable=W0613
    """setting

    mock import

    """
    return test1_plugin


def test_get_class_instance_invalid_model_name(caplog: LogCaptureFixture):
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
    with pytest.raises(exc.ConfigurationHWControlError):
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=mng.__name__):
            inst1 = mng._get_class_instance(manager_id, m_type, mod1, cls, param1)  # pylint: disable=W0212

    # Confirm that the instance cannot be obtained
    assert inst1 is None

    assert len(caplog.records) == 1
    # Inspection: Check the error log
    error_log = caplog.records[0]
    assert error_log.levelname == "ERROR"
    assert error_log.getMessage() == "module name is invalid."


def test_get_class_instance_none_model_name(caplog: LogCaptureFixture):
    """failed

    model_name is None

    """

    manager_id = "test_id"
    m_type = "oob"
    mod1 = None
    cls = "TestPlugin"
    param1 = "param1"
    inst1 = None

    # Create a class instance with one parameter
    with pytest.raises(exc.ConfigurationHWControlError):
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=mng.__name__):
            inst1 = mng._get_class_instance(manager_id, m_type, mod1, cls, param1)  # pylint: disable=W0212

    # Confirm that the instance cannot be obtained
    assert inst1 is None

    assert len(caplog.records) == 1
    # Inspection: Check the error log
    error_log = caplog.records[0]
    assert error_log.levelname == "ERROR"
    assert (
        error_log.getMessage()
        == f"module name is missing or not properly set in the setting file, manager id is {manager_id}."
    )


def test_get_class_instance_none_class_name(caplog: LogCaptureFixture):
    """failed

    class_name is None

    """

    manager_id = "test_id"
    m_type = "oob"
    mod1 = "test1_plugin"
    cls = None
    param1 = "param1"
    inst1 = None

    # Create a class instance with one parameter
    with pytest.raises(exc.ConfigurationHWControlError):
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=mng.__name__):
            inst1 = mng._get_class_instance(manager_id, m_type, mod1, cls, param1)  # pylint: disable=W0212

    # Confirm that the instance cannot be obtained
    assert inst1 is None

    assert len(caplog.records) == 1
    # Inspection: Check the error log
    error_log = caplog.records[0]
    assert error_log.levelname == "ERROR"
    assert (
        error_log.getMessage()
        == f"class name is missing or not properly set in the setting file, manager id is {manager_id}."
    )


def test_get_class_instance_err(monkeypatch: MonkeyPatch, caplog: LogCaptureFixture):
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
    with pytest.raises(exc.PluginGetInstanceHWControlError):
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=mng.__name__):
            inst1 = mng._get_class_instance(manager_id, m_type, mod1, cls, param1)  # pylint: disable=W0212

    # Confirm that the instance cannot be obtained
    assert inst1 is None

    assert len(caplog.records) == 1
    # Inspection: Check the error log
    error_log = caplog.records[0]
    assert error_log.levelname == "ERROR"
    assert error_log.getMessage() == "Failed to create instance."


def test_get_class_instance_ok_none_param(monkeypatch: MonkeyPatch, caplog: LogCaptureFixture):
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
        inst1 = mng._get_class_instance(manager_id, m_type, mod1, cls, param1)  # pylint: disable=W0212

    # Verify that an instance can be obtained
    assert inst1 is not None
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


def test_get_class_instance_ok_with_param(monkeypatch: MonkeyPatch, caplog: LogCaptureFixture):
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
        inst1 = mng._get_class_instance(manager_id, m_type, mod1, cls, param1)  # pylint: disable=W0212

    # Verify that an instance can be obtained
    assert inst1 is not None
    # Check the parameters passed to the class constructor are set
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


def test_get_class_plugin_init_raise_unexpected_exception(monkeypatch: MonkeyPatch, caplog: LogCaptureFixture):
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
    with pytest.raises(exc.BaseHWControlError):
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=mng.__name__):
            inst1 = mng._get_class_instance(manager_id, m_type, mod1, cls, param1)  # pylint: disable=W0212

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


def test_check_manager_id_err_1(caplog: LogCaptureFixture):
    """failed

    Manager ID: 1aB%&h33
    Only alphanumeric characters, "_" and "-" can be used,
    no digit limit

    """
    m_id = "1aB%&h33"

    # Check ID
    with pytest.raises(exc.ManagerIDHWControlError):
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=mng.__name__):
            mng._check_manager_id(m_id)  # pylint: disable=W0212

    # check log
    assert len(caplog.records) == 1
    # Inspection: Check the check manager id error log
    check_manager_id_error_log = caplog.records[0]
    assert check_manager_id_error_log.levelname == "ERROR"

    assert check_manager_id_error_log.getMessage() == "id contains invalid characters."


def test_check_manager_id_err_2(caplog: LogCaptureFixture):
    """failed

    Manager ID: 1aB(33)
    Only alphanumeric characters, "_" and "-" can be used,
    no digit limit

    """
    m_id = "1aB(33)"

    # Check ID
    with pytest.raises(exc.ManagerIDHWControlError):
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=mng.__name__):
            mng._check_manager_id(m_id)  # pylint: disable=W0212

    # check log
    assert len(caplog.records) == 1
    # Inspection: Check the plugin create log
    plugin_create_log = caplog.records[0]
    assert plugin_create_log.levelname == "ERROR"
    assert plugin_create_log.getMessage() == "id contains invalid characters."


def test_check_manager_id_err_4(caplog: LogCaptureFixture):
    """failed

    Manager ID: 1aB'33'
    Only alphanumeric characters, "_" and "-" can be used,
    no digit limit

    """
    m_id = "1aB'33'"

    # Check ID
    with pytest.raises(exc.ManagerIDHWControlError):
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=mng.__name__):
            mng._check_manager_id(m_id)  # pylint: disable=W0212

    # check log
    assert len(caplog.records) == 1
    # Inspection: Check the plugin create log
    plugin_create_log = caplog.records[0]
    assert plugin_create_log.levelname == "ERROR"
    assert plugin_create_log.getMessage() == "id contains invalid characters."


def test_check_manager_id_err_5(caplog: LogCaptureFixture):
    """failed

    Manager ID: 1aB 33
    Only alphanumeric characters, "_" and "-" can be used,
    no restrictions on number of digits

    """
    m_id = "1aB 33"

    # Check ID
    with pytest.raises(exc.ManagerIDHWControlError):
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=mng.__name__):
            mng._check_manager_id(m_id)  # pylint: disable=W0212

    # check log
    assert len(caplog.records) == 1
    # Inspection: Check the plugin create log
    plugin_create_log = caplog.records[0]
    assert plugin_create_log.levelname == "ERROR"
    assert plugin_create_log.getMessage() == "id contains invalid characters."


def test_check_manager_id_ok_1(caplog: LogCaptureFixture):
    """success

    Manager ID: 12345679098644976
    Only alphanumeric characters, "_" and "-" can be used,
    no digit limit

    """
    m_id = "12345679098644976"

    caplog.clear()
    with caplog.at_level(logging.ERROR, logger=mng.__name__):
        # Check ID
        mng._check_manager_id(m_id)  # pylint: disable=W0212

        # check log
        assert len(caplog.records) == 0, "log should be empty."


def test_check_manager_id_ok_2(caplog: LogCaptureFixture):
    """success

    Manager ID: 1234a567DDFT9098B644fgjklk976
    Only alphanumeric characters, "_" and "-" can be used,
    no digit limit

    """
    m_id = "1234a567DDFT9098B644fgjklk976"

    caplog.clear()
    with caplog.at_level(logging.ERROR, logger=mng.__name__):
        # Check ID
        mng._check_manager_id(m_id)  # pylint: disable=W0212

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
    mng._check_manager_id(m_id)  # pylint: disable=W0212


def test_check_plugin_err_by_check_id():
    """failed

    Manager ID: 1aB 33
    Only alphanumeric characters, "_" and "-" can be used,
    no restrictions on number of digits

    """
    m_type = "oOb"
    m_id = "1aB 33"

    # Check plugin
    with pytest.raises(exc.ManagerIDHWControlError):
        check_plugin(m_type, m_id)


def test_check_plugin_err_by_open(caplog: LogCaptureFixture):
    """File open failure case.

    file open failure(No such file or directory)

    """
    m_type = "oOb"
    m_id = "1aB33"

    # Check plugin
    with pytest.raises(exc.ConfigurationHWControlError):
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=mng.__name__):
            check_plugin(m_type, m_id)

    # check log
    assert len(caplog.records) == 1
    # Inspection: Check the plugin create log
    plugin_create_log = caplog.records[0]
    assert plugin_create_log.levelname == "ERROR"
    assert plugin_create_log.getMessage() == "The plugin configuration file of 1aB33 was not found."


def test_check_plugin_err_by_get_class_instance(monkeypatch: MonkeyPatch):
    """failed

    _get_class_instance failed

    """
    m_type = "oOb"
    m_id = "1aB33"

    # Mock Data
    mock_data = {"module": "oob_redfish.test1_plugin", "class": "TestPlugin2"}
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        with pytest.raises(exc.PluginGetInstanceHWControlError):
            check_plugin(m_type, m_id)


def test_check_plugin_err_by_open_yaml_err(monkeypatch: MonkeyPatch, caplog: LogCaptureFixture):
    """File open failure case.

    File open failure (yamlErr)

    """
    m_type = "oOb"
    m_id = "1aB33"

    # Mock Data
    mock_data = {"module": "oob_redfish.test1_plugin", "class": "TestPlugin2"}
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data)), create=True) as mock_file:
        mock_file.return_value.__enter__.return_value = yaml.YAMLError("test error")
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        with pytest.raises(exc.ConfigurationHWControlError):
            caplog.clear()
            with caplog.at_level(logging.INFO, logger=mng.__name__):
                check_plugin(m_type, m_id)

    # check log
    assert len(caplog.records) == 1
    # Inspection: Check the plugin create log
    plugin_create_log = caplog.records[0]
    assert plugin_create_log.levelname == "ERROR"
    assert plugin_create_log.getMessage() == "The plugin configuration file of 1aB33 is incorrect."


def test_check_plugin_ok(monkeypatch: MonkeyPatch):
    """success

    _get_class_instance succeeded,
    but the function itself did not return anything.

    """
    m_type = "oOb"
    m_id = "1aB33"

    # Mock Data
    mock_data = {"module": "oob_redfish.test1_plugin", "class": "TestPlugin"}
    # Creating mocks
    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
        # Use monkeypatch to mock importlib.import_module
        monkeypatch.setattr(importlib, "import_module", mock_import)
        check_plugin(m_type, m_id)


def test_check_plugin_none_type():
    """failed

    type is None

    """
    m_type = None
    m_id = "1aB 33"

    # Check plugin
    with pytest.raises(exc.APIUsageHWControlError):
        check_plugin(m_type, m_id)


def test_check_plugin_none_id():
    """failed

    id is None

    """
    m_type = "oOb"
    m_id = None

    # Check plugin
    with pytest.raises(exc.APIUsageHWControlError):
        check_plugin(m_type, m_id)


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


def test_get_manager_list_err_none_type():
    """failed

    failed(No such file or directory)

    """
    m_type = None
    result = []
    check_list = []
    with pytest.raises(exc.APIUsageHWControlError):
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
    with patch("app.common.utils.plugin_manager.os.listdir") as mock_listdir:
        mock_listdir.return_value = file_list
        with patch("app.common.utils.plugin_manager.os.path.isfile") as mock_isfile:
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
    with patch("app.common.utils.plugin_manager.os.listdir") as mock_listdir:
        mock_listdir.return_value = file_list
        with patch("app.common.utils.plugin_manager.os.path.isfile") as mock_isfile:
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
    with patch("app.common.utils.plugin_manager.os.listdir") as mock_listdir:
        mock_listdir.return_value = file_list
        with patch("app.common.utils.plugin_manager.os.path.isfile") as mock_isfile:
            mock_isfile.return_value = True
            result = get_manager_list(m_type)

    # Check the list
    assert set(result) == set(check_list)


def test_get_manager_list_ok_not_id(caplog: LogCaptureFixture):
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
    with patch("app.common.utils.plugin_manager.os.listdir") as mock_listdir:
        mock_listdir.return_value = file_list
        with patch("app.common.utils.plugin_manager.os.path.isfile") as mock_isfile:
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


def test_get_manager_list_ok_not_yaml(caplog: LogCaptureFixture):
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
    with patch("app.common.utils.plugin_manager.os.listdir") as mock_listdir:
        mock_listdir.return_value = file_list
        with patch("app.common.utils.plugin_manager.os.path.isfile") as mock_isfile:
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
        result = get_plugin(m_type, m_id)
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
        result = get_plugin(m_type, m_id)
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
        result = get_plugin(m_type, m_id)
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
            result = get_plugin(m_type, m_id)
    # Confirm that the instance cannot be obtained
    assert result is None


def test_get_plugin_err_by_get_class_instance(monkeypatch: MonkeyPatch):
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
            result = get_plugin(m_type, m_id)
    # Confirm that the instance cannot be obtained
    assert result is None


def test_get_plugin_ok_no_param(monkeypatch: MonkeyPatch):
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
        result = get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value is None


def test_get_plugin_ok_no_param_only_key(monkeypatch: MonkeyPatch):
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
        result = get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value is None


def test_get_plugin_ok_with_param_1(monkeypatch: MonkeyPatch):
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
        result = get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value == param


def test_get_plugin_ok_with_param_2(monkeypatch: MonkeyPatch):
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
        result = get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value == param


def test_get_plugin_ok_secret_on(mocker: MockFixture, monkeypatch: MonkeyPatch):
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
        result = get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value == param


def test_get_plugin_ok_secret_on_fm(mocker: MockFixture, monkeypatch: MonkeyPatch):
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
        result = get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value == param


def test_get_plugin_ok_secret_on_no_data(mocker: MockFixture, monkeypatch: MonkeyPatch):
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
        result = get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value == param


def test_get_plugin_ok_secret_on_no_specific_data(mocker: MockFixture, monkeypatch: MonkeyPatch):
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
        result = get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value == param


def test_get_plugin_ok_secret_on_empty_specific_data(mocker: MockFixture, monkeypatch: MonkeyPatch):
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
        result = get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value == param


def test_get_plugin_ok_secret_on_not_dict_specific_data(mocker: MockFixture, monkeypatch: MonkeyPatch, caplog):
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
        with pytest.raises(exc.ConfigurationHWControlError):

            caplog.clear()
            with caplog.at_level(logging.INFO, logger=mng.__name__):
                get_plugin(m_type, m_id)

    # check log
    assert len(caplog.records) == 1
    # Inspection: Check the manager ID check error log
    plugin_instance_error_log = caplog.records[0]
    assert plugin_instance_error_log.levelname == "ERROR"
    assert (
        plugin_instance_error_log.getMessage()
        == f"The specific data in plugin configuration file is incorrect, manager id is {m_id}."
    )


def test_get_plugin_ok_secret_off_bool(mocker: MockFixture, monkeypatch: MonkeyPatch):
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
        result = get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value == param


def test_get_plugin_ok_secret_off_int(mocker: MockFixture, monkeypatch: MonkeyPatch):
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
        result = get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value == param


def test_get_plugin_ok_secret_off_str(mocker: MockFixture, monkeypatch: MonkeyPatch):
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
        result = get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value == param


def test_get_plugin_ok_secret_off_none(mocker: MockFixture, monkeypatch: MonkeyPatch):
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
        result = get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value == param


def test_get_plugin_ok_secret_off_no_key(mocker: MockFixture, monkeypatch: MonkeyPatch):
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
        result = get_plugin(m_type, m_id)
    # Verify that an instance can be obtained
    assert result is not None
    assert result.test_value == param


def test_get_plugin_ok_secret_on_dependency_service_hw_control_error(mocker: MockFixture, monkeypatch: MonkeyPatch):
    """success

    secret access error(DependencyServiceHWControlError)

    """
    m_type = "oOb"
    m_id = "1aB33"

    mock_get_secret = mocker.patch("app.common.utils.plugin_manager.smc.get_secret")
    mock_get_secret.side_effect = exc.DependencyServiceHWControlError

    # Mock Data
    mock_data = {
        "module": "oob_redfish.test1_plugin",
        "class": "TestPlugin",
        "secret_access": True,
        "specific_data": {"ip": None, "port": 5678},
    }
    # Creating mocks
    with pytest.raises(exc.DependencyServiceHWControlError):
        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
            # Use monkeypatch to mock importlib.import_module
            monkeypatch.setattr(importlib, "import_module", mock_import)
            get_plugin(m_type, m_id)


def test_get_plugin_ok_secret_on_other_error(mocker: MockFixture, monkeypatch: MonkeyPatch):
    """success

    secret access error(others)

    """
    m_type = "oOb"
    m_id = "1aB33"

    mock_get_secret = mocker.patch("app.common.utils.plugin_manager.smc.get_secret")
    mock_get_secret.side_effect = exc.ConfigurationHWControlError

    # Mock Data
    mock_data = {
        "module": "oob_redfish.test1_plugin",
        "class": "TestPlugin",
        "secret_access": True,
        "specific_data": {"ip": None, "port": 5678},
    }
    # Creating mocks
    with pytest.raises(exc.ConfigurationHWControlError):
        with patch("builtins.open", mock_open(read_data=yaml.dump(mock_data))):
            # Use monkeypatch to mock importlib.import_module
            monkeypatch.setattr(importlib, "import_module", mock_import)
            with pytest.raises(ValueError):
                get_plugin(m_type, m_id)

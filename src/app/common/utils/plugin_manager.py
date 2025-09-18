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

"""Plugin management

By dynamically loading plugins,
it is possible to operate according to the environment.

"""

import logging
from typing import cast, Any
import importlib
import os
import re
import yaml

from app.common.utils.plugin_base import ManagerPluginBase
from app.common.utils.fm_plugin_base import FMPluginBase
from app.common.utils.oob_plugin_base import OOBPluginBase
import app.common.basic_exceptions as exc
from app.common.utils.secret_management_utilities import secret_management_client as smc
from app.common.constants import ManagerType

logger = logging.getLogger(__name__)

_SETTING_FILE_DIR = "/plugins/"
_setting_file_base_path = (
    os.path.abspath(os.path.join(os.path.realpath(__file__), os.pardir, os.pardir, os.pardir, os.pardir))
    + _SETTING_FILE_DIR
)


def _get_secret_info(manager_type: str, manager_id: str) -> dict:
    """Get secret information

    Get secret information from Secret Store.

    Args:
        manager_type (str): The type of manager
        manager_id (str): The ID of manager

    Returns:
        secret: Secret information

    Raises:
        pydantic.ValidationError: From API get_secret,
            send to the upper layer without handling.
        PluginGetInstanceHWControlError: From API get_secret,
            send to the upper layer without handling.
        InternalHWControlError: From API get_secret,
            send to the upper layer without handling.
        ConfigurationHWControlError: From API get_secret,
            send to the upper layer without handling.
    """
    secret = None
    # Currently, there are only two types: fm and oob.
    if manager_type == "fm":
        secret_store = smc.SecretStore.FM
    else:
        # manager_type is oob:
        secret_store = smc.SecretStore.OOB

    secret = smc.get_secret(secret_store, manager_id)

    return secret


def _get_class_instance(
    manager_id: str, manager_type: str, module_name: str, class_name: str, init_param: Any = None
) -> ManagerPluginBase:
    """Get class instance (internal common processing)

    Common process to get class instance of plug-in.

    Args:
        manager_id (str): The ID of manager
        manager_type (str): The type of manager
        module_name (str): The name of module
        class_name (str): The name of class
        init_param (Any): The parameter passed to the class constructor

    Returns:
        class instance: The class instance of the specified module

    Raises:
        ConfigurationHWControlError: An error occurred when
            incorrect in the plugin configuration file
        PluginGetInstanceHWControlError: An error occurred when getting
            the plugin instance failed
        UnexpectedExceptionHWControlError: An error occurred when Plugin
            constructor raised unexpected exception.
    """
    logger.debug("begin manager_type=%s module_name=%s class_name=%s", manager_type, module_name, class_name)

    # Argument check
    # None check
    if module_name is None:
        logger.error("module name is missing or not properly set in the setting file, manager id is %s.", manager_id)
        raise exc.ConfigurationHWControlError(additional_message="The Plugin Configuration File is incorrect.")

    if class_name is None:
        logger.error("class name is missing or not properly set in the setting file, manager id is %s.", manager_id)
        raise exc.ConfigurationHWControlError(additional_message="The Plugin Configuration File is incorrect.")

    # format check of module_name (directory name.module name)
    parts = module_name.split(".")
    if len(parts) < 2 or any(not part for part in parts):
        logger.error("module name is invalid.")
        raise exc.ConfigurationHWControlError(additional_message="The Plugin Configuration File is incorrect.")

    try:
        # Create module path from module name
        module_path = f"plugins.{manager_type}.{module_name}"
        logger.debug("module_path=%s", module_path)

        # Initialize the returned class instance with None
        cls_inst = None
        # Get the module object
        mod = importlib.import_module(module_path)
        logger.debug("import")

        # Clear cache
        importlib.invalidate_caches()
        # Get class
        cls = getattr(mod, class_name)
        logger.debug("getattr")

        # Create instance of class
        cls_inst = cls(init_param)
        logger.info("create %s instance.", type(cls_inst))
        logger.debug("end")

    # ImportError: Raised in _get_class_instance(),
    #     when the import statement fails to load the module.
    # ModuleNotFoundError: Raised in _get_class_instance(),
    #     when the module is not found.
    # AttributeError: Raised in _get_class_instance(),
    #     when the class is not found.
    # ValueError: Raised in _get_class_instance(),
    #     when class instantiation fails (Incorrect specific_data).
    # TypeError: Raised in _get_class_instance(),
    #     when class instantiation fails (No Method)
    # other Exceptions maybe occurred, but don't catch them here,
    # they are caught at the higher-level function.
    except (TypeError, ImportError, AttributeError, ValueError) as err:
        logger.error("Failed to create instance.")
        raise exc.PluginGetInstanceHWControlError from err

    except Exception as err:
        # Plugin constructor raised unexpected exception.
        logger.error("An unexpected exception occurred while getting the class instance, manager id is %s.", manager_id)
        raise exc.UnexpectedExceptionHWControlError from err

    return cls_inst


def _check_manager_id(manager_id: str) -> None:
    """Check the ID of manager (internal common processing)

    Check whether the ID of the specified installation manager is
    according to the rules.
    The ID is an identifier that can identify the manager (OOB/FM) and
    is determined by the higher-level function.
    Only alphanumeric characters and "_" and "-" can be used,
    and there is no specification for the number of digits

    Args:
        manager_id (str): The ID of manager

    Returns:
        No returns

    Raises:
        ManagerIDHWControlError: An error occurred due to an incorrect
            Manager ID
    """
    pattern = r"[^A-Za-z0-9_-]"
    if re.search(pattern, manager_id):
        logger.error("id contains invalid characters.")
        raise exc.ManagerIDHWControlError


def check_plugin(manager_type: str, manager_id: str) -> None:
    """Check whether the plugin is enabled

    Check whether the plugin of specified manager is enabled

    Args:
        manager_type (str): The type of manager
                            (Currently, only OOB or FM)
                            Not case sensitive
        manager_id (str): The ID of manager

    Returns:
        No returns

    Raises:
        APIUsageHWControlError: An error occurred when a function
            argument is incorrect
        ManagerIDHWControlError: An error occurred due to an incorrect
            Manager ID
        ConfigurationHWControlError: An error occurred when
            the plugin configuration file is not found
            or incorrect in the plugin configuration file
        PluginGetInstanceHWControlError: An error occurred when getting
            the plugin instance failed
    """

    # Normalize specified manager type (convert to lowercase)
    try:
        m_type = manager_type.lower()
        logger.debug("Manager Type is %s.", m_type)
        # Check the ID of manager
        _check_manager_id(manager_id)
    # AttributeError: Raised when manager_type or manager_id is none
    # TypeError: Raised when type of manager_type or type of manager_id
    #     is not str
    except (AttributeError, TypeError) as err:
        raise exc.APIUsageHWControlError from err
    # Identify the plugin configuration file based
    # on the manager_type and ID
    setting_file = _setting_file_base_path + m_type + "/" + manager_id + "_manager.yaml"
    logger.debug("Plugin Configuration File is %s.", setting_file)
    try:
        # Get the name of module and class
        # from the plugin configuration file
        with open(setting_file, encoding="utf-8") as f_setting_file:
            data = yaml.safe_load(f_setting_file)
            module_name = data.get("module", None)
            class_name = data.get("class", None)
        logger.debug("module name is %s.", module_name)
        logger.debug("class name is %s.", class_name)
    # FileNotFoundError: Raised when the yaml file is not found.
    except FileNotFoundError as err:
        logger.error("The plugin configuration file of %s was not found.", manager_id)
        raise exc.ConfigurationHWControlError(
            additional_message=("The Plugin Configuration File is not found.")
        ) from err
    # yaml.YAMLError: Raised when the file does not conform to
    #     YAML format.
    # AttributeError: Raised if "data" is None
    except (yaml.YAMLError, AttributeError, PermissionError) as err:
        logger.error("The plugin configuration file of %s is incorrect.", manager_id)
        raise exc.ConfigurationHWControlError(
            additional_message=("The Plugin Configuration File is incorrect.")
        ) from err

    # Invoke _get_class_instance() to get class instance
    cls_inst = _get_class_instance(manager_id, m_type, module_name, class_name, None)
    # Delete class instance
    del cls_inst


def get_manager_list(manager_type: str) -> list[str]:
    """Get the list of managers

    Get the list of the specified managers(list of IDs).

    Args:
        manager_type (str): The type of manager
                            (Currently, only OOB or FM)
                            Not case sensitive

    Returns:
        list of manager id: The list of the specified managers
                            (list of IDs)

    Raises:
        APIUsageHWControlError: An error occurred when a function
            argument is incorrect
    """

    # Normalize specified manager type (convert to lowercase)
    try:
        m_type = manager_type.lower()
    # AttributeError: Raised when manager_type is none
    # TypeError: Raised when type of manager_type is not str
    except (AttributeError, TypeError) as err:
        raise exc.APIUsageHWControlError from err
    logger.debug("Manager Type is %s.", m_type)
    # Identify the path of plugin configuration files based
    # on the manager_type
    setting_file_path = _setting_file_base_path + m_type + "/"
    logger.debug("path of Plugin Configuration File is %s.", setting_file_path)
    id_list = []
    # Get the IDs from all plugin configuration files located under the
    # specified path.
    for file in os.listdir(setting_file_path):
        if not os.path.isfile(os.path.join(setting_file_path, file)):
            continue
        try:
            if file.endswith("_manager.yaml"):
                m_id = file.split("_manager.yaml")[0]
                # Check the ID of manager
                _check_manager_id(m_id)
                id_list.append(m_id)
                logger.debug("Add manager %s into list.", m_id)
        except (AttributeError, IndexError, ValueError, exc.ManagerIDHWControlError) as err:
            logger.error("skip %s because %s.", file, err, exc_info=True)
    return id_list


def get_fm_plugin(manager_id: str) -> FMPluginBase:
    """Get class instance of the FM plugin

    Get the class instance of the FM plugin.

    Args:
        manager_id (str): The ID of manager

    Returns:
        class instance: The class instance of the FM plugin

    Raises:
        APIUsageHWControlError: An error occurred when a function
            argument is incorrect
        ManagerIDHWControlError: An error occurred due to an incorrect
            Manager ID
        PluginGetInstanceHWControlError: An error occurred when getting
            the plugin instance failed

        InternalHWControlError: From API get_secret,
            send to the upper layer without handling.
        ConfigurationHWControlError: An error occurred when
            the plugin configuration file is not found
            or incorrect in the plugin configuration file
        ConfigurationHWControlError: From API get_secret,
            send to the upper layer without handling.
    """
    return cast(FMPluginBase, get_plugin(ManagerType.FM.value, manager_id))


def get_oob_plugin(manager_id: str) -> OOBPluginBase:
    """Get class instance of the OOB plugin

    Get the class instance of the OOB plugin.

    Args:
        manager_id (str): The ID of manager

    Returns:
        class instance: The class instance of the OOB plugin

    Raises:
        APIUsageHWControlError: An error occurred when a function
            argument is incorrect
        ManagerIDHWControlError: An error occurred due to an incorrect
            Manager ID
        PluginGetInstanceHWControlError: An error occurred when getting
            the plugin instance failed

        InternalHWControlError: From API get_secret,
            send to the upper layer without handling.
        ConfigurationHWControlError: An error occurred when
            the plugin configuration file is not found
            or incorrect in the plugin configuration file
        ConfigurationHWControlError: From API get_secret,
            send to the upper layer without handling.
    """
    return cast(OOBPluginBase, get_plugin(ManagerType.OOB.value, manager_id))


def get_plugin(manager_type: str, manager_id: str) -> ManagerPluginBase:
    """Get class instance

    Get the class instance of the specified .

    Args:
        manager_type (str): The type of manager
                            (Currently, only OOB or FM)
                            Not case sensitive
        manager_id (str): The ID of manager

    Returns:
        class instance: The class instance of the specified plugin

    Raises:
        APIUsageHWControlError: An error occurred when a function
            argument is incorrect
        ManagerIDHWControlError: An error occurred due to an incorrect
            Manager ID
        PluginGetInstanceHWControlError: An error occurred when getting
            the plugin instance failed

        pydantic.ValidationError: From API get_secret,
            send to the upper layer without handling.
        InternalHWControlError: From API get_secret,
            send to the upper layer without handling.
        ConfigurationHWControlError: An error occurred when
            the plugin configuration file is not found
            or incorrect in the plugin configuration file
        ConfigurationHWControlError: From API get_secret,
            send to the upper layer without handling.
    """

    # Normalize specified manager type (convert to lowercase)
    try:
        m_type = manager_type.lower()
        logger.debug("Manager Type is %s.", m_type)
        # Check the ID of manager
        _check_manager_id(manager_id)
    # AttributeError: Raised when manager_type or manager_id is none
    # TypeError: Raised when type of manager_type or type of manager_id
    #     is not str
    except (AttributeError, TypeError) as err:
        raise exc.APIUsageHWControlError from err
    # Identify the plugin configuration file based
    # on the manager_type and ID
    setting_file = _setting_file_base_path + m_type + "/" + manager_id + "_manager.yaml"
    logger.debug("Plugin Configuration File is %s.", setting_file)
    try:
        # Get the name of module and class,
        # and authentication information
        # from the plugin configuration file
        with open(setting_file, encoding="utf-8") as f_setting_file:
            data = yaml.safe_load(f_setting_file)
            module_name = data.get("module", None)
            class_name = data.get("class", None)
            specific_data = data.get("specific_data", None)
            secret_access = data.get("secret_access", False)
        logger.debug("module name is %s.", module_name)
        logger.debug("class name is %s.", class_name)
    # FileNotFoundError: Raised when the yaml file is not found.
    except FileNotFoundError as err:
        logger.error("The plugin configuration file of %s was not found.", manager_id)
        raise exc.ConfigurationHWControlError(
            additional_message=("The Plugin Configuration File is not found.")
        ) from err
    # yaml.YAMLError: Raised when the file does not conform to
    #     YAML format.
    # AttributeError: Raised if "data" is None
    #     or if "module" or "class" is not included in "data"
    except (yaml.YAMLError, AttributeError, PermissionError) as err:
        logger.error("The plugin configuration file of %s is incorrect.", manager_id)
        raise exc.ConfigurationHWControlError(
            additional_message=("The Plugin Configuration File is incorrect.")
        ) from err

    if specific_data is not None and not isinstance(specific_data, dict):
        logger.error("The specific data in plugin configuration file is incorrect, manager id is %s.", manager_id)
        raise exc.ConfigurationHWControlError(additional_message="The Plugin Configuration File is incorrect.")

    if isinstance(secret_access, bool) and secret_access:
        # Get secret information
        specific_data = specific_data or {}
        specific_data["secret"] = _get_secret_info(m_type, manager_id)

    # Invoke _get_class_instance() to get class instance
    cls_inst = _get_class_instance(manager_id, m_type, module_name, class_name, specific_data)
    return cls_inst

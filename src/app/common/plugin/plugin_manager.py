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

"""Plugin management.

By dynamically loading plugins, it is possible to operate according to
the environment.

get_plugin returns a plugin execution class instance for either a remote
plugin (configured under FileLocationSettings.plugin_file_dir) or a legacy
Python module plugin (via ServicePluginFMCompatible / ServicePluginOOBCompatible),
depending on where the manager's configuration file is found.

"""

import importlib
import logging
import os
import re
from collections import Counter
from typing import Annotated, Any, cast
from warnings import deprecated

import yaml
from pydantic import StringConstraints, ValidationError, validate_call

import app.common.basic_exceptions as exc
from app.common.constants import ManagerType
from app.common.plugin.compat import ServicePluginFMCompatible, ServicePluginOOBCompatible
from app.common.plugin.service import ServicePlugin, ServicePluginConfig
from app.common.utils.file_location_settings import FileLocationSettings
from app.common.utils.fm_plugin_base import FMPluginBase
from app.common.utils.oob_plugin_base import OOBPluginBase
from app.common.utils.plugin_base import ManagerPluginBase
from app.common.utils.secret_management_utilities import secret_management_client as smc

logger = logging.getLogger(__name__)

_SETTING_FILE_DIR = "/plugins/"
_setting_file_base_path = (
    os.path.abspath(os.path.join(os.path.realpath(__file__), os.pardir, os.pardir, os.pardir, os.pardir))
    + _SETTING_FILE_DIR
)

_MANAGER_FILE_SUFFIX = "_manager.yaml"

# Manager ID type: alphanumeric characters, "_" and "-", one or more characters.
ManagerID = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]+$", min_length=1)]


def _get_secret_info(manager_type: str, manager_id: str) -> dict:
    """Get secret information.

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
    """Get class instance (internal common processing).

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
    """Check the ID of manager (internal common processing).

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
    # "" is rejected explicitly: re.search() on an empty string finds no
    # match (no invalid characters), so it would otherwise pass unnoticed.
    # None/non-str values are left to raise TypeError, as before, so callers
    # that translate that into a different error (e.g. APIUsageHWControlError)
    # keep working.
    if manager_id == "" or re.search(pattern, manager_id):
        logger.error("id contains invalid characters.")
        raise exc.ManagerIDHWControlError


def get_manager_list(manager_type: str | None = None) -> list[str]:
    """Get the list of managers.

    Get the list of the specified managers(list of IDs).

    Args:
        manager_type (str | None): The type of manager
                            ("fm" or "oob", not case sensitive), or None.
                            If None, the manager IDs of the remote plugins,
                            the legacy FM plugins and the legacy OOB
                            plugins are all returned.

    Returns:
        list of manager id: The list of the specified managers
                            (list of IDs)

    Raises:
        APIUsageHWControlError: An error occurred when a function
            argument is incorrect
    """
    if manager_type is None:
        manager_ids = _get_remote_manager_ids()
        manager_ids.extend(_get_legacy_manager_list(ManagerType.FM.value))
        manager_ids.extend(_get_legacy_manager_list(ManagerType.OOB.value))
        # A manager ID must be unique across remote/legacy-FM/legacy-OOB
        # plugins (see spec section 6.1), but deduplicate defensively here,
        # keeping the first occurrence in remote -> FM -> OOB priority order.
        deduplicated_ids = list(dict.fromkeys(manager_ids))
        if len(deduplicated_ids) != len(manager_ids):
            duplicate_ids = [item for item, count in Counter(manager_ids).items() if count > 1]
            logger.warning("Duplicate manager IDs found: %s", duplicate_ids)
        return deduplicated_ids
    return _get_legacy_manager_list(manager_type)


def _get_legacy_manager_list(manager_type: str) -> list[str]:
    """Get the list of managers of the legacy Python module plugins.

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
    if m_type not in (ManagerType.FM.value.lower(), ManagerType.OOB.value.lower()):
        logger.error("manager_type %s is neither 'fm' nor 'oob'.", m_type)
        raise exc.APIUsageHWControlError
    logger.debug("Manager Type is %s.", m_type)
    # Identify the path of plugin configuration files based
    # on the manager_type
    setting_file_path = _setting_file_base_path + m_type + "/"
    logger.debug("path of Plugin Configuration File is %s.", setting_file_path)
    try:
        file_list = os.listdir(setting_file_path)
    # An unavailable configuration directory is not an argument error, so it is
    # treated the same as "no configuration file found" and returns an empty
    # list, as _get_remote_manager_ids does.
    # FileNotFoundError: Raised when the configuration directory for
    #     "fm"/"oob" does not exist.
    # NotADirectoryError: Raised when setting_file_path is not a directory.
    # PermissionError: Raised when setting_file_path is not readable.
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        logger.debug("The plugin configuration directory %s is unavailable.", setting_file_path)
        return []
    id_list = []
    # Get the IDs from all plugin configuration files located under the
    # specified path.
    for file in file_list:
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
            logger.exception("skip %s because %s.", file, err)
    return id_list


def _get_remote_manager_ids() -> list[str]:
    """Get the manager IDs found in the remote plugin configuration directory.

    Returns:
        list[str]: The list of manager IDs of the remote plugins.
    """
    plugin_file_dir = FileLocationSettings().plugin_file_dir
    try:
        file_names = os.listdir(plugin_file_dir)
    # FileNotFoundError: Raised when the directory does not exist.
    # NotADirectoryError: Raised when plugin_file_dir is not a directory.
    # PermissionError: Raised when plugin_file_dir is not readable.
    except (FileNotFoundError, NotADirectoryError, PermissionError):
        logger.debug("The plugin configuration directory %s is unavailable.", plugin_file_dir)
        return []

    manager_ids = []
    for file_name in file_names:
        file_path = os.path.join(plugin_file_dir, file_name)
        if not os.path.isfile(file_path) or not file_name.endswith(_MANAGER_FILE_SUFFIX):
            continue
        manager_id = file_name[: -len(_MANAGER_FILE_SUFFIX)]
        try:
            _check_manager_id(manager_id)
        except exc.ManagerIDHWControlError as err:
            logger.exception("skip %s because %s.", file_name, err)
            continue
        try:
            _load_service_plugin_config(plugin_file_dir, manager_id)
        except exc.ConfigurationHWControlError as err:
            logger.exception("skip %s because %s.", file_name, err)
            continue
        manager_ids.append(manager_id)
    return manager_ids


@deprecated("use get_plugin(manager_id) instead", category=None)
def get_fm_plugin(manager_id: str) -> FMPluginBase:
    """Get class instance of the FM plugin.

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
    return cast(FMPluginBase, _get_plugin(ManagerType.FM.value, manager_id))


@deprecated("use get_plugin(manager_id) instead", category=None)
def get_oob_plugin(manager_id: str) -> OOBPluginBase:
    """Get class instance of the OOB plugin.

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
    return cast(OOBPluginBase, _get_plugin(ManagerType.OOB.value, manager_id))


def _get_plugin(manager_type: str, manager_id: str) -> ManagerPluginBase:
    """Get class instance of a legacy Python module plugin.

    Get the class instance of the specified legacy plugin.

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
            module_name = str(data["module"])
            class_name = str(data["class"])
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
    # KeyError: Raised if "module" or "class" is not included in "data"
    # Typerror: Raised if yaml.safe_load returns a non-dict type (e.g. list, str)
    except (yaml.YAMLError, AttributeError, KeyError, TypeError, PermissionError) as err:
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


@validate_call
def get_plugin(manager_id: ManagerID) -> ServicePlugin:
    """Get an instance of the plugin execution class for the specified manager.

    The configuration file search order is: remote plugin directory
    (HW_CONTROL_PLUGIN_FILE_DIR) -> legacy FM plugin directory -> legacy OOB
    plugin directory. The first location where a matching configuration
    file is found determines which plugin execution class is returned.

    Args:
        manager_id (ManagerID): Manager ID.

    Returns:
        ServicePlugin: An instance of ServicePlugin (or a subclass, for
            legacy plugins) for the specified manager.

    Raises:
        pydantic.ValidationError: `manager_id` is not a string consisting of
            alphanumeric characters, "-" and "_".
        ConfigurationHWControlError: No matching plugin configuration file
            was found, or its content is incorrect.
        PluginGetInstanceHWControlError: The legacy plugin class could not
            be obtained. (legacy plugins only)
        UnexpectedExceptionHWControlError: The legacy plugin constructor
            raised an exception. (legacy plugins only)
        See `secret_management_client.get_secret` for the exceptions raised
            when retrieving secrets for legacy plugins.
    """
    plugin_file_dir = FileLocationSettings().plugin_file_dir
    file_path = os.path.join(plugin_file_dir, f"{manager_id}{_MANAGER_FILE_SUFFIX}")
    if os.path.isfile(file_path):
        config = _load_service_plugin_config(plugin_file_dir, manager_id)
        plugin = ServicePlugin(config)
        plugin.manager_id = manager_id
        return plugin

    legacy_setting_file = _setting_file_base_path + "{manager_type}/" + manager_id + _MANAGER_FILE_SUFFIX
    if os.path.isfile(legacy_setting_file.format(manager_type=ManagerType.FM.value.lower())):
        fm_plugin = ServicePluginFMCompatible()
        fm_plugin.plugin = get_fm_plugin(manager_id)
        fm_plugin.manager_id = manager_id
        return fm_plugin

    if os.path.isfile(legacy_setting_file.format(manager_type=ManagerType.OOB.value.lower())):
        oob_plugin = ServicePluginOOBCompatible()
        oob_plugin.plugin = get_oob_plugin(manager_id)
        oob_plugin.manager_id = manager_id
        return oob_plugin

    logger.error("The Plugin Configuration File of %s was not found.", manager_id)
    raise exc.ConfigurationHWControlError(additional_message="The Plugin Configuration File is not found.")


def _load_service_plugin_config(plugin_file_dir: str, manager_id: str) -> ServicePluginConfig:
    """Load and validate the plugin configuration file for `manager_id`.

    Raises:
        ConfigurationHWControlError: The file is not found, is not valid
            YAML, or does not match ServicePluginConfig.
    """
    file_path = os.path.join(plugin_file_dir, f"{manager_id}{_MANAGER_FILE_SUFFIX}")
    try:
        with open(file_path, encoding="utf-8") as setting_file:
            data = yaml.safe_load(setting_file)
        return ServicePluginConfig.model_validate(data)
    except FileNotFoundError as err:
        logger.error("The Plugin Configuration File of %s was not found.", manager_id)
        raise exc.ConfigurationHWControlError(additional_message="The Plugin Configuration File is not found.") from err
    except (yaml.YAMLError, AttributeError, PermissionError, ValidationError, ValueError) as err:
        logger.error("The Plugin Configuration File of %s is incorrect.", manager_id)
        raise exc.ConfigurationHWControlError(additional_message="The Plugin Configuration File is incorrect.") from err

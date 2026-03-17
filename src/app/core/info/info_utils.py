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

"""HW independent section - Get Information process (Response generation)

Upon receiving a request from the information acquisition API,
make an information acquisition request for the specified Device ID to FM and OOB.
Merge the device information returned from FM and OOB for each device
type and return it to the information acquisition API.

"""

import logging
import json
from pathlib import Path
from typing import Any
from app.common.basic_exceptions import InternalHWControlError
import app.common.constants as const
from app.common.dim import device_id_base as dim
from app.common.messages import message
from app.common.settings import settings
from app.core.info import info_const, info_conv_funcs

logger = logging.getLogger(__name__)


def get_mapping_table(device_type: str, data_type: str, data_source_type: str) -> dict | None:
    """Get mapping table

    Return the mapping table that corresponds to the Device Type and data source and data type.

    Args:
        device_type (str): Device Type
        data_type (str): data type
        data_source_type (str): data source type

    Returns:
        dict | None: mapping table
    """
    # Extract the mapping table corresponding to the Device Type.
    mapping_table = info_const.MAPPING_TABLE[data_type][data_source_type].get(device_type, None)

    return mapping_table


def remove_empty_item(resp: Any) -> Any:
    """Remove empty item

    Remove empty items from response data.

    Args:
        resp (Any): response data

    Returns:
        Any: response data
    """

    def _is_not_empty(val: Any) -> bool:
        """Check not empty
        Check if the value is not empty or unwanted.
        Args:
            val (Any): value
        Returns:
            bool: check result
        """
        if val in (None, "", "NODATA"):
            return False
        if isinstance(val, str) and val.strip() == "":
            return False
        return True

    if isinstance(resp, dict):
        # Exclude items with no values using dictionary comprehension
        return {
            key: clean_val
            for key, val in resp.items()
            if _is_not_empty(val) and (clean_val := remove_empty_item(val)) not in ({}, [])
        }

    if isinstance(resp, list):
        # Exclude items with no values using list comprehension
        return [
            clean_val for val in resp if _is_not_empty(val) and (clean_val := remove_empty_item(val)) not in ({}, [])
        ]

    return resp


def create_resp_from_mapping(mapping_table: dict, source_data: dict) -> dict[str, Any]:
    """Create response data from mapping table

    Create response data from source data according to mapping table.

    Args:
        mapping_table (dict): mapping table
        source_data (dict): source data

    Returns:
        dict[str, Any]: response data
    """
    response_data: dict[str, Any] = {}

    # Loops while extracting the destination key and its mapping information.
    for dest_key, mapping_data in mapping_table.items():

        # Source key name. (If no key name is specified, the same key name is used)
        key = mapping_data.get(info_const.MAPPING_ITEM_KEY, dest_key)

        # If a path is specified (different hierarchy to migrate to),
        if info_const.MAPPING_ITEM_PATH in mapping_data:
            parts = mapping_data[info_const.MAPPING_ITEM_PATH].split(".")
            temp_data: dict[str, Any] | Any = source_data
            # Extract the path value.
            for part in parts:
                temp_data = temp_data.get(part, {})
            value = temp_data
        else:
            # Extract data for the source key.
            value = source_data.get(key, None)  # type: ignore[assignment]

        if isinstance(value, dict):
            # Process the target dict type data by recursive calls.
            response_data[dest_key] = create_resp_from_mapping(
                mapping_data.get(info_const.MAPPING_ITEM_SUB_MAP, {}), value
            )
        elif isinstance(value, list):
            # Item held in list type is sub_mapping specified. (dict type)
            if info_const.MAPPING_ITEM_SUB_MAP in mapping_data:
                # Process dict type data in the list by recursive calls.
                list_data = [
                    create_resp_from_mapping(mapping_data.get(info_const.MAPPING_ITEM_SUB_MAP, {}), item)
                    for item in value
                ]
                response_data[dest_key] = list_data
            else:
                # Item held in list type is a single data type. (str, int, etc.)
                response_data[dest_key] = check_convert_item(mapping_data, key, value)
        else:
            # Set value to destination.
            response_data[dest_key] = check_convert_item(mapping_data, key, value)

    return response_data


def _check_required_item(mapping_data: dict, key: str, item_value: Any) -> None:
    """Check required item

    Check for the presence of values in required item based on the mapping data.

    Args:
        mapping_data (dict): mapping data
        key (str): item key
        item_value (Any): item value

    Returns:
        None
    """
    if mapping_data.get(info_const.MAPPING_ITEM_REQUIRED, False) and (
        item_value is None or (isinstance(item_value, str) and item_value.strip() == "")
    ):
        logger.warning(message.get_log_message(message.W00008, [f"key:{key}"]))
        raise InternalHWControlError(additional_message="The received data is missing required item.")


def _check_list_item_types(mapping_data: dict, key: str, item_value: Any) -> None:
    """Check list item type

    Check the data type of items in the list based on the mapping data.

    Args:
        mapping_data (dict): mapping data
        key (str): item key
        item_value (Any): item value

    Returns:
        None
    """
    if isinstance(item_value, list) and info_const.MAPPING_ITEM_ITEM_TYPE in mapping_data:
        target_type = mapping_data[info_const.MAPPING_ITEM_ITEM_TYPE]
        for item in item_value:
            if not isinstance(item, target_type):
                target_type_name = (
                    ",".join(type_.__name__ for type_ in target_type)
                    if isinstance(target_type, tuple)
                    else target_type.__name__
                )
                logger.warning(
                    message.get_log_message(
                        message.W00009,
                        [f"Key:{key}, Value:{item}, Value type:{type(item).__name__}, Target type:{target_type_name}"],
                    )
                )
                raise InternalHWControlError(additional_message="The data type of the received item is invalid.")


def _check_item_type(mapping_data: dict, key: str, item_value: Any) -> None:
    """Check item type

    Check the data type of item based on the mapping data.

    Args:
        mapping_data (dict): mapping data
        key (str): item key
        item_value (Any): item value

    Returns:
        None
    """
    if info_const.MAPPING_ITEM_TYPE in mapping_data and not (
        item_value is None or (isinstance(item_value, str) and item_value.strip() == "")
    ):
        target_type = mapping_data[info_const.MAPPING_ITEM_TYPE]
        if not isinstance(item_value, target_type):
            target_type_name = (
                ",".join(type_.__name__ for type_ in target_type)
                if isinstance(target_type, tuple)
                else target_type.__name__
            )
            logger.warning(
                message.get_log_message(
                    message.W00009,
                    [
                        (
                            f"Key:{key}, Value:{item_value}, Value type:{type(item_value).__name__}, "
                            f"Target type:{target_type_name}"
                        )
                    ],
                )
            )
            raise InternalHWControlError(additional_message="The data type of the received item is invalid.")


def _execute_if_callable(mapping_data: dict, key: str, item_value: Any) -> Any:
    """Execute function if callable

    Check if the conversion function is callable and return the execution result.

    Args:
        mapping_data (dict): mapping data
        key (str): item key
        item_value (Any): item value

    Returns:
        Any: item value
    """
    # If item_value is None or an empty string, return it as is.
    if item_value is None or (isinstance(item_value, str) and item_value.strip() == ""):
        return item_value

    if info_const.MAPPING_ITEM_CONVERT_FUNC in mapping_data and callable(
        mapping_data[info_const.MAPPING_ITEM_CONVERT_FUNC]
    ):
        result = mapping_data[info_const.MAPPING_ITEM_CONVERT_FUNC](mapping_data, key, item_value)
        if result is None:
            msg = (
                f"Key:{key}, Value:{item_value}, Value type:{type(item_value).__name__}, "
                f"Convert function:{(mapping_data[info_const.MAPPING_ITEM_CONVERT_FUNC]).__name__} returned None."
            )
            logger.warning(message.get_log_message(message.W00009, [msg]))
            raise InternalHWControlError(
                additional_message="The conversion failed because an unexpected value was provided."
            )
        return result
    return item_value


def check_convert_item(mapping_data: dict, key: str, item_value: Any) -> Any:
    """Check and convert mapping item

    Check and convert item value based on mapping data.

    Args:
        mapping_data (dict): mapping data
        key (str): item key
        item_value (Any): item value

    Returns:
        Any: item value
    """
    _check_required_item(mapping_data, key, item_value)
    _check_list_item_types(mapping_data, key, item_value)
    _check_item_type(mapping_data, key, item_value)
    return _execute_if_callable(mapping_data, key, item_value)


def load_mapping_table() -> None:
    """Load mapping table

    Load the mapping table file into the global variable.

    """
    mapping_table = None

    # Initialize
    info_const.MAPPING_TABLE = {}

    for data_type, source_types in info_const.MAPPING_TABLE_FILE.items():
        info_const.MAPPING_TABLE[data_type] = {}
        for source_type in source_types:
            # Mapping table file path.
            file_path = Path(settings.MAPPING_TABLE_PATH) / info_const.MAPPING_TABLE_FILE.get(data_type, {}).get(
                source_type, ""
            )
            # File does not exist.
            if not file_path.exists():
                logger.warning(message.get_log_message(message.W00007, [file_path]))
                # This function is called from info api router lifespan,
                # so set the message in args instead of additional_message
                raise InternalHWControlError(
                    f"The definition file corresponding to the received data is not found: {file_path}"
                )

            # Read file.
            with open(file_path, encoding="utf-8") as mapping_file:
                mapping_table = json.load(mapping_file)
                # Convert string data type in JSON to python data type.
                mapping_table = parse_json_value(mapping_table)
                info_const.MAPPING_TABLE[data_type][source_type] = mapping_table


def parse_json_value(mapping_data: dict | list) -> dict | list:
    """Convert json data

    Convert json data to python data.

    Args:
        mapping_data (dict | list: mapping data

    Returns:
        dict | list: Source data after conversion
    """
    # Dictionary type.
    if not isinstance(mapping_data, dict):
        return mapping_data

    # Find the target key.
    for key, val in mapping_data.items():
        # Data type conversion target.
        if key in info_const.STRING_DATA_TYPE_TARGETS:
            # Multiple data types.
            if isinstance(val, list):
                # Multiple data conversions.
                mapping_data[key] = tuple(info_const.TYPE_STRING_CONVERT_MAP[v] for v in val)
            # Single data type.
            else:
                # Extracts and sets the data type that corresponds to the string data type.
                actual_type = info_const.TYPE_STRING_CONVERT_MAP.get(val, None)
                if actual_type:
                    mapping_data[key] = actual_type
        # Item-specific conversion function.
        elif key == info_const.MAPPING_ITEM_CONVERT_FUNC and hasattr(info_conv_funcs, val):
            # Converts so that it can be identified as a Python function.
            mapping_data[key] = getattr(info_conv_funcs, val)
        else:
            parse_json_value(val)

    # Returns anything else as is.
    return mapping_data


def get_valid_string(val: Any) -> str | None:
    """Get valid string value

    Check if the argument is a valid string value, and if it is, return the string value.

    Args:
        val (Any): item value

    Returns:
        str | None: valid string value or None
    """
    # Check if 'val' is an instance of str; return False if 'val' is None
    if isinstance(val, str) and val.strip() != "":
        return val

    return None


def get_high_priority_device_type(device_type_1: str, device_type_2: str | None) -> str:
    """Get higher priority Device Type

    Determines and returns the Device Type with higher priority based on predefined priority levels.

    Args:
        device_type_1 (str): The first Device Type to compare.
        device_type_2 (str | None): The second Device Type to compare, can be None.

    Returns:
        str: The Device Type with higher priority. Returns device_type_1 if it has equal or higher priority,
             otherwise returns device_type_2.

    Priority Levels:
        - "CPU": 255
        - "sourceFabricAdapter": 200
        - "destinationFabricAdapter": 150
        - "Memory": 100
        - "Storage": 80
        - "NetworkInterface": 60
        - "GPU": 40
        - "other": 0

    Examples:
        >>> get_high_priority_device_type("networkInterface", "sourceFabricAdapter")
        'sourceFabricAdapter'
        >>> get_high_priority_device_type("networkInterface", None)
        'networkInterface'
    """
    priority = {
        "cpu": 255,
        "sourcefabricadapter": 200,
        "destinationfabricadapter": 150,
        "memory": 100,
        "storage": 80,
        "networkinterface": 60,
        "gpu": 40,
        "other": 0,
    }

    if not device_type_2:
        return device_type_1

    s_priority = priority.get(device_type_1.lower(), 0)
    t_priority = priority.get(device_type_2.lower(), 0)

    return device_type_1 if s_priority >= t_priority else device_type_2


def get_combination_match_device(device_id: str) -> tuple[str | None, str | None]:
    """Get Device ID and Device Type for device that combination data match

    Retrieve the combination match Device ID and Device Type based on the given Device ID.

    Args:
        device_id (str): Device ID for which to find the matching information.

    Returns:
        tuple[str | None, str | None]: A tuple containing:
            - The target Device ID (or None if not found)
            - The target Device Type (or None if not found)
    """
    port_type = dim.device_id_to_switch_port_type(device_id)

    target_id = dim.get_device_id_of_switch_port_type(
        device_id, const.SwitchPortType.DSP if port_type == const.SwitchPortType.USP.value else const.SwitchPortType.USP
    )
    if target_id:
        # Return the information once the combination device is obtained.
        return target_id, dim.device_id_to_device_type(target_id)

    if port_type:
        target_id = dim.get_device_id_of_switch_port_type(device_id, None)
        if target_id:
            # Return the information once the combination device is obtained.
            return target_id, dim.device_id_to_device_type(target_id)

    # Return None if a combination device is not found.
    return None, None


def get_merge_type(device_type_1: str, device_type_2: str | None) -> int:
    """Get merge type

    Determines the merge type between two device types.

    Args:
        device_type_1 (str): The first device type to compare.
        device_type_2 (str | None): The second device type to compare, can be None.

    Returns:
        int:
            0 if the first device type has higher priority
            1 if the second device type has higher priority
    """
    if get_high_priority_device_type(device_type_1, device_type_2) == device_type_1:
        return 0

    return 1


def merge_dict(source: dict, target: dict, duplicate_key_action: int) -> dict:
    """
    Recursively merges two dictionaries with configurable handling of duplicate keys.

    Args:
        source (dict): The dictionary to which values will be merged
        target (dict): The dictionary containing values to merge into source
        duplicate_key_action (int): Action to take when duplicate keys are found:
            - 0 (default): Keep the original value from source
            - 1: Overwrite with the value from target

    Returns:
        dict (dict): Dict data after merge
    """

    def _is_empty(val):
        """Return True if val is None or an empty string."""
        return val is None or (isinstance(val, str) and val.strip() == "")

    for key in target:
        if key not in source or _is_empty(source[key]):
            source[key] = target[key]
        elif isinstance(target[key], dict):
            merge_dict(source[key], target[key], duplicate_key_action)
        elif isinstance(target[key], list):
            merge_lists(source[key], target[key])
        elif duplicate_key_action == 1 and not _is_empty(target[key]):
            source[key] = target[key]
    return source


def merge_lists(list1, list2):
    """
    Combine two lists and overwrite duplicate elements with the last element.

    Args:
        list1: The first list
        list2: The second list

    Returns:
        The combined list (duplicate elements are merged.
    """
    for item in list2:
        if item not in list1:
            list1.append(item)

    return list1

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
make an information acquisition request for the specified device ID to FM and OOB.
Merge the device information returned from FM and OOB for each device
type and return it to the information acquisition API.

"""

import json
from typing import List, Dict, Optional, Union, Any
from pathlib import Path
from app.common.utils.log import LOGGER
from app.common.messages import message
from app.common.basic_exceptions import InternalHwControlError
from app.common.settings import settings
from app.core.info import info_const, info_conv_funcs


def get_mapping_table(device_type: str, data_type: str, data_source_type: str) -> dict:
    """Get mapping table

    Return the mapping table that corresponds to the device type and data source and data type.

    Args:
        device_type (str): device type
        data_type (str): data type
        data_source_type (str): data source type

    Returns:
        dict: mapping table
    """
    # Extract the mapping table corresponding to the device type.
    mapping_table = info_const.MAPPING_TABLE[data_type][data_source_type].get(device_type, None)

    return mapping_table


def remove_empty_item(resp: Any) -> Any:
    """Remove empty item

    Remove empty items from response data and ret

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


def create_resp_from_mapping(mapping_table: dict, source_data: dict) -> dict:
    """Create response data from mapping table

    Create response data from source data according to mapping table.

    Args:
        mapping_table (dict): mapping table
        source_data (dict): source data

    Returns:
        dict: response data
    """
    response_data = {}

    # Loops while extracting the destination key and its mapping information.
    for dest_key, mapping_data in mapping_table.items():

        # Source key name. (If no key name is specified, the same key name is used)
        key = mapping_data.get(info_const.MAPPING_ITEM_KEY, dest_key)

        # If a path is specified (different hierarchy to migrate to),
        if info_const.MAPPING_ITEM_PATH in mapping_data:
            parts = mapping_data[info_const.MAPPING_ITEM_PATH].split(".")
            temp_data = source_data
            # Extract the path value.
            for part in parts:
                temp_data = temp_data.get(part, {})
            value = temp_data
        else:
            # Extract data for the source key.
            value = source_data.get(key, None)

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


def _check_required_item(mapping_data, key, item_value):
    """Check required item

    Check for the presence of values in required item based on the mapping data.

    Args:
        mapping_data (dict): mapping data
        key (str): item key
        item_value (Any): item value

    Returns:
        None
    """
    if (
        mapping_data.get(info_const.MAPPING_ITEM_REQUIRED, False)
        and item_value is None
        or (isinstance(item_value, str) and item_value.strip() == "")
    ):
        LOGGER.warning(message.get_log_message(message.W00008, [f"key:{key}"]))
        raise InternalHwControlError(additional_message="The received data is missing required item.")


def _check_list_item_types(mapping_data, key, item_value):
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
                LOGGER.warning(
                    message.get_log_message(
                        message.W00009,
                        [f"Key:{key}, Value:{item}, Value type:{type(item).__name__}, Target type:{target_type_name}"],
                    )
                )
                raise InternalHwControlError(additional_message="The data type of the received item is invalid.")


def _check_item_type(mapping_data, key, item_value):
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
            LOGGER.warning(
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
            raise InternalHwControlError(additional_message="The data type of the received item is invalid.")


def _execute_if_callable(mapping_data, key, item_value) -> Any:
    """Execute function if callable

    Check if the conversion function is callable and return the execution result.

    Args:
        mapping_data (dict): mapping data
        key (str): item key
        item_value (Any): item value

    Returns:
        Any: item value
    """
    if info_const.MAPPING_ITEM_CONVERT_FUNC in mapping_data:
        if callable(mapping_data[info_const.MAPPING_ITEM_CONVERT_FUNC]):
            return mapping_data[info_const.MAPPING_ITEM_CONVERT_FUNC](mapping_data, key, item_value)
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
            if not Path.exists(file_path):
                LOGGER.warning(message.get_log_message(message.W00007, [file_path]))
                raise InternalHwControlError(
                    additional_message="The definition file corresponding to the received data is not found."
                )

            # Read file.
            with open(file_path, "r", encoding="utf-8") as mapping_file:
                mapping_table = json.load(mapping_file)
                # Convert string data type in JSON to python data type.
                mapping_table = parse_json_value(mapping_table)
                info_const.MAPPING_TABLE[data_type][source_type] = mapping_table


def parse_json_value(mapping_data: Union[Dict, List]) -> Union[Dict, List]:
    """Convert json data

    Convert json data to python data.

    Args:
        mapping_data (Union[Dict, List]): mapping data

    Returns:
        Union[Dict, List]: Source data after conversion
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


def get_valid_string(val: Any) -> Optional[str]:
    """Get valid string value

    Check if the argument is a valid string value, and if it is, return the string value.

    Args:
        val (Any): item value

    Returns:
        Optional[str]: valid string value or None
    """
    # Check if 'val' is an instance of str; return False if 'val' is None
    if isinstance(val, str) and val.strip() != "":
        return val

    return None

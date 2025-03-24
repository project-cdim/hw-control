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

import re
from typing import Any


def get_socket_number(mapping_data: dict, key: str, item_value: str) -> Any:  # pylint: disable=W0613
    """Get socket number

    Get Socket number from Socket string.

    Args:
        mapping_data (dict): mapping data
        key (str): item key
        item_value (str): item value

    Returns:
        Any: socket number or None
    """
    # Regular expression.
    pattern = r"CPU (\d+)"

    # Matching.
    match = re.match(pattern, item_value)

    # If it matches, convert it to a number and return it, otherwise return None.
    return int(match.group(1)) if match else None


def duration_to_seconds(mapping_data: dict, key: str, item_value: str) -> Any:  # pylint: disable=W0613
    """Convert duration to seconds

    Convert duration(PnDTnHnMnS) to seconds.

    Args:
        mapping_data (dict): mapping data
        key (str): item key
        item_value (str): item value

    Returns:
        Any: seconds(float) or None
    """

    # Regular expression for period format. (PnDTnHnMnS)
    pattern = re.compile(r"^P(\d+D)?(T(\d+H)?(\d+M)?(\d+(.\d+)?S)?)?$")  # NOSONAR

    # Is the input date string matching the regular expression?
    match = pattern.match(item_value)
    if not match:
        return None

    # Extracts date, time, minutes, and seconds. (non-existent items are set to 0)
    # All are converted to floats for rounding to integers later.
    matches = match.groups()
    days = float(matches[0][:-1]) if matches[0] else 0
    hours = float(matches[2][:-1]) if matches[2] else 0
    minutes = float(matches[3][:-1]) if matches[3] else 0
    seconds = float(matches[4][:-1]) if matches[4] else 0

    # Total value.
    total_seconds = (days * 24 * 60 * 60) + (hours * 60 * 60) + (minutes * 60) + seconds
    # If the decimal point is 0, it is returned as an integer.
    return int(total_seconds) if isinstance(total_seconds, float) and total_seconds.is_integer() else total_seconds

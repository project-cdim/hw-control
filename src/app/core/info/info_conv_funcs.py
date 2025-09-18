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
make an information acquisition request for the specified Device ID to FM and OOB.
Merge the device information returned from FM and OOB for each device
type and return it to the information acquisition API.

"""

import re
from typing import Any


def get_socket_number(mapping_data: dict, key: str, item_value: str) -> Any:  # pylint: disable=W0613
    """Get socket number

    Get socket number from socket string.

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


def _parse_days(date_part: str) -> int | None:
    """
    Parses a string representing a number of days and returns it as a float.

    Args:
        date_part (str): A string expected to be in the format "<number>D",
            where <number> is a float or integer representing days.

    Returns:
        int | None: The number of days as a int if parsing is successful.
            Returns 0 if the input is empty or None if the format is invalid.
    """

    if not date_part:
        return 0

    if "D" in date_part:
        try:
            days_str = date_part.split("D")[0]
            # If there are extra characters other than "D"
            if len(date_part) != len(days_str) + 1:
                return None
            days = int(days_str)
            # If a negative value is specified for day, it is considered invalid.
            if days < 0:
                return None
            return days
        except ValueError:
            return None
    return None


def _parse_time(time_part: str) -> tuple[int, int, float] | None:
    """
    Parses a time string in the format "[<hours>H][<minutes>M][<seconds>S]"
    and returns a tuple of (hours, minutes, seconds).

    Args:
        time_part (str): The time string to parse, e.g., "1H30M15S", "45M", or "20.5S".

    Returns:
        tuple[int, int, float] | None: A tuple containing hours, minutes, and seconds as floats
        if parsing is successful; otherwise, None if the input is invalid.
    """

    hours = minutes = 0
    seconds = 0.0

    if not time_part:
        return hours, minutes, seconds

    rest = time_part
    try:
        if "H" in rest:
            hours_str, _, rest = rest.partition("H")
            hours = int(hours_str)
        if "M" in rest:
            minutes_str, _, rest = rest.partition("M")
            minutes = int(minutes_str)
        if "S" in rest:
            seconds_str, _, rest = rest.partition("S")
            seconds = float(seconds_str)
        # If extra characters remain, or if a negative value is specified for time, it is considered invalid.
        if rest or hours < 0 or minutes < 0 or seconds < 0:
            return None
        return hours, minutes, seconds
    except ValueError:
        return None


def duration_to_seconds(mapping_data: dict, key: str, item_value: str) -> Any:  # pylint: disable=W0613
    """
    Converts an ISO 8601 duration string (format: PnDTnHnMnS) to the total number of seconds.

    Args:
        mapping_data (dict): Unused parameter, present for interface compatibility.
        key (str): Unused parameter, present for interface compatibility.
        item_value (str): The duration string to convert (e.g., 'P2DT3H4M5.5S').

    Returns:
        Any: The total duration in seconds as an integer if whole,
             or float if fractional seconds are present.
             Returns None if the input is invalid or cannot be parsed.

    Notes:
        - Only supports durations with days, hours, minutes, and seconds (e.g., 'P2DT3H4M5.5S').
        - Does not support months or years.
        - Does not use regular expressions for parsing.
    """

    if not isinstance(item_value, str) or not item_value.startswith("P"):
        return None

    # Separate date and time
    date_time_str = item_value[1:]
    if "T" in date_time_str:
        date_part, time_part = date_time_str.split("T", 1)
    else:
        date_part, time_part = date_time_str, ""

    # Invalid if both date and time are not specified.
    if not date_part and not time_part:
        return None

    days = _parse_days(date_part)
    if days is None:
        return None

    time_result = _parse_time(time_part)
    if time_result is None:
        return None
    hours, minutes, seconds = time_result

    # Total value.
    total_seconds = (days * 24 * 60 * 60) + (hours * 60 * 60) + (minutes * 60) + seconds
    # If the decimal point is 0, it is returned as an integer.
    return int(total_seconds) if isinstance(total_seconds, float) and total_seconds.is_integer() else total_seconds

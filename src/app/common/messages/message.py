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

"""Defines the message to be included in the application log."""

import app.common.basic_exceptions as exc

LOG_MESSAGES = {
    "I00001": "I00001: {0[0]} API Start {0[1]}",
    "I00002": "I00002: {0[0]} API Respond {0[1]}",
    "I00003": "I00003: {0[0]} Plugin Call. ",
    "I00004": "I00004: {0[0]} Plugin Respond. ",
    "I00005": "I00005: {0[0]} Agent Call. ",
    "I00006": "I00006: {0[0]} Agent Respond. ",
    "I00007": "I00007: {0[0]} Skipping connection to the Agent. {0[1]}",
    "W00001": "W00001: Unexpected Exception: {0[0]}",
    "W00002": "W00002: Unexpected DeviceType: {0[0]}",
    "W00003": "W00003: Failed to Get Plugin Instance: {0[0]}",
    "W00004": "W00004: Plugin Response Contains Invalid Type: {0[0]}]",
    "W00005": "W00005: Plugin Response Unexpected None:",
    "W00006": "W00006: Device information not found: {0[0]}",
    "W00007": "W00007: File does not exist: {0[0]}",
    "W00008": "W00008: Required item does not exist: {0[0]}",
    "W00009": "W00009: Invalid type value: {0[0]}",
    "W00010": "W00010: Power Operation Error: {0[0]}",
    "W00011": "W00011: Not Power Operation Device: {0[0]}",
    "W00012": "W00012: Failed to get OOB Response: {0[0]}",
    "W00013": "W00013: Failed to connect Agent: {0[0]}",
    "W00014": "W00014: Failed to get Agent Response: {0[0]}",
    "E00001": "E00001: Unexpected Exception: {0[0]}",
    "E00002": "E00002: Unexpected DeviceType: {0[0]}",
    "E00003": "E00003: Device information not found: {0[0]}",
    "E00004": "E00004: Power Operation Error: {0[0]}",
    "E00005": "E00005: Not Power Operation Device: {0[0]}",
    "E00006": "E00006: Failed to get OOB Response: {0[0]}",
}

I00001 = "I00001"
"""I00001: {0[0]} API Start {0[1]}"""
I00002 = "I00002"
"""I00002: {0[0]} API Respond {0[1]}"""
I00003 = "I00003"
"""I00003: {0[0]} Plugin Call. """
I00004 = "I00004"
"""I00004: {0[0]} Plugin Respond. """
I00005 = "I00005"
"""I00005: {0[0]} Agent Call. """
I00006 = "I00006"
"""I00006: {0[0]} Agent Respond. """
I00007 = "I00007"
"""I00007: {0[0]} Skipping connection to the Agent. {0[1]}"""
W00001 = "W00001"
"""W00001: Unexpected Exception: {0[0]}"""
W00002 = "W00002"
"""W00002: Unexpected DeviceType: {0[0]}"""
W00003 = "W00003"
"""W00003: Failed to Get Plugin Instance: {0[0]}"""
W00004 = "W00004"
"""W00004: Plugin Response Contains Invalid Type: {0[0]}]"""
W00005 = "W00005"
"""W00005: Plugin Response Unexpected None:"""
W00006 = "W00006"
"""W00006: Device information not found: {0[0]}"""
W00007 = "W00007"
"""W00007: File does not exist: {0[0]}"""
W00008 = "W00008"
"""W00008: Required item does not exist: {0[0]}"""
W00009 = "W00009"
"""W00009: Invalid type value: {0[0]}"""
W00010 = "W00010"
"""W00010: Power Operation Error: {0[0]}"""
W00011 = "W00011"
"""W00011: Not Power Operation Device: {0[0]}"""
W00012 = "W00012"
"""W00012: Failed to get OOB Response: {0[0]}"""
W00013 = "W00013"
"""W00013: Failed to connect Agent: {0[0]}"""
W00014 = "W00014"
"""W00014: Failed to get Agent Response: {0[0]}"""
E00001 = "E00001"
"""E00001: Unexpected Exception: {0[0]}"""
E00002 = "E00002"
"""E00002: Unexpected DeviceType: {0[0]}"""
E00003 = "E00003"
"""E00003: Device information not found: {0[0]}"""
E00004 = "E00004"
"""E00004: Power Operation Error: {0[0]}"""
E00005 = "E00005"
"""E00005: Not Power Operation Device: {0[0]}"""
E00006 = "E00006"
"""E00006: Failed to get OOB Response: {0[0]}"""


def get_log_message(message_code: str, param_list: list):
    """get log message"""
    try:
        return LOG_MESSAGES[message_code].format(param_list)
    except Exception as error:  # pylint: disable=W0718
        raise exc.InvalidLogMessageParameterHWControlError from error

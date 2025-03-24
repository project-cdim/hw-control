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

"""This is a test program."""

import app.core.info.info_utils as info_utils

# Input dict
# Full-width spaces are essential items.
INPUT_DICT = {
    "deviceID": "1001",
    "type": "memory",
    "schema": {
        "CapacityMiB": 1073741824,
        "LogicalSizeMiB": "　",
        "NonVolatileSizeMiB": "",
        "PersistentRegionNumberLimit": None,
        "AllowedSpeedsMHz": [],
        "Enabled": True,
    },
}

# Output dict (after remove)
OUTPUT_DICT = {
    "deviceID": "1001",
    "type": "memory",
    "schema": {
        "CapacityMiB": 1073741824,
        "Enabled": True,
    },
}


def test_remove_empty_item_dict():
    """Test remove empty item dictionary"""
    assert OUTPUT_DICT == info_utils.remove_empty_item(INPUT_DICT)

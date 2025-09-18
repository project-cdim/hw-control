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

import os
import logging
import pytest
from app.common.settings import settings
from app.common.basic_exceptions import InternalHWControlError
from app.core.info.info_utils import load_mapping_table


# Mapping table file
MAPPING_TABLE_FILE1 = {
    "fm": {"spec": "test_info_core_fm_spec_mapping.json"},
    "oob": {"spec": "test_info_core_oob_spec_mapping.json"},
    "agent": {"metric": "test_info_core_agent_metric_mapping.json"},
}

MAPPING_TABLE_FILE2 = {"agent": {"metric": "test_info_core_test_mapping.json"}}


def _log_contains(record, level, message) -> bool:
    """Comparing log contents"""
    return next(filter(lambda x: (x[1] == level) and (message in x[2]), record), None) is not None


def test_load_mapping_table_not_exist_mapping_file(mocker, caplog):
    """Test Get Information not exist mapping table file"""
    # Current path
    current_path = os.path.dirname(os.path.abspath(__file__))

    # Replace the path of the mapping table file (constant) with the test mapping table file path.
    mapping_path = current_path
    mocker.patch.object(settings, "MAPPING_TABLE_PATH", mapping_path)

    test_mapping_file = {"fm": {"spec": "fm_spec_test.json"}, "oob": {"spec": "oob_spec_test.json"}}
    # Replace the mapping table file (constants) with the test mapping table file.
    mocker.patch.dict("app.core.info.info_const.MAPPING_TABLE_FILE", test_mapping_file)

    # Exception
    with pytest.raises(InternalHWControlError):
        load_mapping_table()
    assert _log_contains(caplog.record_tuples, logging.WARNING, "W00007: File does not exist: ")

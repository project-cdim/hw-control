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

"""Define fixture for logging tests."""

import os

import pytest
import yaml


@pytest.fixture
def default_logging_config():
    """Load default logging config from config/logging_config.yaml

    Returns:
        dict: logging config dict from config/logging_config.yaml
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
    config_path = os.path.join(project_root, "config", "logging_config.yaml")
    with open(config_path, encoding="utf-8") as f:
        # Load the logging configuration from config file.
        config = yaml.safe_load(f)

    return config

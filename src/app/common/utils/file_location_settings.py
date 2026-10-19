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

"""Module for managing configuration settings for a file location.

This module provides a class, `FileLocationSettings`, which fetches
configuration settings from environment variables and validates them.
These settings can be used to get file location.

"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FileLocationSettings(BaseSettings):
    """Configuration settings for interacting with a file location.

    This class retrieves configuration settings from environment variables
    for file location, and stores them as instance variables.

    Attributes:
        config_file_dir (str):
            The base directory relative to which the configuration files are located.
            Default to "/opt/cdim/hw-control/config/".

        data_file_dir (str):
            The base directory relative to which the data files are located.
            Default to "/opt/cdim/hw-control/data/".

        plugin_file_dir (str):
            The base directory relative to which the plugin configuration
            files are located.
            Default to "/opt/cdim/hw-control/data/plugins".

    Example:
        To customize settings via environment variables, you can set them as follows:

        ```
        export HW_CONTROL_CONFIG_FILE_DIR="/opt/cdim/hw-control/config/"
        export HW_CONTROL_DATA_FILE_DIR="/opt/cdim/hw-control/data/"
        export HW_CONTROL_PLUGIN_FILE_DIR="/opt/cdim/hw-control/data/plugins"
        ```

        These environment variables will be automatically picked up and override the default settings.

        To use this class, you can create an instance of it like this:

        >>> settings = FileLocationSettings()
        >>> print(settings.config_file_dir)
        "/opt/cdim/hw-control/config/"

    """

    config_file_dir: str = Field(
        default="/opt/cdim/hw-control/config/",
        alias="HW_CONTROL_CONFIG_FILE_DIR",
        description="The base directory relative to which the configuration files are located.",
    )

    data_file_dir: str = Field(
        default="/opt/cdim/hw-control/data/",
        alias="HW_CONTROL_DATA_FILE_DIR",
        description="The base directory relative to which the data files are located.",
    )

    plugin_file_dir: str = Field(
        default="/opt/cdim/hw-control/data/plugins",
        alias="HW_CONTROL_PLUGIN_FILE_DIR",
        description="The base directory relative to which the plugin configuration files are located.",
    )

    model_config = SettingsConfigDict(case_sensitive=True)

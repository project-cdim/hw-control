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

"""Define logging runtime settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingSettings(BaseSettings):
    """Logging runtime settings from environment variables.

    This class provides settings that cannot be configured via logging system configuration files
    (such as dict_config or file_config).
    For example, whether to propagate exceptions that occur during log message processing.
    It is recommended to set this to True during development and False during production.
    Therefore, it should be configurable at application startup.

    To configure this, the logging.raiseExceptions flag must be set, which cannot be set via dict_config or file_config.
    Thus, it needs to be set separately using environment variables.
    """

    logging_raise_exceptions: bool = Field(
        default=False,
        alias="HW_CONTROL_LOGGING_RAISE_EXCEPTIONS",
    )

    model_config = SettingsConfigDict(case_sensitive=True)

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

"""HW control function - system environment definition"""

from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """System Preferences

    Set constants used in the system from environment variables.

    """

    MAPPING_TABLE_PATH: str = Field(
        default=str((Path(__file__).parent.parent / "mapping").resolve()),
        alias="HW_CONTROL_MAPPING_TABLE_PATH",
        description="Directory for placing the mapping data file used in response generation.",
    )

    HW_CONTROL_AGENT_ENABLED: bool = Field(
        default=False,
        description="Operation status of Hardware Control Agent",
    )


@lru_cache
def get_settings() -> Settings:
    """Get device information

    Get system environment definition information.

    Returns:
        Settings: system definition information
    """
    return Settings()


settings = get_settings()

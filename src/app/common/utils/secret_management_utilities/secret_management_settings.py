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

"""
Module for managing configuration settings for a Secret Management service.

This module provides a class, `SecretManagementSettings`, which fetches
configuration settings from environment variables and validates them.
These settings can be used to facilitate requests to a Secret Management service.

"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecretManagementSettings(BaseSettings):
    """
    Configuration settings for interacting with a Secret Management service.

    This class retrieves configuration settings from environment variables
    for making requests to a secret management service,
    and stores them as instance variables.

    Attributes:
        host (str):
            The host address of the Secret Management service.
            Default to "localhost".

        port (int):
            The port number on which the Secret Management service is running.
            Must be greater than 0 and less than 65535.
            Default to 3500.

        path (str):
            The API base path for accessing secrets.
            Default to "/v1.0/secrets/".

        timeout (int):
            The timeout duration (in seconds) for requests to the secret service.
            Must be greater than 1 and less than 10.
            Default to "/v1.0/secrets/".

    Raises:
        pydantic.ValidationError:
            If the settings retrieved from the environment variables do not meet validation criteria,
            such as the range constraints for `timeout`.

    Example:
        To customize settings via environment variables, you can set them as follows:

        ```
        export HW_CONTROL_SECRET_API_HOST="example.com"
        export HW_CONTROL_SECRET_API_PORT=8080
        export HW_CONTROL_SECRET_API_PATH="/secrets"
        export HW_CONTROL_SECRET_API_TIMEOUT=5
        ```

        These environment variables will be automatically picked up and override the default settings.

        To use this class, you can create an instance of it like this:

        >>> settings = SecretManagementSettings()
        >>> print(settings.host)
        "example.com"
    """

    host: str = Field(
        default="localhost",
        alias="HW_CONTROL_SECRET_API_HOST",
        description="The Secret API host.",
    )

    port: int = Field(
        default=3500,
        alias="HW_CONTROL_SECRET_API_PORT",
        description="The Secret API port.",
        gt=0,
        lt=65535,
    )

    path: str = Field(
        default="/v1.0/secrets/",
        alias="HW_CONTROL_SECRET_API_PATH",
        description="The Secret API base path.",
    )

    timeout: int = Field(
        default=3,
        alias="HW_CONTROL_SECRET_API_TIMEOUT",
        description="The timeout duration (in seconds) for secret requests to the Secret API.",
        gt=1,
        lt=10,
    )

    model_config = SettingsConfigDict(case_sensitive=True)

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

"""
Module for configure settings for request to the Authorization Server.

This module provides a class, `AuthorizationServerSettings`, which fetches 
configuration settings from environment variables and validates them. 
These settings can be used to facilitate requests to the Authorization Server.

"""
from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.common.messages import message


class AuthorizationServerSettingsLog(message.BaseLogMessage):
    """Log Message Model class for setting environment variables for request to The Authorization Server."""

    action: str = Field(
        default="Get Authorization Server settings form environment variables.",
    )

    token_endpoint: HttpUrl | None = Field(
        default=None,
        description="The value of the obtained environment variable `HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT`.",
    )

    timeout: int | None = Field(
        default=None, description="The value of the environment variable `HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT`."
    )


class AuthorizationServerSettings(BaseSettings):
    """
    Configuration settings for interacting with the Authorization Server

    This class retrieves configuration settings from environment variables
    for making requests to the Authorization Server,
    and stores them as instance variables.

    Attributes:
        token_url (pydantic.HttpUrl):
            The access token endpoint url of the Authorization Server.

        timeout (int):
            The timeout duration (in seconds) for access token requests to the Authorization Server.
            Must be greater than 1 and less than 10.
            Default to 3.

    Raises:
        pydantic.ValidationError:
            If the settings retrieved from the environment variables do not meet validation criteria,
            such as the range constraints for `timeout`.

    Example:
        To customize settings via environment variables, you can set them as follows:

        ```
        export HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT= \
        "https://localhost:8443/realms/foo_realm/protocol/openid-connect/token"
        export HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT=5
        ```

        These environment variables will be automatically picked up and override the default settings.

        To use this class, you can create an instance of it like this:

        >>> settings = AuthorizationServerSettings()
        >>> print(settings.timeout)
        5
    """

    token_endpoint: HttpUrl = Field(
        alias="HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT",
        title="The access token endpoint",
        description="The access token endpoint url of the Authorization Server.",
        examples=["https://localhost:8443/realms/foo_realm/protocol/openid-connect/token"],
    )
    timeout: int = Field(
        default=3,
        alias="HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT",
        title="The timeout value for access token request",
        description="The timeout duration (in seconds) for access token requests to the Authorization Server.",
        gt=1,
        lt=10,
    )

    model_config = SettingsConfigDict(case_sensitive=True)

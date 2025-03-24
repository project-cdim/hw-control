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
A module for handling authorization operations.
"""

from http import HTTPStatus

from pydantic import BaseModel, ValidationError, Field
import requests

import app.common.basic_exceptions as exc
from app.common.utils.log import LOGGER
from app.common.messages import message
from app.common.utils.secret_management_utilities import secret_management_client
from app.common.utils.authorization_utilities import authorization_server_settings

CLIENT_SECRET_NAME = "Keycloak"


class ClientCredential(BaseModel):
    """
    Validate client credentials for HW Control.

    This model is responsible for validating the client ID and client secret
    retrieved from a secret API.

    Attributes:
        client_id (str): The client identifier for HW Control.
        client_secret (str): The client secret for HW Control.

    Raises:
        ValueError:
            If the field value is empty or not of type string.
    """

    client_id: str = Field(description="client id of HW Control")

    client_secret: str = Field(description="client secret of HW Control")


class AuthorizationServerRequestLog(message.BaseLogMessage):
    """Log Message Model class for logging request to The Authorization Server."""

    action: str = Field(
        default="Request to the Authorization Server.",
    )
    url: str | None = Field(default=None, description="The URL to which the HTTP request was sent.")
    timeout: int | None = Field(default=None, description="The timeout value for the HTTP request.")


class AuthorizationServerResponseLog(message.BaseLogMessage):
    """Log Message Model class for logging response from The Authorization Server."""

    action: str = Field(
        default="Receive the Authorization Server response.",
    )
    status_code: int | None = Field(
        default=None, description="The HTTP status code returned from the Authorization Server."
    )


def get_agent_access_token() -> str:
    """Fetches an access token from the Authorization Server.

    This function is used to obtain an access token from the Authorization
    Server, which is required for making authorized requests to an agent.

    The access token is used in authorization processes when communicating
    with various services that require secure access.

    Args: None

    Returns:
        str: An access token as a string, which is used for the authorization
        of requests to the agent.

    Raises:
        AuthenticationHwControlError:
            If the authentication of the client to the Authorization Server fails.

        InternalHwControlError:
            If there are issues during the authorization retrieval process, such as connection errors.

        ConfigurationHwControlError:
            If there are configuration errors with environment variables related to the Authorization Server.

        DependencyServiceHwControlError
            If there are unexpected issues in the Authorization Server.

    Example:
        To use the access token in a request header, you might do the following:

        >>> headers = {
            "Authorization": f"Bearer {get_agent_access_token()}"
            }
        # Use headers in your HTTP requests to the agent

    """

    secret = secret_management_client.get_secret(
        secret_store=secret_management_client.SecretStore.AGENT, secret_name=CLIENT_SECRET_NAME
    )

    try:
        client_credential = ClientCredential(**secret)
    except ValidationError as e:
        raise exc.InternalHwControlError(
            additional_message="The client credentials retrieved from secret management are invalid."
        ) from e

    try:
        setting = authorization_server_settings.AuthorizationServerSettings()  # type: ignore
    except ValidationError as e:
        raise exc.ConfigurationHwControlError(
            additional_message=(
                "There is an issue with the configuration of the environment variables related"
                " to the Authorization Server."
            )
        ) from e

    LOGGER.info(
        authorization_server_settings.AuthorizationServerSettingsLog(**setting.model_dump()).to_json_encodable()
    )

    token_request_body = {
        "grant_type": "client_credentials",
        "client_id": client_credential.client_id,
        "client_secret": client_credential.client_secret,
    }

    token_request_headers = {"Content-Type": "application/x-www-form-urlencoded"}

    LOGGER.info(
        AuthorizationServerRequestLog(url=str(setting.token_endpoint), timeout=setting.timeout).to_json_encodable()
    )

    try:
        auth_server_response = requests.post(
            url=str(setting.token_endpoint),
            timeout=setting.timeout,
            data=token_request_body,
            headers=token_request_headers,
        )

    except requests.exceptions.RequestException as e:
        raise exc.InternalHwControlError(
            additional_message="The access token request to the Authorization Server failed due to an unexpected error."
        ) from e

    LOGGER.info(AuthorizationServerResponseLog(status_code=auth_server_response.status_code).to_json_encodable())

    if auth_server_response.status_code in (HTTPStatus.BAD_REQUEST.value, HTTPStatus.UNAUTHORIZED.value):
        response_body = auth_server_response.json()

        auth_server_error_code = response_body.get("error")

        if auth_server_error_code in ("invalid_client", "unauthorized_client"):
            raise exc.AuthenticationHwControlError(
                f"error code: {auth_server_error_code}",
                additional_message="Failed to authenticate to the Authorization Server.",
            )
        raise exc.InternalHwControlError(
            f"error code: {auth_server_error_code}",
            additional_message="Failed to get access token due to an unexpected error.",
        )

    if auth_server_response.status_code != HTTPStatus.OK.value:
        raise exc.DependencyServiceHwControlError(
            additional_message="An unexpected error was returned by the Authorization Server."
        )

    # HTTPStatus = 200 OK case
    try:
        response_body = auth_server_response.json()
        access_token = response_body["access_token"]
    except (
        requests.exceptions.JSONDecodeError,
        KeyError,
    ) as e:  # The Authorization Server return invalid response.
        raise exc.InternalHwControlError(additional_message="The Authorization Server return invalid data.")

    return access_token

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
A module for handling secret management operations.
"""

import logging
from enum import Enum
from http import HTTPStatus
from http import HTTPMethod

from pydantic import validate_call, ValidationError
import requests
from urllib3.util import Url

from app.common.utils.secret_management_utilities import secret_management_settings
import app.common.basic_exceptions as exc

logger = logging.getLogger(__name__)


class SecretStore(Enum):
    """
    An enumeration representing different secret stores.

    This Enum class defines the possible secret store names that can be used
    when interacting with the secret management service. It is utilized for
    type checking of function arguments that require a defined set of secret store names.

    Attributes:
        FM: Represents the secret store named "cdim-hw-control-fm".
        OOB: Represents the secret store named "cdim-hw-control-oob".
        AGENT: Represents the secret store named "cdim-hw-control-agent".
    """

    FM = "cdim-hw-control-fm"
    OOB = "cdim-hw-control-oob"
    AGENT = "cdim-hw-control-agent"


@validate_call
def get_secret(secret_store: SecretStore, secret_name: str) -> dict:
    """
    Retrieve a secret from a specified secret store.

    This function interacts with a secret management service to fetch the
    secret corresponding to the given `secret_name` from the given `secret_store`.

    Args:
        secret_store (SecretStore):
            An enumeration representing the secret store to query.

        secret_name (str):
            The name of the secret to retrieve from the specified secret store.

    Returns:
        dict: A dictionary containing the secret data, such as credentials.

    Raises:
        pydantic.ValidationError:
            If the arguments provided to the function have incorrect types or do not meet validation criteria.
            leveraging `pydantic.validate_call`.

        ValueError:
            If the specified secret is not found in the specified secret store.

        InternalHWControlError:
            If there are issues during the secret retrieval process, such as connection errors.

        ConfigurationHWControlError:
            If there are configuration errors with environment variables related to the secret management.

    Example:
        >>> secret = get_secret(SecretStore.FM, secret_name="foo_secret_name")
        >>> print(secret)
        {"user": "foo_user", "password": "foo_pwd"}

    """
    try:
        setting = secret_management_settings.SecretManagementSettings()
    except ValidationError as e:
        raise exc.ConfigurationHWControlError(
            additional_message=(
                "There is an issue with the configuration of the environment variables related to the secret API."
            )
        ) from e

    logger.info("Get secret API settings form environment variables.", extra={**setting.model_dump()})

    target_url = Url(
        scheme="http",
        host=setting.host,
        port=setting.port,
        path=f"{setting.path}{secret_store.value}/{secret_name}",
    )

    logger.info(
        "Request to secret API",
        extra={
            "secret_store_name": secret_store.value,
            "secret_name": secret_name,
            "ip_address": setting.host,
            "port": setting.port,
            "url": str(target_url),
            "http_method": HTTPMethod.GET,
            "time_out": setting.timeout,
        },
    )

    try:
        secret_manager_return = requests.get(
            url=str(target_url),
            timeout=setting.timeout,
        )

    except requests.exceptions.RequestException as e:
        raise exc.InternalHWControlError(
            additional_message="The secret request to the secret API failed due to an unexpected error."
        ) from e

    # Check response Body.
    try:
        secret_manager_response_body = secret_manager_return.json()
    except requests.exceptions.JSONDecodeError as e:  # Unexpected format response was returned case.
        raise exc.DependencyServiceHWControlError(
            secret_manager_return, additional_message="The secret API return invalid data."
        ) from e

    if secret_manager_return.status_code == HTTPStatus.OK.value:
        logger.info(
            "Get secret from the secret API.",
            extra={"status_code": secret_manager_return.status_code},
        )
        secret = secret_manager_response_body
        logger.debug("obtained secret: %s", {str(secret)})

    else:  # Secret retrieval failure case.
        logger.error(
            "Return error from the secret API.",
            extra={
                "status_code": secret_manager_return.status_code,
                "response_body": secret_manager_response_body,
            },
        )
        raise exc.DependencyServiceHWControlError(additional_message="Failed to get secret due to an unexpected error.")

    return secret

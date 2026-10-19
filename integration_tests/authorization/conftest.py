# Copyright 2026 NEC Corporation
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

"""Fixtures for authorization server tests.

Starts a Keycloak container via testcontainers KeycloakContainer and
provisions the required Realm and Client using the KeycloakAdmin client
provided by the container.
"""

import pytest
from testcontainers.keycloak import KeycloakContainer

_KEYCLOAK_IMAGE = "quay.io/keycloak/keycloak:26.4"
_KEYCLOAK_ADMIN_USERNAME = "admin"
_KEYCLOAK_ADMIN_PASSWORD = "admin"

_CLIENT_ID = "hw-control-client"
_CLIENT_SECRET = "test-secret"

_REALM_NAME = "hw-control"


@pytest.fixture(scope="package")
def keycloak_container():
    """Start a Keycloak container once for the authorization test package.

    Uses KeycloakContainer and waits for the container to become ready via its
    internal wait strategy.  The admin account is fixed to admin/admin.
    """
    container = KeycloakContainer(
        image=_KEYCLOAK_IMAGE, username=_KEYCLOAK_ADMIN_USERNAME, password=_KEYCLOAK_ADMIN_PASSWORD
    )
    with container:
        yield container


@pytest.fixture
def keycloak_realm(keycloak_container: KeycloakContainer):
    """Provide a freshly provisioned hw-control realm for each test function.

    Creates the realm with Keycloak's default signing algorithm.
    Each test can override realm settings via the yielded `realm_admin` client
    (e.g., changing the signing algorithm with `realm_admin.update_realm()`).
    The realm is deleted in teardown regardless of test outcome.

    Yields:
        tuple: A two-element tuple `(realm_admin, realm_settings)`:
            - realm_admin (KeycloakAdmin): Admin client for the provisioned realm.
              Use this to override realm settings (e.g., signing algorithm via
              `realm_admin.update_realm()`).
            - realm_settings (dict): Connection details with the following keys:
                - realm_name (str): Name of the provisioned realm.
                - issuer (str): Issuer URL of the provisioned realm.
                - token_endpoint (str): Token endpoint URL of the provisioned realm.
                - client_id (str): Client ID registered in the realm.
                - client_secret (str): Client secret for the registered client.
    """
    base_url = keycloak_container.get_url()
    realm_path = f"/realms/{_REALM_NAME}"
    realm_issuer = f"{base_url}{realm_path}"
    token_endpoint = f"{base_url}{realm_path}/protocol/openid-connect/token"

    # Setup: create the Realm and Client by default.
    realm_admin = keycloak_container.get_client()
    realm_admin.create_realm({"realm": _REALM_NAME, "enabled": True})
    realm_admin.change_current_realm(_REALM_NAME)
    realm_admin.create_client(
        {
            "clientId": _CLIENT_ID,
            "secret": _CLIENT_SECRET,
            "enabled": True,
            "serviceAccountsEnabled": True,  # required for the client_credentials grant
            "publicClient": False,
        }
    )

    yield (
        realm_admin,
        {
            "realm_name": _REALM_NAME,
            "issuer": realm_issuer,
            "token_endpoint": token_endpoint,
            "client_id": _CLIENT_ID,
            "client_secret": _CLIENT_SECRET,
        },
    )

    # Teardown: delete the Realm so the next test starts from a clean state
    realm_admin.delete_realm(_REALM_NAME)

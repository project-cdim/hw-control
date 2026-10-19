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

"""Tests for authorization_server_client."""

import jwt
import pytest

import app.common.basic_exceptions as exc
from app.common.utils.authorization_utilities.authorization_server_client import get_agent_access_token

_SECRET_MANAGEMENT_PATCH_TARGET = (
    "app.common.utils.authorization_utilities.authorization_server_client.secret_management_client.get_secret"
)


class TestGetAgentAccessToken:
    """Tests for get_agent_access_token()."""

    @pytest.mark.parametrize("algorithm", ["RS256", "ES256"])
    def test_returns_valid_jwt_access_token(self, keycloak_realm, algorithm: str, monkeypatch: pytest.MonkeyPatch):
        """A valid JWT access token is returned from a real Keycloak instance.

        Runs for each supported signing algorithm (RS256, ES256).  The Secret
        Management utility is replaced with a monkeypatch stub.  Network
        communication and token issuance are exercised against the real
        Keycloak container.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        realm_admin, realm_settings = keycloak_realm

        # Configure the realm to use the specified signing algorithm
        realm_admin.update_realm(realm_settings["realm_name"], {"defaultSignatureAlgorithm": algorithm})

        # Replace Secret Management with a stub (the Secret API server is out of IT scope)
        monkeypatch.setattr(
            _SECRET_MANAGEMENT_PATCH_TARGET,
            lambda secret_store, secret_name: {
                "client_id": realm_settings["client_id"],
                "client_secret": realm_settings["client_secret"],
            },
        )

        # Set the Keycloak token endpoint via environment variable
        monkeypatch.setenv(
            "HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT",
            realm_settings["token_endpoint"],
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#

        token = get_agent_access_token()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#

        # The token must be in JWT format
        header = jwt.get_unverified_header(token)
        payload = jwt.decode(
            token,
            options={
                "verify_signature": False,
            },
        )

        # The signing algorithm must match the realm configuration
        assert header["alg"] == algorithm

        # Claims required by downstream token verification must be present
        assert "exp" in payload, "JWT payload should contain 'exp' claim"
        assert "aud" in payload, "JWT payload should contain 'aud' claim"
        assert "iss" in payload, "JWT payload should contain 'iss' claim"

        # The issuer must match the test Realm
        assert payload["iss"] == realm_settings["issuer"]

    @pytest.mark.parametrize(
        ("client_id", "client_secret"),
        [
            ("hw-control-client", "wrong-secret"),  # correct ID, wrong secret
            ("nonexistent-client-id", "test-secret"),  # wrong ID, correct secret
            ("nonexistent-client-id", "wrong-secret"),  # both wrong
        ],
        ids=["wrong_secret", "wrong_client_id", "both_wrong"],
    )
    def test_authentication_error_on_invalid_credentials(
        self, keycloak_realm, monkeypatch: pytest.MonkeyPatch, client_id: str, client_secret: str
    ):
        """AuthenticationHWControlError is raised for any invalid client credentials.

        Covers three cases: wrong secret only, wrong client ID only, and both wrong.
        The Authorization Server returns 401 with error code 'invalid_client' in
        all cases, which get_agent_access_token() translates to
        AuthenticationHWControlError.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        _, realm_settings = keycloak_realm

        monkeypatch.setattr(
            _SECRET_MANAGEMENT_PATCH_TARGET,
            lambda secret_store, secret_name: {
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )
        monkeypatch.setenv(
            "HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT",
            realm_settings["token_endpoint"],
        )

        # ++++ execution / inspection +++++++++++++++++++++++++++++++++#

        with pytest.raises(exc.AuthenticationHWControlError):
            get_agent_access_token()

    @pytest.mark.parametrize(
        "secret",
        [
            {"client_secret": "test-secret"},  # client_id missing
            {"client_id": "hw-control-client"},  # client_secret missing
            {},  # both missing
        ],
        ids=["missing_client_id", "missing_client_secret", "missing_both"],
    )
    def test_internal_error_on_missing_secret_fields(self, monkeypatch: pytest.MonkeyPatch, secret: dict):
        """InternalHWControlError is raised when required fields are absent in the secret.

        The Secret Management utility may return a dict that is missing 'client_id',
        'client_secret', or both.  ClientCredential(**secret) raises a pydantic
        ValidationError, which get_agent_access_token() translates to
        InternalHWControlError.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        monkeypatch.setattr(
            _SECRET_MANAGEMENT_PATCH_TARGET,
            lambda secret_store, secret_name: secret,
        )
        # A syntactically valid URL is required so that AuthorizationServerSettings
        # does not raise first; the credential validation error occurs before
        # any network request is made. 192.0.2.0/24 (RFC 5737 TEST-NET-1) is used
        # instead of 127.0.0.1 so that no request can ever reach a real local
        # service, even if the validation order changes in the future.
        monkeypatch.setenv(
            "HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT",
            "http://192.0.2.1:19999/realms/test/protocol/openid-connect/token",
        )

        # ++++ execution / inspection +++++++++++++++++++++++++++++++++#

        with pytest.raises(exc.InternalHWControlError):
            get_agent_access_token()

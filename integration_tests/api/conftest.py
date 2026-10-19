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

"""Fixtures for api integration tests."""

import pytest
from fastapi.testclient import TestClient

from app.hw_control_main import app


@pytest.fixture
def test_client() -> TestClient:
    """Provide TestClient for api integration tests.

    Returns:
        TestClient: FastAPI test client with raise_server_exceptions=False
                   to allow testing error handling.
    """
    return TestClient(app, raise_server_exceptions=False)

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

"""This is a test program."""

import pytest
from fastapi.testclient import TestClient
from app.routers.info.load_mappings import router
from app.hw_control_main import app
from app.core.info import info_const

client = TestClient(router)


@pytest.mark.asyncio
async def test_load_mapping_startup_event():
    """Test startup event"""
    await app.router.startup()
    assert info_const.MAPPING_TABLE


def test_reload_mapping():
    """Test reload mapping"""
    client.get("/cdim/api/v1/reload-mapping")
    assert info_const.MAPPING_TABLE

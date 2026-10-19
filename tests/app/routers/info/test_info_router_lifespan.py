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

"""This is a test program."""

from unittest.mock import patch

import pytest
from fastapi import APIRouter

from app.routers.info import info_life_span


class TestInfoRouterLifespan:
    """Test class for info_router_lifespan function."""

    @pytest.mark.asyncio
    async def test_info_router_lifespan_startup(self):
        """
        Test the startup process of info_router_lifespan.

        This test verifies that:
        1. load_mapping_table() is called during startup
        2. The lifespan context manager works correctly
        """
        router = APIRouter()

        with patch("app.core.info.info_utils.load_mapping_table") as mock_load_mapping:
            # Simulate the lifespan startup by calling the context manager
            async with info_life_span.info_router_lifespan(router):
                pass

            # Verify that load_mapping_table was called during startup
            mock_load_mapping.assert_called_once()

    @pytest.mark.asyncio
    async def test_info_router_lifespan_with_exception_in_load_mapping(self):
        """
        Test that exceptions in load_mapping_table are properly propagated.
        """
        router = APIRouter()

        with patch("app.core.info.info_utils.load_mapping_table") as mock_load_mapping:
            # Configure mock to raise an exception
            mock_load_mapping.side_effect = Exception("Generic error")

            # Test that the lifespan manager propagates the exception
            with pytest.raises(Exception, match="Generic error"):
                async with info_life_span.info_router_lifespan(router):
                    pass
            mock_load_mapping.assert_called_once()

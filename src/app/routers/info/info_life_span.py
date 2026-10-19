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

"""Module providing lifespan management for the info router in a FastAPI application.

This module defines an asynchronous context manager function to be used as a lifespan handler for an APIRouter.
When the application starts, it loads a mapping table necessary for information retrieval and response generation.
This ensures that essential data is prepared and available for request processing within the router.

"""

from contextlib import asynccontextmanager

from fastapi import APIRouter

from app.core.info import info_utils


@asynccontextmanager
async def info_router_lifespan(_router: APIRouter):
    """Lifespan function for the info router.

    This function is intended to be used as a lifespan event handler for the FastAPI router.
    It loads the mapping table required for information acquisition and response generation
    when the application starts.

    Args:
        _router (APIRouter): The FastAPI router instance.

    Yields:
        None
    """
    # --- Startup process ---
    # Reads the mapping table file used in the information acquisition process (response generation).
    info_utils.load_mapping_table()

    yield
    # --- Shutdown process ---

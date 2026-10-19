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

"""Define lifespan function for hw-control application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import ValidationError

from app.common.log import settings as log_settings

logger = logging.getLogger(__name__)


def _set_logging_settings() -> None:
    """Apply logging settings from environment variables.

    Args:
        None

    Returns:
        None
    """
    try:
        settings = log_settings.LoggingSettings()
    except ValidationError as e:
        logger.critical("Failed to get logging settings from environment variables.", exc_info=True)
        e.add_note("Please check the environment variables for logging settings.")
        raise

    logging.raiseExceptions = settings.logging_raise_exceptions
    logger.info("Logging settings applied.", extra={"raise_exceptions": settings.logging_raise_exceptions})


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Lifespan context manager for the FastAPI application.

    This function is called automatically by FastAPI at application startup and shutdown.
    The argument 'application' is set by FastAPI and receives the FastAPI app instance.
    When you specify 'lifespan=lifespan' in the FastAPI constructor, FastAPI will invoke this function
    as an async context manager, passing the app instance as the first argument.

    The argument name 'application' is used to avoid confusion with the module-level
    'app' and does not cause a circular import.
    This function configures logging settings and logs application lifecycle events.

    Args:
        application (FastAPI): The FastAPI application instance, automatically provided by FastAPI.
    """
    # Application startup
    _set_logging_settings()

    logger.info(
        "hw-control application start.",
        extra={"application_name": application.title, "version": application.version},
    )

    yield

    # Application shutdown
    logger.info("hw-control application shutdown.")

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

"""Main module for hw-control.

This module sets up the FastAPI application object and launches
the hw-control application.

To start the application using uvicorn, run the following command:

    uvicorn app.hw_control_main:app --host 0.0.0.0 --reload --port 8000 --log-config <log config file path>

"""

import uuid

from asgi_correlation_id import CorrelationIdMiddleware
from asgi_correlation_id.middleware import is_valid_uuid4
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

import app.common.basic_exceptions as custom_exceptions
from app import app_life_span
from app.common import constants
from app.routers import api_metadata, error_handlers, middlewares
from app.routers.control import control_api
from app.routers.info import devices

# Generate ASGI application instance.
app = FastAPI(
    title="hw-control",
    description=api_metadata.HW_CONTROL_API_DESCRIPTION,
    version="0.2.1",
    openapi_tags=[
        api_metadata.DEVICE_CONTROL_API_TAG,
        api_metadata.DEVICE_INFO_API_TAG,
    ],
    lifespan=app_life_span.lifespan,
    responses={
        405: api_metadata.error_case_spec_factory(case_description="The specified HTTP method is not supported.")
    },
)

# Add custom error handler to the application.
app.add_exception_handler(
    exc_class_or_status_code=StarletteHTTPException,
    handler=error_handlers.custom_http_exception_handler,
)
app.add_exception_handler(
    exc_class_or_status_code=RequestValidationError,
    handler=error_handlers.custom_validation_exception_handler,
)
app.add_exception_handler(
    exc_class_or_status_code=Exception,
    handler=error_handlers.custom_exception_handler,
)
app.add_exception_handler(
    exc_class_or_status_code=custom_exceptions.BaseHWControlError,
    handler=error_handlers.hw_control_error_handler,
)

# Add custom middleware to the application.
app.add_middleware(middleware_class=middlewares.LoggingMiddleware)
app.add_middleware(
    CorrelationIdMiddleware,
    header_name=constants.CORRELATION_ID_HEADER,
    update_request_header=False,
    generator=lambda: str(uuid.uuid4()),
    validator=is_valid_uuid4,
)

# Include routers in the application.
app.include_router(control_api.router)
app.include_router(devices.router)

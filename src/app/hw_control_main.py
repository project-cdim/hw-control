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

"""Main module for hw-control.

This module sets up the FastAPI application object and launches
the hw-control application.

To start the application using uvicorn, run the following command:

    uvicorn app.hw_control_main:app --host 0.0.0.0 --reload --port 8000

"""
import sys

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.routers import api_metadata


def start_hw_control() -> FastAPI:
    """Process startup functions

    TODO:This is a temporary process to capture exceptions
        at system startup and output them to standard output,
        and needs to be reviewed.
    """
    # Fast API start
    api = FastAPI(
        title="hw-control",
        description="The API specifications of hw-control module.",
        version="0.1.0",
        openapi_tags=[
            api_metadata.DEVICE_CONTROL_API_TAG,
        ],
    )

    try:
        from app.routers.control import control_api  # pylint: disable=C0415
        from app.routers.info import devices, load_mappings  # pylint: disable=C0415
        from app.routers import error_handlers
        import app.common.basic_exceptions as custom_exceptions

        api.add_exception_handler(
            exc_class_or_status_code=StarletteHTTPException, handler=error_handlers.custom_http_exception_handler
        )
        api.add_exception_handler(
            exc_class_or_status_code=RequestValidationError, handler=error_handlers.custom_validation_exception_handler
        )
        api.add_exception_handler(
            exc_class_or_status_code=Exception,
            handler=error_handlers.custom_exception_handler,
        )
        api.add_exception_handler(
            exc_class_or_status_code=custom_exceptions.BaseHwControlError,
            handler=error_handlers.hw_control_error_handler,
        )

        api.include_router(control_api.router)
        api.include_router(devices.router)
        api.include_router(load_mappings.router)

    except ImportError as error:
        print(f"Error: The required library '{error.name}' is not installed.", file=sys.stderr)
        sys.exit(1)
    except Exception as error:  # pylint: disable=W0718
        print(f"Error:{str(error)}", file=sys.stderr)
        sys.exit(1)

    return api


app = start_hw_control()

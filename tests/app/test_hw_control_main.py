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

"""Unit test module for hw_control_main.py."""

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

import app.common.basic_exceptions as custom_exceptions
from app import app_life_span, hw_control_main
from app.routers import error_handlers, middlewares


class TestApplicationInstance:
    """Test class for hw-control application instance.

    hw_control_main module generates the FastAPI application instance
    and sets up.
    This class tests that the application instance is correctly configured.
    """

    def test_exception_handlers_added(self):
        """Test that exception handlers are added to the application."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        app = hw_control_main.app

        handlers = app.exception_handlers

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # Check if the handlers for the expected exceptions are present
        # and that they are the correct functions.

        assert StarletteHTTPException in handlers
        assert RequestValidationError in handlers
        assert Exception in handlers
        assert custom_exceptions.BaseHWControlError in handlers

        # Check if the handler functions are correct

        assert handlers[StarletteHTTPException] == error_handlers.custom_http_exception_handler
        assert handlers[RequestValidationError] == error_handlers.custom_validation_exception_handler
        assert handlers[Exception] == error_handlers.custom_exception_handler
        assert handlers[custom_exceptions.BaseHWControlError] == error_handlers.hw_control_error_handler

    def test_middlewares_ordering(self):
        """Test the ordering of middlewares in the application.

        This test ensures that the middlewares are applied in the correct order
        as expected by the application.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        app = hw_control_main.app
        middleware_classes = [mw.cls for mw in app.user_middleware]

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(middleware_classes) == 2
        assert middleware_classes[0] is CorrelationIdMiddleware
        assert middleware_classes[1] is middlewares.LoggingMiddleware

    def test_lifespan_function_set(self):
        """Test that lifespan function is set in the application."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        app = hw_control_main.app

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#

        assert hasattr(app.router, "lifespan")
        assert app.router.lifespan.__name__ == app_life_span.lifespan.__name__

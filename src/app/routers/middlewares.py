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

"""
This module defines middleware components used in the application.

The middleware in this module is responsible for handling various aspects of
HTTP request and response processing.

Usage:
    Add the middleware defined in this module to your FastAPI application
    object to enable additional request processing features.
"""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):  # pylint: disable=R0903
    """
    Middleware to log details of incoming HTTP requests and outgoing HTTP responses.

    This middleware logs the HTTP method, client IP address, port, path parameters,
    query parameters, request body, and response status code for debugging and tracking purposes.
    """

    async def _log_request(self, request: Request) -> None:
        """
        Logs details of the incoming HTTP request.

        This method extracts and logs the HTTP method, client IP address, port,
        path parameters, query parameters, and body of the request for debugging
        and tracking purposes.

        Args:
            request (Request): The incoming HTTP request object to be logged.
        """

        client_ip_address = ""
        client_port = ""

        if request.client:
            client_ip_address = request.client.host
            client_port = str(request.client.port)

        logger.info(
            msg="Accept http request.",
            extra={
                "http_method": request.method,
                "path": request.url.path,
                "content_length": request.headers.get("content-length", ""),
                "client": {
                    "ip_address": client_ip_address,
                    "port": client_port,
                },
            },
        )

    async def _log_response(self, response: Response, app_process_time: float) -> None:
        """
        Logs details of the HTTP response.

        This method logs the HTTP response.

        Args:
            response (Response): The HTTP response object to be logged.

            app_process_time (float): The time taken to process the request in the application.
        """

        logger.info(
            msg="Return http response.",
            extra={
                "http_status": response.status_code,
                "content_length": response.headers.get("content-length"),
                "app_process_time": app_process_time,
            },
        )

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        Middleware method to handle the dispatch of requests and logging trail.

        This method logs the trail HTTP request and response information.

        Args:
            request (Request): The incoming HTTP request object.
            call_next (RequestResponseEndpoint): A callable that processes the request and returns a response.

        Returns:
            Response: The HTTP response generated after processing the request.
        """

        start_time = time.perf_counter()
        await self._log_request(request)

        response = await call_next(request)

        # Calculate the application processing time for a HTTP request.
        app_process_time = time.perf_counter() - start_time

        await self._log_response(response, app_process_time)

        return response

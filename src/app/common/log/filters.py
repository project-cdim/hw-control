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

"""
Define logging filters.
"""

import logging

from app.common import request_id_utilities


class RequestIDFilter(logging.Filter):  # pylint: disable=R0903
    """Adds the request ID to log records.

    A logging filter that adds the request ID to log records.

    Note:
        If a 'request_id' key is specified in the extra parameters when logging
        (e.g., logger.info("message", extra={"request_id": "custom_value"})),
        this filter will overwrite that value with the current request ID
        obtained from request_id_utilities.get_request_id().
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Adds the request ID to log records.

        This method adds a 'request_id' attribute to the given LogRecord
        object and sets its value to the current request ID.

        Args:
            record (logging.LogRecord): The incoming HTTP request object.

        Returns:
            bool: Always returns True to indicate that the record should always
                be processed after adding the request ID.
        """

        record.request_id = request_id_utilities.get_request_id()
        return True

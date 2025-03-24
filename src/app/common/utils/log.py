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

""" LogFactory
"""

import cdimlogger
from app.common.settings import settings
import app.common.basic_exceptions as exc


class Logger:
    """Create Logger"""

    _logger = {}

    @classmethod
    def get_logger(cls, file_name=settings.LOG_FILE) -> cdimlogger.Logger:
        """Get logger"""
        try:
            if file_name not in cls._logger:
                cls._logger[file_name] = cdimlogger.Logger(
                    tag=settings.LOG_TAG,
                    log_dir=settings.LOG_DIR,
                    log_file=file_name,
                    logging_level=settings.LOGGING_LEVEL,
                    rotation_size=settings.LOG_ROTATION_SIZE,
                    backup_files=settings.LOG_BACKUP_FILES,
                    stdout=settings.LOG_STDOUT,
                )

            return cls._logger[file_name]
        except Exception as error:  # pylint: disable=W0718
            raise exc.UnexpectedExceptionHwControlError from error


LOGGER: cdimlogger.Logger = Logger.get_logger()

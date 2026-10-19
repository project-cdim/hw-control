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

"""Unit test module for app_life_span.py"""

import logging

import pytest
from fastapi import FastAPI
from pydantic import ValidationError
from pytest_mock import MockFixture

from app import app_life_span


class TestLifespan:
    """Unit test class for app_life_span.lifespan"""

    @pytest.mark.asyncio
    async def test_lifespan_logs_start_and_shutdown(self, mocker: MockFixture, caplog: pytest.LogCaptureFixture):
        """
        Test that the lifespan function logs application start and shutdown messages.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # set upt the dummy ASGI application.
        dummy_app = FastAPI(title="dummy_app", version="1.0.0")

        # set upt the mock.
        mocked_set_logging_settings = mocker.patch.object(app_life_span, "_set_logging_settings", return_value=None)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=app_life_span.__name__):
            async with app_life_span.lifespan(dummy_app):
                # ++++ inspection for startup logic

                # test logging settings was called.
                mocked_set_logging_settings.assert_called_once()

                # Inspection: Check the app start log.
                app_start_log = caplog.records[0]
                assert app_start_log.levelname == "INFO"
                assert app_start_log.getMessage() == "hw-control application start."

                assert hasattr(app_start_log, "application_name"), (
                    "application_name should be present in the log record"
                )
                assert getattr(app_start_log, "application_name") == "dummy_app"

                assert hasattr(app_start_log, "version"), "version should be present in the log record"
                assert getattr(app_start_log, "version") == "1.0.0"
            # ++++ inspection for shutdown logic

            # Inspection: Check the app shutdown log.
            app_shutdown_log = caplog.records[1]
            assert app_shutdown_log.levelname == "INFO"
            assert app_shutdown_log.getMessage() == "hw-control application shutdown."

        assert len(caplog.records) == 2

    @pytest.mark.asyncio
    async def test_log_setting_error(self, mocker: MockFixture):
        """Test that the log setting error case is handled properly."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # set upt the dummy ASGI application.
        dummy_app = FastAPI(title="dummy_app", version="1.0.0")

        # set upt the mock.
        dummy_title = "dummy"
        dummy_line_errors: list = []
        mocked_set_logging_settings = mocker.patch.object(
            app_life_span, "_set_logging_settings", side_effect=ValidationError(dummy_title, dummy_line_errors)
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            # Use the lifespan context manager directly
            async with app_life_span.lifespan(dummy_app):
                # test logging settings was called.
                mocked_set_logging_settings.assert_called_once()


class TestSetLoggingSettings:
    """Unit test class for _set_logging_settings."""

    @pytest.mark.parametrize(
        "dummy_logging_raise_exceptions_value",
        [
            True,
            False,
        ],
    )
    def test_apply_logging_settings(
        self, mocker: MockFixture, caplog: pytest.LogCaptureFixture, dummy_logging_raise_exceptions_value: bool
    ):
        """Test _set_logging_settings applies."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Clean up the logging.raiseExceptions before execution
        if dummy_logging_raise_exceptions_value is False:
            logging.raiseExceptions = True
        else:
            logging.raiseExceptions = False

        # set upt the mock.
        dummy_settings = mocker.Mock()
        dummy_settings.logging_raise_exceptions = dummy_logging_raise_exceptions_value
        mocker.patch("app.common.log.settings.LoggingSettings", return_value=dummy_settings)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger=app_life_span.__name__):
            app_life_span._set_logging_settings()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert logging.raiseExceptions is dummy_logging_raise_exceptions_value

        # test for log
        assert len(caplog.records) == 1

        # Inspection: Check the apply setting log.
        apply_setting_log = caplog.records[0]
        assert apply_setting_log.levelname == "INFO"
        assert apply_setting_log.getMessage() == "Logging settings applied."

        assert hasattr(apply_setting_log, "raise_exceptions"), "raise_exceptions should be present in the log record"
        assert getattr(apply_setting_log, "raise_exceptions") is dummy_logging_raise_exceptions_value

    def test_validation_error(self, mocker: MockFixture, caplog: pytest.LogCaptureFixture):
        """Test _set_logging_settings raises ValidationError."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # set upt the mock.
        mocker.patch("app.common.log.settings.LoggingSettings", side_effect=ValidationError("dummy", []))

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with pytest.raises(ValidationError) as exc_info:
            with caplog.at_level(logging.INFO, logger=app_life_span.__name__):
                app_life_span._set_logging_settings()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#

        # Inspection: Check that the note added by add_note is present in the exception
        notes = getattr(exc_info.value, "__notes__")
        assert notes is not None, "ValidationError should have __notes__ attribute after add_note"
        assert any("Please check the environment variables for logging settings." in str(note) for note in notes)

        # test for log
        assert len(caplog.records) == 1

        # Inspection: Check the get setting error log.
        get_setting_error_log = caplog.records[0]
        assert get_setting_error_log.levelname == "CRITICAL"
        assert get_setting_error_log.getMessage() == "Failed to get logging settings from environment variables."

        assert get_setting_error_log.exc_info is not None, "exc_info should be present in the log record"
        assert isinstance(get_setting_error_log.exc_info[1], ValidationError)

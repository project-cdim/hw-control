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
Unit tests for the default logging configuration file (config/logging_config.yaml).

hw-control provides a default logging configuration file.
The logging system is constructed during uvicorn startup using the provided logging configuration file.

- The repository supplies a default logging configuration file.
- This test module verifies the following aspects for the default logging configuration file:
    1. The logging configuration file can be loaded and the logging system is correctly configured.
    2. The logging system constructed from the logging configuration file behaves as expected.
"""

import sys
import json
import os
import logging
import logging.handlers
import logging.config
import tempfile
import http

import pytest
from pytest import CaptureFixture
import pythonjsonlogger
from uvicorn.config import LOGGING_CONFIG as UvicornLoggingConfig
from uvicorn.logging import DefaultFormatter as UvicornDefaultFormatter
from uvicorn.logging import AccessFormatter as UvicornAccessFormatter
from asgi_correlation_id import CorrelationIdFilter

import app
import plugins


@pytest.fixture(scope="function")
def shutdown_logging_system():
    """Fixture to shutdown the logging system before and after each test.

    This fixture ensures that the logging system is properly shut down before and after each test,
    preventing side effects between tests that may be caused by global logging configuration.

    Yields:
        None: This fixture does not return any value.
    """
    # Shutdown logging before the test
    logging.shutdown()
    yield
    # Shutdown logging after the test
    logging.shutdown()


class TestConstructedLoggingSystemConfig:
    """
    Tests the configuration and structure of the constructed logging system.

    This class verifies that the logging system built from config/logging_config.yaml
    is correctly configured.

    In particular, it checks that the configuration for Uvicorn loggers, handlers, and formatters
    follows Uvicorn's default values, and ensures there are no differences from the Uvicorn defaults.
    """

    @pytest.mark.usefixtures("shutdown_logging_system")
    def test_app_logger_config(self, default_logging_config: dict):
        """Test the default logging system config."""

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Create a temporary directory for log testing
        with tempfile.TemporaryDirectory(prefix="hw-control_temp_log_") as log_dir_for_test:
            # Define a subdirectory that does not exist yet
            log_file_path_for_test = os.path.join(log_dir_for_test, "app_hw_control.log")
            # Set the logger configuration dictionary
            default_logging_config["handlers"]["app_log_handler"]["filename"] = log_file_path_for_test

            # ++++ execution ++++++++++++++++++++++++++++++++++++++++++#
            logging.config.dictConfig(default_logging_config)

            # ++++ inspection +++++++++++++++++++++++++++++++++++++++++#

            # logger inspection
            app_logger = logging.getLogger(app.__name__)
            assert app_logger.propagate is True, "`app` Logger should propagate messages to the root logger."
            assert app_logger.level == logging.INFO, "`app` Logger should be set to INFO level."

            # handler inspection
            assert isinstance(
                app_logger.handlers[0], logging.handlers.RotatingFileHandler
            ), "`app` Logger should have a RotatingFileHandler."
            assert app_logger.handlers[0].baseFilename == log_file_path_for_test
            assert app_logger.handlers[0].level == logging.INFO
            assert app_logger.handlers[0].maxBytes == 15000000
            assert app_logger.handlers[0].backupCount == 100
            assert app_logger.handlers[0].encoding == "utf-8"

            # formatter inspection
            app_logger_json_formatter = app_logger.handlers[0].formatter
            assert isinstance(app_logger_json_formatter, pythonjsonlogger.json.JsonFormatter)
            assert (
                app_logger_json_formatter._fmt  # pylint: disable=W0212
                == "%(asctime)s %(levelname)s %(pathname)s %(lineno)d [%(correlation_id)s] %(message)s"
            )
            assert app_logger_json_formatter.datefmt is None

            # filter inspection
            assert isinstance(app_logger.handlers[0].filters[0], CorrelationIdFilter)

    @pytest.mark.usefixtures("shutdown_logging_system")
    def test_plugins_logger_config(self, default_logging_config: dict):
        """Test the plugins logger config."""

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Create a temporary directory for log testing
        with tempfile.TemporaryDirectory(prefix="hw-control_temp_log_") as log_dir_for_test:
            # Define a subdirectory that does not exist yet
            log_file_path_for_test = os.path.join(log_dir_for_test, "app_hw_control.log")
            # Set the logger configuration dictionary
            default_logging_config["handlers"]["app_log_handler"]["filename"] = log_file_path_for_test

            # ++++ execution ++++++++++++++++++++++++++++++++++++++++++#
            logging.config.dictConfig(default_logging_config)

            # ++++ inspection +++++++++++++++++++++++++++++++++++++++++#
            plugins_logger = logging.getLogger("plugins")

            # logger inspection
            assert plugins_logger.level == logging.INFO
            assert plugins_logger.propagate is True, "Plugins logger should propagate messages to the root logger."
            assert isinstance(plugins_logger.handlers[0], logging.handlers.RotatingFileHandler)

            # handler inspection
            assert plugins_logger.handlers[0].baseFilename == log_file_path_for_test
            assert plugins_logger.handlers[0].level == logging.INFO
            assert plugins_logger.handlers[0].maxBytes == 15000000
            assert plugins_logger.handlers[0].backupCount == 100
            assert plugins_logger.handlers[0].encoding == "utf-8"

            # formatter inspection
            assert isinstance(plugins_logger.handlers[0].formatter, pythonjsonlogger.json.JsonFormatter)
            assert (
                plugins_logger.handlers[0].formatter._fmt  # pylint: disable=W0212
                == "%(asctime)s %(levelname)s %(pathname)s %(lineno)d [%(correlation_id)s] %(message)s"
            )
            assert plugins_logger.handlers[0].formatter.datefmt is None

            # filter inspection
            assert isinstance(plugins_logger.handlers[0].filters[0], CorrelationIdFilter)

    @pytest.mark.usefixtures("shutdown_logging_system")
    def test_uvicorn_logger_config(self, default_logging_config: dict):
        """Test the uvicorn logger config."""

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Create a temporary directory for log testing
        with tempfile.TemporaryDirectory(prefix="hw-control_temp_log_") as log_dir_for_test:
            # Define a subdirectory that does not exist yet
            log_file_path_for_test = os.path.join(log_dir_for_test, "app_hw_control.log")
            # Set the logger configuration dictionary
            default_logging_config["handlers"]["app_log_handler"]["filename"] = log_file_path_for_test

            # ++++ execution ++++++++++++++++++++++++++++++++++++++++++#
            logging.config.dictConfig(default_logging_config)

            # ++++ inspection +++++++++++++++++++++++++++++++++++++++++#

            # ++++ config file inspection
            # logger inspection
            assert (
                default_logging_config["loggers"]["uvicorn"]["level"]
                == UvicornLoggingConfig["loggers"]["uvicorn"]["level"]
            )
            assert (
                default_logging_config["loggers"]["uvicorn"]["propagate"]
                == UvicornLoggingConfig["loggers"]["uvicorn"]["propagate"]
            )
            # handler(uvicorn_default) inspection
            assert (
                default_logging_config["handlers"]["uvicorn_default"]["class"]
                == UvicornLoggingConfig["handlers"]["default"]["class"]
            )
            assert (
                default_logging_config["handlers"]["uvicorn_default"]["stream"]
                == UvicornLoggingConfig["handlers"]["default"]["stream"]
            )
            # formatter(uvicorn_default_formatter) inspection
            assert (
                default_logging_config["formatters"]["uvicorn_default_formatter"]
                == UvicornLoggingConfig["formatters"]["default"]
            )

            # ++++ logging system inspection
            uvicorn_logger = logging.getLogger("uvicorn")

            # logger inspection
            assert uvicorn_logger.level == logging.INFO
            assert uvicorn_logger.propagate is False, "Uvicorn logger should not propagate messages to the root logger."
            assert len(uvicorn_logger.handlers) == 1

            # handler(uvicorn_default) inspection
            assert isinstance(uvicorn_logger.handlers[0], logging.StreamHandler)
            assert uvicorn_logger.handlers[0].stream == sys.stderr

            # formatter(uvicorn_default_formatter) inspection
            assert isinstance(uvicorn_logger.handlers[0].formatter, UvicornDefaultFormatter)
            assert getattr(uvicorn_logger.handlers[0].formatter, "_fmt") == "%(levelprefix)s %(message)s"
            assert getattr(uvicorn_logger.handlers[0].formatter, "use_colors") is False

    @pytest.mark.usefixtures("shutdown_logging_system")
    def test_uvicorn_access_logger_config(self, default_logging_config: dict):
        """Test the uvicorn.access logger config."""

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Create a temporary directory for log testing
        with tempfile.TemporaryDirectory(prefix="hw-control_temp_log_") as log_dir_for_test:
            # Define a subdirectory that does not exist yet
            log_file_path_for_test = os.path.join(log_dir_for_test, "app_hw_control.log")
            # Set the logger configuration dictionary
            default_logging_config["handlers"]["app_log_handler"]["filename"] = log_file_path_for_test

            # ++++ execution ++++++++++++++++++++++++++++++++++++++++++#

            logging.config.dictConfig(default_logging_config)

            # ++++ inspection +++++++++++++++++++++++++++++++++++++++++#

            # ++++ config file inspection
            # logger inspection
            assert (
                default_logging_config["loggers"]["uvicorn.access"]["level"]
                == UvicornLoggingConfig["loggers"]["uvicorn.access"]["level"]
            )
            assert (
                default_logging_config["loggers"]["uvicorn.access"]["propagate"]
                == UvicornLoggingConfig["loggers"]["uvicorn.access"]["propagate"]
            )
            # handler(uvicorn_access) inspection
            assert (
                default_logging_config["handlers"]["uvicorn_access"]["class"]
                == UvicornLoggingConfig["handlers"]["access"]["class"]
            )
            assert (
                default_logging_config["handlers"]["uvicorn_access"]["stream"]
                == UvicornLoggingConfig["handlers"]["access"]["stream"]
            )
            # formatter(uvicorn_access_formatter) inspection
            assert (
                default_logging_config["formatters"]["uvicorn_access_formatter"]
                == UvicornLoggingConfig["formatters"]["access"]
            )

            # ++++ logging system inspection
            uvicorn_access_logger = logging.getLogger("uvicorn.access")

            # logger inspection
            assert uvicorn_access_logger.level == logging.INFO
            assert (
                uvicorn_access_logger.propagate is False
            ), "Uvicorn access logger should not propagate messages to the root logger."
            assert len(uvicorn_access_logger.handlers) == 1

            # handler(uvicorn_access) inspection
            assert isinstance(uvicorn_access_logger.handlers[0], logging.StreamHandler)
            assert uvicorn_access_logger.handlers[0].stream == sys.stdout

            # formatter(uvicorn_access_formatter) inspection
            assert isinstance(uvicorn_access_logger.handlers[0].formatter, UvicornAccessFormatter)
            assert (
                getattr(uvicorn_access_logger.handlers[0].formatter, "_fmt")
                == '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
            )

    @pytest.mark.usefixtures("shutdown_logging_system")
    def test_uvicorn_error_logger_config(self, default_logging_config: dict):
        """Test the uvicorn.error logger config."""

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Create a temporary directory for log testing
        with tempfile.TemporaryDirectory(prefix="hw-control_temp_log_") as log_dir_for_test:
            # Define a subdirectory that does not exist yet
            log_file_path_for_test = os.path.join(log_dir_for_test, "app_hw_control.log")
            # Set the logger configuration dictionary
            default_logging_config["handlers"]["app_log_handler"]["filename"] = log_file_path_for_test

            # ++++ execution ++++++++++++++++++++++++++++++++++++++++++#

            logging.config.dictConfig(default_logging_config)

            # ++++ inspection +++++++++++++++++++++++++++++++++++++++++#
            # ++++ config file inspection
            # logger inspection
            assert (
                default_logging_config["loggers"]["uvicorn.error"]["level"]
                == UvicornLoggingConfig["loggers"]["uvicorn.error"]["level"]
            )

            # ++++ logging system inspection
            uvicorn_error_logger = logging.getLogger("uvicorn.error")

            # logger inspection
            assert uvicorn_error_logger.level == logging.INFO
            assert len(uvicorn_error_logger.handlers) == 0


class TestConstructedLoggingSystemBehavior:
    """
    Tests the runtime behavior of the constructed logging system.

    This class verifies that the logging system built from config/logging_config.yaml
    behaves as expected at runtime.
    """

    @pytest.mark.parametrize("logger_name", [app.__name__, plugins.__name__])
    @pytest.mark.usefixtures("shutdown_logging_system")
    def test_initialize_logger_creates_log_dir_and_file(self, default_logging_config: dict, logger_name: str):
        """
        Test that the logger is initialized with the correct handler and log file.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Create a temporary directory for log testing
        with tempfile.TemporaryDirectory(prefix="hw-control_temp_log_") as log_dir_for_test:
            # Define a subdirectory that does not exist yet
            log_file_path_for_test = os.path.join(log_dir_for_test, "app_hw_control.log")
            # Set the logger configuration dictionary
            default_logging_config["handlers"]["app_log_handler"]["filename"] = log_file_path_for_test

            # ++++ execution ++++++++++++++++++++++++++++++++++++++++++#
            logging.config.dictConfig(default_logging_config)

            # The log file is created when the first log entry is output, so output a log entry here.
            logger = logging.getLogger(logger_name)
            logger.info("Logger initialized and log file created for test setup.")

            # ++++ inspection +++++++++++++++++++++++++++++++++++++++++#
            # Check that the log dir exists
            assert os.path.exists(log_dir_for_test), "Log directory should be created."

            # Check that the log file exists
            assert os.path.exists(log_file_path_for_test), "Log file should be created."

    @pytest.mark.parametrize("logger_name", [app.__name__, plugins.__name__])
    @pytest.mark.usefixtures("shutdown_logging_system")
    def test_log_output_default_correlation_id(self, default_logging_config: dict, logger_name: str):
        """
        Test that the logger can log the correct log content and format when Correlation ID is not set.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        # Create a temporary directory for log testing
        with tempfile.TemporaryDirectory(prefix="hw-control-temp_log_") as log_dir_for_test:
            # Define a subdirectory that does not exist yet
            log_file_path_for_test = os.path.join(log_dir_for_test, "app_hw_control.log")
            # Set the logger configuration dictionary
            default_logging_config["handlers"]["app_log_handler"]["filename"] = log_file_path_for_test

            # Set the expected log message
            expected_log_message = "info level log output for test."

            # ++++ execution ++++++++++++++++++++++++++++++++++++++++++#
            logging.config.dictConfig(default_logging_config)

            # get logger
            logger = logging.getLogger(f"{logger_name}.foo")
            # Output info level log
            logger.info(msg=expected_log_message)

            # Read the log
            with open(log_file_path_for_test, encoding="utf-8") as log_file:
                # Parse each non-empty line as JSON
                log_entry_lines = [json.loads(line.rstrip("\n")) for line in log_file if line.strip()]

            # ++++ inspection +++++++++++++++++++++++++++++++++++++++++#
            assert len(log_entry_lines) == 1, "There should be exactly one log entry."

            # Check that the log entry is in JSON format
            assert log_entry_lines[0]["asctime"] is not None, "Log entry should contain asctime."

            assert log_entry_lines[0]["levelname"] == "INFO"
            assert log_entry_lines[0]["pathname"] == os.path.abspath(__file__)
            assert log_entry_lines[0]["lineno"] > 0  # Check that the line number is valid
            assert "correlation_id" in log_entry_lines[0], "Log entry should contain correlation_id."
            assert log_entry_lines[0]["correlation_id"] == "-"
            assert log_entry_lines[0]["message"] == expected_log_message

    @pytest.mark.parametrize("logger_name", [app.__name__, plugins.__name__])
    @pytest.mark.usefixtures("shutdown_logging_system")
    def test_log_output_set_correlation_id(
        self, logger_name: str, default_logging_config: dict, dummy_correlation_id: str
    ):
        """
        Test that the logger can log the correct log content and format when Correlation ID is set.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Create a temporary directory for log testing
        with tempfile.TemporaryDirectory(prefix="hw-control-temp_log_") as log_dir_for_test:
            # Define a subdirectory that does not exist yet
            log_file_path_for_test = os.path.join(log_dir_for_test, "app_hw_control.log")
            # Set the logger configuration dictionary
            default_logging_config["handlers"]["app_log_handler"]["filename"] = log_file_path_for_test

            # Set the expected log message
            expected_log_message = "error level log output for test."

            # ++++ execution ++++++++++++++++++++++++++++++++++++++++++#
            logging.config.dictConfig(default_logging_config)

            # get logger
            logger = logging.getLogger(f"{logger_name}.foo")

            # output error level log
            logger.error(msg=expected_log_message)

            # Read the log
            with open(log_file_path_for_test, encoding="utf-8") as log_file:
                # Parse each non-empty line as JSON
                log_entry_lines = [json.loads(line.rstrip("\n")) for line in log_file if line.strip()]

            # ++++ inspection +++++++++++++++++++++++++++++++++++++++++#
            # Check that the log entry
            assert len(log_entry_lines) == 1, "There should be exactly one log entry."
            assert log_entry_lines[0]["levelname"] == "ERROR"

            assert "correlation_id" in log_entry_lines[0], "Log entry should contain correlation_id."
            assert len(log_entry_lines[0]["correlation_id"]) == 36
            assert log_entry_lines[0]["correlation_id"] == dummy_correlation_id

    @pytest.mark.parametrize("logger_name", [app.__name__, plugins.__name__])
    @pytest.mark.usefixtures("shutdown_logging_system")
    def test_filter_overwrites_correlation_id_from_extra_parameter(
        self, logger_name: str, default_logging_config: dict, dummy_correlation_id: str
    ):
        """Test that CorrelationIdFilter overwrites correlation_id set via extra parameter.

        This test verifies that when a developer accidentally sets 'correlation_id' in the
        extra parameters during logging (e.g., logger.error(msg="test", extra={"correlation_id": "value"})),
        the CorrelationIdFilter will overwrite that value with the current Correlation ID obtained
        from the request context, ensuring consistent Correlation ID tracking throughout the
        application logs.
        """

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Create a temporary directory for log testing
        with tempfile.TemporaryDirectory(prefix="hw-control-temp_log_") as log_dir_for_test:
            # Define a subdirectory that does not exist yet
            log_file_path_for_test = os.path.join(log_dir_for_test, "app_hw_control.log")
            # Set the logger configuration dictionary
            default_logging_config["handlers"]["app_log_handler"]["filename"] = log_file_path_for_test

            # Set the expected correlation_id (value from request context set by fixture)
            expected_correlation_id = dummy_correlation_id

            # ++++ execution ++++++++++++++++++++++++++++++++++++++++++#
            logging.config.dictConfig(default_logging_config)

            # get logger
            logger = logging.getLogger(f"{logger_name}.foo")
            # output log
            logger.error(msg="foo", extra={"correlation_id": "existing Correlation ID from Logger.log extra parameter"})

            # Read the log
            with open(log_file_path_for_test, encoding="utf-8") as log_file:
                # Parse each non-empty line as JSON
                log_entry_lines = [json.loads(line.rstrip("\n")) for line in log_file if line.strip()]

            # ++++ inspection +++++++++++++++++++++++++++++++++++++++++#
            assert len(log_entry_lines) == 1, "There should be exactly one log entry."
            assert (
                log_entry_lines[0]["correlation_id"] == expected_correlation_id
            ), "correlation_id Log entry should set by CorrelationIdFilter, not from extra parameter."

    def test_uvicorn_logger_output(self, default_logging_config: dict, capsys: CaptureFixture):
        """Test that the uvicorn logger outputs the expected log."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input values for the log
        log_message = "test_uvicorn_logger"

        # Set the expected log message
        expected_log = f"INFO:     {log_message}\n"

        # Create a temporary directory for log testing
        with tempfile.TemporaryDirectory(prefix="hw-control_temp_log_") as log_dir_for_test:
            # Define a subdirectory that does not exist yet
            log_file_path_for_test = os.path.join(log_dir_for_test, "app_hw_control.log")
            # Set the logger configuration dictionary
            default_logging_config["handlers"]["app_log_handler"]["filename"] = log_file_path_for_test

            # ++++ execution ++++++++++++++++++++++++++++++++++++++++++#

            logging.config.dictConfig(default_logging_config)
            logger = logging.getLogger("uvicorn")

            logger.info(log_message)

            # ++++ inspection +++++++++++++++++++++++++++++++++++++++++#
            captured = capsys.readouterr()
            assert captured.err == expected_log

    def test_uvicorn_access_logger_output(self, default_logging_config: dict, capsys: CaptureFixture):
        """Test that the uvicorn access logger outputs the expected log."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input values for the log
        client_addr = "127.0.0.1"
        method = "GET"
        path = "/api/test"
        http_version = "1.1"
        status_code = http.HTTPStatus.OK

        # Set the expected log message
        expected_log = f'INFO:     {client_addr} - "{method} {path} HTTP/{http_version}" {status_code} OK\n'

        # Create a temporary directory for log testing
        with tempfile.TemporaryDirectory(prefix="hw-control_temp_log_") as log_dir_for_test:
            # Define a subdirectory that does not exist yet
            log_file_path_for_test = os.path.join(log_dir_for_test, "app_hw_control.log")
            # Set the logger configuration dictionary
            default_logging_config["handlers"]["app_log_handler"]["filename"] = log_file_path_for_test

            # ++++ execution ++++++++++++++++++++++++++++++++++++++++++#

            logging.config.dictConfig(default_logging_config)
            logger = logging.getLogger("uvicorn.access")

            logger.info(
                '%s - "%s %s HTTP/%s" %d',
                client_addr,
                method,
                path,
                http_version,
                status_code,
            )

            # ++++ inspection +++++++++++++++++++++++++++++++++++++++++#
            captured = capsys.readouterr()
            assert captured.out == expected_log

    def test_uvicorn_error_logger_output(self, default_logging_config: dict, capsys: CaptureFixture):
        """Test that the uvicorn error logger outputs the expected log."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set the input values for the log
        log_message = "test_uvicorn_error_logger"

        # Set the expected log message
        expected_log = f"INFO:     {log_message}\n"

        # Create a temporary directory for log testing
        with tempfile.TemporaryDirectory(prefix="hw-control_temp_log_") as log_dir_for_test:
            # Define a subdirectory that does not exist yet
            log_file_path_for_test = os.path.join(log_dir_for_test, "app_hw_control.log")
            # Set the logger configuration dictionary
            default_logging_config["handlers"]["app_log_handler"]["filename"] = log_file_path_for_test

            # ++++ execution ++++++++++++++++++++++++++++++++++++++++++#

            logging.config.dictConfig(default_logging_config)
            logger = logging.getLogger("uvicorn.error")

            logger.info(log_message)

            # ++++ inspection +++++++++++++++++++++++++++++++++++++++++#
            captured = capsys.readouterr()
            assert captured.err == expected_log

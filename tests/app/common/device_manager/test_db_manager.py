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

"""Unit tests for DBSettings and DBManager.

This module tests Pydantic settings validation for database connection settings
and database connection lifecycle management defined in the db_manager module.
"""

import logging
import traceback
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError
from pytest_mock import MockFixture
from sqlalchemy.exc import SQLAlchemyError

from app.common.device_manager.db_manager import (
    DEFAULT_DB_ECHO,
    DEFAULT_MAX_OVERFLOW,
    DEFAULT_POOL_RECYCLE,
    DEFAULT_POOL_SIZE,
    DEFAULT_POOL_TIMEOUT,
    DBManager,
    DBSettings,
)

_VALID_DB_URL = "postgresql+psycopg://user:password@localhost:5432/test-db"

# Environment variable keys used by DBSettings
_ALL_ENV_KEYS = [
    "HW_CONTROL_DEVICE_MANAGER_DB_URL",
    "HW_CONTROL_DEVICE_MANAGER_DB_POOL_SIZE",
    "HW_CONTROL_DEVICE_MANAGER_DB_MAX_OVERFLOW",
    "HW_CONTROL_DEVICE_MANAGER_DB_POOL_TIMEOUT",
    "HW_CONTROL_DEVICE_MANAGER_DB_POOL_RECYCLE",
    "HW_CONTROL_DEVICE_MANAGER_DB_ECHO",
]


class TestDBSettings:
    """Tests for DBSettings model."""

    @pytest.fixture(autouse=True)
    def clear_env(self, monkeypatch: pytest.MonkeyPatch):
        """Clear all DBSettings-related environment variables before each test."""
        for key in _ALL_ENV_KEYS:
            monkeypatch.delenv(key, raising=False)

    def test_default_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verifies that db_url is loaded from env and optional fields have default values."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_URL", _VALID_DB_URL)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual = DBSettings()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert actual.db_url.get_secret_value() == _VALID_DB_URL
        assert actual.pool_size == DEFAULT_POOL_SIZE
        assert actual.max_overflow == DEFAULT_MAX_OVERFLOW
        assert actual.pool_timeout == DEFAULT_POOL_TIMEOUT
        assert actual.pool_recycle == DEFAULT_POOL_RECYCLE
        assert actual.echo == DEFAULT_DB_ECHO

        # Verify that the db_url is masked in str and repr
        str_db_url = str(actual.db_url)
        print(f"[DEBUG] db_url str: {str_db_url}")
        assert str_db_url == "**********"

        repr_db_url = repr(actual.db_url)
        print(f"[DEBUG] db_url repr: {repr_db_url}")
        assert "**********" in repr_db_url

    @pytest.mark.parametrize(
        ("env_key", "field_name", "input_value", "expected_value"),
        [
            pytest.param(
                "HW_CONTROL_DEVICE_MANAGER_DB_POOL_SIZE",
                "pool_size",
                "10",
                10,
                id="pool_size",
            ),
            pytest.param(
                "HW_CONTROL_DEVICE_MANAGER_DB_MAX_OVERFLOW",
                "max_overflow",
                "20",
                20,
                id="max_overflow",
            ),
            pytest.param(
                "HW_CONTROL_DEVICE_MANAGER_DB_POOL_TIMEOUT",
                "pool_timeout",
                "60",
                60,
                id="pool_timeout",
            ),
            pytest.param(
                "HW_CONTROL_DEVICE_MANAGER_DB_POOL_RECYCLE",
                "pool_recycle",
                "3600",
                3600,
                id="pool_recycle",
            ),
            pytest.param(
                "HW_CONTROL_DEVICE_MANAGER_DB_ECHO",
                "echo",
                "true",
                True,
                id="echo",
            ),
        ],
    )
    def test_optional_fields_are_loaded_from_env(
        self,
        monkeypatch: pytest.MonkeyPatch,
        env_key: str,
        field_name: str,
        input_value: str,
        expected_value: int | bool,
    ) -> None:
        """Verifies that each optional field is loaded from its corresponding environment variable."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_URL", _VALID_DB_URL)
        monkeypatch.setenv(env_key, input_value)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual = DBSettings()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert getattr(actual, field_name) == expected_value

    def test_env_case_sensitive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verifies that environment variable names are case-sensitive; lowercase keys are ignored."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        monkeypatch.setenv("hw_control_device_manager_db_url", _VALID_DB_URL)

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            DBSettings()

    @pytest.mark.parametrize(
        ("env_key", "invalid_value"),
        [
            # db_url: missing
            pytest.param(None, None, id="db_url_missing"),
            # db_url: invalid format (missing :// separator)
            pytest.param(
                "HW_CONTROL_DEVICE_MANAGER_DB_URL", "this-is-not-a-valid-database-url", id="db_url_no_separator"
            ),
            # db_url: invalid format (scheme only)
            pytest.param("HW_CONTROL_DEVICE_MANAGER_DB_URL", "postgresql", id="db_url_scheme_only"),
            # pool_size: ge=1, so 0 is invalid
            pytest.param("HW_CONTROL_DEVICE_MANAGER_DB_POOL_SIZE", "0", id="pool_size_below_min"),
            # max_overflow: ge=0, so -1 is invalid
            pytest.param("HW_CONTROL_DEVICE_MANAGER_DB_MAX_OVERFLOW", "-1", id="max_overflow_below_min"),
            # pool_timeout: ge=1, so 0 is invalid
            pytest.param("HW_CONTROL_DEVICE_MANAGER_DB_POOL_TIMEOUT", "0", id="pool_timeout_below_min"),
            # pool_recycle: ge=1, so 0 is invalid
            pytest.param("HW_CONTROL_DEVICE_MANAGER_DB_POOL_RECYCLE", "0", id="pool_recycle_below_min"),
        ],
    )
    def test_invalid_value_raises_validation_error(
        self, monkeypatch: pytest.MonkeyPatch, env_key: str | None, invalid_value: str | None
    ) -> None:
        """Verifies that DBSettings raises ValidationError for missing or invalid values."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        if env_key != "HW_CONTROL_DEVICE_MANAGER_DB_URL" and env_key is not None:
            monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_URL", _VALID_DB_URL)
        if env_key is not None and invalid_value is not None:
            monkeypatch.setenv(env_key, invalid_value)

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            DBSettings()

    @pytest.mark.parametrize(
        ("env_key", "boundary_value", "field_name", "expected_value"),
        [
            # pool_size: ge=1, so 1 is the minimum valid value
            pytest.param(
                "HW_CONTROL_DEVICE_MANAGER_DB_POOL_SIZE",
                "1",
                "pool_size",
                1,
                id="pool_size_min",
            ),
            # max_overflow: ge=0, so 0 is the minimum valid value
            pytest.param(
                "HW_CONTROL_DEVICE_MANAGER_DB_MAX_OVERFLOW",
                "0",
                "max_overflow",
                0,
                id="max_overflow_min",
            ),
            # pool_timeout: ge=1, so 1 is the minimum valid value
            pytest.param(
                "HW_CONTROL_DEVICE_MANAGER_DB_POOL_TIMEOUT",
                "1",
                "pool_timeout",
                1,
                id="pool_timeout_min",
            ),
            # pool_recycle: ge=1, so 1 is the minimum valid value
            pytest.param(
                "HW_CONTROL_DEVICE_MANAGER_DB_POOL_RECYCLE",
                "1",
                "pool_recycle",
                1,
                id="pool_recycle_min",
            ),
        ],
    )
    def test_boundary_minimum_value_is_valid(
        self,
        monkeypatch: pytest.MonkeyPatch,
        env_key: str,
        boundary_value: str,
        field_name: str,
        expected_value: int,
    ) -> None:
        """Verifies that the minimum boundary value is accepted without raising a ValidationError."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_URL", _VALID_DB_URL)
        monkeypatch.setenv(env_key, boundary_value)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        actual = DBSettings()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert getattr(actual, field_name) == expected_value

    def test_secret_str_masks_password_in_validation_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verifies that ValidationError does not expose the password in traceback.

        Tests that hide_input_in_errors=True prevents password leakage in:
        - ValidationError message (str(e))
        - ValidationError details (e.errors())
        - Full traceback including exception chain
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        db_url_with_password = "postgresql+psycopg://user:confidential-pass@localhost:5432/db"
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_URL", db_url_with_password)
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_POOL_SIZE", "0")  # Invalid to trigger error

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError) as exc_info:
            DBSettings()

        # ++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        e = exc_info.value
        error_str = str(e)
        error_details = e.errors()

        print("\n[DEBUG] ValidationError message:")
        print(error_str)
        print("\n[DEBUG] ValidationError details:")
        print(error_details)

        # Verify password is not in the exception message
        assert "confidential-pass" not in error_str, "Password found in ValidationError message!"

        # Verify password is not in the error details
        error_details_str = str(error_details)
        assert "confidential-pass" not in error_details_str, "Password found in ValidationError details!"

        # Verify password is not in the full traceback
        full_traceback = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        print("\n[DEBUG] Full traceback:")
        print(full_traceback)

        assert "confidential-pass" not in full_traceback, (
            "Password found in full traceback! This would leak secrets in logs."
        )

    def test_secret_str_masks_password_in_url_validation_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verifies that URL validation errors do not expose the password in traceback.

        Tests that field_validator for db_url does not leak passwords when
        URL format validation fails (ArgumentError -> ValueError).
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        invalid_url_with_password = "not-a-valid-url://user:secret-password@host/db"
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_URL", invalid_url_with_password)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError) as exc_info:
            DBSettings()

        # ++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        e = exc_info.value
        error_str = str(e)

        print("\n[DEBUG] URL ValidationError message:")
        print(error_str)

        # Verify password is not in the exception message
        assert "secret-password" not in error_str, "Password found in ValidationError message!"

        # Verify error message is generic and safe
        assert "Invalid database URL format" in error_str, (
            "Error message should mention database URL validation failure"
        )

        # Verify password is not in the full traceback
        full_traceback = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        print("\n[DEBUG] Full traceback:")
        print(full_traceback)

        assert "secret-password" not in full_traceback, (
            "Password found in full traceback! This would leak secrets in logs."
        )


@pytest.fixture
def reset_db_manager():
    """Reset DBManager class variables before and after each test."""
    DBManager._engine = None
    DBManager._session_factory = None
    yield
    DBManager._engine = None
    DBManager._session_factory = None


@pytest.mark.usefixtures("reset_db_manager")
class TestDBManagerInitialize:
    """Tests for DBManager.initialize()."""

    @pytest.fixture
    def mock_db_infrastructure(self, mocker: MockFixture, monkeypatch: pytest.MonkeyPatch):
        """Patch create_engine, sessionmaker, and create_all with valid env vars set."""
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_URL", _VALID_DB_URL)
        mock_engine = MagicMock()
        mock_create_engine = mocker.patch(
            "app.common.device_manager.db_manager.create_engine",
            return_value=mock_engine,
        )
        mock_sessionmaker = mocker.patch("app.common.device_manager.db_manager.sessionmaker")
        mock_create_all = mocker.patch("app.common.device_manager.tables.DeviceManagerBaseTable.metadata.create_all")
        return mock_create_engine, mock_sessionmaker, mock_create_all, mock_engine

    def test_initialize_success(
        self,
        mock_db_infrastructure: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Verifies that initialize successfully creates engine, session factory, and tables."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_POOL_SIZE", "8")
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_ECHO", "true")
        mock_create_engine, mock_sessionmaker, mock_create_all, mock_engine = mock_db_infrastructure

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        DBManager.initialize()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # Verify create_engine was called with DBSettings values
        mock_create_engine.assert_called_once()
        call_kwargs = mock_create_engine.call_args.kwargs
        assert call_kwargs["pool_size"] == 8
        assert call_kwargs["echo"] is True

        # Verify sessionmaker was called with correct parameters
        mock_sessionmaker.assert_called_once_with(
            autocommit=False,
            autoflush=False,
            bind=mock_engine,
        )

        # Verify create_all was called
        mock_create_all.assert_called_once_with(mock_engine)

        # Verify class variables are set
        assert DBManager._engine is not None
        assert DBManager._session_factory is not None

    def test_initialize_already_initialized_does_not_recreate_engine(
        self,
        mock_db_infrastructure: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Verifies that calling initialize twice does not recreate the engine and logs a warning."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        mock_create_engine, _, _, _ = mock_db_infrastructure
        DBManager.initialize()
        call_count_after_first = mock_create_engine.call_count

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with caplog.at_level(logging.WARNING, logger="app.common.device_manager.db_manager"):
            DBManager.initialize()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert mock_create_engine.call_count == call_count_after_first
        assert "DBManager is already initialized." in caplog.text

    def test_initialize_raises_and_logs_validation_error(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verifies that ValidationError is raised and logged when DBSettings loading fails."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        monkeypatch.delenv("HW_CONTROL_DEVICE_MANAGER_DB_URL", raising=False)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with caplog.at_level(logging.ERROR, logger="app.common.device_manager.db_manager"):
            with pytest.raises(ValidationError):
                DBManager.initialize()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert "Failed to load device management database settings." in caplog.text

    def test_initialize_handles_create_engine_failure(
        self,
        mocker: MockFixture,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Verifies error handling when create_engine itself raises SQLAlchemyError.

        Checks that:
        - SQLAlchemyError is re-raised to the caller.
        - An error message is logged.
        - _engine remains None (no dispose call since engine was never created).
        - _session_factory remains None.

        This test covers the branch where cls._engine is None in the except clause.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_URL", _VALID_DB_URL)
        mocker.patch(
            "app.common.device_manager.db_manager.create_engine",
            side_effect=SQLAlchemyError("Failed to create engine"),
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with caplog.at_level(logging.ERROR, logger="app.common.device_manager.db_manager"):
            with pytest.raises(SQLAlchemyError):
                DBManager.initialize()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert "Failed to initialize the device management database." in caplog.text
        assert DBManager._engine is None
        assert DBManager._session_factory is None

    def test_initialize_handles_create_all_failure(
        self,
        mock_db_infrastructure: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Verifies cleanup and error handling when create_all raises SQLAlchemyError.

        Checks that:
        - SQLAlchemyError is re-raised to the caller.
        - An error message is logged.
        - The engine is disposed before resetting.
        - _engine and _session_factory are reset to None.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        _, _, mock_create_all, mock_engine = mock_db_infrastructure
        mock_create_all.side_effect = SQLAlchemyError("DB connection failed")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with caplog.at_level(logging.ERROR, logger="app.common.device_manager.db_manager"):
            with pytest.raises(SQLAlchemyError):
                DBManager.initialize()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert "Failed to initialize the device management database." in caplog.text
        mock_engine.dispose.assert_called_once()
        assert DBManager._engine is None
        assert DBManager._session_factory is None


@pytest.mark.usefixtures("reset_db_manager")
class TestDBManagerCreateSession:
    """Tests for DBManager.create_session()."""

    def test_create_session_returns_session_from_factory(self) -> None:
        """Verifies that create_session returns the session produced by the session factory."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        mock_session = MagicMock()
        mock_factory = MagicMock(return_value=mock_session)
        DBManager._session_factory = mock_factory
        DBManager._engine = MagicMock()

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = DBManager.create_session()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        mock_factory.assert_called_once()
        assert result is mock_session

    def test_create_session_not_initialized_raises_runtime_error(self) -> None:
        """Verifies that create_session raises RuntimeError when DBManager is not initialized."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(RuntimeError):
            DBManager.create_session()


@pytest.mark.usefixtures("reset_db_manager")
class TestDBManagerDispose:
    """Tests for DBManager.dispose()."""

    def test_dispose_clears_engine_and_session_factory(self) -> None:
        """Verifies that dispose calls engine.dispose() and sets class variables to None."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        mock_engine = MagicMock()
        DBManager._engine = mock_engine
        DBManager._session_factory = MagicMock()

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        DBManager.dispose()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        mock_engine.dispose.assert_called_once()
        assert DBManager._engine is None
        assert DBManager._session_factory is None

    def test_dispose_not_initialized_logs_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """Verifies that calling dispose when not initialized logs a warning without raising."""
        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with caplog.at_level(logging.WARNING, logger="app.common.device_manager.db_manager"):
            DBManager.dispose()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert "Database engine not initialized." in caplog.text

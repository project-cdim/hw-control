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

"""Integration tests for DBManager.

Tests verify DBManager initialization, session creation, and disposal
with actual PostgreSQL database.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from testcontainers.postgres import PostgresContainer

from app.common.device_manager.db_manager import DBManager

# Environment variable keys for optional DB settings
_OPTIONAL_DB_ENV_KEYS = [
    "HW_CONTROL_DEVICE_MANAGER_DB_POOL_SIZE",
    "HW_CONTROL_DEVICE_MANAGER_DB_MAX_OVERFLOW",
    "HW_CONTROL_DEVICE_MANAGER_DB_POOL_TIMEOUT",
    "HW_CONTROL_DEVICE_MANAGER_DB_POOL_RECYCLE",
    "HW_CONTROL_DEVICE_MANAGER_DB_ECHO",
]


@pytest.fixture(autouse=True)
def clean_db_env_vars(monkeypatch: pytest.MonkeyPatch):
    """Clear all DB-related environment variables before each test.

    Ensures tests are not affected by environment variables set in the
    development/CI environment, maintaining test independence.
    """
    monkeypatch.delenv("HW_CONTROL_DEVICE_MANAGER_DB_URL", raising=False)
    for env_key in _OPTIONAL_DB_ENV_KEYS:
        monkeypatch.delenv(env_key, raising=False)


@pytest.fixture(autouse=True)
def reset_db_manager():
    """Reset DBManager state before and after each test.

    Before test: Forcibly reset internal state without relying on dispose()
    to ensure clean state even if dispose() has bugs.

    After test: Call dispose() to properly release database resources,
    then force reset state to prevent leaking to other test modules.
    """
    # Before: Force reset internal state (independent of dispose() correctness)
    DBManager._engine = None
    DBManager._session_factory = None

    yield

    # After: Properly dispose resources
    if DBManager._engine is not None:
        DBManager.dispose()
    # Force reset state (in case dispose() has bugs or is not implemented correctly)
    DBManager._engine = None
    DBManager._session_factory = None


class TestDBManagerInitialize:
    """Test DBManager.initialize() with actual database."""

    def test_initialize_creates_engine_and_tables(
        self, postgres_container: PostgresContainer, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
    ) -> None:
        """Verify initialize creates engine and all tables in database."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        url = postgres_container.get_connection_url().replace("postgresql+psycopg2://", "postgresql+psycopg://")
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_URL", url)

        # +++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        DBManager.initialize()

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert DBManager._engine is not None
        assert DBManager._session_factory is not None

        session = DBManager.create_session()
        request.addfinalizer(session.close)
        assert session is not None

    def test_initialize_with_unreachable_host_raises_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify initialize with unreachable DB host raises SQLAlchemyError."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        # 192.0.2.0/24 is reserved for documentation and testing by RFC 5737
        # and is guaranteed to be unreachable in any real network environment.
        # connect_timeout shortens the libpq connection attempt so the test
        # fails fast instead of waiting for the OS-level TCP connect timeout.
        monkeypatch.setenv(
            "HW_CONTROL_DEVICE_MANAGER_DB_URL", "postgresql+psycopg://192.0.2.1:5432/test?connect_timeout=2"
        )

        # +++++ execution and inspection ++++++++++++++++++++++++++++++#
        with pytest.raises(SQLAlchemyError):
            DBManager.initialize()

    @pytest.mark.parametrize(
        ("pool_size", "max_overflow", "pool_timeout", "pool_recycle"),
        [
            pytest.param(1, 10, 30, 1800, id="pool_size_min"),
            pytest.param(5, 0, 30, 1800, id="max_overflow_min"),
            pytest.param(5, 10, 1, 1800, id="pool_timeout_min"),
            pytest.param(5, 10, 30, 1, id="pool_recycle_min"),
            pytest.param(1, 0, 1, 1, id="all_minimum_values"),
        ],
    )
    def test_initialize_with_minimum_pool_settings(
        self,
        postgres_container: PostgresContainer,
        monkeypatch: pytest.MonkeyPatch,
        request: pytest.FixtureRequest,
        pool_size: int,
        max_overflow: int,
        pool_timeout: int,
        pool_recycle: int,
    ) -> None:
        """Verify initialization works with various minimum pool settings."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        url = postgres_container.get_connection_url().replace("postgresql+psycopg2://", "postgresql+psycopg://")
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_URL", url)
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_POOL_SIZE", str(pool_size))
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_MAX_OVERFLOW", str(max_overflow))
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_POOL_TIMEOUT", str(pool_timeout))
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_POOL_RECYCLE", str(pool_recycle))

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        DBManager.initialize()

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        session = DBManager.create_session()
        request.addfinalizer(session.close)
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    def test_initialize_failure_cleans_up_internal_state(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Verify initialize cleans up internal state when SQLAlchemyError occurs.

        When initialization fails, both _engine and _session_factory should be reset
        to None to prevent subsequent operations from using partially initialized state.
        """
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        assert DBManager._engine is None
        assert DBManager._session_factory is None
        # 192.0.2.0/24 is reserved for documentation and testing by RFC 5737
        # and is guaranteed to be unreachable in any real network environment.
        # connect_timeout shortens the libpq connection attempt so the test
        # fails fast instead of waiting for the OS-level TCP connect timeout.
        monkeypatch.setenv(
            "HW_CONTROL_DEVICE_MANAGER_DB_URL", "postgresql+psycopg://192.0.2.1:5432/invalid_db?connect_timeout=2"
        )

        # +++++ execution and inspection ++++++++++++++++++++++++++++++#
        with pytest.raises(SQLAlchemyError):
            DBManager.initialize()

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert DBManager._engine is None, "Engine should be None after initialization failure"
        assert DBManager._session_factory is None, "Session factory should be None after initialization failure"

        with pytest.raises(RuntimeError, match="not initialized"):
            DBManager.create_session()


class TestDBManagerCreateSession:
    """Test DBManager.create_session() with actual database."""

    def test_create_session_returns_working_session(
        self, postgres_container: PostgresContainer, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
    ) -> None:
        """Verify create_session returns a working session."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        url = postgres_container.get_connection_url().replace("postgresql+psycopg2://", "postgresql+psycopg://")
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_URL", url)
        DBManager.initialize()

        # +++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        session = DBManager.create_session()
        request.addfinalizer(session.close)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert isinstance(session, Session)
        result = session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    def test_multiple_sessions_are_independent(
        self, postgres_container: PostgresContainer, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
    ) -> None:
        """Verify multiple sessions can be created independently."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        url = postgres_container.get_connection_url().replace("postgresql+psycopg2://", "postgresql+psycopg://")
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_URL", url)
        DBManager.initialize()

        # +++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        session1 = DBManager.create_session()
        session2 = DBManager.create_session()
        request.addfinalizer(session1.close)
        request.addfinalizer(session2.close)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert session1 is not session2


class TestDBManagerDispose:
    """Test DBManager.dispose() with actual database."""

    def test_dispose_cleans_up_resources(
        self, postgres_container: PostgresContainer, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify dispose cleans up engine and session factory."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        url = postgres_container.get_connection_url().replace("postgresql+psycopg2://", "postgresql+psycopg://")
        monkeypatch.setenv("HW_CONTROL_DEVICE_MANAGER_DB_URL", url)
        DBManager.initialize()
        assert DBManager._engine is not None
        assert DBManager._session_factory is not None

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        DBManager.dispose()

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert DBManager._engine is None
        assert DBManager._session_factory is None

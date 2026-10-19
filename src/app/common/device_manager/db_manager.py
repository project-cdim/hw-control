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

"""Database manager for device management.

This module provides database connection and session management.
Uses class methods to share a single DB engine across the entire application.
"""

import logging
from typing import ClassVar

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Engine, create_engine, make_url
from sqlalchemy.exc import ArgumentError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.common.device_manager.tables import DeviceManagerBaseTable

logger = logging.getLogger(__name__)


DEFAULT_POOL_SIZE = 5
DEFAULT_MAX_OVERFLOW = 10
DEFAULT_POOL_TIMEOUT = 30
DEFAULT_POOL_RECYCLE = 1800
DEFAULT_DB_ECHO = False


class DBSettings(BaseSettings):
    """Database connection settings."""

    db_url: SecretStr = Field(
        alias="HW_CONTROL_DEVICE_MANAGER_DB_URL",
        description="Connection URL for device management database (masked in logs)",
    )

    pool_size: int = Field(
        default=DEFAULT_POOL_SIZE,
        alias="HW_CONTROL_DEVICE_MANAGER_DB_POOL_SIZE",
        description="Base number of connections in session pool",
        ge=1,
    )

    max_overflow: int = Field(
        default=DEFAULT_MAX_OVERFLOW,
        alias="HW_CONTROL_DEVICE_MANAGER_DB_MAX_OVERFLOW",
        description="Maximum temporary connections beyond pool_size",
        ge=0,
    )

    pool_timeout: int = Field(
        default=DEFAULT_POOL_TIMEOUT,
        alias="HW_CONTROL_DEVICE_MANAGER_DB_POOL_TIMEOUT",
        description="Timeout in seconds for acquiring connection",
        ge=1,
    )

    pool_recycle: int = Field(
        default=DEFAULT_POOL_RECYCLE,
        alias="HW_CONTROL_DEVICE_MANAGER_DB_POOL_RECYCLE",
        description="Connection recycle time in seconds",
        ge=1,
    )

    echo: bool = Field(
        default=DEFAULT_DB_ECHO,
        alias="HW_CONTROL_DEVICE_MANAGER_DB_ECHO",
        description="Enable SQLAlchemy engine SQL statement logging",
    )

    @field_validator("db_url")
    @classmethod
    def validate_url_format(cls, value: SecretStr) -> SecretStr:
        """Validate that the secret value is a valid SQLAlchemy database URL.

        Args:
            value: The SecretStr containing the database URL.

        Returns:
            The validated SecretStr value.

        Raises:
            ValueError: If the URL format is invalid.
        """
        try:
            make_url(value.get_secret_value())
        except ArgumentError as e:
            raise ValueError("Invalid database URL format") from e
        return value

    model_config = SettingsConfigDict(case_sensitive=True, hide_input_in_errors=True)


class DBManager:
    """Manages database connection infrastructure for device management.

    Manages DB engine and session factory as class variables and generates
    sessions through class methods. Also creates all tables defined in
    tables.py on the DBMS when initialize is called at application
    startup.
    """

    _engine: ClassVar[Engine | None] = None
    _session_factory: ClassVar[sessionmaker[Session] | None] = None

    @classmethod
    def initialize(cls) -> None:
        """Initialize the database manager.

        Loads DB settings from environment variables, creates the DB engine and
        session factory, then creates all managed tables on the DBMS if they do
        not already exist.

        Raises:
            pydantic.ValidationError: If required environment variables are
                missing or invalid when loading :class:`DBSettings`.
            sqlalchemy.exc.SQLAlchemyError: If engine creation or table
                creation fails (e.g., DBMS is unreachable).
        """
        if cls._engine is not None:
            logger.warning("DBManager is already initialized.")
            return

        try:
            db_settings = DBSettings()
        except ValidationError:
            logger.error("Failed to load device management database settings.")
            raise

        try:
            # Create DB engine
            cls._engine = create_engine(
                db_settings.db_url.get_secret_value(),  # Extract actual URL from SecretStr
                echo=db_settings.echo,
                pool_size=db_settings.pool_size,
                max_overflow=db_settings.max_overflow,
                pool_timeout=db_settings.pool_timeout,
                pool_recycle=db_settings.pool_recycle,
            )

            # Create session factory
            cls._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=cls._engine,
            )

            # Create tables - all tables inheriting from DeviceManagerBaseTable are created
            DeviceManagerBaseTable.metadata.create_all(cls._engine)
        except SQLAlchemyError:
            if cls._engine is not None:
                cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None
            logger.exception("Failed to initialize the device management database.")
            raise

    @classmethod
    def create_session(cls) -> Session:
        """Create a new session.

        Returns:
            New session instance (internally borrows connection
            from Engine's connection pool).

        Raises:
            RuntimeError: When called in uninitialized state.

        Note:
            Session is not thread-safe, so a new instance must be created
            per request or per thread. When using session outside of
            dependency injection function, caller is responsible for
            closing the session.

        Example:
            Get from dependency injection function with automatic close::

                def get_db_session():
                    session = DBManager.create_session()
                    try:
                        yield session
                    finally:
                        session.close()
        """
        if cls._session_factory is None:
            raise RuntimeError("DBManager is not initialized. Call DBManager.initialize() first.")
        return cls._session_factory()

    @classmethod
    def dispose(cls) -> None:
        """Dispose database engine and release resources."""
        if cls._engine:
            cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None
            logger.info("Database engine disposed.")
        else:
            logger.warning("Database engine not initialized.")

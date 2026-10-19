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

"""Fixtures for device manager integration tests.

Starts a PostgreSQL container via testcontainers PostgresContainer and provides
a SQLAlchemy Engine connected to it with the device_manager schema created.
"""

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

from app.common.device_manager.tables import DeviceManagerBaseTable


@pytest.fixture(scope="package")
def postgres_container() -> Generator[PostgresContainer]:
    """Start a PostgreSQL container once per package.

    This container is shared across all tests in the integration_tests/device_manager package.
    """
    with PostgresContainer("postgres:16") as container:
        yield container


@pytest.fixture(scope="package")
def db_session_factory(
    postgres_container: PostgresContainer,
) -> Generator[sessionmaker[Session]]:
    """Provide a session factory backed by the shared PostgreSQL container.

    Creates the device_manager schema once and disposes the engine at package teardown.
    """
    url = postgres_container.get_connection_url().replace("postgresql+psycopg2://", "postgresql+psycopg://")
    engine = create_engine(url)
    DeviceManagerBaseTable.metadata.create_all(engine)
    # Mirror the production session settings (see DBManager.initialize in db_manager.py)
    # so tests exercise the same session behavior.
    factory: sessionmaker[Session] = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    yield factory
    engine.dispose()


@pytest.fixture
def db_session(
    db_session_factory: sessionmaker[Session],
) -> Generator[Session]:
    """Provide a fresh session for each test with automatic cleanup.

    Truncates all tables before and after each test to ensure test isolation.
    """
    session = db_session_factory()

    def _truncate_all_tables() -> None:
        for table in reversed(DeviceManagerBaseTable.metadata.sorted_tables):
            session.execute(delete(table))
        session.commit()

    _truncate_all_tables()
    yield session
    session.rollback()
    _truncate_all_tables()
    session.close()

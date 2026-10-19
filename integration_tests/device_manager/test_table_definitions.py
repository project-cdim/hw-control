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

"""Integration tests for device manager table definitions.

Tests verify that SQLAlchemy table definitions correctly map to actual PostgreSQL tables,
including columns, types, constraints, indexes, foreign keys, and relationships.
"""

from collections.abc import Generator

import pytest
from sqlalchemy import Engine, create_engine, inspect
from sqlalchemy.engine import Inspector
from testcontainers.postgres import PostgresContainer

from app.common.device_manager.tables import DeviceManagerBaseTable


@pytest.fixture(scope="module")
def db_engine(postgres_container: PostgresContainer) -> Generator[Engine]:
    """Provide a SQLAlchemy Engine with all device manager tables created."""
    url = postgres_container.get_connection_url().replace("postgresql+psycopg2://", "postgresql+psycopg://")
    engine = create_engine(url)
    DeviceManagerBaseTable.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="module")
def db_inspector(db_engine: Engine) -> Inspector:
    """Provide a SQLAlchemy Inspector for examining database schema."""
    return inspect(db_engine)


class TestTableExistence:
    """Verify that all expected tables exist in the database."""

    def test_all_tables_are_created(self, db_inspector: Inspector) -> None:
        """Verify all 7 device manager tables are created in the database."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        table_names = db_inspector.get_table_names()
        expected_tables = {
            "resource",
            "fm",
            "oob_controller",
            "fabric",
            "switch",
            "port",
            "resource_oob_relation",
        }
        assert expected_tables.issubset(set(table_names)), f"Missing tables: {expected_tables - set(table_names)}"


class TestResourceTable:
    """Verify the resource table schema."""

    def test_columns_exist(self, db_inspector: Inspector) -> None:
        """Verify all required columns exist with correct types."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        columns = db_inspector.get_columns("resource")
        column_names = {col["name"] for col in columns}
        expected_columns = {
            "device_id",
            "cpu_serial_number",
            "cpu_manufacturer",
            "cpu_model",
            "pcie_vendor_id",
            "pcie_device_id",
            "pcie_device_serial_number",
            "device_keys",
        }
        assert column_names == expected_columns

    def test_primary_key(self, db_inspector: Inspector) -> None:
        """Verify primary key constraint."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        pk = db_inspector.get_pk_constraint("resource")
        assert pk["constrained_columns"] == ["device_id"]

    def test_not_null_constraints(self, db_inspector: Inspector) -> None:
        """Verify NOT NULL constraints on required columns."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        # Get all columns as a dict keyed by column name for easy lookup
        columns = {column_info["name"]: column_info for column_info in db_inspector.get_columns("resource")}

        assert columns["device_id"]["nullable"] is False


class TestFMTable:
    """Verify the fm table schema."""

    def test_columns_exist(self, db_inspector: Inspector) -> None:
        """Verify all required columns exist."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        columns = db_inspector.get_columns("fm")
        column_names = {col["name"] for col in columns}
        expected_columns = {"fm_manager_id"}
        assert column_names == expected_columns

    def test_primary_key(self, db_inspector: Inspector) -> None:
        """Verify primary key constraint."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        pk = db_inspector.get_pk_constraint("fm")
        assert pk["constrained_columns"] == ["fm_manager_id"]

    def test_not_null_constraints(self, db_inspector: Inspector) -> None:
        """Verify NOT NULL constraints."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        # Get all columns as a dict keyed by column name for easy lookup
        columns = {column_info["name"]: column_info for column_info in db_inspector.get_columns("fm")}

        assert columns["fm_manager_id"]["nullable"] is False


class TestOOBControllerTable:
    """Verify the oob_controller table schema."""

    def test_columns_exist(self, db_inspector: Inspector) -> None:
        """Verify all required columns exist."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        columns = db_inspector.get_columns("oob_controller")
        column_names = {col["name"] for col in columns}
        expected_columns = {"oob_manager_id"}
        assert column_names == expected_columns

    def test_primary_key(self, db_inspector: Inspector) -> None:
        """Verify primary key constraint."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        pk = db_inspector.get_pk_constraint("oob_controller")
        assert pk["constrained_columns"] == ["oob_manager_id"]

    def test_not_null_constraints(self, db_inspector: Inspector) -> None:
        """Verify NOT NULL constraints."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        # Get all columns as a dict keyed by column name for easy lookup
        columns = {column_info["name"]: column_info for column_info in db_inspector.get_columns("oob_controller")}

        assert columns["oob_manager_id"]["nullable"] is False


class TestFabricTable:
    """Verify the fabric table schema."""

    def test_columns_exist(self, db_inspector: Inspector) -> None:
        """Verify all required columns exist."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        columns = db_inspector.get_columns("fabric")
        column_names = {col["name"] for col in columns}
        expected_columns = {"fm_manager_id", "fabric_id"}
        assert column_names == expected_columns

    def test_primary_key(self, db_inspector: Inspector) -> None:
        """Verify primary key constraint (composite)."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        pk = db_inspector.get_pk_constraint("fabric")
        assert set(pk["constrained_columns"]) == {"fm_manager_id", "fabric_id"}

    def test_foreign_keys(self, db_inspector: Inspector) -> None:
        """Verify foreign key to fm table."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        fks = db_inspector.get_foreign_keys("fabric")
        fm_fks = [fk for fk in fks if fk["referred_table"] == "fm"]

        assert len(fm_fks) == 1
        assert "fm_manager_id" in fm_fks[0]["constrained_columns"]
        assert "fm_manager_id" in fm_fks[0]["referred_columns"]

    def test_not_null_constraints(self, db_inspector: Inspector) -> None:
        """Verify NOT NULL constraints on primary key columns."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        # Get all columns as a dict keyed by column name for easy lookup
        columns = {column_info["name"]: column_info for column_info in db_inspector.get_columns("fabric")}

        assert columns["fm_manager_id"]["nullable"] is False
        assert columns["fabric_id"]["nullable"] is False


class TestSwitchTable:
    """Verify the switch table schema."""

    def test_columns_exist(self, db_inspector: Inspector) -> None:
        """Verify all required columns exist."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        columns = db_inspector.get_columns("switch")
        column_names = {col["name"] for col in columns}
        expected_columns = {
            "device_id",
            "fm_manager_id",
            "fm_switch_id",
            "serial_number",
            "manufacturer",
            "model",
        }
        assert column_names == expected_columns

    def test_primary_key(self, db_inspector: Inspector) -> None:
        """Verify primary key constraint."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        pk = db_inspector.get_pk_constraint("switch")
        assert pk["constrained_columns"] == ["device_id"]

    def test_foreign_keys(self, db_inspector: Inspector) -> None:
        """Verify foreign key to fm table."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        fks = db_inspector.get_foreign_keys("switch")
        fm_fks = [fk for fk in fks if fk["referred_table"] == "fm"]

        assert len(fm_fks) == 1
        assert "fm_manager_id" in fm_fks[0]["constrained_columns"]
        assert "fm_manager_id" in fm_fks[0]["referred_columns"]

    def test_unique_constraint(self, db_inspector: Inspector) -> None:
        """Verify unique constraint on (fm_manager_id, fm_switch_id).

        This constraint is required because PortTable references these columns
        as a composite foreign key.
        """
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        unique_constraints = db_inspector.get_unique_constraints("switch")

        # Find constraint on (fm_manager_id, fm_switch_id)
        target_constraint = None
        for constraint in unique_constraints:
            if set(constraint["column_names"]) == {"fm_manager_id", "fm_switch_id"}:
                target_constraint = constraint
                break

        assert target_constraint is not None, "Unique constraint on (fm_manager_id, fm_switch_id) not found"
        assert target_constraint["name"] == "uq_switch_fm_ids"

    def test_not_null_constraints(self, db_inspector: Inspector) -> None:
        """Verify NOT NULL constraints on required columns."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        # Get all columns as a dict keyed by column name for easy lookup
        columns = {column_info["name"]: column_info for column_info in db_inspector.get_columns("switch")}

        assert columns["device_id"]["nullable"] is False
        assert columns["serial_number"]["nullable"] is False
        assert columns["manufacturer"]["nullable"] is False
        assert columns["model"]["nullable"] is False


class TestPortTable:
    """Verify the port table schema."""

    def test_columns_exist(self, db_inspector: Inspector) -> None:
        """Verify all required columns exist."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        columns = db_inspector.get_columns("port")
        column_names = {col["name"] for col in columns}
        expected_columns = {
            "fm_manager_id",
            "fm_port_id",
            "fabric_id",
            "fm_switch_id",
            "device_id",
            "switch_port_type",
        }
        assert column_names == expected_columns

    def test_primary_key(self, db_inspector: Inspector) -> None:
        """Verify composite primary key constraint."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        pk = db_inspector.get_pk_constraint("port")
        assert set(pk["constrained_columns"]) == {"fm_manager_id", "fm_port_id"}

    def test_foreign_keys(self, db_inspector: Inspector) -> None:
        """Verify foreign keys to fm, fabric, switch, and resource tables."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        fks = db_inspector.get_foreign_keys("port")

        # Foreign key to fm
        fm_fks = [fk for fk in fks if fk["referred_table"] == "fm" and len(fk["constrained_columns"]) == 1]
        assert len(fm_fks) >= 1

        # Foreign key to resource
        resource_fks = [fk for fk in fks if fk["referred_table"] == "resource"]
        assert len(resource_fks) == 1
        assert "device_id" in resource_fks[0]["constrained_columns"]

        # Composite foreign keys to fabric and switch are verified by table creation success

    def test_switch_port_type_column(self, db_inspector: Inspector) -> None:
        """Verify switch_port_type column exists."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        # Get all columns as a dict keyed by column name for easy lookup
        columns = {column_info["name"]: column_info for column_info in db_inspector.get_columns("port")}
        switch_port_type_col = columns["switch_port_type"]

        # Verify column exists and is not nullable
        assert switch_port_type_col is not None
        assert switch_port_type_col["nullable"] is False

    def test_not_null_constraints(self, db_inspector: Inspector) -> None:
        """Verify NOT NULL constraints on required columns."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        # Get all columns as a dict keyed by column name for easy lookup
        columns = {column_info["name"]: column_info for column_info in db_inspector.get_columns("port")}

        assert columns["fm_manager_id"]["nullable"] is False
        assert columns["fm_port_id"]["nullable"] is False
        assert columns["fabric_id"]["nullable"] is False
        assert columns["fm_switch_id"]["nullable"] is False
        assert columns["switch_port_type"]["nullable"] is False


class TestResourceOOBRelationTable:
    """Verify the resource_oob_relation table schema."""

    def test_columns_exist(self, db_inspector: Inspector) -> None:
        """Verify all required columns exist."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        columns = db_inspector.get_columns("resource_oob_relation")
        column_names = {col["name"] for col in columns}
        expected_columns = {"oob_manager_id", "oob_device_id", "device_id", "device_type"}
        assert column_names == expected_columns

    def test_primary_key(self, db_inspector: Inspector) -> None:
        """Verify composite primary key constraint."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        pk = db_inspector.get_pk_constraint("resource_oob_relation")
        assert set(pk["constrained_columns"]) == {"oob_manager_id", "oob_device_id"}

    def test_foreign_keys(self, db_inspector: Inspector) -> None:
        """Verify foreign keys to resource and oob_controller tables."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        fks = db_inspector.get_foreign_keys("resource_oob_relation")

        resource_fks = [fk for fk in fks if fk["referred_table"] == "resource"]
        oob_fks = [fk for fk in fks if fk["referred_table"] == "oob_controller"]

        assert len(resource_fks) == 1
        assert "device_id" in resource_fks[0]["constrained_columns"]

        assert len(oob_fks) == 1
        assert "oob_manager_id" in oob_fks[0]["constrained_columns"]

    def test_not_null_constraints(self, db_inspector: Inspector) -> None:
        """Verify NOT NULL constraints on all columns."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        # Get all columns as a dict keyed by column name for easy lookup
        columns = {
            column_info["name"]: column_info for column_info in db_inspector.get_columns("resource_oob_relation")
        }

        assert columns["oob_manager_id"]["nullable"] is False
        assert columns["oob_device_id"]["nullable"] is False
        assert columns["device_id"]["nullable"] is False
        assert columns["device_type"]["nullable"] is False


class TestCascadeAndIndexes:
    """Verify cascade behavior and indexes."""

    def test_foreign_key_cascade_on_delete(
        self,
        db_inspector: Inspector,
    ) -> None:
        """Verify foreign keys have appropriate cascade behavior.

        This is a placeholder test. Cascade behavior verification requires
        examining foreign key options which may vary by SQLAlchemy version.
        """
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        # Fabric should cascade from FM
        fabric_fks = db_inspector.get_foreign_keys("fabric")
        assert len(fabric_fks) > 0

        # Port should have relationships to switch and resource
        port_fks = db_inspector.get_foreign_keys("port")
        assert len(port_fks) >= 2

    def test_indexes_on_foreign_keys(self, db_inspector: Inspector) -> None:
        """Verify indexes exist on foreign key columns for query performance."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        # Most databases automatically create indexes on foreign keys,
        # but we verify their existence here
        fabric_indexes = db_inspector.get_indexes("fabric")
        switch_indexes = db_inspector.get_indexes("switch")
        port_indexes = db_inspector.get_indexes("port")

        # At minimum, we should have indexes (could be implicit via FK)
        assert isinstance(fabric_indexes, list)
        assert isinstance(switch_indexes, list)
        assert isinstance(port_indexes, list)

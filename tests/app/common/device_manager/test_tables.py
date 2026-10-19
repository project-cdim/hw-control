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

"""Unit tests for Device Manager table definitions.

This module tests SQLAlchemy table metadata without requiring database connections.
Tests verify table structure, constraints, relationships, and column attributes.
"""

from typing import cast

from sqlalchemy import ForeignKeyConstraint, String, Table, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import RelationshipProperty

from app.common.device_manager.tables import (
    DeviceManagerBaseTable,
    FabricTable,
    FMTable,
    OOBControllerTable,
    PortTable,
    ResourceOOBRelationTable,
    ResourceTable,
    SwitchTable,
)


class TestDeviceManagerBaseTable:
    """Tests for DeviceManagerBaseTable."""

    def test_can_manage_all_device_tables_via_metadata(self) -> None:
        """Verifies that DeviceManagerBaseTable.metadata contains all expected device table names."""

        # Verify metadata exists
        assert hasattr(DeviceManagerBaseTable, "metadata")

        # Verify all tables are registered in metadata
        expected_tables = {
            "resource",
            "fm",
            "fabric",
            "switch",
            "port",
            "oob_controller",
            "resource_oob_relation",
        }
        table_names = set(DeviceManagerBaseTable.metadata.tables.keys())
        assert table_names == expected_tables

    def test_all_tables_inherit_from_base(self) -> None:
        """Verifies that all table model classes inherit from DeviceManagerBaseTable."""

        assert issubclass(ResourceTable, DeviceManagerBaseTable)
        assert issubclass(FMTable, DeviceManagerBaseTable)
        assert issubclass(FabricTable, DeviceManagerBaseTable)
        assert issubclass(SwitchTable, DeviceManagerBaseTable)
        assert issubclass(PortTable, DeviceManagerBaseTable)
        assert issubclass(OOBControllerTable, DeviceManagerBaseTable)
        assert issubclass(ResourceOOBRelationTable, DeviceManagerBaseTable)


class TestResourceTable:
    """Tests for ResourceTable definition."""

    def test_table_structure(self) -> None:
        """Verifies that ResourceTable defines the expected table name, columns, and primary key."""

        # Verify table name
        assert ResourceTable.__tablename__ == "resource"

        # Verify required columns exist
        columns = ResourceTable.__table__.columns
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
        assert set(columns.keys()) == expected_columns

        # Verify primary key
        pk_columns = {col.name for col in ResourceTable.__table__.primary_key}
        assert pk_columns == {"device_id"}

        # Verify device_id column attributes
        device_id_col = columns["device_id"]
        assert isinstance(device_id_col.type, UUID)
        assert device_id_col.nullable is False
        assert device_id_col.default.arg.__module__ == "uuid"
        assert device_id_col.default.arg.__qualname__ == "uuid4"

        # Verify cpu_serial_number column attributes
        cpu_serial_number_col = columns["cpu_serial_number"]
        assert isinstance(cpu_serial_number_col.type, String)
        assert cpu_serial_number_col.nullable is True

        # Verify cpu_manufacturer column attributes
        cpu_manufacturer_col = columns["cpu_manufacturer"]
        assert isinstance(cpu_manufacturer_col.type, String)
        assert cpu_manufacturer_col.nullable is True

        # Verify cpu_model column attributes
        cpu_model_col = columns["cpu_model"]
        assert isinstance(cpu_model_col.type, String)
        assert cpu_model_col.nullable is True

        # Verify pcie_vendor_id column attributes
        pcie_vendor_id_col = columns["pcie_vendor_id"]
        assert isinstance(pcie_vendor_id_col.type, String)
        assert pcie_vendor_id_col.nullable is True

        # Verify pcie_device_id column attributes
        pcie_device_id_col = columns["pcie_device_id"]
        assert isinstance(pcie_device_id_col.type, String)
        assert pcie_device_id_col.nullable is True

        # Verify pcie_device_serial_number column attributes
        pcie_device_serial_number_col = columns["pcie_device_serial_number"]
        assert isinstance(pcie_device_serial_number_col.type, String)
        assert pcie_device_serial_number_col.nullable is True

        # Verify device_keys column attributes
        device_keys_col = columns["device_keys"]
        assert isinstance(device_keys_col.type, String)
        assert device_keys_col.nullable is True

    def test_relationships(self) -> None:
        """Verifies that ResourceTable defines the expected relationships to PortTable and ResourceOOBRelationTable."""
        # Verify ports relationship
        assert hasattr(ResourceTable, "ports")
        assert isinstance(ResourceTable.ports.property, RelationshipProperty)
        assert ResourceTable.ports.property.mapper.class_ is PortTable
        assert ResourceTable.ports.property.back_populates == "device"
        assert ResourceTable.ports.property.lazy == "selectin"
        assert ResourceTable.ports.property.passive_deletes == "all"

        # Verify oob_relations relationship
        assert hasattr(ResourceTable, "oob_relations")
        assert isinstance(ResourceTable.oob_relations.property, RelationshipProperty)
        assert ResourceTable.oob_relations.property.mapper.class_ is ResourceOOBRelationTable
        assert ResourceTable.oob_relations.property.back_populates == "resource"
        assert ResourceTable.oob_relations.property.lazy == "selectin"
        assert ResourceTable.oob_relations.property.passive_deletes == "all"


class TestFMTable:
    """Tests for FMTable definition."""

    def test_table_structure(self) -> None:
        """Verifies that FMTable defines the expected table name, columns, and primary key."""
        # Verify table name
        assert FMTable.__tablename__ == "fm"

        # Verify required columns exist
        columns = FMTable.__table__.columns
        expected_columns = {"fm_manager_id"}
        assert set(columns.keys()) == expected_columns

        # Verify primary key
        pk_columns = {col.name for col in FMTable.__table__.primary_key}
        assert pk_columns == {"fm_manager_id"}

        # Verify fm_manager_id column attributes
        fm_manager_id_col = columns["fm_manager_id"]
        assert isinstance(fm_manager_id_col.type, String)
        assert fm_manager_id_col.nullable is False

    def test_relationships(self) -> None:
        """Verifies that FMTable defines the expected relationships to FabricTable, SwitchTable, and PortTable."""
        # Verify fabrics relationship
        assert hasattr(FMTable, "fabrics")
        assert isinstance(FMTable.fabrics.property, RelationshipProperty)
        assert FMTable.fabrics.property.mapper.class_ is FabricTable
        assert FMTable.fabrics.property.back_populates == "fm"
        assert FMTable.fabrics.property.passive_deletes == "all"

        # Verify switches relationship
        assert hasattr(FMTable, "switches")
        assert isinstance(FMTable.switches.property, RelationshipProperty)
        assert FMTable.switches.property.mapper.class_ is SwitchTable
        assert FMTable.switches.property.back_populates == "fm"
        assert FMTable.switches.property.passive_deletes == "all"

        # Verify ports relationship
        assert hasattr(FMTable, "ports")
        assert isinstance(FMTable.ports.property, RelationshipProperty)
        assert FMTable.ports.property.mapper.class_ is PortTable
        assert FMTable.ports.property.back_populates == "fm"
        assert FMTable.ports.property.passive_deletes == "all"


class TestFabricTable:
    """Tests for FabricTable definition."""

    def test_table_structure(self) -> None:
        """Verifies that FabricTable defines the expected table name, columns, and composite primary key."""
        # Verify table name
        assert FabricTable.__tablename__ == "fabric"

        # Verify required columns exist
        columns = FabricTable.__table__.columns
        expected_columns = {"fm_manager_id", "fabric_id"}
        assert set(columns.keys()) == expected_columns

        # Verify composite primary key
        pk_columns = {col.name for col in FabricTable.__table__.primary_key}
        assert pk_columns == {"fabric_id", "fm_manager_id"}

        # Verify fm_manager_id column attributes
        fm_manager_id_col = columns["fm_manager_id"]
        assert isinstance(fm_manager_id_col.type, String)
        assert fm_manager_id_col.nullable is False

        # Verify fabric_id column attributes
        fabric_id_col = columns["fabric_id"]
        assert isinstance(fabric_id_col.type, String)
        assert fabric_id_col.nullable is False

    def test_foreign_keys_and_relationships(self) -> None:
        """Verifies that FabricTable defines the expected foreign keys and relationships."""
        # Verify foreign key to fm table
        fm_manager_id_col = FabricTable.__table__.columns["fm_manager_id"]
        (fk,) = fm_manager_id_col.foreign_keys  # Expected exactly one foreign key on fm_manager_id column
        assert fk.column.table.name == "fm"
        assert fk.column.name == "fm_manager_id"
        assert fk.ondelete == "RESTRICT"

        # Verify fm relationship
        assert hasattr(FabricTable, "fm")
        assert isinstance(FabricTable.fm.property, RelationshipProperty)
        assert FabricTable.fm.property.mapper.class_ is FMTable
        assert FabricTable.fm.property.back_populates == "fabrics"

        # Verify ports relationship
        assert hasattr(FabricTable, "ports")
        assert isinstance(FabricTable.ports.property, RelationshipProperty)
        assert FabricTable.ports.property.mapper.class_ is PortTable
        assert FabricTable.ports.property.back_populates == "fabric"
        assert FabricTable.ports.property.passive_deletes == "all"


class TestSwitchTable:
    """Tests for SwitchTable definition."""

    def test_table_structure(self) -> None:
        """Verifies that SwitchTable defines the expected table name, columns, primary key."""
        # Verify table name
        assert SwitchTable.__tablename__ == "switch"

        # Verify required columns exist
        columns = SwitchTable.__table__.columns
        expected_columns = {
            "device_id",
            "fm_manager_id",
            "fm_switch_id",
            "serial_number",
            "manufacturer",
            "model",
        }
        assert set(columns.keys()) == expected_columns

        # Verify primary key
        pk_columns = {col.name for col in SwitchTable.__table__.primary_key}
        assert pk_columns == {"device_id"}

        # Verify device_id column attributes
        device_id_col = columns["device_id"]
        assert isinstance(device_id_col.type, UUID)
        assert device_id_col.nullable is False
        assert device_id_col.default.arg.__module__ == "uuid"
        assert device_id_col.default.arg.__qualname__ == "uuid4"

        # Verify fm_manager_id column attributes
        fm_manager_id_col = columns["fm_manager_id"]
        assert isinstance(fm_manager_id_col.type, String)
        assert fm_manager_id_col.nullable is True  # NULLed explicitly by repository.sync_fm()

        # Verify fm_switch_id column attributes
        fm_switch_id_col = columns["fm_switch_id"]
        assert isinstance(fm_switch_id_col.type, String)
        assert fm_switch_id_col.nullable is True

        # Verify serial_number column attributes
        serial_number_col = columns["serial_number"]
        assert isinstance(serial_number_col.type, String)
        assert serial_number_col.nullable is False

        # Verify manufacturer column attributes
        manufacturer_col = columns["manufacturer"]
        assert isinstance(manufacturer_col.type, String)
        assert manufacturer_col.nullable is False

        # Verify model column attributes
        model_col = columns["model"]
        assert isinstance(model_col.type, String)
        assert model_col.nullable is False

    def test_foreign_keys_and_relationships(self) -> None:
        """Verifies that SwitchTable defines the expected foreign keys and relationships."""
        # Verify foreign key to fm table with RESTRICT
        fm_manager_id_col = SwitchTable.__table__.columns["fm_manager_id"]
        (fk,) = fm_manager_id_col.foreign_keys  # Expected exactly one foreign key on fm_manager_id column
        assert fk.column.table.name == "fm"
        assert fk.column.name == "fm_manager_id"
        assert fk.ondelete == "RESTRICT"

        # Verify fm relationship
        assert hasattr(SwitchTable, "fm")
        assert isinstance(SwitchTable.fm.property, RelationshipProperty)
        assert FMTable.switches.property.mapper.class_ is SwitchTable  # Bidirectional check
        assert SwitchTable.fm.property.back_populates == "switches"

        # Verify ports relationship
        assert hasattr(SwitchTable, "ports")
        assert isinstance(SwitchTable.ports.property, RelationshipProperty)
        assert SwitchTable.ports.property.mapper.class_ is PortTable
        assert SwitchTable.ports.property.back_populates == "switch"
        assert SwitchTable.ports.property.passive_deletes == "all"

    def test_unique_constraint_on_fm_switch_id(self) -> None:
        """Verifies that SwitchTable defines a unique constraint on (fm_manager_id, fm_switch_id).

        This constraint is required because PortTable references these columns
        as a composite foreign key.
        """
        # SwitchTable.__table__ is typed as FromClause, so narrow it to Table for constraint introspection.
        switch_table = cast(Table, SwitchTable.__table__)

        # Find unique constraint on (fm_manager_id, fm_switch_id)
        unique_constraints = [
            constraint for constraint in switch_table.constraints if isinstance(constraint, UniqueConstraint)
        ]

        # Should have exactly one unique constraint
        assert len(unique_constraints) == 1

        # Verify constraint columns
        constraint = unique_constraints[0]
        constraint_columns = {col.name for col in constraint.columns}
        assert constraint_columns == {"fm_manager_id", "fm_switch_id"}

        # Verify constraint name
        assert constraint.name == "uq_switch_fm_ids"


class TestPortTable:
    """Tests for PortTable definition."""

    def test_table_structure(self) -> None:
        """Verifies that PortTable defines the expected table name, columns, composite primary key."""
        # Verify table name
        assert PortTable.__tablename__ == "port"

        # Verify required columns exist
        columns = PortTable.__table__.columns
        expected_columns = {
            "fm_manager_id",
            "fm_port_id",
            "fabric_id",
            "fm_switch_id",
            "device_id",
            "switch_port_type",
        }
        assert set(columns.keys()) == expected_columns

        # Verify composite primary key
        pk_columns = {col.name for col in PortTable.__table__.primary_key}
        assert pk_columns == {"fm_manager_id", "fm_port_id"}

        # Verify fm_manager_id column attributes
        fm_manager_id_col = columns["fm_manager_id"]
        assert isinstance(fm_manager_id_col.type, String)
        assert fm_manager_id_col.nullable is False

        # Verify fm_port_id column attributes
        fm_port_id_col = columns["fm_port_id"]
        assert isinstance(fm_port_id_col.type, String)
        assert fm_port_id_col.nullable is False

        # Verify fabric_id column attributes
        fabric_id_col = columns["fabric_id"]
        assert isinstance(fabric_id_col.type, String)
        assert fabric_id_col.nullable is False

        # Verify fm_switch_id column attributes
        fm_switch_id_col = columns["fm_switch_id"]
        assert isinstance(fm_switch_id_col.type, String)
        assert fm_switch_id_col.nullable is False

        # Verify device_id column attributes
        device_id_col = columns["device_id"]
        assert isinstance(device_id_col.type, UUID)
        assert device_id_col.nullable is True  # nullable to allow ports without attached resource

        # Verify switch_port_type column attributes
        switch_port_type_col = columns["switch_port_type"]
        assert isinstance(switch_port_type_col.type, String)
        assert switch_port_type_col.nullable is False

    def test_foreign_keys_and_relationships(self) -> None:
        """Verifies that PortTable defines the expected foreign keys (single and composite) and relationships."""
        columns = PortTable.__table__.columns
        # PortTable.__table__ is typed as FromClause, so narrow it to Table for constraint introspection.
        # SQLAlchemy maintainers recommend cast when a Table mapping is known:
        # https://github.com/sqlalchemy/sqlalchemy/issues/9130
        port_table = cast(Table, PortTable.__table__)
        # Create a mapping of foreign key constraints by name for easy access.
        fk_by_name = {
            constraint.name: constraint
            for constraint in port_table.constraints
            if isinstance(constraint, ForeignKeyConstraint)
        }

        # Verify single FK to resource table with RESTRICT
        (device_fk,) = columns["device_id"].foreign_keys  # Expected exactly one foreign key on device_id column
        assert device_fk.column.table.name == "resource"
        assert device_fk.ondelete == "RESTRICT"

        # Verify single FK to fm table (RESTRICT - deletion controlled by repository)
        (fm_fk,) = (
            fk for fk in columns["fm_manager_id"].foreign_keys if fk.column.table.name == "fm"
        )  # Expected exactly one foreign key on fm_manager_id column
        assert fm_fk.ondelete == "RESTRICT"

        # Verify composite FK to fabric table (RESTRICT - deletion controlled by repository)
        fabric_fk = fk_by_name["fk_port_fabric"]
        assert {element.parent.name for element in fabric_fk.elements} == {"fm_manager_id", "fabric_id"}
        assert {element.column.name for element in fabric_fk.elements} == {"fm_manager_id", "fabric_id"}
        assert fabric_fk.ondelete == "RESTRICT"

        # Verify composite FK to switch table (RESTRICT - deletion controlled by repository)
        switch_fk = fk_by_name["fk_port_switch"]
        assert {element.parent.name for element in switch_fk.elements} == {"fm_manager_id", "fm_switch_id"}
        assert {element.column.name for element in switch_fk.elements} == {"fm_manager_id", "fm_switch_id"}
        assert switch_fk.ondelete == "RESTRICT"

        # Verify fm relationship
        assert hasattr(PortTable, "fm")
        assert isinstance(PortTable.fm.property, RelationshipProperty)
        assert PortTable.fm.property.mapper.class_ is FMTable
        assert PortTable.fm.property.back_populates == "ports"

        # Verify fabric relationship
        assert hasattr(PortTable, "fabric")
        assert isinstance(PortTable.fabric.property, RelationshipProperty)
        assert PortTable.fabric.property.mapper.class_ is FabricTable
        assert PortTable.fabric.property.back_populates == "ports"

        # Verify switch relationship
        assert hasattr(PortTable, "switch")
        assert isinstance(PortTable.switch.property, RelationshipProperty)
        assert PortTable.switch.property.mapper.class_ is SwitchTable
        assert PortTable.switch.property.back_populates == "ports"

        # Verify device relationship
        assert hasattr(PortTable, "device")
        assert isinstance(PortTable.device.property, RelationshipProperty)
        assert PortTable.device.property.mapper.class_ is ResourceTable
        assert PortTable.device.property.back_populates == "ports"


class TestOOBControllerTable:
    """Tests for OOBControllerTable definition."""

    def test_table_structure(self) -> None:
        """Verifies that OOBControllerTable defines the expected table name, columns, primary key, and types."""
        # Verify table name
        assert OOBControllerTable.__tablename__ == "oob_controller"

        # Verify required columns exist
        columns = OOBControllerTable.__table__.columns
        expected_columns = {"oob_manager_id"}
        assert set(columns.keys()) == expected_columns

        # Verify primary key
        pk_columns = {col.name for col in OOBControllerTable.__table__.primary_key}
        assert pk_columns == {"oob_manager_id"}

        # Verify oob_manager_id column attributes
        oob_manager_id_col = columns["oob_manager_id"]
        assert isinstance(oob_manager_id_col.type, String)
        assert oob_manager_id_col.nullable is False

    def test_relationships(self) -> None:
        """Verifies that OOBControllerTable defines the expected relationships to ResourceOOBRelationTable."""
        # Verify resource_relations relationship
        assert hasattr(OOBControllerTable, "resource_relations")
        assert isinstance(OOBControllerTable.resource_relations.property, RelationshipProperty)
        assert OOBControllerTable.resource_relations.property.mapper.class_ is ResourceOOBRelationTable
        assert OOBControllerTable.resource_relations.property.back_populates == "oob_controller"
        assert OOBControllerTable.resource_relations.property.passive_deletes == "all"


class TestResourceOOBRelationTable:
    """Tests for ResourceOOBRelationTable definition."""

    def test_table_structure(self) -> None:
        """Verifies that ResourceOOBRelationTable defines the expected table name, columns, composite primary key."""
        # Verify table name
        assert ResourceOOBRelationTable.__tablename__ == "resource_oob_relation"

        # Verify required columns exist
        columns = ResourceOOBRelationTable.__table__.columns
        expected_columns = {"oob_manager_id", "oob_device_id", "device_id", "device_type"}
        assert set(columns.keys()) == expected_columns

        # Verify composite primary key
        pk_columns = {col.name for col in ResourceOOBRelationTable.__table__.primary_key}
        assert pk_columns == {"oob_device_id", "oob_manager_id"}

        # Verify oob_manager_id column attributes
        oob_manager_id_col = columns["oob_manager_id"]
        assert isinstance(oob_manager_id_col.type, String)
        assert oob_manager_id_col.nullable is False

        # Verify oob_device_id column attributes
        oob_device_id_col = columns["oob_device_id"]
        assert isinstance(oob_device_id_col.type, String)
        assert oob_device_id_col.nullable is False

        # Verify device_id column attributes
        device_id_col = columns["device_id"]
        assert isinstance(device_id_col.type, UUID)
        assert device_id_col.nullable is False

        # Verify device_type column attributes
        device_type_col = columns["device_type"]
        assert isinstance(device_type_col.type, String)
        assert device_type_col.nullable is False

    def test_foreign_keys_and_relationships(self) -> None:
        """Verifies that ResourceOOBRelationTable defines the expected foreign keys and relationships."""
        columns = ResourceOOBRelationTable.__table__.columns

        # Verify FK to oob_controller table with RESTRICT
        (oob_fk,) = columns["oob_manager_id"].foreign_keys  # Expected exactly one foreign key on oob_manager_id column
        assert oob_fk.column.table.name == "oob_controller"
        assert oob_fk.column.name == "oob_manager_id"
        assert oob_fk.ondelete == "RESTRICT"

        # Verify FK to resource table with RESTRICT
        (device_fk,) = columns["device_id"].foreign_keys  # Expected exactly one foreign key on device_id column
        assert device_fk.column.table.name == "resource"
        assert device_fk.column.name == "device_id"
        assert device_fk.ondelete == "RESTRICT"

        # Verify resource relationship
        assert hasattr(ResourceOOBRelationTable, "resource")
        assert isinstance(ResourceOOBRelationTable.resource.property, RelationshipProperty)
        assert ResourceOOBRelationTable.resource.property.mapper.class_ is ResourceTable
        assert ResourceOOBRelationTable.resource.property.back_populates == "oob_relations"

        # Verify oob_controller relationship
        assert hasattr(ResourceOOBRelationTable, "oob_controller")
        assert isinstance(ResourceOOBRelationTable.oob_controller.property, RelationshipProperty)
        assert ResourceOOBRelationTable.oob_controller.property.mapper.class_ is OOBControllerTable
        assert ResourceOOBRelationTable.oob_controller.property.back_populates == "resource_relations"

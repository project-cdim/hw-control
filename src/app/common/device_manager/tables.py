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

"""SQLAlchemy table definitions for device management.

All table classes inherit from DeviceManagerBaseTable and define table structures
using SQLAlchemy's DeclarativeBase.
"""

import uuid

from sqlalchemy import ForeignKey, ForeignKeyConstraint, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class DeviceManagerBaseTable(DeclarativeBase):
    """Base class for device management tables.

    All table classes inherit from this class to enable batch creation/deletion
    on the DBMS.
    """


class ResourceTable(DeviceManagerBaseTable):
    """Resource table definition.

    Manages basic information for resources (devices other than switches).

    Holds only information that uniquely identifies physical devices.
    FM/OOB related information is managed in separate tables.
    """

    __tablename__ = "resource"

    # Column definitions
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # CPU device physical identifier set (used only for CPU type)
    cpu_serial_number: Mapped[str | None] = mapped_column(String, nullable=True)
    cpu_manufacturer: Mapped[str | None] = mapped_column(String, nullable=True)
    cpu_model: Mapped[str | None] = mapped_column(String, nullable=True)
    # PCIe device physical identifier set (used only for PCIe type)
    pcie_vendor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    pcie_device_id: Mapped[str | None] = mapped_column(String, nullable=True)
    pcie_device_serial_number: Mapped[str | None] = mapped_column(String, nullable=True)
    # Device keys (fallback when PCIe/CPU identification info is unavailable, stored as JSON string)
    device_keys: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationship definitions
    ports: Mapped[list["PortTable"]] = relationship(
        "PortTable",
        back_populates="device",
        lazy="selectin",
        passive_deletes="all",
    )
    oob_relations: Mapped[list["ResourceOOBRelationTable"]] = relationship(
        "ResourceOOBRelationTable",
        back_populates="resource",
        lazy="selectin",
        passive_deletes="all",
    )


class FMTable(DeviceManagerBaseTable):
    """FM table definition.

    Manages Fabric Manager information.
    """

    __tablename__ = "fm"

    # Column definitions
    fm_manager_id: Mapped[str] = mapped_column(String, primary_key=True)

    # Relationship definitions
    fabrics: Mapped[list["FabricTable"]] = relationship(
        "FabricTable",
        back_populates="fm",
        passive_deletes="all",
    )
    switches: Mapped[list["SwitchTable"]] = relationship(
        "SwitchTable",
        back_populates="fm",
        passive_deletes="all",
    )
    ports: Mapped[list["PortTable"]] = relationship(
        "PortTable",
        back_populates="fm",
        passive_deletes="all",
    )


class FabricTable(DeviceManagerBaseTable):
    """Fabric table definition.

    Manages Fabric (connectivity boundary) information.
    """

    __tablename__ = "fabric"

    # Column definitions
    fm_manager_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("fm.fm_manager_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    fabric_id: Mapped[str] = mapped_column(String, primary_key=True)

    # Relationship definitions
    fm: Mapped["FMTable"] = relationship("FMTable", back_populates="fabrics")
    ports: Mapped[list["PortTable"]] = relationship(
        "PortTable",
        back_populates="fabric",
        passive_deletes="all",
        overlaps="ports",
    )


class SwitchTable(DeviceManagerBaseTable):
    """Switch table definition.

    Manages switch device information.

    Note:
        Determines identical switches by physical identification info
        (serial_number/manufacturer/model). Records remain after FM deletion
        and retain the same device_id when re-managed by another FM.
    """

    __tablename__ = "switch"

    # Column definitions
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fm_manager_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("fm.fm_manager_id", ondelete="RESTRICT"), nullable=True
    )
    fm_switch_id: Mapped[str | None] = mapped_column(String, nullable=True)
    # Physical identification information (all required)
    serial_number: Mapped[str] = mapped_column(String, nullable=False)
    manufacturer: Mapped[str] = mapped_column(String, nullable=False)
    model: Mapped[str] = mapped_column(String, nullable=False)

    # Table constraints
    __table_args__ = (
        UniqueConstraint(
            "fm_manager_id",
            "fm_switch_id",
            name="uq_switch_fm_ids",
        ),
    )

    # Relationship definitions
    fm: Mapped["FMTable | None"] = relationship("FMTable", back_populates="switches")
    ports: Mapped[list["PortTable"]] = relationship(
        "PortTable",
        back_populates="switch",
        passive_deletes="all",
        overlaps="ports",
    )


class PortTable(DeviceManagerBaseTable):
    """Port table definition.

    Manages port information.

    Holds device and Fabric/Switch relationship information.
    switch_port_type is placed here as a per-port attribute.

    Note:
        All foreign keys use RESTRICT to prevent implicit DB-level deletions.
        Deletion order in repository.sync_fm(): Port → Fabric → FM.
        Switch fm_manager_id is set to NULL explicitly in repository.sync_fm()
        after Port deletion.
    """

    __tablename__ = "port"

    # Column definitions
    fm_manager_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("fm.fm_manager_id", ondelete="RESTRICT"),
        primary_key=True,
    )
    fm_port_id: Mapped[str] = mapped_column(String, primary_key=True)
    fabric_id: Mapped[str] = mapped_column(String, nullable=False)
    fm_switch_id: Mapped[str] = mapped_column(String, nullable=False)
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resource.device_id", ondelete="RESTRICT"),
        nullable=True,
    )
    switch_port_type: Mapped[str] = mapped_column(String)

    # Table constraints
    __table_args__ = (
        ForeignKeyConstraint(
            ["fm_manager_id", "fabric_id"],
            ["fabric.fm_manager_id", "fabric.fabric_id"],
            name="fk_port_fabric",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["fm_manager_id", "fm_switch_id"],
            ["switch.fm_manager_id", "switch.fm_switch_id"],
            name="fk_port_switch",
            ondelete="RESTRICT",
        ),
    )

    # Relationship definitions
    fm: Mapped["FMTable"] = relationship("FMTable", back_populates="ports", overlaps="ports")
    fabric: Mapped["FabricTable"] = relationship(
        "FabricTable",
        back_populates="ports",
        foreign_keys=[fm_manager_id, fabric_id],
        overlaps="fm,ports",
    )
    switch: Mapped["SwitchTable"] = relationship(
        "SwitchTable",
        back_populates="ports",
        foreign_keys=[fm_manager_id, fm_switch_id],
        overlaps="fm,ports,fabric",
    )
    device: Mapped["ResourceTable"] = relationship("ResourceTable", back_populates="ports")


class OOBControllerTable(DeviceManagerBaseTable):
    """OOB table definition.

    Manages OOB management system information.
    """

    __tablename__ = "oob_controller"

    # Column definitions
    oob_manager_id: Mapped[str] = mapped_column(String, primary_key=True)

    # Relationship definitions
    resource_relations: Mapped[list["ResourceOOBRelationTable"]] = relationship(
        "ResourceOOBRelationTable",
        back_populates="oob_controller",
        passive_deletes="all",
    )


class ResourceOOBRelationTable(DeviceManagerBaseTable):
    """Resource OOB Relation table definition.

    Manages the relationship between resources and OOB.

    Holds IDs used by the OOB management system to identify resources within the chassis.

    Note:
        Primary key is (oob_manager_id, oob_device_id), ensuring device uniqueness within OOB.
    """

    __tablename__ = "resource_oob_relation"

    # Column definitions
    oob_manager_id: Mapped[str] = mapped_column(
        String, ForeignKey("oob_controller.oob_manager_id", ondelete="RESTRICT"), primary_key=True
    )
    oob_device_id: Mapped[str] = mapped_column(String, primary_key=True)
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resource.device_id", ondelete="RESTRICT"), nullable=False
    )
    device_type: Mapped[str] = mapped_column(String, nullable=False)

    # Relationship definitions
    resource: Mapped["ResourceTable"] = relationship("ResourceTable", back_populates="oob_relations")
    oob_controller: Mapped["OOBControllerTable"] = relationship(
        "OOBControllerTable", back_populates="resource_relations"
    )

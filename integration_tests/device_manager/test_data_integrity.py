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

"""Integration tests for data integrity constraints with actual PostgreSQL database.

Tests verify:
- NOT NULL constraints
- UNIQUE constraints
- Foreign key constraints
- RESTRICT delete behavior (no implicit ORM-side FK manipulation)
"""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common import constants
from app.common.device_manager.tables import (
    FabricTable,
    FMTable,
    OOBControllerTable,
    PortTable,
    ResourceOOBRelationTable,
    ResourceTable,
    SwitchTable,
)


class TestNotNullConstraints:
    """Test NOT NULL constraints are enforced by the database."""

    @pytest.mark.parametrize(
        "switch_kwargs",
        [
            {
                "fm_manager_id": "fm1",
                "fm_switch_id": "sw1",
                "serial_number": None,
                "manufacturer": "Vendor1",
                "model": "Model1",
            },
            {
                "fm_manager_id": "fm1",
                "fm_switch_id": "sw1",
                "serial_number": "SN123",
                "manufacturer": None,
                "model": "Model1",
            },
            {
                "fm_manager_id": "fm1",
                "fm_switch_id": "sw1",
                "serial_number": "SN123",
                "manufacturer": "Vendor1",
                "model": None,
            },
        ],
    )
    def test_switch_table_not_null_fields(self, db_session: Session, switch_kwargs: dict) -> None:
        """Verify NOT NULL columns in switch reject NULL values."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        fm = FMTable(fm_manager_id="fm1")
        db_session.add(fm)
        db_session.commit()

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        switch = SwitchTable(**switch_kwargs)
        db_session.add(switch)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_fm_table_requires_fm_manager_id(self, db_session: Session) -> None:
        """Verify fm.fm_manager_id (NOT NULL) cannot be NULL."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        fm = FMTable(fm_manager_id=None)
        db_session.add(fm)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    @pytest.mark.parametrize(
        "fabric_kwargs",
        [
            {"fm_manager_id": None, "fabric_id": "fab1"},
            {"fm_manager_id": "fm1", "fabric_id": None},
        ],
    )
    def test_fabric_table_not_null_fields(self, db_session: Session, fabric_kwargs: dict) -> None:
        """Verify NOT NULL columns in fabric reject NULL values."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        fm = FMTable(fm_manager_id="fm1")
        db_session.add(fm)
        db_session.commit()

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        fabric = FabricTable(**fabric_kwargs)
        db_session.add(fabric)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_oob_controller_table_requires_oob_manager_id(self, db_session: Session) -> None:
        """Verify oob_controller.oob_manager_id (NOT NULL) cannot be NULL."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        oob = OOBControllerTable(oob_manager_id=None)
        db_session.add(oob)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    @pytest.mark.parametrize(
        "port_kwargs",
        [
            {
                "fm_manager_id": None,
                "fm_port_id": "port1",
                "fabric_id": "fab1",
                "fm_switch_id": "sw1",
                "switch_port_type": constants.SwitchPortType.USP.value,
            },
            {
                "fm_manager_id": "fm1",
                "fm_port_id": None,
                "fabric_id": "fab1",
                "fm_switch_id": "sw1",
                "switch_port_type": constants.SwitchPortType.USP.value,
            },
            {
                "fm_manager_id": "fm1",
                "fm_port_id": "port1",
                "fabric_id": None,
                "fm_switch_id": "sw1",
                "switch_port_type": constants.SwitchPortType.USP.value,
            },
            {
                "fm_manager_id": "fm1",
                "fm_port_id": "port1",
                "fabric_id": "fab1",
                "fm_switch_id": None,
                "switch_port_type": constants.SwitchPortType.USP.value,
            },
            {
                "fm_manager_id": "fm1",
                "fm_port_id": "port1",
                "fabric_id": "fab1",
                "fm_switch_id": "sw1",
                "switch_port_type": None,
            },
        ],
    )
    def test_port_table_not_null_fields(self, db_session: Session, port_kwargs: dict) -> None:
        """Verify NOT NULL columns in port reject NULL values."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        fm = FMTable(fm_manager_id="fm1")
        fabric = FabricTable(fm_manager_id="fm1", fabric_id="fab1")
        switch = SwitchTable(
            fm_manager_id="fm1",
            fm_switch_id="sw1",
            serial_number="SN1",
            manufacturer="V1",
            model="M1",
        )
        db_session.add_all([fm, fabric, switch])
        db_session.commit()

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        port = PortTable(**port_kwargs)
        db_session.add(port)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    @pytest.mark.parametrize(
        "relation_kwargs",
        [
            {
                "device_id": None,
                "oob_manager_id": "oob1",
                "oob_device_id": "dev1",
                "device_type": constants.DeviceType.CPU.value,
            },
            {
                "device_id": "use_resource_id",
                "oob_manager_id": None,
                "oob_device_id": "dev1",
                "device_type": constants.DeviceType.CPU.value,
            },
            {
                "device_id": "use_resource_id",
                "oob_manager_id": "oob1",
                "oob_device_id": None,
                "device_type": constants.DeviceType.CPU.value,
            },
            {
                "device_id": "use_resource_id",
                "oob_manager_id": "oob1",
                "oob_device_id": "dev1",
                "device_type": None,
            },
        ],
    )
    def test_resource_oob_relation_not_null_fields(
        self,
        db_session: Session,
        relation_kwargs: dict,
    ) -> None:
        """Verify NOT NULL columns in resource_oob_relation reject NULL values."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        resource = ResourceTable()
        oob = OOBControllerTable(oob_manager_id="oob1")
        db_session.add_all([resource, oob])
        db_session.commit()

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        insert_kwargs = relation_kwargs.copy()
        if insert_kwargs["device_id"] == "use_resource_id":
            insert_kwargs["device_id"] = resource.device_id

        relation = ResourceOOBRelationTable(**insert_kwargs)
        db_session.add(relation)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()


class TestUniqueConstraints:
    """Test UNIQUE constraints are enforced by the database."""

    def test_fm_manager_id_must_be_unique(self, db_session: Session):
        """Verify fm_manager_id (PRIMARY KEY) is unique."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        fm1 = FMTable(fm_manager_id="fm1")
        fm2 = FMTable(fm_manager_id="fm1")  # Same ID

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        db_session.add(fm1)
        db_session.add(fm2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_fabric_composite_key_must_be_unique(self, db_session: Session):
        """Verify (fm_manager_id, fabric_id) is unique."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        fm = FMTable(fm_manager_id="fm1")
        db_session.add(fm)
        db_session.commit()

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        fabric1 = FabricTable(fm_manager_id="fm1", fabric_id="fab1")
        fabric2 = FabricTable(fm_manager_id="fm1", fabric_id="fab1")
        db_session.add(fabric1)
        db_session.add(fabric2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_switch_unique_constraint_on_fm_ids(self, db_session: Session):
        """Verify (fm_manager_id, fm_switch_id) has unique constraint."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        fm = FMTable(fm_manager_id="fm1")
        db_session.add(fm)
        db_session.commit()

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        switch1 = SwitchTable(
            fm_manager_id="fm1",
            fm_switch_id="sw1",
            serial_number="SN1",
            manufacturer="V1",
            model="M1",
        )
        switch2 = SwitchTable(
            fm_manager_id="fm1",
            fm_switch_id="sw1",
            serial_number="SN2",
            manufacturer="V2",
            model="M2",
        )
        db_session.add(switch1)
        db_session.add(switch2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_port_composite_key_must_be_unique(self, db_session: Session):
        """Verify (fm_manager_id, fm_port_id) is unique."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        fm = FMTable(fm_manager_id="fm1")
        fabric = FabricTable(fm_manager_id="fm1", fabric_id="fab1")
        switch = SwitchTable(
            fm_manager_id="fm1",
            fm_switch_id="sw1",
            serial_number="SN1",
            manufacturer="V1",
            model="M1",
        )
        db_session.add(fm)
        db_session.add(fabric)
        db_session.add(switch)
        db_session.commit()

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        port1 = PortTable(
            fm_manager_id="fm1",
            fm_port_id="port1",
            fabric_id="fab1",
            fm_switch_id="sw1",
            switch_port_type=constants.SwitchPortType.USP.value,
        )
        port2 = PortTable(
            fm_manager_id="fm1",
            fm_port_id="port1",
            fabric_id="fab1",
            fm_switch_id="sw1",
            switch_port_type=constants.SwitchPortType.DSP.value,
        )
        db_session.add(port1)
        db_session.add(port2)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_resource_oob_relation_composite_key_must_be_unique(self, db_session: Session):
        """Verify (oob_manager_id, oob_device_id) is unique."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        resource = ResourceTable()
        oob = OOBControllerTable(oob_manager_id="oob1")
        db_session.add(resource)
        db_session.add(oob)
        db_session.commit()

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        rel1 = ResourceOOBRelationTable(
            device_id=resource.device_id,
            oob_manager_id="oob1",
            oob_device_id="dev1",
            device_type=constants.DeviceType.CPU.value,
        )
        rel2 = ResourceOOBRelationTable(
            device_id=resource.device_id,
            oob_manager_id="oob1",
            oob_device_id="dev1",
            device_type=constants.DeviceType.GPU.value,
        )
        db_session.add(rel1)
        db_session.add(rel2)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestForeignKeyConstraints:
    """Test foreign key constraints prevent orphan records."""

    def test_fabric_requires_existing_fm(self, db_session: Session):
        """Verify fabric cannot reference non-existent FM."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        fabric = FabricTable(
            fm_manager_id="non_existent_fm",  # FK to non-existent FM
            fabric_id="fab1",
        )

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        db_session.add(fabric)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_switch_requires_existing_fm(self, db_session: Session):
        """Verify switch cannot reference non-existent FM."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        switch = SwitchTable(
            fm_manager_id="non_existent_fm",  # FK to non-existent FM
            fm_switch_id="sw1",
            serial_number="SN1",
            manufacturer="V1",
            model="M1",
        )

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        db_session.add(switch)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_port_requires_existing_switch(self, db_session: Session):
        """Verify port cannot reference non-existent switch."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        port = PortTable(
            fm_manager_id="non_existent_fm",
            fm_port_id="port1",
            fabric_id="fab1",
            fm_switch_id="non_existent_sw",  # FK to non-existent switch
            switch_port_type=constants.SwitchPortType.USP.value,
        )

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        db_session.add(port)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_port_device_id_allows_null(self, db_session: Session):
        """Verify port.device_id can be NULL (optional FK)."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        fm = FMTable(fm_manager_id="fm1")
        fabric = FabricTable(fm_manager_id="fm1", fabric_id="fab1")
        switch = SwitchTable(
            fm_manager_id="fm1",
            fm_switch_id="sw1",
            serial_number="SN1",
            manufacturer="V1",
            model="M1",
        )
        db_session.add(fm)
        db_session.add(fabric)
        db_session.add(switch)
        db_session.commit()

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        port = PortTable(
            fm_manager_id="fm1",
            fm_port_id="port1",
            fabric_id="fab1",
            fm_switch_id="sw1",
            device_id=None,  # NULL is allowed
            switch_port_type=constants.SwitchPortType.USP.value,
        )
        db_session.add(port)
        db_session.commit()  # Should succeed

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert db_session.query(PortTable).filter_by(fm_port_id="port1").one().device_id is None

    def test_port_requires_existing_resource_when_device_id_is_set(self, db_session: Session):
        """Verify port.device_id must reference existing resource if not NULL."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        fm = FMTable(fm_manager_id="fm1")
        fabric = FabricTable(fm_manager_id="fm1", fabric_id="fab1")
        switch = SwitchTable(
            fm_manager_id="fm1",
            fm_switch_id="sw1",
            serial_number="SN1",
            manufacturer="V1",
            model="M1",
        )
        db_session.add(fm)
        db_session.add(fabric)
        db_session.add(switch)
        db_session.commit()

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        non_existent_uuid = uuid.uuid4()
        port = PortTable(
            fm_manager_id="fm1",
            fm_port_id="port1",
            fabric_id="fab1",
            fm_switch_id="sw1",
            device_id=non_existent_uuid,  # FK to non-existent resource
            switch_port_type=constants.SwitchPortType.USP.value,
        )
        db_session.add(port)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_resource_oob_relation_requires_existing_resource(self, db_session: Session):
        """Verify resource_oob_relation cannot reference non-existent resource."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        oob = OOBControllerTable(oob_manager_id="oob1")
        db_session.add(oob)
        db_session.commit()

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        non_existent_uuid = uuid.uuid4()
        relation = ResourceOOBRelationTable(
            device_id=non_existent_uuid,  # FK to non-existent resource
            oob_manager_id="oob1",
            oob_device_id="dev1",
            device_type=constants.DeviceType.CPU.value,
        )
        db_session.add(relation)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_resource_oob_relation_requires_existing_oob(self, db_session: Session):
        """Verify resource_oob_relation cannot reference non-existent OOB."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        resource = ResourceTable()
        db_session.add(resource)
        db_session.commit()

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        relation = ResourceOOBRelationTable(
            device_id=resource.device_id,
            oob_manager_id="non_existent_oob",  # FK to non-existent OOB
            oob_device_id="dev1",
            device_type=constants.DeviceType.CPU.value,
        )
        db_session.add(relation)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestCascadeDeletes:
    """Test FK constraint behaviors (RESTRICT) on delete operations."""

    def test_deleting_fm_with_fabrics_is_restricted(self, db_session: Session):
        """Verify deleting FM with fabrics is restricted by FK constraint.

        Fabric table has FK (fm_manager_id) referencing FM with ondelete="RESTRICT".
        Attempting to delete an FM while fabrics still reference it should fail
        with IntegrityError due to RESTRICT constraint.

        Note: In repository.sync_fm(), fabrics are explicitly deleted before FM
        deletion, avoiding this constraint violation.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        fm = FMTable(fm_manager_id="fm1")
        fabric1 = FabricTable(fm_manager_id="fm1", fabric_id="fab1")
        fabric2 = FabricTable(fm_manager_id="fm1", fabric_id="fab2")
        db_session.add(fm)
        db_session.add(fabric1)
        db_session.add(fabric2)
        db_session.commit()

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        db_session.delete(fm)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_deleting_fm_with_switches_is_restricted(self, db_session: Session):
        """Verify deleting FM with switches is restricted by FK constraint.

        Switch table has FK (fm_manager_id) referencing FM with ondelete="RESTRICT".
        FMTable.switches uses passive_deletes="all", so the ORM never loads the
        switches collection to NULL it out on delete(); the deletion is rejected
        by the DB exactly as if performed outside the ORM.

        Note: In repository.sync_fm(), switch.fm_manager_id / fm_switch_id are
        NULLed explicitly via an UPDATE before FM deletion, avoiding this
        constraint violation.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        fm = FMTable(fm_manager_id="fm1")
        switch1 = SwitchTable(
            fm_manager_id="fm1",
            fm_switch_id="sw1",
            serial_number="SN1",
            manufacturer="V1",
            model="M1",
        )
        switch2 = SwitchTable(
            fm_manager_id="fm1",
            fm_switch_id="sw2",
            serial_number="SN2",
            manufacturer="V2",
            model="M2",
        )
        db_session.add(fm)
        db_session.add(switch1)
        db_session.add(switch2)
        db_session.commit()

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        db_session.delete(fm)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_deleting_switch_with_ports_causes_fk_violation(self, db_session: Session):
        """Verify deleting switch with ports is restricted by FK constraint.

        Port table has composite FK (fm_manager_id, fm_switch_id) referencing switch
        with ondelete="RESTRICT". Attempting to delete a switch while ports still
        reference it should fail with IntegrityError due to RESTRICT constraint.

        This test directly validates that the RESTRICT setting on the FK is working
        as intended - deletion is immediately rejected when referenced records exist.

        Note: In repository.sync_fm(), ports are explicitly deleted before switch
        deactivation (fm_manager_id / fm_switch_id set to NULL via UPDATE),
        avoiding this constraint violation.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        fm = FMTable(fm_manager_id="fm1")
        fabric = FabricTable(fm_manager_id="fm1", fabric_id="fab1")
        switch = SwitchTable(
            fm_manager_id="fm1",
            fm_switch_id="sw1",
            serial_number="SN1",
            manufacturer="V1",
            model="M1",
        )
        port1 = PortTable(
            fm_manager_id="fm1",
            fm_port_id="p1",
            fabric_id="fab1",
            fm_switch_id="sw1",
            switch_port_type=constants.SwitchPortType.USP.value,
        )
        port2 = PortTable(
            fm_manager_id="fm1",
            fm_port_id="p2",
            fabric_id="fab1",
            fm_switch_id="sw1",
            switch_port_type=constants.SwitchPortType.DSP.value,
        )
        db_session.add(fm)
        db_session.add(fabric)
        db_session.add(switch)
        db_session.add(port1)
        db_session.add(port2)
        db_session.commit()

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        db_session.delete(switch)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_deleting_fabric_with_ports_is_restricted(self, db_session: Session):
        """Verify deleting fabric with ports is restricted by FK constraint.

        Port table has composite FK (fm_manager_id, fabric_id) referencing fabric
        with ondelete="RESTRICT". Attempting to delete a fabric while ports still
        reference it should fail with IntegrityError due to RESTRICT constraint.

        This test directly validates that the RESTRICT setting on the FK is working
        as intended - deletion is immediately rejected when referenced records exist.

        Note: In repository.sync_fm(), ports are explicitly deleted before fabric
        deletion, avoiding this constraint violation.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        fm = FMTable(fm_manager_id="fm1")
        fabric = FabricTable(fm_manager_id="fm1", fabric_id="fab1")
        switch = SwitchTable(
            fm_manager_id="fm1",
            fm_switch_id="sw1",
            serial_number="SN1",
            manufacturer="V1",
            model="M1",
        )
        port1 = PortTable(
            fm_manager_id="fm1",
            fm_port_id="p1",
            fabric_id="fab1",
            fm_switch_id="sw1",
            switch_port_type=constants.SwitchPortType.USP.value,
        )
        port2 = PortTable(
            fm_manager_id="fm1",
            fm_port_id="p2",
            fabric_id="fab1",
            fm_switch_id="sw1",
            switch_port_type=constants.SwitchPortType.DSP.value,
        )
        db_session.add(fm)
        db_session.add(fabric)
        db_session.add(switch)
        db_session.add(port1)
        db_session.add(port2)
        db_session.commit()

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        db_session.delete(fabric)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_deleting_fm_with_ports_causes_fk_violation(self, db_session: Session):
        """Verify FM deletion with ports is restricted by FK constraint.

        Port table has FK (fm_manager_id) referencing FM with ondelete="RESTRICT".
        FMTable.ports uses passive_deletes="all", so the ORM never loads the ports
        collection to NULL it out on delete(); the deletion is rejected by the DB
        exactly as if performed outside the ORM.

        Note: In repository.sync_fm(), ports are explicitly deleted before FM
        deletion, avoiding this constraint violation.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        fm = FMTable(fm_manager_id="fm1")
        fabric = FabricTable(fm_manager_id="fm1", fabric_id="fab1")
        switch = SwitchTable(
            fm_manager_id="fm1",
            fm_switch_id="sw1",
            serial_number="SN1",
            manufacturer="V1",
            model="M1",
        )
        port1 = PortTable(
            fm_manager_id="fm1",
            fm_port_id="p1",
            fabric_id="fab1",
            fm_switch_id="sw1",
            switch_port_type=constants.SwitchPortType.USP.value,
        )
        port2 = PortTable(
            fm_manager_id="fm1",
            fm_port_id="p2",
            fabric_id="fab1",
            fm_switch_id="sw1",
            switch_port_type=constants.SwitchPortType.DSP.value,
        )
        db_session.add(fm)
        db_session.add(fabric)
        db_session.add(switch)
        db_session.add(port1)
        db_session.add(port2)
        db_session.commit()

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        db_session.delete(fm)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_deleting_resource_with_ports_is_restricted(self, db_session: Session):
        """Verify deleting resource with ports is restricted by FK constraint.

        Port table has FK (device_id) referencing Resource with ondelete="RESTRICT".
        ResourceTable.ports uses passive_deletes="all", so the ORM never loads the
        ports collection to NULL it out on delete(); the deletion is rejected by
        the DB exactly as if performed outside the ORM.

        Note: In repository.sync_fm(), ports are explicitly deleted before FM
        deletion, so this constraint does not affect normal operation.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        fm = FMTable(fm_manager_id="fm1")
        fabric = FabricTable(fm_manager_id="fm1", fabric_id="fab1")
        switch = SwitchTable(
            fm_manager_id="fm1",
            fm_switch_id="sw1",
            serial_number="SN1",
            manufacturer="V1",
            model="M1",
        )
        resource = ResourceTable()
        db_session.add(fm)
        db_session.add(fabric)
        db_session.add(switch)
        db_session.add(resource)
        db_session.flush()  # Flush to generate device_id

        port = PortTable(
            fm_manager_id="fm1",
            fm_port_id="p1",
            fabric_id="fab1",
            fm_switch_id="sw1",
            device_id=resource.device_id,
            switch_port_type=constants.SwitchPortType.USP.value,
        )
        db_session.add(port)
        db_session.commit()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # Pre-condition: verify port is linked to the resource before deletion
        assert port.device_id == resource.device_id

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        db_session.delete(resource)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_deleting_resource_with_oob_relations_is_restricted(self, db_session: Session):
        """Verify deleting resource with OOB relations is restricted by FK constraint.

        ResourceOOBRelation table has FK (device_id) referencing Resource
        with ondelete="RESTRICT". Attempting to delete a resource while
        relations still reference it should fail with IntegrityError.

        Note: In repository.sync_oob(), resource records are never deleted,
        so this constraint does not affect normal operation.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Create a resource and OOB controller as the base records for the relation
        resource = ResourceTable()
        oob = OOBControllerTable(oob_manager_id="oob1")
        db_session.add(resource)
        db_session.add(oob)
        db_session.flush()  # Flush to generate device_id

        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Add OOB relation to set up the precondition for FK check
        relation = ResourceOOBRelationTable(
            device_id=resource.device_id,
            oob_manager_id="oob1",
            oob_device_id="dev1",
            device_type=constants.DeviceType.CPU.value,
        )
        db_session.add(relation)
        db_session.commit()

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        # Delete the resource — should fail due to RESTRICT constraint
        db_session.delete(resource)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_deleting_oob_with_relations_is_restricted(self, db_session: Session):
        """Verify deleting OOB with relations is restricted by FK constraint.

        ResourceOOBRelation table has FK (oob_manager_id) referencing OOBController
        with ondelete="RESTRICT". Attempting to delete an OOB controller while
        relations still reference it should fail with IntegrityError.

        Note: In repository.sync_oob(), relations are explicitly deleted before
        the OOB controller deletion, avoiding this constraint violation.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Create a resource and OOB controller as the base records for the relation
        resource = ResourceTable()
        oob = OOBControllerTable(oob_manager_id="oob1")
        db_session.add(resource)
        db_session.add(oob)
        db_session.flush()  # Flush to generate device_id

        # Add OOB relation to set up the precondition for FK check
        relation = ResourceOOBRelationTable(
            device_id=resource.device_id,
            oob_manager_id="oob1",
            oob_device_id="dev1",
            device_type=constants.DeviceType.CPU.value,
        )
        db_session.add(relation)
        db_session.commit()

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        # Delete the OOB controller — should fail due to RESTRICT constraint
        db_session.delete(oob)
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

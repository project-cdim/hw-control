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

"""Integration tests for DeviceRepository read operations.

Tests verify that get_active_resource, get_active_resources, get_active_switch,
and get_active_switches return correct results against an actual PostgreSQL database.
Covers query mechanics including LEFT OUTER JOIN, DISTINCT, OR conditions,
and NULL value handling.
"""

import uuid

import pytest
from pydantic import UUID4
from sqlalchemy.orm import Session

from app.common import basic_exceptions as exc
from app.common import constants
from app.common.device_manager.repository import (
    DeviceRepository,
    ResourceEntity,
    SwitchEntity,
)
from app.common.device_manager.tables import (
    FabricTable,
    FMTable,
    OOBControllerTable,
    PortTable,
    ResourceOOBRelationTable,
    ResourceTable,
    SwitchTable,
)


class TestGetActiveResource:
    """Test DeviceRepository.get_active_resource()."""

    def test_get_active_resource_with_port(self, db_session: Session) -> None:
        """Verify get_active_resource returns resource with port information."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)

        fm = FMTable(fm_manager_id="fm1")
        fabric = FabricTable(fm_manager_id="fm1", fabric_id="fabric1")
        switch = SwitchTable(
            device_id=uuid.uuid4(),
            fm_manager_id="fm1",
            fm_switch_id="switch1",
            serial_number="SN001",
            manufacturer="Vendor1",
            model="Model1",
        )
        resource = ResourceTable(
            device_id=uuid.uuid4(),
            pcie_vendor_id="1234",
            pcie_device_id="5678",
            pcie_device_serial_number="1234567890abcdef",
        )
        port = PortTable(
            fm_manager_id="fm1",
            fm_port_id="port1",
            fabric_id="fabric1",
            fm_switch_id="switch1",
            device_id=resource.device_id,
            switch_port_type="USP",
        )

        db_session.add_all([fm, fabric, switch, resource, port])
        db_session.commit()

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        result = repository.get_active_resource(UUID4(str(resource.device_id)))

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert isinstance(result, ResourceEntity)
        assert result.device_id == resource.device_id

        # Verify port information is included and correctly mapped
        assert len(result.ports) == 1
        assert result.ports[0].fm_manager_id == "fm1"
        assert result.ports[0].fm_port_id == "port1"
        assert result.ports[0].fabric_id == "fabric1"
        assert result.ports[0].fm_switch_id == "switch1"
        assert result.ports[0].switch_port_type == constants.SwitchPortType.USP

        # Verify OOB relations list is empty
        assert len(result.oob_relations) == 0

    def test_get_active_resource_with_oob(self, db_session: Session) -> None:
        """Verify get_active_resource returns resource with OOB information."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        oob = OOBControllerTable(oob_manager_id="oob1")
        resource = ResourceTable(
            device_id=uuid.uuid4(),
            cpu_serial_number="CPU001",
            cpu_manufacturer="TestManufacturer",
            cpu_model="TestModel",
        )
        oob_relation = ResourceOOBRelationTable(
            oob_manager_id="oob1", oob_device_id="oob_dev1", device_id=resource.device_id, device_type="CPU"
        )

        db_session.add_all([oob, resource, oob_relation])
        db_session.commit()

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        result = repository.get_active_resource(UUID4(str(resource.device_id)))

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert isinstance(result, ResourceEntity)
        assert result.device_id == resource.device_id

        # Verify port information is empty
        assert len(result.ports) == 0

        # Verify OOB relations information is included and correctly mapped
        assert len(result.oob_relations) == 1
        assert result.oob_relations[0].oob_manager_id == "oob1"
        assert result.oob_relations[0].oob_device_id == "oob_dev1"
        assert result.oob_relations[0].device_type == constants.DeviceType.CPU

    def test_get_active_resource_with_port_and_oob(self, db_session: Session) -> None:
        """Verify get_active_resource returns resource with both port and OOB information."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        fm = FMTable(fm_manager_id="fm1")
        fabric = FabricTable(fm_manager_id="fm1", fabric_id="fabric1")
        switch = SwitchTable(
            device_id=uuid.uuid4(),
            fm_manager_id="fm1",
            fm_switch_id="switch1",
            serial_number="SN001",
            manufacturer="Vendor1",
            model="Model1",
        )
        oob = OOBControllerTable(oob_manager_id="oob1")
        resource = ResourceTable(
            device_id=uuid.uuid4(),
            pcie_vendor_id="1234",
            pcie_device_id="5678",
            pcie_device_serial_number="1234567890abcdef",
        )
        port = PortTable(
            fm_manager_id="fm1",
            fm_port_id="port1",
            fabric_id="fabric1",
            fm_switch_id="switch1",
            device_id=resource.device_id,
            switch_port_type="USP",
        )
        oob_relation = ResourceOOBRelationTable(
            oob_manager_id="oob1", oob_device_id="oob_dev1", device_id=resource.device_id, device_type="CPU"
        )

        db_session.add_all([fm, fabric, switch, oob, resource, port, oob_relation])
        db_session.commit()

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        result = repository.get_active_resource(UUID4(str(resource.device_id)))

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert isinstance(result, ResourceEntity)
        assert result.device_id == resource.device_id

        # Verify port information is included and correctly mapped
        assert len(result.ports) == 1
        sorted_ports = sorted(result.ports, key=lambda p: p.fm_port_id)
        assert sorted_ports[0].fm_manager_id == "fm1"
        assert sorted_ports[0].fm_port_id == "port1"
        assert sorted_ports[0].fabric_id == "fabric1"
        assert sorted_ports[0].fm_switch_id == "switch1"
        assert sorted_ports[0].switch_port_type == constants.SwitchPortType.USP

        # Verify OOB relations information is included and correctly mapped
        assert len(result.oob_relations) == 1
        sorted_oob_relations = sorted(result.oob_relations, key=lambda r: r.oob_device_id)
        assert sorted_oob_relations[0].oob_manager_id == "oob1"
        assert sorted_oob_relations[0].oob_device_id == "oob_dev1"
        assert sorted_oob_relations[0].device_type == constants.DeviceType.CPU

    def test_get_active_resource_not_found(self, db_session: Session) -> None:
        """Verify get_active_resource raises DeviceNotFoundHWControlError when resource doesn't exist."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        non_existent_id = UUID4(str(uuid.uuid4()))

        # +++++ execution and inspection ++++++++++++++++++++++++++++++#
        with pytest.raises(exc.DeviceNotFoundHWControlError):
            repository.get_active_resource(non_existent_id)

    def test_get_active_resource_inactive(self, db_session: Session) -> None:
        """Verify get_active_resource raises DeviceNotFoundHWControlError for inactive resource."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        # Resource with no ports and no OOB relations is considered inactive
        resource = ResourceTable(
            device_id=uuid.uuid4(),
            pcie_vendor_id="9999",
            pcie_device_id="8888",
            pcie_device_serial_number="deadbeefcafebabe",
        )
        db_session.add(resource)
        db_session.commit()

        # +++++ execution and inspection ++++++++++++++++++++++++++++++#
        with pytest.raises(exc.DeviceNotFoundHWControlError):
            repository.get_active_resource(UUID4(str(resource.device_id)))


class TestGetActiveResources:
    """Test DeviceRepository.get_active_resources()."""

    def test_get_active_resources_returns_all_active(self, db_session: Session) -> None:
        """Verify get_active_resources returns all active resources."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        fm = FMTable(fm_manager_id="fm1")
        fabric = FabricTable(fm_manager_id="fm1", fabric_id="fabric1")
        switch = SwitchTable(
            device_id=uuid.uuid4(),
            fm_manager_id="fm1",
            fm_switch_id="switch1",
            serial_number="SN001",
            manufacturer="Vendor1",
            model="Model1",
        )
        resource1 = ResourceTable(device_id=uuid.uuid4())
        resource2 = ResourceTable(device_id=uuid.uuid4())
        port1 = PortTable(
            fm_manager_id="fm1",
            fm_port_id="port1",
            fabric_id="fabric1",
            fm_switch_id="switch1",
            device_id=resource1.device_id,
            switch_port_type="USP",
        )
        port2 = PortTable(
            fm_manager_id="fm1",
            fm_port_id="port2",
            fabric_id="fabric1",
            fm_switch_id="switch1",
            device_id=resource2.device_id,
            switch_port_type="DSP",
        )

        db_session.add_all([fm, fabric, switch, resource1, resource2, port1, port2])
        db_session.commit()

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        results = repository.get_active_resources()

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert len(results) == 2
        assert all(isinstance(r, ResourceEntity) for r in results)
        device_ids = {r.device_id for r in results}
        assert {resource1.device_id, resource2.device_id} == device_ids

    def test_get_active_resources_returns_empty_when_none(self, db_session: Session) -> None:
        """Verify get_active_resources returns empty list when no active resources exist."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)

        # +++++ execution and inspection ++++++++++++++++++++++++++++++#
        results = repository.get_active_resources()
        assert results == []

    def test_get_active_resources_excludes_inactive_resources(self, db_session: Session) -> None:
        """Verify get_active_resources does not return resources with no ports and no OOB relations."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        fm = FMTable(fm_manager_id="fm1")
        fabric = FabricTable(fm_manager_id="fm1", fabric_id="fabric1")
        switch = SwitchTable(
            device_id=uuid.uuid4(),
            fm_manager_id="fm1",
            fm_switch_id="switch1",
            serial_number="SN001",
            manufacturer="Vendor1",
            model="Model1",
        )
        active_resource = ResourceTable(
            device_id=uuid.uuid4(),
            pcie_vendor_id="AABB",
            pcie_device_id="1234",
            pcie_device_serial_number="0000000000000001",
        )
        inactive_resource = ResourceTable(
            device_id=uuid.uuid4(),
            pcie_vendor_id="AABB",
            pcie_device_id="9999",
            pcie_device_serial_number="deadbeefcafebabe",
        )
        port = PortTable(
            fm_manager_id="fm1",
            fm_port_id="port1",
            fabric_id="fabric1",
            fm_switch_id="switch1",
            device_id=active_resource.device_id,
            switch_port_type="USP",
        )

        db_session.add_all([fm, fabric, switch, active_resource, inactive_resource, port])
        db_session.commit()

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        results = repository.get_active_resources()

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert len(results) == 1
        assert results[0].device_id == active_resource.device_id
        assert inactive_resource.device_id not in {r.device_id for r in results}

    def test_get_active_resources_with_outer_join_includes_unattached_resources(self, db_session: Session) -> None:
        """Verify get_active_resources uses OUTER JOIN to include resources without ports."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        oob = OOBControllerTable(oob_manager_id="oob1")
        resource_with_port = ResourceTable(
            pcie_vendor_id="AABB",
            pcie_device_id="1234",
            pcie_device_serial_number="0000000000000001",
        )
        resource_without_port = ResourceTable(
            pcie_vendor_id="CCDD",
            pcie_device_id="5678",
            pcie_device_serial_number="0000000000000002",
        )
        db_session.add_all([oob, resource_with_port, resource_without_port])
        db_session.flush()

        # Add OOB relations to both
        relation1 = ResourceOOBRelationTable(
            oob_manager_id="oob1",
            oob_device_id="dev1",
            device_id=resource_with_port.device_id,
            device_type=constants.DeviceType.GPU.value,
        )
        relation2 = ResourceOOBRelationTable(
            oob_manager_id="oob1",
            oob_device_id="dev2",
            device_id=resource_without_port.device_id,
            device_type=constants.DeviceType.GPU.value,
        )

        # Add port only to first resource
        fm = FMTable(fm_manager_id="fm1")
        fabric = FabricTable(fm_manager_id="fm1", fabric_id="fab1")
        switch = SwitchTable(
            fm_manager_id="fm1",
            fm_switch_id="sw1",
            serial_number="SN1",
            manufacturer="V1",
            model="M1",
        )
        db_session.add_all([relation1, relation2, fm, fabric, switch])
        db_session.flush()

        port = PortTable(
            fm_manager_id="fm1",
            fm_port_id="port1",
            fabric_id="fab1",
            fm_switch_id="sw1",
            switch_port_type=constants.SwitchPortType.DSP.value,
            device_id=resource_with_port.device_id,
        )
        db_session.add(port)
        db_session.commit()

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        results = repository.get_active_resources()

        # +++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(results) == 2
        device_ids = {r.device_id for r in results}
        assert {resource_with_port.device_id, resource_without_port.device_id} == device_ids

    def test_get_active_resources_distinct_eliminates_duplicates(self, db_session: Session) -> None:
        """Verify get_active_resources uses DISTINCT to avoid duplicate resources."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        oob = OOBControllerTable(oob_manager_id="oob1")
        resource = ResourceTable(
            pcie_vendor_id="AABB",
            pcie_device_id="9999",
            pcie_device_serial_number="0000000000000003",
        )
        db_session.add_all([oob, resource])
        db_session.flush()

        # Add multiple OOB relations
        relation1 = ResourceOOBRelationTable(
            oob_manager_id="oob1",
            oob_device_id="dev1",
            device_id=resource.device_id,
            device_type=constants.DeviceType.GPU.value,
        )
        db_session.add(relation1)

        # Add multiple ports
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
        db_session.flush()

        port1 = PortTable(
            fm_manager_id="fm1",
            fm_port_id="port1",
            fabric_id="fab1",
            fm_switch_id="sw1",
            switch_port_type=constants.SwitchPortType.DSP.value,
            device_id=resource.device_id,
        )
        port2 = PortTable(
            fm_manager_id="fm1",
            fm_port_id="port2",
            fabric_id="fab1",
            fm_switch_id="sw1",
            switch_port_type=constants.SwitchPortType.DSP.value,
            device_id=resource.device_id,
        )
        db_session.add_all([port1, port2])
        db_session.commit()

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        results = repository.get_active_resources()

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert len(results) == 1
        assert results[0].device_id == resource.device_id

    def test_get_active_resources_or_condition_with_ports_or_oob_relations(self, db_session: Session) -> None:
        """Verify get_active_resources uses OR condition (ports OR oob_relations)."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        resource_port_only = ResourceTable(
            pcie_vendor_id="AABB",
            pcie_device_id="1111",
            pcie_device_serial_number="0000000000000004",
        )
        resource_oob_only = ResourceTable(
            pcie_vendor_id="AABB",
            pcie_device_id="2222",
            pcie_device_serial_number="0000000000000005",
        )
        resource_neither = ResourceTable(
            pcie_vendor_id="AABB",
            pcie_device_id="3333",
            pcie_device_serial_number="0000000000000006",
        )
        db_session.add_all([resource_port_only, resource_oob_only, resource_neither])
        db_session.flush()

        # Add port to first resource
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
        db_session.flush()

        port = PortTable(
            fm_manager_id="fm1",
            fm_port_id="port1",
            fabric_id="fab1",
            fm_switch_id="sw1",
            switch_port_type=constants.SwitchPortType.DSP.value,
            device_id=resource_port_only.device_id,
        )
        db_session.add(port)

        # Add OOB relation to second resource
        oob = OOBControllerTable(oob_manager_id="oob1")
        db_session.add(oob)
        db_session.flush()

        relation = ResourceOOBRelationTable(
            oob_manager_id="oob1",
            oob_device_id="dev1",
            device_id=resource_oob_only.device_id,
            device_type=constants.DeviceType.GPU.value,
        )
        db_session.add(relation)
        db_session.commit()

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        results = repository.get_active_resources()

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert len(results) == 2
        device_ids = {r.device_id for r in results}
        assert {resource_port_only.device_id, resource_oob_only.device_id} == device_ids
        assert resource_neither.device_id not in device_ids

    def test_get_active_resources_handles_null_values_in_joins(self, db_session: Session) -> None:
        """Verify get_active_resources correctly handles NULL values in JOIN results."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        oob = OOBControllerTable(oob_manager_id="oob1")
        resource = ResourceTable(
            cpu_serial_number="CPU123",
            cpu_manufacturer="TestManufacturer",
            cpu_model="TestModel",
        )
        db_session.add_all([oob, resource])
        db_session.flush()

        relation = ResourceOOBRelationTable(
            oob_manager_id="oob1",
            oob_device_id="dev1",
            device_id=resource.device_id,
            device_type=constants.DeviceType.CPU.value,
        )
        db_session.add(relation)
        db_session.commit()

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        results = repository.get_active_resources()

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert len(results) == 1
        resource_entity = results[0]
        assert resource_entity.device_id == resource.device_id
        assert len(resource_entity.ports) == 0  # No ports
        assert len(resource_entity.oob_relations) == 1  # Has OOB relation


class TestGetActiveSwitch:
    """Test DeviceRepository.get_active_switch()."""

    def test_get_active_switch_returns_switch_with_fm(self, db_session: Session) -> None:
        """Verify get_active_switch returns switch with FM information."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        fm = FMTable(fm_manager_id="fm1")
        switch = SwitchTable(
            device_id=uuid.uuid4(),
            fm_manager_id="fm1",
            fm_switch_id="switch1",
            serial_number="SN001",
            manufacturer="Vendor1",
            model="Model1",
        )

        db_session.add_all([fm, switch])
        db_session.commit()

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        result = repository.get_active_switch(UUID4(str(switch.device_id)))

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert isinstance(result, SwitchEntity)
        assert result.device_id == switch.device_id
        assert result.fm_manager_id == "fm1"
        assert result.fm_switch_id == "switch1"

    def test_get_active_switch_not_found(self, db_session: Session) -> None:
        """Verify get_active_switch raises exc.DeviceNotFoundHWControlError when switch doesn't exist."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        non_existent_id = UUID4(str(uuid.uuid4()))

        # +++++ execution and inspection ++++++++++++++++++++++++++++++#
        with pytest.raises(exc.DeviceNotFoundHWControlError):
            repository.get_active_switch(non_existent_id)

    def test_get_active_switch_inactive(self, db_session: Session) -> None:
        """Verify get_active_switch raises exc.DeviceNotFoundHWControlError for inactive switch."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        switch = SwitchTable(
            device_id=uuid.uuid4(),
            fm_manager_id=None,
            fm_switch_id=None,
            serial_number="SN001",
            manufacturer="Vendor1",
            model="Model1",
        )
        db_session.add(switch)
        db_session.commit()

        # +++++ execution and inspection ++++++++++++++++++++++++++++++#
        with pytest.raises(exc.DeviceNotFoundHWControlError):
            repository.get_active_switch(UUID4(str(switch.device_id)))


class TestGetActiveSwitches:
    """Test DeviceRepository.get_active_switches()."""

    def test_get_active_switches_returns_all_active(self, db_session: Session) -> None:
        """Verify get_active_switches returns all active switches."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        fm = FMTable(fm_manager_id="fm1")
        switch1 = SwitchTable(
            device_id=uuid.uuid4(),
            fm_manager_id="fm1",
            fm_switch_id="switch1",
            serial_number="SN001",
            manufacturer="Vendor1",
            model="Model1",
        )
        switch2 = SwitchTable(
            device_id=uuid.uuid4(),
            fm_manager_id="fm1",
            fm_switch_id="switch2",
            serial_number="SN002",
            manufacturer="Vendor1",
            model="Model1",
        )
        # Inactive switch
        switch3 = SwitchTable(
            device_id=uuid.uuid4(),
            fm_manager_id=None,
            fm_switch_id=None,
            serial_number="SN003",
            manufacturer="Vendor1",
            model="Model1",
        )

        db_session.add_all([fm, switch1, switch2, switch3])
        db_session.commit()

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        results = repository.get_active_switches()

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert len(results) == 2
        assert all(isinstance(s, SwitchEntity) for s in results)
        device_ids = {s.device_id for s in results}
        assert {switch1.device_id, switch2.device_id} == device_ids

    def test_get_active_switches_returns_empty_when_none(self, db_session: Session) -> None:
        """Verify get_active_switches returns empty list when no active switches exist."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)

        # +++++ execution and inspection ++++++++++++++++++++++++++++++#
        results = repository.get_active_switches()
        assert results == []

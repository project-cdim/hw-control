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

"""Integration tests for DeviceRepository.sync_fm() with actual PostgreSQL database."""

from sqlalchemy.orm import Session

from app.common import constants
from app.common.device_manager.repository import (
    CPUIdentity,
    DeviceRepository,
    FabricSyncModel,
    FMSyncEntry,
    FMSyncModel,
    PCIeIdentity,
    PortSyncModel,
    ResourceSyncModel,
    SwitchIdentity,
    SwitchSyncModel,
)
from app.common.device_manager.tables import (
    FabricTable,
    FMTable,
    PortTable,
    ResourceTable,
    SwitchTable,
)


class TestSyncFM:
    """Test sync_fm functionality with actual database."""

    def test_sync_fm_creates_new_fm_with_fabrics_switches_ports(self, db_session: Session):
        """Verify sync_fm creates FM, fabrics, switches, ports, and resources."""

        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        # Create sync model with complete topology
        fm_sync = FMSyncModel(
            fm_manager_id="fm_test_1",
            fabrics=[
                FabricSyncModel(fabric_id="fabric1"),
                FabricSyncModel(fabric_id="fabric2"),
            ],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN123",
                        switch_manufacturer="Vendor1",
                        switch_model="Model1",
                    ),
                ),
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port1",
                    fabric_id="fabric1",
                    fm_switch_id="sw1",
                    switch_port_type=constants.SwitchPortType.DSP,
                    attached_resource=ResourceSyncModel(
                        pcie_identity=PCIeIdentity(
                            pcie_vendor_id="AABB",
                            pcie_device_id="1234",
                            pcie_device_serial_number="0000000000000001",
                        ),
                    ),
                ),
                PortSyncModel(
                    fm_port_id="port2",
                    fabric_id="fabric2",
                    fm_switch_id="sw1",
                    switch_port_type=constants.SwitchPortType.USP,
                ),
            ],
        )

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        entries = repository.sync_fm(fm_sync)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify FM created
        fm = db_session.query(FMTable).filter_by(fm_manager_id="fm_test_1").one()
        assert fm.fm_manager_id == "fm_test_1"

        # Verify fabrics created
        fabrics = db_session.query(FabricTable).filter_by(fm_manager_id="fm_test_1").all()
        assert len(fabrics) == 2
        fabric_ids = {f.fabric_id for f in fabrics}
        assert fabric_ids == {"fabric1", "fabric2"}

        # Verify switch created
        switches = db_session.query(SwitchTable).filter_by(fm_manager_id="fm_test_1").all()
        assert len(switches) == 1
        switch = switches[0]
        assert switch.fm_switch_id == "sw1"
        assert switch.serial_number == "SN123"
        assert switch.manufacturer == "Vendor1"
        assert switch.model == "Model1"

        # Verify ports created with correct switch_port_type enum values
        ports = db_session.query(PortTable).filter_by(fm_manager_id="fm_test_1").all()
        assert len(ports) == 2
        dsp_port = db_session.query(PortTable).filter_by(fm_port_id="port1").one()
        usp_port = db_session.query(PortTable).filter_by(fm_port_id="port2").one()
        assert dsp_port.switch_port_type == constants.SwitchPortType.DSP.value
        assert usp_port.switch_port_type == constants.SwitchPortType.USP.value

        # Verify resource created and linked to DSP port
        assert dsp_port.device_id is not None
        resource = db_session.query(ResourceTable).filter_by(device_id=dsp_port.device_id).one()
        assert resource.pcie_vendor_id == "aabb"
        assert resource.pcie_device_id == "1234"
        assert resource.pcie_device_serial_number == "0000000000000001"

        # Verify return value: only DSP port (with attached resource) is included
        assert len(entries) == 1
        assert isinstance(entries[0], FMSyncEntry)
        assert entries[0].device_id == dsp_port.device_id
        assert entries[0].fm_port_id == "port1"
        assert entries[0].fabric_id == "fabric1"
        assert entries[0].fm_switch_id == "sw1"
        assert entries[0].switch_port_type == constants.SwitchPortType.DSP

    def test_sync_fm_replaces_existing_fm_topology(self, db_session: Session):
        """Verify sync_fm deletes old FM topology and creates new one."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        # Create initial FM with old topology including ports
        initial_fm = FMSyncModel(
            fm_manager_id="fm_replace",
            fabrics=[FabricSyncModel(fabric_id="old_fabric")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="old_sw",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="OLD_SN",
                        switch_manufacturer="OldVendor",
                        switch_model="OldModel",
                    ),
                ),
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="old_port",
                    fabric_id="old_fabric",
                    fm_switch_id="old_sw",
                    switch_port_type=constants.SwitchPortType.DSP,
                    attached_resource=ResourceSyncModel(
                        pcie_identity=PCIeIdentity(
                            pcie_vendor_id="AABB",
                            pcie_device_id="1234",
                            pcie_device_serial_number="0000000000000001",
                        ),
                    ),
                ),
            ],
        )
        repository.sync_fm(initial_fm)

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Sync with new topology
        new_fm = FMSyncModel(
            fm_manager_id="fm_replace",
            fabrics=[FabricSyncModel(fabric_id="new_fabric")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="new_sw",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="NEW_SN",
                        switch_manufacturer="NewVendor",
                        switch_model="NewModel",
                    ),
                ),
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="new_port",
                    fabric_id="new_fabric",
                    fm_switch_id="new_sw",
                    switch_port_type=constants.SwitchPortType.USP,
                    attached_resource=ResourceSyncModel(
                        pcie_identity=PCIeIdentity(
                            pcie_vendor_id="CCDD",
                            pcie_device_id="5678",
                            pcie_device_serial_number="0000000000000002",
                        ),
                    ),
                ),
            ],
        )
        repository.sync_fm(new_fm)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify old topology deleted
        assert db_session.query(FabricTable).filter_by(fabric_id="old_fabric").count() == 0
        assert db_session.query(PortTable).filter_by(fm_port_id="old_port").count() == 0

        # Verify new topology exists
        assert db_session.query(FabricTable).filter_by(fabric_id="new_fabric").count() == 1
        assert db_session.query(PortTable).filter_by(fm_port_id="new_port").count() == 1

        # Verify FM still exists
        fm = db_session.query(FMTable).filter_by(fm_manager_id="fm_replace").one()
        assert fm.fm_manager_id == "fm_replace"

    def test_sync_fm_upserts_switch_by_physical_identity(self, db_session: Session):
        """Verify sync_fm reuses existing switch when physical identity matches."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        # Create first FM with a switch
        fm1 = FMSyncModel(
            fm_manager_id="fm1",
            fabrics=[],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="fm1_sw_id",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SHARED_SN",
                        switch_manufacturer="SharedVendor",
                        switch_model="SharedModel",
                    ),
                ),
            ],
            ports=[],
        )
        repository.sync_fm(fm1)

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Get the original switch device_id
        original_switch = (
            db_session.query(SwitchTable).filter_by(serial_number="SHARED_SN", manufacturer="SharedVendor").one()
        )
        original_device_id = original_switch.device_id

        # Create second FM referencing the same physical switch
        fm2 = FMSyncModel(
            fm_manager_id="fm2",
            fabrics=[],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="fm2_sw_id",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SHARED_SN",
                        switch_manufacturer="SharedVendor",
                        switch_model="SharedModel",
                    ),
                ),
            ],
            ports=[],
        )
        repository.sync_fm(fm2)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify only one physical switch exists
        all_switches = db_session.query(SwitchTable).filter_by(serial_number="SHARED_SN").all()
        assert len(all_switches) == 1

        # Verify switch was updated with new FM information
        switch = all_switches[0]
        assert switch.device_id == original_device_id  # Same physical device
        assert switch.fm_manager_id == "fm2"  # Updated to fm2
        assert switch.fm_switch_id == "fm2_sw_id"  # Updated to fm2's switch ID

    def test_sync_fm_ensures_resource_by_pcie_identity(self, db_session: Session):
        """Verify sync_fm reuses existing resource when PCIe identity matches."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        # Create a resource via first FM
        fm1 = FMSyncModel(
            fm_manager_id="fm_pcie1",
            fabrics=[FabricSyncModel(fabric_id="f1")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN1", switch_manufacturer="V1", switch_model="M1"
                    ),
                ),
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port1",
                    fabric_id="f1",
                    fm_switch_id="sw1",
                    switch_port_type=constants.SwitchPortType.DSP,
                    attached_resource=ResourceSyncModel(
                        pcie_identity=PCIeIdentity(
                            pcie_vendor_id="ABCD",
                            pcie_device_id="5678",
                            pcie_device_serial_number="1111111111111111",
                        ),
                    ),
                ),
            ],
        )
        repository.sync_fm(fm1)

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Get original resource device_id
        original_resource = (
            db_session.query(ResourceTable)
            .filter_by(pcie_vendor_id="abcd", pcie_device_id="5678", pcie_device_serial_number="1111111111111111")
            .one()
        )
        original_device_id = original_resource.device_id

        # Sync second FM with same PCIe identity on different port
        fm2 = FMSyncModel(
            fm_manager_id="fm_pcie2",
            fabrics=[FabricSyncModel(fabric_id="f2")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw2",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN2", switch_manufacturer="V2", switch_model="M2"
                    ),
                ),
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port2",
                    fabric_id="f2",
                    fm_switch_id="sw2",
                    switch_port_type=constants.SwitchPortType.USP,
                    attached_resource=ResourceSyncModel(
                        pcie_identity=PCIeIdentity(
                            pcie_vendor_id="ABCD",
                            pcie_device_id="5678",
                            pcie_device_serial_number="1111111111111111",
                        ),
                    ),
                ),
            ],
        )
        repository.sync_fm(fm2)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify only one resource exists
        all_resources = db_session.query(ResourceTable).filter_by(pcie_device_serial_number="1111111111111111").all()
        assert len(all_resources) == 1

        # Verify both ports reference the same resource
        port1 = db_session.query(PortTable).filter_by(fm_port_id="port1").one()
        port2 = db_session.query(PortTable).filter_by(fm_port_id="port2").one()
        assert port1.device_id == original_device_id
        assert port2.device_id == original_device_id

    def test_sync_fm_ensures_resource_by_cpu_identity(self, db_session: Session):
        """Verify sync_fm reuses existing resource when CPU identity matches.

        CXL switch USP ports and PCIe switch root complex ports cannot provide
        PCIe serial numbers, so CPU identity is used as the resource key instead.
        """
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        # Create a resource via first FM using CPU identity (e.g. CXL switch USP port)
        fm1 = FMSyncModel(
            fm_manager_id="fm_cpu1",
            fabrics=[FabricSyncModel(fabric_id="f1")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN1", switch_manufacturer="V1", switch_model="M1"
                    ),
                ),
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port1",
                    fabric_id="f1",
                    fm_switch_id="sw1",
                    switch_port_type=constants.SwitchPortType.USP,
                    attached_resource=ResourceSyncModel(
                        cpu_identity=CPUIdentity(
                            cpu_serial_number="SHARED_CPU_SN",
                            cpu_manufacturer="SharedCPUVendor",
                            cpu_model="SharedCPUModel",
                        ),
                    ),
                ),
            ],
        )
        repository.sync_fm(fm1)

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Get original resource device_id
        original_resource = (
            db_session.query(ResourceTable)
            .filter_by(cpu_serial_number="SHARED_CPU_SN", cpu_manufacturer="SharedCPUVendor")
            .one()
        )
        original_device_id = original_resource.device_id

        # Sync second FM with same CPU identity on a different port
        fm2 = FMSyncModel(
            fm_manager_id="fm_cpu2",
            fabrics=[FabricSyncModel(fabric_id="f2")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw2",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN2", switch_manufacturer="V2", switch_model="M2"
                    ),
                ),
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port2",
                    fabric_id="f2",
                    fm_switch_id="sw2",
                    switch_port_type=constants.SwitchPortType.USP,
                    attached_resource=ResourceSyncModel(
                        cpu_identity=CPUIdentity(
                            cpu_serial_number="SHARED_CPU_SN",
                            cpu_manufacturer="SharedCPUVendor",
                            cpu_model="SharedCPUModel",
                        ),
                    ),
                ),
            ],
        )
        repository.sync_fm(fm2)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify only one resource exists
        all_resources = db_session.query(ResourceTable).filter_by(cpu_serial_number="SHARED_CPU_SN").all()
        assert len(all_resources) == 1

        # Verify both ports reference the same resource
        port1 = db_session.query(PortTable).filter_by(fm_port_id="port1").one()
        port2 = db_session.query(PortTable).filter_by(fm_port_id="port2").one()
        assert port1.device_id == original_device_id
        assert port2.device_id == original_device_id

    def test_sync_fm_ensures_resource_by_device_keys(self, db_session: Session):
        """Verify sync_fm reuses existing resource when device_keys match."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        shared_device_keys = {"wwn": "0x5000c50099e8abcd", "model": "SharedStorage"}
        # Create a resource via first FM using device_keys
        fm1 = FMSyncModel(
            fm_manager_id="fm_dkeys1",
            fabrics=[FabricSyncModel(fabric_id="f1")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN1", switch_manufacturer="V1", switch_model="M1"
                    ),
                ),
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port1",
                    fabric_id="f1",
                    fm_switch_id="sw1",
                    switch_port_type=constants.SwitchPortType.DSP,
                    attached_resource=ResourceSyncModel(device_keys=shared_device_keys),
                ),
            ],
        )
        repository.sync_fm(fm1)

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Get original resource device_id
        original_resource = db_session.query(ResourceTable).filter(ResourceTable.device_keys.isnot(None)).one()
        original_device_id = original_resource.device_id

        # Sync second FM with same device_keys on a different port (key order differs)
        fm2 = FMSyncModel(
            fm_manager_id="fm_dkeys2",
            fabrics=[FabricSyncModel(fabric_id="f2")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw2",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN2", switch_manufacturer="V2", switch_model="M2"
                    ),
                ),
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port2",
                    fabric_id="f2",
                    fm_switch_id="sw2",
                    switch_port_type=constants.SwitchPortType.DSP,
                    attached_resource=ResourceSyncModel(
                        device_keys={"model": "SharedStorage", "wwn": "0x5000c50099e8abcd"}  # Different order
                    ),
                ),
            ],
        )
        repository.sync_fm(fm2)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify only one resource exists
        all_resources = db_session.query(ResourceTable).filter(ResourceTable.device_keys.isnot(None)).all()
        assert len(all_resources) == 1

        # Verify both ports reference the same resource
        port1 = db_session.query(PortTable).filter_by(fm_port_id="port1").one()
        port2 = db_session.query(PortTable).filter_by(fm_port_id="port2").one()
        assert port1.device_id == original_device_id
        assert port2.device_id == original_device_id

    def test_sync_fm_multiple_ports_same_new_resource_creates_single_resource(self, db_session: Session):
        """Verify sync_fm deduplicates resources when multiple ports reference the same PCIe identity."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        # Create sync model with 2 ports referencing the SAME new PCIe resource
        same_pcie = PCIeIdentity(
            pcie_vendor_id="AABB",
            pcie_device_id="9999",
            pcie_device_serial_number="0000000000000abc",  # Valid 16-digit hex
        )

        fm_sync = FMSyncModel(
            fm_manager_id="fm_flush_test",
            fabrics=[FabricSyncModel(fabric_id="fab1")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SW_SN1",
                        switch_manufacturer="Vendor",
                        switch_model="Model",
                    ),
                ),
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port1",
                    fabric_id="fab1",
                    fm_switch_id="sw1",
                    switch_port_type=constants.SwitchPortType.DSP,
                    attached_resource=ResourceSyncModel(pcie_identity=same_pcie),
                ),
                PortSyncModel(
                    fm_port_id="port2",
                    fabric_id="fab1",
                    fm_switch_id="sw1",
                    switch_port_type=constants.SwitchPortType.DSP,
                    attached_resource=ResourceSyncModel(pcie_identity=same_pcie),
                ),
            ],
        )

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Synchronize FM (both ports processed in same transaction)
        repository.sync_fm(fm_sync)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify only ONE resource created despite 2 ports referencing it
        resources = (
            db_session.query(ResourceTable)
            .filter_by(
                pcie_vendor_id="aabb",
                pcie_device_id="9999",
                pcie_device_serial_number="0000000000000abc",
            )
            .all()
        )
        assert len(resources) == 1, "Expected single resource, but duplicates were created"

        # Verify both ports reference the same resource
        port1 = db_session.query(PortTable).filter_by(fm_port_id="port1").one()
        port2 = db_session.query(PortTable).filter_by(fm_port_id="port2").one()
        assert port1.device_id == port2.device_id, "Ports should reference the same resource"

    def test_sync_fm_with_ports_succeeds_on_resync(self, db_session: Session):
        """Verify re-syncing FM that has ports and fabrics succeeds.

        Deletion order is Port → Fabric → FM. If Fabric is deleted before Port,
        the port→fabric FK (RESTRICT) would reject the deletion. If FM is deleted
        before Fabric, the fabric→FM FK (RESTRICT) would reject the deletion.
        """
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)

        fm_with_ports = FMSyncModel(
            fm_manager_id="fm_resync",
            fabrics=[FabricSyncModel(fabric_id="fab1")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN001",
                        switch_manufacturer="Vendor1",
                        switch_model="Model1",
                    ),
                ),
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port1",
                    fabric_id="fab1",
                    fm_switch_id="sw1",
                    switch_port_type=constants.SwitchPortType.DSP,
                    attached_resource=ResourceSyncModel(
                        pcie_identity=PCIeIdentity(
                            pcie_vendor_id="AABB",
                            pcie_device_id="1234",
                            pcie_device_serial_number="0000000000000001",
                        ),
                    ),
                ),
            ],
        )

        # First sync succeeds
        repository.sync_fm(fm_with_ports)
        assert db_session.query(PortTable).filter_by(fm_manager_id="fm_resync").count() == 1

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Second sync with same FM succeeds (ports deleted before FM deletion)
        repository.sync_fm(fm_with_ports)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert db_session.query(FMTable).filter_by(fm_manager_id="fm_resync").count() == 1
        assert db_session.query(PortTable).filter_by(fm_manager_id="fm_resync").count() == 1

    def test_sync_fm_fabrics_deleted_on_resync(self, db_session: Session):
        """Verify fabrics are explicitly deleted on re-sync, not via FM CASCADE.

        FabricTable.fm_manager_id uses ondelete=RESTRICT, so fabrics must be
        deleted before FM deletion. This test confirms that re-syncing an FM
        that has fabrics succeeds and old fabrics are removed.
        """
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        fm_sync = FMSyncModel(
            fm_manager_id="fm_fabric_resync",
            fabrics=[FabricSyncModel(fabric_id="old_fab")],
            switches=[],
            ports=[],
        )
        repository.sync_fm(fm_sync)
        assert db_session.query(FabricTable).filter_by(fm_manager_id="fm_fabric_resync").count() == 1

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        fm_sync_new = FMSyncModel(
            fm_manager_id="fm_fabric_resync",
            fabrics=[FabricSyncModel(fabric_id="new_fab")],
            switches=[],
            ports=[],
        )
        repository.sync_fm(fm_sync_new)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert db_session.query(FabricTable).filter_by(fabric_id="old_fab").count() == 0
        assert db_session.query(FabricTable).filter_by(fabric_id="new_fab").count() == 1
        assert db_session.query(FMTable).filter_by(fm_manager_id="fm_fabric_resync").count() == 1

    def test_sync_fm_with_empty_lists(self, db_session: Session):
        """Verify sync_fm with empty fabrics/switches/ports lists."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        fm_sync = FMSyncModel(
            fm_manager_id="fm_empty",
            fabrics=[],
            switches=[],
            ports=[],
        )

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        entries = repository.sync_fm(fm_sync)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify FM exists but no subordinates
        assert db_session.query(FMTable).filter_by(fm_manager_id="fm_empty").count() == 1
        assert db_session.query(SwitchTable).filter_by(fm_manager_id="fm_empty").count() == 0
        assert db_session.query(PortTable).filter_by(fm_manager_id="fm_empty").count() == 0
        assert entries == []

    def test_sync_fm_replace_empty_with_full(self, db_session: Session):
        """Verify replacing empty FM with full topology."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        # Sync an FM with empty topology as initial state
        repository = DeviceRepository(db_session)
        fm_sync_empty = FMSyncModel(
            fm_manager_id="fm1",
            fabrics=[],
            switches=[],
            ports=[],
        )
        repository.sync_fm(fm_sync_empty)

        # Build a full topology model for the replacement
        fm_sync_full = FMSyncModel(
            fm_manager_id="fm1",
            fabrics=[FabricSyncModel(fabric_id="fab1")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN1",
                        switch_manufacturer="V1",
                        switch_model="M1",
                    ),
                )
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port1",
                    fabric_id="fab1",
                    fm_switch_id="sw1",
                    switch_port_type=constants.SwitchPortType.USP,
                )
            ],
        )
        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Replace the empty FM with the full topology
        repository.sync_fm(fm_sync_full)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify full topology is created after replacing empty FM
        assert db_session.query(SwitchTable).filter_by(fm_manager_id="fm1").count() == 1
        assert db_session.query(PortTable).filter_by(fm_manager_id="fm1").count() == 1

    def test_sync_fm_replace_full_with_empty(self, db_session: Session):
        """Verify replacing full FM topology with empty lists."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        # First sync: full topology
        fm_sync_full = FMSyncModel(
            fm_manager_id="fm1",
            fabrics=[FabricSyncModel(fabric_id="fab1")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN1",
                        switch_manufacturer="V1",
                        switch_model="M1",
                    ),
                )
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port1",
                    fabric_id="fab1",
                    fm_switch_id="sw1",
                    switch_port_type=constants.SwitchPortType.DSP,
                    attached_resource=ResourceSyncModel(
                        pcie_identity=PCIeIdentity(
                            pcie_vendor_id="AABB",
                            pcie_device_id="1234",
                            pcie_device_serial_number="0000000000000001",
                        ),
                    ),
                ),
            ],
        )
        repository.sync_fm(fm_sync_full)
        assert db_session.query(PortTable).filter_by(fm_manager_id="fm1").count() == 1

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Second sync: empty
        fm_sync_empty = FMSyncModel(
            fm_manager_id="fm1",
            fabrics=[],
            switches=[],
            ports=[],
        )
        repository.sync_fm(fm_sync_empty)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify topology is cleared but FM still exists
        assert db_session.query(FMTable).filter_by(fm_manager_id="fm1").count() == 1
        assert db_session.query(FabricTable).filter_by(fm_manager_id="fm1").count() == 0
        assert db_session.query(SwitchTable).filter_by(fm_manager_id="fm1").count() == 0
        assert db_session.query(PortTable).filter_by(fm_manager_id="fm1").count() == 0

    def test_switch_reused_when_moved_to_different_fm(self, db_session: Session):
        """Verify switch keeps same device_id when moved between FMs."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        # Register a switch under fm1
        repository = DeviceRepository(db_session)
        fm1_sync = FMSyncModel(
            fm_manager_id="fm1",
            fabrics=[FabricSyncModel(fabric_id="fab1")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="UNIQUE_SN",
                        switch_manufacturer="VendorX",
                        switch_model="ModelY",
                    ),
                )
            ],
            ports=[],
        )
        repository.sync_fm(fm1_sync)

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Record the original device_id, then sync fm2 with the same physical switch identity
        switch1 = db_session.query(SwitchTable).filter_by(fm_manager_id="fm1", fm_switch_id="sw1").one()
        original_device_id = switch1.device_id

        fm2_sync = FMSyncModel(
            fm_manager_id="fm2",
            fabrics=[FabricSyncModel(fabric_id="fab2")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw_new",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="UNIQUE_SN",
                        switch_manufacturer="VendorX",
                        switch_model="ModelY",
                    ),
                )
            ],
            ports=[],
        )
        repository.sync_fm(fm2_sync)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify the switch retains its original device_id after moving to fm2
        switch2 = db_session.query(SwitchTable).filter_by(fm_manager_id="fm2", fm_switch_id="sw_new").one()
        assert switch2.device_id == original_device_id

    def test_orphaned_switch_has_null_fm_manager_id(self, db_session: Session):
        """Verify switch.fm_manager_id and fm_switch_id are NULLed explicitly after sync_fm removes the FM."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        # Register a switch under fm1 and record its device_id
        repository = DeviceRepository(db_session)
        fm_sync = FMSyncModel(
            fm_manager_id="fm1",
            fabrics=[],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN1",
                        switch_manufacturer="V1",
                        switch_model="M1",
                    ),
                )
            ],
            ports=[],
        )
        repository.sync_fm(fm_sync)

        switch = db_session.query(SwitchTable).filter_by(fm_manager_id="fm1").one()
        device_id = switch.device_id

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Re-sync with empty topology: switch is orphaned via explicit NULL update
        repository.sync_fm(FMSyncModel(fm_manager_id="fm1", fabrics=[], switches=[], ports=[]))

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify the orphaned switch has fm_manager_id and fm_switch_id set to NULL
        db_session.expire_all()
        orphaned_switch = db_session.query(SwitchTable).filter_by(device_id=device_id).one()
        assert orphaned_switch.fm_manager_id is None
        assert orphaned_switch.fm_switch_id is None

    def test_sync_fm_commit_persists_data(self, db_session: Session, db_session_factory):
        """Verify sync_fm commits transaction and data persists."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        # Sync an FM with a fabric
        repository = DeviceRepository(db_session)
        fm_sync = FMSyncModel(
            fm_manager_id="fm_commit",
            fabrics=[FabricSyncModel(fabric_id="fab1")],
            switches=[],
            ports=[],
        )
        repository.sync_fm(fm_sync)

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Commit and close the session
        db_session.commit()
        db_session.close()

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify data persists in a new independent session
        new_session = db_session_factory()
        fm = new_session.query(FMTable).filter_by(fm_manager_id="fm_commit").one()
        assert fm.fm_manager_id == "fm_commit"
        fabrics = new_session.query(FabricTable).filter_by(fm_manager_id="fm_commit").all()
        assert len(fabrics) == 1
        new_session.close()

    def test_sync_fm_with_resources_succeeds_on_resync(self, db_session: Session):
        """Verify re-syncing FM that has ports and resources succeeds.

        Existing FM topology (ports, fabrics, FM) is deleted in explicit order
        before re-creation. If CASCADE were relied upon, removing RESTRICT FK
        constraints or reordering would silently break the deletion logic.
        """
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)

        fm_with_resources = FMSyncModel(
            fm_manager_id="fm_resync",
            fabrics=[FabricSyncModel(fabric_id="fab1")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN1",
                        switch_manufacturer="V1",
                        switch_model="M1",
                    ),
                ),
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port1",
                    fabric_id="fab1",
                    fm_switch_id="sw1",
                    switch_port_type=constants.SwitchPortType.DSP,
                    attached_resource=ResourceSyncModel(
                        pcie_identity=PCIeIdentity(
                            pcie_vendor_id="AABB",
                            pcie_device_id="1234",
                            pcie_device_serial_number="0000000000000001",
                        ),
                    ),
                ),
            ],
        )

        # First sync succeeds
        repository.sync_fm(fm_with_resources)
        assert db_session.query(PortTable).filter_by(fm_manager_id="fm_resync").count() == 1

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Second sync with same FM succeeds
        repository.sync_fm(fm_with_resources)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert db_session.query(FMTable).filter_by(fm_manager_id="fm_resync").count() == 1
        assert db_session.query(FabricTable).filter_by(fm_manager_id="fm_resync").count() == 1
        assert db_session.query(PortTable).filter_by(fm_manager_id="fm_resync").count() == 1

    def test_resource_migration_between_fms_fm1_synced_first(self, db_session: Session):
        """Verify device migration from FM 1 to FM 2 when FM 1 is synced first.

        Scenario:
        1. Device is synced as being under FM 1 (connected via a port).
        2. Device physically moves from FM 1's switch to FM 2's switch.
        3. FM 1 is synced (without the device) → device's port under FM 1 is deleted,
           device temporarily has no ports.
        4. FM 2 is synced (with the device) → device gets a port under FM 2.

        Final state: device has exactly one port (under FM 2).
        """
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        device_pcie = PCIeIdentity(
            pcie_vendor_id="AABB",
            pcie_device_id="1234",
            pcie_device_serial_number="0000000000000001",
        )

        # Step 1: Device is synced under FM 1
        repository.sync_fm(
            FMSyncModel(
                fm_manager_id="fm1",
                fabrics=[FabricSyncModel(fabric_id="fab1")],
                switches=[
                    SwitchSyncModel(
                        fm_switch_id="sw1",
                        switch_identity=SwitchIdentity(
                            switch_serial_number="SN_sw1",
                            switch_manufacturer="Vendor",
                            switch_model="Model",
                        ),
                    )
                ],
                ports=[
                    PortSyncModel(
                        fm_port_id="port_fm1",
                        fabric_id="fab1",
                        fm_switch_id="sw1",
                        switch_port_type=constants.SwitchPortType.DSP,
                        attached_resource=ResourceSyncModel(pcie_identity=device_pcie),
                    )
                ],
            )
        )
        device_id = (
            db_session.query(ResourceTable).filter_by(pcie_device_serial_number="0000000000000001").one().device_id
        )
        assert db_session.query(PortTable).filter_by(device_id=device_id).count() == 1

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Step 3: FM 1 synced first (without the device)
        repository.sync_fm(
            FMSyncModel(
                fm_manager_id="fm1",
                fabrics=[FabricSyncModel(fabric_id="fab1")],
                switches=[
                    SwitchSyncModel(
                        fm_switch_id="sw1",
                        switch_identity=SwitchIdentity(
                            switch_serial_number="SN_sw1",
                            switch_manufacturer="Vendor",
                            switch_model="Model",
                        ),
                    )
                ],
                ports=[],
            )
        )
        # Device is temporarily inactive (no ports)
        assert db_session.query(PortTable).filter_by(device_id=device_id).count() == 0

        # Step 4: FM 2 synced with the device
        repository.sync_fm(
            FMSyncModel(
                fm_manager_id="fm2",
                fabrics=[FabricSyncModel(fabric_id="fab2")],
                switches=[
                    SwitchSyncModel(
                        fm_switch_id="sw2",
                        switch_identity=SwitchIdentity(
                            switch_serial_number="SN_sw2",
                            switch_manufacturer="Vendor",
                            switch_model="Model",
                        ),
                    )
                ],
                ports=[
                    PortSyncModel(
                        fm_port_id="port_fm2",
                        fabric_id="fab2",
                        fm_switch_id="sw2",
                        switch_port_type=constants.SwitchPortType.DSP,
                        attached_resource=ResourceSyncModel(pcie_identity=device_pcie),
                    )
                ],
            )
        )

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Device should now have exactly one port under FM 2
        all_ports = db_session.query(PortTable).filter_by(device_id=device_id).all()
        assert len(all_ports) == 1
        assert all_ports[0].fm_manager_id == "fm2"
        assert db_session.query(PortTable).filter_by(fm_manager_id="fm1", device_id=device_id).count() == 0

    def test_resource_migration_between_fms_fm2_synced_first(self, db_session: Session):
        """Verify device migration from FM 1 to FM 2 when FM 2 is synced first.

        Scenario:
        1. Device is synced as being under FM 1 (connected via a port).
        2. Device physically moves from FM 1's switch to FM 2's switch.
        3. FM 2 is synced first (with the device) → device temporarily has ports
           under both FM 1 and FM 2.
        4. FM 1 is synced (without the device) → device's port under FM 1 is deleted.

        During the window between steps 3 and 4, the device appears under both FMs.
        This is the expected system behavior when syncs arrive in reverse order.
        Final state: device has exactly one port (under FM 2).
        """
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        device_pcie = PCIeIdentity(
            pcie_vendor_id="AABB",
            pcie_device_id="1234",
            pcie_device_serial_number="0000000000000001",
        )

        # Step 1: Device is synced under FM 1
        repository.sync_fm(
            FMSyncModel(
                fm_manager_id="fm1",
                fabrics=[FabricSyncModel(fabric_id="fab1")],
                switches=[
                    SwitchSyncModel(
                        fm_switch_id="sw1",
                        switch_identity=SwitchIdentity(
                            switch_serial_number="SN_sw1",
                            switch_manufacturer="Vendor",
                            switch_model="Model",
                        ),
                    )
                ],
                ports=[
                    PortSyncModel(
                        fm_port_id="port_fm1",
                        fabric_id="fab1",
                        fm_switch_id="sw1",
                        switch_port_type=constants.SwitchPortType.DSP,
                        attached_resource=ResourceSyncModel(pcie_identity=device_pcie),
                    )
                ],
            )
        )
        device_id = (
            db_session.query(ResourceTable).filter_by(pcie_device_serial_number="0000000000000001").one().device_id
        )
        assert db_session.query(PortTable).filter_by(device_id=device_id).count() == 1

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Step 3: FM 2 synced first (with the device)
        repository.sync_fm(
            FMSyncModel(
                fm_manager_id="fm2",
                fabrics=[FabricSyncModel(fabric_id="fab2")],
                switches=[
                    SwitchSyncModel(
                        fm_switch_id="sw2",
                        switch_identity=SwitchIdentity(
                            switch_serial_number="SN_sw2",
                            switch_manufacturer="Vendor",
                            switch_model="Model",
                        ),
                    )
                ],
                ports=[
                    PortSyncModel(
                        fm_port_id="port_fm2",
                        fabric_id="fab2",
                        fm_switch_id="sw2",
                        switch_port_type=constants.SwitchPortType.DSP,
                        attached_resource=ResourceSyncModel(pcie_identity=device_pcie),
                    )
                ],
            )
        )
        # Device is temporarily under both FM 1 and FM 2
        assert db_session.query(PortTable).filter_by(device_id=device_id).count() == 2

        # Step 4: FM 1 synced (without the device)
        repository.sync_fm(
            FMSyncModel(
                fm_manager_id="fm1",
                fabrics=[FabricSyncModel(fabric_id="fab1")],
                switches=[
                    SwitchSyncModel(
                        fm_switch_id="sw1",
                        switch_identity=SwitchIdentity(
                            switch_serial_number="SN_sw1",
                            switch_manufacturer="Vendor",
                            switch_model="Model",
                        ),
                    )
                ],
                ports=[],
            )
        )

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Device should now have exactly one port under FM 2
        all_ports = db_session.query(PortTable).filter_by(device_id=device_id).all()
        assert len(all_ports) == 1
        assert all_ports[0].fm_manager_id == "fm2"
        assert db_session.query(PortTable).filter_by(fm_manager_id="fm1", device_id=device_id).count() == 0

    def test_sync_fm_resource_persists_after_port_removal(self, db_session: Session):
        """Verify resource record is retained even after all FM ports are removed.

        The resource table has an independent lifecycle from FM topology.
        A resource created via sync_fm must remain in the DB after the port
        is removed by a subsequent sync_fm (empty ports), so that the device_id
        continues to identify the same physical device on the next sync.
        """
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        fm_with_resource = FMSyncModel(
            fm_manager_id="fm1",
            fabrics=[FabricSyncModel(fabric_id="fab1")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN1", switch_manufacturer="V1", switch_model="M1"
                    ),
                )
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port1",
                    fabric_id="fab1",
                    fm_switch_id="sw1",
                    switch_port_type=constants.SwitchPortType.DSP,
                    attached_resource=ResourceSyncModel(
                        pcie_identity=PCIeIdentity(
                            pcie_vendor_id="AABB",
                            pcie_device_id="1234",
                            pcie_device_serial_number="0000000000000001",
                        ),
                    ),
                )
            ],
        )
        repository.sync_fm(fm_with_resource)

        original_resource = (
            db_session.query(ResourceTable).filter_by(pcie_device_serial_number="0000000000000001").one()
        )
        original_device_id = original_resource.device_id

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Re-sync without ports (port is deleted)
        repository.sync_fm(FMSyncModel(fm_manager_id="fm1", fabrics=[], switches=[], ports=[]))

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Port is removed but resource record must still exist
        assert db_session.query(PortTable).filter_by(fm_manager_id="fm1").count() == 0
        assert db_session.query(ResourceTable).filter_by(device_id=original_device_id).count() == 1

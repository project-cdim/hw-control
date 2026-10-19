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

"""Integration tests for DeviceRepository.sync_oob() with actual PostgreSQL database."""

import json

from sqlalchemy.orm import Session

from app.common import constants
from app.common.device_manager.repository import (
    CPUIdentity,
    DeviceRepository,
    OOBResourceSyncModel,
    OOBSyncEntry,
    OOBSyncModel,
    PCIeIdentity,
)
from app.common.device_manager.tables import (
    OOBControllerTable,
    ResourceOOBRelationTable,
    ResourceTable,
)


class TestSyncOOB:
    """Test sync_oob functionality with actual database."""

    def test_sync_oob_creates_new_oob_with_resources(self, db_session: Session):
        """Verify sync_oob creates OOB controller and resource relations."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        # Create OOB sync model with devices
        oob_sync = OOBSyncModel(
            oob_manager_id="oob1",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="oob_dev1",
                    device_type=constants.DeviceType.CPU,
                    cpu_identity=CPUIdentity(
                        cpu_serial_number="CPU_SN_001",
                        cpu_manufacturer="TestManufacturer",
                        cpu_model="TestModel",
                    ),
                ),
                OOBResourceSyncModel(
                    oob_device_id="oob_dev2",
                    device_type=constants.DeviceType.GPU,
                    pcie_identity=PCIeIdentity(
                        pcie_vendor_id="CCDD",
                        pcie_device_id="1234",
                        pcie_device_serial_number="2222222222222222",
                    ),
                ),
            ],
        )

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        entries = repository.sync_oob(oob_sync)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify OOB controller created
        oob = db_session.query(OOBControllerTable).filter_by(oob_manager_id="oob1").one()
        assert oob.oob_manager_id == "oob1"

        # Verify Resources created
        cpu_resource = (
            db_session.query(ResourceTable)
            .filter_by(cpu_serial_number="CPU_SN_001", cpu_manufacturer="TestManufacturer")
            .one()
        )
        gpu_resource = db_session.query(ResourceTable).filter_by(pcie_device_serial_number="2222222222222222").one()

        # Verify Resource-OOB relations created
        relations = db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob1").all()
        assert len(relations) == 2

        relation_dict = {r.oob_device_id: r for r in relations}
        assert relation_dict["oob_dev1"].device_id == cpu_resource.device_id
        assert relation_dict["oob_dev1"].device_type == constants.DeviceType.CPU.value
        assert relation_dict["oob_dev2"].device_id == gpu_resource.device_id
        assert relation_dict["oob_dev2"].device_type == constants.DeviceType.GPU.value

        # Verify return value
        assert len(entries) == 2
        assert all(isinstance(e, OOBSyncEntry) for e in entries)
        entry_dict = {e.oob_device_id: e for e in entries}
        assert entry_dict["oob_dev1"].device_id == cpu_resource.device_id
        assert entry_dict["oob_dev1"].device_type == constants.DeviceType.CPU
        assert entry_dict["oob_dev2"].device_id == gpu_resource.device_id
        assert entry_dict["oob_dev2"].device_type == constants.DeviceType.GPU

    def test_sync_oob_replaces_existing_oob_relations(self, db_session: Session):
        """Verify sync_oob deletes old OOB relations and creates new ones."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        # Create initial OOB with old devices
        initial_oob = OOBSyncModel(
            oob_manager_id="oob_replace",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="old_dev",
                    device_type=constants.DeviceType.CPU,
                    cpu_identity=CPUIdentity(
                        cpu_serial_number="OLD_CPU",
                        cpu_manufacturer="OldCPU",
                        cpu_model="OldModel",
                    ),
                ),
            ],
        )
        repository.sync_oob(initial_oob)

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Sync with new devices
        new_oob = OOBSyncModel(
            oob_manager_id="oob_replace",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="new_dev",
                    device_type=constants.DeviceType.GPU,
                    pcie_identity=PCIeIdentity(
                        pcie_vendor_id="CCDD",
                        pcie_device_id="9999",
                        pcie_device_serial_number="3333333333333333",
                    ),
                ),
            ],
        )
        repository.sync_oob(new_oob)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify old relation deleted
        old_relations = db_session.query(ResourceOOBRelationTable).filter_by(oob_device_id="old_dev").all()
        assert len(old_relations) == 0

        # Verify new relation exists
        new_relations = db_session.query(ResourceOOBRelationTable).filter_by(oob_device_id="new_dev").all()
        assert len(new_relations) == 1
        assert new_relations[0].device_type == constants.DeviceType.GPU.value

        # Verify OOB controller still exists
        oob = db_session.query(OOBControllerTable).filter_by(oob_manager_id="oob_replace").one()
        assert oob.oob_manager_id == "oob_replace"

    def test_sync_oob_reuses_resource_by_cpu_identity(self, db_session: Session):
        """Verify sync_oob reuses existing resource when CPU identity matches."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        # Register a resource via first OOB using CPU identity
        repository = DeviceRepository(db_session)
        oob1 = OOBSyncModel(
            oob_manager_id="oob_cpu1",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="dev1",
                    device_type=constants.DeviceType.CPU,
                    cpu_identity=CPUIdentity(
                        cpu_serial_number="SHARED_CPU_SN",
                        cpu_manufacturer="TestManufacturer",
                        cpu_model="TestModel",
                    ),
                ),
            ],
        )
        repository.sync_oob(oob1)

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Get original resource device_id
        original_resource = (
            db_session.query(ResourceTable)
            .filter_by(cpu_serial_number="SHARED_CPU_SN", cpu_manufacturer="TestManufacturer")
            .one()
        )
        original_device_id = original_resource.device_id

        # Sync second OOB with same CPU identity
        oob2 = OOBSyncModel(
            oob_manager_id="oob_cpu2",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="dev2",
                    device_type=constants.DeviceType.CPU,
                    cpu_identity=CPUIdentity(
                        cpu_serial_number="SHARED_CPU_SN",
                        cpu_manufacturer="TestManufacturer",
                        cpu_model="TestModel",
                    ),
                ),
            ],
        )
        repository.sync_oob(oob2)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify only one resource exists
        all_resources = db_session.query(ResourceTable).filter_by(cpu_serial_number="SHARED_CPU_SN").all()
        assert len(all_resources) == 1

        # Verify both OOB relations reference the same resource
        relation1 = (
            db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob_cpu1", oob_device_id="dev1").one()
        )
        relation2 = (
            db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob_cpu2", oob_device_id="dev2").one()
        )
        assert relation1.device_id == original_device_id
        assert relation2.device_id == original_device_id

    def test_sync_oob_reuses_resource_by_device_keys(self, db_session: Session):
        """Verify sync_oob reuses existing resource when device_keys match."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        # Create a resource with device_keys via first OOB
        oob1 = OOBSyncModel(
            oob_manager_id="oob_keys1",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="keys_dev1",
                    device_type=constants.DeviceType.STORAGE,
                    device_keys={"wwn": "0x5000c50099e8a123", "model": "Samsung_SSD"},
                ),
            ],
        )
        repository.sync_oob(oob1)

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Get original resource device_id
        original_resource = db_session.query(ResourceTable).filter(ResourceTable.device_keys.isnot(None)).one()
        original_device_id = original_resource.device_id

        # Sync second OOB with same device_keys
        oob2 = OOBSyncModel(
            oob_manager_id="oob_keys2",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="keys_dev2",
                    device_type=constants.DeviceType.STORAGE,
                    device_keys={"model": "Samsung_SSD", "wwn": "0x5000c50099e8a123"},  # Different order
                ),
            ],
        )
        repository.sync_oob(oob2)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify only one resource exists
        all_resources = db_session.query(ResourceTable).filter(ResourceTable.device_keys.isnot(None)).all()
        assert len(all_resources) == 1

        # Verify both OOB relations reference the same resource
        relation1 = (
            db_session.query(ResourceOOBRelationTable)
            .filter_by(oob_manager_id="oob_keys1", oob_device_id="keys_dev1")
            .one()
        )
        relation2 = (
            db_session.query(ResourceOOBRelationTable)
            .filter_by(oob_manager_id="oob_keys2", oob_device_id="keys_dev2")
            .one()
        )
        assert relation1.device_id == original_device_id
        assert relation2.device_id == original_device_id

    def test_sync_oob_reuses_resource_by_pcie_identity(self, db_session: Session):
        """Verify sync_oob reuses existing resource when PCIe identity matches."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        # Create first OOB with resource
        oob1 = OOBSyncModel(
            oob_manager_id="oob1",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="dev1",
                    device_type=constants.DeviceType.GPU,
                    pcie_identity=PCIeIdentity(
                        pcie_vendor_id="CCDD",
                        pcie_device_id="9999",
                        pcie_device_serial_number="3333333333333333",
                    ),
                )
            ],
        )
        repository.sync_oob(oob1)

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        original_resource = (
            db_session.query(ResourceTable).filter_by(pcie_device_serial_number="3333333333333333").one()
        )
        original_device_id = original_resource.device_id

        # Sync second OOB with same PCIe identity
        oob2 = OOBSyncModel(
            oob_manager_id="oob2",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="dev2",
                    device_type=constants.DeviceType.GPU,
                    pcie_identity=PCIeIdentity(
                        pcie_vendor_id="CCDD",
                        pcie_device_id="9999",
                        pcie_device_serial_number="3333333333333333",
                    ),
                )
            ],
        )
        repository.sync_oob(oob2)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify only one resource exists
        all_resources = db_session.query(ResourceTable).filter_by(pcie_device_serial_number="3333333333333333").all()
        assert len(all_resources) == 1
        assert all_resources[0].device_id == original_device_id

        # Verify both OOB relations reference the same resource
        relations = db_session.query(ResourceOOBRelationTable).filter_by(device_id=original_device_id).all()
        assert len(relations) == 2
        oob_ids = {r.oob_manager_id for r in relations}
        assert oob_ids == {"oob1", "oob2"}

    def test_sync_oob_with_resources_succeeds_on_resync(self, db_session: Session):
        """Verify re-syncing OOB that has resource relations succeeds.

        ResourceOOBRelation records are explicitly deleted before OOBController deletion.
        If this order is violated or CASCADE is relied upon, the FK constraint would reject
        the OOBController deletion while relations still exist.
        """
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)

        oob_with_resources = OOBSyncModel(
            oob_manager_id="oob_resync",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="dev1",
                    device_type=constants.DeviceType.GPU,
                    pcie_identity=PCIeIdentity(
                        pcie_vendor_id="AABB",
                        pcie_device_id="1234",
                        pcie_device_serial_number="0000000000000001",
                    ),
                ),
            ],
        )

        # First sync succeeds
        repository.sync_oob(oob_with_resources)
        assert db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob_resync").count() == 1

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Second sync with same OOB succeeds
        repository.sync_oob(oob_with_resources)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert db_session.query(OOBControllerTable).filter_by(oob_manager_id="oob_resync").count() == 1
        assert db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob_resync").count() == 1

    def test_sync_oob_relations_deleted_before_controller_on_resync(self, db_session: Session):
        """Verify ResourceOOBRelation is explicitly deleted before OOBController deletion.

        ResourceOOBRelationTable.oob_manager_id uses ondelete=RESTRICT, so relations
        must be deleted before OOBController deletion. This test confirms that
        re-syncing an OOB with relations succeeds and old relations are removed.
        """
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        oob_with_relations = OOBSyncModel(
            oob_manager_id="oob_explicit_del",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="dev1",
                    device_type=constants.DeviceType.GPU,
                    pcie_identity=PCIeIdentity(
                        pcie_vendor_id="AABB",
                        pcie_device_id="1234",
                        pcie_device_serial_number="0000000000000002",
                    ),
                ),
            ],
        )
        repository.sync_oob(oob_with_relations)
        assert db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob_explicit_del").count() == 1

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        oob_new_device = OOBSyncModel(
            oob_manager_id="oob_explicit_del",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="dev2",
                    device_type=constants.DeviceType.CPU,
                    cpu_identity=CPUIdentity(
                        cpu_serial_number="NEW_CPU",
                        cpu_manufacturer="NewVendor",
                        cpu_model="NewModel",
                    ),
                ),
            ],
        )
        repository.sync_oob(oob_new_device)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        assert db_session.query(ResourceOOBRelationTable).filter_by(oob_device_id="dev1").count() == 0
        assert db_session.query(ResourceOOBRelationTable).filter_by(oob_device_id="dev2").count() == 1
        assert db_session.query(OOBControllerTable).filter_by(oob_manager_id="oob_explicit_del").count() == 1

    def test_sync_oob_with_empty_devices(self, db_session: Session):
        """Verify sync_oob with empty devices list."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        # Create an OOB sync model with no devices
        repository = DeviceRepository(db_session)
        oob_sync = OOBSyncModel(
            oob_manager_id="oob_empty",
            devices=[],
        )

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        entries = repository.sync_oob(oob_sync)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify OOB controller exists but no resources were created
        assert db_session.query(OOBControllerTable).filter_by(oob_manager_id="oob_empty").count() == 1
        assert db_session.query(ResourceTable).count() == 0
        assert entries == []

    def test_sync_oob_replace_empty_with_full(self, db_session: Session):
        """Verify replacing empty OOB with full device list."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        # Sync an OOB with empty device list as initial state
        repository = DeviceRepository(db_session)
        oob_sync_empty = OOBSyncModel(
            oob_manager_id="oob1",
            devices=[],
        )
        repository.sync_oob(oob_sync_empty)
        assert db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob1").count() == 0

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Replace the empty OOB with a full device list
        oob_sync_full = OOBSyncModel(
            oob_manager_id="oob1",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="dev1",
                    device_type=constants.DeviceType.GPU,
                    pcie_identity=PCIeIdentity(
                        pcie_vendor_id="AABB",
                        pcie_device_id="1234",
                        pcie_device_serial_number="0000000000000001",
                    ),
                ),
            ],
        )
        repository.sync_oob(oob_sync_full)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify OOB controller and relation exist after replacement
        assert db_session.query(OOBControllerTable).filter_by(oob_manager_id="oob1").count() == 1
        assert db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob1").count() == 1

    def test_sync_oob_replace_full_with_empty(self, db_session: Session):
        """Verify replacing full OOB device list with empty."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        # Sync an OOB with one device as initial state
        repository = DeviceRepository(db_session)
        oob_sync_full = OOBSyncModel(
            oob_manager_id="oob1",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="dev1",
                    device_type=constants.DeviceType.GPU,
                    pcie_identity=PCIeIdentity(
                        pcie_vendor_id="AABB",
                        pcie_device_id="1234",
                        pcie_device_serial_number="0000000000000001",
                    ),
                ),
            ],
        )
        repository.sync_oob(oob_sync_full)
        assert db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob1").count() == 1

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Replace the full OOB with an empty device list
        oob_sync_empty = OOBSyncModel(
            oob_manager_id="oob1",
            devices=[],
        )
        repository.sync_oob(oob_sync_empty)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify OOB controller still exists but relation was removed
        assert db_session.query(OOBControllerTable).filter_by(oob_manager_id="oob1").count() == 1
        assert db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob1").count() == 0

    def test_sync_oob_resource_persists_after_device_removal(self, db_session: Session):
        """Verify resource record is retained even after all OOB devices are removed.

        The resource table has an independent lifecycle from OOB relations.
        A resource created via sync_oob must remain in the DB after the
        resource_oob_relation is removed by a subsequent sync_oob (empty devices),
        so that the device_id continues to identify the same physical device
        on the next sync.
        """
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        oob_with_device = OOBSyncModel(
            oob_manager_id="oob1",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="dev1",
                    device_type=constants.DeviceType.GPU,
                    pcie_identity=PCIeIdentity(
                        pcie_vendor_id="AABB",
                        pcie_device_id="1234",
                        pcie_device_serial_number="0000000000000001",
                    ),
                ),
            ],
        )
        repository.sync_oob(oob_with_device)

        original_resource = (
            db_session.query(ResourceTable).filter_by(pcie_device_serial_number="0000000000000001").one()
        )
        original_device_id = original_resource.device_id

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Re-sync without devices (resource_oob_relation is deleted)
        repository.sync_oob(OOBSyncModel(oob_manager_id="oob1", devices=[]))

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Relation is removed but resource record must still exist
        assert db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob1").count() == 0
        assert db_session.query(ResourceTable).filter_by(device_id=original_device_id).count() == 1

    def test_device_keys_with_special_characters(self, db_session: Session):
        """Verify device_keys handles special characters correctly."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        # Create an OOB with device_keys containing special characters
        repository = DeviceRepository(db_session)
        oob = OOBSyncModel(
            oob_manager_id="oob_special",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="dev_special",
                    device_type=constants.DeviceType.STORAGE,
                    device_keys={
                        "serial": "SN-123_ABC@456",
                        "path": "/dev/disk/by-id/wwn-0x5000c50012345678",
                        "special": "key with spaces & symbols: #!$%",
                    },
                )
            ],
        )

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        repository.sync_oob(oob)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify device_keys are stored and retrieved with special characters intact
        relations = db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob_special").all()
        assert len(relations) == 1
        resource = db_session.query(ResourceTable).filter_by(device_id=relations[0].device_id).one()
        assert resource.device_keys is not None
        device_keys = json.loads(resource.device_keys)
        assert device_keys["serial"] == "SN-123_ABC@456"
        assert device_keys["path"] == "/dev/disk/by-id/wwn-0x5000c50012345678"
        assert device_keys["special"] == "key with spaces & symbols: #!$%"

    def test_sync_oob_commit_persists_data(self, db_session: Session, db_session_factory):
        """Verify sync_oob commits transaction and data persists."""
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        # Sync an OOB with one device
        repository = DeviceRepository(db_session)
        oob_sync = OOBSyncModel(
            oob_manager_id="oob_commit",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="dev1",
                    device_type=constants.DeviceType.GPU,
                    pcie_identity=PCIeIdentity(
                        pcie_vendor_id="CCDD",
                        pcie_device_id="1111",
                        pcie_device_serial_number="4444444444444444",
                    ),
                )
            ],
        )
        repository.sync_oob(oob_sync)

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Commit and close the session
        db_session.commit()
        db_session.close()

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify data persists in a new independent session
        new_session = db_session_factory()
        oob = new_session.query(OOBControllerTable).filter_by(oob_manager_id="oob_commit").one()
        assert oob.oob_manager_id == "oob_commit"
        relations = new_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob_commit").all()
        assert len(relations) == 1
        new_session.close()

    def test_resource_migration_between_oobs_oob1_synced_first(self, db_session: Session):
        """Verify device migration from OOB 1 to OOB 2 when OOB 1 is synced first.

        Scenario:
        1. Device is synced as being under OOB 1.
        2. Device physically moves from OOB 1 to OOB 2.
        3. OOB 1 is synced (without the device) → device becomes temporarily inactive.
        4. OOB 2 is synced (with the device) → device is active under OOB 2 only.

        Final state: device has exactly one OOB relation (to OOB 2).
        """
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        device_pcie = PCIeIdentity(
            pcie_vendor_id="AABB",
            pcie_device_id="1234",
            pcie_device_serial_number="0000000000000001",
        )
        # Step 1: Device is synced under OOB 1
        repository.sync_oob(
            OOBSyncModel(
                oob_manager_id="oob1",
                devices=[
                    OOBResourceSyncModel(
                        oob_device_id="dev1",
                        device_type=constants.DeviceType.GPU,
                        pcie_identity=device_pcie,
                    ),
                ],
            )
        )
        device_id = (
            db_session.query(ResourceTable).filter_by(pcie_device_serial_number="0000000000000001").one().device_id
        )
        assert db_session.query(ResourceOOBRelationTable).filter_by(device_id=device_id).count() == 1

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Step 3: OOB 1 synced first (without the device)
        repository.sync_oob(OOBSyncModel(oob_manager_id="oob1", devices=[]))
        # Device is temporarily inactive (no OOB relations)
        assert db_session.query(ResourceOOBRelationTable).filter_by(device_id=device_id).count() == 0

        # Step 4: OOB 2 synced with the device
        repository.sync_oob(
            OOBSyncModel(
                oob_manager_id="oob2",
                devices=[
                    OOBResourceSyncModel(
                        oob_device_id="dev1",
                        device_type=constants.DeviceType.GPU,
                        pcie_identity=device_pcie,
                    ),
                ],
            )
        )

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Device should now be under OOB 2 only
        all_relations = db_session.query(ResourceOOBRelationTable).filter_by(device_id=device_id).all()
        assert len(all_relations) == 1
        assert all_relations[0].oob_manager_id == "oob2"
        assert db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob1").count() == 0

    def test_resource_migration_between_oobs_oob2_synced_first(self, db_session: Session):
        """Verify device migration from OOB 1 to OOB 2 when OOB 2 is synced first.

        Scenario:
        1. Device is synced as being under OOB 1.
        2. Device physically moves from OOB 1 to OOB 2.
        3. OOB 2 is synced first (with the device) → device is temporarily under both OOBs.
        4. OOB 1 is synced (without the device) → device is active under OOB 2 only.

        During the window between steps 3 and 4, the device appears under both OOBs.
        This is the expected system behavior when syncs arrive in reverse order.
        Final state: device has exactly one OOB relation (to OOB 2).
        """
        # +++++ preparation +++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(db_session)
        device_pcie = PCIeIdentity(
            pcie_vendor_id="AABB",
            pcie_device_id="1234",
            pcie_device_serial_number="0000000000000001",
        )
        # Step 1: Device is synced under OOB 1
        repository.sync_oob(
            OOBSyncModel(
                oob_manager_id="oob1",
                devices=[
                    OOBResourceSyncModel(
                        oob_device_id="dev1",
                        device_type=constants.DeviceType.GPU,
                        pcie_identity=device_pcie,
                    ),
                ],
            )
        )
        device_id = (
            db_session.query(ResourceTable).filter_by(pcie_device_serial_number="0000000000000001").one().device_id
        )
        assert db_session.query(ResourceOOBRelationTable).filter_by(device_id=device_id).count() == 1

        # +++++ execution +++++++++++++++++++++++++++++++++++++++++++++#
        # Step 3: OOB 2 synced first (with the device)
        repository.sync_oob(
            OOBSyncModel(
                oob_manager_id="oob2",
                devices=[
                    OOBResourceSyncModel(
                        oob_device_id="dev1",
                        device_type=constants.DeviceType.GPU,
                        pcie_identity=device_pcie,
                    ),
                ],
            )
        )
        # Device is temporarily under both OOBs
        assert db_session.query(ResourceOOBRelationTable).filter_by(device_id=device_id).count() == 2

        # Step 4: OOB 1 synced (without the device)
        repository.sync_oob(OOBSyncModel(oob_manager_id="oob1", devices=[]))

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Device should now be under OOB 2 only
        all_relations = db_session.query(ResourceOOBRelationTable).filter_by(device_id=device_id).all()
        assert len(all_relations) == 1
        assert all_relations[0].oob_manager_id == "oob2"
        assert db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob1").count() == 0

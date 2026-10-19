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

"""Integration tests for FM and OOB sync correlation in DeviceRepository with actual PostgreSQL database."""

from pydantic import UUID4
from sqlalchemy.orm import Session

from app.common import constants
from app.common.device_manager.repository import (
    CPUIdentity,
    DeviceRepository,
    FabricSyncModel,
    FMSyncModel,
    OOBResourceSyncModel,
    OOBSyncModel,
    PCIeIdentity,
    PortSyncModel,
    ResourceEntity,
    ResourceSyncModel,
    SwitchIdentity,
    SwitchSyncModel,
)
from app.common.device_manager.tables import (
    PortTable,
    ResourceOOBRelationTable,
    ResourceTable,
)


class TestFMOOBCorrelation:
    """Test that FM-synced and OOB-synced device data are correctly correlated in the database.

    Verifies that a resource registered via sync_fm() and sync_oob() with the same
    physical identity shares a single device_id, so that both port (FM) and OOB
    relation data are accessible together via get_active_resource().
    """

    def test_pcie_resource_correlated_after_fm_then_oob_sync(self, db_session: Session):
        """Verify FM port and OOB relation are correlated via PCIe identity (FM sync first).

        When sync_fm registers a device via port and sync_oob registers the same
        physical device via OOB with identical PCIe identity, both should share
        the same device_id and be retrievable together via get_active_resource().
        """
        repository = DeviceRepository(db_session)

        # +++++ preparation: Sync FM +++++++++++++++++++++++++++++++++#
        fm_sync = FMSyncModel(
            fm_manager_id="fm1",
            fabrics=[FabricSyncModel(fabric_id="fab1")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN1",
                        switch_manufacturer="Vendor1",
                        switch_model="Model1",
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
        repository.sync_fm(fm_sync)

        # +++++ execution: Sync OOB with same PCIe identity +++++++++++#
        oob_sync = OOBSyncModel(
            oob_manager_id="oob1",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="oob_dev1",
                    device_type=constants.DeviceType.GPU,
                    pcie_identity=PCIeIdentity(
                        pcie_vendor_id="AABB",
                        pcie_device_id="1234",
                        pcie_device_serial_number="0000000000000001",
                    ),
                )
            ],
        )
        repository.sync_oob(oob_sync)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify only one resource exists (FM and OOB correlated to same device)
        all_resources = db_session.query(ResourceTable).all()
        assert len(all_resources) == 1
        device_id = all_resources[0].device_id

        # Verify both port and OOB relation reference the same device_id
        port = db_session.query(PortTable).filter_by(fm_port_id="port1").one()
        assert port.device_id == device_id
        oob_relation = db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob1").one()
        assert oob_relation.device_id == device_id

        # Verify get_active_resource returns both port and OOB relation
        result = repository.get_active_resource(UUID4(str(device_id)))
        assert isinstance(result, ResourceEntity)
        assert len(result.ports) == 1
        assert result.ports[0].fm_port_id == "port1"
        assert len(result.oob_relations) == 1
        assert result.oob_relations[0].oob_manager_id == "oob1"

    def test_pcie_resource_correlated_after_oob_then_fm_sync(self, db_session: Session):
        """Verify FM port and OOB relation are correlated via PCIe identity (OOB sync first).

        The correlation must work regardless of which sync runs first.
        """
        repository = DeviceRepository(db_session)

        # +++++ preparation: Sync OOB first +++++++++++++++++++++++++++#
        oob_sync = OOBSyncModel(
            oob_manager_id="oob1",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="oob_dev1",
                    device_type=constants.DeviceType.GPU,
                    pcie_identity=PCIeIdentity(
                        pcie_vendor_id="AABB",
                        pcie_device_id="1234",
                        pcie_device_serial_number="0000000000000001",
                    ),
                )
            ],
        )
        repository.sync_oob(oob_sync)

        # +++++ execution: Sync FM with same PCIe identity ++++++++++++#
        fm_sync = FMSyncModel(
            fm_manager_id="fm1",
            fabrics=[FabricSyncModel(fabric_id="fab1")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN1",
                        switch_manufacturer="Vendor1",
                        switch_model="Model1",
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
        repository.sync_fm(fm_sync)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        all_resources = db_session.query(ResourceTable).all()
        assert len(all_resources) == 1
        device_id = all_resources[0].device_id

        port = db_session.query(PortTable).filter_by(fm_port_id="port1").one()
        assert port.device_id == device_id
        oob_relation = db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob1").one()
        assert oob_relation.device_id == device_id

        result = repository.get_active_resource(UUID4(str(device_id)))
        assert isinstance(result, ResourceEntity)
        assert len(result.ports) == 1
        assert result.ports[0].fm_port_id == "port1"
        assert len(result.oob_relations) == 1
        assert result.oob_relations[0].oob_manager_id == "oob1"

    def test_cpu_resource_correlated_after_fm_then_oob_sync(self, db_session: Session):
        """Verify FM port and OOB relation are correlated via CPU identity (FM sync first).

        CPU identity is used for CXL switch USP ports and PCIe switch root complex
        ports that cannot provide PCIe serial numbers.
        """
        repository = DeviceRepository(db_session)

        # +++++ preparation: Sync FM +++++++++++++++++++++++++++++++++#
        fm_sync = FMSyncModel(
            fm_manager_id="fm1",
            fabrics=[FabricSyncModel(fabric_id="fab1")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN1",
                        switch_manufacturer="Vendor1",
                        switch_model="Model1",
                    ),
                )
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port1",
                    fabric_id="fab1",
                    fm_switch_id="sw1",
                    switch_port_type=constants.SwitchPortType.USP,
                    attached_resource=ResourceSyncModel(
                        cpu_identity=CPUIdentity(
                            cpu_serial_number="CPU_SN_001",
                            cpu_manufacturer="CPUVendor",
                            cpu_model="CPUModel",
                        ),
                    ),
                )
            ],
        )
        repository.sync_fm(fm_sync)

        # +++++ execution: Sync OOB with same CPU identity ++++++++++++#
        oob_sync = OOBSyncModel(
            oob_manager_id="oob1",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="oob_dev1",
                    device_type=constants.DeviceType.CPU,
                    cpu_identity=CPUIdentity(
                        cpu_serial_number="CPU_SN_001",
                        cpu_manufacturer="CPUVendor",
                        cpu_model="CPUModel",
                    ),
                )
            ],
        )
        repository.sync_oob(oob_sync)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        all_resources = db_session.query(ResourceTable).all()
        assert len(all_resources) == 1
        device_id = all_resources[0].device_id

        port = db_session.query(PortTable).filter_by(fm_port_id="port1").one()
        assert port.device_id == device_id
        oob_relation = db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob1").one()
        assert oob_relation.device_id == device_id

        result = repository.get_active_resource(UUID4(str(device_id)))
        assert isinstance(result, ResourceEntity)
        assert len(result.ports) == 1
        assert result.ports[0].fm_port_id == "port1"
        assert len(result.oob_relations) == 1
        assert result.oob_relations[0].oob_manager_id == "oob1"

    def test_cpu_resource_correlated_after_oob_then_fm_sync(self, db_session: Session):
        """Verify FM port and OOB relation are correlated via CPU identity (OOB sync first).

        The correlation must work regardless of which sync runs first.
        """
        repository = DeviceRepository(db_session)

        # +++++ preparation: Sync OOB first +++++++++++++++++++++++++++#
        oob_sync = OOBSyncModel(
            oob_manager_id="oob1",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="oob_dev1",
                    device_type=constants.DeviceType.CPU,
                    cpu_identity=CPUIdentity(
                        cpu_serial_number="CPU_SN_001",
                        cpu_manufacturer="CPUVendor",
                        cpu_model="CPUModel",
                    ),
                )
            ],
        )
        repository.sync_oob(oob_sync)

        # +++++ execution: Sync FM with same CPU identity +++++++++++++++#
        fm_sync = FMSyncModel(
            fm_manager_id="fm1",
            fabrics=[FabricSyncModel(fabric_id="fab1")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN1",
                        switch_manufacturer="Vendor1",
                        switch_model="Model1",
                    ),
                )
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port1",
                    fabric_id="fab1",
                    fm_switch_id="sw1",
                    switch_port_type=constants.SwitchPortType.USP,
                    attached_resource=ResourceSyncModel(
                        cpu_identity=CPUIdentity(
                            cpu_serial_number="CPU_SN_001",
                            cpu_manufacturer="CPUVendor",
                            cpu_model="CPUModel",
                        ),
                    ),
                )
            ],
        )
        repository.sync_fm(fm_sync)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        all_resources = db_session.query(ResourceTable).all()
        assert len(all_resources) == 1
        device_id = all_resources[0].device_id

        port = db_session.query(PortTable).filter_by(fm_port_id="port1").one()
        assert port.device_id == device_id
        oob_relation = db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob1").one()
        assert oob_relation.device_id == device_id

        result = repository.get_active_resource(UUID4(str(device_id)))
        assert isinstance(result, ResourceEntity)
        assert len(result.ports) == 1
        assert result.ports[0].fm_port_id == "port1"
        assert len(result.oob_relations) == 1
        assert result.oob_relations[0].oob_manager_id == "oob1"

    def test_device_keys_resource_correlated_after_fm_then_oob_sync(self, db_session: Session):
        """Verify FM port and OOB relation are correlated via device_keys (FM sync first).

        device_keys is used for devices that lack both PCIe serial number and CPU identity,
        such as storage devices identified only by vendor-specific key-value attributes.
        The correlation must work even when the key order in the dict differs between syncs.
        """
        repository = DeviceRepository(db_session)
        shared_device_keys = {"wwn": "0x5000c50099e8abcd", "model": "SharedStorage"}

        # +++++ preparation: Sync FM +++++++++++++++++++++++++++++++++#
        fm_sync = FMSyncModel(
            fm_manager_id="fm1",
            fabrics=[FabricSyncModel(fabric_id="fab1")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN1",
                        switch_manufacturer="Vendor1",
                        switch_model="Model1",
                    ),
                )
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port1",
                    fabric_id="fab1",
                    fm_switch_id="sw1",
                    switch_port_type=constants.SwitchPortType.DSP,
                    attached_resource=ResourceSyncModel(device_keys=shared_device_keys),
                )
            ],
        )
        repository.sync_fm(fm_sync)

        # +++++ execution: Sync OOB with same device_keys +++++++++++++#
        oob_sync = OOBSyncModel(
            oob_manager_id="oob1",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="oob_dev1",
                    device_type=constants.DeviceType.STORAGE,
                    device_keys={"model": "SharedStorage", "wwn": "0x5000c50099e8abcd"},  # Different key order
                )
            ],
        )
        repository.sync_oob(oob_sync)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        all_resources = db_session.query(ResourceTable).all()
        assert len(all_resources) == 1
        device_id = all_resources[0].device_id

        port = db_session.query(PortTable).filter_by(fm_port_id="port1").one()
        assert port.device_id == device_id
        oob_relation = db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob1").one()
        assert oob_relation.device_id == device_id

        result = repository.get_active_resource(UUID4(str(device_id)))
        assert isinstance(result, ResourceEntity)
        assert len(result.ports) == 1
        assert result.ports[0].fm_port_id == "port1"
        assert len(result.oob_relations) == 1
        assert result.oob_relations[0].oob_manager_id == "oob1"

    def test_device_keys_resource_correlated_after_oob_then_fm_sync(self, db_session: Session):
        """Verify FM port and OOB relation are correlated via device_keys (OOB sync first).

        The correlation must work regardless of which sync runs first.
        Key order in the dict must not affect correlation.
        """
        repository = DeviceRepository(db_session)
        shared_device_keys = {"wwn": "0x5000c50099e8abcd", "model": "SharedStorage"}

        # +++++ preparation: Sync OOB first +++++++++++++++++++++++++++#
        oob_sync = OOBSyncModel(
            oob_manager_id="oob1",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="oob_dev1",
                    device_type=constants.DeviceType.STORAGE,
                    device_keys=shared_device_keys,
                )
            ],
        )
        repository.sync_oob(oob_sync)

        # +++++ execution: Sync FM with same device_keys +++++++++++++++#
        fm_sync = FMSyncModel(
            fm_manager_id="fm1",
            fabrics=[FabricSyncModel(fabric_id="fab1")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN1",
                        switch_manufacturer="Vendor1",
                        switch_model="Model1",
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
                        device_keys={"model": "SharedStorage", "wwn": "0x5000c50099e8abcd"},  # Different key order
                    ),
                )
            ],
        )
        repository.sync_fm(fm_sync)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify only one resource exists (OOB and FM correlated to same device)
        all_resources = db_session.query(ResourceTable).all()
        assert len(all_resources) == 1
        device_id = all_resources[0].device_id

        port = db_session.query(PortTable).filter_by(fm_port_id="port1").one()
        assert port.device_id == device_id
        oob_relation = db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob1").one()
        assert oob_relation.device_id == device_id

    def test_resource_correlated_across_multiple_fms(self, db_session: Session):
        """Verify one resource shared across multiple FMs is correctly correlated with OOB.

        When the same physical device is connected to two different FM switches,
        sync_fm registers ports from each FM. A subsequent sync_oob with the same
        identity must correlate to the same device_id, and get_active_resource()
        must return all FM ports together with the OOB relation.
        """
        repository = DeviceRepository(db_session)
        shared_pcie = PCIeIdentity(
            pcie_vendor_id="AABB",
            pcie_device_id="1234",
            pcie_device_serial_number="0000000000000001",
        )

        # +++++ preparation: FM1 sync +++++++++++++++++++++++++++++++++#
        fm1_sync = FMSyncModel(
            fm_manager_id="fm1",
            fabrics=[FabricSyncModel(fabric_id="fab1")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN1",
                        switch_manufacturer="Vendor1",
                        switch_model="Model1",
                    ),
                )
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port_fm1",
                    fabric_id="fab1",
                    fm_switch_id="sw1",
                    switch_port_type=constants.SwitchPortType.DSP,
                    attached_resource=ResourceSyncModel(pcie_identity=shared_pcie),
                )
            ],
        )
        repository.sync_fm(fm1_sync)

        # +++++ execution: FM2 sync with same PCIe identity ++++++++++++#
        fm2_sync = FMSyncModel(
            fm_manager_id="fm2",
            fabrics=[FabricSyncModel(fabric_id="fab2")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw2",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN2",
                        switch_manufacturer="Vendor2",
                        switch_model="Model2",
                    ),
                )
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port_fm2",
                    fabric_id="fab2",
                    fm_switch_id="sw2",
                    switch_port_type=constants.SwitchPortType.DSP,
                    attached_resource=ResourceSyncModel(pcie_identity=shared_pcie),
                )
            ],
        )
        repository.sync_fm(fm2_sync)

        # OOB sync with same PCIe identity
        oob_sync = OOBSyncModel(
            oob_manager_id="oob1",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="oob_dev1",
                    device_type=constants.DeviceType.GPU,
                    pcie_identity=shared_pcie,
                )
            ],
        )
        repository.sync_oob(oob_sync)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify only one resource exists
        all_resources = db_session.query(ResourceTable).all()
        assert len(all_resources) == 1
        device_id = all_resources[0].device_id

        # Verify both FM ports reference the same device
        port_fm1 = db_session.query(PortTable).filter_by(fm_port_id="port_fm1").one()
        port_fm2 = db_session.query(PortTable).filter_by(fm_port_id="port_fm2").one()
        assert port_fm1.device_id == device_id
        assert port_fm2.device_id == device_id

        # Verify OOB relation references the same device
        oob_relation = db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob1").one()
        assert oob_relation.device_id == device_id

        # Verify get_active_resource returns all ports and OOB relation
        result = repository.get_active_resource(UUID4(str(device_id)))
        assert isinstance(result, ResourceEntity)
        port_ids = {p.fm_port_id for p in result.ports}
        assert port_ids == {"port_fm1", "port_fm2"}
        assert len(result.oob_relations) == 1
        assert result.oob_relations[0].oob_manager_id == "oob1"

    def test_resource_correlated_across_multiple_oob_controllers(self, db_session: Session):
        """Verify one resource shared across multiple OOB controllers is correctly correlated with FM.

        When the same physical device is managed by two different OOB controllers,
        sync_oob registers relations from each OOB. A prior sync_fm with the same
        identity must share the same device_id, and get_active_resource() must return
        the FM port together with all OOB relations.
        """
        repository = DeviceRepository(db_session)
        shared_pcie = PCIeIdentity(
            pcie_vendor_id="CCDD",
            pcie_device_id="5678",
            pcie_device_serial_number="2222222222222222",
        )

        # +++++ preparation: FM sync ++++++++++++++++++++++++++++++++++#
        fm_sync = FMSyncModel(
            fm_manager_id="fm1",
            fabrics=[FabricSyncModel(fabric_id="fab1")],
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN1",
                        switch_manufacturer="Vendor1",
                        switch_model="Model1",
                    ),
                )
            ],
            ports=[
                PortSyncModel(
                    fm_port_id="port1",
                    fabric_id="fab1",
                    fm_switch_id="sw1",
                    switch_port_type=constants.SwitchPortType.DSP,
                    attached_resource=ResourceSyncModel(pcie_identity=shared_pcie),
                )
            ],
        )
        repository.sync_fm(fm_sync)

        # +++++ execution: OOB1 and OOB2 sync with same PCIe identity ++#
        oob1_sync = OOBSyncModel(
            oob_manager_id="oob1",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="oob1_dev1",
                    device_type=constants.DeviceType.GPU,
                    pcie_identity=shared_pcie,
                )
            ],
        )
        repository.sync_oob(oob1_sync)

        oob2_sync = OOBSyncModel(
            oob_manager_id="oob2",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="oob2_dev1",
                    device_type=constants.DeviceType.GPU,
                    pcie_identity=shared_pcie,
                )
            ],
        )
        repository.sync_oob(oob2_sync)

        # +++++ inspection ++++++++++++++++++++++++++++++++++++++++++++#
        # Verify only one resource exists
        all_resources = db_session.query(ResourceTable).all()
        assert len(all_resources) == 1
        device_id = all_resources[0].device_id

        # Verify FM port references the same device
        port = db_session.query(PortTable).filter_by(fm_port_id="port1").one()
        assert port.device_id == device_id

        # Verify both OOB relations reference the same device
        oob1_relation = db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob1").one()
        oob2_relation = db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id="oob2").one()
        assert oob1_relation.device_id == device_id
        assert oob2_relation.device_id == device_id

        # Verify get_active_resource returns FM port and all OOB relations
        result = repository.get_active_resource(UUID4(str(device_id)))
        assert isinstance(result, ResourceEntity)
        assert len(result.ports) == 1
        assert result.ports[0].fm_port_id == "port1"
        oob_ids = {r.oob_manager_id for r in result.oob_relations}
        assert oob_ids == {"oob1", "oob2"}

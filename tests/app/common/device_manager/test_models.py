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

"""Unit tests for Device Repository model classes.

This module tests Pydantic model validation for identity, entity, and sync models
defined in the device repository module.
"""

import uuid

import pytest
from pydantic import ValidationError

from app.common.constants import DeviceType, SwitchPortType
from app.common.device_manager.repository import (
    BaseSyncModel,
    CPUIdentity,
    EntityBaseModel,
    FabricSyncModel,
    FMSyncModel,
    OOBResourceSyncModel,
    OOBSyncModel,
    PCIeIdentity,
    PortEntity,
    PortSyncModel,
    ResourceEntity,
    ResourceOOBRelation,
    ResourceSyncModel,
    SwitchEntity,
    SwitchIdentity,
    SwitchSyncModel,
)
from app.common.device_manager.tables import (
    PortTable,
    ResourceOOBRelationTable,
    ResourceTable,
    SwitchTable,
)


class TestPCIeIdentity:
    """Tests for PCIeIdentity model."""

    def test_valid_identity(self) -> None:
        """Verifies that PCIeIdentity accepts valid hex field values."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        identity = PCIeIdentity(
            pcie_vendor_id="1234",
            pcie_device_id="5678",
            pcie_device_serial_number="0123456789abcdef",
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#

        assert identity.pcie_vendor_id == "1234"
        assert identity.pcie_device_id == "5678"
        assert identity.pcie_device_serial_number == "0123456789abcdef"

    def test_valid_uppercase_hex_normalized_to_lowercase(self) -> None:
        """Verifies that uppercase hex digits in PCIeIdentity fields are normalized to lowercase."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        identity = PCIeIdentity(
            pcie_vendor_id="ABCD",
            pcie_device_id="EF01",
            pcie_device_serial_number="0123456789ABCDEF",
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#

        assert identity.pcie_vendor_id == "abcd"
        assert identity.pcie_device_id == "ef01"
        assert identity.pcie_device_serial_number == "0123456789abcdef"

    @pytest.mark.parametrize(
        "kwargs",
        [
            # pcie_vendor_id is 3 digits (too short; must be exactly 4)
            pytest.param(
                {"pcie_vendor_id": "123", "pcie_device_id": "5678", "pcie_device_serial_number": "0123456789abcdef"},
                id="vendor_id_too_short",
            ),
            # pcie_vendor_id is 5 digits (too long; must be exactly 4)
            pytest.param(
                {"pcie_vendor_id": "12345", "pcie_device_id": "5678", "pcie_device_serial_number": "0123456789abcdef"},
                id="vendor_id_too_long",
            ),
            # pcie_vendor_id contains non-hex characters
            pytest.param(
                {"pcie_vendor_id": "GHIJ", "pcie_device_id": "5678", "pcie_device_serial_number": "0123456789abcdef"},
                id="vendor_id_non_hex",
            ),
            # pcie_device_id is 3 digits (too short; must be exactly 4)
            pytest.param(
                {"pcie_vendor_id": "1234", "pcie_device_id": "567", "pcie_device_serial_number": "0123456789abcdef"},
                id="device_id_too_short",
            ),
            # pcie_device_serial_number is 15 digits (too short; must be exactly 16)
            pytest.param(
                {"pcie_vendor_id": "1234", "pcie_device_id": "5678", "pcie_device_serial_number": "0123456789abcde"},
                id="serial_number_too_short",
            ),
            # pcie_device_serial_number is 17 digits (too long; must be exactly 16)
            pytest.param(
                {"pcie_vendor_id": "1234", "pcie_device_id": "5678", "pcie_device_serial_number": "0123456789abcdef0"},
                id="serial_number_too_long",
            ),
            # pcie_vendor_id is an integer (int is not accepted for str fields in Pydantic v2)
            pytest.param(
                {"pcie_vendor_id": 1234, "pcie_device_id": "5678", "pcie_device_serial_number": "0123456789abcdef"},
                id="vendor_id_int",
            ),
            # pcie_vendor_id is None (None is not accepted for a required str field)
            pytest.param(
                {"pcie_vendor_id": None, "pcie_device_id": "5678", "pcie_device_serial_number": "0123456789abcdef"},
                id="vendor_id_none",
            ),
            # pcie_device_serial_number is a list (list is not accepted for str fields)
            pytest.param(
                {"pcie_vendor_id": "1234", "pcie_device_id": "5678", "pcie_device_serial_number": ["0123456789abcdef"]},
                id="serial_number_list",
            ),
        ],
    )
    def test_invalid_field_raises_validation_error(self, kwargs: dict) -> None:
        """Verifies that PCIeIdentity raises ValidationError for invalid field values or types."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            PCIeIdentity(**kwargs)

    @pytest.mark.parametrize(
        "kwargs",
        [
            # pcie_vendor_id is absent
            pytest.param(
                {"pcie_device_id": "5678", "pcie_device_serial_number": "0123456789abcdef"}, id="vendor_id_missing"
            ),
            # pcie_device_id is absent
            pytest.param(
                {"pcie_vendor_id": "1234", "pcie_device_serial_number": "0123456789abcdef"}, id="device_id_missing"
            ),
            # pcie_device_serial_number is absent
            pytest.param({"pcie_vendor_id": "1234", "pcie_device_id": "5678"}, id="serial_number_missing"),
        ],
    )
    def test_missing_required_field_raises_validation_error(self, kwargs: dict) -> None:
        """Verifies that PCIeIdentity raises ValidationError when a required field is absent."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            PCIeIdentity(**kwargs)


class TestCPUIdentity:
    """Tests for CPUIdentity model."""

    def test_valid_identity(self) -> None:
        """Verifies that CPUIdentity accepts valid field values."""
        identity = CPUIdentity(
            cpu_serial_number="SN12345",
            cpu_manufacturer="example_manufacturer",
            cpu_model="example_model",
        )
        assert identity.cpu_serial_number == "SN12345"
        assert identity.cpu_manufacturer == "example_manufacturer"
        assert identity.cpu_model == "example_model"

    @pytest.mark.parametrize(
        "kwargs",
        [
            # cpu_serial_number is an integer (int is not accepted for str fields in Pydantic v2)
            pytest.param(
                {"cpu_serial_number": 12345, "cpu_manufacturer": "example_manufacturer", "cpu_model": "example_model"},
                id="serial_number_int",
            ),
            # cpu_serial_number is None (None is not accepted for a required str field)
            pytest.param(
                {"cpu_serial_number": None, "cpu_manufacturer": "example_manufacturer", "cpu_model": "example_model"},
                id="serial_number_none",
            ),
            # cpu_manufacturer is a list (list is not accepted for str fields)
            pytest.param(
                {
                    "cpu_serial_number": "SN12345",
                    "cpu_manufacturer": ["example_manufacturer"],
                    "cpu_model": "example_model",
                },
                id="manufacturer_list",
            ),
            # cpu_serial_number is an empty string (min_length=1 rejects empty strings)
            pytest.param(
                {"cpu_serial_number": "", "cpu_manufacturer": "example_manufacturer", "cpu_model": "example_model"},
                id="serial_number_empty",
            ),
            # cpu_manufacturer is an empty string (min_length=1 rejects empty strings)
            pytest.param(
                {"cpu_serial_number": "SN12345", "cpu_manufacturer": "", "cpu_model": "example_model"},
                id="manufacturer_empty",
            ),
            # cpu_model is an empty string (min_length=1 rejects empty strings)
            pytest.param(
                {"cpu_serial_number": "SN12345", "cpu_manufacturer": "example_manufacturer", "cpu_model": ""},
                id="model_empty",
            ),
        ],
    )
    def test_invalid_field_raises_validation_error(self, kwargs: dict) -> None:
        """Verifies that CPUIdentity raises ValidationError for fields with invalid types."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            CPUIdentity(**kwargs)

    @pytest.mark.parametrize(
        "kwargs",
        [
            # cpu_serial_number is absent
            pytest.param(
                {"cpu_manufacturer": "example_manufacturer", "cpu_model": "example_model"}, id="serial_number_missing"
            ),
            # cpu_manufacturer is absent
            pytest.param({"cpu_serial_number": "SN12345", "cpu_model": "example_model"}, id="manufacturer_missing"),
            # cpu_model is absent
            pytest.param(
                {"cpu_serial_number": "SN12345", "cpu_manufacturer": "example_manufacturer"}, id="model_missing"
            ),
        ],
    )
    def test_missing_required_field_raises_validation_error(self, kwargs: dict) -> None:
        """Verifies that CPUIdentity raises ValidationError when a required field is absent."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            CPUIdentity(**kwargs)


class TestSwitchIdentity:
    """Tests for SwitchIdentity model."""

    def test_valid_identity(self) -> None:
        """Verifies that SwitchIdentity accepts valid field values."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        identity = SwitchIdentity(
            switch_serial_number="SW-001",
            switch_manufacturer="example_manufacturer",
            switch_model="example_model",
        )
        assert identity.switch_serial_number == "SW-001"
        assert identity.switch_manufacturer == "example_manufacturer"
        assert identity.switch_model == "example_model"

    @pytest.mark.parametrize(
        "kwargs",
        [
            # switch_serial_number is an integer (int is not accepted for str fields in Pydantic v2)
            pytest.param(
                {
                    "switch_serial_number": 1,
                    "switch_manufacturer": "example_manufacturer",
                    "switch_model": "example_model",
                },
                id="serial_number_int",
            ),
            # switch_serial_number is None (None is not accepted for a required str field)
            pytest.param(
                {
                    "switch_serial_number": None,
                    "switch_manufacturer": "example_manufacturer",
                    "switch_model": "example_model",
                },
                id="serial_number_none",
            ),
            # switch_model is a list (list is not accepted for str fields)
            pytest.param(
                {
                    "switch_serial_number": "SW-001",
                    "switch_manufacturer": "example_manufacturer",
                    "switch_model": ["example_model"],
                },
                id="model_list",
            ),
            # switch_serial_number is an empty string (min_length=1 rejects empty strings)
            pytest.param(
                {
                    "switch_serial_number": "",
                    "switch_manufacturer": "example_manufacturer",
                    "switch_model": "example_model",
                },
                id="serial_number_empty",
            ),
            # switch_manufacturer is an empty string (min_length=1 rejects empty strings)
            pytest.param(
                {
                    "switch_serial_number": "SW-001",
                    "switch_manufacturer": "",
                    "switch_model": "example_model",
                },
                id="manufacturer_empty",
            ),
            # switch_model is an empty string (min_length=1 rejects empty strings)
            pytest.param(
                {
                    "switch_serial_number": "SW-001",
                    "switch_manufacturer": "example_manufacturer",
                    "switch_model": "",
                },
                id="model_empty",
            ),
        ],
    )
    def test_invalid_field_raises_validation_error(self, kwargs: dict) -> None:
        """Verifies that SwitchIdentity raises ValidationError for fields with invalid types."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            SwitchIdentity(**kwargs)

    @pytest.mark.parametrize(
        "kwargs",
        [
            # switch_serial_number is absent
            pytest.param(
                {"switch_manufacturer": "example_manufacturer", "switch_model": "example_model"},
                id="serial_number_missing",
            ),
            # switch_manufacturer is absent
            pytest.param(
                {"switch_serial_number": "SW-001", "switch_model": "example_model"}, id="manufacturer_missing"
            ),
            # switch_model is absent
            pytest.param(
                {"switch_serial_number": "SW-001", "switch_manufacturer": "example_manufacturer"}, id="model_missing"
            ),
        ],
    )
    def test_missing_required_field_raises_validation_error(self, kwargs: dict) -> None:
        """Verifies that SwitchIdentity raises ValidationError when a required field is absent."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            SwitchIdentity(**kwargs)


class TestEntityBaseModel:
    """Tests for EntityBaseModel configuration shared by all entity model subclasses."""

    class _ConcreteEntityModel(EntityBaseModel):
        """Minimal concrete subclass for testing EntityBaseModel behavior."""

        name: str

    @pytest.mark.parametrize(
        "model_class",
        [
            pytest.param(PortEntity, id="PortEntity"),
            pytest.param(ResourceOOBRelation, id="ResourceOOBRelation"),
            pytest.param(ResourceEntity, id="ResourceEntity"),
            pytest.param(SwitchEntity, id="SwitchEntity"),
        ],
    )
    def test_inherits_entity_base_model(self, model_class: type) -> None:
        """Verifies that all Entity classes inherit from EntityBaseModel."""
        assert issubclass(model_class, EntityBaseModel)


class TestPortEntity:
    """Tests for PortEntity model."""

    @pytest.mark.parametrize(
        "switch_port_type",
        [
            pytest.param(SwitchPortType.USP, id="usp"),
            pytest.param(SwitchPortType.DSP, id="dsp"),
        ],
    )
    def test_valid_entity(self, switch_port_type: SwitchPortType) -> None:
        """Verifies that PortEntity accepts valid inputs for each switch port type."""
        entity = PortEntity(
            fm_manager_id="fm-001",
            fm_port_id="port-001",
            fabric_id="fabric-001",
            switch_port_type=switch_port_type,
            fm_switch_id="switch-001",
        )
        assert entity.fm_manager_id == "fm-001"
        assert entity.switch_port_type == switch_port_type

    @pytest.mark.parametrize(
        "kwargs",
        [
            # fm_manager_id is an integer (int is not accepted for str fields in Pydantic v2)
            pytest.param(
                {
                    "fm_manager_id": 1,
                    "fm_port_id": "port-001",
                    "fabric_id": "fabric-001",
                    "switch_port_type": SwitchPortType.USP,
                    "fm_switch_id": "switch-001",
                },
                id="manager_id_int",
            ),
            # fm_manager_id is None (None is not accepted for a required str field)
            pytest.param(
                {
                    "fm_manager_id": None,
                    "fm_port_id": "port-001",
                    "fabric_id": "fabric-001",
                    "switch_port_type": SwitchPortType.USP,
                    "fm_switch_id": "switch-001",
                },
                id="manager_id_none",
            ),
            # switch_port_type is an unrecognized string (not a valid SwitchPortType value)
            pytest.param(
                {
                    "fm_manager_id": "fm-001",
                    "fm_port_id": "port-001",
                    "fabric_id": "fabric-001",
                    "switch_port_type": "INVALID_PORT_TYPE",
                    "fm_switch_id": "switch-001",
                },
                id="port_type_invalid_str",
            ),
            # switch_port_type is None (None is not accepted for a required enum field)
            pytest.param(
                {
                    "fm_manager_id": "fm-001",
                    "fm_port_id": "port-001",
                    "fabric_id": "fabric-001",
                    "switch_port_type": None,
                    "fm_switch_id": "switch-001",
                },
                id="port_type_none",
            ),
        ],
    )
    def test_invalid_field_raises_validation_error(self, kwargs: dict) -> None:
        """Verifies that PortEntity raises ValidationError for fields with invalid types."""
        with pytest.raises(ValidationError):
            PortEntity(**kwargs)

    def test_model_validate_from_table_row(self) -> None:
        """Verifies that PortEntity.model_validate() reads all fields correctly from a PortTable row."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        row = PortTable(
            fm_manager_id="fm-001",
            fm_port_id="port-001",
            fabric_id="fabric-001",
            switch_port_type=SwitchPortType.USP.value,
            fm_switch_id="switch-001",
        )

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#

        entity = PortEntity.model_validate(row)

        assert entity.fm_manager_id == "fm-001"
        assert entity.fm_port_id == "port-001"
        assert entity.fabric_id == "fabric-001"
        assert entity.switch_port_type == SwitchPortType.USP
        assert entity.fm_switch_id == "switch-001"


class TestResourceOOBRelation:
    """Tests for ResourceOOBRelation model."""

    @pytest.mark.parametrize(
        "device_type",
        [
            pytest.param(DeviceType.CPU, id="cpu"),
            pytest.param(DeviceType.MEMORY, id="memory"),
            pytest.param(DeviceType.GPU, id="gpu"),
        ],
    )
    def test_valid_relation(self, device_type: DeviceType) -> None:
        """Verifies that ResourceOOBRelation accepts valid inputs for each device type."""
        relation = ResourceOOBRelation(
            oob_manager_id="oob-001",
            oob_device_id="dev-001",
            device_type=device_type,
        )
        assert relation.oob_manager_id == "oob-001"
        assert relation.device_type == device_type

    @pytest.mark.parametrize(
        "kwargs",
        [
            # oob_manager_id is an integer (int is not accepted for str fields in Pydantic v2)
            pytest.param(
                {"oob_manager_id": 1, "oob_device_id": "dev-001", "device_type": DeviceType.CPU},
                id="manager_id_int",
            ),
            # oob_manager_id is None (None is not accepted for a required str field)
            pytest.param(
                {"oob_manager_id": None, "oob_device_id": "dev-001", "device_type": DeviceType.CPU},
                id="manager_id_none",
            ),
            # device_type is an unrecognized string (not a valid DeviceType value)
            pytest.param(
                {"oob_manager_id": "oob-001", "oob_device_id": "dev-001", "device_type": "INVALID_DEVICE_TYPE"},
                id="device_type_invalid_str",
            ),
            # device_type is None (None is not accepted for a required enum field)
            pytest.param(
                {"oob_manager_id": "oob-001", "oob_device_id": "dev-001", "device_type": None},
                id="device_type_none",
            ),
        ],
    )
    def test_invalid_field_raises_validation_error(self, kwargs: dict) -> None:
        """Verifies that ResourceOOBRelation raises ValidationError for fields with invalid types."""
        with pytest.raises(ValidationError):
            ResourceOOBRelation(**kwargs)

    def test_model_validate_from_table_row(self) -> None:
        """Test model validation from ResourceOOBRelationTable row.

        Verifies that ResourceOOBRelation.model_validate() correctly reads all
        fields from a ResourceOOBRelationTable row using Pydantic's from_attributes.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        row = ResourceOOBRelationTable(
            oob_manager_id="oob-001",
            oob_device_id="dev-001",
            device_type=DeviceType.CPU.value,
            device_id=uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
        )

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#

        entity = ResourceOOBRelation.model_validate(row)

        assert entity.oob_manager_id == "oob-001"
        assert entity.oob_device_id == "dev-001"
        assert entity.device_type == DeviceType.CPU


class TestResourceEntity:
    """Tests for ResourceEntity model."""

    @pytest.mark.parametrize(
        "kwargs",
        [
            # device_id only; ports and oob_relations default to empty lists
            pytest.param(
                {
                    "device_id": uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
                    "ports": [],
                    "oob_relations": [],
                },
                id="empty_relations",
            ),
            # device_id with populated ports and oob_relations
            pytest.param(
                {
                    "device_id": uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
                    "ports": [
                        PortEntity(
                            fm_manager_id="fm-001",
                            fm_port_id="port-001",
                            fabric_id="fabric-001",
                            switch_port_type=SwitchPortType.USP,
                            fm_switch_id="switch-001",
                        ),
                    ],
                    "oob_relations": [
                        ResourceOOBRelation(
                            oob_manager_id="oob-001",
                            oob_device_id="dev-001",
                            device_type=DeviceType.CPU,
                        ),
                    ],
                },
                id="with_relations",
            ),
        ],
    )
    def test_valid_entity(self, kwargs: dict) -> None:
        """Verifies that ResourceEntity accepts valid inputs with and without related entities."""
        model = ResourceEntity(**kwargs)
        for field, value in kwargs.items():
            assert getattr(model, field) == value

    @pytest.mark.parametrize(
        "kwargs",
        [
            # device_id is a plain string that is not a valid UUID
            pytest.param({"device_id": "not-a-uuid"}, id="device_id_invalid_str"),
            # device_id is None (None is not accepted for a required UUID field)
            pytest.param({"device_id": None}, id="device_id_none"),
            # ports is a plain string (str is not accepted for a list field)
            pytest.param(
                {
                    "device_id": uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
                    "ports": "invalid",
                },
                id="ports_str",
            ),
        ],
    )
    def test_invalid_field_raises_validation_error(self, kwargs: dict) -> None:
        """Verifies that ResourceEntity raises ValidationError for fields with invalid types."""
        with pytest.raises(ValidationError):
            ResourceEntity(**kwargs)

    def test_model_validate_from_table_row(self) -> None:
        """Test model validation from ResourceTable row.

        Verifies that ResourceEntity.model_validate() correctly reads all fields
        from a ResourceTable row, including nested relationship objects.
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        device_uuid = uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
        port_row = PortTable(
            fm_manager_id="fm-001",
            fm_port_id="port-001",
            fabric_id="fabric-001",
            switch_port_type=SwitchPortType.USP.value,
            fm_switch_id="switch-001",
        )
        oob_row = ResourceOOBRelationTable(
            oob_manager_id="oob-001",
            oob_device_id="dev-001",
            device_type=DeviceType.CPU.value,
            device_id=device_uuid,
        )
        resource_row = ResourceTable(
            device_id=device_uuid,
            ports=[port_row],
            oob_relations=[oob_row],
        )

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#

        entity = ResourceEntity.model_validate(resource_row)

        assert entity.device_id == device_uuid
        assert len(entity.ports) == 1
        assert entity.ports[0].fm_manager_id == "fm-001"
        assert entity.ports[0].switch_port_type == SwitchPortType.USP
        assert len(entity.oob_relations) == 1
        assert entity.oob_relations[0].oob_manager_id == "oob-001"
        assert entity.oob_relations[0].device_type == DeviceType.CPU


class TestSwitchEntity:
    """Tests for SwitchEntity model."""

    @pytest.mark.parametrize(
        "kwargs",
        [
            # all fields provided including optional ones
            pytest.param(
                {
                    "device_id": uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
                    "fm_manager_id": "fm-001",
                    "fm_switch_id": "switch-001",
                },
                id="with_optional_fields",
            ),
            # optional fields absent; they default to None
            pytest.param(
                {"device_id": uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")},
                id="without_optional_fields",
            ),
        ],
    )
    def test_valid_entity(self, kwargs: dict) -> None:
        """Verifies that SwitchEntity accepts valid inputs with and without optional fields."""
        entity = SwitchEntity(**kwargs)
        assert entity.device_id == kwargs["device_id"]
        assert entity.fm_manager_id == kwargs.get("fm_manager_id")
        assert entity.fm_switch_id == kwargs.get("fm_switch_id")

    @pytest.mark.parametrize(
        "kwargs",
        [
            # device_id is a plain string that is not a valid UUID
            pytest.param({"device_id": "not-a-uuid"}, id="device_id_invalid_str"),
            # device_id is None (None is not accepted for a required UUID field)
            pytest.param({"device_id": None}, id="device_id_none"),
            # fm_manager_id is an integer (int is not accepted for str fields in Pydantic v2)
            pytest.param(
                {
                    "device_id": uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11"),
                    "fm_manager_id": 1,
                },
                id="manager_id_int",
            ),
        ],
    )
    def test_invalid_field_raises_validation_error(self, kwargs: dict) -> None:
        """Verifies that SwitchEntity raises ValidationError for fields with invalid types."""
        with pytest.raises(ValidationError):
            SwitchEntity(**kwargs)

    def test_model_validate_from_table_row(self) -> None:
        """Verifies that SwitchEntity.model_validate() reads all fields correctly from a SwitchTable row."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#

        device_uuid = uuid.UUID("a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11")
        row = SwitchTable(
            device_id=device_uuid,
            fm_manager_id="fm-001",
            fm_switch_id="switch-001",
            serial_number="SN-001",
            manufacturer="example_manufacturer",
            model="example_model",
        )

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#

        entity = SwitchEntity.model_validate(row)

        assert entity.device_id == device_uuid
        assert entity.fm_manager_id == "fm-001"
        assert entity.fm_switch_id == "switch-001"


class TestBaseSyncModel:
    """Tests for BaseSyncModel configuration shared by all upsert model subclasses."""

    class _ConcreteModel(BaseSyncModel):
        """Minimal concrete subclass for testing BaseSyncModel behavior."""

        value: str

    @pytest.mark.parametrize(
        "model_class",
        [
            pytest.param(ResourceSyncModel, id="ResourceSyncModel"),
            pytest.param(PortSyncModel, id="PortSyncModel"),
            pytest.param(FabricSyncModel, id="FabricSyncModel"),
            pytest.param(SwitchSyncModel, id="SwitchSyncModel"),
            pytest.param(OOBResourceSyncModel, id="OOBResourceSyncModel"),
            pytest.param(OOBSyncModel, id="OOBSyncModel"),
            pytest.param(FMSyncModel, id="FMSyncModel"),
        ],
    )
    def test_inherits_base_sync_model(self, model_class: type) -> None:
        """Verifies that all SyncModel classes inherit from BaseSyncModel."""
        assert issubclass(model_class, BaseSyncModel)

    def test_extra_field_forbidden(self) -> None:
        """Verifies that BaseSyncModel subclasses reject extra fields."""
        with pytest.raises(ValidationError):
            # Intentionally passing a non-existent field to verify Pydantic rejects it.
            # mypy flags this as a type error since extra_field is not in the model definition.
            self._ConcreteModel(value="ok", extra_field="not_allowed")  # type: ignore[call-arg]

    def test_validate_assignment(self) -> None:
        """Verifies that BaseSyncModel subclasses validate field values on assignment."""
        model = self._ConcreteModel(value="ok")
        with pytest.raises(ValidationError):
            # Intentionally assigning an int to a str field to verify Pydantic rejects it.
            # mypy flags this as a type error since int is incompatible with str field type.
            model.value = 123  # type: ignore[assignment]


class TestResourceSyncModel:
    """Tests for ResourceSyncModel validation."""

    @pytest.mark.parametrize(
        "kwargs",
        [
            # only pcie_identity is provided (cpu_identity and device_keys default to None)
            pytest.param(
                {
                    "pcie_identity": PCIeIdentity(
                        pcie_vendor_id="1234",
                        pcie_device_id="5678",
                        pcie_device_serial_number="0123456789abcdef",
                    )
                },
                id="pcie_identity_only",
            ),
            # only cpu_identity is provided
            pytest.param(
                {
                    "cpu_identity": CPUIdentity(
                        cpu_serial_number="SN12345",
                        cpu_manufacturer="example_manufacturer",
                        cpu_model="example_model",
                    )
                },
                id="cpu_identity_only",
            ),
            # only device_keys is provided
            pytest.param(
                {"device_keys": {"key1": "value1"}},
                id="device_keys_only",
            ),
            # pcie_identity, cpu_identity, and device_keys are all provided
            pytest.param(
                {
                    "pcie_identity": PCIeIdentity(
                        pcie_vendor_id="1234",
                        pcie_device_id="5678",
                        pcie_device_serial_number="0123456789abcdef",
                    ),
                    "cpu_identity": CPUIdentity(
                        cpu_serial_number="SN12345",
                        cpu_manufacturer="example_manufacturer",
                        cpu_model="example_model",
                    ),
                    "device_keys": {"key1": "value1"},
                },
                id="all_fields",
            ),
        ],
    )
    def test_valid_model(self, kwargs: dict) -> None:
        """Verifies that ResourceSyncModel accepts valid combinations of identity fields."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        model = ResourceSyncModel(**kwargs)
        for field, value in kwargs.items():
            assert getattr(model, field) == value

    def test_invalid_no_identity(self) -> None:
        """Verifies that ResourceSyncModel raises ValidationError when no identity field is provided."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(
            ValidationError, match="At least one of pcie_identity, cpu_identity, or device_keys is required."
        ):
            ResourceSyncModel()


class TestPortSyncModel:
    """Tests for PortSyncModel validation."""

    @pytest.mark.parametrize(
        "switch_port_type",
        [
            pytest.param(SwitchPortType.USP, id="usp"),
            pytest.param(SwitchPortType.DSP, id="dsp"),
        ],
    )
    def test_valid_without_attached_resource(self, switch_port_type: SwitchPortType) -> None:
        """Verifies that PortSyncModel accepts valid inputs without attached_resource for each port type."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        model = PortSyncModel(
            fm_port_id="port-001",
            fabric_id="fabric-001",
            fm_switch_id="switch-001",
            switch_port_type=switch_port_type,
        )
        assert model.switch_port_type == switch_port_type
        assert model.attached_resource is None

    @pytest.mark.parametrize(
        "switch_port_type",
        [
            pytest.param(SwitchPortType.USP, id="usp"),
            pytest.param(SwitchPortType.DSP, id="dsp"),
        ],
    )
    def test_valid_with_attached_resource(self, switch_port_type: SwitchPortType) -> None:
        """Verifies that PortSyncModel accepts valid inputs with attached_resource for each port type."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        model = PortSyncModel(
            fm_port_id="port-001",
            fabric_id="fabric-001",
            fm_switch_id="switch-001",
            switch_port_type=switch_port_type,
            attached_resource=ResourceSyncModel(
                pcie_identity=PCIeIdentity(
                    pcie_vendor_id="1234",
                    pcie_device_id="5678",
                    pcie_device_serial_number="0123456789abcdef",
                ),
            ),
        )
        assert model.switch_port_type == switch_port_type
        assert model.attached_resource is not None

    @pytest.mark.parametrize(
        "kwargs",
        [
            # fm_port_id is an integer (int is not accepted for str fields in Pydantic v2)
            pytest.param(
                {
                    "fm_port_id": 1,
                    "fabric_id": "fabric-001",
                    "fm_switch_id": "switch-001",
                    "switch_port_type": SwitchPortType.USP,
                },
                id="port_id_int",
            ),
            # fm_port_id is None (None is not accepted for a required str field)
            pytest.param(
                {
                    "fm_port_id": None,
                    "fabric_id": "fabric-001",
                    "fm_switch_id": "switch-001",
                    "switch_port_type": SwitchPortType.USP,
                },
                id="port_id_none",
            ),
            # switch_port_type is an unrecognized string (not a valid SwitchPortType value)
            pytest.param(
                {
                    "fm_port_id": "port-001",
                    "fabric_id": "fabric-001",
                    "fm_switch_id": "switch-001",
                    "switch_port_type": "INVALID_PORT_TYPE",
                },
                id="port_type_invalid_str",
            ),
            # switch_port_type is None (None is not accepted for a required enum field)
            pytest.param(
                {
                    "fm_port_id": "port-001",
                    "fabric_id": "fabric-001",
                    "fm_switch_id": "switch-001",
                    "switch_port_type": None,
                },
                id="port_type_none",
            ),
            # attached_resource is a plain string (str is not accepted for ResourceSyncModel)
            pytest.param(
                {
                    "fm_port_id": "port-001",
                    "fabric_id": "fabric-001",
                    "fm_switch_id": "switch-001",
                    "switch_port_type": SwitchPortType.USP,
                    "attached_resource": "invalid",
                },
                id="attached_resource_str",
            ),
            # fm_port_id is an empty string (min_length=1 rejects empty strings)
            pytest.param(
                {
                    "fm_port_id": "",
                    "fabric_id": "fabric-001",
                    "fm_switch_id": "switch-001",
                    "switch_port_type": SwitchPortType.USP,
                },
                id="port_id_empty",
            ),
            # fabric_id is an empty string (min_length=1 rejects empty strings)
            pytest.param(
                {
                    "fm_port_id": "port-001",
                    "fabric_id": "",
                    "fm_switch_id": "switch-001",
                    "switch_port_type": SwitchPortType.USP,
                },
                id="fabric_id_empty",
            ),
            # fm_switch_id is an empty string (min_length=1 rejects empty strings)
            pytest.param(
                {
                    "fm_port_id": "port-001",
                    "fabric_id": "fabric-001",
                    "fm_switch_id": "",
                    "switch_port_type": SwitchPortType.USP,
                },
                id="switch_id_empty",
            ),
        ],
    )
    def test_invalid_field_raises_validation_error(self, kwargs: dict) -> None:
        """Verifies that PortSyncModel raises ValidationError for fields with invalid types."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            PortSyncModel(**kwargs)


class TestFabricSyncModel:
    """Tests for FabricSyncModel validation."""

    def test_valid_model(self) -> None:
        """Verifies that FabricSyncModel accepts valid field values."""
        model = FabricSyncModel(fabric_id="fabric-001")
        assert model.fabric_id == "fabric-001"

    @pytest.mark.parametrize(
        "kwargs",
        [
            # fabric_id is an integer (int is not accepted for str fields in Pydantic v2)
            pytest.param({"fabric_id": 1}, id="fabric_id_int"),
            # fabric_id is None (None is not accepted for a required str field)
            pytest.param({"fabric_id": None}, id="fabric_id_none"),
            # fabric_id is a list (list is not accepted for str fields)
            pytest.param({"fabric_id": ["fabric-001"]}, id="fabric_id_list"),
            # fabric_id is an empty string (min_length=1 rejects empty strings)
            pytest.param({"fabric_id": ""}, id="fabric_id_empty"),
        ],
    )
    def test_invalid_field_raises_validation_error(self, kwargs: dict) -> None:
        """Verifies that FabricSyncModel raises ValidationError for fields with invalid types."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            FabricSyncModel(**kwargs)


class TestSwitchSyncModel:
    """Tests for SwitchSyncModel validation."""

    def test_valid_model(self) -> None:
        """Verifies that SwitchSyncModel accepts valid field values."""
        model = SwitchSyncModel(
            fm_switch_id="switch-001",
            switch_identity=SwitchIdentity(
                switch_serial_number="SW-001",
                switch_manufacturer="example_manufacturer",
                switch_model="example_model",
            ),
        )
        assert model.fm_switch_id == "switch-001"
        assert model.switch_identity.switch_serial_number == "SW-001"

    @pytest.mark.parametrize(
        "kwargs",
        [
            # fm_switch_id is an integer (int is not accepted for str fields in Pydantic v2)
            pytest.param(
                {
                    "fm_switch_id": 1,
                    "switch_identity": SwitchIdentity(
                        switch_serial_number="SW-001",
                        switch_manufacturer="example_manufacturer",
                        switch_model="example_model",
                    ),
                },
                id="switch_id_int",
            ),
            # fm_switch_id is None (None is not accepted for a required str field)
            pytest.param(
                {
                    "fm_switch_id": None,
                    "switch_identity": SwitchIdentity(
                        switch_serial_number="SW-001",
                        switch_manufacturer="example_manufacturer",
                        switch_model="example_model",
                    ),
                },
                id="switch_id_none",
            ),
            # switch_identity is a plain string (str is not accepted for SwitchIdentity)
            pytest.param(
                {"fm_switch_id": "switch-001", "switch_identity": "invalid"},
                id="switch_identity_str",
            ),
            # switch_identity is None (None is not accepted for a required field)
            pytest.param(
                {"fm_switch_id": "switch-001", "switch_identity": None},
                id="switch_identity_none",
            ),
            # fm_switch_id is an empty string (min_length=1 rejects empty strings)
            pytest.param(
                {
                    "fm_switch_id": "",
                    "switch_identity": SwitchIdentity(
                        switch_serial_number="SW-001",
                        switch_manufacturer="example_manufacturer",
                        switch_model="example_model",
                    ),
                },
                id="switch_id_empty",
            ),
        ],
    )
    def test_invalid_field_raises_validation_error(self, kwargs: dict) -> None:
        """Verifies that SwitchSyncModel raises ValidationError for fields with invalid types."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            SwitchSyncModel(**kwargs)

    def test_missing_switch_identity(self) -> None:
        """Verifies that SwitchSyncModel raises ValidationError when switch_identity is absent."""
        with pytest.raises(ValidationError):
            # Intentionally omitting the required switch_identity field to verify Pydantic validates it.
            # mypy flags this as a type error since switch_identity is a required field.
            SwitchSyncModel(fm_switch_id="switch-001")  # type: ignore[call-arg]


class TestOOBResourceSyncModel:
    """Tests for OOBResourceSyncModel validation."""

    @pytest.mark.parametrize(
        "device_type",
        [
            pytest.param(DeviceType.CPU, id="cpu"),
            pytest.param(DeviceType.MEMORY, id="memory"),
            pytest.param(DeviceType.GPU, id="gpu"),
        ],
    )
    def test_valid_model(self, device_type: DeviceType) -> None:
        """Verifies that OOBResourceSyncModel accepts valid inputs for each device type."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        model = OOBResourceSyncModel(
            oob_device_id="dev-001",
            device_type=device_type,
            pcie_identity=PCIeIdentity(
                pcie_vendor_id="1234",
                pcie_device_id="5678",
                pcie_device_serial_number="0123456789abcdef",
            ),
        )
        assert model.device_type == device_type

    @pytest.mark.parametrize(
        "kwargs",
        [
            # oob_device_id is None (None is not accepted for a required str field)
            pytest.param(
                {
                    "oob_device_id": None,
                    "device_type": DeviceType.CPU,
                    "pcie_identity": PCIeIdentity(
                        pcie_vendor_id="1234",
                        pcie_device_id="5678",
                        pcie_device_serial_number="0123456789abcdef",
                    ),
                },
                id="device_id_none",
            ),
            # device_type is an unrecognized string (not a valid DeviceType value)
            pytest.param(
                {
                    "oob_device_id": "dev-001",
                    "device_type": "INVALID_DEVICE_TYPE",
                    "pcie_identity": PCIeIdentity(
                        pcie_vendor_id="1234",
                        pcie_device_id="5678",
                        pcie_device_serial_number="0123456789abcdef",
                    ),
                },
                id="device_type_invalid_str",
            ),
            # device_type is None (None is not accepted for a required enum field)
            pytest.param(
                {
                    "oob_device_id": "dev-001",
                    "device_type": None,
                    "pcie_identity": PCIeIdentity(
                        pcie_vendor_id="1234",
                        pcie_device_id="5678",
                        pcie_device_serial_number="0123456789abcdef",
                    ),
                },
                id="device_type_none",
            ),
            # oob_device_id is an empty string (min_length=1 rejects empty strings)
            pytest.param(
                {
                    "oob_device_id": "",
                    "device_type": DeviceType.CPU,
                    "pcie_identity": PCIeIdentity(
                        pcie_vendor_id="1234",
                        pcie_device_id="5678",
                        pcie_device_serial_number="0123456789abcdef",
                    ),
                },
                id="device_id_empty",
            ),
        ],
    )
    def test_invalid_field_raises_validation_error(self, kwargs: dict) -> None:
        """Verifies that OOBResourceSyncModel raises ValidationError for fields with invalid types."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            OOBResourceSyncModel(**kwargs)

    def test_inherits_identity_validation(self) -> None:
        """Verifies that OOBResourceSyncModel raises ValidationError when no identity field is provided."""
        with pytest.raises(
            ValidationError, match="At least one of pcie_identity, cpu_identity, or device_keys is required."
        ):
            OOBResourceSyncModel(
                oob_device_id="dev-001",
                device_type=DeviceType.CPU,
            )


class TestOOBSyncModel:
    """Tests for OOBSyncModel validation."""

    @pytest.mark.parametrize(
        "kwargs",
        [
            # devices list is empty (default)
            pytest.param(
                {"oob_manager_id": "oob-001", "devices": []},
                id="empty_devices",
            ),
            # devices list contains valid resources
            pytest.param(
                {
                    "oob_manager_id": "oob-001",
                    "devices": [
                        OOBResourceSyncModel(
                            oob_device_id="dev-001",
                            device_type=DeviceType.CPU,
                            cpu_identity=CPUIdentity(
                                cpu_serial_number="SN001",
                                cpu_manufacturer="example_manufacturer",
                                cpu_model="example_model",
                            ),
                        ),
                        OOBResourceSyncModel(
                            oob_device_id="dev-002",
                            device_type=DeviceType.MEMORY,
                            device_keys={"slot": "example-slot-2"},
                        ),
                    ],
                },
                id="with_devices",
            ),
        ],
    )
    def test_valid_model(self, kwargs: dict) -> None:
        """Verifies that OOBSyncModel accepts valid combinations of oob_manager_id and devices."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        model = OOBSyncModel(**kwargs)
        for field, value in kwargs.items():
            assert getattr(model, field) == value

    @pytest.mark.parametrize(
        "kwargs",
        [
            # oob_manager_id is an integer (int is not accepted for str fields in Pydantic v2)
            pytest.param({"oob_manager_id": 1}, id="manager_id_int"),
            # oob_manager_id is None (None is not accepted for a required str field)
            pytest.param({"oob_manager_id": None}, id="manager_id_none"),
            # devices is a plain string (str is not accepted for a list field)
            pytest.param({"oob_manager_id": "oob-001", "devices": "invalid"}, id="devices_str"),
            # oob_manager_id is an empty string (min_length=1 rejects empty strings)
            pytest.param({"oob_manager_id": ""}, id="manager_id_empty"),
        ],
    )
    def test_invalid_field_raises_validation_error(self, kwargs: dict) -> None:
        """Verifies that OOBSyncModel raises ValidationError for fields with invalid types."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            OOBSyncModel(**kwargs)

    def test_invalid_duplicate_oob_device_ids(self) -> None:
        """Verifies that OOBSyncModel raises ValidationError when oob_device_id values are not unique."""
        with pytest.raises(ValidationError, match="Duplicate oob_device_id"):
            OOBSyncModel(
                oob_manager_id="oob-001",
                devices=[
                    OOBResourceSyncModel(
                        oob_device_id="dev-001",  # duplicate ID
                        device_type=DeviceType.CPU,
                        device_keys={"key": "val1"},
                    ),
                    OOBResourceSyncModel(
                        oob_device_id="dev-001",  # duplicate ID
                        device_type=DeviceType.MEMORY,
                        device_keys={"key": "val2"},
                    ),
                ],
            )

    def test_invalid_duplicate_pcie_identities(self) -> None:
        """Verifies that OOBSyncModel raises ValidationError when PCIe identities are not unique."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        duplicate_pcie = PCIeIdentity(
            pcie_vendor_id="abcd",
            pcie_device_id="1234",
            pcie_device_serial_number="0123456789abcdef",
        )

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError, match="Duplicate PCIe identity found"):
            OOBSyncModel(
                oob_manager_id="oob-001",
                devices=[
                    OOBResourceSyncModel(
                        oob_device_id="dev-001",
                        device_type=DeviceType.CPU,
                        pcie_identity=duplicate_pcie,
                    ),
                    OOBResourceSyncModel(
                        oob_device_id="dev-002",
                        device_type=DeviceType.CPU,
                        pcie_identity=duplicate_pcie,
                    ),
                ],
            )

    def test_invalid_duplicate_cpu_identities(self) -> None:
        """Verifies that OOBSyncModel raises ValidationError when CPU identities are not unique."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        duplicate_cpu = CPUIdentity(
            cpu_serial_number="SN001",
            cpu_manufacturer="example_manufacturer",
            cpu_model="example_model",
        )

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError, match="Duplicate CPU identity found"):
            OOBSyncModel(
                oob_manager_id="oob-001",
                devices=[
                    OOBResourceSyncModel(
                        oob_device_id="dev-001",
                        device_type=DeviceType.CPU,
                        cpu_identity=duplicate_cpu,
                    ),
                    OOBResourceSyncModel(
                        oob_device_id="dev-002",
                        device_type=DeviceType.CPU,
                        cpu_identity=duplicate_cpu,
                    ),
                ],
            )

    def test_invalid_duplicate_device_keys(self) -> None:
        """Verifies that OOBSyncModel raises ValidationError when device_keys are not unique."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        duplicate_keys = {"key_a": "value_1", "key_b": "value_2"}

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError, match="Duplicate device_keys found"):
            OOBSyncModel(
                oob_manager_id="oob-001",
                devices=[
                    OOBResourceSyncModel(
                        oob_device_id="dev-001",
                        device_type=DeviceType.CPU,
                        device_keys=duplicate_keys,
                    ),
                    OOBResourceSyncModel(
                        oob_device_id="dev-002",
                        device_type=DeviceType.CPU,
                        device_keys=duplicate_keys,
                    ),
                ],
            )


class TestFMSyncModel:
    """Tests for FMSyncModel validation."""

    @pytest.mark.parametrize(
        "kwargs",
        [
            # all lists are empty (default)
            pytest.param(
                {"fm_manager_id": "fm-001", "switches": [], "fabrics": [], "ports": []},
                id="empty_lists",
            ),
            # switches, fabrics, and ports are all populated with valid entries
            pytest.param(
                {
                    "fm_manager_id": "fm-001",
                    "switches": [
                        SwitchSyncModel(
                            fm_switch_id="switch-001",
                            switch_identity=SwitchIdentity(
                                switch_serial_number="SW-001",
                                switch_manufacturer="example_manufacturer",
                                switch_model="example_model",
                            ),
                        ),
                    ],
                    "fabrics": [FabricSyncModel(fabric_id="fabric-001")],
                    "ports": [
                        PortSyncModel(
                            fm_port_id="port-001",
                            fabric_id="fabric-001",
                            fm_switch_id="switch-001",
                            switch_port_type=SwitchPortType.USP,
                        ),
                    ],
                },
                id="full_model",
            ),
        ],
    )
    def test_valid_model(self, kwargs: dict) -> None:
        """Verifies that FMSyncModel accepts valid combinations of switches, fabrics, and ports."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        model = FMSyncModel(**kwargs)
        for field, value in kwargs.items():
            assert getattr(model, field) == value

    @pytest.mark.parametrize(
        "kwargs",
        [
            # fm_manager_id is an integer (int is not accepted for str fields in Pydantic v2)
            pytest.param(
                {"fm_manager_id": 1},
                id="manager_id_int",
            ),
            # fm_manager_id is None (None is not accepted for a required str field)
            pytest.param(
                {"fm_manager_id": None},
                id="manager_id_none",
            ),
            # switches is a plain string (str is not accepted for a list field)
            pytest.param(
                {"fm_manager_id": "fm-001", "switches": "invalid"},
                id="switches_str",
            ),
            # ports is a plain string (str is not accepted for a list field)
            pytest.param(
                {"fm_manager_id": "fm-001", "ports": "invalid"},
                id="ports_str",
            ),
            # fm_manager_id is an empty string (min_length=1 rejects empty strings)
            pytest.param(
                {"fm_manager_id": ""},
                id="manager_id_empty",
            ),
        ],
    )
    def test_invalid_field_raises_validation_error(self, kwargs: dict) -> None:
        """Verifies that FMSyncModel raises ValidationError for fields with invalid types."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError):
            FMSyncModel(**kwargs)

    def test_invalid_port_references_unknown_fabric(self) -> None:
        """Verifies that FMSyncModel raises ValidationError when a port references an undefined fabric."""
        with pytest.raises(ValidationError, match="undefined fabric_id"):
            FMSyncModel(
                fm_manager_id="fm-001",
                switches=[
                    SwitchSyncModel(
                        fm_switch_id="switch-001",
                        switch_identity=SwitchIdentity(
                            switch_serial_number="SW-001",
                            switch_manufacturer="example_manufacturer",
                            switch_model="example_model",
                        ),
                    ),
                ],
                fabrics=[
                    FabricSyncModel(fabric_id="fabric-001"),
                ],
                ports=[
                    PortSyncModel(
                        fm_port_id="port-001",
                        fabric_id="fabric-999",  # undefined fabric reference
                        fm_switch_id="switch-001",
                        switch_port_type=SwitchPortType.USP,
                    ),
                ],
            )

    def test_invalid_port_references_unknown_switch(self) -> None:
        """Verifies that FMSyncModel raises ValidationError when a port references an undefined switch."""
        with pytest.raises(ValidationError, match="undefined fm_switch_id"):
            FMSyncModel(
                fm_manager_id="fm-001",
                switches=[
                    SwitchSyncModel(
                        fm_switch_id="switch-001",
                        switch_identity=SwitchIdentity(
                            switch_serial_number="SW-001",
                            switch_manufacturer="example_manufacturer",
                            switch_model="example_model",
                        ),
                    ),
                ],
                fabrics=[
                    FabricSyncModel(fabric_id="fabric-001"),
                ],
                ports=[
                    PortSyncModel(
                        fm_port_id="port-001",
                        fabric_id="fabric-001",
                        fm_switch_id="switch-999",  # undefined switch reference
                        switch_port_type=SwitchPortType.USP,
                    ),
                ],
            )

    def test_invalid_port_references_both_unknown(self) -> None:
        """Verifies that FMSyncModel raises ValidationError when a port references both undefined fabric and switch."""
        with pytest.raises(ValidationError):
            FMSyncModel(
                fm_manager_id="fm-001",
                switches=[],
                fabrics=[],
                ports=[
                    PortSyncModel(
                        fm_port_id="port-001",
                        fabric_id="fabric-999",  # undefined fabric reference
                        fm_switch_id="switch-999",  # undefined switch reference
                        switch_port_type=SwitchPortType.USP,
                    ),
                ],
            )

    def test_invalid_duplicate_switch_identities(self) -> None:
        """Verifies FMSyncModel rejects the same physical switch under two fm_switch_id values.

        The same physical switch (serial/manufacturer/model) must map to a single
        device_id. Without this validation, two switches sharing the physical identity
        would create duplicate switch rows during sync_fm (autoflush=False prevents the
        second _upsert_switch from finding the first, un-flushed row).
        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        duplicate_identity = SwitchIdentity(
            switch_serial_number="SW-DUP",
            switch_manufacturer="example_manufacturer",
            switch_model="example_model",
        )

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(ValidationError, match="Duplicate switch identity found"):
            FMSyncModel(
                fm_manager_id="fm-001",
                switches=[
                    SwitchSyncModel(fm_switch_id="switch-001", switch_identity=duplicate_identity),
                    SwitchSyncModel(fm_switch_id="switch-002", switch_identity=duplicate_identity),
                ],
                fabrics=[],
                ports=[],
            )

    def test_valid_distinct_switch_identities(self) -> None:
        """Verifies FMSyncModel accepts multiple switches with distinct physical identities."""
        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        model = FMSyncModel(
            fm_manager_id="fm-001",
            switches=[
                SwitchSyncModel(
                    fm_switch_id="switch-001",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SW-001",
                        switch_manufacturer="example_manufacturer",
                        switch_model="example_model",
                    ),
                ),
                SwitchSyncModel(
                    fm_switch_id="switch-002",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SW-002",
                        switch_manufacturer="example_manufacturer",
                        switch_model="example_model",
                    ),
                ),
            ],
            fabrics=[],
            ports=[],
        )
        assert len(model.switches) == 2

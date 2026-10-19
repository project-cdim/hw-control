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

"""Device Repository and related domain models."""

import json
import logging
import uuid
from typing import Self

from pydantic import UUID4, BaseModel, ConfigDict, Field, ValidationError, model_validator, validate_call
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import app.common.basic_exceptions as exc
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

logger = logging.getLogger(__name__)


class PCIeIdentity(BaseModel):
    """PCIe device identification triplet.

    Attributes:
        pcie_vendor_id: 4-digit lowercase hex string.
        pcie_device_id: 4-digit lowercase hex string.
        pcie_device_serial_number: 16-digit lowercase hex string.

    Note:
        Accepts both uppercase and lowercase hex input, but normalizes
        all values to lowercase on instantiation.
    """

    pcie_vendor_id: str = Field(pattern=r"^[0-9a-fA-F]{4}$", description="PCIe vendor ID (4-digit hex)")
    pcie_device_id: str = Field(pattern=r"^[0-9a-fA-F]{4}$", description="PCIe device ID (4-digit hex)")
    pcie_device_serial_number: str = Field(
        pattern=r"^[0-9a-fA-F]{16}$", description="PCIe serial number (16-digit hex)"
    )

    @model_validator(mode="after")
    def normalize_to_lowercase(self) -> Self:
        """Normalize all hex fields to lowercase."""
        self.pcie_vendor_id = self.pcie_vendor_id.lower()
        self.pcie_device_id = self.pcie_device_id.lower()
        self.pcie_device_serial_number = self.pcie_device_serial_number.lower()
        return self


class CPUIdentity(BaseModel):
    """CPU device identification triplet."""

    cpu_serial_number: str = Field(min_length=1, description="CPU serial number")
    cpu_manufacturer: str = Field(min_length=1, description="CPU manufacturer")
    cpu_model: str = Field(min_length=1, description="CPU model")


class SwitchIdentity(BaseModel):
    """Switch device identification triplet."""

    switch_serial_number: str = Field(min_length=1, description="Switch serial number")
    switch_manufacturer: str = Field(min_length=1, description="Switch manufacturer")
    switch_model: str = Field(min_length=1, description="Switch model")


class EntityBaseModel(BaseModel):
    """Base class for read-only entity models converted from SQLAlchemy objects."""

    model_config = ConfigDict(
        from_attributes=True,  # Allow conversion from SQLAlchemy objects
    )


class PortEntity(EntityBaseModel):
    """Port entity converted from PortTable."""

    fm_manager_id: str = Field(description="FM manager ID")
    fm_port_id: str = Field(description="FM port ID")
    fabric_id: str = Field(description="Fabric ID")
    switch_port_type: constants.SwitchPortType = Field(description="Switch port type (USP/DSP)")
    fm_switch_id: str = Field(description="FM switch ID that this port belongs to")


class ResourceOOBRelation(EntityBaseModel):
    """Resource-to-OOB relation entity converted from ResourceOOBRelationTable."""

    oob_manager_id: str = Field(description="OOB manager ID")
    oob_device_id: str = Field(description="OOB device ID")
    device_type: constants.DeviceType = Field(description="Device type from OOB perspective")


class ResourceEntity(EntityBaseModel):
    """Resource entity converted from ResourceTable.

    Includes related ports and OOB relations via SQLAlchemy relationships.
    Physical identifiers (cpu_*, pcie_*) are excluded.
    """

    device_id: UUID4 = Field(description="Device ID")

    # Information obtained via relationships
    ports: list[PortEntity] = Field(default_factory=list, description="List of port information")
    oob_relations: list[ResourceOOBRelation] = Field(
        default_factory=list, description="List of OOB relation information (includes device_type)"
    )


class SwitchEntity(EntityBaseModel):
    """Switch entity converted from SwitchTable.

    Physical identifiers (serial_number, manufacturer, model)
    are excluded.
    """

    device_id: UUID4 = Field(description="Device ID")
    fm_manager_id: str | None = Field(None, description="FM manager ID")
    fm_switch_id: str | None = Field(None, description="FM switch ID")


class OOBSyncEntry(BaseModel):
    """Result entry returned by sync_oob for each synchronized device."""

    device_id: UUID4 = Field(description="Device ID")
    oob_device_id: str = Field(description="OOB device ID")
    device_type: constants.DeviceType = Field(description="Device type from OOB perspective")


class FMSyncEntry(BaseModel):
    """Result entry returned by sync_fm for each synchronized port with an attached resource."""

    device_id: UUID4 = Field(description="Device ID")
    fm_port_id: str = Field(description="FM port ID")
    fabric_id: str = Field(description="Fabric ID")
    fm_switch_id: str = Field(description="FM switch ID that this port belongs to")
    switch_port_type: constants.SwitchPortType = Field(description="Switch port type (USP/DSP)")


class BaseSyncModel(BaseModel):
    """Base class for all upsert models.

    Raises:
        ValidationError: If an undefined field is passed on instantiation,
            or if a field value fails validation on assignment.
    """

    model_config = ConfigDict(
        validate_assignment=True,  # Validate on instance variable assignment
        extra="forbid",  # Raise ValidationError on undefined fields
    )


class ResourceSyncModel(BaseSyncModel):
    """Resource identification for sync operations.

    At least one of pcie_identity, cpu_identity, or device_keys
    must be provided. Identification priority:
    pcie_identity > cpu_identity > device_keys.
    """

    pcie_identity: PCIeIdentity | None = Field(None, description="PCIe device identification")
    cpu_identity: CPUIdentity | None = Field(None, description="CPU device identification")
    device_keys: dict | None = Field(
        None, description="Device keys (fallback when PCIe/CPU identification is unavailable)"
    )

    @model_validator(mode="after")
    def validate_any_identity(self) -> Self:
        """Validate that at least one identity is provided.

        Raises:
            ValueError: If all of pcie_identity, cpu_identity, and
                device_keys are None.
        """
        if self.pcie_identity is None and self.cpu_identity is None and self.device_keys is None:
            raise ValueError("At least one of pcie_identity, cpu_identity, or device_keys is required.")
        return self


class PortSyncModel(BaseSyncModel):
    """Port information for FM sync operations."""

    fm_port_id: str = Field(min_length=1, description="FM port ID (unique within FM manager)")
    fabric_id: str = Field(min_length=1, description="Fabric ID")
    fm_switch_id: str = Field(min_length=1, description="FM switch ID that this port belongs to")
    switch_port_type: constants.SwitchPortType = Field(description="Port type (USP/DSP)")

    attached_resource: ResourceSyncModel | None = Field(
        None, description="Identification of the resource connected to this port"
    )


class FabricSyncModel(BaseSyncModel):
    """Fabric information for FM sync operations."""

    fabric_id: str = Field(min_length=1, description="Fabric ID (unique within FM manager)")


class SwitchSyncModel(BaseSyncModel):
    """Switch information for FM sync operations."""

    fm_switch_id: str = Field(min_length=1, description="FM switch ID (unique within FM manager)")
    switch_identity: SwitchIdentity = Field(description="Switch identification")


class OOBResourceSyncModel(ResourceSyncModel):
    """OOB resource information for OOB sync operations.

    Inherits identity validation from ResourceSyncModel.
    """

    oob_device_id: str = Field(min_length=1, description="OOB device ID")
    device_type: constants.DeviceType = Field(description="Device type")


class OOBSyncModel(BaseSyncModel):
    """Aggregate root for OOB sync operations.

    Synchronizes all resources under a single OOB manager.

    Raises:
        ValidationError: If validation fails, including when duplicate
            oob_device_id values are found across devices.
    """

    oob_manager_id: str = Field(min_length=1, description="OOB manager ID")
    devices: list[OOBResourceSyncModel] = Field(
        default_factory=list, description="List of resource information under OOB"
    )

    @model_validator(mode="after")
    def validate_oob_device_ids_unique(self) -> Self:
        """Validate that oob_device_id values are unique across devices.

        Raises:
            ValueError: If duplicate oob_device_id values are found.
                Pydantic automatically converts this to ValidationError.
        """
        oob_device_ids = [d.oob_device_id for d in self.devices]
        seen: set[str] = set()
        duplicates: set[str] = set()
        for oob_device_id in oob_device_ids:
            if oob_device_id in seen:
                duplicates.add(oob_device_id)
            seen.add(oob_device_id)
        if duplicates:
            raise ValueError(f"Duplicate oob_device_id found: {sorted(duplicates)}")
        return self

    @model_validator(mode="after")
    def validate_pcie_identities_unique(self) -> Self:
        """Validate that PCIe identities are unique across devices.

        Raises:
            ValueError: If duplicate PCIe identities are found.
                Pydantic automatically converts this to ValidationError.
        """
        seen: set[tuple[str, str, str]] = set()
        duplicates: set[tuple[str, str, str]] = set()
        for device in self.devices:
            if device.pcie_identity is not None:
                key = (
                    device.pcie_identity.pcie_vendor_id,
                    device.pcie_identity.pcie_device_id,
                    device.pcie_identity.pcie_device_serial_number,
                )
                if key in seen:
                    duplicates.add(key)
                seen.add(key)
        if duplicates:
            raise ValueError(f"Duplicate PCIe identity found: {sorted(duplicates)}")
        return self

    @model_validator(mode="after")
    def validate_cpu_identities_unique(self) -> Self:
        """Validate that CPU identities are unique across devices.

        Raises:
            ValueError: If duplicate CPU identities are found.
                Pydantic automatically converts this to ValidationError.
        """
        seen: set[tuple[str, str, str]] = set()
        duplicates: set[tuple[str, str, str]] = set()
        for device in self.devices:
            if device.cpu_identity is not None:
                key = (
                    device.cpu_identity.cpu_serial_number,
                    device.cpu_identity.cpu_manufacturer,
                    device.cpu_identity.cpu_model,
                )
                if key in seen:
                    duplicates.add(key)
                seen.add(key)
        if duplicates:
            raise ValueError(f"Duplicate CPU identity found: {sorted(duplicates)}")
        return self

    @model_validator(mode="after")
    def validate_device_keys_unique(self) -> Self:
        """Validate that device_keys are unique across devices.

        Raises:
            ValueError: If duplicate device_keys are found.
                Pydantic automatically converts this to ValidationError.
        """
        seen: set[str] = set()
        duplicates: set[str] = set()
        for device in self.devices:
            if device.device_keys is not None:
                key = json.dumps(device.device_keys, sort_keys=True)
                if key in seen:
                    duplicates.add(key)
                seen.add(key)
        if duplicates:
            raise ValueError(f"Duplicate device_keys found: {sorted(duplicates)}")
        return self


class FMSyncModel(BaseSyncModel):
    """Aggregate root for FM sync operations.

    Synchronizes switches, fabrics, and ports under a single FM manager.

    Raises:
        ValidationError: If validation fails, including when a port
            references an undefined fabric_id or fm_switch_id.
    """

    fm_manager_id: str = Field(min_length=1, description="FM manager ID of this FM")

    switches: list[SwitchSyncModel] = Field(
        default_factory=list, description="List of switch information under this FM"
    )
    fabrics: list[FabricSyncModel] = Field(default_factory=list, description="List of fabric information under this FM")
    ports: list[PortSyncModel] = Field(default_factory=list, description="List of port information under this FM")

    @model_validator(mode="after")
    def validate_port_references(self) -> Self:
        """Validate that ports reference defined fabrics and switches.

        Raises:
            ValueError: If a port references an undefined fabric_id
                or fm_switch_id. Pydantic automatically converts this to ValidationError.
        """
        fabric_ids = {f.fabric_id for f in self.fabrics}
        switch_ids = {s.fm_switch_id for s in self.switches}
        for port in self.ports:
            if port.fabric_id not in fabric_ids:
                raise ValueError(f"Port '{port.fm_port_id}' references undefined fabric_id='{port.fabric_id}'")
            if port.fm_switch_id not in switch_ids:
                raise ValueError(f"Port '{port.fm_port_id}' references undefined fm_switch_id='{port.fm_switch_id}'")
        return self

    @model_validator(mode="after")
    def validate_switch_identities_unique(self) -> Self:
        """Validate that switch physical identities are unique across switches.

        The same physical switch (serial_number/manufacturer/model triplet) must
        map to a single device_id. Per the FM data model, a physical switch appears
        at most once under a single FM, so a duplicate indicates malformed input.

        Raises:
            ValueError: If duplicate switch identities are found.
                Pydantic automatically converts this to ValidationError.
        """
        seen: set[tuple[str, str, str]] = set()
        duplicates: set[tuple[str, str, str]] = set()
        for switch in self.switches:
            key = (
                switch.switch_identity.switch_serial_number,
                switch.switch_identity.switch_manufacturer,
                switch.switch_identity.switch_model,
            )
            if key in seen:
                duplicates.add(key)
            seen.add(key)
        if duplicates:
            raise ValueError(f"Duplicate switch identity found: {sorted(duplicates)}")
        return self


class DeviceRepository:
    """Provides data access to device information (implemented with Repository pattern).

    Hides transactions from the caller.
    Hides internal DB data structure from the caller.
    """

    def __init__(self, db_session: Session) -> None:
        """Initialize the repository with a database session.

        Args:
            db_session (Session): The database session instance.
        """
        self._db_session = db_session

    @validate_call
    def get_active_resource(self, device_id: UUID4) -> ResourceEntity:
        """Get an active resource by device ID.

        A resource is considered active if it has at least one port
        or OOB relation.

        Args:
            device_id: UUID of the resource to retrieve.

        Returns:
            The resource entity.

        Raises:
            ValidationError: If device_id is not a valid UUID.
            DeviceNotFoundHWControlError: If the resource does not exist
                or is inactive.
            InternalHWControlError: If the database query fails or
                the database contains unexpected data.
        """
        try:
            target_device_entity = self._db_session.get(ResourceTable, device_id)
        except SQLAlchemyError as e:
            logger.exception("Failed to retrieve the resource record from the device management database.")
            raise exc.InternalHWControlError(
                additional_message="Failed to retrieve device management data.",
            ) from e

        if target_device_entity is None:
            raise exc.DeviceNotFoundHWControlError(
                f"No ResourceTable record found for device_id={device_id}.",
                additional_message=f"The target Device ID is: {device_id}.",
            )

        # Check if the device is active (has port or OOB relations)
        has_port = bool(target_device_entity.ports)
        has_oob = bool(target_device_entity.oob_relations)

        if not (has_port or has_oob):
            raise exc.DeviceNotFoundHWControlError(
                f"Device {device_id} exists but is inactive (not managed by FM/OOB).",
                additional_message=f"The target Device ID is: {device_id}.",
            )

        try:
            return ResourceEntity.model_validate(target_device_entity)
        except ValidationError as e:
            logger.exception("Failed to convert the ResourceTable record to a ResourceEntity.")
            raise exc.InternalHWControlError(
                additional_message="Device management data is in an inconsistent state.",
            ) from e

    def get_active_resources(self) -> list[ResourceEntity]:
        """Get all active resources.

        A resource is considered active if it has at least one port
        or OOB relation.

        Returns:
            List of active resource entities.

        Raises:
            InternalHWControlError: If the database query fails or
                the database contains unexpected data.
        """
        try:
            # Query resources that have port or OOB relations (active devices)
            devices = (
                self._db_session.query(ResourceTable)
                .outerjoin(PortTable, ResourceTable.device_id == PortTable.device_id)
                .outerjoin(ResourceOOBRelationTable, ResourceTable.device_id == ResourceOOBRelationTable.device_id)
                .filter(or_(PortTable.device_id.isnot(None), ResourceOOBRelationTable.device_id.isnot(None)))
                .distinct()
                .all()
            )
        except SQLAlchemyError as e:
            logger.exception("Failed to retrieve active resource records from the device management database.")
            raise exc.InternalHWControlError(
                additional_message="Failed to retrieve device management data.",
            ) from e

        try:
            # Convert resource records to Pydantic models
            return [ResourceEntity.model_validate(device) for device in devices]
        except ValidationError as e:
            logger.exception("Failed to convert ResourceTable records to ResourceEntity instances.")
            raise exc.InternalHWControlError(
                additional_message="Device management data is in an inconsistent state.",
            ) from e

    # Switch methods
    @validate_call
    def get_active_switch(self, device_id: UUID4) -> SwitchEntity:
        """Get an active switch by device ID.

        A switch is considered active if it has a non-null fm_manager_id.

        Args:
            device_id: UUID of the switch to retrieve.

        Returns:
            The switch entity.

        Raises:
            ValidationError: If device_id is not a valid UUID.
            DeviceNotFoundHWControlError: If the switch does not exist
                or is inactive.
            InternalHWControlError: If the database query fails or
                the database contains unexpected data.
        """
        try:
            target_switch = self._db_session.get(SwitchTable, device_id)
        except SQLAlchemyError as e:
            logger.exception("Failed to retrieve the switch record from the device management database.")
            raise exc.InternalHWControlError(
                additional_message="Failed to retrieve device management data.",
            ) from e

        if target_switch is None:
            raise exc.DeviceNotFoundHWControlError(
                f"No SwitchTable record found for device_id={device_id}.",
                additional_message=f"The target Switch Device ID is: {device_id}.",
            )

        # Check if the switch is active (managed by FM)
        if target_switch.fm_manager_id is None:
            raise exc.DeviceNotFoundHWControlError(
                f"Switch {device_id} exists but is inactive (not managed by FM).",
                additional_message=f"The target Switch Device ID is: {device_id}.",
            )

        try:
            return SwitchEntity.model_validate(target_switch)
        except ValidationError as e:
            logger.exception("Failed to convert the SwitchTable record to a SwitchEntity.")
            raise exc.InternalHWControlError(
                additional_message="Device management data is in an inconsistent state.",
            ) from e

    def get_active_switches(self) -> list[SwitchEntity]:
        """Get all active switches.

        A switch is considered active if it has a non-null fm_manager_id.

        Returns:
            List of active switch entities.

        Raises:
            InternalHWControlError: If the database query fails or
                the database contains unexpected data.
        """
        try:
            # Query switches that are managed by FM (fm_manager_id is not NULL)
            switches = self._db_session.query(SwitchTable).filter(SwitchTable.fm_manager_id.isnot(None)).all()
        except SQLAlchemyError as e:
            logger.exception("Failed to retrieve active switch records from the device management database.")
            raise exc.InternalHWControlError(
                additional_message="Failed to retrieve device management data.",
            ) from e

        try:
            return [SwitchEntity.model_validate(switch) for switch in switches]
        except ValidationError as e:
            logger.exception("Failed to convert SwitchTable records to SwitchEntity instances.")
            raise exc.InternalHWControlError(
                additional_message="Device management data is in an inconsistent state.",
            ) from e

    @validate_call
    def sync_oob(self, oob_sync_model: OOBSyncModel) -> list[OOBSyncEntry]:
        """Synchronize OOB information using full refresh.

        Deletes existing ResourceOOBRelation and OOBController records explicitly,
        recreates OOBController, and rebuilds all resource relations.

        Args:
            oob_sync_model: OOB information to synchronize.

        Returns:
            List of OOBSyncEntry, one per synchronized device.
            Empty list if no devices were provided.

        Raises:
            ValidationError: If oob_sync_model is not an OOBSyncModel instance.
            InternalHWControlError: If the database transaction fails.
        """
        oob_manager_id = oob_sync_model.oob_manager_id
        device_count = len(oob_sync_model.devices)
        logger.info("Starting OOB synchronize.", extra={"oob_manager_id": oob_manager_id, "devices": device_count})

        try:
            # Step 1: Delete existing OOB records explicitly.
            self._db_session.query(ResourceOOBRelationTable).filter_by(oob_manager_id=oob_manager_id).delete()
            self._db_session.query(OOBControllerTable).filter_by(oob_manager_id=oob_manager_id).delete()
            self._db_session.flush()

            # Step 2: Recreate OOB record
            self._db_session.add(OOBControllerTable(oob_manager_id=oob_manager_id))

            # Step 3: Rebuild resource relations
            entries: list[OOBSyncEntry] = []
            for device_model in oob_sync_model.devices:
                resource = self._ensure_resource(device_model)

                self._db_session.add(
                    ResourceOOBRelationTable(
                        device_id=resource.device_id,
                        oob_manager_id=oob_manager_id,
                        oob_device_id=device_model.oob_device_id,
                        device_type=device_model.device_type.value,
                    )
                )
                entries.append(
                    OOBSyncEntry(
                        device_id=resource.device_id,
                        oob_device_id=device_model.oob_device_id,
                        device_type=device_model.device_type,
                    )
                )

            self._db_session.flush()
            self._db_session.commit()
            logger.info("Completed OOB synchronize.", extra={"oob_manager_id": oob_manager_id, "devices": device_count})
            return entries
        except SQLAlchemyError as e:
            self._db_session.rollback()
            logger.exception("Database transaction failed during OOB synchronize.")
            raise exc.InternalHWControlError(
                additional_message="OOB synchronize transaction failed.",
            ) from e

    def _insert_fabric(self, fm_manager_id: str, fabric_model: FabricSyncModel) -> None:
        """Insert a single fabric record.

        Args:
            fm_manager_id: Target FM manager ID.
            fabric_model: Fabric information to insert.
        """
        self._db_session.add(
            FabricTable(
                fm_manager_id=fm_manager_id,
                fabric_id=fabric_model.fabric_id,
            )
        )

    def _ensure_resource(self, resource_model: ResourceSyncModel) -> ResourceTable:
        """Find an existing resource by identity or create a new one.

        Searches in priority order: PCIe identity, CPU identity, device keys.

        Args:
            resource_model: Resource identification to look up.

        Returns:
            The existing or newly created resource record.
        """
        pcie_identity = resource_model.pcie_identity
        cpu_identity = resource_model.cpu_identity

        resource: ResourceTable | None = None
        if pcie_identity is not None:
            resource = (
                self._db_session.query(ResourceTable)
                .filter(
                    ResourceTable.pcie_vendor_id == pcie_identity.pcie_vendor_id,
                    ResourceTable.pcie_device_id == pcie_identity.pcie_device_id,
                    ResourceTable.pcie_device_serial_number == pcie_identity.pcie_device_serial_number,
                )
                .first()
            )

        if resource is None and cpu_identity is not None:
            resource = (
                self._db_session.query(ResourceTable)
                .filter(
                    ResourceTable.cpu_serial_number == cpu_identity.cpu_serial_number,
                    ResourceTable.cpu_manufacturer == cpu_identity.cpu_manufacturer,
                    ResourceTable.cpu_model == cpu_identity.cpu_model,
                )
                .first()
            )

        if resource is None and resource_model.device_keys is not None:
            device_keys_json = json.dumps(resource_model.device_keys, sort_keys=True)
            resource = (
                self._db_session.query(ResourceTable).filter(ResourceTable.device_keys == device_keys_json).first()
            )

        if resource is not None:
            logger.debug("Found existing resource.", extra={"device_id": str(resource.device_id)})
            return resource

        new_device_id = uuid.uuid4()
        logger.debug("Creating new resource.", extra={"device_id": str(new_device_id)})
        resource = ResourceTable(
            device_id=new_device_id,
            cpu_serial_number=cpu_identity.cpu_serial_number if cpu_identity else None,
            cpu_manufacturer=cpu_identity.cpu_manufacturer if cpu_identity else None,
            cpu_model=cpu_identity.cpu_model if cpu_identity else None,
            pcie_vendor_id=pcie_identity.pcie_vendor_id if pcie_identity else None,
            pcie_device_id=pcie_identity.pcie_device_id if pcie_identity else None,
            pcie_device_serial_number=pcie_identity.pcie_device_serial_number if pcie_identity else None,
            device_keys=(
                json.dumps(resource_model.device_keys, sort_keys=True)
                if resource_model.device_keys is not None
                else None
            ),
        )
        self._db_session.add(resource)
        # Flush so a later call in this same sync loop can find this resource via
        # query() above. autoflush=False means an un-flushed row is invisible to
        # query(); without this, the same physical device attached to multiple
        # ports/OOB devices in one sync would be inserted as duplicate resources.
        self._db_session.flush()

        return resource

    def _insert_port(self, fm_manager_id: str, port_model: PortSyncModel) -> FMSyncEntry | None:
        """Insert a single port record.

        Args:
            fm_manager_id: Target FM manager ID.
            port_model: Port information to insert.

        Returns:
            FMSyncEntry if the port has an attached resource, None otherwise.
        """
        device_id = None
        if port_model.attached_resource is not None:
            resource = self._ensure_resource(port_model.attached_resource)
            device_id = resource.device_id

        self._db_session.add(
            PortTable(
                fm_manager_id=fm_manager_id,
                fm_port_id=port_model.fm_port_id,
                fabric_id=port_model.fabric_id,
                fm_switch_id=port_model.fm_switch_id,
                switch_port_type=port_model.switch_port_type.value,
                device_id=device_id,
            )
        )

        if device_id is None:
            return None
        return FMSyncEntry(
            device_id=device_id,
            fm_port_id=port_model.fm_port_id,
            fabric_id=port_model.fabric_id,
            fm_switch_id=port_model.fm_switch_id,
            switch_port_type=port_model.switch_port_type,
        )

    def _upsert_switch(self, fm_manager_id: str, switch_model: SwitchSyncModel) -> SwitchTable:
        """Upsert a single switch record.

        Searches for an existing switch by physical identification.
        If found, updates FM information; otherwise creates a new record.

        Args:
            fm_manager_id: Target FM manager ID.
            switch_model: Switch information to upsert.

        Returns:
            The upserted switch record.
        """
        switch_identity = switch_model.switch_identity

        existing_switch = (
            self._db_session.query(SwitchTable)
            .filter_by(
                serial_number=switch_identity.switch_serial_number,
                manufacturer=switch_identity.switch_manufacturer,
                model=switch_identity.switch_model,
            )
            .first()
        )

        if existing_switch:
            # Existing switch: update FM information
            existing_switch.fm_manager_id = fm_manager_id
            existing_switch.fm_switch_id = switch_model.fm_switch_id
            logger.debug(
                "Updated existing switch.",
                extra={"device_id": str(existing_switch.device_id), "fm_switch_id": switch_model.fm_switch_id},
            )
            return existing_switch

        # Create new switch
        new_device_id = uuid.uuid4()
        logger.debug(
            "Creating new switch.",
            extra={"device_id": str(new_device_id), "fm_switch_id": switch_model.fm_switch_id},
        )
        new_switch = SwitchTable(
            device_id=new_device_id,
            fm_manager_id=fm_manager_id,
            fm_switch_id=switch_model.fm_switch_id,
            serial_number=switch_identity.switch_serial_number,
            manufacturer=switch_identity.switch_manufacturer,
            model=switch_identity.switch_model,
        )
        self._db_session.add(new_switch)
        return new_switch

    @validate_call
    def sync_fm(self, fm_sync_model: FMSyncModel) -> list[FMSyncEntry]:
        """Synchronize FM information using full refresh.

        Deletes existing Port, Fabric, and FM records explicitly,
        recreates FM, and rebuilds all subordinate records.

        Args:
            fm_sync_model: FM information to synchronize.

        Returns:
            List of FMSyncEntry, one per port that has an attached resource.
            Ports without an attached resource are excluded.
            Empty list if no such ports exist.

        Raises:
            ValidationError: If fm_sync_model is not an FMSyncModel instance.
            InternalHWControlError: If the database transaction fails.
        """
        fm_manager_id = fm_sync_model.fm_manager_id
        logger.info(
            "Starting FM synchronize.",
            extra={
                "fm_manager_id": fm_manager_id,
                "switches": len(fm_sync_model.switches),
                "fabrics": len(fm_sync_model.fabrics),
                "ports": len(fm_sync_model.ports),
            },
        )

        try:
            # Step 1: Delete existing FM records explicitly.
            # Deletion order: Port → Fabric → Switch(NULL) → FM.
            # Port must be deleted first to avoid FK constraint violation
            # from the port→fabric and port→switch composite FKs (RESTRICT).
            # Switch fm_manager_id / fm_switch_id must be NULLed explicitly
            # before FM deletion because SwitchTable.fm_manager_id uses RESTRICT.
            self._db_session.query(PortTable).filter_by(fm_manager_id=fm_manager_id).delete()
            self._db_session.query(FabricTable).filter_by(fm_manager_id=fm_manager_id).delete()
            self._db_session.query(SwitchTable).filter_by(fm_manager_id=fm_manager_id).update(
                {"fm_manager_id": None, "fm_switch_id": None}
            )
            self._db_session.query(FMTable).filter_by(fm_manager_id=fm_manager_id).delete()
            self._db_session.flush()

            # Step 2: Recreate FM
            self._db_session.add(FMTable(fm_manager_id=fm_manager_id))
            self._db_session.flush()

            # Step 3: Upsert switches
            for switch_model in fm_sync_model.switches:
                self._upsert_switch(fm_manager_id, switch_model)
            self._db_session.flush()

            # Step 4: Insert fabrics
            for fabric_model in fm_sync_model.fabrics:
                self._insert_fabric(fm_manager_id, fabric_model)
            self._db_session.flush()

            # Step 5: Insert ports
            # fabric_id / fm_switch_id referential integrity already validated by FMSyncModel
            entries: list[FMSyncEntry] = []
            for port_model in fm_sync_model.ports:
                entry = self._insert_port(fm_manager_id, port_model)
                if entry is not None:
                    entries.append(entry)

            self._db_session.flush()
            self._db_session.commit()
            logger.info("Completed FM synchronize.", extra={"fm_manager_id": fm_manager_id})
            return entries
        except SQLAlchemyError as e:
            self._db_session.rollback()
            logger.exception("Database transaction failed during FM synchronize.")
            raise exc.InternalHWControlError(
                additional_message="FM synchronize transaction failed.",
            ) from e

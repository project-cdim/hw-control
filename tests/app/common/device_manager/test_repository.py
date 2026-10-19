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

"""Unit tests for DeviceRepository."""

import logging
import uuid
from unittest.mock import MagicMock

import pytest
from pydantic import TypeAdapter, ValidationError
from pytest_mock import MockFixture
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import app.common.basic_exceptions as exc
from app.common import constants
from app.common.device_manager.repository import (
    CPUIdentity,
    DeviceRepository,
    FabricSyncModel,
    FMSyncEntry,
    FMSyncModel,
    OOBResourceSyncModel,
    OOBSyncEntry,
    OOBSyncModel,
    PCIeIdentity,
    PortSyncModel,
    ResourceSyncModel,
    SwitchIdentity,
    SwitchSyncModel,
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


def _make_resource_table(
    device_id: uuid.UUID | None = None,
    ports: list | None = None,
    oob_relations: list | None = None,
) -> ResourceTable:
    """Create a transient ResourceTable with preset attributes."""
    resource = ResourceTable()
    resource.device_id = device_id or uuid.uuid4()
    resource.ports = ports if ports is not None else []
    resource.oob_relations = oob_relations if oob_relations is not None else []
    return resource


def _make_port_table(
    fm_manager_id: str = "fm-1",
    fm_port_id: str = "port-1",
    fabric_id: str = "fabric-1",
    fm_switch_id: str = "sw-1",
) -> PortTable:
    """Create a transient PortTable with preset attributes."""
    port = PortTable()
    port.fm_manager_id = fm_manager_id
    port.fm_port_id = fm_port_id
    port.fabric_id = fabric_id
    port.fm_switch_id = fm_switch_id
    port.switch_port_type = constants.SwitchPortType.DSP.value
    port.device_id = None
    return port


def _make_oob_relation_table(
    oob_manager_id: str = "oob-1",
    oob_device_id: str = "oob-dev-1",
    device_type: constants.DeviceType = constants.DeviceType.CPU,
) -> ResourceOOBRelationTable:
    """Create a transient ResourceOOBRelationTable with preset attributes."""
    oob_rel = ResourceOOBRelationTable()
    oob_rel.oob_manager_id = oob_manager_id
    oob_rel.oob_device_id = oob_device_id
    oob_rel.device_type = device_type.value
    return oob_rel


def _make_switch_table(
    device_id: uuid.UUID | None = None,
    fm_manager_id: str | None = "fm-1",
    fm_switch_id: str | None = "sw-1",
) -> SwitchTable:
    """Create a transient SwitchTable with preset attributes."""
    switch = SwitchTable()
    switch.device_id = device_id or uuid.uuid4()
    switch.fm_manager_id = fm_manager_id
    switch.fm_switch_id = fm_switch_id
    switch.serial_number = "SN001"
    switch.manufacturer = "example_manufacturer"
    switch.model = "example_model"
    return switch


def _make_validation_error() -> ValidationError:
    """Create a ValidationError instance for testing purposes."""
    try:
        TypeAdapter(int).validate_python("not_an_int")
    except ValidationError as e:
        return e
    raise AssertionError("Expected ValidationError was not raised")  # pragma: no cover


class TestDeviceRepositoryInit:
    """Tests for DeviceRepository.__init__()."""

    def test_init_stores_session(self) -> None:
        """Verifies that the provided session is stored as the internal DB session."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock
        mock_session = MagicMock(spec=Session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        repository = DeviceRepository(mock_session)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert repository._db_session is mock_session


class TestDeviceRepositoryGetActiveResource:
    """Tests for DeviceRepository.get_active_resource()."""

    def test_get_active_resource_returns_entity_when_active_with_port(self) -> None:
        """Verifies that an entity is returned for a resource that has at least one port."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        device_id = uuid.uuid4()
        resource = _make_resource_table(device_id=device_id, ports=[_make_port_table()])

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_session.get.return_value = resource

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = repository.get_active_resource(device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result.device_id == device_id

    def test_get_active_resource_returns_entity_when_active_with_oob(self) -> None:
        """Verifies that an entity is returned for a resource that has at least one OOB relation."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        device_id = uuid.uuid4()
        resource = _make_resource_table(device_id=device_id, oob_relations=[_make_oob_relation_table()])

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_session.get.return_value = resource

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = repository.get_active_resource(device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result.device_id == device_id

    def test_get_active_resource_raises_when_not_found(self) -> None:
        """Verifies that DeviceNotFoundHWControlError is raised when no resource exists."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        device_id = uuid.uuid4()

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_session.get.return_value = None

        repository = DeviceRepository(mock_session)

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(exc.DeviceNotFoundHWControlError):
            repository.get_active_resource(device_id)

    def test_get_active_resource_raises_when_inactive(self) -> None:
        """Verifies that DeviceNotFoundHWControlError is raised when resource has no ports or OOB relations."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        device_id = uuid.uuid4()
        resource = _make_resource_table(device_id=device_id, ports=[], oob_relations=[])

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_session.get.return_value = resource

        repository = DeviceRepository(mock_session)

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(exc.DeviceNotFoundHWControlError):
            repository.get_active_resource(device_id)

    def test_get_active_resource_raises_internal_error_on_db_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        """Verifies that InternalHWControlError is raised and an error is logged when the database query fails."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        device_id = uuid.uuid4()

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_session.get.side_effect = SQLAlchemyError("DB connection failed")

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.ERROR, logger="app.common.device_manager.repository"):
            with pytest.raises(exc.InternalHWControlError):
                repository.get_active_resource(device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1
        error_log = caplog.records[0]
        assert error_log.levelname == "ERROR"
        assert error_log.getMessage() == "Failed to retrieve the resource record from the device management database."

    def test_get_active_resource_raises_internal_error_on_validation_error(
        self, mocker: MockFixture, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verifies that InternalHWControlError is raised and an error is logged when model_validate fails."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        device_id = uuid.uuid4()
        resource = _make_resource_table(device_id=device_id, ports=[_make_port_table()])

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_session.get.return_value = resource

        repository = DeviceRepository(mock_session)
        mocker.patch(
            "app.common.device_manager.repository.ResourceEntity.model_validate",
            side_effect=_make_validation_error(),
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.ERROR, logger="app.common.device_manager.repository"):
            with pytest.raises(exc.InternalHWControlError):
                repository.get_active_resource(device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1
        error_log = caplog.records[0]
        assert error_log.levelname == "ERROR"
        assert error_log.getMessage() == "Failed to convert the ResourceTable record to a ResourceEntity."


class TestDeviceRepositoryGetActiveResources:
    """Tests for DeviceRepository.get_active_resources()."""

    def test_get_active_resources_returns_entity_list(self) -> None:
        """Verifies that a list of entities is returned for active resources."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        resource1 = _make_resource_table(ports=[_make_port_table()])
        resource2 = _make_resource_table(oob_relations=[_make_oob_relation_table()])

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.all.return_value = [resource1, resource2]

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = repository.get_active_resources()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(result) == 2

    def test_get_active_resources_returns_empty_list_when_none(self) -> None:
        """Verifies that an empty list is returned when no active resources exist."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.all.return_value = []

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = repository.get_active_resources()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result == []

    def test_get_active_resources_raises_internal_error_on_db_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        """Verifies that InternalHWControlError is raised and an error is logged when the database query fails."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.all.side_effect = SQLAlchemyError("DB connection failed")

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.ERROR, logger="app.common.device_manager.repository"):
            with pytest.raises(exc.InternalHWControlError):
                repository.get_active_resources()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1
        error_log = caplog.records[0]
        assert error_log.levelname == "ERROR"
        assert (
            error_log.getMessage() == "Failed to retrieve active resource records from the device management database."
        )

    def test_get_active_resources_raises_internal_error_on_validation_error(
        self, mocker: MockFixture, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verifies that InternalHWControlError is raised and an error is logged when model_validate fails."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.outerjoin.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.all.return_value = [_make_resource_table(ports=[_make_port_table()])]

        repository = DeviceRepository(mock_session)
        mocker.patch(
            "app.common.device_manager.repository.ResourceEntity.model_validate",
            side_effect=_make_validation_error(),
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.ERROR, logger="app.common.device_manager.repository"):
            with pytest.raises(exc.InternalHWControlError):
                repository.get_active_resources()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1
        error_log = caplog.records[0]
        assert error_log.levelname == "ERROR"
        assert error_log.getMessage() == "Failed to convert ResourceTable records to ResourceEntity instances."


class TestDeviceRepositoryGetActiveSwitch:
    """Tests for DeviceRepository.get_active_switch()."""

    def test_get_active_switch_returns_entity(self) -> None:
        """Verifies that an entity is returned for an active switch."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        device_id = uuid.uuid4()
        switch = _make_switch_table(device_id=device_id)

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_session.get.return_value = switch

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = repository.get_active_switch(device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result.device_id == device_id
        assert result.fm_manager_id == "fm-1"

    def test_get_active_switch_raises_when_not_found(self) -> None:
        """Verifies that DeviceNotFoundHWControlError is raised when no switch exists."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        device_id = uuid.uuid4()

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_session.get.return_value = None

        repository = DeviceRepository(mock_session)

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(exc.DeviceNotFoundHWControlError):
            repository.get_active_switch(device_id)

    def test_get_active_switch_raises_when_inactive(self) -> None:
        """Verifies that DeviceNotFoundHWControlError is raised when switch has no fm_manager_id."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        device_id = uuid.uuid4()
        switch = _make_switch_table(device_id=device_id, fm_manager_id=None, fm_switch_id=None)

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_session.get.return_value = switch

        repository = DeviceRepository(mock_session)

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(exc.DeviceNotFoundHWControlError):
            repository.get_active_switch(device_id)

    def test_get_active_switch_raises_internal_error_on_db_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        """Verifies that InternalHWControlError is raised and an error is logged when the database query fails."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        device_id = uuid.uuid4()

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_session.get.side_effect = SQLAlchemyError("DB connection failed")

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.ERROR, logger="app.common.device_manager.repository"):
            with pytest.raises(exc.InternalHWControlError):
                repository.get_active_switch(device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1
        error_log = caplog.records[0]
        assert error_log.levelname == "ERROR"
        assert error_log.getMessage() == "Failed to retrieve the switch record from the device management database."

    def test_get_active_switch_raises_internal_error_on_validation_error(
        self, mocker: MockFixture, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verifies that InternalHWControlError is raised and an error is logged when model_validate fails."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        device_id = uuid.uuid4()
        switch = _make_switch_table(device_id=device_id)

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_session.get.return_value = switch

        repository = DeviceRepository(mock_session)
        mocker.patch(
            "app.common.device_manager.repository.SwitchEntity.model_validate",
            side_effect=_make_validation_error(),
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.ERROR, logger="app.common.device_manager.repository"):
            with pytest.raises(exc.InternalHWControlError):
                repository.get_active_switch(device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1
        error_log = caplog.records[0]
        assert error_log.levelname == "ERROR"
        assert error_log.getMessage() == "Failed to convert the SwitchTable record to a SwitchEntity."


class TestDeviceRepositoryGetActiveSwitches:
    """Tests for DeviceRepository.get_active_switches()."""

    def test_get_active_switches_returns_entity_list(self) -> None:
        """Verifies that a list of entities is returned for active switches."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        switch1 = _make_switch_table()
        switch2 = _make_switch_table(fm_manager_id="fm-2", fm_switch_id="sw-2")

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [switch1, switch2]

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = repository.get_active_switches()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(result) == 2

    def test_get_active_switches_raises_internal_error_on_db_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        """Verifies that InternalHWControlError is raised and an error is logged when the database query fails."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.side_effect = SQLAlchemyError("DB connection failed")

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.ERROR, logger="app.common.device_manager.repository"):
            with pytest.raises(exc.InternalHWControlError):
                repository.get_active_switches()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1
        error_log = caplog.records[0]
        assert error_log.levelname == "ERROR"
        assert error_log.getMessage() == "Failed to retrieve active switch records from the device management database."

    def test_get_active_switches_raises_internal_error_on_validation_error(
        self, mocker: MockFixture, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verifies that InternalHWControlError is raised and an error is logged when model_validate fails."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [_make_switch_table()]

        repository = DeviceRepository(mock_session)
        mocker.patch(
            "app.common.device_manager.repository.SwitchEntity.model_validate",
            side_effect=_make_validation_error(),
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.ERROR, logger="app.common.device_manager.repository"):
            with pytest.raises(exc.InternalHWControlError):
                repository.get_active_switches()

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1
        error_log = caplog.records[0]
        assert error_log.levelname == "ERROR"
        assert error_log.getMessage() == "Failed to convert SwitchTable records to SwitchEntity instances."


class TestDeviceRepositoryInsertFabric:
    """Tests for DeviceRepository._insert_fabric()."""

    def test_insert_fabric_adds_fabric_table(self) -> None:
        """Verifies that a FabricTable record is added to the session with the given IDs."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        fabric_model = FabricSyncModel(fabric_id="fabric-1")

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        repository._insert_fabric("fm-1", fabric_model)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        mock_session.add.assert_called_once()
        added_fabric = mock_session.add.call_args.args[0]
        assert isinstance(added_fabric, FabricTable)
        assert added_fabric.fm_manager_id == "fm-1"
        assert added_fabric.fabric_id == "fabric-1"


class TestDeviceRepositoryEnsureResource:
    """Tests for DeviceRepository._ensure_resource()."""

    def test_ensure_resource_finds_existing_by_pcie_identity(self) -> None:
        """Verifies that an existing resource is returned when matched by PCIe identity."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        existing = _make_resource_table()
        identity = ResourceSyncModel(
            pcie_identity=PCIeIdentity(
                pcie_vendor_id="abcd",
                pcie_device_id="1234",
                pcie_device_serial_number="0123456789abcdef",
            )
        )

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = repository._ensure_resource(identity)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result is existing
        mock_session.add.assert_not_called()

    def test_ensure_resource_finds_existing_by_cpu_identity(self) -> None:
        """Verifies that an existing resource is returned when matched by CPU identity (no PCIe)."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        existing = _make_resource_table()
        identity = ResourceSyncModel(
            cpu_identity=CPUIdentity(
                cpu_serial_number="CPU-SN-001",
                cpu_manufacturer="example_manufacturer",
                cpu_model="example_model",
            )
        )

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = repository._ensure_resource(identity)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result is existing
        mock_session.add.assert_not_called()

    def test_ensure_resource_finds_existing_by_device_keys(self) -> None:
        """Verifies that an existing resource is returned when matched by device_keys (no PCIe/CPU)."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        existing = _make_resource_table()
        identity = ResourceSyncModel(device_keys={"vendor_id": "abc", "serial": "123"})

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = repository._ensure_resource(identity)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result is existing
        mock_session.add.assert_not_called()

    def test_ensure_resource_device_keys_sorted_for_search(self) -> None:
        """Verifies that device_keys are JSON-serialized with sorted keys when searching for existing resources."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values with keys in reverse alphabetical order
        identity = ResourceSyncModel(device_keys={"z_key": "value3", "b_key": "value2", "a_key": "value1"})

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # Not found, will create new

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        repository._ensure_resource(identity)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # Verify that filter() was called with sorted JSON (keys in alphabetical order)
        expected_json = '{"a_key": "value1", "b_key": "value2", "z_key": "value3"}'
        mock_query.filter.assert_called_once()

        # Extract the filter condition
        filter_call_args = mock_query.filter.call_args[0][0]
        # The filter condition is a comparison expression (ResourceTable.device_keys == expected_json)
        # We can verify by checking the right side of the comparison
        assert filter_call_args.right.value == expected_json

    def test_ensure_resource_device_keys_sorted_for_creation(self) -> None:
        """Verifies that device_keys are JSON-serialized with sorted keys when creating new resources."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values with nested dict and keys in reverse alphabetical order
        identity = ResourceSyncModel(
            device_keys={
                "z_key": {"nested_z": "value_z", "nested_a": "value_a"},
                "b_key": "value2",
                "a_key": "value1",
            }
        )

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # Not found, will create new

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = repository._ensure_resource(identity)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # Verify that the created resource has sorted JSON in device_keys
        # Both top-level and nested keys should be in alphabetical order
        expected_json = (
            '{"a_key": "value1", "b_key": "value2", "z_key": {"nested_a": "value_a", "nested_z": "value_z"}}'
        )
        assert result.device_keys == expected_json
        mock_session.add.assert_called_once_with(result)

    def test_ensure_resource_creates_new_when_not_found(self) -> None:
        """Verifies that a new resource is created and added to the session when no match is found."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        identity = ResourceSyncModel(
            pcie_identity=PCIeIdentity(
                pcie_vendor_id="abcd",
                pcie_device_id="1234",
                pcie_device_serial_number="0123456789abcdef",
            )
        )

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = repository._ensure_resource(identity)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        mock_session.add.assert_called_once_with(result)


class TestDeviceRepositoryUpsertSwitch:
    """Tests for DeviceRepository._upsert_switch()."""

    def test_upsert_switch_updates_existing_switch(self) -> None:
        """Verifies that fm_manager_id and fm_switch_id are updated when an existing switch is found."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        existing = _make_switch_table(fm_manager_id="fm-old", fm_switch_id="sw-old")
        switch_model = SwitchSyncModel(
            fm_switch_id="sw-new",
            switch_identity=SwitchIdentity(
                switch_serial_number="SN001",
                switch_manufacturer="example_manufacturer",
                switch_model="example_model",
            ),
        )

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = existing

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = repository._upsert_switch("fm-new", switch_model)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result is existing
        assert result.fm_manager_id == "fm-new"
        assert result.fm_switch_id == "sw-new"
        mock_session.add.assert_not_called()

    def test_upsert_switch_creates_new_switch(self) -> None:
        """Verifies that a new switch record is created and added to the session when not found."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        switch_model = SwitchSyncModel(
            fm_switch_id="sw-new",
            switch_identity=SwitchIdentity(
                switch_serial_number="SN999",
                switch_manufacturer="example_manufacturer",
                switch_model="example_model",
            ),
        )

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = None

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = repository._upsert_switch("fm-1", switch_model)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        mock_session.add.assert_called_once_with(result)
        assert result.fm_manager_id == "fm-1"
        assert result.fm_switch_id == "sw-new"


class TestDeviceRepositoryInsertPort:
    """Tests for DeviceRepository._insert_port()."""

    def test_insert_port_without_attached_resource_returns_none(self, mocker: MockFixture) -> None:
        """Verifies that a port without attached_resource is inserted with device_id=None and returns None."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        port_model = PortSyncModel(
            fm_port_id="port-1",
            fabric_id="fabric-1",
            fm_switch_id="sw-1",
            switch_port_type=constants.SwitchPortType.USP,
        )

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        repository = DeviceRepository(mock_session)
        mock_ensure_resource = mocker.patch.object(repository, "_ensure_resource")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = repository._insert_port("fm-1", port_model)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert result is None
        mock_ensure_resource.assert_not_called()
        mock_session.add.assert_called_once()
        added_port = mock_session.add.call_args.args[0]
        assert added_port.fm_manager_id == "fm-1"
        assert added_port.fm_port_id == "port-1"
        assert added_port.fabric_id == "fabric-1"
        assert added_port.fm_switch_id == "sw-1"
        assert added_port.device_id is None

    def test_insert_port_with_attached_resource_returns_fm_sync_entry(self, mocker: MockFixture) -> None:
        """Verifies a port with attached_resource is inserted with the resolved device_id and returns FMSyncEntry."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        device_id = uuid.uuid4()
        port_model = PortSyncModel(
            fm_port_id="port-1",
            fabric_id="fabric-1",
            fm_switch_id="sw-1",
            switch_port_type=constants.SwitchPortType.DSP,
            attached_resource=ResourceSyncModel(
                pcie_identity=PCIeIdentity(
                    pcie_vendor_id="abcd",
                    pcie_device_id="1234",
                    pcie_device_serial_number="0123456789abcdef",
                )
            ),
        )

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        repository = DeviceRepository(mock_session)
        mock_ensure_resource = mocker.patch.object(
            repository, "_ensure_resource", return_value=_make_resource_table(device_id=device_id)
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = repository._insert_port("fm-1", port_model)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        mock_ensure_resource.assert_called_once_with(port_model.attached_resource)
        mock_session.add.assert_called_once()
        added_port = mock_session.add.call_args.args[0]
        assert added_port.device_id == device_id

        assert isinstance(result, FMSyncEntry)
        assert result.device_id == device_id
        assert result.fm_port_id == "port-1"
        assert result.fabric_id == "fabric-1"
        assert result.fm_switch_id == "sw-1"
        assert result.switch_port_type == constants.SwitchPortType.DSP


class TestDeviceRepositorySyncOob:
    """Tests for DeviceRepository.sync_oob()."""

    def test_sync_oob_commits_transaction_on_success(
        self, mocker: MockFixture, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verifies transaction management and logging when sync_oob succeeds."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        oob_model = OOBSyncModel(
            oob_manager_id="oob-1",
            devices=[
                OOBResourceSyncModel(
                    oob_device_id="oob-dev-1",
                    device_type=constants.DeviceType.CPU,
                    pcie_identity=PCIeIdentity(
                        pcie_vendor_id="abcd",
                        pcie_device_id="1234",
                        pcie_device_serial_number="0123456789abcdef",
                    ),
                )
            ],
        )

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        repository = DeviceRepository(mock_session)
        mocker.patch.object(repository, "_ensure_resource", return_value=_make_resource_table())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="app.common.device_manager.repository"):
            result = repository.sync_oob(oob_model)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()
        assert len(result) == 1
        assert isinstance(result[0], OOBSyncEntry)
        assert result[0].oob_device_id == "oob-dev-1"

        assert len(caplog.records) == 2

        start_log = caplog.records[0]
        assert start_log.levelname == "INFO"
        assert start_log.getMessage() == "Starting OOB synchronize."
        assert hasattr(start_log, "oob_manager_id"), "oob_manager_id should be present in the log record"
        assert getattr(start_log, "oob_manager_id") == "oob-1"
        assert hasattr(start_log, "devices"), "devices should be present in the log record"
        assert getattr(start_log, "devices") == 1

        complete_log = caplog.records[1]
        assert complete_log.levelname == "INFO"
        assert complete_log.getMessage() == "Completed OOB synchronize."
        assert hasattr(complete_log, "oob_manager_id"), "oob_manager_id should be present in the log record"
        assert getattr(complete_log, "oob_manager_id") == "oob-1"
        assert hasattr(complete_log, "devices"), "devices should be present in the log record"
        assert getattr(complete_log, "devices") == 1

    def test_sync_oob_rollbacks_on_sqlalchemy_error(self) -> None:
        """Verifies that rollback is called and InternalHWControlError is raised on DB failure."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        oob_model = OOBSyncModel(oob_manager_id="oob-1", devices=[])

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session.flush.side_effect = SQLAlchemyError("DB failure")

        repository = DeviceRepository(mock_session)

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(exc.InternalHWControlError):
            repository.sync_oob(oob_model)
        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()

    def test_sync_oob_logs_error_on_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        """Verifies that info and error logs are emitted when sync_oob fails."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        oob_model = OOBSyncModel(oob_manager_id="oob-1", devices=[])

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session.flush.side_effect = SQLAlchemyError("DB failure")

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="app.common.device_manager.repository"):
            with pytest.raises(exc.InternalHWControlError):
                repository.sync_oob(oob_model)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 2

        start_log = caplog.records[0]
        assert start_log.levelname == "INFO"
        assert start_log.getMessage() == "Starting OOB synchronize."
        assert hasattr(start_log, "oob_manager_id"), "oob_manager_id should be present in the log record"
        assert getattr(start_log, "oob_manager_id") == "oob-1"
        assert hasattr(start_log, "devices"), "devices should be present in the log record"
        assert getattr(start_log, "devices") == 0

        error_log = caplog.records[1]
        assert error_log.levelname == "ERROR"
        assert error_log.getMessage() == "Database transaction failed during OOB synchronize."

    def test_sync_oob_deletes_existing_oob_before_recreating(self) -> None:
        """Verifies ResourceOOBRelation then OOBController are explicitly deleted before recreating."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        oob_model = OOBSyncModel(oob_manager_id="oob-1", devices=[])

        # Set up the mock
        mock_session = MagicMock(spec=Session)

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        repository.sync_oob(oob_model)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # Verify explicit delete() calls in correct order:
        # ResourceOOBRelationTable first, then OOBControllerTable
        delete_calls = mock_session.query.return_value.filter_by.return_value.delete.call_args_list
        assert len(delete_calls) == 2
        queried_tables = [call.args[0] for call in mock_session.query.call_args_list]
        assert queried_tables[0] is ResourceOOBRelationTable
        assert queried_tables[1] is OOBControllerTable
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_called_once()


class TestDeviceRepositorySyncFm:
    """Tests for DeviceRepository.sync_fm()."""

    def test_sync_fm_commits_transaction_on_success(
        self, mocker: MockFixture, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Verifies transaction management and logging when sync_fm succeeds."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        fm_model = FMSyncModel(
            fm_manager_id="fm-1",
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw-1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN001",
                        switch_manufacturer="example_manufacturer",
                        switch_model="example_model",
                    ),
                )
            ],
            fabrics=[FabricSyncModel(fabric_id="fabric-1")],
            ports=[
                PortSyncModel(
                    fm_port_id="port-1",
                    fabric_id="fabric-1",
                    fm_switch_id="sw-1",
                    switch_port_type=constants.SwitchPortType.DSP,
                )
            ],
        )

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        repository = DeviceRepository(mock_session)
        mocker.patch.object(repository, "_upsert_switch", return_value=_make_switch_table())
        mocker.patch.object(repository, "_ensure_resource", return_value=_make_resource_table())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="app.common.device_manager.repository"):
            result = repository.sync_fm(fm_model)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        mock_session.commit.assert_called_once()
        mock_session.rollback.assert_not_called()
        assert len(result) == 0

        assert len(caplog.records) == 2

        start_log = caplog.records[0]
        assert start_log.levelname == "INFO"
        assert start_log.getMessage() == "Starting FM synchronize."
        assert hasattr(start_log, "fm_manager_id"), "fm_manager_id should be present in the log record"
        assert getattr(start_log, "fm_manager_id") == "fm-1"
        assert hasattr(start_log, "switches"), "switches should be present in the log record"
        assert getattr(start_log, "switches") == 1
        assert hasattr(start_log, "fabrics"), "fabrics should be present in the log record"
        assert getattr(start_log, "fabrics") == 1
        assert hasattr(start_log, "ports"), "ports should be present in the log record"
        assert getattr(start_log, "ports") == 1

        complete_log = caplog.records[1]
        assert complete_log.levelname == "INFO"
        assert complete_log.getMessage() == "Completed FM synchronize."
        assert hasattr(complete_log, "fm_manager_id"), "fm_manager_id should be present in the log record"
        assert getattr(complete_log, "fm_manager_id") == "fm-1"

    def test_sync_fm_rollbacks_on_sqlalchemy_error(self) -> None:
        """Verifies that rollback is called and InternalHWControlError is raised on DB failure."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        fm_model = FMSyncModel(fm_manager_id="fm-1")

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session.flush.side_effect = SQLAlchemyError("DB failure")

        repository = DeviceRepository(mock_session)

        # ++++ execution and inspection +++++++++++++++++++++++++++++++#
        with pytest.raises(exc.InternalHWControlError):
            repository.sync_fm(fm_model)
        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()

    def test_sync_fm_logs_error_on_failure(self, caplog: pytest.LogCaptureFixture) -> None:
        """Verifies that info and error logs are emitted when sync_fm fails."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        fm_model = FMSyncModel(fm_manager_id="fm-1")

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session.flush.side_effect = SQLAlchemyError("DB failure")

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.INFO, logger="app.common.device_manager.repository"):
            with pytest.raises(exc.InternalHWControlError):
                repository.sync_fm(fm_model)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 2

        start_log = caplog.records[0]
        assert start_log.levelname == "INFO"
        assert start_log.getMessage() == "Starting FM synchronize."
        assert hasattr(start_log, "fm_manager_id"), "fm_manager_id should be present in the log record"
        assert getattr(start_log, "fm_manager_id") == "fm-1"
        assert hasattr(start_log, "switches"), "switches should be present in the log record"
        assert getattr(start_log, "switches") == 0
        assert hasattr(start_log, "fabrics"), "fabrics should be present in the log record"
        assert getattr(start_log, "fabrics") == 0
        assert hasattr(start_log, "ports"), "ports should be present in the log record"
        assert getattr(start_log, "ports") == 0

        error_log = caplog.records[1]
        assert error_log.levelname == "ERROR"
        assert error_log.getMessage() == "Database transaction failed during FM synchronize."

    def test_sync_fm_deletes_existing_fm_before_recreating(self) -> None:
        """Verifies Port, Fabric, FM are explicitly deleted and Switch is NULLed in order before recreating."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        fm_model = FMSyncModel(fm_manager_id="fm-1")

        # Set up the mock
        mock_session = MagicMock(spec=Session)

        repository = DeviceRepository(mock_session)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        repository.sync_fm(fm_model)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        # Verify query call order: Port(delete) → Fabric(delete) → Switch(update) → FM(delete)
        queried_tables = [call.args[0] for call in mock_session.query.call_args_list]
        assert queried_tables[0] is PortTable
        assert queried_tables[1] is FabricTable
        assert queried_tables[2] is SwitchTable
        assert queried_tables[3] is FMTable

        # Verify Switch was updated to NULL (not deleted)
        mock_session.query.return_value.filter_by.return_value.update.assert_called_once_with(
            {"fm_manager_id": None, "fm_switch_id": None}
        )
        mock_session.delete.assert_not_called()
        mock_session.commit.assert_called_once()

    def test_sync_fm_inserts_port_with_attached_resource(self, mocker: MockFixture) -> None:
        """Verifies that _ensure_resource is called when a port has an attached resource."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        # Set up the input values
        fm_model = FMSyncModel(
            fm_manager_id="fm-1",
            switches=[
                SwitchSyncModel(
                    fm_switch_id="sw-1",
                    switch_identity=SwitchIdentity(
                        switch_serial_number="SN001",
                        switch_manufacturer="example_manufacturer",
                        switch_model="example_model",
                    ),
                )
            ],
            fabrics=[FabricSyncModel(fabric_id="fabric-1")],
            ports=[
                PortSyncModel(
                    fm_port_id="port-1",
                    fabric_id="fabric-1",
                    fm_switch_id="sw-1",
                    switch_port_type=constants.SwitchPortType.DSP,
                    attached_resource=ResourceSyncModel(
                        pcie_identity=PCIeIdentity(
                            pcie_vendor_id="abcd",
                            pcie_device_id="1234",
                            pcie_device_serial_number="0123456789abcdef",
                        )
                    ),
                )
            ],
        )

        # Set up the mock
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        repository = DeviceRepository(mock_session)
        mocker.patch.object(repository, "_upsert_switch", return_value=_make_switch_table())
        mock_ensure_resource = mocker.patch.object(repository, "_ensure_resource", return_value=_make_resource_table())

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        result = repository.sync_fm(fm_model)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        mock_session.commit.assert_called_once()
        mock_ensure_resource.assert_called_once()
        assert len(result) == 1
        assert isinstance(result[0], FMSyncEntry)
        assert result[0].fm_port_id == "port-1"

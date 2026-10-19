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

"""Device manager package.

Manages devices handled by hw-control in a database.
Provides repository classes and models as interfaces for table access.
Also provides a Database manager to manage connections to the DBMS.
"""

from app.common.device_manager.db_manager import DBManager
from app.common.device_manager.repository import (
    BaseSyncModel,
    CPUIdentity,
    DeviceRepository,
    EntityBaseModel,
    FabricSyncModel,
    FMSyncEntry,
    FMSyncModel,
    OOBResourceSyncModel,
    OOBSyncEntry,
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

__all__ = [
    # Database manager
    "DBManager",
    # Repository
    "DeviceRepository",
    # Identity models
    "PCIeIdentity",
    "CPUIdentity",
    "SwitchIdentity",
    # Entity models
    "EntityBaseModel",
    "PortEntity",
    "ResourceOOBRelation",
    "ResourceEntity",
    "SwitchEntity",
    # Sync models
    "BaseSyncModel",
    "ResourceSyncModel",
    "PortSyncModel",
    "FabricSyncModel",
    "SwitchSyncModel",
    "OOBResourceSyncModel",
    "OOBSyncModel",
    "FMSyncModel",
    # Sync result models
    "OOBSyncEntry",
    "FMSyncEntry",
]

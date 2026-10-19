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
# under the License.

"""Data types returned by the ServicePlugin execution class methods.

File: hw-control/src/app/common/plugin/models.py

This module must not import any other HW Control module so that it can be
reused as-is by a remote plugin implemented in Python.
"""

import re
from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints, ValidationInfo

_CONTROL_CHARS_PATTERN = re.compile(r"[\x00-\x1F\x7F-\x9F]")


def _reject_control_chars_and_blank(value: str) -> str:
    """Reject strings that are blank or contain control characters."""
    if not value.strip() or _CONTROL_CHARS_PATTERN.search(value):
        raise ValueError("must be a non-blank string without control characters")
    return value


_ELEMENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9._~-]+$")


def _validate_element_id(value: str, info: ValidationInfo) -> str:
    """Validate an element identifier unless the context skips the check.

    The "." and ".." path segments are rejected separately: they carry a
    path-traversal meaning even though "/" itself is already excluded by
    the pattern. This only guards against a lone "." or "..", not a full
    "../" traversal chain.

    Args:
        value (str): Value to validate.
        info (ValidationInfo): Validation info supplied by pydantic.

    Returns:
        str: The value as given.

    Raises:
        ValueError: The value is not a valid element identifier.

    Note:
        When the validation context contains skip_element_id_check=True,
        the check is bypassed so that an identifier returned by a legacy
        plugin (a plain str, not constrained to ElementID) can be
        converted without failing.
    """
    context = info.context if isinstance(info.context, dict) else {}
    if context.get("skip_element_id_check"):
        return value
    if not _ELEMENT_ID_PATTERN.match(value):
        raise ValueError("must consist only of RFC 3986 unreserved characters")
    if value in {".", ".."}:
        raise ValueError('must not be "." or ".."')
    return value


# RFC 3986 unreserved characters (alphanumeric, "-", ".", "_", "~"), excluding
# the "." and ".." path segments.
# Used for element identifiers, which are embedded in URL path parameters,
# so that no encoding is required.
ElementID = Annotated[str, AfterValidator(_validate_element_id)]

# String type used for text returned by plugins.
# Control characters (U+0000-U+001F, U+007F-U+009F) and whitespace-only
# strings (which also covers the empty string) are rejected to keep returned
# data and log output well-formed. _reject_control_chars_and_blank alone
# covers both checks, so no separate min_length constraint is needed.
VisibleString = Annotated[str, AfterValidator(_reject_control_chars_and_blank)]

# LTSSM state of a PCIe port.
LTSSMState = Literal[
    "L0", "L0s", "L1", "L2", "Detect", "Polling", "Configuration", "Recovery", "HotReset", "Disabled", "Loopback"
]

# 4-digit hexadecimal string, used for PCIeIdentity.pcie_vendor_id/pcie_device_id.
_HexID4 = Annotated[str, StringConstraints(pattern=r"^[0-9a-fA-F]{4}$")]

# 16-digit hexadecimal string, used for PCIeIdentity.pcie_device_serial_number.
_HexID16 = Annotated[str, StringConstraints(pattern=r"^[0-9a-fA-F]{16}$")]

# HTTP status code carried in an error body, used for ErrorBaseModel.status.
# Restricted to the 3-digit range defined for HTTP status codes.
_HTTPStatusCode = Annotated[int, Field(ge=100, le=599)]

# API version of a remote plugin. Currently only "v1" is supported.
PluginInterfaceVersion = Literal["v1"]


class DeviceType(StrEnum):
    """Device type as returned by a plugin.

    This is redefined here (in addition to app.common.constants.DeviceType)
    because this module must not depend on the rest of HW Control.
    """

    ACCELERATOR = "Accelerator"
    CPU = "CPU"
    DSP = "DSP"
    FPGA = "FPGA"
    GPU = "GPU"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORKINTERFACE = "networkInterface"
    GRAPHICCONTROLLER = "graphicController"
    SWITCH = "switch"
    UNKNOWN = "unknown"


class SwitchPortType(StrEnum):
    """Switch port type as returned by a plugin.

    This is redefined here (in addition to app.common.constants.SwitchPortType)
    because this module must not depend on the rest of HW Control.
    """

    USP = "USP"
    DSP = "DSP"


class PowerState(StrEnum):
    """Power state of an element."""

    ON = "On"
    OFF = "Off"
    PAUSED = "Paused"
    POWERING_OFF = "PoweringOff"
    POWERING_ON = "PoweringOn"
    UNKNOWN = "Unknown"


class ExecuteElementAction(StrEnum):
    """Action executed on an element by ServicePlugin.power_on/power_off/os_shutdown/cpu_reset."""

    POWER_ON = "power-on"
    POWER_OFF = "power-off"
    CPU_RESET = "cpu-reset"
    OS_SHUTDOWN = "os-shutdown"


class ExecuteConnectionAction(StrEnum):
    """Action executed on a connection by ServicePlugin.add_connection/remove_connection."""

    CONNECT = "connect"
    DISCONNECT = "disconnect"


class PluginFunctionName(StrEnum):
    """Function supported by a plugin, as declared in ServicePluginConfig.supported_features."""

    METRIC = "metric"
    POWER = "power"
    RESET = "reset"
    SHUTDOWN = "shutdown"
    CONNECTION = "connection"


class PluginSupportedModel(BaseModel):
    """Support status of a remote plugin, returned by GET /hw-control-plugin/v1.

    Public plugin interface schema. Corresponds to the PluginSupportedModel
    schema in the plugin-dev-guide OpenAPI spec (docs/ja/openapi.yaml); kept as
    the published contract for plugin authors even when HW Control has no
    internal caller yet.
    """

    model_config = ConfigDict(populate_by_name=True)

    base_url: str = Field(default="")
    version: PluginInterfaceVersion = Field(default="v1")
    supported_features: list[PluginFunctionName] = Field(min_length=1)


class CPUIdentity(BaseModel):
    """Information identifying a CPU."""

    model_config = ConfigDict(populate_by_name=True)

    cpu_manufacturer: VisibleString = Field(alias="CPUManufacturer")
    cpu_model: VisibleString = Field(alias="CPUModel")
    cpu_serial_number: VisibleString = Field(alias="CPUSerialNumber")


class PCIeIdentity(BaseModel):
    """Information identifying a PCIe device."""

    model_config = ConfigDict(populate_by_name=True)

    pcie_vendor_id: _HexID4 = Field(alias="PCIeVendorID")
    pcie_device_id: _HexID4 = Field(alias="PCIeDeviceID")
    pcie_device_serial_number: _HexID16 = Field(alias="PCIeDeviceSerialNumber")


class SwitchIdentity(BaseModel):
    """Information identifying a switch."""

    model_config = ConfigDict(populate_by_name=True)

    switch_manufacturer: VisibleString = Field(alias="switchManufacturer")
    switch_model: VisibleString = Field(alias="switchModel")
    switch_serial_number: VisibleString = Field(alias="switchSerialNumber")


class DevicePortListModel(BaseModel):
    """Port information of a device.

    Included in ElementModel.schema_, keyed by device type.
    """

    model_config = ConfigDict(populate_by_name=True)

    switch_id: ElementID | None = Field(None, alias="switchID")
    fabric_id: VisibleString | None = Field(None, alias="fabricID")
    switch_port_type: SwitchPortType | None = Field(None, alias="switchPortType")
    switch_port_number: VisibleString | None = Field(None, alias="switchPortNumber")
    ltssm_state: LTSSMState | None = Field(None, alias="LTSSMState")


class HardwareIdentity(BaseModel):
    """Information identifying a piece of hardware uniquely within HW Control.

    Holds exactly one of cpu_identity, pcie_identity, switch_identity,
    device_keys or port_keys, depending on the type of the identified
    hardware.
    """

    model_config = ConfigDict(populate_by_name=True)

    cpu_identity: CPUIdentity | None = Field(None, alias="CPUIdentity")
    pcie_identity: PCIeIdentity | None = Field(None, alias="PCIeIdentity")
    switch_identity: SwitchIdentity | None = Field(None, alias="switchIdentity")
    device_keys: dict[VisibleString, VisibleString] | None = Field(None, alias="deviceKeys")
    port_keys: dict[VisibleString, VisibleString] | None = Field(None, alias="portKeys")


# --- Device/metric schema detail types -----------------------------------
# The following classes mirror the deviceType-specific `schema`/`metric`
# structures defined in the plugin-dev-guide OpenAPI spec
# (docs/ja/openapi.yaml). ElementModel.schema_ and MetricModel.schema_/metric
# are validated against one of these types, selected by device_type.


class StatusModel(BaseModel):
    """Status information of an element."""

    model_config = ConfigDict(populate_by_name=True)

    state: VisibleString | None = Field(default=None, alias="State")
    """State of the element."""
    health: VisibleString | None = Field(default=None, alias="Health")
    """Health state of the element."""


class StatusCommon(BaseModel):
    """Status and power information common to several element schemas."""

    model_config = ConfigDict(populate_by_name=True)

    status: StatusModel = Field(default_factory=StatusModel, alias="Status")
    """Status information of the element."""
    power_state: VisibleString | None = Field(None, alias="PowerState")
    """Current power state of the element."""
    power_capability: bool | None = Field(None, alias="PowerCapability")
    """Whether power control is available."""


class GraphicControllerSchema(BaseModel):
    """Schema for a graphicController element."""

    model_config = ConfigDict(populate_by_name=True)

    device_port_list: list[DevicePortListModel] = Field(default_factory=list, alias="DevicePortList")
    """FM port information associated with this element."""
    schema_bios_version: VisibleString | None = Field(None, alias="SchemaBiosVersion")
    """Version of the graphic controller BIOS or primary graphic controller firmware."""
    driver_version: VisibleString | None = Field(None, alias="DriverVersion")
    """Version of the graphic controller driver."""
    serial_number: VisibleString | None = Field(None, alias="SerialNumber")
    """Serial number of the graphic controller."""
    manufacturer: VisibleString | None = Field(None, alias="Manufacturer")
    """Manufacturer of the graphic controller."""
    model: VisibleString | None = Field(None, alias="Model")
    """Model number of the graphic controller."""
    status: StatusModel = Field(default_factory=StatusModel, alias="Status")
    """Status information of the graphic controller."""


class MemoryLocationModel(BaseModel):
    """Location of a memory device within its socket/controller/channel/slot."""

    model_config = ConfigDict(populate_by_name=True)

    channel: int | None = Field(None, alias="Channel")
    """Channel number the memory device is connected to."""
    memory_controller: int | None = Field(None, alias="MemoryController")
    """Memory controller number the memory device is connected to."""
    slot: int | None = Field(None, alias="Slot")
    """Slot number the memory device is connected to."""
    socket: int | None = Field(None, alias="Socket")
    """Socket number the memory device is connected to."""


class MemorySchema(StatusCommon):
    """Schema for a memory element."""

    device_port_list: list[DevicePortListModel] = Field(default_factory=list, alias="DevicePortList")
    """FM port information associated with this element."""
    capacity_mib: int | None = Field(None, alias="CapacityMiB")
    """Memory capacity (MiB)."""
    logical_size_mib: int | None = Field(None, alias="LogicalSizeMiB")
    """Total logical memory size (MiB)."""
    non_volatile_size_mib: int | None = Field(None, alias="NonVolatileSizeMiB")
    """Total non-volatile region size (MiB)."""
    persistent_region_number_limit: int | None = Field(None, alias="PersistentRegionNumberLimit")
    """Maximum number of persistent regions the memory device supports."""
    persistent_region_size_limit_mib: int | None = Field(None, alias="PersistentRegionSizeLimitMiB")
    """Total persistent region size limit (MiB)."""
    persistent_region_size_max_mib: int | None = Field(None, alias="PersistentRegionSizeMaxMiB")
    """Maximum size of a single persistent region (MiB)."""
    volatile_region_size_limit_mib: int | None = Field(None, alias="VolatileRegionSizeLimitMiB")
    """Total volatile region size limit (MiB)."""
    volatile_region_size_max_mib: int | None = Field(None, alias="VolatileRegionSizeMaxMiB")
    """Maximum size of a single volatile region (MiB)."""
    allocation_alignment_mib: int | None = Field(None, alias="AllocationAlignmentMiB")
    """Boundary alignment for memory region allocation (MiB)."""
    allocation_increment_mib: int | None = Field(None, alias="AllocationIncrementMiB")
    """Minimum allocation increment for a memory region (MiB)."""
    allowed_speeds_mhz: list[int] | None = Field(None, alias="AllowedSpeedsMHz")
    """Speeds supported by the memory device (MHz)."""
    operating_speed_mhz: int | None = Field(None, alias="OperatingSpeedMHz")
    """Operating speed of the memory (MHz)."""
    bus_width_bits: int | None = Field(None, alias="BusWidthBits")
    """Bus width in bits."""
    data_width_bits: int | None = Field(None, alias="DataWidthBits")
    """Data width in bits."""
    max_tdp_milli_watts: list[int] | None = Field(None, alias="MaxTDPMilliWatts")
    """Set of maximum power budgets supported by the memory device (mW)."""
    enabled: bool | None = Field(None, alias="Enabled")
    """Whether the memory is enabled."""
    memory_media: list[VisibleString] | None = Field(None, alias="MemoryMedia")
    """Media of the memory device."""
    memory_type: VisibleString | None = Field(None, alias="MemoryType")
    """Type of the memory device."""
    memory_device_type: VisibleString | None = Field(None, alias="MemoryDeviceType")
    """Detailed type of the memory device."""
    memory_location: MemoryLocationModel | None = Field(None, alias="MemoryLocation")
    """Memory connection information to the socket and memory controller."""
    serial_number: VisibleString | None = Field(None, alias="SerialNumber")
    """Serial number of the memory."""
    manufacturer: VisibleString | None = Field(None, alias="Manufacturer")
    """Manufacturer of the memory device."""
    model: VisibleString | None = Field(None, alias="Model")
    """Model number of the device."""


class HealthDataModel(BaseModel):
    """Health information of a memory device."""

    model_config = ConfigDict(populate_by_name=True)

    data_loss_detected: bool | None = Field(None, alias="DataLossDetected")
    """Whether data loss was detected."""
    last_shutdown_success: bool | None = Field(None, alias="LastShutdownSuccess")
    """Whether the last shutdown succeeded."""
    performance_degraded: bool | None = Field(None, alias="PerformanceDegraded")
    """Whether performance is degraded."""
    predicted_media_life_left_percent: float | None = Field(None, alias="PredictedMediaLifeLeftPercent")
    """Predicted percentage of read/write life remaining in the media."""


class MetricMemory(BaseModel):
    """Metric information specific to a memory element."""

    model_config = ConfigDict(populate_by_name=True)

    bandwidth_percent: float | None = Field(None, alias="BandwidthPercent")
    """Bandwidth utilization of the memory (%)."""
    block_size_bytes: int | None = Field(None, alias="BlockSizeBytes")
    """Block size in bytes."""
    operating_speed_mhz: int | None = Field(None, alias="OperatingSpeedMHz")
    """Operating speed of the memory, in MHz or MT/s as applicable."""
    health_data: HealthDataModel | None = Field(None, alias="HealthData")
    """Health information of the memory."""


class NetworkDeviceFunctionsMetricModel(BaseModel):
    """Metric information of a network device function."""

    model_config = ConfigDict(populate_by_name=True)

    rx_avg_queue_depth_percent: float | None = Field(None, alias="RXAvgQueueDepthPercent")
    """Average RX queue depth."""
    tx_avg_queue_depth_percent: float | None = Field(None, alias="TXAvgQueueDepthPercent")
    """Average TX queue depth."""
    rx_bytes: int | None = Field(None, alias="RXBytes")
    """Total number of bytes received by the network function."""
    rx_frames: int | None = Field(None, alias="RXFrames")
    """Total number of frames received by the network function."""
    tx_bytes: int | None = Field(None, alias="TXBytes")
    """Total number of bytes transmitted by the network function."""
    tx_frames: int | None = Field(None, alias="TXFrames")
    """Total number of frames transmitted by the network function."""


class NetworkMetricModel(BaseModel):
    """Metric information of a network adapter."""

    model_config = ConfigDict(populate_by_name=True)

    cpu_core_percent: float | None = Field(None, alias="CPUCorePercent")
    """CPU core utilization of the device (%)."""
    host_bus_rx_percent: float | None = Field(None, alias="HostBusRXPercent")
    """RX utilization of the host bus, such as PCIe (%)."""
    host_bus_tx_percent: float | None = Field(None, alias="HostBusTXPercent")
    """TX utilization of the host bus, such as PCIe (%)."""


class MetricNetworkInterface(BaseModel):
    """Metric information specific to a networkInterface element."""

    model_config = ConfigDict(populate_by_name=True)

    network: NetworkMetricModel | None = Field(None, alias="Network")
    """Network metric information."""
    network_device_functions: NetworkDeviceFunctionsMetricModel | None = Field(None, alias="NetworkDeviceFunctions")
    """Network device function metric information."""


class CacheModel(BaseModel):
    """Processor cache metrics."""

    model_config = ConfigDict(populate_by_name=True)

    occupancy_bytes: int | None = Field(None, alias="OccupancyBytes")
    """Total cache level occupancy in bytes."""
    occupancy_percent: float | None = Field(None, alias="OccupancyPercent")
    """Total cache occupancy percentage."""
    cache_miss: float | None = Field(None, alias="CacheMiss")
    """Number of cache line misses, in millions."""
    cache_misses_per_instruction: float | None = Field(None, alias="CacheMissesPerInstruction")
    """Number of cache misses per instruction."""
    hit_ratio: float | None = Field(None, alias="HitRatio")
    """Cache line hit ratio."""


class CoreCacheModel(BaseModel):
    """Cache metrics of a single processor core."""

    model_config = ConfigDict(populate_by_name=True)

    occupancy_bytes: int | None = Field(None, alias="OccupancyBytes")
    """Total cache level occupancy in bytes."""
    occupancy_percent: float | None = Field(None, alias="OccupancyPercent")
    """Total cache occupancy percentage."""


class CoreMetricModel(BaseModel):
    """Metric information of a single processor core."""

    model_config = ConfigDict(populate_by_name=True)

    core_id: VisibleString | None = Field(None, alias="CoreId")
    """Processor core identifier."""
    instructions_per_cycle: float | None = Field(None, alias="InstructionsPerCycle")
    """Instructions per clock cycle of this core."""
    core_cache: list[CoreCacheModel] | None = Field(None, alias="CoreCache")
    """Cache measurements of the core within the processor."""


class MetricProcessor(BaseModel):
    """Metric information specific to a processor-like element."""

    model_config = ConfigDict(populate_by_name=True)

    bandwidth_percent: float | None = Field(None, alias="BandwidthPercent")
    """Bandwidth utilization of the processor (%)."""
    operating_speed_mhz: int | None = Field(None, alias="OperatingSpeedMHz")
    """Operating speed of the processor (MHz)."""
    local_memory_bandwidth_bytes: int | None = Field(None, alias="LocalMemoryBandwidthBytes")
    """Local memory bandwidth usage in bytes."""
    remote_memory_bandwidth_bytes: int | None = Field(None, alias="RemoteMemoryBandwidthBytes")
    """Remote memory bandwidth usage in bytes."""
    cache: list[CacheModel] | None = Field(None, alias="Cache")
    """Processor cache measurements."""
    core_metrics: list[CoreMetricModel] | None = Field(None, alias="CoreMetrics")
    """Processor core measurements."""


class MetricSchemaMemory(StatusCommon):
    """Schema for memory metric information."""

    enabled: bool | None = Field(None, alias="Enabled")
    """Whether the memory is enabled."""


class NetworkDeviceFunctionsBaseModel(BaseModel):
    """Common fields of a network device function."""

    model_config = ConfigDict(populate_by_name=True)

    device_enabled: bool | None = Field(None, alias="DeviceEnabled")
    """Whether this network device function is enabled."""


class MetricSchemaNetworkInterface(BaseModel):
    """Schema for networkInterface metric information."""

    model_config = ConfigDict(populate_by_name=True)

    network_device_functions: NetworkDeviceFunctionsBaseModel | None = Field(None, alias="NetworkDeviceFunctions")
    """Network device function information."""
    network: StatusCommon | None = Field(None, alias="Network")
    """Network information."""


class MetricSchemaDrive(StatusCommon):
    """Metric schema of a drive."""

    negotiated_speed_gbs: float | None = Field(None, alias="NegotiatedSpeedGbs")
    """Speed at which this drive currently communicates with storage."""


class ByteDataModel(BaseModel):
    """Byte-level capacity data."""

    model_config = ConfigDict(populate_by_name=True)

    allocated_bytes: int | None = Field(None, alias="AllocatedBytes")
    """Number of bytes currently allocated by storage."""
    consumed_bytes: int | None = Field(None, alias="ConsumedBytes")
    """Number of bytes consumed."""
    guaranteed_bytes: int | None = Field(None, alias="GuaranteedBytes")
    """Number of bytes guaranteed by storage."""
    provisioned_bytes: int | None = Field(None, alias="ProvisionedBytes")
    """Maximum number of bytes that can be allocated."""


class MetricCapacityModel(BaseModel):
    """Capacity metric information."""

    model_config = ConfigDict(populate_by_name=True)

    data: ByteDataModel | None = Field(None, alias="Data")
    """Capacity information related to user data."""
    metadata: ByteDataModel | None = Field(None, alias="Metadata")
    """Capacity information related to metadata."""
    snapshot: ByteDataModel | None = Field(None, alias="Snapshot")
    """Capacity information related to snapshot or backup data."""


class MetricVolumeModel(BaseModel):
    """Metric information of a storage volume."""

    model_config = ConfigDict(populate_by_name=True)

    remaining_capacity_percent: int | None = Field(None, alias="RemainingCapacityPercent")
    """Percentage of capacity remaining in this volume."""
    capacity: MetricCapacityModel | None = Field(None, alias="Capacity")
    """Capacity information of this volume."""


class MetricSchemaStorage(BaseModel):
    """Schema for storage metric information."""

    model_config = ConfigDict(populate_by_name=True)

    volume: MetricVolumeModel | None = Field(None, alias="Volume")
    """Volume information."""
    drive: MetricSchemaDrive | None = Field(None, alias="Drive")
    """Drive information."""


class VLANModel(BaseModel):
    """VLAN information of a network interface."""

    model_config = ConfigDict(populate_by_name=True)

    vlan_enable: bool | None = Field(None, alias="VLANEnable")
    """Whether this VLAN is enabled."""
    vlan_id: int | None = Field(None, alias="VLANId")
    """ID of this VLAN."""


class EthernetModel(BaseModel):
    """Ethernet-specific information of a network device function."""

    model_config = ConfigDict(populate_by_name=True)

    mac_address: VisibleString | None = Field(None, alias="MACAddress")
    """Currently configured MAC address."""
    mtu_size: int | None = Field(None, alias="MTUSize")
    """Configured maximum transmission unit (MTU)."""
    mtu_size_maximum: int | None = Field(None, alias="MTUSizeMaximum")
    """Maximum supported maximum transmission unit (MTU) size."""
    permanent_mac_address: VisibleString | None = Field(None, alias="PermanentMACAddress")
    """Permanent MAC address."""
    vlan: VLANModel | None = Field(None, alias="VLAN")
    """VLAN information of this interface."""


class LimitsModel(BaseModel):
    """Bandwidth/packet-rate limits of a network device function."""

    model_config = ConfigDict(populate_by_name=True)

    burst_bytes_per_second: int | None = Field(None, alias="BurstBytesPerSecond")
    """Maximum number of bytes per second during a burst."""
    burst_packets_per_second: int | None = Field(None, alias="BurstPacketsPerSecond")
    """Maximum number of packets per second during a burst."""
    direction: VisibleString | None = Field(None, alias="Direction")
    """Direction of the data to which this limit applies."""
    sustained_bytes_per_second: int | None = Field(None, alias="SustainedBytesPerSecond")
    """Maximum number of sustained bytes per second."""
    sustained_packets_per_second: int | None = Field(None, alias="SustainedPacketsPerSecond")
    """Maximum number of sustained packets per second."""


class NetworkDeviceFunctionsModel(BaseModel):
    """Network device function information."""

    model_config = ConfigDict(populate_by_name=True)

    device_enabled: bool | None = Field(None, alias="DeviceEnabled")
    """Whether this network device function is enabled."""
    ethernet: EthernetModel | None = Field(None, alias="Ethernet")
    """Ethernet capabilities, status and configuration of the network device."""
    limits: list[LimitsModel] | None = Field(None, alias="Limits")
    """Byte and packet limits of the network device function."""


class CapableModel(BaseModel):
    """Whether a capability is supported."""

    model_config = ConfigDict(populate_by_name=True)

    capable: bool | None = Field(None, alias="Capable")
    """Whether Data Center Bridging (DCB) is supported."""


class NPARModel(BaseModel):
    """NIC partitioning (NPAR) capability information."""

    model_config = ConfigDict(populate_by_name=True)

    npar_capable: bool | None = Field(None, alias="NparCapable")
    """Whether NIC function partitioning is supported."""
    npar_enabled: bool | None = Field(None, alias="NparEnabled")
    """Whether NIC function partitioning is active."""


class NPIVModel(BaseModel):
    """N_Port ID Virtualization (NPIV) capability information."""

    model_config = ConfigDict(populate_by_name=True)

    max_device_logins: int | None = Field(None, alias="MaxDeviceLogins")
    """Maximum number of NPIV logins allowed from all ports simultaneously."""
    max_port_logins: int | None = Field(None, alias="MaxPortLogins")
    """Maximum number of NPIV logins allowed per physical port."""


class SRIOVModel(BaseModel):
    """Single Root I/O Virtualization (SR-IOV) capability information."""

    model_config = ConfigDict(populate_by_name=True)

    sriov_vepa_capable: bool | None = Field(None, alias="SRIOVVEPACapable")
    """Whether SR-IOV is supported in Virtual Ethernet Port Aggregator (VEPA) mode."""


class VirtualFunctionModel(BaseModel):
    """Virtual function capability information."""

    model_config = ConfigDict(populate_by_name=True)

    device_max_count: int | None = Field(None, alias="DeviceMaxCount")
    """Maximum number of virtual functions supported."""
    network_port_max_count: int | None = Field(None, alias="NetworkPortMaxCount")
    """Maximum number of virtual functions supported per port."""
    min_assignment_group_size: int | None = Field(None, alias="MinAssignmentGroupSize")
    """Minimum number of virtual functions that can be assigned or moved."""


class VirtualizationOffloadModel(BaseModel):
    """Virtualization offload capability information."""

    model_config = ConfigDict(populate_by_name=True)

    virtual_function: VirtualFunctionModel | None = Field(None, alias="VirtualFunction")
    """Virtual function capability of the controller."""
    sriov: SRIOVModel | None = Field(None, alias="SRIOV")
    """Single Root I/O Virtualization (SR-IOV) capability."""


class ControllerCapabilitiesModel(BaseModel):
    """Capabilities of a network adapter controller."""

    model_config = ConfigDict(populate_by_name=True)

    data_center_bridging: CapableModel | None = Field(None, alias="DataCenterBridging")
    """Data Center Bridging (DCB) capability."""
    network_device_function_count: int | None = Field(None, alias="NetworkDeviceFunctionCount")
    """Maximum number of physical functions available."""
    network_port_count: int | None = Field(None, alias="NetworkPortCount")
    """Number of physical ports."""
    npar: NPARModel | None = Field(None, alias="NPAR")
    """NIC partitioning (NPAR) capability."""
    npiv: NPIVModel | None = Field(None, alias="NPIV")
    """N_Port ID Virtualization (NPIV) capability."""
    virtualization_offload: VirtualizationOffloadModel | None = Field(None, alias="VirtualizationOffload")
    """Virtualization offload capability."""


class IdentifiersModel(BaseModel):
    """A durable name identifying a drive/volume/controller."""

    model_config = ConfigDict(populate_by_name=True)

    durable_name_format: VisibleString | None = Field(None, alias="DurableNameFormat")
    """Format of the durable name property."""
    durable_name: VisibleString | None = Field(None, alias="DurableName")
    """World-wide durable name of the element."""


class PartLocationModel(BaseModel):
    """Physical location of a part within an enclosure."""

    model_config = ConfigDict(populate_by_name=True)

    service_label: VisibleString | None = Field(None, alias="ServiceLabel")
    """Label of the part's location."""
    location_type: VisibleString | None = Field(None, alias="LocationType")
    """Type of the part's location."""
    location_ordinal_value: int | None = Field(None, alias="LocationOrdinalValue")
    """Number representing the part's location."""
    reference: VisibleString | None = Field(None, alias="Reference")
    """Reference point of the part location."""
    orientation: VisibleString | None = Field(None, alias="Orientation")
    """Slot enumeration order used by LocationOrdinalValue."""


class LocationModel(BaseModel):
    """Location information of a resource."""

    model_config = ConfigDict(populate_by_name=True)

    part_location: PartLocationModel | None = Field(None, alias="PartLocation")
    """Location of the resource's part within the enclosure."""


class PCIeInterfaceModel(BaseModel):
    """PCIe interface details of a controller."""

    model_config = ConfigDict(populate_by_name=True)

    lanes_in_use: int | None = Field(None, alias="LanesInUse")
    """Number of PCIe lanes in use by this device."""
    max_lanes: int | None = Field(None, alias="MaxLanes")
    """Number of PCIe lanes supported by this device."""
    pcie_type: VisibleString | None = Field(None, alias="PCIeType")
    """Version of the PCIe specification in use on this device."""
    max_pcie_type: VisibleString | None = Field(None, alias="MaxPCIeType")
    """Latest version of the PCIe specification supported by this device."""


class ControllersModel(BaseModel):
    """A network adapter controller."""

    model_config = ConfigDict(populate_by_name=True)

    controller_capabilities: ControllerCapabilitiesModel | None = Field(None, alias="ControllerCapabilities")
    """Capabilities of the controller."""
    firmware_package_version: VisibleString | None = Field(None, alias="FirmwarePackageVersion")
    """Version of the firmware package."""
    identifiers: list[IdentifiersModel] | None = Field(None, alias="Identifiers")
    """Durable name of the network adapter controller."""
    location: LocationModel | None = Field(None, alias="Location")
    """Location of the controller."""
    pcie_interface: PCIeInterfaceModel | None = Field(None, alias="PCIeInterface")
    """Details of the controller's PCIe interface."""


class NetworkModel(StatusCommon):
    """Network adapter information."""

    controllers: list[ControllersModel] | None = Field(None, alias="Controllers")
    """Network controllers composing this network adapter."""
    serial_number: VisibleString | None = Field(None, alias="SerialNumber")
    """Serial number of this network adapter."""
    manufacturer: VisibleString | None = Field(None, alias="Manufacturer")
    """Manufacturer of this network adapter."""
    model: VisibleString | None = Field(None, alias="Model")
    """Model number of this network adapter."""


class AllocationPercentModel(BaseModel):
    """A bandwidth allocation percentage."""

    model_config = ConfigDict(populate_by_name=True)

    allocation_percent: int | None = Field(None, alias="AllocationPercent")
    """Bandwidth allocation percentage."""


class LinkConfigurationModel(BaseModel):
    """Link configuration of a network port."""

    model_config = ConfigDict(populate_by_name=True)

    capable_link_speed_gbps: list[float] | None = Field(None, alias="CapableLinkSpeedGbps")
    """Set of link speed capabilities of this port (Gbit/s)."""


class PortModel(BaseModel):
    """Network port information."""

    model_config = ConfigDict(populate_by_name=True)

    function_max_bandwidth: list[AllocationPercentModel] | None = Field(None, alias="FunctionMaxBandwidth")
    """Maximum bandwidth allocation percentage of functions associated with this port."""
    function_min_bandwidth: list[AllocationPercentModel] | None = Field(None, alias="FunctionMinBandwidth")
    """Minimum bandwidth allocation percentage of functions associated with this port."""
    max_speed_gbps: float | None = Field(None, alias="MaxSpeedGbps")
    """Currently configured maximum speed of this port (Gbit/s)."""
    link_configuration: list[LinkConfigurationModel] | None = Field(None, alias="LinkConfiguration")
    """Link configuration of this port."""


class SerialInterfacesModel(BaseModel):
    """Serial interface information of a network interface."""

    model_config = ConfigDict(populate_by_name=True)

    bit_rate: VisibleString | None = Field(None, alias="BitRate")
    """Receive and transmit data flow rate of the serial interface."""


class NetworkInterfaceSchema(BaseModel):
    """Schema for a networkInterface element."""

    model_config = ConfigDict(populate_by_name=True)

    device_port_list: list[DevicePortListModel] = Field(default_factory=list, alias="DevicePortList")
    """FM port information associated with this element."""
    serial_interfaces: SerialInterfacesModel | None = Field(None, alias="SerialInterfaces")
    """Serial interface information."""
    network: NetworkModel | None = Field(None, alias="Network")
    """Network information."""
    port: PortModel | None = Field(None, alias="Port")
    """Port information."""
    network_device_functions: NetworkDeviceFunctionsModel | None = Field(None, alias="NetworkDeviceFunctions")
    """Network device function information."""


class MemorySummaryModel(BaseModel):
    """Summary of memory associated with a processor."""

    model_config = ConfigDict(populate_by_name=True)

    ecc_mode_enabled: bool | None = Field(None, alias="ECCModeEnabled")
    """Whether the memory ECC mode is enabled."""
    total_cache_size_mib: int | None = Field(None, alias="TotalCacheSizeMiB")
    """Total size of the cache memory (MiB)."""
    total_memory_size_mib: int | None = Field(None, alias="TotalMemorySizeMiB")
    """Total size of the attached volatile memory (MiB)."""


class ProcessorIdModel(BaseModel):
    """Identification information of a processor."""

    model_config = ConfigDict(populate_by_name=True)

    effective_family: VisibleString | None = Field(None, alias="EffectiveFamily")
    """Effective family."""
    effective_model: VisibleString | None = Field(None, alias="EffectiveModel")
    """Effective model."""
    identification_registers: VisibleString | None = Field(None, alias="IdentificationRegisters")
    """Raw processor identification registers provided by the processor manufacturer."""
    microcode_info: VisibleString | None = Field(None, alias="MicrocodeInfo")
    """Microcode information."""
    protected_identification_number: VisibleString | None = Field(None, alias="ProtectedIdentificationNumber")
    """PPIN (Protected Processor Inventory Number)."""
    step: VisibleString | None = Field(None, alias="Step")
    """Stepping value."""
    vendor_id: VisibleString | None = Field(None, alias="VendorId")
    """Vendor identification information."""


class ProcessorMemoryModel(BaseModel):
    """Memory attached to or integrated in a processor."""

    model_config = ConfigDict(populate_by_name=True)

    capacity_mib: int | None = Field(None, alias="CapacityMiB")
    """Memory capacity (MiB)."""
    integrated_memory: bool | None = Field(None, alias="IntegratedMemory")
    """Whether the memory is integrated into the processor."""
    memory_type: VisibleString | None = Field(None, alias="MemoryType")
    """Type of memory used by the processor."""
    speed_mhz: int | None = Field(None, alias="SpeedMHz")
    """Operating speed of the memory (MHz)."""


class ProcessorSchema(StatusCommon):
    """Schema for a processor-like element (Accelerator/CPU/DSP/FPGA/GPU)."""

    device_port_list: list[DevicePortListModel] = Field(default_factory=list, alias="DevicePortList")
    """FM port information associated with this element."""
    base_speed_mhz: int | None = Field(None, alias="BaseSpeedMHz")
    """Base (nominal) clock speed of the processor (MHz)."""
    operating_speed_mhz: int | None = Field(None, alias="OperatingSpeedMHz")
    """Clock speed of the processor while operating (MHz)."""
    tdp_watts: int | None = Field(None, alias="TDPWatts")
    """Nominal thermal design power (TDP) (W)."""
    total_cores: int | None = Field(None, alias="TotalCores")
    """Total number of cores contained in this processor."""
    total_enabled_cores: int | None = Field(None, alias="TotalEnabledCores")
    """Total number of enabled cores contained in this processor."""
    total_threads: int | None = Field(None, alias="TotalThreads")
    """Total number of execution threads supported by this processor."""
    processor_memory: list[ProcessorMemoryModel] | None = Field(None, alias="ProcessorMemory")
    """Memory attached to or integrated into this processor."""
    memory_summary: MemorySummaryModel | None = Field(None, alias="MemorySummary")
    """Summary of all memory associated with this processor."""
    instruction_set: VisibleString | None = Field(None, alias="InstructionSet")
    """Instruction set of the processor."""
    processor_architecture: VisibleString | None = Field(None, alias="ProcessorArchitecture")
    """Architecture of the processor."""
    processor_id: ProcessorIdModel | None = Field(None, alias="ProcessorId")
    """Identification information of this processor."""
    serial_number: VisibleString | None = Field(None, alias="SerialNumber")
    """Serial number of the processor."""
    socket: VisibleString | None = Field(None, alias="Socket")
    """Socket of the processor."""
    manufacturer: VisibleString | None = Field(None, alias="Manufacturer")
    """Manufacturer of the processor."""
    model: VisibleString | None = Field(None, alias="Model")
    """Model number of the device."""


class SchemaCommon(BaseModel):
    """Schema common to switch and unknown elements."""

    model_config = ConfigDict(populate_by_name=True)

    device_port_list: list[DevicePortListModel] = Field(default_factory=list, alias="DevicePortList")
    """FM port information associated with this element."""


class DriveModel(StatusCommon):
    """Drive information."""

    predicted_media_life_left_percent: float | None = Field(None, alias="PredictedMediaLifeLeftPercent")
    """Predicted percentage of read/write life remaining in this drive."""
    capacity_bytes: int | None = Field(None, alias="CapacityBytes")
    """Size of this drive in bytes."""
    capable_speed_gbs: float | None = Field(None, alias="CapableSpeedGbs")
    """Speed at which this drive communicates with storage under ideal conditions."""
    negotiated_speed_gbs: float | None = Field(None, alias="NegotiatedSpeedGbs")
    """Speed at which this drive currently communicates with storage."""
    hotspare_type: VisibleString | None = Field(None, alias="HotspareType")
    """Type of hot spare this drive is currently serving as."""
    serial_number: VisibleString | None = Field(None, alias="SerialNumber")
    """Serial number of the drive."""
    manufacturer: VisibleString | None = Field(None, alias="Manufacturer")
    """Manufacturer of the drive."""
    model: VisibleString | None = Field(None, alias="Model")
    """Model number of the drive."""
    identifiers: list[IdentifiersModel] | None = Field(None, alias="Identifiers")
    """Identifiers of the drive."""


class RedundancyModel(BaseModel):
    """Redundancy information of a storage subsystem."""

    model_config = ConfigDict(populate_by_name=True)

    redundancy_enabled: bool | None = Field(None, alias="RedundancyEnabled")
    """Whether redundancy is enabled."""
    mode: VisibleString | None = Field(None, alias="Mode")
    """Redundancy mode."""
    name: VisibleString | None = Field(None, alias="Name")
    """Name of the element or array member."""
    max_num_supported: int | None = Field(None, alias="MaxNumSupported")
    """Maximum number of members allowed in this particular redundancy group."""
    min_num_needed: int | None = Field(None, alias="MinNumNeeded")
    """Minimum number of members needed for this group to be redundant."""
    redundancy_set: list[VisibleString] | None = Field(None, alias="RedundancySet")
    """Redundancy member information (device information unique IDs)."""


class StorageModel(BaseModel):
    """Storage subsystem information."""

    model_config = ConfigDict(populate_by_name=True)

    redundancy: list[RedundancyModel] | None = Field(None, alias="Redundancy")
    """Redundancy information of the storage subsystem."""


class CapacityModel(BaseModel):
    """Capacity information split into data and metadata."""

    model_config = ConfigDict(populate_by_name=True)

    data: ByteDataModel | None = Field(None, alias="Data")
    """Capacity information related to user data."""
    metadata: ByteDataModel | None = Field(None, alias="Metadata")
    """Capacity information related to metadata."""


class VolumeModel(BaseModel):
    """Storage volume information."""

    model_config = ConfigDict(populate_by_name=True)

    access_capabilities: list[VisibleString] | None = Field(None, alias="AccessCapabilities")
    """IO access capabilities supported by this volume."""
    optimum_io_size_bytes: int | None = Field(None, alias="OptimumIOSizeBytes")
    """Optimum IO size of this volume, in bytes."""
    capacity: CapacityModel | None = Field(None, alias="Capacity")
    """Capacity information for this volume."""
    capacity_snapshot: ByteDataModel | None = Field(None, alias="CapacitySnapshot")
    """Capacity information related to snapshot or backup data."""
    capacity_bytes: int | None = Field(None, alias="CapacityBytes")
    """Size of this volume in bytes."""
    max_block_size_bytes: int | None = Field(None, alias="MaxBlockSizeBytes")
    """Maximum block size of this volume, in bytes."""
    recoverable_capacity_source_count: int | None = Field(None, alias="RecoverableCapacitySourceCount")
    """Current number of available capacity resources that can be used as replacements for this volume."""
    remaining_capacity_percent: int | None = Field(None, alias="RemainingCapacityPercent")
    """Percentage of capacity remaining in this volume."""
    manufacturer: VisibleString | None = Field(None, alias="Manufacturer")
    """Manufacturer of the volume."""
    model: VisibleString | None = Field(None, alias="Model")
    """Model number of the volume."""
    identifiers: list[IdentifiersModel] | None = Field(None, alias="Identifiers")
    """Identifiers of the volume."""


class StorageSchema(BaseModel):
    """Schema for a storage element."""

    model_config = ConfigDict(populate_by_name=True)

    device_port_list: list[DevicePortListModel] = Field(default_factory=list, alias="DevicePortList")
    """FM port information associated with this element."""
    storage: StorageModel | None = Field(None, alias="Storage")
    """Storage information."""
    volume: VolumeModel | None = Field(None, alias="Volume")
    """Volume information."""
    drive: DriveModel | None = Field(None, alias="Drive")
    """Drive information."""


class EnergyJoulesModel(BaseModel):
    """Energy consumption information."""

    model_config = ConfigDict(populate_by_name=True)

    reading: float | None = Field(None, alias="Reading")
    """Measured energy consumption (J)."""


class SensorModel(BaseModel):
    """Sensor timing information."""

    model_config = ConfigDict(populate_by_name=True)

    sensor_reset_time: str | None = Field(None, alias="SensorResetTime")
    """Date and time the time property was last reset (UTC, ISO 8601 format)."""
    sensing_interval: VisibleString | None = Field(None, alias="SensingInterval")
    """Time interval between sensor readings (duration, PnDTnHnMnS format)."""
    reading_time: str | None = Field(None, alias="ReadingTime")
    """Date and time the measurement was obtained from the sensor (UTC, ISO 8601 format)."""


class EnvironmentModel(BaseModel):
    """Environment/energy information of an element, returned by ServicePlugin.get_metric."""

    model_config = ConfigDict(populate_by_name=True)

    sensor: SensorModel | None = Field(None, alias="Sensor")
    """Sensor information."""
    energy_joules: EnergyJoulesModel | None = Field(None, alias="EnergyJoules")
    """Energy consumption information."""


class _ElementBaseModel(BaseModel):
    """Fields common to every ElementModel variant."""

    model_config = ConfigDict(populate_by_name=True)

    id: ElementID
    hardware_id: HardwareIdentity = Field(alias="hardwareID")
    link: list[ElementID] | None = Field(None)
    connection: list[ElementID] | None = Field(None)
    time: datetime | None = Field(None)


class ProcessorElementModel(_ElementBaseModel):
    """Element information for an Accelerator/CPU/DSP/FPGA/GPU element."""

    device_type: Literal[DeviceType.ACCELERATOR, DeviceType.CPU, DeviceType.DSP, DeviceType.FPGA, DeviceType.GPU] = (
        Field(alias="deviceType")
    )
    schema_: ProcessorSchema = Field(alias="schema")


class MemoryElementModel(_ElementBaseModel):
    """Element information for a memory element."""

    device_type: Literal[DeviceType.MEMORY] = Field(alias="deviceType")
    schema_: MemorySchema = Field(alias="schema")


class StorageElementModel(_ElementBaseModel):
    """Element information for a storage element."""

    device_type: Literal[DeviceType.STORAGE] = Field(alias="deviceType")
    schema_: StorageSchema = Field(alias="schema")


class NetworkInterfaceElementModel(_ElementBaseModel):
    """Element information for a network interface element."""

    device_type: Literal[DeviceType.NETWORKINTERFACE] = Field(alias="deviceType")
    schema_: NetworkInterfaceSchema = Field(alias="schema")


class GraphicControllerElementModel(_ElementBaseModel):
    """Element information for a graphic controller element."""

    device_type: Literal[DeviceType.GRAPHICCONTROLLER] = Field(alias="deviceType")
    schema_: GraphicControllerSchema = Field(alias="schema")


class SwitchOrUnknownElementModel(_ElementBaseModel):
    """Element information for a switch or unknown element.

    `schema` may be omitted, defaulting to an empty SchemaCommon, matching
    the `default` on `schema` for SwitchDevice/UnknownDevice in the
    plugin-dev-guide OpenAPI spec (docs/ja/openapi.yaml).
    """

    device_type: Literal[DeviceType.SWITCH, DeviceType.UNKNOWN] = Field(alias="deviceType")
    schema_: SchemaCommon = Field(default_factory=SchemaCommon, alias="schema")


ElementModel = Annotated[
    ProcessorElementModel
    | MemoryElementModel
    | StorageElementModel
    | NetworkInterfaceElementModel
    | GraphicControllerElementModel
    | SwitchOrUnknownElementModel,
    Field(discriminator="device_type"),
]
"""Information of an element managed by a plugin.

Corresponds to the `data` field of ElementResponseModel in the
plugin-dev-guide OpenAPI spec (docs/ja/openapi.yaml); the concrete variant
is selected by `device_type`.

Returned by ServicePlugin.get_element, and as the data of a ResponseModel
with kind="element" returned by ServicePlugin.get_elements.
"""


class ErrorBaseModel(BaseModel):
    """Basic error model, conforming to the RFC 9457 problem details format."""

    model_config = ConfigDict(populate_by_name=True)

    type: VisibleString = Field(default="about: blank")
    title: VisibleString
    status: _HTTPStatusCode
    detail: VisibleString
    instance: VisibleString


class ErrorExceptionModel(ErrorBaseModel):
    """Error model returned as the data of a ResponseModel with kind="error"."""

    error: ErrorBaseModel | None = Field(None)
    additional_message: VisibleString | None = Field(None)


class Error409(ErrorExceptionModel):
    """Error model returned by a plugin with HTTP status 409 (conflict).

    Unlike ErrorExceptionModel, additional_message is required.
    Public plugin interface schema, corresponding to the Error409 schema in the
    plugin-dev-guide OpenAPI spec (docs/ja/openapi.yaml); kept as the published
    contract for plugin authors even when HW Control has no internal caller yet.
    """

    additional_message: VisibleString = Field()


class Error502(ErrorExceptionModel):
    """Error model returned by a plugin with HTTP status 502 (bad gateway).

    Unlike ErrorExceptionModel, error is required.
    Public plugin interface schema, corresponding to the Error502 schema in the
    plugin-dev-guide OpenAPI spec (docs/ja/openapi.yaml); kept as the published
    contract for plugin authors even when HW Control has no internal caller yet.
    """

    error: ErrorBaseModel = Field()


class ElementResponseModel(BaseModel):
    """A single element response returned by ServicePlugin.get_elements."""

    model_config = ConfigDict(populate_by_name=True)

    kind: Literal["element"] = "element"
    data: ElementModel


class ErrorResponseModel(BaseModel):
    """A single error response returned by ServicePlugin.get_elements."""

    model_config = ConfigDict(populate_by_name=True)

    kind: Literal["error"] = "error"
    data: ErrorExceptionModel


ResponseModel = Annotated[ElementResponseModel | ErrorResponseModel, Field(discriminator="kind")]
"""A single element of the list returned by ServicePlugin.get_elements.

Corresponds to the discriminated union of ElementResponseModel/
ErrorResponseModel in the plugin-dev-guide OpenAPI spec (docs/ja/openapi.yaml);
the concrete variant is selected by `kind`.
"""


class PowerStateModel(BaseModel):
    """Power state of an element, returned by ServicePlugin.get_power_state."""

    model_config = ConfigDict(populate_by_name=True)

    power_state: PowerState = Field(alias="powerState")
    time: datetime


class TimeStampModel(BaseModel):
    """Timestamp of an executed or completed operation.

    Returned by ServicePlugin.power_on, power_off, os_shutdown, cpu_reset,
    add_connection and remove_connection.
    """

    time: datetime


class _MetricBaseModel(BaseModel):
    """Fields common to every MetricModel variant."""

    model_config = ConfigDict(populate_by_name=True)

    environment: EnvironmentModel | None = Field(None)
    time: datetime


class ProcessorMetricModel(_MetricBaseModel):
    """Metric information for an Accelerator/CPU/DSP/FPGA/GPU element."""

    device_type: Literal[DeviceType.ACCELERATOR, DeviceType.CPU, DeviceType.DSP, DeviceType.FPGA, DeviceType.GPU] = (
        Field(alias="deviceType")
    )
    schema_: StatusCommon | None = Field(None, alias="schema")
    metric: MetricProcessor | None = Field(None)


class MemoryMetricModel(_MetricBaseModel):
    """Metric information for a memory element."""

    device_type: Literal[DeviceType.MEMORY] = Field(alias="deviceType")
    schema_: MetricSchemaMemory | None = Field(None, alias="schema")
    metric: MetricMemory | None = Field(None)


class StorageMetricModel(_MetricBaseModel):
    """Metric information for a storage element."""

    device_type: Literal[DeviceType.STORAGE] = Field(alias="deviceType")
    schema_: MetricSchemaStorage | None = Field(None, alias="schema")


class NetworkInterfaceMetricModel(_MetricBaseModel):
    """Metric information for a network interface element."""

    device_type: Literal[DeviceType.NETWORKINTERFACE] = Field(alias="deviceType")
    schema_: MetricSchemaNetworkInterface | None = Field(None, alias="schema")
    metric: MetricNetworkInterface | None = Field(None)


class GraphicControllerOrSwitchOrUnknownMetricModel(_MetricBaseModel):
    """Metric information for a graphic controller, switch or unknown element."""

    device_type: Literal[DeviceType.GRAPHICCONTROLLER, DeviceType.SWITCH, DeviceType.UNKNOWN] = Field(
        alias="deviceType"
    )


MetricModel = Annotated[
    ProcessorMetricModel
    | MemoryMetricModel
    | StorageMetricModel
    | NetworkInterfaceMetricModel
    | GraphicControllerOrSwitchOrUnknownMetricModel,
    Field(discriminator="device_type"),
]
"""Metric information of an element, returned by ServicePlugin.get_metric.

Corresponds to the discriminated union of deviceType-specific Metric schemas
in the plugin-dev-guide OpenAPI spec (docs/ja/openapi.yaml); the concrete
variant is selected by `device_type`.
"""

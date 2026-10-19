# Copyright 2025-2026 NEC Corporation
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

"""Response models for Fast API.

Define response models used in API definition of Fast API

"""

from pydantic import BaseModel, Field

SAMPLES_DEVICE_ID_LIST_DESCRIPTION = "The Device ID of Device IDs list."
SAMPLES_DEVICE_ID_DESCRIPTION = "The Device ID of Device."
SAMPLES_DEVICE_TYPE_DESCRIPTION = (
    "device type of Device  " + " \n examples: CPU, GPU, memory, storage, networkInterface, graphicController"
)
SAMPLES_DEVICE_STATUS_DESCRIPTION = "status information of Device"
SAMPLES_POWER_STATE_DESCRIPTION = "The current power state of the drive."
SAMPLES_POWER_CAPABILITY_DESCRIPTION = "Whether the power control feature is enabled."
SAMPLES_LINK_DEVICE_DESCRIPTION = "The Device ID and Device type of the link target device."
SAMPLES_ATTRIBUTE_DESCRIPTION = "Attributes for each device type."
SAMPLES_SPECIFIC_DESCRIPTION = "Specific information for each device type."
SAMPLES_CONSTRAINTS_DESCRIPTION = "Constraints for each device type."
SAMPLES_NONREMOVABLE_DEVICE_ID_LIST_DESCRIPTION = "Non-removable device id of Device IDs list."
SAMPLES_PORT_LIST_DESCRIPTION = "Port list of Device Information."
SAMPLES_SERIAL_NUMBER_DESCRIPTION = "Serial number of Device."
SAMPLES_MANUFACTURER_DESCRIPTION = "Manufacturer of Device."
SAMPLES_MODEL_DESCRIPTION = "Product model number of Device."
SAMPLES_TIMESTAMP_DESCRIPTION = "Information acquisition date and time (UTC)."
SAMPLES_TIMESTAMP = "2025-01-01T00:00:00Z"


class DeviceListInformation(BaseModel):
    """A class to Device Information."""

    device_id: str = Field(
        alias="deviceID",
        description=SAMPLES_DEVICE_ID_LIST_DESCRIPTION,
        examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
    )
    device_type: str = Field(
        alias="type",
        description=SAMPLES_DEVICE_TYPE_DESCRIPTION,
        examples=["CPU"],
    )


class GetsListDevicesResponseBody(BaseModel):
    """The HTTP Response Body schema of Gets A List Of Devices."""

    device_list: list[DeviceListInformation] = Field(
        alias="deviceList",
    )
    info_timestamp: str = Field(
        alias="infoTimestamp",
        description=SAMPLES_TIMESTAMP_DESCRIPTION,
        examples=[SAMPLES_TIMESTAMP],
    )


class StatusInformation(BaseModel):
    """A class to represent Status Information."""

    state: str = Field(
        description="state of Device",
        examples=["Enabled"],
    )
    health: str = Field(
        description="health of Device",
        examples=["OK"],
    )


class AttributeEachDevices(BaseModel):
    """A class to represent information of attribute devices."""

    device_attribute: dict = Field(
        alias="deviceSpecificInformation",
        description=SAMPLES_SPECIFIC_DESCRIPTION,
    )


class NonRemovableDevices(BaseModel):
    """A class to represent information (deviceID) of non-removable devices."""

    device_id: list[str] = Field(
        alias="deviceID",
        description=SAMPLES_NONREMOVABLE_DEVICE_ID_LIST_DESCRIPTION,
        examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
    )


class DeviceSpecificConstraints(BaseModel):
    """A class to represent information of attribute devices."""

    device_specific: list[NonRemovableDevices] = Field(
        alias="nonRemovableDevices",
        description=SAMPLES_CONSTRAINTS_DESCRIPTION,
    )


class PortListInformation(BaseModel):
    """A class to represent Device Port List Information."""

    fabric_id: str = Field(
        alias="fabricID",
        description="Fabric ID",
        examples=["12446A3B"],
    )
    LTSSMState: str = Field(
        description="Link state of CXL device",
        examples=["L0"],
    )
    switch_id: str = Field(
        alias="switchID",
        description="CXL switch identifier",
        examples=["fmsw-01"],
    )
    switch_port_number: str = Field(
        alias="switchPortNumber",
        description="Port number of CXL switch",
        examples=["1"],
    )
    switch_port_type: str = Field(
        alias="switchPortType",
        description="Whether the port type is USP side or DSP side",
        examples=["DSP"],
    )


class MetricEnergyJoules(BaseModel):
    """A class to represent defining energy consumption (J) for Devices."""

    sensor_reset_time: str = Field(
        alias="sensorResetTime",
        description="The timestamp when the time property was last reset. (UTC)",
        examples=[SAMPLES_TIMESTAMP],
    )
    sensing_interval: int = Field(
        alias="sensingInterval",
        description="The interval between sensor readings (in seconds).",
        examples=[10],
    )
    reading_time: str = Field(
        alias="readingTime",
        description="The timestamp when the measurement was obtained from the sensor. (UTC)",
        examples=[SAMPLES_TIMESTAMP],
    )
    reading: int | float = Field(
        description="The measured value of energy consumption (Joules).",
        examples=[0],
    )


class GetsDeviceInformationResponseBody(BaseModel):
    """The HTTP Response Body schema of Gets Information Of Device."""

    device_id: str = Field(
        alias="deviceID",
        description=SAMPLES_DEVICE_ID_DESCRIPTION,
        examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
    )
    device_type: str = Field(
        alias="type",
        description=SAMPLES_DEVICE_TYPE_DESCRIPTION,
        examples=["CPU"],
    )
    attribute: AttributeEachDevices = Field(description=SAMPLES_ATTRIBUTE_DESCRIPTION)
    status: StatusInformation = Field(
        description=SAMPLES_DEVICE_STATUS_DESCRIPTION,
    )
    power_state: str = Field(
        alias="powerState",
        description=SAMPLES_POWER_STATE_DESCRIPTION,
        examples=["On"],
    )
    power_capability: bool = Field(
        alias="powerCapability",
        description=SAMPLES_POWER_CAPABILITY_DESCRIPTION,
        examples=["True"],
    )
    device_serial_number: str = Field(
        alias="serialNumber",
        description=SAMPLES_SERIAL_NUMBER_DESCRIPTION,
        examples=["1234568"],
    )
    device_manufacturer: str = Field(
        alias="manufacturer",
        description=SAMPLES_MANUFACTURER_DESCRIPTION,
        examples=["Example Manufacturer"],
    )
    device_model: str = Field(
        alias="model",
        description=SAMPLES_MODEL_DESCRIPTION,
        examples=["Example Model"],
    )
    links: list[DeviceListInformation] = Field(
        description=SAMPLES_LINK_DEVICE_DESCRIPTION,
    )
    constraints: DeviceSpecificConstraints = Field(
        description=SAMPLES_CONSTRAINTS_DESCRIPTION,
    )
    device_port_list: PortListInformation = Field(
        alias="devicePortList",
        description=SAMPLES_PORT_LIST_DESCRIPTION,
    )
    info_timestamp: str = Field(
        alias="infoTimestamp",
        description=SAMPLES_TIMESTAMP_DESCRIPTION,
        examples=[SAMPLES_TIMESTAMP],
    )


class GetsResourceInformationResponseBody(GetsDeviceInformationResponseBody):
    """The HTTP Response Body schema of Gets Resource Of Device."""

    metric_energy_joules: MetricEnergyJoules = Field(
        alias="metricEnergyJoules",
        description="The energy consumption of the device.",
    )
    info_timestamp: str = Field(
        alias="infoTimestamp",
        description=SAMPLES_TIMESTAMP_DESCRIPTION,
        examples=[SAMPLES_TIMESTAMP],
    )


class GetsMetricInformationResponseBody(BaseModel):
    """The HTTP Response Body schema of Get Metric Information."""

    device_id: str = Field(
        alias="deviceID",
        description=SAMPLES_DEVICE_ID_DESCRIPTION,
        examples=["451b0faf-b70d-4476-832a-4c93f0e6e1ce"],
    )
    device_type: str = Field(
        alias="type",
        description=SAMPLES_DEVICE_TYPE_DESCRIPTION,
        examples=["CPU"],
    )
    status: StatusInformation = Field(
        description=SAMPLES_DEVICE_STATUS_DESCRIPTION,
    )
    power_state: str = Field(
        alias="powerState",
        description=SAMPLES_POWER_STATE_DESCRIPTION,
        examples=["On"],
    )
    power_capability: bool = Field(
        alias="powerCapability",
        description=SAMPLES_POWER_CAPABILITY_DESCRIPTION,
        examples=["True"],
    )
    device_port_list: PortListInformation = Field(
        alias="devicePortList",
        description=SAMPLES_PORT_LIST_DESCRIPTION,
    )
    metric_energy_joules: MetricEnergyJoules = Field(
        alias="metricEnergyJoules",
        description="The energy consumption of the device.",
    )
    info_timestamp: str = Field(
        alias="infoTimestamp",
        description=SAMPLES_TIMESTAMP_DESCRIPTION,
        examples=[SAMPLES_TIMESTAMP],
    )


class GetsAllDevicesResponseBody(BaseModel):
    """The HTTP Response Body schema of Gets Information Of Devices."""

    device_list: list[GetsDeviceInformationResponseBody] = Field(
        alias="deviceList",
    )
    info_timestamp: str = Field(
        alias="infoTimestamp",
        description=SAMPLES_TIMESTAMP_DESCRIPTION,
        examples=[SAMPLES_TIMESTAMP],
    )


class DeviceInformation(BaseModel):
    """A class to represent Device Information.

    Device Information model

    """

    # use aliases to match the names defined in the response format (JSON)
    device_id: str = Field(
        default="",
        alias="deviceID",
    )
    type: str = Field(
        default="",
    )
    info_timestamp: str = Field(
        default="",
        alias="infoTimestamp",
    )


class IncompleteList(BaseModel):
    """A class to represent Incomplete Device information.

    Incomplete List Device information model

    """

    # Use aliases to match the names defined in the response format (JSON).
    error_info: list[dict[str, str]] = Field(
        # Error information data for the cause of acquisition failure
        # Store a list of error codes and error messages
        default=[],
        alias="errorInfo",
    )
    device_id: str = Field(
        default="",
        alias="deviceID",
    )
    info_timestamp: str = Field(
        default="",
        alias="infoTimestamp",
    )


class ResourceList(BaseModel):
    """A class to represent Resource information.

    Resource list information model

    """

    # Use aliases to match the names defined in the response format (JSON).
    device_list: list[dict] = Field(
        default=[],
        alias="deviceList",
    )
    incomplete_device_list: list[dict] = Field(
        default=[],
        alias="incompleteDeviceList",
    )
    info_timestamp: str = Field(
        default="",
        alias="infoTimestamp",
    )


class DeviceResourceList(BaseModel):
    """A class to represent Device Resource list information.

    Device Resource list information model

    """

    # Use aliases to match the names defined in the response format (JSON).
    device_list: list[dict] = Field(
        default=[],
        alias="deviceList",
    )
    info_timestamp: str = Field(
        default="",
        alias="infoTimestamp",
    )


class IncompleteResourceList(BaseModel):
    """A class to represent Incomplete Resource list information.

    Incomplete Resource list information model

    """

    # Use aliases to match the names defined in the response format (JSON).
    incomplete_device_list: list[dict] = Field(
        default=[],
        alias="incompleteDeviceList",
    )
    info_timestamp: str = Field(
        default="",
        alias="infoTimestamp",
    )

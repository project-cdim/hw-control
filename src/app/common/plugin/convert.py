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

"""Convert legacy plugin return data into ServicePlugin data types.

File: hw-control/src/app/common/plugin/convert.py

Used only by app.common.plugin.compat, and planned for removal once
support for the legacy Python module plugins ends.
"""

from datetime import UTC, datetime
from http import HTTPStatus

from pydantic import TypeAdapter, ValidationError

import app.common.basic_exceptions as exc
from app.common.plugin.models import (
    CPUIdentity,
    DevicePortListModel,
    DeviceType,
    ElementModel,
    ElementResponseModel,
    ErrorExceptionModel,
    ErrorResponseModel,
    HardwareIdentity,
    PCIeIdentity,
    ResponseModel,
    SwitchIdentity,
)
from app.common.utils.fm_plugin_base import FMPortData, FMSwitchData
from app.common.utils.oob_plugin_base import OOBDeviceListItem

_MIB = 1024 * 1024
_element_type_adapter: TypeAdapter[ElementModel] = TypeAdapter(ElementModel)

# Validation context used when converting legacy plugin data (spec 2.4.1 to
# 2.4.3). The identifiers returned by a legacy plugin are plain str values
# without the ElementID constraints, so the ElementID validation is skipped
# to keep converting instead of failing.
_SKIP_ELEMENT_ID_CHECK = {"skip_element_id_check": True}

# Fixed type/title values for the ErrorExceptionModel produced by
# convert_device_info_and_spec_info_to_responses, per spec 2.4.4.
_ERROR_TYPE = "about: blank"
_NOT_FOUND_TITLE = "Not Found"
_INTERNAL_ERROR_TITLE = "Internal Server Error"

# Fallback for "instance", used when device.oob_device_id is blank. The spec
# (2.4.4) says to use the device ID as "instance", but OOBDeviceListItem.oob_device_id
# is a plain str without VisibleString's blank-string rejection, so a blank
# legacy plugin response would otherwise fail to build this error model.
_PLACEHOLDER_INSTANCE = "unknown"

# NOTE: FMPortData.ltssm_state allows "Disable" and does not allow "L1",
# while models.LTSSMState allows "Disabled" but not "Disable". This mapping
# is a tentative workaround pending clarification of the spec/legacy plugin
# behavior; other values are passed through unchanged.
_LTSSM_STATE_MAP = {"Disable": "Disabled"}


def _build_pcie_identity(
    vendor_id: str | None, device_id: str | None, device_serial_number: str | None
) -> PCIeIdentity | None:
    """Build PCIeIdentity only if all three identifiers are present."""
    if vendor_id is None or device_id is None or device_serial_number is None:
        return None
    return PCIeIdentity(
        pcie_vendor_id=vendor_id, pcie_device_id=device_id, pcie_device_serial_number=device_serial_number
    )


def _build_cpu_identity(manufacturer: str | None, model: str | None, serial_number: str | None) -> CPUIdentity | None:
    """Build CPUIdentity only if all three identifiers are present."""
    if manufacturer is None or model is None or serial_number is None:
        return None
    return CPUIdentity(cpu_manufacturer=manufacturer, cpu_model=model, cpu_serial_number=serial_number)


def _build_port_device_port_list(data: FMPortData) -> list[dict[str, object]]:
    """Build the DevicePortList entry for a single FMPortData, or [] if unset."""
    # Spec 2.4.1 builds the entry when a source item is "not None", so test
    # against None rather than truthiness: StrictStr fields may be blank.
    ltssm_state = _LTSSM_STATE_MAP.get(data.ltssm_state, data.ltssm_state) if data.ltssm_state is not None else None
    port_values = (data.fabric_id, data.switch_id, data.switch_port_type, data.switch_port_number, ltssm_state)
    if all(value is None for value in port_values):
        return []
    # Validating DevicePortListModel (rather than building a plain dict)
    # validates ltssm_state against models.LTSSMState here, so an unmappable
    # value raises pydantic.ValidationError -> InternalHWControlError below.
    port = DevicePortListModel.model_validate(
        {
            "switch_id": data.switch_id,
            "fabric_id": data.fabric_id,
            "switch_port_type": data.switch_port_type,
            "switch_port_number": data.switch_port_number,
            "ltssm_state": ltssm_state,
        },
        context=_SKIP_ELEMENT_ID_CHECK,
    )
    return [port.model_dump(by_alias=True)]


def _build_port_capacity_schema(data: FMPortData) -> dict[str, int | None]:
    """Build the CapacityMiB/VolatileRegionSizeLimitMiB/NonVolatileSizeMiB schema entries."""
    if data.device_type != "CXL-Type3" or data.capacity is None:
        return {"CapacityMiB": None, "VolatileRegionSizeLimitMiB": None, "NonVolatileSizeMiB": None}
    return {
        "CapacityMiB": data.capacity["total"] // _MIB,
        "VolatileRegionSizeLimitMiB": data.capacity["volatile"] // _MIB,
        "NonVolatileSizeMiB": data.capacity["persistent"] // _MIB,
    }


def convert_port_info_to_elements(data: list[FMPortData]) -> list[ElementModel]:
    """Convert a list of legacy FM FMPortData into a list of ElementModel.

    Args:
        data (list[FMPortData]): Data returned by the legacy FM plugin's
            get_port_info.

    Returns:
        list[ElementModel]: Data used by get_element/get_elements.

    Raises:
        InternalHWControlError: A conversion failure occurred.
    """
    try:
        elements: list[ElementModel] = []
        for item in data:
            hardware_id = HardwareIdentity(
                pcie_identity=_build_pcie_identity(
                    item.pcie_vendor_id, item.pcie_device_id, item.pcie_device_serial_number
                ),
                cpu_identity=_build_cpu_identity(item.cpu_manufacturer, item.cpu_model, item.cpu_serial_number),
                device_keys=item.device_keys or None,
                port_keys=item.port_keys or None,
            )
            payload = {
                "id": item.id,
                "device_type": DeviceType.MEMORY if item.device_type == "CXL-Type3" else DeviceType.UNKNOWN,
                "hardware_id": hardware_id,
                "schema": {"DevicePortList": _build_port_device_port_list(item), **_build_port_capacity_schema(item)},
                "connection": item.link,
                "time": datetime.now(UTC),
            }
            elements.append(_element_type_adapter.validate_python(payload, context=_SKIP_ELEMENT_ID_CHECK))
    except (ValidationError, KeyError, TypeError) as err:
        raise exc.InternalHWControlError from err
    return elements


def convert_switch_info_to_elements(manager_id: str, data: list[FMSwitchData]) -> list[ElementModel]:
    """Convert a list of legacy FM FMSwitchData into a list of ElementModel.

    Args:
        manager_id (str): ID of the manager the data was retrieved from.
        data (list[FMSwitchData]): Data returned by the legacy FM plugin's
            get_switch_info.

    Returns:
        list[ElementModel]: Data used by get_element/get_elements.

    Raises:
        InternalHWControlError: A conversion failure occurred.
    """
    try:
        elements: list[ElementModel] = []
        for item in data:
            fallback = f"{manager_id}_{item.switch_id}"
            # Spec 2.4.2 substitutes the fallback when a source item is "None",
            # so test against None rather than truthiness: StrictStr fields may
            # be blank.
            switch_identity = SwitchIdentity(
                switch_manufacturer=item.switch_manufacturer if item.switch_manufacturer is not None else fallback,
                switch_model=item.switch_model if item.switch_model is not None else fallback,
                switch_serial_number=item.switch_serial_number if item.switch_serial_number is not None else fallback,
            )
            payload = {
                "id": item.switch_id,
                "device_type": DeviceType.SWITCH,
                "hardware_id": HardwareIdentity(switch_identity=switch_identity),
                "link": item.link,
                "time": datetime.now(UTC),
            }
            elements.append(_element_type_adapter.validate_python(payload, context=_SKIP_ELEMENT_ID_CHECK))
    except ValidationError as err:
        raise exc.InternalHWControlError from err
    return elements


def _error_instance(oob_device_id: str) -> str:
    """Return `oob_device_id` as the error model's "instance", or a placeholder if blank."""
    return oob_device_id if oob_device_id.strip() else _PLACEHOLDER_INSTANCE


def _convert_oob_link(value: object) -> list[str] | None:
    """Convert the "link" entry of an OOB spec dict to a list of device IDs."""
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError("link must be a list")
    return [item["deviceID"] for item in value]


def convert_device_info_and_spec_info_to_element(device: OOBDeviceListItem, spec: dict) -> ElementModel:
    """Convert a legacy OOB OOBDeviceListItem and get_spec_info entry into an ElementModel.

    Args:
        device (OOBDeviceListItem): One entry returned by the legacy OOB
            plugin's get_device_info.
        spec (dict): The matching entry returned by get_spec_info.

    Returns:
        ElementModel: Data used by get_element.

    Raises:
        InternalHWControlError: A conversion failure occurred.
    """
    try:
        hardware_id = HardwareIdentity(
            pcie_identity=_build_pcie_identity(
                device.pcie_vendor_id, device.pcie_device_id, device.pcie_device_serial_number
            ),
            cpu_identity=_build_cpu_identity(device.cpu_manufacturer, device.cpu_model, device.cpu_serial_number),
            device_keys=device.device_keys,
            port_keys=device.port_keys,
        )
        payload = {
            "id": device.oob_device_id,
            "device_type": device.device_type,
            "hardware_id": hardware_id,
            "link": _convert_oob_link(spec.get("link")),
            "time": spec["time"],
        }
        if "schema" in spec:
            payload["schema_"] = spec["schema"]
        element = _element_type_adapter.validate_python(payload, context=_SKIP_ELEMENT_ID_CHECK)
    except (ValidationError, KeyError, TypeError, ValueError) as err:
        # Only the exception class name is passed on: the message reaches the
        # caller as the "detail" of an error response, and the original text
        # may quote legacy plugin data.
        raise exc.InternalHWControlError(
            additional_message=f"failed to convert spec data: {type(err).__name__}"
        ) from err
    return element


def convert_device_info_and_spec_info_to_responses(
    devices: list[OOBDeviceListItem], specs: list[dict]
) -> list[ResponseModel]:
    """Convert legacy OOB get_device_info/get_spec_info results into a list of ResponseModel.

    Args:
        devices (list[OOBDeviceListItem]): Data returned by the legacy OOB
            plugin's get_device_info.
        specs (list[dict]): Data returned by the legacy OOB plugin's
            get_spec_info.

    Returns:
        list[ResponseModel]: Data used by get_elements.
    """
    responses: list[ResponseModel] = []
    for device in devices:
        spec = next((s for s in specs if s.get("deviceID") == device.oob_device_id), None)
        if spec is None:
            error = ErrorExceptionModel(
                status=HTTPStatus.NOT_FOUND.value,
                detail="spec data is not found.",
                type=_ERROR_TYPE,
                title=_NOT_FOUND_TITLE,
                instance=_error_instance(device.oob_device_id),
            )
            responses.append(ErrorResponseModel(data=error))
            continue
        try:
            element = convert_device_info_and_spec_info_to_element(device, spec)
        except exc.InternalHWControlError as err:
            error = ErrorExceptionModel(
                status=HTTPStatus.INTERNAL_SERVER_ERROR.value,
                # Spec 2.4.4 wants the exception message here. Read it from
                # "message", not str(err): HWControlError keeps its messages
                # apart from Exception.args, so str(err) would be blank.
                detail=err.message,
                type=_ERROR_TYPE,
                title=_INTERNAL_ERROR_TITLE,
                instance=_error_instance(device.oob_device_id),
            )
            responses.append(ErrorResponseModel(data=error))
            continue
        responses.append(ElementResponseModel(data=element))
    return responses

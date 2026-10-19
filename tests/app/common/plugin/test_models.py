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

"""Unit test module for app/common/plugin/models.py."""

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from app.common.plugin.models import (
    CPUIdentity,
    DevicePortListModel,
    DeviceType,
    DriveModel,
    ElementID,
    ElementResponseModel,
    Error409,
    Error502,
    ErrorBaseModel,
    ErrorExceptionModel,
    ErrorResponseModel,
    ExecuteConnectionAction,
    ExecuteElementAction,
    GraphicControllerOrSwitchOrUnknownMetricModel,
    HardwareIdentity,
    MemorySchema,
    MetricModel,
    MetricProcessor,
    MetricSchemaDrive,
    MetricSchemaMemory,
    NetworkModel,
    PCIeIdentity,
    PluginFunctionName,
    PluginInterfaceVersion,
    PluginSupportedModel,
    PowerState,
    PowerStateModel,
    ProcessorElementModel,
    ProcessorMetricModel,
    ProcessorSchema,
    ResponseModel,
    SensorModel,
    StatusCommon,
    StorageMetricModel,
    SwitchOrUnknownElementModel,
    SwitchPortType,
    TimeStampModel,
    VisibleString,
)

_HARDWARE_ID = {"CPUIdentity": {"CPUManufacturer": "NEC", "CPUModel": "m1", "CPUSerialNumber": "sn1"}}
_ELEMENT_DICT = {
    "id": "elem-1",
    "deviceType": "CPU",
    "hardwareID": _HARDWARE_ID,
    "schema": {"DevicePortList": []},
}


class _VisibleStringHolder(BaseModel):
    """Helper model to validate the VisibleString type alias."""

    value: VisibleString


class _ElementIDHolder(BaseModel):
    """Helper model to validate the ElementID type alias."""

    value: ElementID


class TestVisibleStringTypeAlias:
    """Test the VisibleString type alias."""

    @pytest.mark.parametrize("value", ["abc", "a b c", "1"])
    def test_accepts_non_blank_strings(self, value: str):
        """Non-blank strings without control characters are accepted."""
        assert _VisibleStringHolder(value=value).value == value

    @pytest.mark.parametrize("value", ["", "   ", "a\x00b", "a\x7fb"])
    def test_rejects_blank_or_control_characters(self, value: str):
        """Blank strings and strings with control characters are rejected."""
        with pytest.raises(ValidationError):
            _VisibleStringHolder(value=value)


class TestElementIDTypeAlias:
    """Test the ElementID type alias."""

    @pytest.mark.parametrize("value", ["abc123", "a.b_c~d-e"])
    def test_accepts_unreserved_characters(self, value: str):
        """RFC 3986 unreserved characters are accepted."""
        assert _ElementIDHolder(value=value).value == value

    @pytest.mark.parametrize("value", ["a/b", "a b", "a?b", ""])
    def test_rejects_other_characters(self, value: str):
        """Characters outside the unreserved set are rejected."""
        with pytest.raises(ValidationError):
            _ElementIDHolder(value=value)

    @pytest.mark.parametrize("value", [".", ".."])
    def test_rejects_dot_segments(self, value: str):
        """A "." or ".." value is rejected as a path-traversal-relevant token."""
        with pytest.raises(ValidationError):
            _ElementIDHolder(value=value)

    @pytest.mark.parametrize("value", ["...", "a..b", "..a"])
    def test_accepts_non_dot_segment_values_containing_dots(self, value: str):
        """A value that merely contains dots, but is not exactly "." or "..", is accepted."""
        assert _ElementIDHolder(value=value).value == value

    @pytest.mark.parametrize("value", ["a/b", "", "."])
    def test_skips_the_check_when_the_context_asks_for_it(self, value: str):
        """skip_element_id_check=True in the context bypasses the validation."""
        holder = _ElementIDHolder.model_validate({"value": value}, context={"skip_element_id_check": True})
        assert holder.value == value

    @pytest.mark.parametrize("context", [None, {}, {"skip_element_id_check": False}, "not-a-dict"])
    def test_validates_without_a_skipping_context(self, context: object):
        """The validation applies unless the context sets skip_element_id_check."""
        with pytest.raises(ValidationError):
            _ElementIDHolder.model_validate({"value": "a/b"}, context=context)


class TestPluginInterfaceVersionTypeAlias:
    """Test the PluginInterfaceVersion type alias."""

    def test_accepts_v1(self):
        """The only currently supported API version, "v1", is accepted."""
        assert TypeAdapter(PluginInterfaceVersion).validate_python("v1") == "v1"

    @pytest.mark.parametrize("value", ["v2", "V1", "1", ""])
    def test_rejects_other_values(self, value: str):
        """Any value other than "v1" is rejected."""
        with pytest.raises(ValidationError):
            TypeAdapter(PluginInterfaceVersion).validate_python(value)


class TestEnums:
    """Test the enums are string enums with the expected members."""

    def test_device_type_members(self):
        """DeviceType members match the specification."""
        assert DeviceType.CPU == "CPU"
        assert DeviceType.MEMORY == "memory"
        assert DeviceType.UNKNOWN == "unknown"

    def test_switch_port_type_members(self):
        """SwitchPortType members match the specification."""
        assert SwitchPortType.USP == "USP"
        assert SwitchPortType.DSP == "DSP"

    def test_power_state_members(self):
        """PowerState members match the specification."""
        assert PowerState.ON == "On"
        assert PowerState.UNKNOWN == "Unknown"

    def test_execute_element_action_members(self):
        """ExecuteElementAction members match the specification."""
        assert ExecuteElementAction.POWER_ON == "power-on"
        assert ExecuteElementAction.OS_SHUTDOWN == "os-shutdown"

    def test_execute_connection_action_members(self):
        """ExecuteConnectionAction members match the specification."""
        assert ExecuteConnectionAction.CONNECT == "connect"
        assert ExecuteConnectionAction.DISCONNECT == "disconnect"

    def test_plugin_function_name_members(self):
        """PluginFunctionName members match the specification."""
        assert {member.value for member in PluginFunctionName} == {
            "metric",
            "power",
            "reset",
            "shutdown",
            "connection",
        }


class TestCPUIdentity:
    """Test the CPUIdentity model."""

    def test_all_fields_required(self):
        """All fields are required."""
        identity = CPUIdentity(CPUManufacturer="NEC", CPUModel="m1", CPUSerialNumber="sn1")
        assert identity.cpu_serial_number == "sn1"

    def test_missing_field_raises(self):
        """Missing a required field raises ValidationError."""
        with pytest.raises(ValidationError):
            CPUIdentity(CPUManufacturer="NEC", CPUModel="m1")


class TestPCIeIdentity:
    """Test the PCIeIdentity model."""

    def test_fields(self):
        """All fields are set from their aliases."""
        identity = PCIeIdentity(PCIeVendorID="abcd", PCIeDeviceID="1234", PCIeDeviceSerialNumber="0123456789abcdef")
        assert identity.pcie_vendor_id == "abcd"
        assert identity.pcie_device_id == "1234"
        assert identity.pcie_device_serial_number == "0123456789abcdef"

    def test_vendor_id_wrong_length_raises(self):
        """pcie_vendor_id must be exactly 4 hex digits."""
        with pytest.raises(ValidationError):
            PCIeIdentity(PCIeVendorID="abc", PCIeDeviceID="1234", PCIeDeviceSerialNumber="0123456789abcdef")

    def test_serial_number_non_hex_raises(self):
        """pcie_device_serial_number must be hexadecimal."""
        with pytest.raises(ValidationError):
            PCIeIdentity(PCIeVendorID="abcd", PCIeDeviceID="1234", PCIeDeviceSerialNumber="not-a-hex-string")


class TestHardwareIdentity:
    """Test the HardwareIdentity model."""

    def test_default_all_none(self):
        """All fields default to None."""
        identity = HardwareIdentity()
        assert identity.cpu_identity is None
        assert identity.pcie_identity is None
        assert identity.switch_identity is None
        assert identity.device_keys is None
        assert identity.port_keys is None

    def test_cpu_identity_set(self):
        """cpu_identity is populated from the CPUIdentity alias."""
        identity = HardwareIdentity(CPUIdentity={"CPUManufacturer": "NEC", "CPUModel": "m1", "CPUSerialNumber": "sn1"})
        assert identity.cpu_identity is not None
        assert identity.cpu_identity.cpu_manufacturer == "NEC"


class TestElementModel:
    """Test the ElementModel discriminated union."""

    def test_required_fields(self):
        """id, device_type, hardware_id and schema_ are required for a processor element."""
        element = ProcessorElementModel(**_ELEMENT_DICT)
        assert element.id == "elem-1"
        assert element.device_type == DeviceType.CPU
        assert element.link is None
        assert element.connection is None
        assert element.time is None

    def test_missing_hardware_id_raises(self):
        """Missing hardwareID raises ValidationError."""
        data = {k: v for k, v in _ELEMENT_DICT.items() if k != "hardwareID"}
        with pytest.raises(ValidationError):
            ProcessorElementModel(**data)

    def test_by_alias_round_trip(self):
        """model_dump(by_alias=True) uses the camelCase key names."""
        element = ProcessorElementModel(**_ELEMENT_DICT)
        dumped = element.model_dump(by_alias=True)
        assert dumped["deviceType"] == DeviceType.CPU
        assert dumped["hardwareID"]["CPUIdentity"]["CPUManufacturer"] == "NEC"
        assert dumped["schema"]["DevicePortList"] == []

    def test_schema_kwarg_already_correct_type_is_kept(self):
        """Passing an already-constructed schema_ instance is kept as-is."""
        data = {k: v for k, v in _ELEMENT_DICT.items() if k != "schema"}
        element = ProcessorElementModel(schema_=ProcessorSchema(TotalCores=4), **data)
        assert isinstance(element.schema_, ProcessorSchema)
        assert element.schema_.total_cores == 4

    def test_missing_schema_key_raises(self):
        """A missing schema/schema_ key raises ValidationError for a processor element."""
        data = {k: v for k, v in _ELEMENT_DICT.items() if k != "schema"}
        with pytest.raises(ValidationError):
            ProcessorElementModel(**data)

    def test_switch_schema_key_optional(self):
        """schema/schema_ defaults to an empty SchemaCommon for switch/unknown elements."""
        element = SwitchOrUnknownElementModel(id="sw-1", deviceType="switch", hardwareID=_HARDWARE_ID)
        assert element.schema_.device_port_list == []


class TestErrorModels:
    """Test ErrorBaseModel and ErrorExceptionModel."""

    def test_error_base_model_default_type(self):
        """type defaults to 'about: blank'."""
        error = ErrorBaseModel(title="t", status=500, detail="d", instance="i")
        assert error.type == "about: blank"

    def test_error_exception_model_optional_fields(self):
        """error and additional_message default to None."""
        error = ErrorExceptionModel(title="t", status=500, detail="d", instance="i")
        assert error.error is None
        assert error.additional_message is None

    @pytest.mark.parametrize("status", [100, 599])
    def test_status_accepts_http_status_code_range(self, status: int):
        """status accepts the 3-digit HTTP status code range."""
        error = ErrorBaseModel(title="t", status=status, detail="d", instance="i")
        assert error.status == status

    @pytest.mark.parametrize("status", [99, 600])
    def test_status_outside_range_raises(self, status: int):
        """status outside 100-599 raises ValidationError."""
        with pytest.raises(ValidationError):
            ErrorBaseModel(title="t", status=status, detail="d", instance="i")

    def test_status_rejects_non_numeric_string(self):
        """A non-numeric status raises ValidationError."""
        with pytest.raises(ValidationError):
            ErrorBaseModel(title="t", status="unauthorized", detail="d", instance="i")


class TestError409:
    """Test the Error409 model."""

    def test_additional_message_required(self):
        """additional_message is required, unlike ErrorExceptionModel."""
        error = Error409(title="t", status=409, detail="d", instance="i", additional_message="m")
        assert error.additional_message == "m"

    def test_missing_additional_message_raises(self):
        """Omitting additional_message raises ValidationError."""
        with pytest.raises(ValidationError):
            Error409(title="t", status=409, detail="d", instance="i")


class TestError502:
    """Test the Error502 model."""

    def test_error_required(self):
        """error is required, unlike ErrorExceptionModel."""
        error = Error502(
            title="t",
            status=502,
            detail="d",
            instance="i",
            error={"title": "ut", "status": 500, "detail": "ud", "instance": "ui"},
        )
        assert error.error.title == "ut"

    def test_missing_error_raises(self):
        """Omitting error raises ValidationError."""
        with pytest.raises(ValidationError):
            Error502(title="t", status=502, detail="d", instance="i")


class TestPluginSupportedModel:
    """Test the PluginSupportedModel model."""

    def test_defaults(self):
        """base_url and version default when omitted."""
        model = PluginSupportedModel(supported_features=["metric"])
        assert model.base_url == ""
        assert model.version == "v1"
        assert model.supported_features == [PluginFunctionName.METRIC]

    def test_fields_set(self):
        """Fields can be populated."""
        model = PluginSupportedModel(base_url="http://x", version="v1", supported_features=["metric", "power"])
        assert model.base_url == "http://x"
        assert model.supported_features == [PluginFunctionName.METRIC, PluginFunctionName.POWER]

    def test_missing_supported_features_raises(self):
        """Omitting supported_features raises ValidationError."""
        with pytest.raises(ValidationError):
            PluginSupportedModel()

    def test_empty_supported_features_raises(self):
        """An empty supported_features raises ValidationError."""
        with pytest.raises(ValidationError):
            PluginSupportedModel(supported_features=[])


class TestResponseModel:
    """Test the ResponseModel discriminated union, which discriminates on kind."""

    def test_kind_element(self):
        """kind='element' validates as ElementResponseModel, data as an ElementModel variant."""
        response = TypeAdapter(ResponseModel).validate_python({"kind": "element", "data": _ELEMENT_DICT})
        assert isinstance(response, ElementResponseModel)
        assert isinstance(response.data, ProcessorElementModel)

    def test_kind_error(self):
        """kind='error' validates as ErrorResponseModel, data as ErrorExceptionModel."""
        response = TypeAdapter(ResponseModel).validate_python(
            {"kind": "error", "data": {"title": "t", "status": 404, "detail": "d", "instance": "i"}}
        )
        assert isinstance(response, ErrorResponseModel)
        assert isinstance(response.data, ErrorExceptionModel)

    def test_invalid_kind_raises(self):
        """A kind outside {'element', 'error'} raises ValidationError."""
        with pytest.raises(ValidationError):
            TypeAdapter(ResponseModel).validate_python({"kind": "unknown", "data": _ELEMENT_DICT})


class TestPowerStateModel:
    """Test the PowerStateModel model."""

    def test_fields(self):
        """powerState and time are required and use the correct alias."""
        model = PowerStateModel(powerState="On", time="2026-01-01T00:00:00Z")
        assert model.power_state == PowerState.ON


class TestTimeStampModel:
    """Test the TimeStampModel model."""

    def test_time_required(self):
        """time is required."""
        model = TimeStampModel(time="2026-01-01T00:00:00Z")
        assert model.time.year == 2026


class TestSensorModel:
    """Test SensorModel."""

    def test_sensing_interval_accepts_duration_string(self):
        """sensing_interval accepts a duration string (PnDTnHnMnS format)."""
        model = SensorModel(SensingInterval="PT5S")
        assert model.sensing_interval == "PT5S"

    def test_sensing_interval_defaults_to_none(self):
        """sensing_interval defaults to None when omitted."""
        assert SensorModel().sensing_interval is None

    def test_sensing_interval_accepts_explicit_none(self):
        """An explicit null sensing_interval is accepted."""
        assert SensorModel(SensingInterval=None).sensing_interval is None

    @pytest.mark.parametrize("value", ["", " ", "PT5S\n", 5])
    def test_sensing_interval_rejects_invalid_value(self, value):
        """Blank, control-character-containing and non-string values are rejected."""
        with pytest.raises(ValidationError):
            SensorModel(SensingInterval=value)


class TestMetricModel:
    """Test the MetricModel discriminated union."""

    def test_missing_time_raises(self):
        """time is required."""
        with pytest.raises(ValidationError):
            ProcessorMetricModel(deviceType="CPU")

    def test_processor_schema_and_metric_default_to_none_when_omitted(self):
        """For a processor element, schema_/metric default to None when omitted."""
        model = ProcessorMetricModel(deviceType="CPU", time="2026-01-01T00:00:00Z")
        assert model.device_type == DeviceType.CPU
        assert model.environment is None
        assert model.schema_ is None
        assert model.metric is None

    def test_processor_schema_and_metric_accept_explicit_none(self):
        """For a processor element, an explicit null schema/metric is accepted."""
        model = TypeAdapter(MetricModel).validate_python(
            {"deviceType": "CPU", "time": "2026-01-01T00:00:00Z", "schema": None, "metric": None}
        )
        assert isinstance(model, ProcessorMetricModel)
        assert model.schema_ is None
        assert model.metric is None

    def test_storage_schema_defaults_to_none_when_omitted(self):
        """For a storage element (no metric key), schema_ defaults to None when omitted."""
        model = TypeAdapter(MetricModel).validate_python({"deviceType": "storage", "time": "2026-01-01T00:00:00Z"})
        assert isinstance(model, StorageMetricModel)
        assert model.schema_ is None

    def test_graphic_controller_switch_unknown_have_no_schema_or_metric(self):
        """graphicController/switch/unknown elements have neither schema nor metric."""
        model = TypeAdapter(MetricModel).validate_python(
            {"deviceType": "graphicController", "time": "2026-01-01T00:00:00Z"}
        )
        assert isinstance(model, GraphicControllerOrSwitchOrUnknownMetricModel)

    def test_optional_fields_set(self):
        """Optional fields can be populated, converted to the type matching device_type."""
        model = ProcessorMetricModel(
            deviceType="CPU",
            environment={"EnergyJoules": {"Reading": 1.5}},
            time="2026-01-01T00:00:00Z",
            schema={"Status": {"State": "Enabled"}},
            metric={"BandwidthPercent": 42.0},
        )
        assert model.environment.energy_joules.reading == 1.5
        assert model.schema_.status.state == "Enabled"
        assert model.metric.bandwidth_percent == 42.0

    def test_model_validate_non_dict_input_raises(self):
        """model_validate on a non-dict, non-instance value raises ValidationError."""
        with pytest.raises(ValidationError):
            TypeAdapter(MetricModel).validate_python(["not", "a", "dict"])

    def test_schema_and_metric_kwargs_already_correct_type_are_kept(self):
        """Passing already-constructed schema_/metric instances are kept as-is."""
        model = ProcessorMetricModel(
            deviceType="CPU",
            time="2026-01-01T00:00:00Z",
            schema_=StatusCommon(PowerCapability=True),
            metric=MetricProcessor(BandwidthPercent=1.0),
        )
        assert isinstance(model.schema_, StatusCommon)
        assert model.schema_.power_capability is True
        assert isinstance(model.metric, MetricProcessor)
        assert model.metric.bandwidth_percent == 1.0


class TestStatusCommonSubclasses:
    """Test the models sharing the StatusCommon status/power fields."""

    _SUBCLASSES = (
        MemorySchema,
        MetricSchemaMemory,
        MetricSchemaDrive,
        NetworkModel,
        ProcessorSchema,
        DriveModel,
    )
    _COMMON_ALIASES = ("Status", "PowerState", "PowerCapability")

    @pytest.mark.parametrize("model_class", _SUBCLASSES)
    def test_common_fields_come_first_in_declaration_order(self, model_class):
        """The status/power fields stay ahead of the model specific fields."""
        assert issubclass(model_class, StatusCommon)
        assert list(model_class.model_fields)[:3] == list(StatusCommon.model_fields)

    @pytest.mark.parametrize("model_class", _SUBCLASSES)
    def test_common_fields_keep_their_aliases_and_defaults(self, model_class):
        """An empty instance dumps the status/power fields as the IF spec defines."""
        dumped = model_class().model_dump(by_alias=True)
        assert dumped["Status"] == {"State": None, "Health": None}
        assert dumped["PowerState"] is None
        assert dumped["PowerCapability"] is None

    @pytest.mark.parametrize("model_class", _SUBCLASSES)
    def test_common_fields_are_flattened_in_the_json_schema(self, model_class):
        """Inheritance must not introduce a nested StatusCommon reference."""
        schema = model_class.model_json_schema()
        assert set(self._COMMON_ALIASES) <= set(schema["properties"])
        assert "allOf" not in schema

    @pytest.mark.parametrize("model_class", _SUBCLASSES)
    def test_common_fields_accept_values_by_alias(self, model_class):
        """The inherited fields are still populated from their aliases."""
        model = model_class(Status={"State": "Enabled"}, PowerState="On", PowerCapability=True)
        assert model.status.state == "Enabled"
        assert model.power_state == "On"
        assert model.power_capability is True

    @pytest.mark.parametrize("model_class", _SUBCLASSES)
    def test_common_fields_accept_values_by_field_name(self, model_class):
        """populate_by_name is inherited from StatusCommon."""
        model = model_class(power_state="Off")
        assert model.power_state == "Off"


class TestDevicePortListModel:
    """Test the DevicePortListModel model, in particular the LTSSMState field."""

    def test_valid_ltssm_state(self):
        """A documented LTSSM state value is accepted."""
        model = DevicePortListModel(LTSSMState="L0")
        assert model.ltssm_state == "L0"

    def test_invalid_ltssm_state_raises(self):
        """An undocumented LTSSM state value raises ValidationError."""
        with pytest.raises(ValidationError):
            DevicePortListModel(LTSSMState="NotAState")

    def test_all_fields_optional(self):
        """All fields default to None."""
        model = DevicePortListModel()
        assert model.switch_id is None
        assert model.fabric_id is None
        assert model.switch_port_type is None
        assert model.switch_port_number is None
        assert model.ltssm_state is None

    @pytest.mark.parametrize("value", [SwitchPortType.USP, SwitchPortType.DSP])
    def test_switch_port_type_set(self, value: SwitchPortType):
        """switchPortType is populated from the SwitchPortType alias."""
        model = DevicePortListModel(switchPortType=value)
        assert model.switch_port_type == value

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

"""Unit test module for app/common/plugin/convert.py."""

import pytest

import app.common.basic_exceptions as exc
from app.common.plugin.convert import (
    convert_device_info_and_spec_info_to_element,
    convert_device_info_and_spec_info_to_responses,
    convert_port_info_to_elements,
    convert_switch_info_to_elements,
)
from app.common.plugin.models import DeviceType, ElementResponseModel, ErrorExceptionModel, ProcessorElementModel
from app.common.utils.fm_plugin_base import FMPortData, FMSwitchData
from app.common.utils.oob_plugin_base import OOBDeviceListItem

_PCIE_KWARGS = {"PCIeVendorId": "abcd", "PCIeDeviceId": "1234", "PCIeDeviceSerialNumber": "0123456789abcdef"}
_CPU_KWARGS = {"CPUManufacturer": "NEC", "CPUModel": "m1", "CPUSerialNumber": "sn1"}


class TestConvertPortInfoToElements:
    """Test convert_port_info_to_elements."""

    def test_cxl_type3_maps_to_memory(self):
        """A CXL-Type3 port maps to DeviceType.MEMORY."""
        data = [FMPortData(id="p1", deviceType="CXL-Type3")]
        result = convert_port_info_to_elements(data)
        assert result[0].device_type == DeviceType.MEMORY

    def test_other_type_maps_to_unknown(self):
        """A non-CXL-Type3 port maps to DeviceType.UNKNOWN."""
        data = [FMPortData(id="p1", deviceType="PCIe")]
        result = convert_port_info_to_elements(data)
        assert result[0].device_type == DeviceType.UNKNOWN

    def test_pcie_identity_all_present(self):
        """PCIeIdentity is built when all three identifiers are present."""
        data = [FMPortData(id="p1", **_PCIE_KWARGS)]
        result = convert_port_info_to_elements(data)
        assert result[0].hardware_id.pcie_identity is not None
        assert result[0].hardware_id.pcie_identity.pcie_vendor_id == "abcd"

    def test_pcie_identity_partial_is_none(self):
        """PCIeIdentity is None when any of the three identifiers is missing."""
        data = [FMPortData(id="p1", PCIeVendorId="abcd", PCIeDeviceId="1234")]
        result = convert_port_info_to_elements(data)
        assert result[0].hardware_id.pcie_identity is None

    def test_cpu_identity_all_present(self):
        """CPUIdentity is built when all three identifiers are present."""
        data = [FMPortData(id="p1", **_CPU_KWARGS)]
        result = convert_port_info_to_elements(data)
        assert result[0].hardware_id.cpu_identity is not None
        assert result[0].hardware_id.cpu_identity.cpu_manufacturer == "NEC"

    def test_device_port_list_empty_when_all_none(self):
        """DevicePortList is empty when fabric/switch/port fields are all None."""
        data = [FMPortData(id="p1")]
        result = convert_port_info_to_elements(data)
        assert result[0].schema_.device_port_list == []

    def test_device_port_list_populated(self):
        """DevicePortList has one entry when any port field is set."""
        data = [FMPortData(id="p1", fabricId="fab1")]
        result = convert_port_info_to_elements(data)
        assert len(result[0].schema_.device_port_list) == 1
        assert result[0].schema_.device_port_list[0].fabric_id == "fab1"

    def test_device_port_list_populated_when_port_number_is_zero(self):
        """switchPortNumber "0" is a value, not "unset", so DevicePortList has one entry."""
        data = [FMPortData(id="p1", switchPortNumber="0")]
        result = convert_port_info_to_elements(data)
        assert len(result[0].schema_.device_port_list) == 1
        assert result[0].schema_.device_port_list[0].switch_port_number == "0"

    @pytest.mark.parametrize("field", ["switchPortNumber", "fabricId"])
    def test_blank_port_field_raises_internal_error(self, field):
        """A blank StrictStr port field is "not None", so it is rejected by VisibleString."""
        data = [FMPortData(id="p1", **{field: ""})]
        with pytest.raises(exc.InternalHWControlError):
            convert_port_info_to_elements(data)

    @pytest.mark.parametrize("switch_id", ["", "sw1/../etc"])
    def test_switch_id_outside_element_id_charset_is_kept(self, switch_id):
        """DevicePortList's switchID skips the ElementID check, per spec 2.4.1."""
        data = [FMPortData(id="p1", switchId=switch_id)]
        result = convert_port_info_to_elements(data)
        assert result[0].schema_.device_port_list[0].switch_id == switch_id

    @pytest.mark.parametrize("element_id", ["p/1", ".."])
    def test_id_outside_element_id_charset_is_kept(self, element_id):
        """FMPortData.id skips the ElementID check, per spec 2.4.1."""
        data = [FMPortData(id=element_id)]
        result = convert_port_info_to_elements(data)
        assert result[0].id == element_id

    def test_connection_outside_element_id_charset_is_kept(self):
        """FMPortData.link skips the ElementID check, per spec 2.4.1."""
        data = [FMPortData(id="p1", link=["p2/../etc"])]
        result = convert_port_info_to_elements(data)
        assert result[0].connection == ["p2/../etc"]

    def test_ltssm_state_disable_is_mapped_to_disabled(self):
        """FMPortData's "Disable" LTSSMState value is mapped to models' "Disabled"."""
        data = [FMPortData(id="p1", LTSSMState="Disable")]
        result = convert_port_info_to_elements(data)
        assert result[0].schema_.device_port_list[0].ltssm_state == "Disabled"

    def test_ltssm_state_other_value_passes_through(self):
        """A documented LTSSMState value other than "Disable" is passed through unchanged."""
        data = [FMPortData(id="p1", LTSSMState="L0")]
        result = convert_port_info_to_elements(data)
        assert result[0].schema_.device_port_list[0].ltssm_state == "L0"

    def test_capacity_mib_computed_for_cxl_type3(self):
        """Capacity fields are computed (floor division to MiB) for CXL-Type3."""
        data = [
            FMPortData(
                id="p1",
                deviceType="CXL-Type3",
                capacity={"total": 100 * 1024 * 1024, "volatile": 60 * 1024 * 1024, "persistent": 40 * 1024 * 1024},
            )
        ]
        result = convert_port_info_to_elements(data)
        assert result[0].schema_.capacity_mib == 100
        assert result[0].schema_.volatile_region_size_limit_mib == 60
        assert result[0].schema_.non_volatile_size_mib == 40

    def test_capacity_mib_none_for_non_cxl_type3(self):
        """Capacity fields are absent (SchemaCommon has no capacity fields) when the device is not CXL-Type3."""
        data = [FMPortData(id="p1", deviceType="PCIe")]
        result = convert_port_info_to_elements(data)
        assert not hasattr(result[0].schema_, "capacity_mib")

    def test_connection_is_link_and_link_is_none(self):
        """FMPortData.link maps to ElementModel.connection; ElementModel.link is always None."""
        data = [FMPortData(id="p1", link=["a", "b"])]
        result = convert_port_info_to_elements(data)
        assert result[0].connection == ["a", "b"]
        assert result[0].link is None

    def test_invalid_ltssm_state_raises_internal_error(self, mocker):
        """An unmappable LTSSMState value fails DevicePortListModel validation and raises InternalHWControlError."""
        data = [FMPortData(id="p1", fabricId="fab1")]
        mocker.patch(
            "app.common.plugin.convert._LTSSM_STATE_MAP",
            {},
        )
        item = data[0]
        item.ltssm_state = None
        # Force an unrecognized value directly to bypass FMPortData's own Literal constraint.
        object.__setattr__(item, "ltssm_state", "NotAState")
        with pytest.raises(exc.InternalHWControlError):
            convert_port_info_to_elements(data)


class TestConvertSwitchInfoToElements:
    """Test convert_switch_info_to_elements."""

    def test_switch_identity_use_provided_values(self):
        """switchIdentity uses FMSwitchData's manufacturer/model/serialNumber when present."""
        data = [FMSwitchData(switchId="sw1", switchManufacturer="NEC", switchModel="m1", switchSerialNumber="sn1")]
        result = convert_switch_info_to_elements("mgr1", data)
        assert result[0].hardware_id.switch_identity.switch_manufacturer == "NEC"

    def test_switch_identity_fallback_when_none(self):
        """switchIdentity falls back to '{manager_id}_{switch_id}' when a field is None."""
        data = [FMSwitchData(switchId="sw1")]
        result = convert_switch_info_to_elements("mgr1", data)
        assert result[0].hardware_id.switch_identity.switch_manufacturer == "mgr1_sw1"
        assert result[0].hardware_id.switch_identity.switch_model == "mgr1_sw1"
        assert result[0].hardware_id.switch_identity.switch_serial_number == "mgr1_sw1"

    @pytest.mark.parametrize("field", ["switchManufacturer", "switchModel", "switchSerialNumber"])
    def test_blank_switch_identity_field_raises_internal_error(self, field):
        """A blank StrictStr field is "not None", so it is rejected by VisibleString."""
        data = [FMSwitchData(switchId="sw1", **{field: ""})]
        with pytest.raises(exc.InternalHWControlError):
            convert_switch_info_to_elements("mgr1", data)

    def test_device_type_is_switch(self):
        """device_type is always DeviceType.SWITCH."""
        data = [FMSwitchData(switchId="sw1")]
        result = convert_switch_info_to_elements("mgr1", data)
        assert result[0].device_type == DeviceType.SWITCH

    def test_link_maps_to_link_and_connection_is_none(self):
        """FMSwitchData.link maps to ElementModel.link; connection is always None."""
        data = [FMSwitchData(switchId="sw1", link=["sw2"])]
        result = convert_switch_info_to_elements("mgr1", data)
        assert result[0].link == ["sw2"]
        assert result[0].connection is None

    def test_device_port_list_is_empty(self):
        """schema.DevicePortList is always an empty list."""
        data = [FMSwitchData(switchId="sw1")]
        result = convert_switch_info_to_elements("mgr1", data)
        assert result[0].schema_.device_port_list == []

    def test_link_outside_element_id_charset_is_kept(self):
        """A link entry skips the ElementID check, per spec 2.4.2."""
        data = [FMSwitchData(switchId="sw1", link=["sw2/../etc"])]
        result = convert_switch_info_to_elements("mgr1", data)
        assert result[0].link == ["sw2/../etc"]

    @pytest.mark.parametrize("switch_id", ["sw/1", "."])
    def test_switch_id_outside_element_id_charset_is_kept(self, switch_id):
        """FMSwitchData.switchId skips the ElementID check, per spec 2.4.2."""
        data = [FMSwitchData(switchId=switch_id)]
        result = convert_switch_info_to_elements("mgr1", data)
        assert result[0].id == switch_id


class TestConvertDeviceInfoAndSpecInfoToElement:
    """Test convert_device_info_and_spec_info_to_element."""

    def test_basic_fields(self):
        """id, deviceType and schema are taken from device/spec."""
        device = OOBDeviceListItem(oobDeviceID="dev1", deviceType="CPU")
        spec = {"schema": {"DevicePortList": []}, "time": "2026-01-01T00:00:00Z"}
        element = convert_device_info_and_spec_info_to_element(device, spec)
        assert isinstance(element, ProcessorElementModel)
        assert element.id == "dev1"
        assert element.device_type == DeviceType.CPU
        assert element.schema_.device_port_list == []

    def test_device_keys_and_port_keys_passed_through(self):
        """deviceKeys/portKeys are passed through without conversion."""
        device = OOBDeviceListItem(oobDeviceID="dev1", deviceType="CPU", deviceKeys={"a": "b"}, portKeys={"c": "d"})
        spec = {"schema": {"DevicePortList": []}, "time": "2026-01-01T00:00:00Z"}
        element = convert_device_info_and_spec_info_to_element(device, spec)
        assert element.hardware_id.device_keys == {"a": "b"}
        assert element.hardware_id.port_keys == {"c": "d"}

    def test_link_missing_key_is_none(self):
        """A spec dict with no "link" key produces link=None."""
        device = OOBDeviceListItem(oobDeviceID="dev1", deviceType="CPU")
        spec = {"schema": {"DevicePortList": []}, "time": "2026-01-01T00:00:00Z"}
        element = convert_device_info_and_spec_info_to_element(device, spec)
        assert element.link is None

    def test_link_valid_format_converted_to_device_ids(self):
        """A spec dict with a valid "link" list is converted to a list of device IDs."""
        device = OOBDeviceListItem(oobDeviceID="dev1", deviceType="CPU")
        spec = {
            "schema": {"DevicePortList": []},
            "time": "2026-01-01T00:00:00Z",
            "link": [{"deviceID": "dev2", "type": "CPU"}],
        }
        element = convert_device_info_and_spec_info_to_element(device, spec)
        assert element.link == ["dev2"]

    def test_link_invalid_format_raises_internal_error(self):
        """A spec dict with a non-list "link" value raises InternalHWControlError."""
        device = OOBDeviceListItem(oobDeviceID="dev1", deviceType="CPU")
        spec = {"schema": {"DevicePortList": []}, "time": "2026-01-01T00:00:00Z", "link": "not-a-list"}
        with pytest.raises(exc.InternalHWControlError):
            convert_device_info_and_spec_info_to_element(device, spec)

    def test_missing_time_raises_internal_error(self):
        """A spec dict without a "time" key raises InternalHWControlError."""
        device = OOBDeviceListItem(oobDeviceID="dev1", deviceType="CPU")
        spec = {"schema": {"DevicePortList": []}}
        with pytest.raises(exc.InternalHWControlError):
            convert_device_info_and_spec_info_to_element(device, spec)

    def test_missing_schema_raises_internal_error(self):
        """A spec dict without a "schema" key raises InternalHWControlError."""
        device = OOBDeviceListItem(oobDeviceID="dev1", deviceType="CPU")
        spec = {"time": "2026-01-01T00:00:00Z"}
        with pytest.raises(exc.InternalHWControlError):
            convert_device_info_and_spec_info_to_element(device, spec)


class TestConvertDeviceInfoAndSpecInfoToResponses:
    """Test convert_device_info_and_spec_info_to_responses."""

    def test_matching_spec_returns_element_response(self):
        """A device with a matching spec entry produces a kind="element" ResponseModel."""
        device = OOBDeviceListItem(oobDeviceID="dev1", deviceType="CPU")
        specs = [{"deviceID": "dev1", "schema": {"DevicePortList": []}, "time": "2026-01-01T00:00:00Z"}]
        result = convert_device_info_and_spec_info_to_responses([device], specs)
        assert len(result) == 1
        assert isinstance(result[0], ElementResponseModel)
        assert result[0].kind == "element"
        assert isinstance(result[0].data, ProcessorElementModel)

    def test_missing_spec_returns_404_error_response(self):
        """A device with no matching spec entry produces a 404 error ResponseModel."""
        device = OOBDeviceListItem(oobDeviceID="dev1", deviceType="CPU")
        result = convert_device_info_and_spec_info_to_responses([device], [])
        assert result[0].kind == "error"
        assert isinstance(result[0].data, ErrorExceptionModel)
        assert result[0].data.status == 404
        assert result[0].data.detail == "spec data is not found."
        assert result[0].data.title == "Not Found"
        assert result[0].data.instance == "dev1"

    def test_conversion_failure_returns_500_error_response(self):
        """A spec that fails conversion produces a 500 error ResponseModel carrying the exception message."""
        device = OOBDeviceListItem(oobDeviceID="dev1", deviceType="CPU")
        specs = [{"deviceID": "dev1"}]  # missing "schema" and "time"
        result = convert_device_info_and_spec_info_to_responses([device], specs)
        assert result[0].kind == "error"
        assert result[0].data.status == 500
        assert result[0].data.title == "Internal Server Error"
        assert result[0].data.instance == "dev1"
        assert result[0].data.detail.endswith("failed to convert spec data: KeyError")

    def test_conversion_failure_detail_distinguishes_the_cause(self):
        """The 500 error "detail" names the failing exception type, so causes are distinguishable."""
        device = OOBDeviceListItem(oobDeviceID="dev1", deviceType="CPU")
        specs = [
            {"deviceID": "dev1", "schema": {"DevicePortList": []}, "time": "2026-01-01T00:00:00Z", "link": "not-a-list"}
        ]
        result = convert_device_info_and_spec_info_to_responses([device], specs)
        assert result[0].data.detail.endswith("failed to convert spec data: ValueError")

    def test_device_id_outside_element_id_charset_is_kept(self):
        """OOBDeviceListItem.oobDeviceID skips the ElementID check, per spec 2.4.3."""
        device = OOBDeviceListItem(oobDeviceID="dev/1", deviceType="CPU")
        specs = [{"deviceID": "dev/1", "schema": {"DevicePortList": []}, "time": "2026-01-01T00:00:00Z"}]
        result = convert_device_info_and_spec_info_to_responses([device], specs)
        assert result[0].kind == "element"
        assert result[0].data.id == "dev/1"

    def test_missing_spec_with_blank_device_id_falls_back_to_placeholder_instance(self):
        """A blank oob_device_id falls back to a placeholder "instance" instead of failing."""
        device = OOBDeviceListItem(oobDeviceID="", deviceType="CPU")
        result = convert_device_info_and_spec_info_to_responses([device], [])
        assert result[0].kind == "error"
        assert result[0].data.instance == "unknown"

    def test_multiple_devices_mixed_results(self):
        """Multiple devices produce one response each, preserving order."""
        device1 = OOBDeviceListItem(oobDeviceID="dev1", deviceType="CPU")
        device2 = OOBDeviceListItem(oobDeviceID="dev2", deviceType="CPU")
        specs = [{"deviceID": "dev1", "schema": {"DevicePortList": []}, "time": "2026-01-01T00:00:00Z"}]
        result = convert_device_info_and_spec_info_to_responses([device1, device2], specs)
        assert len(result) == 2
        assert result[0].kind == "element"
        assert result[1].kind == "error"

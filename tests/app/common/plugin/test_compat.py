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

"""Unit test module for app/common/plugin/compat.py."""

from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

import app.common.basic_exceptions as exc
from app.common import constants
from app.common.device_manager.repository import ResourceEntity, ResourceOOBRelation
from app.common.plugin.compat import ServicePluginFMCompatible, ServicePluginOOBCompatible
from app.common.plugin.models import (
    ElementResponseModel,
    PowerStateModel,
    ProcessorElementModel,
    ProcessorMetricModel,
    SwitchOrUnknownElementModel,
    TimeStampModel,
)
from app.common.utils.fm_plugin_base import FMPluginBase, FMPortData, FMSwitchData
from app.common.utils.oob_plugin_base import OOBDeviceListItem, OOBPluginBase


def _make_fm_compatible(plugin: MagicMock, manager_id: str = "mgr1") -> ServicePluginFMCompatible:
    instance = ServicePluginFMCompatible()
    instance.plugin = plugin
    instance.manager_id = manager_id
    return instance


def _make_oob_compatible(plugin: MagicMock, manager_id: str = "mgr1") -> ServicePluginOOBCompatible:
    instance = ServicePluginOOBCompatible()
    instance.plugin = plugin
    instance.manager_id = manager_id
    return instance


class TestServicePluginFMCompatibleInit:
    """Test ServicePluginFMCompatible.__init__."""

    def test_does_not_call_service_plugin_init(self):
        """ServicePlugin.__init__'s attributes (_baseurl etc.) are not set."""
        instance = ServicePluginFMCompatible()
        assert not hasattr(instance, "_baseurl")
        assert instance.plugin is None
        assert instance.manager_id == ""

    def test_raises_when_plugin_is_not_set(self):
        """_fm_plugin raises InternalHWControlError while plugin is None."""
        instance = ServicePluginFMCompatible()
        with pytest.raises(exc.InternalHWControlError):
            instance._fm_plugin()


class TestServicePluginFMCompatibleGetElements:
    """Test ServicePluginFMCompatible.get_elements."""

    def test_combines_ports_and_switches(self):
        """get_elements combines converted ports and switches into ElementResponseModel."""
        plugin = MagicMock(spec=FMPluginBase)
        plugin.get_port_info.return_value = {"data": [FMPortData(id="p1")]}
        plugin.get_switch_info.return_value = {"data": [FMSwitchData(switchId="sw1")]}
        instance = _make_fm_compatible(plugin)
        result = instance.get_elements()
        assert len(result) == 2
        assert all(isinstance(r, ElementResponseModel) for r in result)
        plugin.get_port_info.assert_called_once_with()
        plugin.get_switch_info.assert_called_once_with()

    def test_empty_result_raises_internal_error(self):
        """An empty combined result raises InternalHWControlError."""
        plugin = MagicMock(spec=FMPluginBase)
        plugin.get_port_info.return_value = {"data": []}
        plugin.get_switch_info.return_value = {"data": []}
        instance = _make_fm_compatible(plugin)
        with pytest.raises(exc.InternalHWControlError):
            instance.get_elements()

    def test_hw_control_error_propagates_unchanged(self):
        """A BaseHWControlError from the legacy plugin is sent through unchanged."""
        plugin = MagicMock(spec=FMPluginBase)
        plugin.get_port_info.side_effect = exc.DeviceNotFoundHWControlError
        instance = _make_fm_compatible(plugin)
        with pytest.raises(exc.DeviceNotFoundHWControlError):
            instance.get_elements()

    def test_unexpected_exception_becomes_unknown_error(self):
        """An unexpected exception from the legacy plugin becomes UnknownHWControlError."""
        plugin = MagicMock(spec=FMPluginBase)
        plugin.get_port_info.side_effect = ZeroDivisionError
        instance = _make_fm_compatible(plugin)
        with pytest.raises(exc.UnknownHWControlError):
            instance.get_elements()

    def test_response_without_data_key_becomes_unknown_error(self):
        """A legacy response without the "data" key becomes UnknownHWControlError."""
        plugin = MagicMock(spec=FMPluginBase)
        plugin.get_port_info.return_value = {"ports": [FMPortData(id="p1")]}
        instance = _make_fm_compatible(plugin)
        with pytest.raises(exc.UnknownHWControlError):
            instance.get_elements()

    def test_non_subscriptable_response_becomes_unknown_error(self):
        """A legacy response that is not a mapping becomes UnknownHWControlError."""
        plugin = MagicMock(spec=FMPluginBase)
        plugin.get_port_info.return_value = None
        instance = _make_fm_compatible(plugin)
        with pytest.raises(exc.UnknownHWControlError):
            instance.get_elements()


class TestServicePluginFMCompatibleGetElement:
    """Test ServicePluginFMCompatible.get_element."""

    def test_found_via_port_info(self):
        """A port found via get_port_info is returned directly."""
        plugin = MagicMock(spec=FMPluginBase)
        plugin.get_port_info.return_value = {"data": [FMPortData(id="p1")]}
        instance = _make_fm_compatible(plugin)
        result = instance.get_element("p1")
        assert isinstance(result, SwitchOrUnknownElementModel)
        plugin.get_switch_info.assert_not_called()

    def test_falls_back_to_switch_info(self):
        """A port not found (DeviceNotFoundHWControlError) falls back to get_switch_info."""
        plugin = MagicMock(spec=FMPluginBase)
        plugin.get_port_info.side_effect = exc.DeviceNotFoundHWControlError
        plugin.get_switch_info.return_value = {"data": [FMSwitchData(switchId="sw1")]}
        instance = _make_fm_compatible(plugin)
        result = instance.get_element("sw1")
        assert isinstance(result, SwitchOrUnknownElementModel)
        assert result.id == "sw1"

    def test_both_fail_raises_internal_error(self):
        """A switch fallback with zero results raises InternalHWControlError."""
        plugin = MagicMock(spec=FMPluginBase)
        plugin.get_port_info.side_effect = exc.DeviceNotFoundHWControlError
        plugin.get_switch_info.return_value = {"data": []}
        instance = _make_fm_compatible(plugin)
        with pytest.raises(exc.InternalHWControlError):
            instance.get_element("missing")

    def test_switch_response_without_data_key_becomes_unknown_error(self):
        """A malformed switch response inside the except block becomes UnknownHWControlError."""
        plugin = MagicMock(spec=FMPluginBase)
        plugin.get_port_info.side_effect = exc.DeviceNotFoundHWControlError
        plugin.get_switch_info.return_value = {"switches": [FMSwitchData(switchId="sw1")]}
        instance = _make_fm_compatible(plugin)
        with pytest.raises(exc.UnknownHWControlError):
            instance.get_element("sw1")

    def test_element_id_outside_element_id_charset_is_not_rejected_before_calling_plugin(self):
        """An element_id outside the ElementID charset reaches the legacy plugin call, not rejected by validate_call.

        Legacy FM plugin IDs (FMPortData.id) are plain str with no ElementID
        constraint, so this class does not use @validate_call on element_id;
        the value is passed straight to plugin.get_port_info instead of
        being rejected up front with pydantic.ValidationError.
        """
        plugin = MagicMock(spec=FMPluginBase)
        plugin.get_port_info.side_effect = exc.DeviceNotFoundHWControlError
        plugin.get_switch_info.side_effect = exc.DeviceNotFoundHWControlError
        instance = _make_fm_compatible(plugin)
        with pytest.raises(exc.DeviceNotFoundHWControlError):
            instance.get_element("../admin")
        plugin.get_port_info.assert_called_once_with(target_id="../admin")


class TestServicePluginFMCompatibleUnsupported:
    """Test the unsupported methods of ServicePluginFMCompatible."""

    @pytest.mark.parametrize(
        "method_name", ["get_power_state", "get_metric", "power_on", "power_off", "os_shutdown", "cpu_reset"]
    )
    def test_raises_not_supported(self, method_name: str):
        """Each unsupported method raises RequestNotSupportedHWControlError."""
        plugin = MagicMock(spec=FMPluginBase)
        instance = _make_fm_compatible(plugin)
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            getattr(instance, method_name)("elem-1")


class TestServicePluginFMCompatibleConnection:
    """Test ServicePluginFMCompatible.add_connection/remove_connection."""

    def test_add_connection_calls_connect(self):
        """add_connection calls plugin.connect with cpu_id/device_id and returns TimeStampModel."""
        plugin = MagicMock(spec=FMPluginBase)
        instance = _make_fm_compatible(plugin)
        result = instance.add_connection("u1", "d1")
        assert isinstance(result, TimeStampModel)
        plugin.connect.assert_called_once_with(cpu_id="u1", device_id="d1")

    def test_remove_connection_calls_disconnect(self):
        """remove_connection calls plugin.disconnect with cpu_id/device_id and returns TimeStampModel."""
        plugin = MagicMock(spec=FMPluginBase)
        instance = _make_fm_compatible(plugin)
        result = instance.remove_connection("u1", "d1")
        assert isinstance(result, TimeStampModel)
        plugin.disconnect.assert_called_once_with(cpu_id="u1", device_id="d1")


class TestServicePluginOOBCompatibleInit:
    """Test ServicePluginOOBCompatible.__init__."""

    def test_does_not_call_service_plugin_init(self):
        """ServicePlugin.__init__'s attributes (_baseurl etc.) are not set."""
        instance = ServicePluginOOBCompatible()
        assert not hasattr(instance, "_baseurl")
        assert instance.plugin is None
        assert instance.manager_id == ""

    def test_raises_when_plugin_is_not_set(self):
        """_oob_plugin raises InternalHWControlError while plugin is None."""
        instance = ServicePluginOOBCompatible()
        with pytest.raises(exc.InternalHWControlError):
            instance._oob_plugin()


class TestServicePluginOOBCompatibleGetElements:
    """Test ServicePluginOOBCompatible.get_elements."""

    def test_returns_converted_responses(self):
        """get_elements builds key_values from get_device_info and converts get_spec_info."""
        plugin = MagicMock(spec=OOBPluginBase)
        plugin.get_device_info.return_value = [OOBDeviceListItem(oobDeviceID="dev1", deviceType="CPU")]
        plugin.get_spec_info.return_value = {
            "devices": [{"deviceID": "dev1", "schema": {"DevicePortList": []}, "time": "2026-01-01T00:00:00Z"}]
        }
        instance = _make_oob_compatible(plugin)
        result = instance.get_elements()
        assert len(result) == 1
        assert result[0].kind == "element"
        plugin.get_spec_info.assert_called_once_with(key_values=[{"oob_device_id": "dev1", "device_type": "CPU"}])

    def test_response_without_devices_key_becomes_unknown_error(self):
        """A legacy response without the "devices" key becomes UnknownHWControlError."""
        plugin = MagicMock(spec=OOBPluginBase)
        plugin.get_device_info.return_value = [OOBDeviceListItem(oobDeviceID="dev1", deviceType="CPU")]
        plugin.get_spec_info.return_value = {"data": []}
        instance = _make_oob_compatible(plugin)
        with pytest.raises(exc.UnknownHWControlError):
            instance.get_elements()

    def test_empty_result_raises_internal_error(self):
        """An empty device list raises InternalHWControlError."""
        plugin = MagicMock(spec=OOBPluginBase)
        plugin.get_device_info.return_value = []
        plugin.get_spec_info.return_value = {"devices": []}
        instance = _make_oob_compatible(plugin)
        with pytest.raises(exc.InternalHWControlError):
            instance.get_elements()


class TestServicePluginOOBCompatibleGetElement:
    """Test ServicePluginOOBCompatible.get_element."""

    def test_found_returns_element_model(self):
        """A matching device with a matching spec is converted to ElementModel."""
        plugin = MagicMock(spec=OOBPluginBase)
        plugin.get_device_info.return_value = [OOBDeviceListItem(oobDeviceID="dev1", deviceType="CPU")]
        plugin.get_spec_info.return_value = {
            "devices": [{"schema": {"DevicePortList": []}, "time": "2026-01-01T00:00:00Z"}]
        }
        instance = _make_oob_compatible(plugin)
        result = instance.get_element("dev1")
        assert isinstance(result, ProcessorElementModel)
        assert result.id == "dev1"

    def test_not_found_raises_device_not_found_error(self):
        """A device_id absent from get_device_info raises DeviceNotFoundHWControlError."""
        plugin = MagicMock(spec=OOBPluginBase)
        plugin.get_device_info.return_value = []
        instance = _make_oob_compatible(plugin)
        with pytest.raises(exc.DeviceNotFoundHWControlError):
            instance.get_element("missing")

    def test_multiple_spec_matches_raises_internal_error(self):
        """A spec result with other than one entry raises InternalHWControlError."""
        plugin = MagicMock(spec=OOBPluginBase)
        plugin.get_device_info.return_value = [OOBDeviceListItem(oobDeviceID="dev1", deviceType="CPU")]
        plugin.get_spec_info.return_value = {"devices": []}
        instance = _make_oob_compatible(plugin)
        with pytest.raises(exc.InternalHWControlError):
            instance.get_element("dev1")


class TestServicePluginOOBCompatibleConnectionUnsupported:
    """Test the unsupported connection methods of ServicePluginOOBCompatible."""

    def test_add_connection_raises_not_supported(self):
        """add_connection raises RequestNotSupportedHWControlError."""
        plugin = MagicMock(spec=OOBPluginBase)
        instance = _make_oob_compatible(plugin)
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            instance.add_connection("u1", "d1")

    def test_remove_connection_raises_not_supported(self):
        """remove_connection raises RequestNotSupportedHWControlError."""
        plugin = MagicMock(spec=OOBPluginBase)
        instance = _make_oob_compatible(plugin)
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            instance.remove_connection("u1", "d1")


class TestServicePluginOOBCompatibleGetDeviceType:
    """Test ServicePluginOOBCompatible._get_device_type."""

    def _resource_entity(self, oob_manager_id: str, oob_device_id: str, device_type: constants.DeviceType):
        return ResourceEntity(
            device_id="12345678-1234-4234-a234-123456789012",
            ports=[],
            oob_relations=[
                ResourceOOBRelation(oob_manager_id=oob_manager_id, oob_device_id=oob_device_id, device_type=device_type)
            ],
        )

    def test_found_returns_device_type_value(self, mocker: MockerFixture):
        """A matching (manager_id, element_id) relation returns its device_type.value."""
        session = MagicMock()
        mocker.patch("app.common.plugin.compat.DBManager.create_session", return_value=session)
        mocker.patch(
            "app.common.plugin.compat.DeviceRepository.get_active_resources",
            return_value=[self._resource_entity("mgr1", "dev1", constants.DeviceType.CPU)],
        )
        plugin = MagicMock(spec=OOBPluginBase)
        instance = _make_oob_compatible(plugin, manager_id="mgr1")
        assert instance._get_device_type("dev1") == "CPU"
        session.close.assert_called_once()

    def test_not_found_raises_device_not_found_error(self, mocker: MockerFixture):
        """No matching relation raises DeviceNotFoundHWControlError."""
        session = MagicMock()
        mocker.patch("app.common.plugin.compat.DBManager.create_session", return_value=session)
        mocker.patch(
            "app.common.plugin.compat.DeviceRepository.get_active_resources",
            return_value=[self._resource_entity("other_mgr", "dev1", constants.DeviceType.CPU)],
        )
        plugin = MagicMock(spec=OOBPluginBase)
        instance = _make_oob_compatible(plugin, manager_id="mgr1")
        with pytest.raises(exc.DeviceNotFoundHWControlError):
            instance._get_device_type("dev1")
        session.close.assert_called_once()

    def test_uninitialized_db_manager_raises_internal_error(self, mocker: MockerFixture):
        """DBManager.create_session raising RuntimeError becomes InternalHWControlError."""
        mocker.patch("app.common.plugin.compat.DBManager.create_session", side_effect=RuntimeError)
        plugin = MagicMock(spec=OOBPluginBase)
        instance = _make_oob_compatible(plugin, manager_id="mgr1")
        with pytest.raises(exc.InternalHWControlError):
            instance._get_device_type("dev1")

    def test_session_closed_even_on_repository_error(self, mocker: MockerFixture):
        """The session is closed even if get_active_resources raises."""
        session = MagicMock()
        mocker.patch("app.common.plugin.compat.DBManager.create_session", return_value=session)
        mocker.patch(
            "app.common.plugin.compat.DeviceRepository.get_active_resources",
            side_effect=exc.InternalHWControlError,
        )
        plugin = MagicMock(spec=OOBPluginBase)
        instance = _make_oob_compatible(plugin, manager_id="mgr1")
        with pytest.raises(exc.InternalHWControlError):
            instance._get_device_type("dev1")
        session.close.assert_called_once()


class TestServicePluginOOBCompatibleGetPowerState:
    """Test ServicePluginOOBCompatible.get_power_state."""

    def test_returns_power_state_model(self, mocker: MockerFixture):
        """A well-formed power state result is converted to PowerStateModel."""
        plugin = MagicMock(spec=OOBPluginBase)
        plugin.get_power_state.return_value = {"devices": [{"powerState": "On", "time": "2026-01-01T00:00:00Z"}]}
        instance = _make_oob_compatible(plugin)
        mocker.patch.object(instance, "_get_device_type", return_value="CPU")
        result = instance.get_power_state("dev1")
        assert isinstance(result, PowerStateModel)
        plugin.get_power_state.assert_called_once_with(key_values=[{"oob_device_id": "dev1", "device_type": "CPU"}])

    def test_missing_power_state_raises_not_supported(self, mocker: MockerFixture):
        """A result missing 'powerState' raises RequestNotSupportedHWControlError."""
        plugin = MagicMock(spec=OOBPluginBase)
        plugin.get_power_state.return_value = {"devices": [{"time": "2026-01-01T00:00:00Z"}]}
        instance = _make_oob_compatible(plugin)
        mocker.patch.object(instance, "_get_device_type", return_value="CPU")
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            instance.get_power_state("dev1")

    def test_missing_time_raises_internal_error(self, mocker: MockerFixture):
        """A result missing 'time' raises InternalHWControlError."""
        plugin = MagicMock(spec=OOBPluginBase)
        plugin.get_power_state.return_value = {"devices": [{"powerState": "On"}]}
        instance = _make_oob_compatible(plugin)
        mocker.patch.object(instance, "_get_device_type", return_value="CPU")
        with pytest.raises(exc.InternalHWControlError):
            instance.get_power_state("dev1")

    def test_multiple_results_raises_internal_error(self, mocker: MockerFixture):
        """A result with other than one entry raises InternalHWControlError."""
        plugin = MagicMock(spec=OOBPluginBase)
        plugin.get_power_state.return_value = {"devices": []}
        instance = _make_oob_compatible(plugin)
        mocker.patch.object(instance, "_get_device_type", return_value="CPU")
        with pytest.raises(exc.InternalHWControlError):
            instance.get_power_state("dev1")


class TestServicePluginOOBCompatibleGetMetric:
    """Test ServicePluginOOBCompatible.get_metric."""

    def test_returns_metric_model(self, mocker: MockerFixture):
        """A well-formed metric result is converted to MetricModel."""
        plugin = MagicMock(spec=OOBPluginBase)
        plugin.get_metric_info.return_value = {
            "devices": [{"deviceID": "dev1", "type": "CPU", "time": "2026-01-01T00:00:00Z"}]
        }
        instance = _make_oob_compatible(plugin)
        mocker.patch.object(instance, "_get_device_type", return_value="CPU")
        result = instance.get_metric("dev1")
        assert isinstance(result, ProcessorMetricModel)

    def test_missing_type_raises_internal_error(self, mocker: MockerFixture):
        """A result without the "type" key raises InternalHWControlError."""
        plugin = MagicMock(spec=OOBPluginBase)
        plugin.get_metric_info.return_value = {"devices": [{"deviceID": "dev1", "time": "2026-01-01T00:00:00Z"}]}
        instance = _make_oob_compatible(plugin)
        mocker.patch.object(instance, "_get_device_type", return_value="CPU")
        with pytest.raises(exc.InternalHWControlError):
            instance.get_metric("dev1")

    def test_multiple_results_raises_internal_error(self, mocker: MockerFixture):
        """A result with other than one entry raises InternalHWControlError."""
        plugin = MagicMock(spec=OOBPluginBase)
        plugin.get_metric_info.return_value = {"devices": []}
        instance = _make_oob_compatible(plugin)
        mocker.patch.object(instance, "_get_device_type", return_value="CPU")
        with pytest.raises(exc.InternalHWControlError):
            instance.get_metric("dev1")

    def test_invalid_result_raises_internal_error(self, mocker: MockerFixture):
        """A result that fails MetricModel validation raises InternalHWControlError."""
        plugin = MagicMock(spec=OOBPluginBase)
        plugin.get_metric_info.return_value = {"devices": [{"not": "valid"}]}
        instance = _make_oob_compatible(plugin)
        mocker.patch.object(instance, "_get_device_type", return_value="CPU")
        with pytest.raises(exc.InternalHWControlError):
            instance.get_metric("dev1")


class TestServicePluginOOBCompatibleActionMethods:
    """Test ServicePluginOOBCompatible.power_on/power_off/os_shutdown/cpu_reset."""

    @pytest.mark.parametrize(
        ("method_name", "legacy_method_name"),
        [
            ("power_on", "post_power_on"),
            ("power_off", "post_power_off"),
            ("os_shutdown", "post_os_shutdown"),
            ("cpu_reset", "post_cpu_reset"),
        ],
    )
    def test_calls_expected_legacy_method(self, mocker: MockerFixture, method_name: str, legacy_method_name: str):
        """Each action method calls the corresponding legacy method and returns TimeStampModel."""
        plugin = MagicMock(spec=OOBPluginBase)
        getattr(plugin, legacy_method_name).return_value = {"devices": [{"time": "2026-01-01T00:00:00Z"}]}
        instance = _make_oob_compatible(plugin)
        mocker.patch.object(instance, "_get_device_type", return_value="CPU")
        result = getattr(instance, method_name)("dev1")
        assert isinstance(result, TimeStampModel)
        getattr(plugin, legacy_method_name).assert_called_once_with(
            key_values=[{"oob_device_id": "dev1", "device_type": "CPU"}]
        )

    @pytest.mark.parametrize(
        ("method_name", "legacy_method_name"),
        [
            ("power_on", "post_power_on"),
            ("power_off", "post_power_off"),
            ("os_shutdown", "post_os_shutdown"),
            ("cpu_reset", "post_cpu_reset"),
        ],
    )
    def test_missing_time_raises_internal_error(self, mocker: MockerFixture, method_name: str, legacy_method_name: str):
        """A result missing 'time' raises InternalHWControlError."""
        plugin = MagicMock(spec=OOBPluginBase)
        getattr(plugin, legacy_method_name).return_value = {"devices": [{}]}
        instance = _make_oob_compatible(plugin)
        mocker.patch.object(instance, "_get_device_type", return_value="CPU")
        with pytest.raises(exc.InternalHWControlError):
            getattr(instance, method_name)("dev1")

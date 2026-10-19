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

"""Plugin execution classes that call legacy Python module plugins.

File: hw-control/src/app/common/plugin/compat.py

Used only by app.common.plugin.plugin_manager, and planned for removal
once support for the legacy Python module plugins ends.
"""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from pydantic import TypeAdapter

import app.common.basic_exceptions as exc
from app.common.device_manager import DBManager, DeviceRepository
from app.common.plugin.convert import (
    convert_device_info_and_spec_info_to_element,
    convert_device_info_and_spec_info_to_responses,
    convert_port_info_to_elements,
    convert_switch_info_to_elements,
)
from app.common.plugin.models import (
    ElementID,
    ElementModel,
    ElementResponseModel,
    MetricModel,
    PowerStateModel,
    ResponseModel,
    TimeStampModel,
)
from app.common.plugin.service import ServicePlugin
from app.common.utils.fm_plugin_base import FMPluginBase
from app.common.utils.oob_plugin_base import OOBPluginBase

_metric_type_adapter: TypeAdapter[MetricModel] = TypeAdapter(MetricModel)

# Key that wraps the payload of a legacy FM plugin response.
_FM_DATA_KEY = "data"
# Key that wraps the payload of a legacy OOB plugin response.
_OOB_DATA_KEY = "devices"


def _call_legacy[T](callable_: Callable[..., T], /, *args: Any, **kwargs: Any) -> T:
    """Call a legacy plugin method, converting unexpected exceptions.

    Raises:
        BaseHWControlError: Sent through unchanged.
        UnknownHWControlError: Any other exception raised by the legacy
            plugin.
    """
    try:
        return callable_(*args, **kwargs)
    except exc.BaseHWControlError:
        raise
    except Exception as err:
        raise exc.UnknownHWControlError from err


def _call_legacy_data(callable_: Callable[..., Any], data_key: str, /, *args: Any, **kwargs: Any) -> Any:
    """Call a legacy plugin method and return the payload of its response.

    The legacy plugin base classes document a dict wrapping the payload as
    the return value, under "data" for FM and "devices" for OOB, but that is
    only a convention: a plugin is free to return anything. Reading the entry
    here keeps a malformed response from leaving this module as a bare
    KeyError/TypeError, which the spec (2.8.1, 2.8.2) requires to be
    reported as UnknownHWControlError.

    Args:
        callable_ (Callable[..., Any]): Legacy plugin method to call.
        data_key (str): Key that wraps the payload of the response.
            `_FM_DATA_KEY` for FM plugins, `_OOB_DATA_KEY` for OOB plugins.
        *args (Any): Positional arguments passed to `callable_`.
        **kwargs (Any): Keyword arguments passed to `callable_`.

    Returns:
        Any: The `data_key` entry of the legacy plugin's response.

    Raises:
        BaseHWControlError: Sent through unchanged.
        UnknownHWControlError: Any other exception raised by the legacy
            plugin, or its response had no `data_key` entry.
    """
    response = _call_legacy(callable_, *args, **kwargs)
    try:
        return response[data_key]
    except (KeyError, TypeError) as err:
        raise exc.UnknownHWControlError from err


class ServicePluginFMCompatible(ServicePlugin):
    """Plugin execution class that calls a legacy FM plugin.

    Attributes:
        plugin (FMPluginBase | None): The legacy FM plugin instance. Set by
            get_plugin after this instance is created.
        manager_id (str): Manager ID. Set by get_plugin after this instance
            is created; it is empty until then.
    """

    def __init__(self) -> None:
        """Initialize without calling ServicePlugin.__init__.

        ServicePlugin.__init__ sets up the remote-plugin HTTP configuration
        (base URL, timeout, supported features), none of which this class
        needs since it wraps a legacy FM plugin instance instead.
        """
        self.plugin: FMPluginBase | None = None
        self.manager_id: str = ""
        self.specific_data: dict | None = None

    def _fm_plugin(self) -> FMPluginBase:
        """Return `self.plugin`, narrowed to non-None.

        get_plugin always sets `plugin` right after constructing this
        class, before any other method is called.

        Returns:
            FMPluginBase: The legacy FM plugin instance.

        Raises:
            InternalHWControlError: `plugin` has not been set yet.
        """
        if self.plugin is None:
            raise exc.InternalHWControlError
        return self.plugin

    def get_elements(self) -> list[ResponseModel]:
        """Get the information of all elements managed by the legacy FM plugin.

        Returns:
            list[ResponseModel]: The information of all elements.

        Raises:
            InternalHWControlError: The converted list was empty.
            BaseHWControlError: Sent through unchanged from the legacy plugin.
            UnknownHWControlError: Any other exception from the legacy plugin.
        """
        plugin = self._fm_plugin()
        ports = _call_legacy_data(plugin.get_port_info, _FM_DATA_KEY)
        switches = _call_legacy_data(plugin.get_switch_info, _FM_DATA_KEY)
        elements = convert_port_info_to_elements(ports) + convert_switch_info_to_elements(self.manager_id, switches)
        if not elements:
            raise exc.InternalHWControlError
        return [ElementResponseModel(data=element) for element in elements]

    def get_element(self, element_id: ElementID) -> ElementModel:
        """Get the information of the specified element.

        Args:
            element_id (ElementID): ID of the element to get.

        Returns:
            ElementModel: The information of the specified element.

        Raises:
            InternalHWControlError: The converted result did not contain
                exactly one element.
            BaseHWControlError: Sent through unchanged from the legacy plugin.
            UnknownHWControlError: Any other exception from the legacy plugin.
        """
        plugin = self._fm_plugin()
        try:
            ports = _call_legacy_data(plugin.get_port_info, _FM_DATA_KEY, target_id=element_id)
        except exc.DeviceNotFoundHWControlError:
            switches = _call_legacy_data(plugin.get_switch_info, _FM_DATA_KEY, switch_id=element_id)
            elements = convert_switch_info_to_elements(self.manager_id, switches)
        else:
            elements = convert_port_info_to_elements(ports)
        if len(elements) != 1:
            raise exc.InternalHWControlError
        return elements[0]

    def get_power_state(self, element_id: ElementID) -> PowerStateModel:
        """Not supported by legacy FM plugins.

        Raises:
            RequestNotSupportedHWControlError: Always raised.
        """
        raise exc.RequestNotSupportedHWControlError

    def get_metric(self, element_id: ElementID) -> MetricModel:
        """Not supported by legacy FM plugins.

        Raises:
            RequestNotSupportedHWControlError: Always raised.
        """
        raise exc.RequestNotSupportedHWControlError

    def power_on(self, element_id: ElementID) -> TimeStampModel:
        """Not supported by legacy FM plugins.

        Raises:
            RequestNotSupportedHWControlError: Always raised.
        """
        raise exc.RequestNotSupportedHWControlError

    def power_off(self, element_id: ElementID) -> TimeStampModel:
        """Not supported by legacy FM plugins.

        Raises:
            RequestNotSupportedHWControlError: Always raised.
        """
        raise exc.RequestNotSupportedHWControlError

    def os_shutdown(self, element_id: ElementID) -> TimeStampModel:
        """Not supported by legacy FM plugins.

        Raises:
            RequestNotSupportedHWControlError: Always raised.
        """
        raise exc.RequestNotSupportedHWControlError

    def cpu_reset(self, element_id: ElementID) -> TimeStampModel:
        """Not supported by legacy FM plugins.

        Raises:
            RequestNotSupportedHWControlError: Always raised.
        """
        raise exc.RequestNotSupportedHWControlError

    def add_connection(self, uid: ElementID, did: ElementID) -> TimeStampModel:
        """Connect the specified USP-side and DSP-side elements via the legacy FM plugin.

        Args:
            uid (ElementID): ID of the USP-side element.
            did (ElementID): ID of the DSP-side element.

        Returns:
            TimeStampModel: The date and time the connection succeeded.

        Raises:
            BaseHWControlError: Sent through unchanged from the legacy plugin.
            UnknownHWControlError: Any other exception from the legacy plugin.
        """
        _call_legacy(self._fm_plugin().connect, cpu_id=uid, device_id=did)
        return TimeStampModel(time=datetime.now(UTC))

    def remove_connection(self, uid: ElementID, did: ElementID) -> TimeStampModel:
        """Disconnect the specified USP-side and DSP-side elements via the legacy FM plugin.

        Args:
            uid (ElementID): ID of the USP-side element.
            did (ElementID): ID of the DSP-side element.

        Returns:
            TimeStampModel: The date and time the disconnection succeeded.

        Raises:
            BaseHWControlError: Sent through unchanged from the legacy plugin.
            UnknownHWControlError: Any other exception from the legacy plugin.
        """
        _call_legacy(self._fm_plugin().disconnect, cpu_id=uid, device_id=did)
        return TimeStampModel(time=datetime.now(UTC))


class ServicePluginOOBCompatible(ServicePlugin):
    """Plugin execution class that calls a legacy OOB plugin.

    Attributes:
        plugin (OOBPluginBase | None): The legacy OOB plugin instance. Set
            by get_plugin after this instance is created.
        manager_id (str): Manager ID. Set by get_plugin after this instance
            is created; it is empty until then.
    """

    def __init__(self) -> None:
        """Initialize without calling ServicePlugin.__init__.

        ServicePlugin.__init__ sets up the remote-plugin HTTP configuration
        (base URL, timeout, supported features), none of which this class
        needs since it wraps a legacy OOB plugin instance instead.
        """
        self.plugin: OOBPluginBase | None = None
        self.manager_id: str = ""
        self.specific_data: dict | None = None

    def _oob_plugin(self) -> OOBPluginBase:
        """Return `self.plugin`, narrowed to non-None.

        get_plugin always sets `plugin` right after constructing this
        class, before any other method is called.

        Returns:
            OOBPluginBase: The legacy OOB plugin instance.

        Raises:
            InternalHWControlError: `plugin` has not been set yet.
        """
        if self.plugin is None:
            raise exc.InternalHWControlError
        return self.plugin

    def get_elements(self) -> list[ResponseModel]:
        """Get the information of all elements managed by the legacy OOB plugin.

        Returns:
            list[ResponseModel]: The information of all elements.

        Raises:
            InternalHWControlError: The converted list was empty.
            BaseHWControlError: Sent through unchanged from the legacy plugin.
            UnknownHWControlError: Any other exception from the legacy plugin.
        """
        plugin = self._oob_plugin()
        devices = _call_legacy(plugin.get_device_info)
        key_values = [{"oob_device_id": d.oob_device_id, "device_type": d.device_type} for d in devices]
        specs = _call_legacy_data(plugin.get_spec_info, _OOB_DATA_KEY, key_values=key_values)
        responses = convert_device_info_and_spec_info_to_responses(devices, specs)
        if not responses:
            raise exc.InternalHWControlError
        return responses

    def get_element(self, element_id: ElementID) -> ElementModel:
        """Get the information of the specified element.

        Args:
            element_id (ElementID): ID of the element to get.

        Returns:
            ElementModel: The information of the specified element.

        Raises:
            DeviceNotFoundHWControlError: No matching device was found.
            InternalHWControlError: The converted result did not contain
                exactly one element.
            BaseHWControlError: Sent through unchanged from the legacy plugin.
            UnknownHWControlError: Any other exception from the legacy plugin.
        """
        plugin = self._oob_plugin()
        devices = _call_legacy(plugin.get_device_info)
        device = next((d for d in devices if d.oob_device_id == element_id), None)
        if device is None:
            raise exc.DeviceNotFoundHWControlError
        key_values = [{"oob_device_id": element_id, "device_type": device.device_type}]
        specs = _call_legacy_data(plugin.get_spec_info, _OOB_DATA_KEY, key_values=key_values)
        if len(specs) != 1:
            raise exc.InternalHWControlError
        return convert_device_info_and_spec_info_to_element(device, specs[0])

    def _get_device_type(self, element_id: str) -> str:
        """Get the device type of `element_id` from the device management database.

        Raises:
            DeviceNotFoundHWControlError: No matching device was found.
            InternalHWControlError: The database session could not be
                created.
        """
        try:
            session = DBManager.create_session()
        except RuntimeError as err:
            raise exc.InternalHWControlError from err
        try:
            resources = DeviceRepository(session).get_active_resources()
        finally:
            session.close()
        for resource in resources:
            for relation in resource.oob_relations:
                if relation.oob_manager_id == self.manager_id and relation.oob_device_id == element_id:
                    return relation.device_type.value
        raise exc.DeviceNotFoundHWControlError

    def get_power_state(self, element_id: ElementID) -> PowerStateModel:
        """Get the power state of the specified element via the legacy OOB plugin.

        Args:
            element_id (ElementID): ID of the element to get.

        Returns:
            PowerStateModel: The power state of the specified element.

        Raises:
            RequestNotSupportedHWControlError: The legacy plugin's response
                did not contain a power state.
            InternalHWControlError: The converted result did not contain
                exactly one entry, or did not contain a time.
            BaseHWControlError: Sent through unchanged from the legacy plugin.
            UnknownHWControlError: Any other exception from the legacy plugin.
        """
        device_type = self._get_device_type(element_id)
        key_values = [{"oob_device_id": element_id, "device_type": device_type}]
        data = _call_legacy_data(self._oob_plugin().get_power_state, _OOB_DATA_KEY, key_values=key_values)
        if len(data) != 1 or "time" not in data[0]:
            raise exc.InternalHWControlError
        if "powerState" not in data[0]:
            raise exc.RequestNotSupportedHWControlError
        return PowerStateModel(power_state=data[0]["powerState"], time=data[0]["time"])

    def get_metric(self, element_id: ElementID) -> MetricModel:
        """Get the metric information of the specified element via the legacy OOB plugin.

        Args:
            element_id (ElementID): ID of the element to get.

        Returns:
            MetricModel: The metric information of the specified element.

        Raises:
            InternalHWControlError: The converted result did not contain
                exactly one entry, or could not be converted to MetricModel.
            BaseHWControlError: Sent through unchanged from the legacy plugin.
            UnknownHWControlError: Any other exception from the legacy plugin.
        """
        device_type = self._get_device_type(element_id)
        key_values = [{"oob_device_id": element_id, "device_type": device_type}]
        data = _call_legacy_data(self._oob_plugin().get_metric_info, _OOB_DATA_KEY, key_values=key_values)
        if len(data) != 1:
            raise exc.InternalHWControlError
        try:
            # The legacy plugin reports the device type as "type", while
            # MetricModel selects its variant by "deviceType".
            return _metric_type_adapter.validate_python({**data[0], "deviceType": data[0]["type"]})
        except Exception as err:
            raise exc.InternalHWControlError from err

    def _post_and_build_time_stamp(self, method: Callable, element_id: str) -> TimeStampModel:
        """Call a legacy OOB post_* method and build a TimeStampModel from its response."""
        device_type = self._get_device_type(element_id)
        key_values = [{"oob_device_id": element_id, "device_type": device_type}]
        data = _call_legacy_data(method, _OOB_DATA_KEY, key_values=key_values)
        if len(data) != 1 or "time" not in data[0]:
            raise exc.InternalHWControlError
        return TimeStampModel(time=data[0]["time"])

    def power_on(self, element_id: ElementID) -> TimeStampModel:
        """Execute a power-on operation on the specified element via the legacy OOB plugin.

        Args:
            element_id (ElementID): ID of the element to operate on.

        Returns:
            TimeStampModel: The date and time the action was executed.

        Raises:
            InternalHWControlError: The converted result did not contain
                exactly one entry, or did not contain a time.
            BaseHWControlError: Sent through unchanged from the legacy plugin.
            UnknownHWControlError: Any other exception from the legacy plugin.
        """
        return self._post_and_build_time_stamp(self._oob_plugin().post_power_on, element_id)

    def power_off(self, element_id: ElementID) -> TimeStampModel:
        """Execute a power-off operation on the specified element via the legacy OOB plugin.

        Args:
            element_id (ElementID): ID of the element to operate on.

        Returns:
            TimeStampModel: The date and time the action was executed.

        Raises:
            InternalHWControlError: The converted result did not contain
                exactly one entry, or did not contain a time.
            BaseHWControlError: Sent through unchanged from the legacy plugin.
            UnknownHWControlError: Any other exception from the legacy plugin.
        """
        return self._post_and_build_time_stamp(self._oob_plugin().post_power_off, element_id)

    def os_shutdown(self, element_id: ElementID) -> TimeStampModel:
        """Execute an OS shutdown operation on the specified element via the legacy OOB plugin.

        Args:
            element_id (ElementID): ID of the element to operate on.

        Returns:
            TimeStampModel: The date and time the action was executed.

        Raises:
            InternalHWControlError: The converted result did not contain
                exactly one entry, or did not contain a time.
            BaseHWControlError: Sent through unchanged from the legacy plugin.
            UnknownHWControlError: Any other exception from the legacy plugin.
        """
        return self._post_and_build_time_stamp(self._oob_plugin().post_os_shutdown, element_id)

    def cpu_reset(self, element_id: ElementID) -> TimeStampModel:
        """Execute a CPU reset operation on the specified element via the legacy OOB plugin.

        Args:
            element_id (ElementID): ID of the element to operate on.

        Returns:
            TimeStampModel: The date and time the action was executed.

        Raises:
            InternalHWControlError: The converted result did not contain
                exactly one entry, or did not contain a time.
            BaseHWControlError: Sent through unchanged from the legacy plugin.
            UnknownHWControlError: Any other exception from the legacy plugin.
        """
        return self._post_and_build_time_stamp(self._oob_plugin().post_cpu_reset, element_id)

    def add_connection(self, uid: ElementID, did: ElementID) -> TimeStampModel:
        """Not supported by legacy OOB plugins.

        Raises:
            RequestNotSupportedHWControlError: Always raised.
        """
        raise exc.RequestNotSupportedHWControlError

    def remove_connection(self, uid: ElementID, did: ElementID) -> TimeStampModel:
        """Not supported by legacy OOB plugins.

        Raises:
            RequestNotSupportedHWControlError: Always raised.
        """
        raise exc.RequestNotSupportedHWControlError

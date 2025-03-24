# Copyright 2025 NEC Corporation
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

"""HW independent section - Get FM Information

Get device information for the specified device ID device type

"""
from typing import cast
import traceback
import app.common.messages.message as msg
import app.common.constants as const
from app.common.utils.log import LOGGER
from app.common.utils.plugin_manager import get_plugin
from app.common.utils.fm_plugin_base import FmPortData
from app.common.utils.fm_plugin_base import FMPluginBase
from app.common.basic_exceptions import InternalHwControlError
from app.common.deviceIdManager import device_id_base as dim

# INDEX where device information is stored in FMPlugin.get_port_info
PLUGIN_DEVICE_DATA_KEY = "data"


class GetSpecFMInfo:
    """Get FM Information

    class for get Device information from Fabric Manager.

    """

    def __init__(self):
        self.plugin = None
        self.manager_id = ""

    def _import_plugin(self, device_id: str) -> bool:
        """import Plugin

        Import the plugin corresponding to the device

        Args:
            device_id (str): DeviceID

        Returns:
            bool: True(Import Successful) or False(Import Failed)
        """
        LOGGER.debug(f"[_import_plugin] begin device_id={device_id}")
        # Import FMPlugin
        manager_ids = dim.device_id_to_manager_id(device_id)
        if not manager_ids[const.ManagerType.FM.value.lower()]:
            return False

        self.manager_id = manager_ids[const.ManagerType.FM.value.lower()]
        self.plugin = get_plugin(const.ManagerType.FM.value.lower(), self.manager_id)
        return True

    def _transport_fm_plugin_result_to_port_data(self, fm_port_data: FmPortData) -> dict:
        """Transport plugin result to port data

        Convert 'FmPortData' to port information

        Args:
            fm_port_data (FmPortData): FM Port Data

        Returns:
            dict: FmPortData
        """
        LOGGER.debug(f"[_transport_fm_plugin_result_to_port_data] begin fm_port_data={fm_port_data}")

        result = {}

        device_id = dim.fm_port_id_to_device_id(fm_port_data.id, self.manager_id)
        device_type = dim.device_id_to_device_type(str(device_id))
        result["deviceID"] = device_id
        result["type"] = device_type
        result["fmPortId"] = fm_port_data.id
        result["deviceSwitchInfo"] = dim.fm_switch_id_to_device_id(str(fm_port_data.switch_id), self.manager_id)
        result["switchId"] = fm_port_data.switch_id
        result["switchPortNumber"] = fm_port_data.switch_port_number
        result["switchPortType"] = fm_port_data.switch_port_type
        result["fabricId"] = fm_port_data.fabric_id
        if fm_port_data.link is not None and len(fm_port_data.link) > 0:
            link = []
            for link_fm_port_id in fm_port_data.link:
                device_id = dim.fm_port_id_to_device_id(link_fm_port_id, self.manager_id)
                device_type = dim.device_id_to_device_type(str(device_id))
                link_item = {}
                link_item["deviceID"] = device_id
                link_item["type"] = device_type
                link.append(link_item)
            result["link"] = link

        result["fmDeviceType"] = fm_port_data.device_type
        result["PCIClassCode"] = fm_port_data.pci_class_code
        result["PCIeVendorId"] = fm_port_data.pcie_vendor_id
        result["PCIeDeviceId"] = fm_port_data.pcie_device_id
        result["PCIeDeviceSerialNumber"] = fm_port_data.pcie_device_serial_number
        result["CPUManufacturer"] = fm_port_data.cpu_manufacturer
        result["CPUModel"] = fm_port_data.cpu_model
        result["CPUSerialNumber"] = fm_port_data.cpu_serial_number
        result["LTSSMState"] = fm_port_data.ltssm_state
        result["deviceKeys"] = fm_port_data.device_keys
        result["portKeys"] = fm_port_data.port_keys
        result["capacity"] = fm_port_data.capacity

        return result

    def _get_spec(self, device_id: str) -> list:
        """Get device information

        Get device information by specifying ID

        Args:
            device_id (str): DeviceID

        Returns:
            list: specs
        """
        LOGGER.debug(f"[_get_spec] begin device_id={device_id}")

        fm_port_id = dim.device_id_to_fm_port_id(device_id)

        # Call FMPlugin to get device information
        call_info = f"manager_id: {self.manager_id}, device_id: {device_id}, fm_port_id: {fm_port_id}"
        LOGGER.info(msg.get_log_message(msg.I00003, [call_info]))
        plugin_result = cast(FMPluginBase, self.plugin).get_port_info(fm_port_id)
        LOGGER.info(msg.get_log_message(msg.I00004, [call_info]))

        specs = []
        plugin_port_data = plugin_result[PLUGIN_DEVICE_DATA_KEY]
        fm_port_data = plugin_port_data[0]
        converted = self._transport_fm_plugin_result_to_port_data(fm_port_data)
        specs.append(converted)
        return specs

    def get_spec_fm(self, device_id: str, device_type: str) -> dict:
        """Get FM device information

        Get device information for the specified device ID and device type

        Args:
            device_id (str): DeviceID
            device_type (str): DeviceType

        Returns:
            dict: {"data": ListOfDeviceInfo}

        Examples:

            >>> get_fm_info = GetSpecFMInfo()
                spec_fm_info = get_fm_info.get_spec_fm("12345", "CPU")
        """
        try:
            LOGGER.debug(f"[get_spec_fm] begin device_id={device_id} device_type={device_type}")

            specs: list

            dummy_specs = [{"deviceID": device_id, "type": device_type}]

            if device_type == const.DeviceType.GC.value or device_type == const.DeviceType.VM.value:
                specs = dummy_specs

            elif not self._import_plugin(device_id):
                specs = dummy_specs

            elif device_type in [const_device_type.value for const_device_type in const.DeviceType]:
                specs = self._get_spec(device_id)

            else:
                LOGGER.warning(msg.get_log_message(msg.W00002, [device_type]))
                raise InternalHwControlError(additional_message=f"The device_type({device_type}) was abnormal.")

            result = {"data": specs}
            LOGGER.debug("[get_spec_fm] end")
            return result

        except Exception:
            LOGGER.warning(msg.get_log_message(msg.W00001, [traceback.format_exc()]))
            raise

        finally:
            if self.plugin:
                del self.plugin
            else:  # empty else for C1 coverage
                pass

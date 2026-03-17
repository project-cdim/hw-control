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

"""HW independent section - Get FM Information

Get device information for the specified Device ID Device Type

"""
import traceback
import logging
import app.common.messages.message as msg
import app.common.constants as const
from app.common.basic_exceptions import InternalHWControlError
from app.common.dim import device_id_base as dim
import app.common.plugin.svc.loader as plugin_loader
from app.common.utils.fm_plugin_base import FMPortData
from app.common.utils.fm_plugin_base import FMPluginBase
from app.core.info import info_const, info_utils

# INDEX where device information is stored in FMPlugin.get_port_info
PLUGIN_DEVICE_DATA_KEY = "data"

# Get a logger object.
logger = logging.getLogger(__name__)


class GetSpecFMInfo:  # pylint: disable=R0903
    """Get FM Information

    class for get Device information from Fabric Manager.

    """

    def _transport_fm_plugin_result_to_port_data(self, manager_id: str, fm_port_data: FMPortData) -> dict:
        """Transport Plugin result to port data

        Convert 'FMPortData' to port information

        Args:
            manager_id (str): Plugin manager ID
            fm_port_data (FMPortData): FM port data

        Returns:
            dict: FMPortData
        """
        logger.debug("[_transport_fm_plugin_result_to_port_data] begin fm_port_data=%s", fm_port_data)

        result: dict[str, object] = {}

        device_id = dim.fm_port_id_to_device_id(fm_port_data.id, manager_id)
        device_type = dim.device_id_to_device_type(str(device_id))
        result["deviceID"] = device_id
        result["type"] = device_type

        fm_port = {}
        fm_port["deviceSwitchInfo"] = dim.fm_switch_id_to_device_id(str(fm_port_data.switch_id), manager_id)
        fm_port["fabricId"] = fm_port_data.fabric_id
        fm_port["fmPortId"] = fm_port_data.id
        fm_port["LTSSMState"] = fm_port_data.ltssm_state
        fm_port["switchId"] = fm_port_data.switch_id
        fm_port["switchPortNumber"] = fm_port_data.switch_port_number
        fm_port["switchPortType"] = fm_port_data.switch_port_type
        result["devicePortList"] = [fm_port]

        if fm_port_data.link is not None and len(fm_port_data.link) > 0:
            link = []
            for link_fm_port_id in fm_port_data.link:
                device_id = dim.fm_port_id_to_device_id(link_fm_port_id, manager_id)
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
        result["deviceKeys"] = fm_port_data.device_keys
        result["portKeys"] = fm_port_data.port_keys
        result["capacity"] = fm_port_data.capacity

        return result

    def _get_spec(self, device_id: str, manager_id: str, plugin: FMPluginBase) -> list:
        """Get device information

        Get device information by specifying ID

        Args:
            device_id (str): Device ID
            manager_id (str): Plugin manager ID
            plugin (FMPluginBase): FM Plugin

        Returns:
            list: specs
        """
        logger.debug("[_get_spec] begin device_id=%s", device_id)

        specs = []
        for fm_port_id in dim.device_id_to_fm_port_id_multi_hostport(device_id, manager_id):
            # Call FMPlugin to get device information
            call_info = f"manager_id: {manager_id}, device_id: {device_id}, fm_port_id: {fm_port_id}"
            logger.info(msg.get_log_message(msg.I00003, [call_info]))
            plugin_result: dict[str, list[FMPortData]] = plugin.get_port_info(fm_port_id)
            logger.info(msg.get_log_message(msg.I00004, [call_info]))

            plugin_port_data = plugin_result[PLUGIN_DEVICE_DATA_KEY]
            fm_port_data = plugin_port_data[0]
            converted = self._transport_fm_plugin_result_to_port_data(manager_id, fm_port_data)
            specs.append(converted)

        return specs

    def get_spec_fm(self, device_id: str, device_type: str) -> dict:
        """Get FM device information

        Get device information for the specified Device ID and Device Type

        Args:
            device_id (str): Device ID
            device_type (str): Device Type

        Returns:
            dict: {"data": ListOfDeviceInfo}

        Examples:

            >>> get_fm_info = GetSpecFMInfo()
                spec_fm_info = get_fm_info.get_spec_fm("12345", "CPU")
        """
        try:
            logger.debug("[get_spec_fm] begin device_id=%s device_type=%s", device_id, device_type)

            if device_type not in [const_device_type.value for const_device_type in const.DeviceType]:
                logger.warning(msg.get_log_message(msg.W00002, [device_type]))
                raise InternalHWControlError(additional_message=f"The device_type({device_type}) was abnormal.")

            dummy_data = {PLUGIN_DEVICE_DATA_KEY: [{"deviceID": device_id, "type": device_type}]}

            if device_type in (const.DeviceType.GC.value, const.DeviceType.VM.value):
                logger.debug("[get_spec_fm] end. return dummy data.")
                return dummy_data

            # Get Plugin manager IDs
            manager_ids: dict[str, list[str]] = dim.device_id_to_manager_id_multi_hostport(device_id)
            if not manager_ids[const.ManagerType.FM.value.lower()]:
                logger.debug("[get_spec_fm] end. manager not found.")
                return dummy_data

            # Get device information
            specs = []
            for manager_id in manager_ids[const.ManagerType.FM.value.lower()]:
                specs.extend(self._get_spec(device_id, manager_id, plugin_loader.get_fm(manager_id)))

            # Get combination device information.
            target_id, target_type = info_utils.get_combination_match_device(device_id)
            if target_id and target_type:
                manager_ids = dim.device_id_to_manager_id_multi_hostport(target_id)
                if manager_ids[const.ManagerType.FM.value.lower()]:
                    for manager_id in manager_ids[const.ManagerType.FM.value.lower()]:
                        specs.extend(self._get_spec(target_id, manager_id, plugin_loader.get_fm(manager_id)))

            # Convert links devices.
            for device_info in specs:
                device_info = self._convert_links_device(device_info)

            if not specs:
                logger.debug("[get_spec_fm] end. no data.")
                return dummy_data

            logger.debug("[get_spec_fm] end")
            return {PLUGIN_DEVICE_DATA_KEY: specs}

        except Exception:
            logger.warning(msg.get_log_message(msg.W00001, [traceback.format_exc()]))
            raise

    def _convert_links_device(self, device_info: dict) -> dict:
        """Converts link information in a device info dictionary.

        This method processes the link information contained within the device_info dictionary,
        transforming link data as needed.
        - Resolving Device ID and Device Type combinations.
        - Handling special cases for CPU devices linked to fabric adapter.
        - Extending links with additional fabric device information when applicable.

        Args:
            device_info : dict
                A dictionary containing information about a device, including its links to other devices.

        Returns:
            dict:
                Device information after link data converted.
        """
        # Convert links.
        links = []
        for link in device_info.get(info_const.DATA_ITEM_FM_LINK, []):
            fm_link_id = link[info_const.DATA_ITEM_DEVICE_ID]
            fm_link_type = link[info_const.DATA_ITEM_TYPE]
            # Resolving Device ID and Device Type combinations.
            target_id, target_type = info_utils.get_combination_match_device(fm_link_id)
            if target_id and target_type == info_utils.get_high_priority_device_type(fm_link_type, target_type):
                links.append({info_const.DATA_ITEM_DEVICE_ID: target_id, info_const.DATA_ITEM_TYPE: target_type})
            else:
                links.append({info_const.DATA_ITEM_DEVICE_ID: fm_link_id, info_const.DATA_ITEM_TYPE: fm_link_type})

        if links:
            device_info[info_const.DATA_ITEM_FM_LINK] = links

        return device_info

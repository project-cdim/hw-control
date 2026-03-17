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

"""HW independent part - Get OOB information

Get device information for the specified Device ID and Device Type

"""


import traceback
import logging
import app.common.constants as const
import app.common.messages.message as msg
import app.common.plugin.svc.loader as plugin_loader
from app.common.basic_exceptions import InternalHWControlError
from app.common.dim import device_id_base as dim
from app.common.utils.oob_plugin_base import OOBPluginBase
from app.core.info import info_const, info_utils


logger = logging.getLogger(__name__)


class GetSpecOOBInfo:
    """OOB information acquisition process
    A class that acquires OOB information from various devices
    """

    def get_spec_oob(self, device_id: str, device_type: str) -> dict:
        """Get OOB device information

        Get OOB device information corresponding to the
        specified Device ID and Device Type

        Args:
            device_id (str): Device ID
            device_type (str): Device Type

        Returns:
            dict: OOB device information

        Examples:

            >>> get_oob_info = GetSpecOOBInfo()
                spec_oob_info = get_oob_info.get_spec_oob("12345", "cpu")
        """
        # Get source device.
        oob_info = self._get_oob_info(OOBPluginBase.get_spec_info.__name__, device_id, device_type)

        # Get target device.
        target_id, target_type = info_utils.get_combination_match_device(device_id)
        if target_id and target_type:
            target = self._get_oob_info(OOBPluginBase.get_spec_info.__name__, target_id, target_type)
            oob_info[info_const.OOB_DATA_ITEM].extend(target[info_const.OOB_DATA_ITEM])

        # Convert links devices.
        for device_info in oob_info[info_const.OOB_DATA_ITEM]:
            device_info = self._convert_links_device(device_info)

        return oob_info

    def get_metric_oob(self, device_id: str, device_type: str) -> dict:
        """Get OOB device metric information

        Get OOB device metric information corresponding to the
        specified Device ID and Device Type

        Args:
            device_id (str): Device ID
            device_type (str): Device Type

        Returns:
            dict: OOB device metric information

        Examples:

            >>> get_oob_info = GetSpecOOBInfo()
                metric_oob_info = get_oob_info.get_metric_oob("12345", "cpu")
        """
        # Get device information.
        oob_info = self._get_oob_info(OOBPluginBase.get_metric_info.__name__, device_id, device_type)

        # Get combination device information.
        target_id, target_type = info_utils.get_combination_match_device(device_id)
        if target_id and target_type:
            target = self._get_oob_info(OOBPluginBase.get_metric_info.__name__, target_id, target_type)
            oob_info[info_const.OOB_DATA_ITEM].extend(target[info_const.OOB_DATA_ITEM])

        return oob_info

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
        for link in device_info.get(info_const.DATA_ITEM_OOB_LINK, []):
            oob_link_id = link[info_const.DATA_ITEM_DEVICE_ID]
            oob_link_type = link[info_const.DATA_ITEM_TYPE]
            # Resolving Device ID and Device Type combinations.
            target_id, target_type = info_utils.get_combination_match_device(oob_link_id)
            if target_id and target_type == info_utils.get_high_priority_device_type(oob_link_type, target_type):
                links.append({info_const.DATA_ITEM_DEVICE_ID: target_id, info_const.DATA_ITEM_TYPE: target_type})
                # Handling special cases for CPU devices linked to fabric adapter.
                if (
                    device_info[info_const.DATA_ITEM_TYPE] == const.DeviceType.CPU.value
                    and target_type == const.DeviceType.SFA.value
                ):
                    # Extending links with additional fabric device information when applicable.
                    links.extend(self._get_fabric_device_links(target_id, target_type))
            else:
                links.append({info_const.DATA_ITEM_DEVICE_ID: oob_link_id, info_const.DATA_ITEM_TYPE: oob_link_type})

        if links:
            device_info[info_const.DATA_ITEM_OOB_LINK] = links

        return device_info

    def _get_fabric_device_links(self, device_id: str, device_type: str) -> list:
        """Get a list of device links for a specific device within the fabric.

        This method fetches out-of-band (OOB) information for a given device and filters
        to return only the links associated with VM (Virtual Machine) devices.

        Args:
            device_id (str): The unique identifier for the device.
            device_type (str): The type of the device (should match a known device type in the system).

        Returns:
            list: A list of link dictionaries for VM devices associated with the specified device.
                Each link dictionary contains details about the connection to the VM.
        """
        oob_info = self._get_oob_info(OOBPluginBase.get_spec_info.__name__, device_id, device_type)

        result_links = []
        for device_info in oob_info.get(info_const.OOB_DATA_ITEM, []):
            for links in device_info.get(info_const.DATA_ITEM_OOB_LINK, []):
                if links.get(info_const.DATA_ITEM_TYPE) == const.DeviceType.DFA.value:
                    result_links.append(links)
        return result_links

    def _get_oob_info(self, func_name: str, device_id: str, device_type: str) -> dict:
        """Get OOB Plugin response

        Get the information of the specified Device ID and Device Type

        Args:
            func_name (str): function name
            device_id (str): Device ID
            device_type (str): Device Type

        Returns:
            dict: OOB device information
        """

        try:
            logger.debug(
                "[get_oob_info] begin func_name=%s device_id=%s device_type=%s", func_name, device_id, device_type
            )

            # allowed type: CPU,memory,storage,networkInterface,GPU,graphicController
            if device_type not in [
                const.DeviceType.CPU.value,
                const.DeviceType.MEMORY.value,
                const.DeviceType.STORAGE.value,
                const.DeviceType.NIC.value,
                const.DeviceType.SFA.value,
                const.DeviceType.DFA.value,
                const.DeviceType.GPU.value,
                const.DeviceType.GC.value,
            ]:
                logger.warning(msg.get_log_message(msg.W00002, [device_type]))
                raise InternalHWControlError(additional_message=f"The device_type({device_type}) was abnormal.")

            manager_ids: dict[str, list[str]] = dim.device_id_to_manager_id_multi_hostport(device_id)
            if not manager_ids[const.ManagerType.OOB.value.lower()]:
                logger.debug("[get_oob_info] end. return dummy data.")
                return {info_const.OOB_DATA_ITEM: [{"deviceID": device_id, "type": device_type}]}

            specs = []
            for manager_id in manager_ids[const.ManagerType.OOB.value.lower()]:
                # Plugin's parameter
                oob_device_id = dim.device_id_to_oob_device_id(device_id)
                call_info = f"{manager_id} {func_name} device_id: {device_id} oob_device_id: {oob_device_id}"
                logger.info(msg.get_log_message(msg.I00003, [call_info]))

                # no attr name check because of _get_oob_info is private
                param_key_value = [{"oob_device_id": oob_device_id, "device_type": device_type}]
                oob_info: dict[str, list[dict]] = getattr(plugin_loader.get_oob(manager_id), func_name)(param_key_value)
                logger.info(msg.get_log_message(msg.I00004, [call_info]))

                if not oob_info or info_const.OOB_DATA_ITEM not in oob_info:
                    continue

                # Set the number of processor sockets (socketNum) to the default value.
                if device_type == const.DeviceType.CPU.value and func_name == OOBPluginBase.get_spec_info.__name__:
                    self._oob_info_add_cpu_socket_num(oob_info)

                specs.extend(self._oob_info_change_device_id(manager_id, oob_info))

            if not specs:
                logger.warning(msg.get_log_message(msg.W00005, []))
                raise InternalHWControlError(additional_message="The Plugin response was none.")

            logger.debug("[get_oob_info] end")
            return {info_const.OOB_DATA_ITEM: specs}

        except Exception:
            logger.warning(msg.get_log_message(msg.W00001, [traceback.format_exc()]))
            raise

    def _oob_info_change_device_id(self, manager_id: str, oob_info: dict[str, list[dict]]) -> list:
        """change Device ID in oob_info

        Convert the OOB Device ID in the oob information into Device ID

        Args:
            manager_id (str): Plugin Manager ID
            oob_info (dict): OOB information

        Returns:
            list: OOB information
        """
        logger.debug("[_oob_info_change_device_id] begin oob_info=%s", oob_info)
        devices = oob_info[info_const.OOB_DATA_ITEM]
        ret_devices = []
        for device in devices:
            ret_device = self._change_to_device_id(manager_id, device)
            if "schema" in ret_device and "link" in ret_device:
                links = ret_device["link"]
                ret_links = []
                for link in links:
                    ret_link = self._change_to_device_id(manager_id, link)
                    ret_links.append(ret_link)

                ret_device["link"] = ret_links

            ret_devices.append(ret_device)

        return ret_devices

    def _change_to_device_id(self, manager_id: str, info: dict) -> dict:
        """change deviceID in dict

        Convert the OOB Device ID in the OOB information into Device ID

        Args:
            manager_id (str): Plugin Manager ID
            info (dict): OOB information

        Returns:
            dict: OOB information
        """
        logger.debug("[_change_to_device_id] begin info=%s", info)
        if "deviceID" not in info:
            return info

        info["deviceID"] = dim.oob_device_id_to_device_id(info["deviceID"], str(manager_id))
        info["type"] = dim.device_id_to_device_type(str(info["deviceID"]))
        return info

    def _oob_info_add_cpu_socket_num(self, oob_info: dict[str, list[dict]]) -> None:
        """CPU socketNum add in oob_info

        ADD CPU socketNum property  in the OOB information into processor

        Args:
            oob_info (dict): OOB information

        Returns:
            list: OOB information
        """
        logger.debug("[_oob_info_add_CPU_socketNum] begin oob_info=%s", oob_info)
        socket_num: int = 1

        for device in oob_info[info_const.OOB_DATA_ITEM]:
            # Add socketNum to each device's schema
            device["schema"]["socketNum"] = socket_num

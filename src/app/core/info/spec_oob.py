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

"""HW independent part - Get OOB information

Get device information for the specified Device ID and Device Type

"""


import traceback
import logging
import app.common.messages.message as msg
import app.common.constants as const
from app.common.utils.plugin_manager import get_oob_plugin
from app.common.basic_exceptions import InternalHWControlError
from app.common.utils.oob_plugin_base import OOBPluginBase
from app.common.dim import device_id_base as dim

# INDEX where device information is stored in OOBPlugin.get_spec_info
PLUGIN_DEVICE_DATA_KEY = "devices"

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
        return self._get_oob_info(OOBPluginBase.get_spec_info.__name__, device_id, device_type)

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
        return self._get_oob_info(OOBPluginBase.get_metric_info.__name__, device_id, device_type)

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
                const.DeviceType.GPU.value,
                const.DeviceType.GC.value,
            ]:
                logger.warning(msg.get_log_message(msg.W00002, [device_type]))
                raise InternalHWControlError(additional_message=f"The device_type({device_type}) was abnormal.")

            manager_ids: dict[str, list[str]] = dim.device_id_to_manager_id_multi_hostport(device_id)
            if not manager_ids[const.ManagerType.OOB.value.lower()]:
                logger.debug("[get_oob_info] end. return dummy data.")
                return {PLUGIN_DEVICE_DATA_KEY: [{"deviceID": device_id, "type": device_type}]}

            specs = []
            for manager_id in manager_ids[const.ManagerType.OOB.value.lower()]:
                # Plugin's parameter
                oob_device_id = dim.device_id_to_oob_device_id(device_id)
                call_info = f"{manager_id} {func_name} device_id: {device_id} oob_device_id: {oob_device_id}"
                logger.info(msg.get_log_message(msg.I00003, [call_info]))

                # no attr name check because of _get_oob_info is private
                param_key_value = [{"oob_device_id": oob_device_id, "device_type": device_type}]
                oob_info: dict[str, list[dict]] = getattr(get_oob_plugin(manager_id), func_name)(param_key_value)
                logger.info(msg.get_log_message(msg.I00004, [call_info]))

                if not oob_info or PLUGIN_DEVICE_DATA_KEY not in oob_info:
                    continue

                specs.extend(self._oob_info_change_device_id(manager_id, oob_info))

            if not specs:
                logger.warning(msg.get_log_message(msg.W00005, []))
                raise InternalHWControlError(additional_message="The Plugin response was none.")

            logger.debug("[get_oob_info] end")
            return {PLUGIN_DEVICE_DATA_KEY: specs}

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
        devices = oob_info["devices"]
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

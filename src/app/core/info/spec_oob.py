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

Get device information for the specified device ID and device type

"""


import traceback
from app.common.utils.log import LOGGER
import app.common.messages.message as msg
import app.common.constants as const
from app.common.utils.plugin_manager import get_plugin
from app.common.basic_exceptions import InternalHwControlError
from app.common.utils.oob_plugin_base import OOBPluginBase as oob_plugin
from app.common.deviceIdManager import device_id_base as dim


class GetSpecOOBInfo:
    """OOB information acquisition process
    A class that acquires OOB information from various devices
    """

    def __init__(self) -> None:
        """constructor
        Constructor for OOB information acquisition processing
        """
        self.param_key_value = None
        self.plugin = None
        self.manager_id = None

    def get_spec_oob(self, device_id: str, device_type: str) -> dict:
        """Get OOB device information

        Get OOB device information corresponding to the
        specified device ID and device type

        Args:
            device_id (str): device ID
            device_type (str): device type

        Returns:
            dict: OOB device information

        Examples:

            >>> get_oob_info = GetSpecOOBInfo()
                spec_oob_info = get_oob_info.get_spec_oob("12345", "cpu")
        """
        return self._get_oob_info(oob_plugin.get_spec_info.__name__, device_id, device_type)

    def get_metric_oob(self, device_id: str, device_type: str) -> dict:
        """Get OOB device metric information

        Get OOB device metric information corresponding to the
        specified device ID and device type

        Args:
            device_id (str): device ID
            device_type (str): device type

        Returns:
            dict: OOB device metric information

        Examples:

            >>> get_oob_info = GetSpecOOBInfo()
                metric_oob_info = get_oob_info.get_metric_oob("12345", "cpu")
        """
        return self._get_oob_info(oob_plugin.get_metric_info.__name__, device_id, device_type)

    def _get_oob_info(self, func_name: str, device_id: str, device_type: str) -> dict:
        """Get OOB plugin response

        Get the information of the specified device_id and device_type

        Args:
            func_name (str): FunctionName
            device_id (str): DeviceID
            device_type (str): DeviceType

        Returns:
            dict: OOB device information
        """

        try:
            LOGGER.debug(f"[get_oob_info] begin func_name={func_name} device_id={device_id} device_type={device_type}")

            # allowed type: CPU,memory,storage,networkInterface,GPU,graphicController
            if device_type not in [
                const.DeviceType.CPU.value,
                const.DeviceType.MEMORY.value,
                const.DeviceType.STORAGE.value,
                const.DeviceType.NIC.value,
                const.DeviceType.GPU.value,
                const.DeviceType.GC.value,
            ]:
                LOGGER.warning(msg.get_log_message(msg.W00002, [device_type]))
                raise InternalHwControlError(additional_message=f"The device_type({device_type}) was abnormal.")

            # get plugin
            if not self._import_plugin(device_id):
                dummy_data = {"devices": [{"deviceID": device_id, "type": device_type}]}
                return dummy_data

            # Plugin's parameter
            oob_device_id = dim.device_id_to_oob_device_id(device_id)
            self.param_key_value = [{"oob_device_id": oob_device_id, "device_type": device_type}]

            call_info = f"{self.manager_id} {func_name} device_id: {device_id} oob_device_id: {oob_device_id}"
            LOGGER.info(msg.get_log_message(msg.I00003, [call_info]))

            # no attr name check because of _get_oob_info is private
            oob_info = getattr(self.plugin, func_name)(self.param_key_value)
            LOGGER.info(msg.get_log_message(msg.I00004, [call_info]))

            if oob_info and "devices" in oob_info:
                result = self._oob_info_change_device_id(oob_info)
                return result

            LOGGER.warning(msg.get_log_message(msg.W00005, []))
            raise InternalHwControlError(additional_message="The plugin response was none.")

        except Exception:
            LOGGER.warning(msg.get_log_message(msg.W00001, [traceback.format_exc()]))
            raise

        finally:
            if self.plugin:
                del self.plugin
            else:  # empty else for C1 coverage
                pass

    def _import_plugin(self, device_id: str) -> bool:
        """Plugin import process

        Import the Plugin corresponding to the device

        Args:
            device_id (str): DeviceID

        Returns:
            bool: True(Import Successful) or False(Import Failed)
        """
        LOGGER.debug(f"[_import_plugin] begin device_id={device_id}")

        # Import FMPlugin
        manager_ids = dim.device_id_to_manager_id(device_id)
        if not manager_ids[const.ManagerType.OOB.value.lower()]:
            return False

        self.manager_id = manager_ids[const.ManagerType.OOB.value.lower()]
        self.plugin = get_plugin(const.ManagerType.OOB.value.lower(), self.manager_id)
        return True

    def _oob_info_change_device_id(self, oob_info: dict) -> dict:
        """change deviceID in oob_info

        Convert the oob-deviceID in the oob information into deviceID

        Args:
            oob_info (dict): oob information

        Returns:
            dict: oob information
        """
        LOGGER.debug(f"[_oob_info_change_device_id] begin oob_info={oob_info}")
        devices = oob_info["devices"]
        ret_devices = []
        for device in devices:
            ret_device = self._change_to_device_id(device)
            if "schema" in ret_device and "link" in ret_device:
                links = ret_device["link"]
                ret_links = []
                for link in links:
                    ret_link = self._change_to_device_id(link)
                    ret_links.append(ret_link)

                ret_device["link"] = ret_links

            ret_devices.append(ret_device)

        ret_oob_info = {}
        ret_oob_info["devices"] = ret_devices
        return ret_oob_info

    def _change_to_device_id(self, info: dict) -> dict:
        """change deviceID in dict

        Convert the oob-deviceID in the oob information into deviceID

        Args:
            oob_info (dict): oob information

        Returns:
            dict: oob information
        """
        LOGGER.debug(f"[_change_to_device_id] begin info={info}")
        if "deviceID" not in info:
            return info

        info["deviceID"] = dim.oob_device_id_to_device_id(info["deviceID"], str(self.manager_id))
        info["type"] = dim.device_id_to_device_type(str(info["deviceID"]))
        return info

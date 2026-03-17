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

"""HW independent section - Get Information process (Response generation)

Upon receiving a request from the information acquisition API,
make an information acquisition request for the specified Device ID to FM and OOB.
Merge the device information returned from FM and OOB for each device
type and return it to the information acquisition API.

"""

import logging
import json
import datetime
from typing import Any, Annotated
from collections.abc import Callable
from pydantic import BaseModel, Field
from app.common.messages import message
from app.common.basic_exceptions import BaseHWControlError, InternalHWControlError
import app.common.constants as const
from app.common.dim import device_id_base as dim
from app.common.settings import settings
from app.common.utils import error_utils
from app.core.info import info_utils, info_const
from app.core.info.metric_agent import InfoMetricAgent
from app.core.info.spec_fm import GetSpecFMInfo
from app.core.info.spec_oob import GetSpecOOBInfo

logger = logging.getLogger(__name__)


class Device(BaseModel):
    """Device information

    Device information data class

    """

    device_id: Annotated[str, Field(alias="deviceID")] = ""
    type: str = ""


class DeviceList(BaseModel):
    """Device list information

    Device list information data class

    """

    device_list: Annotated[list[Device], Field(alias="deviceList")] = []
    info_timestamp: Annotated[str, Field(alias="infoTimestamp")] = ""


class InformationCore:
    """Information Core

    Get information from various devices

    """

    def get_spec_info(self, device_id: str) -> tuple[Any, list]:
        """Get device information

        Get device information for the specified Device ID

        Args:
            device_id (str): Device ID

        Returns:
            tuple[Any, list]: device information, error information

        Examples:
            Get device information by specifying Device ID

            >>> get_info = GetInformation()
                device_info = get_info.get_spec_info("0001")

        """

        response_data = None
        oob_data = None
        fm_data = None
        device_type = None
        errors = []

        try:
            # Get the Device Type from Device ID management.
            device_type = dim.device_id_to_device_type(device_id)
            if device_type is None:
                logger.warning(
                    message.get_log_message(
                        message.W00006, [f"Unable to retrieve the Device Type corresponding to Device ID: {device_id}."]
                    )
                )
                raise InternalHWControlError(
                    additional_message=f"Unable to retrieve the Device Type corresponding to Device ID: {device_id}."
                )
        except BaseHWControlError as bex:
            errors.append(bex.to_error_dict())

        if device_type is not None:
            try:
                # Get FM device information.
                get_spec_fm_info = GetSpecFMInfo()
                fm_data = get_spec_fm_info.get_spec_fm(device_id, device_type)
            except BaseHWControlError as bex:
                errors.append(bex.to_error_dict())

            try:
                # Get OOB device information.
                get_spec_oob_info = GetSpecOOBInfo()
                oob_data = get_spec_oob_info.get_spec_oob(device_id, device_type)
            except BaseHWControlError as bex:
                errors.append(bex.to_error_dict())

            try:
                # Generate response data.
                response_data = self._create_spec_info(device_id, device_type, fm_data, oob_data)
            except BaseHWControlError as bex:
                errors.append(bex.to_error_dict())

            if response_data is not None:
                # Set current datetime and assign it to the return data structure.
                response_data[info_const.RESP_ITEM_NAME_INFO_TIMESTAMP] = datetime.datetime.now(datetime.UTC).strftime(
                    const.TIME_STAMP_FORMAT
                )

        # Return response data.
        return response_data, error_utils.remove_duplicates(errors)

    def get_metric_info(self, device_id: str) -> tuple[Any, list]:
        """Get metric information

        Get metric information for the specified Device ID

        Args:
            device_id (str): Device ID

        Returns:
            tuple[Any, list]: metric information, error information

        Examples:
            Get metric information by specifying Device ID

            >>> get_info = GetInformation()
                metric_info = get_info.get_metric_info("0001")

        """
        response_data = None
        agent_data = None
        oob_data = None
        fm_data = None
        device_type = None
        errors = []

        try:
            # Retrieve Device Type from Device ID management.
            device_type = dim.device_id_to_device_type(device_id)
            if device_type is None:
                logger.warning(
                    message.get_log_message(
                        message.W00006, [f"Unable to retrieve the Device Type corresponding to Device ID: {device_id}."]
                    )
                )
                raise InternalHWControlError(
                    additional_message=f"Unable to retrieve the Device Type corresponding to Device ID: {device_id}."
                )
        except BaseHWControlError as bex:
            errors.append(bex.to_error_dict())

        if device_type not in (
            const.DeviceType.CPU.value,
            const.DeviceType.STORAGE.value,
            const.DeviceType.NIC.value,
            const.DeviceType.SFA.value,
            const.DeviceType.DFA.value,
            const.DeviceType.MEMORY.value,
            const.DeviceType.GPU.value,
        ):
            return response_data, errors

        # Function to handle errors for data fetching
        def fetch_data(fetch_func: Callable) -> Any:
            """Fetch data

            Fetches data using the provided fetch function and handles any BaseHWControlError exceptions.

            Args:
                fetch_func (Callable): A lambda or function that performs the data fetch operation.

            Returns:
                Any: The data fetched by the fetch_func, or None if an error occurred.
            """
            try:
                return fetch_func()
            except BaseHWControlError as bex:
                errors.append(bex.to_error_dict())
                return None

        # Get OOB metric information.
        get_spec_oob_info = GetSpecOOBInfo()
        oob_data = fetch_data(lambda: get_spec_oob_info.get_metric_oob(device_id, device_type))

        # Obtain FM device information. (FM retrieves metric information from device information)
        get_spec_fm_info = GetSpecFMInfo()
        fm_data = fetch_data(lambda: get_spec_fm_info.get_spec_fm(device_id, device_type))

        if settings.HW_CONTROL_AGENT_ENABLED and device_type not in (
            const.DeviceType.GPU.value,
            const.DeviceType.SFA.value,
            const.DeviceType.DFA.value,
        ):
            try:
                # Check agent connectivity.
                is_agent_access, cpu_device_id = self._verify_agent_access(device_id, device_type, oob_data, fm_data)
                if is_agent_access:
                    # Retrieve agent metric information.
                    get_metric_agent_info = InfoMetricAgent()
                    agent_data = get_metric_agent_info.get_metric_agent(device_id, device_type, cpu_device_id)
            except BaseHWControlError as bex:
                errors.append(bex.to_error_dict())

        # Generate response data.
        response_data = fetch_data(
            lambda: self._create_metric_info(device_id, device_type, agent_data, oob_data, fm_data)
        )

        if response_data:
            # Retrieve current datetime and assign it to the return data structure.
            response_data[info_const.RESP_ITEM_NAME_INFO_TIMESTAMP] = datetime.datetime.now(datetime.UTC).strftime(
                const.TIME_STAMP_FORMAT
            )

        # Return response data.
        return response_data, error_utils.remove_duplicates(errors)

    def _create_spec_info(
        self, device_id: str, device_type: str | Any, fm_data: dict | None, oob_data: dict | None
    ) -> dict:
        """Generate device information

        Generate device information to return

        Args:
            device_id (str): Device ID
            device_type (str | Any): Device Type
            fm_data (dict | None): FM data
            oob_data (dict | None): OOB data

        Returns:
            dict: device information

        """
        resp: dict[str, Any] = info_const.RESP_INIT.copy()
        resp[info_const.RESP_ITEM_NAME_DEVICE_ID] = device_id
        resp[info_const.RESP_ITEM_NAME_TYPE] = device_type

        if device_type is None:
            return resp

        def _merge_resp(source_type: str, data: dict) -> dict:
            """
            Merges response data for a given source type and data item using a mapping table.

            Args:
                source_type (str): The type of the data source.
                data (dict): The data dictionary containing the response data.

            Returns:
                dict: The merged response dictionary created from the mapping table and data item.
                      Returns an empty dictionary if data or mapping is None, or if an exception occurs.

            Raises:
                BaseHWControlError: If an error occurs during response creation from the mapping.
            """
            mapping = info_utils.get_mapping_table(device_type, source_type, info_const.DATA_TYPE_SPEC)
            if mapping is not None:
                try:
                    resp = info_utils.create_resp_from_mapping(mapping, data)
                    # Remove items with missing values from the response.
                    return info_utils.remove_empty_item(resp)
                except BaseHWControlError as bex:
                    logger.warning(
                        "Device ID:%s, %s data:%r, Error Code:%s, Error Message:%s, Exception:%r",
                        device_id,
                        source_type,
                        data,
                        bex.error_code,
                        bex.message,
                        bex,
                    )
                    raise
            return {}

        resp_oob, resp_fm = None, None

        # OOB
        if oob_data is not None:
            resp_oob = _merge_resp(
                info_const.DATA_SOURCE_TYPE_OOB, self._merge_device_info(oob_data[info_const.OOB_DATA_ITEM])
            )
            if resp_oob is not None:
                resp.update(resp_oob)

        # FM
        if fm_data is not None:
            resp_fm = _merge_resp(
                info_const.DATA_SOURCE_TYPE_FM, self._merge_device_info(fm_data[info_const.FM_DATA_ITEM])
            )
            if resp_fm is not None:
                resp.update(resp_fm)

        merged_link = self._merge_spec_link_data(resp_oob, resp_fm)
        # Set link data.
        if merged_link:
            resp[info_const.RESP_ITEM_NAME_LINK] = merged_link

        # Set constraints property.
        constraints = self._create_constraints(device_id, device_type, merged_link)
        if constraints and constraints[info_const.RESP_ITEM_NAME_CONSTRAINTS]:
            resp[info_const.RESP_ITEM_NAME_CONSTRAINTS] = constraints[info_const.RESP_ITEM_NAME_CONSTRAINTS]

        # Set model property according to the Device Type.
        self._set_model_property(resp)

        return resp

    def _merge_device_info(self, device_info_list: list) -> dict:
        """Merge device information

        Merge a list of device information dictionaries into a single dictionary.

        Args:
            device_info_list (list):
                A list of dictionaries containing device information to be merged.

        Returns:
            dict: Device information after merge.

        Notes:
            If the input list is empty, an empty dictionary is returned.
        """
        result = None

        for item in device_info_list:
            if result is None:
                # Set as a merge source.
                result = item
                continue

            device_id = result.get(info_const.RESP_ITEM_NAME_DEVICE_ID)
            device_type = result.get(info_const.RESP_ITEM_NAME_TYPE)
            target_id = item.get(info_const.RESP_ITEM_NAME_DEVICE_ID)
            target_type = item.get(info_const.RESP_ITEM_NAME_TYPE)

            if (device_id != target_id) and (device_type == target_type):
                msg1 = "The target device cannot merged. "
                msg2 = f"Device ID 1: {device_id},{device_type}, Device ID 2: {target_id},{target_type}."
                logger.warning(message.get_log_message(message.W00001, [msg1 + msg2]))
                raise InternalHWControlError(additional_message=msg1 + msg2)

            info_utils.merge_dict(
                result,
                item,
                info_utils.get_merge_type(result[info_const.RESP_ITEM_NAME_TYPE], item[info_const.RESP_ITEM_NAME_TYPE]),
            )

        return result if result is not None else {}

    def _merge_spec_link_data(self, resp_oob: dict | None, resp_fm: dict | None) -> list[Any]:
        """Merge spec link data

        Merge spec link data.

        Args:
            resp_oob (dict | None): OOB response data
            resp_fm (dict | None): FM response data

        Returns:
            list[Any]: link data
        """
        merged_link: list[Any] = []

        # Both have link information.
        if (resp_oob is not None and resp_oob.get(info_const.RESP_ITEM_NAME_LINK, None) is not None) and (
            resp_fm is not None and resp_fm.get(info_const.RESP_ITEM_NAME_LINK, None) is not None
        ):
            # Concatenate both links.
            merged_link = resp_oob[info_const.RESP_ITEM_NAME_LINK] + resp_fm[info_const.RESP_ITEM_NAME_LINK]
            # Resolve duplicate data, convert dict to JSON, convert to set, and convert back to dict.
            merged_link = [json.loads(s) for s in set(map(json.dumps, merged_link))]
        # Only FM has link information.
        elif resp_fm is not None and resp_fm.get(info_const.RESP_ITEM_NAME_LINK, None) is not None:
            merged_link = resp_fm[info_const.RESP_ITEM_NAME_LINK]
        # Only OOB has link information.
        elif resp_oob is not None and resp_oob.get(info_const.RESP_ITEM_NAME_LINK, None) is not None:
            merged_link = resp_oob[info_const.RESP_ITEM_NAME_LINK]

        return merged_link

    def _set_model_property(self, resp: dict) -> None:
        """Set model property

        Set model property according to the Device Type.

        Args:
            resp (dict): response data
        """
        device_type = None
        if isinstance(resp, dict):
            device_type = resp.get(info_const.RESP_ITEM_NAME_TYPE, None)

        if device_type is None:
            return

        model = None
        if device_type == const.DeviceType.STORAGE.value:
            val = info_utils.get_valid_string(resp.get(info_const.RESP_ITEM_NAME_DRIVE_MODEL, None))
            if val is not None:
                model = val
        elif device_type in (const.DeviceType.NIC.value, const.DeviceType.SFA.value, const.DeviceType.DFA.value):
            val = info_utils.get_valid_string(resp.get(info_const.RESP_ITEM_NAME_NETWORK_ADAPTER_MODEL, None))
            if val is not None:
                model = val
            else:
                val = info_utils.get_valid_string(resp.get(info_const.RESP_ITEM_NAME_FABRIC_ADAPTER_MODEL, None))
                if val is not None:
                    model = val
        if model is not None:
            resp[info_const.RESP_ITEM_NAME_MODEL] = model

    def _create_metric_info(  # pylint: disable=R0913,R0917
        self,
        device_id: str,
        device_type: str | Any,
        agent_data: dict | None,
        oob_data: dict | None,
        fm_data: dict | None,
    ) -> dict:
        """Generate metric information

        Generate metric information to return

        Args:
            device_id (str): Device ID
            device_type (str | Any): Device Type
            agent_data (dict | None): Agent data
            oob_data (dict | None): OOB data
            fm_data (dict | None): FM data

        Returns:
            dict: metric information

        """
        resp = info_const.RESP_INIT.copy()
        resp[info_const.RESP_ITEM_NAME_DEVICE_ID] = device_id
        resp[info_const.RESP_ITEM_NAME_TYPE] = device_type

        if device_type is None:
            return resp

        def _merge_resp(source_type: str, data: dict, data_item: str) -> dict:
            """
            Merges response data for a given source type and data item using a mapping table.

            Args:
                source_type (str): The type of the data source.
                data (dict): The data dictionary containing the response data.
                data_item (str): The key for the specific data item to process within the data dictionary.

            Returns:
                dict: The merged response dictionary created from the mapping table and data item.
                      Returns an empty dictionary if data or mapping is None, or if an exception occurs.

            Raises:
                BaseHWControlError: If an error occurs during response creation from the mapping.
            """
            mapping = info_utils.get_mapping_table(device_type, source_type, info_const.DATA_TYPE_METRIC)
            if mapping is not None:
                try:
                    resp = info_utils.create_resp_from_mapping(mapping, data[data_item][0])
                    # Remove items with missing values from the response.
                    return info_utils.remove_empty_item(resp)
                except BaseHWControlError as bex:
                    logger.warning(
                        "Device ID:%s, %s data:%r, Error Code:%s, Error Message:%s, Exception:%r",
                        device_id,
                        source_type,
                        data,
                        bex.error_code,
                        bex.message,
                        bex,
                    )
                    raise
            return {}

        # Agent
        if agent_data is not None:
            resp_agent = _merge_resp(info_const.DATA_SOURCE_TYPE_AGENT, agent_data, info_const.AGENT_DATA_ITEM)
            if resp_agent is not None:
                resp.update(resp_agent)

        # OOB
        if oob_data is not None:
            resp_oob = _merge_resp(info_const.DATA_SOURCE_TYPE_OOB, oob_data, info_const.OOB_DATA_ITEM)
            if resp_oob is not None:
                resp.update(resp_oob)

        # FM
        if fm_data is not None:
            resp_fm = _merge_resp(info_const.DATA_SOURCE_TYPE_FM, fm_data, info_const.FM_DATA_ITEM)
            if resp_fm is not None:
                resp.update(resp_fm)

        return resp

    def _create_constraints(self, device_id: str, device_type: str, links: list) -> dict:
        """Create constraints

        Generates constraints based on information obtained from OOB and FM and returns them.

        Args:
            device_id (str): base Device ID
            device_type (str): base Device Type
            links (list): device connection information

        Returns:
            dict: constraints
        """

        constraints: dict = {info_const.RESP_ITEM_NAME_CONSTRAINTS: {}}

        # Determine whether the base device is an internal device.
        is_built_in_device: bool = dim.device_id_to_fm_valid(device_id) is False

        # Determine whether the device cannot be disconnected.
        non_removable_devices: list = []
        for link_device in links:
            link_device_id = link_device.get(info_const.RESP_ITEM_NAME_DEVICE_ID)
            link_device_type = link_device.get(info_const.RESP_ITEM_NAME_TYPE)
            if (
                # If no information has been obtained from the FM,
                not dim.device_id_to_fm_valid(link_device_id)  # pylint: disable=R0916
                # or if the base device is an internal device and linking Device Type is "CPU",
                or (is_built_in_device and link_device_type == const.DeviceType.CPU.value)
                # or if the base Device Type is "CPU" and linking Device Type is "sourceFabricAdapter",
                or (device_type == const.DeviceType.CPU.value and link_device_type == const.DeviceType.SFA.value)
                # or if the base Device Type is "sourceFabricAdapter" and linking Device Type is "CPU",
                or (device_type == const.DeviceType.SFA.value and link_device_type == const.DeviceType.CPU.value)
            ):
                # it is determined that disconnection is not possible.
                non_removable_devices.append({info_const.RESP_ITEM_NAME_DEVICE_ID: link_device_id})
        # Add a list of non-dis-connectable devices to the constraints.
        if len(non_removable_devices) > 0:
            constraints[info_const.RESP_ITEM_NAME_CONSTRAINTS][
                info_const.RESP_ITEM_NAME_NON_REMOVABLE_DEVICES
            ] = non_removable_devices

        return constraints

    def get_device_list(self, device_type: str | None) -> dict:
        """Get device list

        Get a list of devices that correspond to the specified Device Type.
        If no Device Type is specified, get a list of all devices.

        Args:
            device_type (str | None): Device Type

        Returns:
            dict: device list

        Examples:
            Get device list by specifying Device Type

            >>> get_info = GetInformation()
                device_list = get_info.get_device_list("CPU")

        """
        # Create a data structure for returning (for device list).
        resp_device_list = DeviceList()

        # For generating device attribute information (stub).
        dev_list_all = []
        # Loop for the number of Device IDs.
        for dev_id in dim.get_controllable_device_id_list():
            # Get Device Type from Device ID management.
            dev_type = dim.device_id_to_device_type(dev_id)
            if not dev_type:
                # Do not return unknown device.
                continue

            _, target_type = info_utils.get_combination_match_device(dev_id)
            if info_utils.get_high_priority_device_type(dev_type, target_type) != dev_type:
                # Do not return low-priority devices.
                continue

            # Add to device list for generating device attribute information (stub).
            dev_list_all.append(
                {
                    info_const.DEVICE_LIST_ITEM_NAME_DEVICE_ID: dev_id,
                    info_const.DEVICE_LIST_ITEM_NAME_DEVICE_TYPE: dev_type,
                }
            )
            # If a Device Type is specified as an argument, does it match?
            if device_type is None or (device_type is not None and dev_type == device_type):
                # Pair the Device ID and the Device Type and add to the array.
                device = Device()
                device.device_id = dev_id
                device.type = dev_type
                resp_device_list.device_list.append(device)

        # Get the current date and time and set it to the data structure for returning.
        resp_device_list.info_timestamp = datetime.datetime.now(datetime.UTC).strftime(const.TIME_STAMP_FORMAT)

        # Generate device list information from the data structure for returning.
        resp_data = resp_device_list.model_dump(by_alias=True)

        # If Device ID information does not exist, delete the item itself.
        if not resp_device_list.device_list:
            resp_data.pop(info_const.DEVICE_LIST_ITEM_NAME_DEVICE_LIST, None)

        # Generate device attribute information (stub).
        if dev_list_all:
            # Generate device attribute information (Agent connection stub information).
            get_metric_agent_info = InfoMetricAgent()
            get_metric_agent_info.create_device_attribute(dev_list_all)

        return resp_data

    def _verify_agent_access(
        self, device_id: str, device_type: str, oob_data: dict | Any, fm_data: dict | Any
    ) -> tuple[bool, Any]:
        """Verify agent access

        Verify agent can be accessed

        Args:
            device_id (str): Device ID
            device_type (str): Device Type
            oob_data (dict | Any): OOB metric data
            fm_data (dict | Any): FM device data

        Returns:
            tuple[bool, Any]: True(connectable) or False(Unable connect), CPU Device ID

        """

        rtn_is_access = False
        rtn_cpu_device_id = None
        log_param = f"device_id: {device_id}, device_type: {device_type}, "

        # Argument check.
        invalid_values = [
            name
            for name, value in [
                ("device_id", device_id),
                ("device_type", device_type),
                ("oob_data", oob_data),
                ("fm_data", fm_data),
            ]
            if not value
        ]
        if invalid_values:
            logger.info(
                message.get_log_message(
                    message.I00007, [log_param, f"Invalid input values: {', '.join(invalid_values)}."]
                )
            )
            return rtn_is_access, rtn_cpu_device_id

        if device_type not in (
            const.DeviceType.CPU.value,
            const.DeviceType.STORAGE.value,
            const.DeviceType.NIC.value,
            const.DeviceType.MEMORY.value,
        ):
            logger.info(
                message.get_log_message(message.I00007, [log_param, f"Device Type {device_type} is not supported."])
            )
            return rtn_is_access, rtn_cpu_device_id

        if info_const.POWER_STATE_ON != self._get_oob_power_state(device_type, oob_data):
            logger.info(
                message.get_log_message(
                    message.I00007,
                    [log_param, f"Device {info_const.DATA_ITEM_POWER_STATE} is not {info_const.POWER_STATE_ON}."],
                )
            )
            return rtn_is_access, rtn_cpu_device_id

        if device_type == const.DeviceType.CPU.value:
            rtn_is_access = True
            rtn_cpu_device_id = device_id
        else:
            cpu_power_state, cpu_device_id = self._get_cpu_power_state(device_id, device_type, fm_data)
            if cpu_device_id and cpu_power_state == info_const.POWER_STATE_ON:
                rtn_is_access = True
                rtn_cpu_device_id = cpu_device_id
            else:
                if not cpu_device_id:
                    logger.info(
                        message.get_log_message(message.I00007, [log_param, "This device is not linked to the CPU."])
                    )
                else:
                    logger.info(
                        message.get_log_message(
                            message.I00007,
                            [
                                log_param,
                                f"CPU {info_const.DATA_ITEM_POWER_STATE} is not {info_const.POWER_STATE_ON}.",
                            ],
                        )
                    )

        return rtn_is_access, rtn_cpu_device_id

    def _get_oob_power_state(self, device_type: str, oob_data: dict | Any) -> Any:
        """Get power state

        Get power state from OOB data.

        Args:
            device_type (str): Device Type
            oob_data (dict | Any): OOB metric data

        Returns:
            Any: Power State

        """
        power_state = None

        # Get power status according to Device Type.
        if device_type in (const.DeviceType.CPU.value, const.DeviceType.MEMORY.value):
            power_state = (
                oob_data.get(info_const.OOB_DATA_ITEM, [{}])[info_const.DATA_ITEM_INDEX]
                .get(info_const.DATA_ITEM_SCHEMA, {})
                .get(info_const.DATA_ITEM_POWER_STATE)
            )
        elif device_type == const.DeviceType.STORAGE.value:
            power_state = (
                oob_data.get(info_const.OOB_DATA_ITEM, [{}])[info_const.DATA_ITEM_INDEX]
                .get(info_const.DATA_ITEM_SCHEMA, {})
                .get(info_const.DATA_ITEM_DRIVE, {})
                .get(info_const.DATA_ITEM_POWER_STATE)
            )
        elif device_type == const.DeviceType.NIC.value:
            power_state = (
                oob_data.get(info_const.OOB_DATA_ITEM, [{}])[info_const.DATA_ITEM_INDEX]
                .get(info_const.DATA_ITEM_SCHEMA, {})
                .get(info_const.DATA_ITEM_NETWORK, {})
                .get(info_const.DATA_ITEM_POWER_STATE)
            )

        return power_state

    def _get_cpu_power_state(self, device_id: str, device_type: str, fm_data: dict | Any) -> tuple[Any, Any]:
        """Get CPU power state

        Get CPU power state from FM data.

        Args:
            device_id (str): Device ID
            device_type (str): Device Type
            fm_data (dict | Any): FM data

        Returns:
            tuple[Any, Any]: CPU power state, CPU Device ID

        """
        cpu_power_state = None
        cpu_device_id = None
        get_spec_oob_info = GetSpecOOBInfo()
        # Get CPU power information from FM. (external device)
        fm_link = fm_data.get(info_const.FM_DATA_ITEM, [{}])[info_const.DATA_ITEM_INDEX].get(
            info_const.DATA_ITEM_FM_LINK
        )
        if fm_link:
            # Get CPU Device ID from FM link information.
            cpu_device_id = next(
                (
                    item[info_const.DATA_ITEM_DEVICE_ID]
                    for item in fm_link
                    if item[info_const.DATA_ITEM_TYPE] == const.DeviceType.CPU.value
                ),
                None,
            )
            if cpu_device_id:
                # Get CPU power information from OOB.
                cpu_oob_data = get_spec_oob_info.get_metric_oob(cpu_device_id, const.DeviceType.CPU.value)
                cpu_power_state = (
                    cpu_oob_data.get(info_const.OOB_DATA_ITEM, [{}])[info_const.DATA_ITEM_INDEX]
                    .get(info_const.DATA_ITEM_SCHEMA, {})
                    .get(info_const.DATA_ITEM_POWER_STATE)
                )
        # If CPU power information cannot be obtained from FM, get it from oob (built-in device).
        if not cpu_power_state:
            # To get CPU power information from OOB, get link information from your own device.
            oob_device_data = get_spec_oob_info.get_spec_oob(device_id, device_type)
            # Get CPU Device ID from link information.
            oob_link = oob_device_data.get(info_const.OOB_DATA_ITEM, [{}])[info_const.DATA_ITEM_INDEX].get(
                info_const.DATA_ITEM_OOB_LINK
            )
            if oob_link:
                cpu_device_id = next(
                    (
                        item[info_const.DATA_ITEM_DEVICE_ID]
                        for item in oob_link
                        if item[info_const.DATA_ITEM_TYPE] == const.DeviceType.CPU.value
                    ),
                    None,
                )
                if cpu_device_id:
                    # Get CPU power information from OOB.
                    cpu_oob_data = get_spec_oob_info.get_metric_oob(cpu_device_id, const.DeviceType.CPU.value)
                    cpu_power_state = (
                        cpu_oob_data.get(info_const.OOB_DATA_ITEM, [{}])[info_const.DATA_ITEM_INDEX]
                        .get(info_const.DATA_ITEM_SCHEMA, {})
                        .get(info_const.DATA_ITEM_POWER_STATE)
                    )

        return cpu_power_state, cpu_device_id

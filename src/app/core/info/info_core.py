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

"""HW independent section - Get Information process (Response generation)

Upon receiving a request from the information acquisition API,
make an information acquisition request for the specified device ID to FM and OOB.
Merge the device information returned from FM and OOB for each device
type and return it to the information acquisition API.

"""

import json
import datetime
from typing import List, Dict, Union, Any, Callable
from pydantic import BaseModel
from app.common.utils.log import LOGGER
from app.common.messages import message
from app.common.basic_exceptions import BaseHwControlError, InternalHwControlError
from app.core.info.spec_oob import GetSpecOOBInfo
from app.core.info.spec_fm import GetSpecFMInfo
from app.core.info.metric_agent import InfoMetricAgent
from app.common.constants import TIME_STAMP_FORMAT
from app.common.deviceIdManager import device_id_base as dim
import app.common.constants as const
from app.common.utils import error_utils
from app.core.info import info_utils, info_const
from app.common.settings import settings


class Device(BaseModel):
    """Device information

    Device information data class

    """

    # To align with the name defined in the JSON response format, use NOSONAR.
    deviceID: str = ""  # NOSONAR
    type: str = ""


class DeviceList(BaseModel):
    """Device list information

    Device list information data class

    """

    # To align with the name defined in the JSON response format, use NOSONAR.
    deviceList: List[Device] = []  # NOSONAR
    infoTimestamp: str = ""  # NOSONAR


class InformationCore:
    """Information Core

    Get information from various devices

    """

    def get_spec_info(self, device_id: str) -> tuple[Any, list]:
        """Get device information

        Get device information for the specified device ID

        Args:
            device_id (str): device ID

        Returns:
            tuple[Any, list]: device information, error information

        Examples:
            Get device information by specifying device ID

            >>> get_info = GetInformation()
                device_info = get_info.get_spec_info("0001")

        """

        response_data = None
        oob_data = None
        fm_data = None
        device_type = None
        errors = []

        try:
            # Get the device type from device ID management.
            device_type = dim.device_id_to_device_type(device_id)
            if device_type is None:
                LOGGER.warning(
                    message.get_log_message(
                        message.W00006, [f"Unable to retrieve the device type corresponding to Device ID: {device_id}."]
                    )
                )
                raise InternalHwControlError(
                    additional_message=f"Unable to retrieve the device type corresponding to Device ID: {device_id}."
                )
        except BaseHwControlError as bex:
            errors.append(bex.to_error_dict())

        if device_type is not None:
            try:
                # Get FM device information.
                get_spec_fm_info = GetSpecFMInfo()
                fm_data = get_spec_fm_info.get_spec_fm(device_id, device_type)
            except BaseHwControlError as bex:
                errors.append(bex.to_error_dict())

            try:
                # Get OOB device information.
                get_spec_oob_info = GetSpecOOBInfo()
                oob_data = get_spec_oob_info.get_spec_oob(device_id, device_type)
            except BaseHwControlError as bex:
                errors.append(bex.to_error_dict())

            try:
                # Generate response data.
                response_data = self._create_spec_info(device_id, device_type, fm_data, oob_data)
            except BaseHwControlError as bex:
                errors.append(bex.to_error_dict())

            if response_data is not None:
                # Set current datetime and assign it to the return data structure.
                response_data[info_const.RESP_ITEM_NAME_INFO_TIMESTAMP] = datetime.datetime.now(datetime.UTC).strftime(
                    TIME_STAMP_FORMAT
                )

        # Return response data.
        return response_data, error_utils.remove_duplicates(errors)

    def get_metric_info(self, device_id: str) -> tuple[Any, list]:
        """Get metric information

        Get metric information for the specified device ID

        Args:
            device_id (str): device ID

        Returns:
            tuple[Any, list]: metric information, error information

        Examples:
            Get metric information by specifying device ID

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
            # Retrieve device type from device ID management.
            device_type = dim.device_id_to_device_type(device_id)
            if device_type is None:
                LOGGER.warning(
                    message.get_log_message(
                        message.W00006, [f"Unable to retrieve the device type corresponding to Device ID: {device_id}."]
                    )
                )
                raise InternalHwControlError(
                    additional_message=f"Unable to retrieve the device type corresponding to Device ID: {device_id}."
                )
        except BaseHwControlError as bex:
            errors.append(bex.to_error_dict())

        if device_type not in (
            const.DeviceType.CPU.value,
            const.DeviceType.STORAGE.value,
            const.DeviceType.NIC.value,
            const.DeviceType.MEMORY.value,
            const.DeviceType.GPU.value,
        ):
            return response_data, errors

        # Function to handle errors for data fetching
        def fetch_data(fetch_func: Callable) -> Any:
            """Fetch data

            Fetches data using the provided fetch function and handles any BaseHwControlError exceptions.

            Args:
                fetch_func (Callable): A lambda or function that performs the data fetch operation.

            Returns:
                Any: The data fetched by the fetch_func, or None if an error occurred.
            """
            try:
                return fetch_func()
            except BaseHwControlError as bex:
                errors.append(bex.to_error_dict())
                return None

        # Get OOB metric information.
        get_spec_oob_info = GetSpecOOBInfo()
        oob_data = fetch_data(lambda: get_spec_oob_info.get_metric_oob(device_id, device_type))

        # Obtain FM device information. (FM retrieves metric information from device information)
        get_spec_fm_info = GetSpecFMInfo()
        fm_data = fetch_data(lambda: get_spec_fm_info.get_spec_fm(device_id, device_type))

        if settings.HW_CONTROL_AGENT_ENABLED and device_type != const.DeviceType.GPU.value:
            try:
                # Check agent connectivity.
                is_agent_access, cpu_device_id = self._verify_agent_access(device_id, device_type, oob_data, fm_data)
                if is_agent_access:
                    # Retrieve agent metric information.
                    get_metric_agent_info = InfoMetricAgent()
                    agent_data = get_metric_agent_info.get_metric_agent(device_id, device_type, cpu_device_id)
            except BaseHwControlError as bex:
                errors.append(bex.to_error_dict())

        # Generate response data.
        response_data = fetch_data(
            lambda: self._create_metric_info(device_id, device_type, agent_data, oob_data, fm_data)
        )

        if response_data:
            # Retrieve current datetime and assign it to the return data structure.
            response_data[info_const.RESP_ITEM_NAME_INFO_TIMESTAMP] = datetime.datetime.now(datetime.UTC).strftime(
                TIME_STAMP_FORMAT
            )

        # Return response data.
        return response_data, error_utils.remove_duplicates(errors)

    def _create_spec_info(
        self, device_id: str, device_type: Union[str, Any], fm_data: Union[dict, None], oob_data: Union[dict, None]
    ) -> dict:
        """Generate device information

        Generate device information to return

        Args:
            device_id (Union[str, Any]): device id
            device_type (Union[str, None]): device type
            fm_data (Union[dict, None]): fm data
            oob_data (Union[dict, None]): OOB data

        Returns:
            dict: device information

        """
        resp: Dict[str, Any] = info_const.RESP_INIT.copy()
        resp[info_const.RESP_ITEM_NAME_DEVICE_ID] = device_id
        resp[info_const.RESP_ITEM_NAME_TYPE] = device_type

        if device_type is None:
            return resp

        resp_oob, resp_fm = None, None

        if oob_data:
            try:
                # Get OOB mapping table.
                oob_mapping = info_utils.get_mapping_table(
                    device_type, info_const.DATA_SOURCE_TYPE_OOB, info_const.DATA_TYPE_SPEC
                )
                # Generate OOB response.
                resp_oob = info_utils.create_resp_from_mapping(oob_mapping, oob_data[info_const.OOB_DATA_ITEM][0])
                # Merge responses.
                resp.update(resp_oob)
            except BaseHwControlError as bex:
                LOGGER.warning(
                    f"Device ID:{device_id}, Agent data:{repr(oob_data)}, "
                    f"Error Code:{bex.error_code}, Error Message:{bex.message}, Exception:{repr(bex)}"
                )
                raise

        if fm_data:
            try:
                # Get FM mapping table.
                fm_mapping = info_utils.get_mapping_table(
                    device_type, info_const.DATA_SOURCE_TYPE_FM, info_const.DATA_TYPE_SPEC
                )
                # Generate FM response.
                resp_fm = info_utils.create_resp_from_mapping(fm_mapping, fm_data[info_const.FM_DATA_ITEM][0])
                # Merge responses.
                resp.update(resp_fm)
            except BaseHwControlError as bex:
                LOGGER.warning(
                    f"Device ID:{device_id}, Agent data:{repr(fm_data)}, "
                    f"Error Code:{bex.error_code}, Error Message:{bex.message}, Exception:{repr(bex)}"
                )
                raise

        merged_link = self._merge_spec_link_data(resp_oob, resp_fm)
        # Set link data.
        if len(merged_link) > 0:
            resp[info_const.RESP_ITEM_NAME_LINK] = merged_link

        # Set constraints property.
        constraints = self._create_constraints(device_id, merged_link)
        resp[info_const.RESP_ITEM_NAME_CONSTRAINTS] = constraints[info_const.RESP_ITEM_NAME_CONSTRAINTS]

        # Set model property according to the device type.
        self._set_model_property(resp)

        # Remove items with missing values from the response.
        return info_utils.remove_empty_item(resp)

    def _merge_spec_link_data(self, resp_oob: Union[dict, None], resp_fm: Union[dict, None]) -> List[Any]:
        """Merge spec link data

        Merge spec link data.

        Args:
            fm_data (Union[dict, None]): fm data
            oob_data (Union[dict, None]): OOB data

        Returns:
            List[Any]: link data
        """
        merged_link: List[Any] = []

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

        Set model property according to the device type.

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
        elif device_type == const.DeviceType.NIC.value:
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
        device_type: Union[str, Any],
        agent_data: Union[dict, None],
        oob_data: Union[dict, None],
        fm_data: Union[dict, None],
    ) -> dict:
        """Generate metric information

        Generate metric information to return

        Args:
            device_id (str): device id
            device_type (Union[str, Any]): device type
            agent_data (Union[dict, None]): Agent data
            oob_data (Union[dict, None]): OOB data
            fm_data (Union[dict, None]): FM data

        Returns:
            dict: metric information

        """
        resp = info_const.RESP_INIT.copy()
        resp[info_const.RESP_ITEM_NAME_DEVICE_ID] = device_id
        resp[info_const.RESP_ITEM_NAME_TYPE] = device_type

        if device_type is None:
            return resp

        if agent_data is not None:
            # Get agent mapping table.
            agent_mapping = info_utils.get_mapping_table(
                device_type, info_const.DATA_SOURCE_TYPE_AGENT, info_const.DATA_TYPE_METRIC
            )
            try:
                # Generate agent response.
                resp_agent = info_utils.create_resp_from_mapping(
                    agent_mapping, agent_data[info_const.AGENT_DATA_ITEM][0]
                )
            except BaseHwControlError as bex:
                LOGGER.warning(
                    f"Device ID:{device_id}, Agent data:{repr(agent_data)}, "
                    f"Error Code:{bex.error_code}, Error Message:{bex.message}, Exception:{repr(bex)}"
                )
                raise
            # Merge responses.
            resp = {**resp_agent, **resp}
        if oob_data is not None:
            # Get OOB metric mapping table.
            oob_mapping = info_utils.get_mapping_table(
                device_type, info_const.DATA_SOURCE_TYPE_OOB, info_const.DATA_TYPE_METRIC
            )
            try:
                # Generate OOB response.
                resp_oob = info_utils.create_resp_from_mapping(oob_mapping, oob_data[info_const.OOB_DATA_ITEM][0])
            except BaseHwControlError as bex:
                LOGGER.warning(
                    f"Device ID:{device_id}, Agent data:{repr(oob_data)}, "
                    f"Error Code:{bex.error_code}, Error Message:{bex.message}, Exception:{repr(bex)}"
                )
                raise
            # Merge responses.
            resp = {**resp_oob, **resp}
        if fm_data is not None:
            # Get FM metric mapping table.
            fm_mapping = info_utils.get_mapping_table(
                device_type, info_const.DATA_SOURCE_TYPE_FM, info_const.DATA_TYPE_METRIC
            )
            try:
                # Generate FM response.
                resp_fm = info_utils.create_resp_from_mapping(fm_mapping, fm_data[info_const.FM_DATA_ITEM][0])
            except BaseHwControlError as bex:
                LOGGER.warning(
                    f"Device ID:{device_id}, Agent data:{repr(fm_data)}, "
                    f"Error Code:{bex.error_code}, Error Message:{bex.message}, Exception:{repr(bex)}"
                )
                raise
            # Merge responses.
            resp = {**resp_fm, **resp}

        # Remove items with non-existent values from response.
        resp = info_utils.remove_empty_item(resp)

        return resp

    def _create_constraints(self, device_id: str, links: list) -> dict:
        """Create Constraints

        Generates constraints based on information obtained from OOB and FM and returns them.

        Args:
            device_id (str): base device id
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
            if (dim.device_id_to_fm_valid(link_device_id) is False) or (
                is_built_in_device is True and link_device.get(info_const.RESP_ITEM_NAME_TYPE)
            ):
                # If no information has been obtained from the FM, or if the base device is an internal device
                # and the device type is "CPU", it is determined that disconnection is not possible.
                non_removable_devices.append({info_const.RESP_ITEM_NAME_DEVICE_ID: link_device_id})
        # Add a list of non-dis-connectable devices to the constraints.
        if len(non_removable_devices) > 0:
            constraints[info_const.RESP_ITEM_NAME_CONSTRAINTS][
                info_const.RESP_ITEM_NAME_NON_REMOVABLE_DEVICES
            ] = non_removable_devices

        return constraints

    def get_device_list(self, device_type: str | None) -> dict:
        """Get device list

        Get a list of devices that correspond to the specified device type.
        If no device type is specified, get a list of all devices.

        Args:
            device_type (str | None): device type

        Returns:
            dict: device list

        Examples:
            Get device list by specifying device type

            >>> get_info = GetInformation()
                device_list = get_info.get_device_list("CPU")

        """

        resp_data = None

        # Create a data structure for returning (for device list).
        resp_device_list = DeviceList()

        # Get a list of device IDs from device ID management.
        dev_id_list = dim.get_controllable_device_id_list()
        # For generating device attribute information (stub).
        dev_list_all = []
        # Loop for the number of device IDs.
        for dev_id in dev_id_list:
            # Get device type from device ID management.
            dev_type = dim.device_id_to_device_type(dev_id)
            if dev_type is not None:
                # Add to device list for generating device attribute information (stub).
                dev_list_all.append(
                    {
                        info_const.DEVICE_LIST_ITEM_NAME_DEVICE_ID: dev_id,
                        info_const.DEVICE_LIST_ITEM_NAME_DEVICE_TYPE: dev_type,
                    }
                )
                # If a device type is specified as an argument, does it match?
                if device_type is None or (device_type is not None and dev_type == device_type):
                    # Pair the device ID and the device type and add to the array.
                    device = Device()
                    device.deviceID = dev_id  # pylint: disable=C0103
                    device.type = dev_type
                    resp_device_list.deviceList.append(device)

        # Get the current date and time and set it to the data structure for returning.
        resp_device_list.infoTimestamp = datetime.datetime.now(datetime.UTC).strftime(  # pylint: disable=C0103
            TIME_STAMP_FORMAT
        )

        # Generate device list information from the data structure for returning.
        resp_data = json.loads(resp_device_list.model_dump_json())

        # If device ID information does not exist, delete the item itself.
        if not resp_device_list.deviceList:
            resp_data.pop(info_const.DEVICE_LIST_ITEM_NAME_DEVICE_LIST, None)

        # Generate device attribute information (stub).
        if dev_list_all:
            # Generate device attribute information (Agent connection stub information).
            get_metric_agent_info = InfoMetricAgent()
            get_metric_agent_info.create_device_attribute(dev_list_all)

        return resp_data

    def _verify_agent_access(
        self, device_id: str, device_type: str, oob_data: Union[dict, Any], fm_data: Union[dict, Any]
    ) -> tuple[bool, Any]:
        """Verify agent access

        Verify agent can be accessed

        Args:
            device_id (str): device id
            device_type (str): device type
            oob_data (Union[dict, Any]): OOB metric data
            fm_data (Union[dict, Any]): FM device data

        Returns:
            tuple[bool, Any]: True(connectable) or False(Unable connect), cpu device id

        """

        rtn_is_access = False
        rtn_cpu_device_id = None
        log_pram = f"device_id: {device_id}, device_type: {device_type}, "

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
            LOGGER.info(
                message.get_log_message(
                    message.I00007, [log_pram, f"Invalid input values: {', '.join(invalid_values)}."]
                )
            )
            return rtn_is_access, rtn_cpu_device_id

        if device_type not in (
            const.DeviceType.CPU.value,
            const.DeviceType.STORAGE.value,
            const.DeviceType.NIC.value,
            const.DeviceType.MEMORY.value,
        ):
            LOGGER.info(
                message.get_log_message(message.I00007, [log_pram, f"Device type {device_type} is not supported."])
            )
            return rtn_is_access, rtn_cpu_device_id

        if info_const.POWER_STATE_ON != self._get_oob_power_state(device_type, oob_data):
            LOGGER.info(
                message.get_log_message(
                    message.I00007,
                    [log_pram, f"Device {info_const.DATA_ITEM_POWER_STATE} is not {info_const.POWER_STATE_ON}."],
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
                    LOGGER.info(
                        message.get_log_message(message.I00007, [log_pram, "This device is not linked to the CPU."])
                    )
                else:
                    LOGGER.info(
                        message.get_log_message(
                            message.I00007,
                            [
                                log_pram,
                                f"CPU {info_const.DATA_ITEM_POWER_STATE} is not {info_const.POWER_STATE_ON}.",
                            ],
                        )
                    )

        return rtn_is_access, rtn_cpu_device_id

    def _get_oob_power_state(self, device_type: str, oob_data: Union[dict, Any]) -> Any:
        """Get power state

        Get power state from OOB data.

        Args:
            device_type (str): device type
            oob_data (Union[dict, Any]): OOB metric data

        Returns:
            Any: Power State

        """
        power_state = None

        # Get power status according to device type.
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

    def _get_cpu_power_state(self, device_id: str, device_type: str, fm_data: Union[dict, Any]) -> tuple[Any, Any]:
        """Get cpu power state

        Get cpu power state from FM data.

        Args:
            device_id (str): device id
            device_type (str): device type
            fm_data (Union[dict, Any]): FM data

        Returns:
            tuple[Any, Any]: cpu power state, cpu device id

        """
        cpu_power_state = None
        cpu_device_id = None
        get_spec_oob_info = GetSpecOOBInfo()
        # Get CPU power information from FM. (external device)
        fm_link = fm_data.get(info_const.FM_DATA_ITEM, [{}])[info_const.DATA_ITEM_INDEX].get(
            info_const.DATA_ITEM_FM_LINK
        )
        if fm_link:
            # Get CPU device ID from FM link information.
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
            # Get CPU device ID from link information.
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

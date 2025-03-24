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

"""
HW independent section - Agent control

Upon receiving a request from the control API,
Makes a control request to Agent for the device
specified by the 'Device ID'.
"""
import traceback
from enum import Enum
from http import HTTPStatus
from http import HTTPMethod

import requests
from urllib3.util import Url
from urllib3.util.retry import Retry
from pydantic import BaseModel, Field

from app.core.control.control_base import PowerControlTargetDevice
from app.core.control import oob_control
from app.common.utils import os_ipaddress
from app.common import constants
import app.common.basic_exceptions as exc
from app.common.utils.log import LOGGER
from app.common.messages import message
from app.common.utils.authorization_utilities import authorization_server_client

# build for REST API URL
AGENT_REST_API_SCHEME = "http"
AGENT_REST_API_PORT = 8000

# The default value for the timeout when sending a request to the Agent.
AGENT_REST_API_TIMEOUT = 3.0
# The default value for the retry backoff time of requests to the Agent.
BACKOFF_TIME = 1.0


class AgentApiPath(Enum):
    """An enumeration of agent REST API path.

    This Enum class is used to represent different types of
    REST API path for agent.

    Args:
        IS_OS_READY_API (str):
            Represents a url of 'is os ready api' for agent.

        OS_SHUTDOWN_API (str):
            Represents a url of 'os shutdown api' for agent.

    """

    IS_OS_READY_API = "cdim/api/v1/agent/is-os-ready"
    OS_SHUTDOWN_API = "cdim/api/v1/agent/os-shutdown"


class ControlTargetAgent(BaseModel):
    """
    Represents the information of an agent running on the host OS of the control target node.

    Attributes:
        host_cpu_device_id (str):
            Identifier that uniquely identifies the device (host CPU).

        ip_address (str):
            IP address of the host OS.

        port (int):
            Port for the agent's service. Defaults to 8000.
    """

    host_cpu_device_id: str = Field()
    ip_address: str = Field(default="")
    port: int = Field(default=AGENT_REST_API_PORT)

    def model_post_init(self, __context):
        """Post-initialization method for ControlTargetAgent.

        This method is called after the initialization of an instance of ControlTargetAgent.
        It sets the 'IP Address' and 'Port' for the target Agent service.
        If any of these settings fail, a RequestNotSupportedHwControlError is raised.

        Raises:
            exc.RequestNotSupportedHwControlError: If setting the ip_address fails.
        """
        try:
            self.set_ip_address()
        except ValueError as e:
            raise exc.RequestNotSupportedHwControlError from e

    def set_ip_address(self) -> None:
        """Set the ip address of the OS running on the target device.

        Set the ip address of the OS running on the target device.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError
            - The 'IP Address' could not be obtained from os_ipaddress.

        """

        target_ip_address, is_agent_exist = os_ipaddress.get_os_ipaddress(self.host_cpu_device_id)

        if not is_agent_exist:
            raise ValueError

        if target_ip_address is None:
            raise ValueError

        self.ip_address = target_ip_address


class AgentController:
    """
    A class to control the target agent by sending requests to the agent
    running on the host OS.

    Attributes: None

    Methods:
        os_shutdown:
            Shutdown the target host OS.

        is_os_ready:
            Check whether the target host OS is ready.
    """

    @staticmethod
    def _execute_os_shutdown(target_agent: ControlTargetAgent) -> None:
        """
        Execute host OS shutdown.

        Args:
            target_device (PowerControlTargetDevice):
                Represents the CPU device object,
                which is responsible for executing the target host OS.

        Raises:
            AuthenticationHwControlError:
                If failed to authenticate to the HW Control Agent.

            InternalHwControlError:
                If the request to the Agent failed due to an unexpected error.

            ControlObjectHwControlError
                If the HW Control Agent failed to shutdown Host OS state due to an unexpected error.

        Returns:
            None
        """

        access_token = authorization_server_client.get_agent_access_token()
        requests_header = {"Authorization": f"Bearer {access_token}"}

        target_url = Url(
            scheme=AGENT_REST_API_SCHEME,
            host=target_agent.ip_address,
            port=target_agent.port,
            path=AgentApiPath.OS_SHUTDOWN_API.value,
        )

        LOGGER.info(
            message=message.AgentRequestLog(
                ip_address=target_agent.ip_address,
                port=AGENT_REST_API_PORT,
                url=str(target_url),
                http_method=HTTPMethod.PUT,
                time_out=AGENT_REST_API_TIMEOUT,
            ).to_json_encodable()
        )

        # request OS shutdown to Agent using REST-API
        try:
            agent_response = requests.put(
                url=str(target_url),
                timeout=AGENT_REST_API_TIMEOUT,
                headers=requests_header,
            )
        except requests.exceptions.RequestException as e:
            raise exc.InternalHwControlError(
                additional_message="The request to the Agent failed due to an unexpected error."
            ) from e

        LOGGER.info(message=message.AgentResponseLog.create_from_response(response=agent_response).to_json_encodable())

        if agent_response.status_code == HTTPStatus.UNAUTHORIZED.value:
            raise exc.AuthenticationHwControlError(additional_message="Failed to authenticate to the HW Control Agent.")

        if agent_response.status_code != HTTPStatus.OK.value:
            raise exc.ControlObjectHwControlError(
                additional_message="The HW Control Agent failed to shutdown Host OS."
            )  # Handling cases where an error other than 401 Unauthorized is returned.

    @staticmethod
    def os_shutdown(target_device: PowerControlTargetDevice, target_agent: ControlTargetAgent) -> None:
        """
        Perform an host OS shutdown via the Agent, and if it fails,
        perform an ACPI shutdown via OOB.

        Args:
            target_device (PowerControlTargetDevice):
                Represents the CPU device object that boots the target
                host OS.

            target_agent (ControlTargetAgent):
                The agent object running on the host OS.

        Returns:
            None

        Raises:
            RequestNotSupportedHwControlError:
                If the specified device is not a CPU.

            InternalHwControlError:
                If the specified device power state is unexpected.
        """

        if target_device.device_type != constants.DeviceType.CPU.value:
            raise exc.RequestNotSupportedHwControlError()

        try:
            target_device.set_power_state()
        except ValueError as e:
            # TODO: add more reason
            raise exc.RequestNotSupportedHwControlError from e

        if target_device.power_state in (constants.DevicePowerState.PAUSED, constants.DevicePowerState.UNKNOWN):
            # TODO: logging target_device.power_state
            raise exc.InternalHwControlError(additional_message="The specified device power state is unexpected.")

        if target_device.power_state in (
            constants.DevicePowerState.OFF,
            constants.DevicePowerState.POWERING_OFF,
        ):
            return

        try:
            AgentController._execute_os_shutdown(target_agent=target_agent)
        except exc.BaseHwControlError:
            # The shutdown of host OS via the Agent failed.
            LOGGER.warning(
                message.ExceptionLog(
                    detail="Retry with ACPI shutdown", trace_back=traceback.format_exc()
                ).to_json_encodable()
            )
            # Retry with ACPI shutdown via OOB.
            oob_control.OobController.power_off(target_device=target_device)

    @staticmethod
    def is_os_ready(target_device: PowerControlTargetDevice, target_agent: ControlTargetAgent, timeout: int) -> bool:
        """
        Check whether the target host OS is ready.

        This method sends a request to the agent to check if the target
        host OS is ready within the specified timeout period.

        Args:
            target_device (PowerControlTargetDevice):
                Represents the CPU device object,
                which is responsible for executing the target host OS.

            target_agent (ControlTargetAgent):
                The agent running on the host OS.

            timeout (int):
                Timeout value for checking the OS state in seconds.

        Raises:
            RequestNotSupportedHwControlError:
                If the specified device is not a CPU.

            HostCpuPowerOffBadRequestHwControlError:
                If the host CPU is powered off.

            InternalHwControlError:
                If the request to the Agent failed due to an unexpected error.

            AuthenticationHwControlError:
                If failed to authenticate to the HW Control Agent.

            ControlObjectHwControlError
                If the HW Control Agent failed to check Host OS state due to an unexpected error.

        Returns:
            bool:
                True if the target host OS is ready, False otherwise.
        """
        os_state = False

        if target_device.device_type != constants.DeviceType.CPU.value:
            raise exc.RequestNotSupportedHwControlError()

        try:
            target_device.set_power_state()
        except ValueError as e:
            # TODO: add more reason
            raise exc.RequestNotSupportedHwControlError from e

        if target_device.power_state in (
            constants.DevicePowerState.OFF,
            constants.DevicePowerState.POWERING_OFF,
        ):
            raise exc.HostCpuPowerOffBadRequestHwControlError

        if target_device.power_state in (constants.DevicePowerState.PAUSED, constants.DevicePowerState.UNKNOWN):
            # TODO: logging target_device.power_state
            raise exc.InternalHwControlError(additional_message="The specified device power state is unexpected.")

        retry_times: int = int(timeout // (BACKOFF_TIME + AGENT_REST_API_TIMEOUT))

        with requests.Session() as session:
            retries = Retry(total=retry_times, backoff_factor=BACKOFF_TIME, backoff_max=BACKOFF_TIME)
            session.mount(
                prefix=f"{AGENT_REST_API_SCHEME}://",
                adapter=requests.adapters.HTTPAdapter(max_retries=retries),
            )

            access_token = authorization_server_client.get_agent_access_token()
            requests_header = {"Authorization": f"Bearer {access_token}"}

            target_url = Url(
                scheme=AGENT_REST_API_SCHEME,
                host=target_agent.ip_address,
                port=target_agent.port,
                path=AgentApiPath.IS_OS_READY_API.value,
            )

            LOGGER.info(
                message=message.AgentRequestLog(
                    ip_address=target_agent.ip_address,
                    port=target_agent.port,
                    url=str(target_url),
                    http_method=HTTPMethod.GET,
                    time_out=timeout,
                ).to_json_encodable()
            )

            try:
                agent_response = session.get(
                    url=str(target_url),
                    timeout=AGENT_REST_API_TIMEOUT,
                    headers=requests_header,
                )

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                os_state = False
                return os_state

            except requests.exceptions.RequestException as e:
                raise exc.InternalHwControlError(
                    additional_message="The request to the Agent failed due to an unexpected error."
                ) from e

            LOGGER.info(
                message=message.AgentResponseLog.create_from_response(response=agent_response).to_json_encodable()
            )

            if agent_response.status_code == HTTPStatus.OK.value:
                os_state = True

            elif agent_response.status_code == HTTPStatus.UNAUTHORIZED.value:
                raise exc.AuthenticationHwControlError(
                    additional_message="Failed to authenticate to the HW Control Agent."
                )

            else:
                raise exc.ControlObjectHwControlError(
                    additional_message="The HW Control Agent failed to check Host OS state."
                )  # Handling cases where an error other than 401 Unauthorized is returned.

        return os_state

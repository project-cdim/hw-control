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

"""Unit test module for agent_control.py module."""
import pytest
from pytest_mock import MockFixture

from tests.app.core.control import test_util

from app.common.utils import os_ipaddress
import app.common.basic_exceptions as exc
from app.core.control import agent_control

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++++#
from app.core.control.agent_control import ControlTargetAgent

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


class TestControlTargetAgentGenerate:
    """Unit test class for ControlTargetAgent instance generate."""

    @pytest.mark.parametrize(
        "ip_address_manager_return",
        [(test_util.DummyCPUInfo.IP_ADDRESS.value, True)],
    )
    def test_instance_generate_successful(
        self,
        mocker: MockFixture,
        ip_address_manager_return,
    ):
        """Unit test for ControlTargetAgent instance generate successful."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Expected results:
        expected_ip_address, _ = ip_address_manager_return
        expected_port = agent_control.AGENT_REST_API_PORT

        # Set up the mock.
        mocker.patch.object(os_ipaddress, "get_os_ipaddress", return_value=ip_address_manager_return)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        test_agent = ControlTargetAgent(host_cpu_device_id=target_device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert test_agent.ip_address == expected_ip_address
        assert test_agent.port == expected_port

    @pytest.mark.parametrize(
        "ip_address_manager_return",
        [
            (test_util.DummyCPUInfo.IP_ADDRESS.value, False),
            (None, True),
            (None, False),
        ],
    )
    def test_get_os_ipaddress_return_invalid(
        self,
        mocker: MockFixture,
        ip_address_manager_return,
    ):
        """Unit test for get_os_ipaddress return invalid value case."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        target_device_id = test_util.DummyCPUInfo.DEVICE_ID.value

        # Set up the mock.
        mocker.patch.object(os_ipaddress, "get_os_ipaddress", return_value=ip_address_manager_return)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        with pytest.raises(exc.RequestNotSupportedHWControlError):
            _ = ControlTargetAgent(host_cpu_device_id=target_device_id)

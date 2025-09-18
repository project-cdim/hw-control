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

"""This module define app.routers.control common fixture."""

import pytest
from pytest_mock import MockFixture

from tests import test_util

from app.core.control import control_base
from app.core.control import agent_control
from app.core.control import fm_control
from app.common import constants


@pytest.fixture(scope="function")
def default_power_control_target_device_fixture(mocker: MockFixture):
    """
    Fixture to create a PowerControlTargetDevice instance with patched `model_post_init`.

    This fixture patches the `model_post_init` method of the `ControlTargetDevice`
    class to do nothing (using a no-op lambda function). It then creates an instance
    of `ControlTargetDevice` with specified parameters or default values.
    """
    mocker.patch.object(control_base.PowerControlTargetDevice, "model_post_init", lambda self, __context: None)

    device = control_base.PowerControlTargetDevice(
        device_id=test_util.DummyCPUInfo.DEVICE_ID.value,
        device_type=test_util.DummyCPUInfo.DEVICE_TYPE.value,
        oob_manager_id=test_util.DummyCPUInfo.OOB_MANAGER_ID.value,
        oob_device_id=test_util.DummyCPUInfo.OOB_DEVICE_ID.value,
        power_state=constants.DevicePowerState.UNKNOWN,
    )
    return device


@pytest.fixture(scope="function")
def default_fm_control_host_cpu_fixture(mocker: MockFixture):
    """
    Fixture to create a FMControlTargetDevice instance with patched `model_post_init`.

    This fixture patches the `model_post_init` method of the `fm_control`
    class to do nothing (using a no-op lambda function). It then creates an instance
    of `ControlTargetDevice` with specified parameters or default values.
    """
    mocker.patch.object(fm_control.FMControlTargetDevice, "model_post_init", lambda self, __context: None)

    device = fm_control.FMControlTargetDevice(
        device_id=test_util.DummyCPUInfo.DEVICE_ID.value,
        switch_port_type=test_util.DummyCPUInfo.SWITCH_PORT_TYPE.value,
        fm_manager_id=test_util.DummyCPUInfo.FM_MANAGER_ID.value,
        fm_port_id=test_util.DummyCPUInfo.FM_PORT_ID.value,
    )
    return device


@pytest.fixture(scope="function")
def default_control_target_agent_fixture(mocker: MockFixture):
    """
    Fixture to create a PowerControlTargetAgent instance with patched `model_post_init`.

    This fixture patches the `model_post_init` method of the `ControlTargetAgent`
    class to do nothing (using a no-op lambda function). It then creates an instance
    of `ControlTargetAgent` with specified parameters or default values.
    """
    mocker.patch.object(agent_control.ControlTargetAgent, "model_post_init", lambda self, __context: None)

    agent = agent_control.ControlTargetAgent(
        host_cpu_device_id=test_util.DummyCPUInfo.DEVICE_ID.value, ip_address=test_util.DummyCPUInfo.IP_ADDRESS.value
    )
    return agent

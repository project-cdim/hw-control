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

"""This module define common fixture."""

import uuid
import pytest
from pytest_mock import MockFixture

from tests import test_util

from app.common import constants
from app.common import request_id_utilities
from app.core.control import control_base
from app.core.control import agent_control
from app.core.control import fm_control


@pytest.fixture(scope="function")
def dummy_request_id():
    """Provides a dummy request ID set in the context variable for testing.

    Yields:
        str: The dummy request ID set in the context.
    """
    dummy_request_id = str(uuid.uuid4())
    # Set up the dummy request ID in context.
    token = request_id_utilities._request_id.set(dummy_request_id)  # pylint: disable=W0212

    yield dummy_request_id

    # Clean up the request ID in context.
    request_id_utilities._request_id.reset(token)  # pylint: disable=W0212


@pytest.fixture(scope="function")
def control_target_agent_fixture(mocker: MockFixture, request):
    """Fixture to create a test instance of ControlTargetAgent.

    This fixture generates a ControlTargetAgent object for testing purposes. The
    fixture mocks the `model_post_init` method of ControlTargetAgent to bypass
    post-initialization logic, allowing the creation of an instance with specified values.
    The customized values for the instance are provided through the `request.param` dictionary.

    Args:
        mocker (MockFixture): The mocker fixture used to mock target methods.
        request: The request parameter used to pass parameters to the fixture.

    Returns:
        ControlTargetAgent: A test instance of ControlTargetAgent with the specified
        `host_cpu_device_id` and `ip_address`.
    Example:
        Using this fixture in a test:

        @pytest.mark.parametrize(
            "control_target_agent_fixture",
            [
                {
                    "host_cpu_device_id": "451b0faf-b70d-4476-832a-4c93f0e6e1ce",
                    "ip_address": 192.168.1.19,
                },
                {
                    "device_id": "852f416b-a6e7-4d32-b9c4-238901544d48",
                    "ip_address": 192.168.1.20,
                },
            ],
            indirect=True,
        )
        def test_function(control_target_agent_fixture)
    """
    mocker.patch.object(agent_control.ControlTargetAgent, "model_post_init", lambda self, __context: None)

    params = request.param
    agent = agent_control.ControlTargetAgent(
        host_cpu_device_id=params.get("host_cpu_device_id", test_util.DummyCPUInfo.DEVICE_ID.value),
        ip_address=params.get("ip_address", test_util.DummyCPUInfo.IP_ADDRESS.value),
    )
    return agent


@pytest.fixture(scope="function")
def fm_control_target_device_pair_fixture(mocker: MockFixture, request):
    """Fixture to create a test instance of FMControlTargetDevicePair.

    This fixture generates a FMControlTargetDevicePair object for testing purposes. The
    FMControlTargetDevicePair class has attributes `upstream_device` and `downstream_device`, each
    of which is an instance of FMControlTargetDevice.

    The fixture mocks the `model_post_init` method of FMControlTargetDevice to bypass
    post-initialization logic, allowing the creation of instances with specified values.
    These instances are then stored in the `upstream_device` and `downstream_device` attributes of
    the FMControlTargetDevicePair object.

    The attributes of the `upstream_device` and `downstream_device` instances can be customized
    using the `request.param` dictionary.

    Args:
        mocker (MockFixture): The mocker fixture used to mock target methods.
        request: The request parameter used to pass parameters to the fixture.

    Returns:
        FMControlTargetDevicePair: A test instance of FMControlTargetDevicePair containing
        the mocked `upstream_device` and `downstream_device` instances.

    Example:
        Using this fixture in a test:

        @pytest.mark.parametrize(
            "fm_control_target_device_pair_fixture",
            [
                {
                    # upstream_device parameter
                    "upstream_device_device_id": "451b0faf-b70d-4476-832a-4c93f0e6e1ce",
                    "upstream_device_switch_port_type": constants.DeviceType.USP.value,
                    "upstream_device_fm_manager_id": "test_fm_manager_id",
                    # downstream_device parameter
                    "downstream_device_device_id": "852f416b-a6e7-4d32-b9c4-238901544d48",
                    "downstream_device_switch_port_type": constants.SwitchPortType.DSP.value,
                    "downstream_device_fm_manager_id": "test_fm_manager_id",
                },
            ],
            indirect=True,
        )
        def test_function(fm_control_target_device_pair_fixture)
    """
    mocker.patch.object(fm_control.FMControlTargetDevice, "model_post_init", lambda self, __context: None)

    params = request.param
    upstream_device = fm_control.FMControlTargetDevice(
        device_id=params.get("upstream_device_id", test_util.DummyCPUInfo.DEVICE_ID.value),
        switch_port_type=params.get("upstream_device_switch_port_type", test_util.DummyCPUInfo.DEVICE_TYPE.value),
        fm_port_id=params.get("upstream_device_fm_port_id", test_util.DummyCPUInfo.OOB_MANAGER_ID.value),
        fm_manager_id=params.get("upstream_device_fm_manager_id", test_util.DummyCPUInfo.OOB_DEVICE_ID.value),
    )
    downstream_device = fm_control.FMControlTargetDevice(
        device_id=params.get("downstream_device_device_id", test_util.DummyDeviceInfo.DEVICE_ID.value),
        switch_port_type=params.get("downstream_device_switch_port_type", test_util.DummyDeviceInfo.DEVICE_TYPE.value),
        fm_port_id=params.get("downstream_device_fm_port_id", test_util.DummyDeviceInfo.OOB_MANAGER_ID.value),
        fm_manager_id=params.get("downstream_device_fm_manager_id", test_util.DummyDeviceInfo.OOB_DEVICE_ID.value),
    )

    device_pair = fm_control.FMControlTargetDevicePair(
        upstream_device=upstream_device, downstream_device=downstream_device
    )

    return device_pair


@pytest.fixture(scope="function")
def power_control_target_device_fixture(mocker: MockFixture, request):
    """
    Fixture to create a PowerControlTargetDevice instance with patched `model_post_init`.

    This fixture patches the `model_post_init` method of the `PowerControlTargetDevice`
    class to do nothing (using a no-op lambda function). It then creates an instance
    of `PowerControlTargetDevice` with specified parameters or default values.

    Args:
        mocker (MockFixture): The mocker fixture provided by pytest-mock.
        request: The request object provided by pytest, which contains
            the parametrized values.

    Returns:
        ControlTargetDevice: An instance of PowerControlTargetDevice with specified or
        default values for its attributes.

    Example:
        Using this fixture in a test:

        @pytest.mark.parametrize(
            "power_control_target_device_fixture",
            [
                {
                    "device_id": "451b0faf-b70d-4476-832a-4c93f0e6e1ce",
                    "device_type": constants.DeviceType.CPU.value,
                    "oob_manager_id": "BMC_001",
                    "oob_device_id": "CPU_001",
                    "power_state": constants.DevicePowerState.ON.value,
                },
                {
                    "device_id": "852f416b-a6e7-4d32-b9c4-238901544d48",
                    "device_type": constants.DeviceType.NIC.value,
                    "oob_manager_id": "BMC_002",
                    "oob_device_id": "NIC_001",
                    "power_state": constants.DevicePowerState.OFF.value,
                },
            ],
            indirect=True,
        )
        def test_function(power_control_target_device_fixture)
    """
    mocker.patch.object(control_base.PowerControlTargetDevice, "model_post_init", lambda self, __context: None)

    params = request.param
    device = control_base.PowerControlTargetDevice(
        device_id=params.get("device_id", test_util.DummyCPUInfo.DEVICE_ID.value),
        device_type=params.get("device_type", test_util.DummyCPUInfo.DEVICE_TYPE.value),
        oob_manager_id=params.get("oob_manager_id", test_util.DummyCPUInfo.OOB_MANAGER_ID.value),
        oob_device_id=params.get("oob_device_id", test_util.DummyCPUInfo.OOB_DEVICE_ID.value),
        power_state=params.get("power_state", constants.DevicePowerState.UNKNOWN),
    )
    return device

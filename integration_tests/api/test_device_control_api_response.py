# Copyright 2026 NEC Corporation
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

"""Integration tests for API response format consistency.

Verifies that successful responses include the expected payload shape.
Error response format is covered by test_error_handling.py and
test_request_parameter_validation.py, since generating the error format is
the error handlers' responsibility, not the control API endpoints'.
"""

from fastapi.testclient import TestClient
from pytest_mock import MockFixture

from app.core.control import agent_control, control_base, fm_control

_DEVICE_UUID = "451b0faf-b70d-4476-832a-4c93f0e6e1ce"
_DOWNSTREAM_DEVICE_UUID = "b9f9b678-bce8-49a1-bca3-dbbc32259abf"
_POWER_URL = f"/cdim/api/v1/devices/{_DEVICE_UUID}/power"
_AGGREGATION_URL = f"/cdim/api/v1/devices/{_DEVICE_UUID}/aggregations"
_IS_OS_READY_URL = f"/cdim/api/v1/cpu/{_DEVICE_UUID}/is-os-ready"


class TestSuccessResponseFormat:
    """Successful (2xx) responses include the expected payload fields."""

    def test_power_control_success_response(self, test_client: TestClient, mocker: MockFixture):
        """Successful Power Control response contains 'deviceID' with the requested device ID."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        mocker.patch.object(control_base.PowerControlTargetDevice, "model_post_init", return_value=None)
        mocker.patch.object(control_base.PowerControlTargetDevice, "device_id", _DEVICE_UUID, create=True)
        mocker.patch(
            "app.core.control.control_base.PowerControlTargetDevice",
            return_value=control_base.PowerControlTargetDevice.model_construct(device_id=_DEVICE_UUID),
        )
        mocker.patch("app.routers.control.control_api.oob_control.OOBController.power_on", return_value=None)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.put(_POWER_URL, json={"action": "on"})

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 200
        body = response.json()
        assert body == {"deviceID": _DEVICE_UUID}

    def test_is_os_ready_success_response(self, test_client: TestClient, mocker: MockFixture):
        """Successful Is OS Ready response contains 'status' and 'IPAddress' matching the agent's values."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        dummy_ip = "192.0.2.1"

        mocker.patch.object(control_base.PowerControlTargetDevice, "model_post_init", return_value=None)
        mocker.patch.object(agent_control.ControlTargetAgent, "model_post_init", return_value=None)

        mock_agent = agent_control.ControlTargetAgent.model_construct(
            host_cpu_device_id=_DEVICE_UUID, ip_address=dummy_ip
        )
        mocker.patch(
            "app.routers.control.control_api.agent_control.ControlTargetAgent",
            return_value=mock_agent,
        )
        mocker.patch(
            "app.routers.control.control_api.control_base.PowerControlTargetDevice",
            return_value=control_base.PowerControlTargetDevice.model_construct(device_id=_DEVICE_UUID),
        )
        mocker.patch(
            "app.routers.control.control_api.agent_control.AgentController.is_os_ready",
            return_value=True,
        )

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.get(_IS_OS_READY_URL)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 200
        body = response.json()
        assert body == {"status": True, "IPAddress": dummy_ip}

    def test_device_aggregation_control_success_response(self, test_client: TestClient, mocker: MockFixture):
        """Successful Device Aggregation Control response contains 'sourceDeviceID'
        and 'destinationDeviceID' matching the request."""
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        mocker.patch.object(fm_control.FMControlTargetDevice, "model_post_init", return_value=None)
        mocker.patch(
            "app.routers.control.control_api._get_true_device_ids",
            return_value=(_DEVICE_UUID, _DOWNSTREAM_DEVICE_UUID),
        )
        mocker.patch.object(fm_control.FMController, "connect", return_value=None)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        response = test_client.put(
            _AGGREGATION_URL,
            json={"destinationDeviceID": _DOWNSTREAM_DEVICE_UUID, "action": "connect"},
        )

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert response.status_code == 200
        body = response.json()
        assert body == {"sourceDeviceID": _DEVICE_UUID, "destinationDeviceID": _DOWNSTREAM_DEVICE_UUID}

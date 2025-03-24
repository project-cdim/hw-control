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

"""Define API metadata of hw-control."""

DEVICE_CONTROL_API = "Device Control API"
DEVICE_CONTROL_API_TAG = {
    "name": DEVICE_CONTROL_API,
    "description": (
        "This API provides endpoints for changing the configuration of a node by controlling the link state between"
        " the host CPU and the target device. It also controls the power state of each device."
    ),
}

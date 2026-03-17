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

"""Classes that inherit ControlObjectHWControlError

file path: /app/common/basic_exceptions/control_object_exceptions.py

This module defines an exception class that inherits from the
ControlObjectHWControlError class.
The exception classes defined in this module are as follows.

FMConnectFailureHWControlError
FMDisconnectFailureHWControlError
PowerOnFailureHWControlError
PowerOffFailureHWControlError
CPUResetFailureHWControlError
AgentConnectFailureHWControlError
AgentGetInformationFailureHWControlError

"""

from app.common.basic_exceptions.base_exceptions import ControlObjectHWControlError


class FMConnectFailureHWControlError(ControlObjectHWControlError):
    """HwControl FM Connect Failure Error Detail Exception class

    This class is common detail exception class for HwControl defined
    exceptions of Connect Failure in FM.

    """

    error_code = "EF004BAS001"
    default_error_message: str = (
        "The Fabric Manager failed to establish a connection "
        "between the specified source device and the destination device."
    )


class FMDisconnectFailureHWControlError(ControlObjectHWControlError):
    """HwControl FM Disconnect Failure Error Detail Exception class

    This class is common detail exception class for HwControl defined
    exceptions of Disconnect Failure in FM.

    """

    error_code = "EF004BAS002"
    default_error_message: str = (
        "The Fabric Manager failed to disconnect a connection "
        "between the specified source device and the destination device."
    )


class PowerOnFailureHWControlError(ControlObjectHWControlError):
    """HwControl defined OOB Power On Failure Error Detail Exception class.

    This class is common HwControl defined detail exception class
    for when device power on Failure in OOB.

    """

    error_code = "EF004BAS003"
    default_error_message: str = "The Out-of-Band Controller failed to power on the specified device."


class PowerOffFailureHWControlError(ControlObjectHWControlError):
    """HwControl defined OOB Power Off Failure Error Detail Exception class.

    This class is common HwControl defined detail exception class
    for when device power off Failure in OOB.

    """

    error_code = "EF004BAS004"
    default_error_message: str = "The Out-of-Band Controller failed to power off the specified device."


class CPUResetFailureHWControlError(ControlObjectHWControlError):
    """HwControl defined OOB CpuReset Failure Error Detail Exception class.

    This class is common HwControl defined detail exception class
    for when CpuReset Failure in OOB.

    """

    error_code = "EF004BAS005"
    default_error_message: str = "The Out-of-Band Controller failed to reset the specified Host CPU."


class AgentConnectFailureHWControlError(ControlObjectHWControlError):
    """HwControl Agent Connect Failure Error Detail Exception class

    This class is common detail exception class for HwControl defined
    exceptions of Connect Failure in Agent.

    """

    error_code = "EF004BAS006"
    default_error_message: str = "Failed to connect to the HW Control Agent."


class AgentGetInformationFailureHWControlError(ControlObjectHWControlError):
    """HwControl Agent Get Information Failure Error Detail Exception class

    This class is common detail exception class for HwControl defined
    exceptions of Get Information Failure in Agent.

    """

    error_code = "EF004BAS007"
    default_error_message: str = "The HW Control Agent failed to get information from the Host OS."

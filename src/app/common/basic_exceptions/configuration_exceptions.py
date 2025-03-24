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
This module defines an exception class that inherits from the 
ConfigurationHwControlError class.
The exception classes defined in this module are as follows.

ApiUsageHwControlError
ManagerIdHwControlError
PluginGetInstanceHwControlError
PluginRespondUnExpectedTypeHwControlError
InvalidSerialNumberConfigFileNotFoundHwControlError
InvalidSerialNumberConfigFileIncorrectHwControlError
DeviceIdFileNotFoundHwControlError
DeviceIdFileIncorrectHwControlError
DeviceIdFileUpdateHwControlError
InvalidTypeDeviceIdHwControlError
InvalidDeviceTypeParameterHwControlError
InvalidLogMessageParameterHwControlError
PluginRespondNoneHwControlError

"""

from app.common.basic_exceptions.base_exceptions import ConfigurationHwControlError


class ApiUsageHwControlError(ConfigurationHwControlError):
    """API usage Error Case Exception class
    This class is common detail exception class for HwControl
    defined exceptions of API usage Error.
    """

    error_code = "EF007BAS002"
    default_error_message: str = "The specified argument is invalid."


class ManagerIdHwControlError(ConfigurationHwControlError):
    """Manager ID Error Case Exception class
    This class is common detail exception class for HwControl
    defined exceptions of Manager ID Error.
    """

    error_code = "EF007BAS003"
    default_error_message: str = "The specified Manager ID is invalid."


class PluginGetInstanceHwControlError(ConfigurationHwControlError):
    """No MethodError Error Case Exception class
    This class is common detail exception class for HwControl
    defined exceptions of getting instance error.
    """

    error_code = "EF007BAS006"
    default_error_message: str = "Failed to get the Plugin class instance."


class PluginRespondUnExpectedTypeHwControlError(ConfigurationHwControlError):
    """HwControl Configuration Error Exception class
    Class for  HwControl defined exceptions of Plugin Respond Un Expected Type Error.
    """

    error_code = "EF007BAS007"
    default_error_message: str = "The Plugin returned invalid type data."


class InvalidSerialNumberConfigFileNotFoundHwControlError(ConfigurationHwControlError):
    """Not Found json file(Invalid Serial Number list file) Error Case Exception class
    This class is common detail exception class for HwControl
    defined exceptions of finding json file(Invalid Serial Number list file).
    """

    error_code = "EF007BAS008"
    default_error_message: str = "The Invalid Serial Number List File is not found."


class InvalidSerialNumberConfigFileIncorrectHwControlError(ConfigurationHwControlError):
    """Json file(Invalid Serial Number list file) Error Case Exception class
    This class is common detail exception class for HwControl
    defined exceptions of json file setting error.
    """

    error_code = "EF007BAS009"
    default_error_message: str = "The Invalid Serial Number List File is incorrect."


class DeviceIdFileNotFoundHwControlError(ConfigurationHwControlError):
    """Not Found json file(Device ID manager file) Error Case Exception class
    This class is common detail exception class for HwControl
    defined exceptions of finding json file(Device ID manager file).
    """

    error_code = "EF007BAS010"
    default_error_message: str = "The Device ID Management File is not found."


class DeviceIdFileIncorrectHwControlError(ConfigurationHwControlError):
    """Json file(Device ID manager file) Error Case Exception class
    This class is common detail exception class for HwControl
    defined exceptions of json file setting error.
    """

    error_code = "EF007BAS011"
    default_error_message: str = "The Device ID Management File is incorrect."


class DeviceIdFileUpdateHwControlError(ConfigurationHwControlError):
    """No MethodError Error Case Exception class
    This class is common detail exception class for HwControl
    defined exceptions of updating Device ID Management File.
    """

    error_code = "EF007BAS012"
    default_error_message: str = "Failed to update the Device ID Management File."


class InvalidTypeDeviceIdHwControlError(ConfigurationHwControlError):
    """Invalid Type Device ID Error Case Exception class
    This class is common detail exception class for HwControl
    defined exceptions of invalid Type Device ID.
    """

    error_code = "EF007BAS015"
    default_error_message: str = "An unexpected type device was specified."


class InvalidDeviceTypeParameterHwControlError(ConfigurationHwControlError):
    """HwControl Configuration Error Exception class
    Class for  HwControl defined exceptions of Invalid Device Type Parameter Error.
    """

    error_code = "EF007BAS016"
    default_error_message: str = "The specified Device Type is invalid."


class InvalidLogMessageParameterHwControlError(ConfigurationHwControlError):
    """HwControl Configuration Error Exception class
    Class for  HwControl defined exceptions of Invalid Log Message Parameter Error.
    """

    error_code = "EF007BAS017"
    default_error_message: str = "An invalid argument was specified to 'get_log_message' function."


class PluginRespondNoneHwControlError(ConfigurationHwControlError):
    """HwControl Configuration Error Exception class
    Class for  HwControl defined exceptions of Plugin Respond None Error.
    """

    error_code = "EF007BAS018"
    default_error_message: str = "The Plugin returned None."

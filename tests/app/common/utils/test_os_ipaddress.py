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

"""UT test module

UT of app/common/utils/os_ipaddress.py
"""

import logging
import uuid
import yaml

from pytest import MonkeyPatch, LogCaptureFixture
from pytest_mock import MockFixture

import app.common.basic_exceptions as exc
from app.common.dim import device_id_base

# ++++ system under test ++++++++++++++++++++++++++++++++++++++++++++#
from app.common.utils import os_ipaddress

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++#


def mock_safe_load(file: str, encoding: str | None = None) -> dict:
    """
    Mock : safe_load
    """
    response = {
        "OS_IPAddress": [
            {
                # device_id : 00000001-0001-0001-0001-000000000001
                "fmPortID": "49951897-c615-43a5-a125-ad63266fd8c6",
                "IPAddress": "192.168.122.11",
            },
            {
                # device_id : 00000002-0002-0002-0002-000000000002
                "fmPortID": "6bfcd16b-76c8-4dbc-ac56-3da1d008f15d",
                "IPAddress": "192.168.122.12",
            },
            {
                # device_id : 00000003-0003-0003-0003-000000000003
                "fmPortID": "072fcd71-7137-454f-a678-aea4eaf54732",
                "IPAddress": "192.168.122.13",
            },
        ]
    }
    return response


def mock_device_id_to_fm_port_id(device_id: str) -> str | None:
    """
    Mock : device_id_to_fm_port_id
    """
    # Check the format of the UUID.
    # In case of an error, ValueError or AttributeError exceptions will occur.
    uuid.UUID(device_id, version=4)

    if device_id == "00000001-0001-0001-0001-000000000001":
        return "49951897-c615-43a5-a125-ad63266fd8c6"
    if device_id == "00000002-0002-0002-0002-000000000002":
        return "6bfcd16b-76c8-4dbc-ac56-3da1d008f15d"
    if device_id == "00000003-0003-0003-0003-000000000003":
        return "072fcd71-7137-454f-a678-aea4eaf54732"
    return ""


class TestOSIPAddress:
    """
    Test Class for os_ip_address module
    """

    def test_get_os_ipaddress_cpu1(self, mocker: MockFixture):
        """
        get_os_ipaddress test
        get cpu1 ipaddress(use os_ipaddress.yaml)

        """
        # preparations
        cpu_device_id = "00000001-0001-0001-0001-000000000001"
        expected_response = ("192.168.122.11", True)
        mocker.patch("builtins.open")
        mocker.patch.object(yaml, "safe_load", side_effect=mock_safe_load)
        mocker.patch.object(device_id_base, "device_id_to_fm_port_id", side_effect=mock_device_id_to_fm_port_id)

        # test run
        actual = os_ipaddress.get_os_ipaddress(cpu_device_id)

        # verification
        assert expected_response == actual

    def test_get_os_ipaddress_cpu2(self, mocker: MockFixture):
        """
        get_os_ipaddress test
        get cpu2 ipaddress(use os_ipaddress.yaml)

        """

        # preparations
        cpu_device_id = "00000002-0002-0002-0002-000000000002"
        expected_response = ("192.168.122.12", True)
        mocker.patch("builtins.open")
        mocker.patch.object(yaml, "safe_load", side_effect=mock_safe_load)
        mocker.patch.object(device_id_base, "device_id_to_fm_port_id", side_effect=mock_device_id_to_fm_port_id)

        # test run
        actual = os_ipaddress.get_os_ipaddress(cpu_device_id)

        # verification
        assert expected_response == actual

    def test_get_os_ipaddress_cpu_notfound(self, mocker: MockFixture):
        """
        get_os_ipaddress test
        cpu not found (use os_ipaddress.yaml)

        """
        # preparations
        cpu_device_id = "00000099-0099-0099-0099-000000000099"
        expected_response = (None, False)
        mocker.patch("builtins.open")
        mocker.patch.object(yaml, "safe_load", side_effect=mock_safe_load)
        mocker.patch.object(device_id_base, "device_id_to_fm_port_id", side_effect=mock_device_id_to_fm_port_id)

        # test run
        actual = os_ipaddress.get_os_ipaddress(cpu_device_id)

        # verification
        assert expected_response == actual

    def test_get_os_ipaddress_except_yaml_error(self, mocker: MockFixture):
        """
        get_os_ipaddress test
        cpu not found (use os_ipaddress.yaml)

        """
        # preparations
        cpu_device_id = "00000001-0001-0001-0001-000000000001"
        expected_response = (None, False)
        mocker.patch("builtins.open")
        mocker.patch.object(yaml, "safe_load", side_effect=yaml.YAMLError)
        mocker.patch.object(device_id_base, "device_id_to_fm_port_id", side_effect=mock_device_id_to_fm_port_id)

        # test run
        actual = os_ipaddress.get_os_ipaddress(cpu_device_id)

        # verification
        assert expected_response == actual

    def test_get_os_ipaddress_except_attributeerror(self, mocker: MockFixture):
        """
        get_os_ipaddress test
        cpu not found (use os_ipaddress.yaml)

        """
        # preparations
        cpu_device_id = "00000001-0001-0001-0001-000000000001"
        expected_response = (None, False)
        mocker.patch("builtins.open")
        mocker.patch.object(yaml, "safe_load", side_effect=AttributeError)
        mocker.patch.object(device_id_base, "device_id_to_fm_port_id", side_effect=mock_device_id_to_fm_port_id)

        # test run
        actual = os_ipaddress.get_os_ipaddress(cpu_device_id)

        # verification
        assert expected_response == actual

    def test_get_os_ipaddress_except_keyerror1(self, mocker: MockFixture):
        """
        get_os_ipaddress test
        except KeyError (OS_IPAddress)

        """

        def mock_safe_load_keyerror(file: str, encoding: str | None = None) -> dict:
            """
            mock_safe_load_keyerror
                KeyError in yaml file data(TEST_OS_IPAddress)

            """
            response = {
                "TEST_OS_IPAddress": [
                    {
                        # device_id : 00000001-0001-0001-0001-000000000001
                        "fmPortID": "49951897-c615-43a5-a125-ad63266fd8c6",
                        "IPAddress": "192.168.122.11",
                    }
                ]
            }
            return response

        # preparations
        cpu_device_id = "00000001-0001-0001-0001-000000000001"
        expected_response = (None, False)
        mocker.patch("builtins.open")
        mocker.patch.object(yaml, "safe_load", side_effect=mock_safe_load_keyerror)
        mocker.patch.object(device_id_base, "device_id_to_fm_port_id", side_effect=mock_device_id_to_fm_port_id)

        # test run
        actual = os_ipaddress.get_os_ipaddress(cpu_device_id)

        # verification
        assert expected_response == actual

    def test_get_os_ipaddress_except_keyerror2(self, mocker: MockFixture):
        """
        get_os_ipaddress test
        except KeyError (fmPortID)

        """

        def mock_safe_load_keyerror(file: str, encoding: str | None = None) -> dict:
            """
            mock_safe_load_keyerror
                KeyError in yaml file data(TEST_fmPortID)

            """
            response = {
                "OS_IPAddress": [
                    {
                        # device_id : 00000001-0001-0001-0001-000000000001
                        "TEST_fmPortID": "49951897-c615-43a5-a125-ad63266fd8c6",
                        "IPAddress": "192.168.122.11",
                    }
                ]
            }
            return response

        # preparations
        cpu_device_id = "00000001-0001-0001-0001-000000000001"
        expected_response = (None, False)
        mocker.patch("builtins.open")
        mocker.patch.object(yaml, "safe_load", side_effect=mock_safe_load_keyerror)
        mocker.patch.object(device_id_base, "device_id_to_fm_port_id", side_effect=mock_device_id_to_fm_port_id)

        # test run
        actual = os_ipaddress.get_os_ipaddress(cpu_device_id)

        # verification
        assert expected_response == actual

    def test_get_os_ipaddress_except_keyerror3(self, mocker: MockFixture):
        """
        get_os_ipaddress test
        except KeyError (IPAddress)

        """

        def mock_safe_load_keyerror(file: str, encoding: str | None = None) -> dict:
            """
            mock_safe_load_keyerror
                KeyError in yaml file data(TEST_IPAddress)

            """
            response = {
                "OS_IPAddress": [
                    {
                        # device_id : 00000001-0001-0001-0001-000000000001
                        "fmPortID": "49951897-c615-43a5-a125-ad63266fd8c6",
                        "TEST_IPAddress": "192.168.122.11",
                    }
                ]
            }
            return response

        # preparations
        cpu_device_id = "00000001-0001-0001-0001-000000000001"
        expected_response = (None, False)
        mocker.patch("builtins.open")
        mocker.patch.object(yaml, "safe_load", side_effect=mock_safe_load_keyerror)
        mocker.patch.object(device_id_base, "device_id_to_fm_port_id", side_effect=mock_device_id_to_fm_port_id)

        # test run
        actual = os_ipaddress.get_os_ipaddress(cpu_device_id)

        # verification
        assert expected_response == actual

    def test_get_os_ipaddress_except_file_not_found(self, mocker: MockFixture):
        """
        get_os_ipaddress test
        except FileNotFoundError (os_ipaddress.yaml)

        """

        # preparations
        cpu_device_id = "00000001-0001-0001-0001-000000000001"
        expected_response = (None, False)
        mocker.patch("builtins.open", side_effect=FileNotFoundError)
        mocker.patch.object(device_id_base, "device_id_to_fm_port_id", side_effect=mock_device_id_to_fm_port_id)

        # test run
        actual = os_ipaddress.get_os_ipaddress(cpu_device_id)

        # verification
        assert expected_response == actual

    def test_get_os_ipaddress_except_device_id_notfound(self, mocker: MockFixture):
        """
        get_os_ipaddress test
        except DeviceIDNotFoundHWControlError

        """
        # preparations
        cpu_device_id = "00000001-0001-0001-0001-000000000001"
        expected_response = (None, False)
        mocker.patch("builtins.open")
        mocker.patch.object(yaml, "safe_load", side_effect=mock_safe_load)
        mocker.patch.object(device_id_base, "device_id_to_fm_port_id", side_effect=exc.DeviceIDNotFoundHWControlError)

        # test run
        actual = os_ipaddress.get_os_ipaddress(cpu_device_id)

        # verification
        assert expected_response == actual

    def test_get_os_ipaddress_except_device_id_file_incorrect(self, mocker: MockFixture):
        """
        get_os_ipaddress test
        except DeviceIDFileIncorrectHWControlError

        """
        # preparations
        cpu_device_id = "00000001-0001-0001-0001-000000000001"
        expected_response = (None, False)
        mocker.patch("builtins.open")
        mocker.patch.object(yaml, "safe_load", side_effect=mock_safe_load)
        mocker.patch.object(
            device_id_base, "device_id_to_fm_port_id", side_effect=exc.DeviceIDFileIncorrectHWControlError
        )

        # test run
        actual = os_ipaddress.get_os_ipaddress(cpu_device_id)

        # verification
        assert expected_response == actual

    def test_get_os_ipaddress_except_device_id_file_notfound(self, mocker: MockFixture):
        """
        get_os_ipaddress test
        except DeviceIDFileNotFoundHWControlError

        """
        # preparations
        cpu_device_id = "00000001-0001-0001-0001-000000000001"
        expected_response = (None, False)
        mocker.patch("builtins.open")
        mocker.patch.object(yaml, "safe_load", side_effect=mock_safe_load)
        mocker.patch.object(
            device_id_base, "device_id_to_fm_port_id", side_effect=exc.DeviceIDFileNotFoundHWControlError
        )

        # test run
        actual = os_ipaddress.get_os_ipaddress(cpu_device_id)

        # verification
        assert expected_response == actual

    def test_get_os_ipaddress_output_debug_log(
        self, mocker: MockFixture, caplog: LogCaptureFixture, monkeypatch: MonkeyPatch
    ):
        """
        get_os_ipaddress test
        logging path of os_ipaddress.yaml

        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        cpu_device_id = "00000001-0001-0001-0001-000000000001"

        mocker.patch("builtins.open")
        mocker.patch.object(yaml, "safe_load", side_effect=mock_safe_load)
        mocker.patch.object(device_id_base, "device_id_to_fm_port_id", side_effect=mock_device_id_to_fm_port_id)

        monkeypatch.delenv("HW_CONTROL_CONFIG_FILE_DIR", raising=False)

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.DEBUG, logger=os_ipaddress.__name__):
            os_ipaddress.get_os_ipaddress(cpu_device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        # Inspection: Check the error debug log.
        error_debug_log = caplog.records[-1]
        assert error_debug_log.levelname == "DEBUG"
        assert error_debug_log.getMessage() == "[get_os_ipaddress] config_file_dir=/opt/cdim/hw-control/config/"

    def test_get_os_ipaddress_output_debug_log_with_env(
        self, mocker: MockFixture, caplog: LogCaptureFixture, monkeypatch: MonkeyPatch
    ):
        """
        get_os_ipaddress test
        logging path of os_ipaddress.yaml with environment variable

        """
        # ++++ preparation ++++++++++++++++++++++++++++++++++++++++++++#
        cpu_device_id = "00000001-0001-0001-0001-000000000001"

        mocker.patch("builtins.open")
        mocker.patch.object(yaml, "safe_load", side_effect=mock_safe_load)
        mocker.patch.object(device_id_base, "device_id_to_fm_port_id", side_effect=mock_device_id_to_fm_port_id)

        monkeypatch.setenv("HW_CONTROL_CONFIG_FILE_DIR", "/dev/null")

        # ++++ execution ++++++++++++++++++++++++++++++++++++++++++++++#
        caplog.clear()
        with caplog.at_level(logging.DEBUG, logger=os_ipaddress.__name__):
            os_ipaddress.get_os_ipaddress(cpu_device_id)

        # ++++ inspection +++++++++++++++++++++++++++++++++++++++++++++#
        assert len(caplog.records) == 1

        # Inspection: Check the error debug log.
        error_debug_log = caplog.records[-1]
        assert error_debug_log.levelname == "DEBUG"
        assert error_debug_log.getMessage() == "[get_os_ipaddress] config_file_dir=/dev/null"

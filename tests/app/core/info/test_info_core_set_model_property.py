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

"""This is a test program."""

from app.core.info.info_core import InformationCore

# RESP storage driveModel not exist
RESP_STORAGE_DRIVE_MODEL_NOT_EXIST_IN_OUT = {"deviceID": "2001", "type": "storage"}

# RESP storage driveModel is None
RESP_STORAGE_DRIVE_MODEL_IS_NONE_IN_OUT = {"deviceID": "2001", "type": "storage", "driveModel": None}

# RESP storage driveModel is Empty
RESP_STORAGE_DRIVE_MODEL_IS_EMPTY_IN_OUT = {"deviceID": "2001", "type": "storage", "driveModel": ""}

# RESP storage driveModel is Whitespace
RESP_STORAGE_DRIVE_MODEL_IS_WHITESPACE_IN_OUT = {"deviceID": "2001", "type": "storage", "driveModel": "   "}

# RESP storage driveModel exist input
RESP_STORAGE_DRIVE_MODEL_EXIST_IN = {"deviceID": "2001", "type": "storage", "driveModel": "C123"}

# RESP storage driveModel exist output
RESP_STORAGE_DRIVE_MODEL_EXIST_OUT = {"deviceID": "2001", "type": "storage", "driveModel": "C123", "model": "C123"}

# RESP NIC networkAdapterModel fabricAdapterModel not exist input output
RESP_NIC_NETWORK_FABRIC_NOT_EXIST_IN_OUT = {"deviceID": "3001", "type": "networkInterface"}

# RESP NIC networkAdapterModel not exist input
RESP_NIC_NETWORK_NOT_EXIST_IN = {"deviceID": "3001", "type": "networkInterface", "fabricAdapterModel": "FABRIC-T"}

# RESP NIC networkAdapterModel not exist output
RESP_NIC_NETWORK_NOT_EXIST_OUT = {
    "deviceID": "3001",
    "type": "networkInterface",
    "fabricAdapterModel": "FABRIC-T",
    "model": "FABRIC-T",
}

# RESP NIC fabricAdapterModel not exist input
RESP_NIC_FABRIC_NOT_EXIST_IN = {"deviceID": "3001", "type": "networkInterface", "networkAdapterModel": "NETWORK-T"}

# RESP NIC fabricAdapterModel not exist output
RESP_NIC_FABRIC_NOT_EXIST_OUT = {
    "deviceID": "3001",
    "type": "networkInterface",
    "networkAdapterModel": "NETWORK-T",
    "model": "NETWORK-T",
}

# RESP NIC networkAdapterModel fabricAdapterModel exist input
RESP_NIC_NETWORK_FABRIC_EXIST_IN = {
    "deviceID": "3001",
    "type": "networkInterface",
    "networkAdapterModel": "NETWORK-T",
    "fabricAdapterModel": "FABRIC-T",
}

# RESP NIC networkAdapterModel fabricAdapterModel exist output
RESP_NIC_NETWORK_FABRIC_EXIST_OUT = {
    "deviceID": "3001",
    "type": "networkInterface",
    "networkAdapterModel": "NETWORK-T",
    "fabricAdapterModel": "FABRIC-T",
    "model": "NETWORK-T",
}

# RESP CPU input output
RESP_CPU_IN_OUT = {"deviceID": "0001", "type": "CPU"}

# RESP Device Type not exist
RESP_DEVICE_TYPE_NOT_EXIST_IN_OUT = {"deviceID": "0001"}


def test_drive_model_not_exist():
    """Test storage driveModel not exist"""
    get_information = InformationCore()
    resp = RESP_STORAGE_DRIVE_MODEL_NOT_EXIST_IN_OUT
    get_information._set_model_property(resp)  # pylint: disable=protected-access
    assert resp == RESP_STORAGE_DRIVE_MODEL_NOT_EXIST_IN_OUT


def test_drive_model_none():
    """Test storage driveModel is None"""
    get_information = InformationCore()
    resp = RESP_STORAGE_DRIVE_MODEL_IS_NONE_IN_OUT
    get_information._set_model_property(resp)  # pylint: disable=protected-access
    assert resp == RESP_STORAGE_DRIVE_MODEL_IS_NONE_IN_OUT


def test_drive_model_empty():
    """Test storage driveModel is Empty"""
    get_information = InformationCore()
    resp = RESP_STORAGE_DRIVE_MODEL_IS_EMPTY_IN_OUT
    get_information._set_model_property(resp)  # pylint: disable=protected-access
    assert resp == RESP_STORAGE_DRIVE_MODEL_IS_EMPTY_IN_OUT


def test_drive_model_whitespace():
    """Test storage driveModel is Whitespace"""
    get_information = InformationCore()
    resp = RESP_STORAGE_DRIVE_MODEL_IS_WHITESPACE_IN_OUT
    get_information._set_model_property(resp)  # pylint: disable=protected-access
    assert resp == RESP_STORAGE_DRIVE_MODEL_IS_WHITESPACE_IN_OUT


def test_drive_model_exist():
    """Test storage driveModel exist"""
    get_information = InformationCore()
    resp = RESP_STORAGE_DRIVE_MODEL_EXIST_IN
    get_information._set_model_property(resp)  # pylint: disable=protected-access
    assert resp == RESP_STORAGE_DRIVE_MODEL_EXIST_OUT


def test_network_fabric_not_exist():
    """Test NIC networkAdapterModel fabricAdapterModel not exist"""
    get_information = InformationCore()
    resp = RESP_NIC_NETWORK_FABRIC_NOT_EXIST_IN_OUT
    get_information._set_model_property(resp)  # pylint: disable=protected-access
    assert resp == RESP_NIC_NETWORK_FABRIC_NOT_EXIST_IN_OUT


def test_network_not_exist():
    """Test NIC networkAdapterModel not exist"""
    get_information = InformationCore()
    resp = RESP_NIC_NETWORK_NOT_EXIST_IN
    get_information._set_model_property(resp)  # pylint: disable=protected-access
    assert resp == RESP_NIC_NETWORK_NOT_EXIST_OUT


def test_fabric_not_exist():
    """Test NIC fabricAdapterModel not exist"""
    get_information = InformationCore()
    resp = RESP_NIC_FABRIC_NOT_EXIST_IN
    get_information._set_model_property(resp)  # pylint: disable=protected-access
    assert resp == RESP_NIC_FABRIC_NOT_EXIST_OUT


def test_network_fabric_exist():
    """Test NIC networkAdapterModel fabricAdapterModel exist"""
    get_information = InformationCore()
    resp = RESP_NIC_NETWORK_FABRIC_EXIST_IN
    get_information._set_model_property(resp)  # pylint: disable=protected-access
    assert resp == RESP_NIC_NETWORK_FABRIC_EXIST_OUT


def test_other_device_type():
    """Test other Device Type"""
    get_information = InformationCore()
    resp = RESP_CPU_IN_OUT
    get_information._set_model_property(resp)  # pylint: disable=protected-access
    assert resp == RESP_CPU_IN_OUT


def test_device_type_not_exist():
    """Test Device Type not exist"""
    get_information = InformationCore()
    resp = RESP_DEVICE_TYPE_NOT_EXIST_IN_OUT
    get_information._set_model_property(resp)  # pylint: disable=protected-access
    assert resp == RESP_DEVICE_TYPE_NOT_EXIST_IN_OUT


def test_resp_is_none():
    """Test when response is None"""
    get_information = InformationCore()
    resp = None
    get_information._set_model_property(resp)  # pylint: disable=protected-access # type: ignore[protected-access]
    assert resp is None

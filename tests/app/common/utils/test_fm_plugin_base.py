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

"""
Test program for app/common/utils/fm_plugin_base.py
"""

from unittest import TestCase

import pytest
from pydantic import ValidationError

from app.common.utils.fm_plugin_base import FMPluginBase, FMPortData, FMSwitchData


class FMPortDataTests(TestCase):
    """Test FMPortData class"""

    default: dict = {"id": "sample_id"}

    def _check_none_member(self, key_name: str, member: str):
        """Test that the FMPortData's member can be set None."""
        for value in [self.default, self.default | {key_name: None}]:
            fpd = FMPortData(**value)
            assert getattr(fpd, member) is None

    def _check_condition_member(self, key_name: str, member: str, allows: list, denials: list):
        """Test that the FMPortData's member can set allows items, can not set denials items."""
        for value in allows:
            fpd = FMPortData(**{"id": "sample_id", key_name: value})
            assert value == getattr(fpd, member)

            fpd = FMPortData(**self.default)
            setattr(fpd, member, value)
            assert value == getattr(fpd, member)

        for value in denials:
            with pytest.raises(ValidationError):
                FMPortData(**{"id": "sample_id", key_name: value})

            fpd = FMPortData(**self.default)
            with pytest.raises(ValidationError):
                setattr(fpd, member, value)

    def _check_none_or_condition_member(self, key_name: str, member: str, allows: list, denials: list):
        """Test that the FMPortData's member can set allows items or None,
        can not set denials items.
        """
        self._check_none_member(key_name, member)
        self._check_condition_member(key_name, member, allows, denials)

    def _check_none_or_string_member(self, key_name: str, member: str):
        """Test that the FMPortData's member can only be set to string or None."""
        self._check_none_or_condition_member(key_name, member, ["sample"], [1, ["data1", "data2"], {}])

    def _check_none_or_literal_member(self, key_name: str, member: str, allows: list):
        """Test that the FMPortData's member can only be set to literal or None."""
        self._check_none_or_condition_member(key_name, member, allows, ["Not Allow", 0, [], {"key": "value"}])

    def _check_dictionary_member(self, key_name: str, member: str):
        """Test that the FMPortData's member can only be set to dictionary."""
        fpd = FMPortData(**self.default)
        assert {} == getattr(fpd, member)
        allows: list = [{}, {"key": "value"}, {"key1": "value1", "key2": 2}]
        denials: list = [None, [], "string"]
        self._check_condition_member(key_name, member, allows, denials)

    def test_id(self):
        """Validation test of id in FMPortData class"""
        fpd = FMPortData(**self.default)
        assert "sample_id" == fpd.id
        for value in [{}, {"id": None}]:
            with pytest.raises(ValidationError):
                FMPortData(**value)

    def test_switch_id(self):
        """Validation test of switchId in FMPortData class"""
        self._check_none_or_string_member("switchId", "switch_id")

    def test_switch_port_number(self):
        """Validation test of switchPortNumber in FMPortData class"""
        self._check_none_or_string_member("switchPortNumber", "switch_port_number")

    def test_switch_port_type(self):
        """Validation test of switchPortType in FMPortData class"""
        self._check_none_or_literal_member("switchPortType", "switch_port_type", ["USP", "DSP"])

    def test_fabric_id(self):
        """Validation test of fabricId in FMPortData class"""
        self._check_none_or_string_member("fabricId", "fabric_id")

    def test_link(self):
        """Validation test of link in FMPortData class"""
        allows = [[], ["id"], ["id1", "id2"]]
        denials = ["string", ["id1", "id2", None], [1, 2]]
        self._check_none_or_condition_member("link", "link", allows, denials)

    def test_device_type(self):
        """Validation test of deviceType in FMPortData class"""
        allows = ["CXL-Type1", "CXL-Type2", "CXL-Type3", "CXL-Type3-MLD", "PCIe", "Undetected", "Other", "Unknown"]
        self._check_none_or_literal_member("deviceType", "device_type", allows)

    def test_pci_class_code(self):
        """Validation test of PCIClassCode in FMPortData class"""
        sample = {"base": 0, "sub": 1, "prog": 0xFF}
        fpd = FMPortData(**self.default)
        assert fpd.pci_class_code is None
        fpd = FMPortData(**{"id": "sample", "PCIClassCode": None})
        assert fpd.pci_class_code is None
        fpd.pci_class_code = sample
        assert sample == fpd.pci_class_code
        fpd = FMPortData(**{"id": "dummy", "PCIClassCode": sample})
        assert sample == fpd.pci_class_code
        for data in [
            "string",
            1,
            {},
            {"base": 0, "sub": 0, "xxx": 0},
            {"base": 0x100, "sub": 0, "prog": 0},
            {"base": 0, "sub": -1, "prog": 0},
            {"base": 0, "sub": 0, "prog": 0, "other": 0},
            {"base": 0, "prog": 0},
        ]:
            with pytest.raises(ValidationError):
                FMPortData(**{"id": "sample", "PCIClassCode": data})

            fpd = FMPortData(**self.default)
            with pytest.raises(ValidationError):
                fpd.pci_class_code = data

    def test_pcie_vendor_id(self):
        """Validation test of PCIeVendorId in FMPortData class"""
        allows = ["0000", "0123", "4567", "89ab", "cdef", "ABCD", "EF12", "FFFF", "ffff"]
        denials = [-1, 0, 0xFFFF, "00000", "000", "defg"]
        self._check_none_or_condition_member("PCIeVendorId", "pcie_vendor_id", allows, denials)

    def test_pcie_device_id(self):
        """Validation test of PCIeDeviceId in FMPortData class"""
        allows = ["0000", "0123", "4567", "89ab", "cdef", "ABCD", "EF12", "FFFF", "ffff"]
        denials = [-1, 0, 0xFFFF, "00000", "000", "defg"]
        self._check_none_or_condition_member("PCIeDeviceId", "pcie_device_id", allows, denials)

    def test_pcie_device_serial_number(self):
        """Validation test of PCIeDeviceSerialNumber in FMPortData class"""
        allows = ["0000000000000000", "0123456789abcdef", "FEDCBA9876543210", "FFFFFFFFFFFFFFFF"]
        denials = ["000000000000000", "00000000000000000", "123456789ABCDEFG"]
        self._check_none_or_condition_member("PCIeDeviceSerialNumber", "pcie_device_serial_number", allows, denials)

    def test_cpu_manufacturer(self):
        """Validation test of CPUManufacturer in FMPortData class"""
        self._check_none_or_string_member("CPUManufacturer", "cpu_manufacturer")

    def test_cpu_model(self):
        """Validation test of CPUModel in FMPortData class"""
        self._check_none_or_string_member("CPUModel", "cpu_model")

    def test_cpu_serial_number(self):
        """Validation test of CPUSerialNumber in FMPortData class"""
        self._check_none_or_string_member("CPUSerialNumber", "cpu_serial_number")

    def test_ltssm_state(self):
        """Validation test of LTSSMState in FMPortData class"""
        allows = [
            "L0",
            "L0s",
            "L2",
            "Detect",
            "Polling",
            "Configuration",
            "Recovery",
            "HotReset",
            "Disable",
            "Loopback",
        ]
        self._check_none_or_literal_member("LTSSMState", "ltssm_state", allows)

    def test_device_keys(self):
        """Validation test of deviceKeys in FMPortData class"""
        self._check_dictionary_member("deviceKeys", "device_keys")

    def test_port_keys(self):
        """Validation test of portKeys in FMPortData class"""
        self._check_dictionary_member("portKeys", "port_keys")

    def test_capacity(self):
        """Validation test of capacity in FMPortData class"""
        fpd = FMPortData(**self.default)
        assert fpd.capacity is None
        fpd = FMPortData(**{"id": "sample_id", "capacity": None})
        assert fpd.capacity is None

        sample = {"volatile": 10, "persistent": 20, "total": 30}
        allows = []
        allows.append(({"volatile": 10}, {"volatile": 10, "persistent": 0, "total": 10}))
        allows.append(({"persistent": 20}, {"volatile": 0, "persistent": 20, "total": 20}))
        allows.append(({"volatile": 10, "persistent": 20}, sample))
        allows.append(({"volatile": 10, "total": 30}, sample))
        allows.append(({"persistent": 20, "total": 30}, sample))
        allows.append((sample, sample))
        for value, check in allows:
            fpd = FMPortData(**{"id": "dummy", "capacity": value})
            assert check == fpd.capacity

            fpd = FMPortData(**self.default)
            fpd.capacity = value
            assert check == fpd.capacity

        fpd = FMPortData(**{"id": "dummy", "capacity": sample})
        fpd.capacity["volatile"] = 0
        assert {"volatile": 0, "persistent": 20, "total": 30} == fpd.capacity

        for value in [
            "string",
            {},
            {"volatile": -1},
            {"volatile": "10"},
            {"total": 10},
            {"err": 10, "volatile": 10},
            {"volatile": 1, "persistent": 1, "total": 1},
            {"volatile": 10, "persistent": 10, "total": 20, "unknown": 1},
            {"volatile": 10, "persistent": 10, "unknown": 20},
            {"volatile": 100, "total": 10},
            {"persistent": 30, "total": 29},
        ]:
            with pytest.raises(ValidationError):
                FMPortData(**{"id": "dummy", "capacity": value})
            fpd = FMPortData(**self.default)
            with pytest.raises(ValidationError):
                fpd.capacity = value

    def _check_validation_error_without_none(self, data: dict, members: list):
        for member in members:
            data[member] = "dummy"
            with pytest.raises(ValidationError):
                FMPortData(**data)
            data[member] = None

    def test_validate_port_type_cpu_pcie(self):
        """Validation test of port type and cpu or pcie data"""
        data = {
            "id": "usp_dsp",
            "PCIeVendorId": "ffee",
            "PCIeDeviceId": "ddcc",
            "PCIeDeviceSerialNumber": "bbaa998877665544",
            "CPUManufacturer": "manufacturer",
            "CPUModel": "model",
            "CPUSerialNumber": "serial",
        }
        FMPortData(**data)
        usp = data | {"switchPortType": "USP"}
        with pytest.raises(ValidationError):
            FMPortData(**usp)
        dsp = data | {"switchPortType": "DSP"}
        with pytest.raises(ValidationError):
            FMPortData(**dsp)

        cpu_data = ["CPUManufacturer", "CPUModel", "CPUSerialNumber"]
        self._check_validation_error_without_none(usp, cpu_data)
        pcie_data = ["PCIeVendorId", "PCIeDeviceId", "PCIeDeviceSerialNumber"]
        self._check_validation_error_without_none(dsp, pcie_data)

    def test_exchange_to_dictionary(self):
        """Conversion test to dictionary, class dictionary"""
        data = {
            "id": "sample_id",
            "switchId": None,
            "switchPortNumber": None,
            "switchPortType": None,
            "fabricId": None,
            "link": None,
            "deviceType": None,
            "PCIClassCode": None,
            "PCIeVendorId": None,
            "PCIeDeviceId": None,
            "PCIeDeviceSerialNumber": None,
            "CPUManufacturer": None,
            "CPUModel": None,
            "CPUSerialNumber": None,
            "LTSSMState": None,
            "deviceKeys": {},
            "portKeys": {},
            "capacity": None,
        }
        assert data == FMPortData(**self.default).model_dump(by_alias=True)
        data = {
            "id": "exchange_id",
            "switchId": "switch-1",
            "switchPortNumber": "port-1",
            "switchPortType": "DSP",
            "fabricId": "switch-1-manufacturer-serial",
            "link": [],
            "deviceType": "PCIe",
            "PCIClassCode": {"base": 0x11, "sub": 0x22, "prog": 0x33},
            "PCIeVendorId": "4455",
            "PCIeDeviceId": "6677",
            "PCIeDeviceSerialNumber": "8899aAbBcCdDeEfF",
            "CPUManufacturer": None,
            "CPUModel": None,
            "CPUSerialNumber": None,
            "LTSSMState": "L0",
            "deviceKeys": {"device_key": "device_value"},
            "portKeys": {"port_key": "port_value"},
            "capacity": {"volatile": 1, "persistent": 2, "total": 3},
        }
        assert data == FMPortData(**data).model_dump(by_alias=True)


class FMSwitchDataTests(TestCase):
    """Test FMSwitchData class"""

    default: dict = {"switchId": "sample_id"}

    def _check_none_member(self, key_name: str, member: str):
        """Test that the FMSwitchData's member can be set None."""
        for value in [self.default, self.default | {key_name: None}]:
            fsd = FMSwitchData(**value)
            assert getattr(fsd, member) is None

    def _check_none_or_condition_member(self, key_name: str, member: str, allows: list, denials: list):
        """Test that the FMSwitchData's member can set allows items or None,
        can not set denials items.
        """
        self._check_none_member(key_name, member)
        for value in allows:
            fsd = FMSwitchData(**{"switchId": "sample_id", key_name: value})
            assert value == getattr(fsd, member)

            fsd = FMSwitchData(**self.default)
            setattr(fsd, member, value)
            assert value == getattr(fsd, member)

        for value in denials:
            with pytest.raises(ValidationError):
                FMSwitchData(**{"switchId": "sample_id", key_name: value})

            fsd = FMSwitchData(**self.default)
            with pytest.raises(ValidationError):
                setattr(fsd, member, value)

    def _check_none_or_string_member(self, key_name: str, member: str):
        """Test that the FMSwitchData's member can only be set to string or None."""
        self._check_none_or_condition_member(key_name, member, ["sample"], [1, []])

    def test_switch_id(self):
        """Validation test of switchId in FMSwitchData class"""
        fsd = FMSwitchData(**self.default)
        assert "sample_id" == fsd.switch_id
        for value in [{}, {"switchId": None}]:
            with pytest.raises(ValidationError):
                FMSwitchData(**value)

    def test_switch_manufacturer(self):
        """Validation test of switchManufacturer in FMSwitchData class"""
        self._check_none_or_string_member("switchManufacturer", "switch_manufacturer")

    def test_switch_model(self):
        """Validation test of switchModel in FMSwitchData class"""
        self._check_none_or_string_member("switchModel", "switch_model")

    def test_switch_serial_number(self):
        """Validation test of switchSerialNumber in FMSwitchData class"""
        self._check_none_or_string_member("switchSerialNumber", "switch_serial_number")

    def test_link(self):
        """Validation test of link in FMSwitchData class"""
        allows = [[], ["id"], ["id1", "id2"]]
        denials = ["string", ["id1", "id2", None], [1, 2]]
        self._check_none_or_condition_member("link", "link", allows, denials)

    def test_exchange_to_dictionary(self):
        """Conversion test to dictionary, class dictionary"""
        data = {
            "switchId": "sample_id",
            "switchManufacturer": None,
            "switchModel": None,
            "switchSerialNumber": None,
            "link": None,
        }
        assert data == FMSwitchData(**self.default).model_dump(by_alias=True)
        data = {
            "switchId": "exchange_id",
            "switchManufacturer": "manufacturer",
            "switchModel": "model",
            "switchSerialNumber": "serial",
            "link": [],
        }
        assert data == FMSwitchData(**data).model_dump(by_alias=True)


class FMPluginBaseTests(TestCase):
    """Test FMPluginBase class for fm_plugin_base module"""

    # revisit
    def test_no_init_class(self):
        """Test for class without __init__ method"""

        class _Dummy(FMPluginBase):
            """Dummy class for testing"""

            def connect(self, _cpu_id: str, _device_id: str):
                return self.specific_data

            def disconnect(self, _cpu_id: str, _device_id: str):
                return self.specific_data

            def get_port_info(self, _target_id: str | None = None):
                return self.specific_data

            def get_switch_info(self, _switch_id: str | None = None):
                return self.specific_data

        # The plugin framework may pass None to check the plugin interface.
        inst = _Dummy(None)
        assert inst.specific_data is None
        assert inst.connect("", "") is None
        assert inst.disconnect("", "") is None
        assert inst.get_port_info("") is None
        inst = _Dummy({"test_key": "test_value"})
        assert inst.specific_data == {"test_key": "test_value"}
        assert inst.connect("", "") == {"test_key": "test_value"}
        assert inst.disconnect("", "") == {"test_key": "test_value"}
        assert inst.get_port_info("") == {"test_key": "test_value"}

    def test_no_connect_class(self):
        """Test for class without connect method"""

        class _Dummy(FMPluginBase):
            """Dummy class for testing"""

            def __init__(self, _specific_data=None):
                super().__init__(_specific_data)

            def disconnect(self, _cpu_id: str, _device_id: str):
                """Create only definitions for evaluation"""

            def get_port_info(self, _target_id: str | None = None):
                """Create only definitions for evaluation"""

            def get_switch_info(self, _switch_id: str | None = None):
                """Create only definitions for evaluation"""

        with pytest.raises(TypeError):
            _Dummy()

    def test_no_disconnect_class(self):
        """Test for class without disconnect method"""

        class _Dummy(FMPluginBase):
            """Dummy class for testing"""

            def __init__(self, _specific_data=None):
                super().__init__(_specific_data)

            def connect(self, _cpu_id: str, _device_id: str):
                """Create only definitions for evaluation"""

            def get_port_info(self, _target_id: str | None = None):
                """Create only definitions for evaluation"""

            def get_switch_info(self, _switch_id: str | None = None):
                """Create only definitions for evaluation"""

        with pytest.raises(TypeError):
            _Dummy()

    def test_no_show_class(self):
        """Test for class without get_port_info method"""

        class _Dummy(FMPluginBase):
            """Dummy class for testing"""

            def __init__(self, _specific_data=None):
                super().__init__(_specific_data)

            def connect(self, _cpu_id: str, _device_id: str):
                """Create only definitions for evaluation"""

            def disconnect(self, _cpu_id: str, _device_id: str):
                """Create only definitions for evaluation"""

            def get_switch_info(self, _switch_id: str | None = None):
                """Create only definitions for evaluation"""

        with pytest.raises(TypeError):
            _Dummy()

    def test_no_show_switch_class(self):
        """Test for class without get_switch_info method"""

        class _Dummy(FMPluginBase):
            """Dummy class for testing"""

            def __init__(self, _specific_data=None):
                super().__init__(_specific_data)

            def connect(self, _cpu_id: str, _device_id: str):
                """Create only definitions for evaluation"""

            def disconnect(self, _cpu_id: str, _device_id: str):
                """Create only definitions for evaluation"""

            def get_port_info(self, _target_id: str | None = None):
                """Create only definitions for evaluation"""

        with pytest.raises(TypeError):
            _Dummy()

    def test_normal_class(self):
        """Test for class with all method"""

        class _Dummy(FMPluginBase):
            """Dummy class for testing"""

            def __init__(self, _specific_data=None):
                super().__init__(_specific_data)

            def connect(self, _cpu_id: str, _device_id: str):
                """Create only definitions for evaluation"""

            def disconnect(self, _cpu_id: str, _device_id: str):
                """Create only definitions for evaluation"""

            def get_port_info(self, _target_id: str | None = None):
                """Create only definitions for evaluation"""

            def get_switch_info(self, _switch_id: str | None = None):
                """Create only definitions for evaluation"""

        inst = _Dummy()
        inst.connect("", "")
        inst.disconnect("", "")
        inst.get_port_info("")
        inst.get_switch_info("")

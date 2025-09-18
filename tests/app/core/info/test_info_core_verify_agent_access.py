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

import logging
import pytest
from app.core.info.info_core import InformationCore
from app.common.basic_exceptions import BaseHWControlError

# OOB metric data CPU On
OOB_METRIC_DATA_CPU_ON = {
    "devices": [
        {
            "type": "CPU",
            "deviceID": "0001",
            "schema": {"PowerState": "On", "PowerCapability": True, "Status": {"Health": "OK", "State": "Enabled"}},
        }
    ]
}

# OOB metric data CPU Off
OOB_METRIC_DATA_CPU_OFF = {
    "devices": [
        {
            "type": "CPU",
            "deviceID": "0001",
            "schema": {"PowerState": "Off", "PowerCapability": True, "Status": {"Health": "OK", "State": "Enabled"}},
        }
    ]
}

# OOB spec data CPU
OOB_SPEC_DATA_CPU = {
    "devices": [
        {
            "type": "CPU",
            "deviceID": "0001",
            "schema": {"PowerState": "On", "PowerCapability": True, "Status": {"Health": "OK", "State": "Enabled"}},
            "link": [{"type": "memory", "deviceID": "1001"}],
        }
    ]
}

# FM data CPU
FM_DATA_CPU = {
    "data": [
        {
            "deviceID": "0001",
            "type": "CPU",
            "LTSSMState": "L0",
            "link": [{"deviceID": "2001", "type": "storage"}, {"deviceID": "3001", "type": "networkInterface"}],
        }
    ]
}

# OOB metric data memory on
OOB_METRIC_DATA_MEMORY_ON = {
    "devices": [
        {
            "type": "memory",
            "deviceID": "0001",
            "schema": {"PowerState": "On", "PowerCapability": True, "Status": {"Health": "OK", "State": "Enabled"}},
        }
    ]
}

# OOB metric data memory off
OOB_METRIC_DATA_MEMORY_OFF = {
    "devices": [
        {
            "type": "memory",
            "deviceID": "0001",
            "schema": {"PowerState": "Off", "PowerCapability": True, "Status": {"Health": "OK", "State": "Enabled"}},
        }
    ]
}

# OOB Spec data memory
OOB_SPEC_DATA_MEMORY = {
    "devices": [
        {
            "type": "memory",
            "deviceID": "1001",
            "schema": {"PowerState": "On", "PowerCapability": True, "Status": {"Health": "OK", "State": "Enabled"}},
            "link": [{"type": "CPU", "deviceID": "0001"}],
        }
    ]
}

# OOB Spec data memory no link
OOB_SPEC_DATA_MEMORY_NO_LINK = {
    "devices": [
        {
            "type": "memory",
            "deviceID": "1001",
            "schema": {"PowerState": "On", "PowerCapability": True, "Status": {"Health": "OK", "State": "Enabled"}},
        }
    ]
}

# OOB Spec data memory link No CPU
OOB_SPEC_DATA_MEMORY_LINK_NO_CPU = {
    "devices": [
        {
            "type": "memory",
            "deviceID": "1001",
            "schema": {"PowerState": "On", "PowerCapability": True, "Status": {"Health": "OK", "State": "Enabled"}},
            "link": [{"type": "GPU", "deviceID": "5001"}],
        }
    ]
}

# FM data memory link
FM_DATA_MEMORY_LINK = {
    "data": [{"deviceID": "1001", "type": "memory", "LTSSMState": "L0", "link": [{"deviceID": "0001", "type": "CPU"}]}]
}

# FM data memory no link
FM_DATA_MEMORY_NO_LINK = {"data": [{"deviceID": "1001", "type": "memory", "LTSSMState": "L0"}]}

# FM data memory link no cpu
FM_DATA_MEMORY_LINK_NO_CPU = {
    "data": [{"deviceID": "1001", "type": "memory", "LTSSMState": "L0", "link": [{"deviceID": "5001", "type": "GPU"}]}]
}

# OOB metric data storage on
OOB_METRIC_DATA_STORAGE_ON = {
    "devices": [
        {
            "type": "storage",
            "deviceID": "2001",
            "schema": {
                "Drive": {
                    "NegotiatedSpeedGbs": 12,
                    "PowerState": "On",
                    "PowerCapability": True,
                    "Status": {"Health": "OK", "State": "Enabled"},
                }
            },
        }
    ]
}

# OOB metric data storage off
OOB_METRIC_DATA_STORAGE_OFF = {
    "devices": [
        {
            "type": "storage",
            "deviceID": "2001",
            "schema": {
                "Drive": {
                    "NegotiatedSpeedGbs": 12,
                    "PowerState": "Off",
                    "PowerCapability": True,
                    "Status": {"Health": "OK", "State": "Enabled"},
                }
            },
        }
    ]
}

# OOB Spec data storage
OOB_SPEC_DATA_STORAGE = {
    "devices": [
        {
            "type": "storage",
            "deviceID": "2001",
            "schema": {
                "Drive": {
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "PowerState": "On",
                    "PowerCapability": True,
                }
            },
            "link": [{"type": "CPU", "deviceID": "0001"}],
        }
    ]
}

# FM data storage link
FM_DATA_STORAGE_LINK = {
    "data": [{"deviceID": "2001", "type": "storage", "LTSSMState": "L0", "link": [{"type": "CPU", "deviceID": "0001"}]}]
}

# FM data storage no link
FM_DATA_STORAGE_NO_LINK = {"data": [{"deviceID": "2001", "type": "storage", "LTSSMState": "L0"}]}

# OOB metric data NIC on
OOB_METRIC_DATA_NIC_ON = {
    "devices": [
        {
            "type": "networkInterface",
            "deviceID": "3001",
            "schema": {
                "Network": {
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "PowerState": "On",
                    "PowerCapability": False,
                }
            },
        }
    ]
}

# OOB metric data NIC off
OOB_METRIC_DATA_NIC_OFF = {
    "devices": [
        {
            "type": "networkInterface",
            "deviceID": "3001",
            "schema": {
                "Network": {
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "PowerState": "Off",
                    "PowerCapability": False,
                }
            },
        }
    ]
}

# OOB Spec data
OOB_SPEC_DATA_NIC = {
    "devices": [
        {
            "type": "networkInterface",
            "deviceID": "3001",
            "schema": {
                "Network": {
                    "PowerState": "On",
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "PowerCapability": False,
                },
            },
            "link": [{"type": "CPU", "deviceID": "0001"}],
        }
    ]
}

# FM data networkInterface link
FM_DATA_NIC_LINK = {
    "data": [
        {
            "deviceID": "3001",
            "type": "networkInterface",
            "LTSSMState": "L0",
            "link": [{"type": "CPU", "deviceID": "0001"}],
        }
    ]
}

# FM data networkInterface no link
FM_DATA_NIC_NO_LINK = {"data": [{"deviceID": "3001", "type": "networkInterface", "LTSSMState": "L0"}]}


def _log_contains(record, level, message) -> bool:
    """Comparing log contents"""
    return next(filter(lambda x: (x[1] == level) and (message in x[2]), record), None) is not None


def _moc_verify_agent_access(
    mocker, caplog, device_id, device_type, oob_data, fm_data, moc_oob_spec_data, moc_oob_metric_cpu_data
):
    """Get Information"""
    caplog.set_level(logging.INFO)

    def mock_oob_spec(_, __):
        return moc_oob_spec_data

    def mock_oob_metric_cpu(_, __):
        return moc_oob_metric_cpu_data

    # Replace obtaining OOB device information with a mock.
    mocker.patch("app.core.info.spec_oob.GetSpecOOBInfo.get_spec_oob", side_effect=mock_oob_spec)

    # Replace obtaining OOB metric (CPU) information with a mock.
    mocker.patch("app.core.info.spec_oob.GetSpecOOBInfo.get_metric_oob", side_effect=mock_oob_metric_cpu)

    get_information = InformationCore()
    return get_information._verify_agent_access(  # pylint: disable=protected-access
        device_id, device_type, oob_data, fm_data
    )


def test_verify_agent_access_arg_check(mocker, caplog):
    """Test argument none"""
    # When there are no arguments
    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker, caplog, None, "CPU", OOB_METRIC_DATA_CPU_ON, FM_DATA_CPU, OOB_SPEC_DATA_CPU, OOB_METRIC_DATA_CPU_ON
    )
    assert not is_access and cpu_device_id is None
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "device_id: None, device_type: CPU,  Skipping connection to the Agent. Invalid input values: device_id.",
    )

    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker, caplog, "0001", None, OOB_METRIC_DATA_CPU_ON, FM_DATA_CPU, OOB_SPEC_DATA_CPU, OOB_METRIC_DATA_CPU_ON
    )
    assert not is_access and cpu_device_id is None
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "device_id: 0001, device_type: None,  Skipping connection to the Agent. Invalid input values: device_type.",
    )

    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker, caplog, "0001", "CPU", None, FM_DATA_CPU, OOB_SPEC_DATA_CPU, OOB_METRIC_DATA_CPU_ON
    )
    assert not is_access and cpu_device_id is None
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "device_id: 0001, device_type: CPU,  Skipping connection to the Agent. Invalid input values: oob_data.",
    )

    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker, caplog, "0001", "CPU", OOB_METRIC_DATA_CPU_ON, None, OOB_SPEC_DATA_CPU, OOB_METRIC_DATA_CPU_ON
    )
    assert not is_access and cpu_device_id is None
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "device_id: 0001, device_type: CPU,  Skipping connection to the Agent. Invalid input values: fm_data.",
    )

    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker, caplog, None, None, OOB_METRIC_DATA_CPU_ON, FM_DATA_CPU, OOB_SPEC_DATA_CPU, OOB_METRIC_DATA_CPU_ON
    )
    assert not is_access and cpu_device_id is None
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "device_id: None, device_type: None,  Skipping connection to the Agent. "
        "Invalid input values: device_id, device_type.",
    )


def test_verify_agent_access_cpu_on(mocker, caplog):
    """Test CPU power on"""
    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker, caplog, "0001", "CPU", OOB_METRIC_DATA_CPU_ON, FM_DATA_CPU, OOB_SPEC_DATA_CPU, OOB_METRIC_DATA_CPU_ON
    )
    assert is_access and cpu_device_id == "0001"


def test_verify_agent_access_cpu_off(mocker, caplog):
    """Test CPU power off"""
    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker, caplog, "0001", "CPU", OOB_METRIC_DATA_CPU_OFF, FM_DATA_CPU, OOB_SPEC_DATA_CPU, OOB_METRIC_DATA_CPU_ON
    )
    assert not is_access and cpu_device_id is None
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "device_id: 0001, device_type: CPU,  Skipping connection to the Agent. Device PowerState is not On.",
    )


def test_verify_agent_access_memory_on(mocker, caplog):
    """Test memory power on"""
    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker,
        caplog,
        "1001",
        "memory",
        OOB_METRIC_DATA_MEMORY_ON,
        FM_DATA_MEMORY_LINK,
        OOB_SPEC_DATA_MEMORY,
        OOB_METRIC_DATA_CPU_ON,
    )
    assert is_access and cpu_device_id == "0001"


def test_verify_agent_access_memory_fm_no_link(mocker, caplog):
    """Test memory fm no link"""
    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker,
        caplog,
        "1001",
        "memory",
        OOB_METRIC_DATA_MEMORY_ON,
        FM_DATA_MEMORY_NO_LINK,
        OOB_SPEC_DATA_MEMORY,
        OOB_METRIC_DATA_CPU_ON,
    )
    assert is_access and cpu_device_id == "0001"


def test_verify_agent_access_memory_off(mocker, caplog):
    """Test memory power off"""
    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker,
        caplog,
        "1001",
        "memory",
        OOB_METRIC_DATA_MEMORY_OFF,
        FM_DATA_MEMORY_LINK,
        OOB_SPEC_DATA_MEMORY,
        OOB_METRIC_DATA_CPU_ON,
    )
    assert not is_access and cpu_device_id is None
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "device_id: 1001, device_type: memory,  Skipping connection to the Agent. Device PowerState is not On.",
    )


def test_verify_agent_access_storage_on(mocker, caplog):
    """Test storage power on"""
    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker,
        caplog,
        "2001",
        "storage",
        OOB_METRIC_DATA_STORAGE_ON,
        FM_DATA_STORAGE_LINK,
        OOB_SPEC_DATA_STORAGE,
        OOB_METRIC_DATA_CPU_ON,
    )
    assert is_access and cpu_device_id == "0001"


def test_verify_agent_access_storage_fm_no_link(mocker, caplog):
    """Test storage fm no link"""
    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker,
        caplog,
        "2001",
        "storage",
        OOB_METRIC_DATA_STORAGE_ON,
        FM_DATA_STORAGE_NO_LINK,
        OOB_SPEC_DATA_STORAGE,
        OOB_METRIC_DATA_CPU_ON,
    )
    assert is_access and cpu_device_id == "0001"


def test_verify_agent_access_storage_off(mocker, caplog):
    """Test storage power off"""
    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker,
        caplog,
        "2001",
        "storage",
        OOB_METRIC_DATA_STORAGE_OFF,
        FM_DATA_STORAGE_LINK,
        OOB_SPEC_DATA_STORAGE,
        OOB_METRIC_DATA_CPU_ON,
    )
    assert not is_access and cpu_device_id is None
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "device_id: 2001, device_type: storage,  Skipping connection to the Agent. Device PowerState is not On.",
    )


def test_verify_agent_access_nic_on(mocker, caplog):
    """Test networkInterface power on"""
    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker,
        caplog,
        "3001",
        "networkInterface",
        OOB_METRIC_DATA_NIC_ON,
        FM_DATA_NIC_LINK,
        OOB_SPEC_DATA_NIC,
        OOB_METRIC_DATA_CPU_ON,
    )
    assert is_access and cpu_device_id == "0001"


def test_verify_agent_access_nic_fm_no_link(mocker, caplog):
    """Test networkInterface fm no link"""
    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker,
        caplog,
        "3001",
        "networkInterface",
        OOB_METRIC_DATA_NIC_ON,
        FM_DATA_NIC_NO_LINK,
        OOB_SPEC_DATA_NIC,
        OOB_METRIC_DATA_CPU_ON,
    )
    assert is_access and cpu_device_id == "0001"


def test_verify_agent_access_nic_off(mocker, caplog):
    """Test networkInterface power off"""
    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker,
        caplog,
        "3001",
        "networkInterface",
        OOB_METRIC_DATA_NIC_OFF,
        FM_DATA_NIC_LINK,
        OOB_SPEC_DATA_NIC,
        OOB_METRIC_DATA_CPU_ON,
    )
    assert not is_access and cpu_device_id is None
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "device_id: 3001, device_type: networkInterface,  Skipping connection to the Agent. "
        "Device PowerState is not On.",
    )


def test_verify_agent_access_base_exception(mocker):
    """base exception"""
    # Forcing an BaseHWControlError in get_metric_oob triggers the BaseHWControlError to be thrown.
    mocker.patch("app.core.info.spec_oob.GetSpecOOBInfo.get_metric_oob", side_effect=BaseHWControlError)
    get_information = InformationCore()
    with pytest.raises(BaseHWControlError):
        get_information._verify_agent_access(  # pylint: disable=protected-access
            "1001", "memory", OOB_METRIC_DATA_MEMORY_ON, FM_DATA_MEMORY_NO_LINK
        )


def test_verify_agent_access_device_type_none(mocker, caplog):
    """Test device_type None"""
    is_access, cpu_device_id = _moc_verify_agent_access(mocker, caplog, "3001", None, {}, {}, {}, {})
    assert not is_access and cpu_device_id is None
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "device_id: 3001, device_type: None,  Skipping connection to the Agent. "
        "Invalid input values: device_type, oob_data, fm_data.",
    )


def test_verify_agent_access_device_type_gpu(mocker, caplog):
    """Test device_type None"""
    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker,
        caplog,
        "5001",
        "GPU",
        OOB_METRIC_DATA_NIC_ON,
        FM_DATA_NIC_LINK,
        OOB_SPEC_DATA_NIC,
        OOB_METRIC_DATA_CPU_ON,
    )
    assert not is_access and cpu_device_id is None
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "device_id: 5001, device_type: GPU,  Skipping connection to the Agent. Device Type GPU is not supported.",
    )


def test_verify_agent_access_fm_cpu_device_id_none(mocker, caplog):
    """Test fm cpu_device_id none"""
    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker,
        caplog,
        "1001",
        "memory",
        OOB_METRIC_DATA_MEMORY_ON,
        FM_DATA_MEMORY_LINK_NO_CPU,
        OOB_SPEC_DATA_MEMORY,
        OOB_METRIC_DATA_CPU_ON,
    )
    assert is_access and cpu_device_id == "0001"


def test_verify_agent_access_oob_cpu_device_id_none(mocker, caplog):
    """Test oob cpu_device_id none"""
    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker,
        caplog,
        "1001",
        "memory",
        OOB_METRIC_DATA_MEMORY_ON,
        FM_DATA_MEMORY_NO_LINK,
        OOB_SPEC_DATA_MEMORY_LINK_NO_CPU,
        OOB_METRIC_DATA_CPU_ON,
    )
    assert not is_access and cpu_device_id is None
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "device_id: 1001, device_type: memory,  Skipping connection to the Agent. "
        "This device is not linked to the CPU.",
    )


def test_verify_agent_access_memory_oob_no_link(mocker, caplog):
    """Test memory oob no link"""
    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker,
        caplog,
        "1001",
        "memory",
        OOB_METRIC_DATA_MEMORY_ON,
        FM_DATA_MEMORY_NO_LINK,
        OOB_SPEC_DATA_MEMORY_NO_LINK,
        OOB_METRIC_DATA_CPU_ON,
    )
    assert not is_access and cpu_device_id is None
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "device_id: 1001, device_type: memory,  Skipping connection to the Agent. "
        "This device is not linked to the CPU.",
    )


def test_verify_agent_access_memory_oob_link_cpu_off(mocker, caplog):
    """Test memory oob no link"""
    is_access, cpu_device_id = _moc_verify_agent_access(
        mocker,
        caplog,
        "1001",
        "memory",
        OOB_METRIC_DATA_MEMORY_ON,
        FM_DATA_MEMORY_LINK,
        OOB_SPEC_DATA_MEMORY_NO_LINK,
        OOB_METRIC_DATA_CPU_OFF,
    )
    assert not is_access and cpu_device_id is None
    assert _log_contains(
        caplog.record_tuples,
        logging.INFO,
        "device_id: 1001, device_type: memory,  Skipping connection to the Agent. CPU PowerState is not On.",
    )


def test_get_oob_power_state_other_device_type():
    """Test _get_oob_power_state() other device_type"""
    get_information = InformationCore()
    rtn = get_information._get_oob_power_state("VM", None)  # pylint: disable=protected-access
    assert rtn is None

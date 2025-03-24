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

from pathlib import Path
import cdimlogger.common
from app.common.settings import Settings


def environment_setup(monkeypatch):
    """Set up environment variables for testing."""
    monkeypatch.setenv("HW_CONTROL_DEBUG", "true")
    monkeypatch.setenv("HW_CONTROL_LOG_TAG", "TestTag")
    monkeypatch.setenv("HW_CONTROL_LOG_DIR", "/tmp/log")
    monkeypatch.setenv("HW_CONTROL_LOG_FILE", "test.log")
    monkeypatch.setenv("HW_CONTROL_LOGGING_LEVEL", "DEBUG")
    monkeypatch.setenv("HW_CONTROL_LOG_ROTATION_SIZE", "2000000")
    monkeypatch.setenv("HW_CONTROL_LOG_BACKUP_FILES", "5")
    monkeypatch.setenv("HW_CONTROL_LOG_STDOUT", "true")
    monkeypatch.setenv("HW_CONTROL_AGENT_ENABLED", "true")
    monkeypatch.setenv("HW_CONTROL_MAPPING_TABLE_PATH", "/tmp/mapping")


def delete_environment(monkeypatch):
    """Delete environment variables for testing."""
    monkeypatch.delenv("HW_CONTROL_DEBUG", raising=False)
    monkeypatch.delenv("HW_CONTROL_LOG_TAG", raising=False)
    monkeypatch.delenv("HW_CONTROL_LOG_DIR", raising=False)
    monkeypatch.delenv("HW_CONTROL_LOG_FILE", raising=False)
    monkeypatch.delenv("HW_CONTROL_LOGGING_LEVEL", raising=False)
    monkeypatch.delenv("HW_CONTROL_LOG_ROTATION_SIZE", raising=False)
    monkeypatch.delenv("HW_CONTROL_LOG_BACKUP_FILES", raising=False)
    monkeypatch.delenv("HW_CONTROL_LOG_STDOUT", raising=False)
    monkeypatch.delenv("HW_CONTROL_AGENT_ENABLED", raising=False)
    monkeypatch.delenv("HW_CONTROL_MAPPING_TABLE_PATH", raising=False)


def test_environment_settings(monkeypatch):
    """Test environment settings"""
    environment_setup(monkeypatch)
    settings = Settings()
    assert settings.DEBUG is True
    assert settings.LOG_TAG == "TestTag"
    assert settings.LOG_DIR == "/tmp/log"
    assert settings.LOG_FILE == "test.log"
    assert settings.LOGGING_LEVEL == "DEBUG"
    assert settings.LOG_ROTATION_SIZE == 2000000
    assert settings.LOG_BACKUP_FILES == 5
    assert settings.LOG_STDOUT is True
    assert settings.MAPPING_TABLE_PATH == "/tmp/mapping"
    assert settings.HW_CONTROL_AGENT_ENABLED is True


def test_environment_settings_default(monkeypatch):
    """Test environment settings default"""
    delete_environment(monkeypatch)
    settings = Settings()
    assert settings.DEBUG is False
    assert settings.LOG_TAG == cdimlogger.common.TAG_APP_HWCONTROL
    assert settings.LOG_DIR == "/var/log/cdim"
    assert settings.LOG_FILE == "app_hw_control.log"
    assert settings.LOGGING_LEVEL == "INFO"
    assert settings.LOG_ROTATION_SIZE == 1000000
    assert settings.LOG_BACKUP_FILES == 3
    assert settings.LOG_STDOUT is False
    assert settings.MAPPING_TABLE_PATH == str(
        (Path(__file__).parent.parent.parent.parent / "src" / "app" / "mapping").resolve()
    )
    assert settings.HW_CONTROL_AGENT_ENABLED is False

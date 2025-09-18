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
from app.common.settings import Settings


def environment_setup(monkeypatch):
    """Set up environment variables for testing."""
    monkeypatch.setenv("HW_CONTROL_AGENT_ENABLED", "true")
    monkeypatch.setenv("HW_CONTROL_MAPPING_TABLE_PATH", "/tmp/mapping")


def delete_environment(monkeypatch):
    """Delete environment variables for testing."""
    monkeypatch.delenv("HW_CONTROL_AGENT_ENABLED", raising=False)
    monkeypatch.delenv("HW_CONTROL_MAPPING_TABLE_PATH", raising=False)


def test_environment_settings(monkeypatch):
    """Test environment settings"""
    environment_setup(monkeypatch)
    settings = Settings()
    assert settings.MAPPING_TABLE_PATH == "/tmp/mapping"
    assert settings.HW_CONTROL_AGENT_ENABLED is True


def test_environment_settings_default(monkeypatch):
    """Test environment settings default"""
    delete_environment(monkeypatch)
    settings = Settings()
    assert settings.MAPPING_TABLE_PATH == str(
        (Path(__file__).parent.parent.parent.parent / "src" / "app" / "mapping").resolve()
    )
    assert settings.HW_CONTROL_AGENT_ENABLED is False

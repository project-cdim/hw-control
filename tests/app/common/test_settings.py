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

"""This is a test program."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from app.common.settings import Settings


def environment_setup(monkeypatch):
    """Set up environment variables for testing."""
    monkeypatch.setenv("HW_CONTROL_AGENT_ENABLED", "true")
    monkeypatch.setenv("HW_CONTROL_MAPPING_TABLE_PATH", "/tmp/mapping")
    monkeypatch.setenv("HW_CONTROL_PLUGIN_MAX_RESPONSE_SIZE", "65536")


def delete_environment(monkeypatch):
    """Delete environment variables for testing."""
    monkeypatch.delenv("HW_CONTROL_AGENT_ENABLED", raising=False)
    monkeypatch.delenv("HW_CONTROL_MAPPING_TABLE_PATH", raising=False)
    monkeypatch.delenv("HW_CONTROL_PLUGIN_MAX_RESPONSE_SIZE", raising=False)


def test_environment_settings(monkeypatch):
    """Test environment settings"""
    environment_setup(monkeypatch)
    settings = Settings()
    assert settings.mapping_table_path == "/tmp/mapping"
    assert settings.agent_enabled is True
    assert settings.plugin_max_response_size == 65536


def test_environment_settings_default(monkeypatch):
    """Test environment settings default"""
    delete_environment(monkeypatch)
    settings = Settings()
    assert settings.mapping_table_path == str(
        (Path(__file__).parent.parent.parent.parent / "src" / "app" / "mapping").resolve()
    )
    assert settings.agent_enabled is False
    assert settings.plugin_max_response_size == 1024 * 1024


@pytest.mark.parametrize("value", [65536, 10485760])
def test_plugin_max_response_size_boundary_valid(monkeypatch, value):
    """Test the accepted boundary values of the max response size."""
    delete_environment(monkeypatch)
    monkeypatch.setenv("HW_CONTROL_PLUGIN_MAX_RESPONSE_SIZE", str(value))
    settings = Settings()
    assert settings.plugin_max_response_size == value


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (65535, "greater than or equal to 65536"),
        (10485761, "less than or equal to 10485760"),
    ],
)
def test_plugin_max_response_size_boundary_invalid(monkeypatch, value, message):
    """Test the rejected boundary values of the max response size."""
    delete_environment(monkeypatch)
    monkeypatch.setenv("HW_CONTROL_PLUGIN_MAX_RESPONSE_SIZE", str(value))
    with pytest.raises(ValidationError) as exc_info:
        Settings()
    assert message in str(exc_info.value)

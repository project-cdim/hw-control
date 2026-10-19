# Copyright 2026 NEC Corporation
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
# under the License.

"""Unit test module for app/common/plugin/plugin_manager.py."""

import logging

import pytest
from pydantic import ValidationError
from pytest_mock import MockerFixture

import app.common.basic_exceptions as exc
from app.common.plugin import plugin_manager
from app.common.plugin.compat import ServicePluginFMCompatible, ServicePluginOOBCompatible
from app.common.plugin.service import ServicePlugin

_VALID_CONFIG_CONTENT = "base_url: http://localhost:3500\nversion: v1\nsupported_features:\n  - metric\n"


def _write_config(tmp_path, manager_id: str, content: str = _VALID_CONFIG_CONTENT) -> None:
    (tmp_path / f"{manager_id}_manager.yaml").write_text(content, encoding="utf-8")


class TestGetManagerList:
    """Test get_manager_list."""

    def test_non_string_manager_type_raises(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """A non-string manager_type raises APIUsageHWControlError."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path))
        with pytest.raises(exc.APIUsageHWControlError):
            plugin_manager.get_manager_list(123)  # type: ignore[arg-type]

    def test_manager_type_case_insensitive(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """manager_type is not case sensitive."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path))
        _write_config(tmp_path, "mgr1")
        assert plugin_manager.get_manager_list("FM") == plugin_manager.get_manager_list("fm")

    def test_unknown_manager_type_raises_api_usage_error(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """A manager_type other than 'fm'/'oob' raises APIUsageHWControlError, not FileNotFoundError."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path))
        with pytest.raises(exc.APIUsageHWControlError):
            plugin_manager.get_manager_list("xyz")

    def test_path_traversal_manager_type_raises_api_usage_error(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """A manager_type crafted for path traversal is rejected before being used to build a path."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path))
        with pytest.raises(exc.APIUsageHWControlError):
            plugin_manager.get_manager_list("../../etc")

    def test_missing_legacy_config_dir_returns_empty_list(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """A missing legacy 'fm'/'oob' config directory is treated as "no plugin found"."""
        monkeypatch.setattr(plugin_manager, "_setting_file_base_path", str(tmp_path / "no_such_dir") + "/")
        assert plugin_manager.get_manager_list("fm") == []

    def test_legacy_config_dir_is_file_returns_empty_list(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """A legacy config path that is not a directory is treated as "no plugin found"."""
        (tmp_path / "fm").write_text("not a directory", encoding="utf-8")
        monkeypatch.setattr(plugin_manager, "_setting_file_base_path", str(tmp_path) + "/")
        assert plugin_manager.get_manager_list("fm") == []

    def test_unreadable_legacy_config_dir_returns_empty_list(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """An unreadable legacy config directory is treated as "no plugin found"."""
        legacy_dir = tmp_path / "fm"
        legacy_dir.mkdir()
        legacy_dir.chmod(0o000)
        monkeypatch.setattr(plugin_manager, "_setting_file_base_path", str(tmp_path) + "/")
        try:
            assert plugin_manager.get_manager_list("fm") == []
        finally:
            legacy_dir.chmod(0o700)

    def test_no_manager_type_returns_remote_and_legacy(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
    ):
        """manager_type=None merges remote plugin IDs with legacy FM and OOB plugin IDs."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path))
        _write_config(tmp_path, "remote1")
        mocker.patch(
            "app.common.plugin.plugin_manager._get_legacy_manager_list",
            side_effect=lambda manager_type: {"FM": ["fm1"], "OOB": ["oob1"]}[manager_type],
        )
        result = plugin_manager.get_manager_list()
        assert sorted(result) == ["fm1", "oob1", "remote1"]

    def test_no_manager_type_deduplicates_ids_in_priority_order(
        self,
        tmp_path,
        monkeypatch: pytest.MonkeyPatch,
        mocker: MockerFixture,
        caplog: pytest.LogCaptureFixture,
    ):
        """A manager ID present in more than one plugin type is returned once, remote taking priority."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path))
        _write_config(tmp_path, "dup")
        mocker.patch(
            "app.common.plugin.plugin_manager._get_legacy_manager_list",
            side_effect=lambda manager_type: {"FM": ["dup", "fm1"], "OOB": ["dup"]}[manager_type],
        )
        with caplog.at_level(logging.WARNING, logger=plugin_manager.__name__):
            result = plugin_manager.get_manager_list()
        assert result == ["dup", "fm1"]
        assert any("dup" in record.getMessage() for record in caplog.records if record.levelname == "WARNING")

    def test_manager_type_fm_only_calls_legacy_fm(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
    ):
        """manager_type='fm' only returns legacy FM plugin IDs, not remote or OOB ones."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path))
        _write_config(tmp_path, "remote1")
        legacy_mock = mocker.patch("app.common.plugin.plugin_manager._get_legacy_manager_list", return_value=["fm1"])
        result = plugin_manager.get_manager_list("fm")
        assert result == ["fm1"]
        legacy_mock.assert_called_once_with("fm")

    def test_missing_plugin_dir_returns_only_legacy(self, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture):
        """A missing remote plugin directory does not raise; only legacy IDs are returned."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", "/no/such/directory")
        mocker.patch(
            "app.common.plugin.plugin_manager._get_legacy_manager_list",
            side_effect=lambda manager_type: {"FM": [], "OOB": []}[manager_type],
        )
        assert plugin_manager.get_manager_list() == []

    def test_invalid_manager_id_in_remote_dir_is_skipped(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ):
        """A remote config file whose manager ID contains invalid characters is skipped and logged."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path))
        _write_config(tmp_path, "bad id")
        with caplog.at_level(logging.ERROR, logger=plugin_manager.__name__):
            assert plugin_manager._get_remote_manager_ids() == []
        assert any("bad id_manager.yaml" in record.getMessage() for record in caplog.records)

    def test_invalid_remote_config_content_is_skipped(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ):
        """A remote config file with invalid content is skipped without raising, and logged."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path))
        _write_config(tmp_path, "broken", content="not: [valid, yaml, for, this, schema")
        with caplog.at_level(logging.ERROR, logger=plugin_manager.__name__):
            assert plugin_manager._get_remote_manager_ids() == []
        assert any("broken_manager.yaml" in record.getMessage() for record in caplog.records)

    def test_non_manager_yaml_files_are_ignored(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """Files not matching the '{manager_id}_manager.yaml' pattern are ignored."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path))
        (tmp_path / "readme.txt").write_text("not a config", encoding="utf-8")
        (tmp_path / "subdir_manager.yaml").mkdir()
        _write_config(tmp_path, "remote1")
        assert plugin_manager._get_remote_manager_ids() == ["remote1"]

    def test_plugin_dir_not_a_directory_is_skipped(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """A plugin_file_dir that points at a regular file does not raise; it is treated as empty."""
        not_a_dir = tmp_path / "not_a_dir"
        not_a_dir.write_text("I am a file, not a directory", encoding="utf-8")
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(not_a_dir))
        assert plugin_manager._get_remote_manager_ids() == []

    def test_empty_manager_id_in_remote_dir_is_skipped(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """A remote config file literally named '_manager.yaml' (empty manager ID) is skipped."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path))
        _write_config(tmp_path, "")
        assert plugin_manager._get_remote_manager_ids() == []


class TestDeprecatedLegacyPluginGetters:
    """Test that get_fm_plugin/get_oob_plugin are marked deprecated without warning at call time."""

    def test_get_fm_plugin_is_marked_deprecated(self):
        """get_fm_plugin carries a __deprecated__ marker for static analysis."""
        assert "use get_plugin(manager_id) instead" in plugin_manager.get_fm_plugin.__deprecated__

    def test_get_oob_plugin_is_marked_deprecated(self):
        """get_oob_plugin carries a __deprecated__ marker for static analysis."""
        assert "use get_plugin(manager_id) instead" in plugin_manager.get_oob_plugin.__deprecated__

    def test_get_fm_plugin_call_does_not_emit_deprecation_warning(self, recwarn: pytest.WarningsRecorder):
        """category=None means calling get_fm_plugin does not raise DeprecationWarning at runtime."""
        with pytest.raises(exc.ManagerIDHWControlError):
            plugin_manager.get_fm_plugin("bad id!")
        assert not any(issubclass(w.category, DeprecationWarning) for w in recwarn.list)


class TestGetPlugin:
    """Test get_plugin."""

    def test_invalid_manager_id_raises(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """A manager_id with invalid characters raises ValidationError."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path))
        with pytest.raises(ValidationError):
            plugin_manager.get_plugin("bad id!")

    def test_empty_manager_id_raises(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """An empty manager_id raises ValidationError."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path))
        with pytest.raises(ValidationError):
            plugin_manager.get_plugin("")

    def test_none_manager_id_raises_validation_error(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """A non-string manager_id raises ValidationError."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path))
        with pytest.raises(ValidationError):
            plugin_manager.get_plugin(None)  # type: ignore[arg-type]

    def test_missing_config_file_raises(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """A missing plugin configuration file raises ConfigurationHWControlError."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path))
        with pytest.raises(exc.ConfigurationHWControlError):
            plugin_manager.get_plugin("nonexistent")

    def test_invalid_yaml_raises(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """A config file that is not valid YAML raises ConfigurationHWControlError."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path))
        _write_config(tmp_path, "mgr1", content="key: [unterminated")
        with pytest.raises(exc.ConfigurationHWControlError):
            plugin_manager.get_plugin("mgr1")

    def test_config_not_matching_schema_raises(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """A config file that does not match ServicePluginConfig raises ConfigurationHWControlError."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path))
        _write_config(tmp_path, "mgr1", content="base_url: http://localhost:3500\n")
        with pytest.raises(exc.ConfigurationHWControlError):
            plugin_manager.get_plugin("mgr1")

    def test_valid_config_returns_service_plugin(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """A valid remote plugin config returns a ServicePlugin with manager_id set."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path))
        _write_config(
            tmp_path, "mgr1", content="base_url: http://localhost:3500\nversion: v1\nsupported_features:\n  - metric\n"
        )
        plugin = plugin_manager.get_plugin("mgr1")
        assert isinstance(plugin, ServicePlugin)
        assert plugin.manager_id == "mgr1"

    def test_falls_back_to_legacy_fm_when_remote_config_missing(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
    ):
        """When no remote config exists, a legacy FM config file yields ServicePluginFMCompatible."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path / "remote"))
        monkeypatch.setattr(plugin_manager, "_setting_file_base_path", str(tmp_path) + "/")
        (tmp_path / "fm").mkdir()
        (tmp_path / "fm" / "mgr1_manager.yaml").write_text("module: m\nclass: C\n", encoding="utf-8")
        fake_plugin = mocker.Mock()
        mocker.patch("app.common.plugin.plugin_manager.get_fm_plugin", return_value=fake_plugin)

        plugin = plugin_manager.get_plugin("mgr1")

        assert isinstance(plugin, ServicePluginFMCompatible)
        assert plugin.plugin is fake_plugin
        assert plugin.manager_id == "mgr1"

    def test_falls_back_to_legacy_oob_when_remote_and_fm_config_missing(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
    ):
        """When no remote/FM config exists, a legacy OOB config file yields ServicePluginOOBCompatible."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path / "remote"))
        monkeypatch.setattr(plugin_manager, "_setting_file_base_path", str(tmp_path) + "/")
        (tmp_path / "oob").mkdir()
        (tmp_path / "oob" / "mgr1_manager.yaml").write_text("module: m\nclass: C\n", encoding="utf-8")
        fake_plugin = mocker.Mock()
        mocker.patch("app.common.plugin.plugin_manager.get_oob_plugin", return_value=fake_plugin)

        plugin = plugin_manager.get_plugin("mgr1")

        assert isinstance(plugin, ServicePluginOOBCompatible)
        assert plugin.plugin is fake_plugin
        assert plugin.manager_id == "mgr1"

    def test_remote_config_takes_priority_over_legacy(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
    ):
        """A remote config file takes priority over a legacy FM/OOB config with the same manager ID."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path / "remote"))
        monkeypatch.setattr(plugin_manager, "_setting_file_base_path", str(tmp_path) + "/")
        (tmp_path / "remote").mkdir()
        _write_config(tmp_path / "remote", "mgr1")
        (tmp_path / "fm").mkdir()
        (tmp_path / "fm" / "mgr1_manager.yaml").write_text("module: m\nclass: C\n", encoding="utf-8")

        plugin = plugin_manager.get_plugin("mgr1")

        assert isinstance(plugin, ServicePlugin)
        assert not isinstance(plugin, ServicePluginFMCompatible)

    def test_no_matching_config_anywhere_raises(self, tmp_path, monkeypatch: pytest.MonkeyPatch):
        """No matching remote, FM or OOB config file raises ConfigurationHWControlError."""
        monkeypatch.setenv("HW_CONTROL_PLUGIN_FILE_DIR", str(tmp_path / "remote"))
        monkeypatch.setattr(plugin_manager, "_setting_file_base_path", str(tmp_path) + "/")
        with pytest.raises(exc.ConfigurationHWControlError):
            plugin_manager.get_plugin("mgr1")


class TestLoadServicePluginConfig:
    """Test _load_service_plugin_config directly, including the file-not-found path."""

    def test_file_not_found_raises_configuration_error(self, tmp_path):
        """A file that does not exist raises ConfigurationHWControlError."""
        with pytest.raises(exc.ConfigurationHWControlError):
            plugin_manager._load_service_plugin_config(str(tmp_path), "nonexistent")

    def test_schema_mismatch_raises_configuration_error(self, tmp_path):
        """A file that does not match ServicePluginConfig raises ConfigurationHWControlError."""
        (tmp_path / "mgr1_manager.yaml").write_text("baseUrl: 123\n", encoding="utf-8")
        with pytest.raises(exc.ConfigurationHWControlError):
            plugin_manager._load_service_plugin_config(str(tmp_path), "mgr1")

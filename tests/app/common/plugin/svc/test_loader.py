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

"""Unit tests for loader module."""

import logging
from unittest.mock import call

import pytest
from pytest import LogCaptureFixture
from pytest_mock import MockerFixture, MockType

from app.common.utils import plugin_manager
from app.common.utils.fm_plugin_base import FMPluginBase, FMPortData, FMSwitchData
from app.common.utils.oob_plugin_base import OOBPluginBase, OOBDeviceListItem
from app.common.plugin import ext
from app.common.plugin.svc.loader import PluginLoader, enable_plugin_lifecycle, get_fm, get_oob


def _log_contains(caplog: LogCaptureFixture, level: int, message: str) -> bool:
    for record in caplog.records:
        if record.levelno == level and message in record.message:
            return True
    return False


def _configure_plugin_manager(mocker: MockerFixture) -> tuple[MockType, MockType]:
    get_fm_plugin_mock = mocker.patch.object(plugin_manager, "get_fm_plugin")
    get_oob_plugin_mock = mocker.patch.object(plugin_manager, "get_oob_plugin")
    return get_fm_plugin_mock, get_oob_plugin_mock


class _FMPlugin(FMPluginBase):
    def connect(self, cpu_id: str, device_id: str) -> None:
        raise NotImplementedError

    def disconnect(self, cpu_id: str, device_id: str) -> None:
        raise NotImplementedError

    def get_port_info(self, target_id: str | None = None) -> dict[str, list[FMPortData]]:
        raise NotImplementedError

    def get_switch_info(self, switch_id: str | None = None) -> dict[str, list[FMSwitchData]]:
        raise NotImplementedError


class _OOBPlugin(OOBPluginBase):
    def get_spec_info(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        raise NotImplementedError

    def get_metric_info(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        raise NotImplementedError

    def get_power_state(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        raise NotImplementedError

    def get_device_info(self) -> list[OOBDeviceListItem]:
        raise NotImplementedError

    def post_power_on(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        raise NotImplementedError

    def post_power_off(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        raise NotImplementedError

    def post_cpu_reset(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        raise NotImplementedError

    def post_os_shutdown(self, key_values: list[dict[str, str]]) -> dict[str, list[dict]]:
        raise NotImplementedError


# ============================================================
# PluginLoader
# ============================================================
def test_plugin_loader_get_fm_cache(mocker: MockerFixture):
    """Check that PluginLoader.get_fm() caches FM plugin."""

    get_fm_plugin_mock, _ = _configure_plugin_manager(mocker)
    fm_plugin_1 = _FMPlugin()
    fm_plugin_2 = _FMPlugin()

    get_fm_plugin_mock.side_effect = [fm_plugin_1, fm_plugin_2]

    loader = PluginLoader()

    assert loader.get_fm("fm_plugin_1") is fm_plugin_1
    assert loader.get_fm("fm_plugin_1") is fm_plugin_1
    assert loader.get_fm("fm_plugin_2") is fm_plugin_2
    assert loader.get_fm("fm_plugin_2") is fm_plugin_2
    assert loader.get_fm("fm_plugin_1") is fm_plugin_1

    get_fm_plugin_mock.assert_has_calls([call("fm_plugin_1"), call("fm_plugin_2")])


def test_plugin_loader_get_fm_initialize(mocker: MockerFixture):
    """Check that PluginLoader.get_fm() invokes initialize() of the FM plugin implementing LifecycleAware."""

    class _FMPluginCountingInitialize(_FMPlugin, ext.LifecycleAware):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.initialize_count = 0

        def initialize(self) -> None:
            self.initialize_count += 1

        def finalize(self) -> None:
            raise NotImplementedError

    get_fm_plugin_mock, _ = _configure_plugin_manager(mocker)
    fm_plugin = _FMPluginCountingInitialize()

    get_fm_plugin_mock.return_value = fm_plugin

    loader = PluginLoader()

    assert loader.get_fm("fm_plugin") is fm_plugin
    assert loader.get_fm("fm_plugin") is fm_plugin
    assert fm_plugin.initialize_count == 1


def test_plugin_loader_get_oob_cache(mocker: MockerFixture):
    """Check that PluginLoader.get_oob() caches OOB plugin."""

    _, get_oob_plugin_mock = _configure_plugin_manager(mocker)
    oob_plugin_1 = _OOBPlugin()
    oob_plugin_2 = _OOBPlugin()

    get_oob_plugin_mock.side_effect = [oob_plugin_1, oob_plugin_2]

    loader = PluginLoader()

    assert loader.get_oob("oob_plugin_1") is oob_plugin_1
    assert loader.get_oob("oob_plugin_1") is oob_plugin_1
    assert loader.get_oob("oob_plugin_2") is oob_plugin_2
    assert loader.get_oob("oob_plugin_2") is oob_plugin_2
    assert loader.get_oob("oob_plugin_1") is oob_plugin_1

    get_oob_plugin_mock.assert_has_calls([call("oob_plugin_1"), call("oob_plugin_2")])


def test_plugin_loader_get_oob_initialize(mocker: MockerFixture):
    """Check that PluginLoader.get_oob() invokes initialize() of the OOB plugin implementing LifecycleAware."""

    class _OOBPluginCountingInitialize(_OOBPlugin, ext.LifecycleAware):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.initialize_count = 0

        def initialize(self) -> None:
            self.initialize_count += 1

        def finalize(self) -> None:
            raise NotImplementedError

    _, get_oob_plugin_mock = _configure_plugin_manager(mocker)
    oob_plugin = _OOBPluginCountingInitialize()

    get_oob_plugin_mock.return_value = oob_plugin

    loader = PluginLoader()

    assert loader.get_oob("oob_plugin") is oob_plugin
    assert loader.get_oob("oob_plugin") is oob_plugin
    assert oob_plugin.initialize_count == 1


def test_plugin_loader_dispose(mocker: MockerFixture):
    """Check that PluginLoader.dispose() invokes finalize() of the plugin implementing LifecycleAware."""

    class _FMPluginCountingFinalizeCalls(_FMPlugin, ext.LifecycleAware):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.finalize_count = 0

        def initialize(self) -> None:
            pass

        def finalize(self) -> None:
            self.finalize_count += 1

    class _OOBPluginCountingFinalizeCalls(_OOBPlugin, ext.LifecycleAware):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.finalize_count = 0

        def initialize(self) -> None:
            pass

        def finalize(self) -> None:
            self.finalize_count += 1

    get_fm_plugin_mock_, get_oob_plugin_mock = _configure_plugin_manager(mocker)
    fm_plugin_1 = _FMPlugin()
    fm_plugin_2 = _FMPluginCountingFinalizeCalls()
    oob_plugin_1 = _OOBPlugin()
    oob_plugin_2 = _OOBPluginCountingFinalizeCalls()

    get_fm_plugin_mock_.side_effect = [fm_plugin_1, fm_plugin_2]
    get_oob_plugin_mock.side_effect = [oob_plugin_1, oob_plugin_2]

    loader = PluginLoader()

    assert loader.get_fm("fm_plugin_1") is fm_plugin_1
    assert loader.get_fm("fm_plugin_2") is fm_plugin_2
    assert loader.get_oob("oob_plugin_1") is oob_plugin_1
    assert loader.get_oob("oob_plugin_2") is oob_plugin_2

    loader.dispose()
    assert fm_plugin_2.finalize_count == 1
    assert oob_plugin_2.finalize_count == 1


def test_plugin_loader_dispose_logs_exception(mocker: MockerFixture, caplog: LogCaptureFixture):
    """Check that PluginLoader.dispose() logs an exception raised by finalize() of the plugin."""

    class _FMPluginCountingFinalizeOrRaiseOnFinalize(_FMPlugin, ext.LifecycleAware):
        def __init__(self, raise_on_finalize: bool, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._raise_on_finalize = raise_on_finalize
            self.finalize_count = 0

        def initialize(self) -> None:
            pass

        def finalize(self) -> None:
            if self._raise_on_finalize:
                raise RuntimeError
            self.finalize_count += 1

    class _OOBPluginCountingFinalizeOrRaiseOnFinalize(_OOBPlugin, ext.LifecycleAware):
        def __init__(self, raise_on_finalize: bool, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._raise_on_finalize = raise_on_finalize
            self.finalize_count = 0

        def initialize(self) -> None:
            pass

        def finalize(self) -> None:
            if self._raise_on_finalize:
                raise RuntimeError
            self.finalize_count += 1

    get_fm_plugin_mock_, get_oob_plugin_mock = _configure_plugin_manager(mocker)
    fm_plugin_1 = _FMPluginCountingFinalizeOrRaiseOnFinalize(raise_on_finalize=True)
    fm_plugin_2 = _FMPluginCountingFinalizeOrRaiseOnFinalize(raise_on_finalize=False)
    oob_plugin_1 = _OOBPluginCountingFinalizeOrRaiseOnFinalize(raise_on_finalize=True)
    oob_plugin_2 = _OOBPluginCountingFinalizeOrRaiseOnFinalize(raise_on_finalize=False)

    get_fm_plugin_mock_.side_effect = [fm_plugin_1, fm_plugin_2]
    get_oob_plugin_mock.side_effect = [oob_plugin_1, oob_plugin_2]

    loader = PluginLoader()

    assert loader.get_fm("fm_plugin_1") is fm_plugin_1
    assert loader.get_fm("fm_plugin_2") is fm_plugin_2
    assert loader.get_oob("oob_plugin_1") is oob_plugin_1
    assert loader.get_oob("oob_plugin_2") is oob_plugin_2

    loader.dispose()
    assert fm_plugin_2.finalize_count == 1
    assert oob_plugin_2.finalize_count == 1
    _log_contains(caplog, logging.WARNING, "Failed to finalize plugin")


# ============================================================
# functions
# ============================================================
class _FMPluginCountingInitializeAndFinalize(_FMPlugin, ext.LifecycleAware):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initialize_count = 0
        self.finalize_count = 0

    def initialize(self) -> None:
        self.initialize_count += 1

    def finalize(self) -> None:
        self.finalize_count += 1


class _OOBPluginCountingInitializeAndFinalize(_OOBPlugin, ext.LifecycleAware):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initialize_count = 0
        self.finalize_count = 0

    def initialize(self) -> None:
        self.initialize_count += 1

    def finalize(self) -> None:
        self.finalize_count += 1


def test_get_fm_using_plugin_loader(mocker: MockerFixture):
    """Check that get_fm() uses PluginLoader to load FM plugin
    if get_fm() is invoked in the function decorated by @enable_plugin_lifecycle."""

    @enable_plugin_lifecycle
    def _invoke_get_fm(manager_id: str) -> FMPluginBase:
        get_fm(manager_id)
        return get_fm(manager_id)

    get_fm_plugin_mock, _ = _configure_plugin_manager(mocker)
    fm_plugin = _FMPluginCountingInitializeAndFinalize()

    get_fm_plugin_mock.return_value = fm_plugin

    assert _invoke_get_fm("fm_plugin") is fm_plugin
    assert get_fm_plugin_mock.call_count == 1
    assert fm_plugin.initialize_count == 1
    assert fm_plugin.finalize_count == 1


def test_get_fm_not_using_plugin_loader(mocker: MockerFixture):
    """Check that get_fm() does not use PluginLoader to load FM plugin
    if get_fm() is invoked in the function not decorated by @enable_plugin_lifecycle."""

    def _invoke_get_fm(manager_id: str) -> FMPluginBase:
        get_fm(manager_id)
        return get_fm(manager_id)

    get_fm_plugin_mock, _ = _configure_plugin_manager(mocker)
    fm_plugin = _FMPluginCountingInitializeAndFinalize()

    get_fm_plugin_mock.return_value = fm_plugin

    assert _invoke_get_fm("fm_plugin") is fm_plugin
    assert get_fm_plugin_mock.call_count == 2
    assert fm_plugin.initialize_count == 0
    assert fm_plugin.finalize_count == 0


def test_get_fm_nest_decorator():
    """Check that get_fm() raises an exception if @enable_plugin_lifecycle is nested."""

    @enable_plugin_lifecycle
    def _invoke_get_fm(manager_id: str) -> FMPluginBase:
        return _do_invoke_get_fm(manager_id)

    @enable_plugin_lifecycle
    def _do_invoke_get_fm(manager_id: str) -> FMPluginBase:
        return get_fm(manager_id)

    with pytest.raises(RuntimeError):
        _invoke_get_fm("fm_plugin")


def test_get_oob_using_plugin_loader(mocker: MockerFixture):
    """Check that get_oob() uses PluginLoader to load OOB plugin
    if get_oob() is invoked in the function decorated by @enable_plugin_lifecycle."""

    @enable_plugin_lifecycle
    def _invoke_get_oob(manager_id: str) -> OOBPluginBase:
        get_oob(manager_id)
        return get_oob(manager_id)

    _, get_oob_plugin_mock = _configure_plugin_manager(mocker)
    oob_plugin = _OOBPluginCountingInitializeAndFinalize()

    get_oob_plugin_mock.return_value = oob_plugin

    assert _invoke_get_oob("oob_plugin") is oob_plugin
    assert get_oob_plugin_mock.call_count == 1
    assert oob_plugin.initialize_count == 1
    assert oob_plugin.finalize_count == 1


def test_get_oob_not_using_plugin_loader(mocker: MockerFixture):
    """Check that get_oob() does not use PluginLoader to load OOB plugin
    if get_oob() is invoked in the function not decorated by @enable_plugin_lifecycle."""

    def _invoke_get_oob(manager_id: str) -> OOBPluginBase:
        get_oob(manager_id)
        return get_oob(manager_id)

    _, get_oob_plugin_mock = _configure_plugin_manager(mocker)
    oob_plugin = _OOBPluginCountingInitializeAndFinalize()

    get_oob_plugin_mock.return_value = oob_plugin

    assert _invoke_get_oob("oob_plugin") is oob_plugin
    assert get_oob_plugin_mock.call_count == 2
    assert oob_plugin.initialize_count == 0
    assert oob_plugin.finalize_count == 0


def test_get_oob_nest_decorator():
    """Check that get_oob() raises an exception if @enable_plugin_lifecycle is nested."""

    @enable_plugin_lifecycle
    def _invoke_get_oob(manager_id: str) -> OOBPluginBase:
        return _do_invoke_get_oob(manager_id)

    @enable_plugin_lifecycle
    def _do_invoke_get_oob(manager_id: str) -> OOBPluginBase:
        return get_oob(manager_id)

    with pytest.raises(RuntimeError):
        _invoke_get_oob("oob_plugin")

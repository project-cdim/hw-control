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

"""Plugin loader creates plugins, caches them, and manages their lifecycle.

To enable plugin lifecycle management, follow these steps:

  (1) Implement ext.LifecycleAware in the plugin.
  (2) Decorate the function using the plugins with @enable_plugin_lifecycle.
  (3) Get the plugin by get_fm() or get_oob() in decorated functions
      or functions called from those.

  >>> import app.common.plugin.ext as plugin_ext
  >>> ...
  >>> class FMPlugin(plugin_ext.LifecycleAware, FMPluginBase):
  >>>     ...

  >>> import app.common.plugin.svc.loader as plugin_loader
  >>> ...
  >>> @plugin_loader.enable_plugin_lifecycle
  >>> def _get_all_device_info(...
  >>>     fm_plugin_1 = plugin_loader.get_fm("fm_plugin_1")
  >>>     ...
  >>>     _get_spec_oob(...)
  >>>
  >>> def _get_spec_oob(...)
  >>>     oob_plugin_1 = plugin_loader.get_oob("oob_plugin_1")
  >>>     ...
"""

import contextvars
import functools
import logging

from app.common.utils import plugin_manager
from app.common.utils.fm_plugin_base import FMPluginBase
from app.common.utils.oob_plugin_base import OOBPluginBase
from app.common.plugin import ext


logger = logging.getLogger(__name__)


class PluginLoader:
    """Plugin loader."""

    def __init__(self) -> None:
        """Initialize plugin loader."""
        self._fm_plugins: dict[str, FMPluginBase] = {}
        self._oob_plugins: dict[str, OOBPluginBase] = {}

    def get_fm(self, manager_id: str) -> FMPluginBase:
        """Get FM plugin by Manager ID.

        If the FM plugin is not yet loaded, load it and save it to the cache.
        If the FM plugin implements LifecycleAware, its initialize() is invoked.
        An exception is thrown if the FM plugin cannot be loaded.

        Args:
            manager_id: Manager ID (prefix of the plugin configuration file)
        Returns:
            FM plugin
        """
        if plugin := self._fm_plugins.get(manager_id):
            return plugin

        plugin = plugin_manager.get_fm_plugin(manager_id)
        if isinstance(plugin, ext.LifecycleAware):
            plugin.initialize()
        self._fm_plugins[manager_id] = plugin
        return plugin

    def get_oob(self, manager_id: str) -> OOBPluginBase:
        """Get OOB plugin by Manager ID.

        If the OOB plugin is not yet loaded, load it and save it to the cache.
        If the OOB plugin implements LifecycleAware, its initialize() is invoked.
        An exception is thrown if the OOB plugin cannot be loaded.

        Args:
            manager_id: Manager ID (prefix of the plugin configuration file)
        Returns:
            OOB plugin
        """
        if plugin := self._oob_plugins.get(manager_id):
            return plugin

        plugin = plugin_manager.get_oob_plugin(manager_id)
        if isinstance(plugin, ext.LifecycleAware):
            plugin.initialize()
        self._oob_plugins[manager_id] = plugin
        return plugin

    def dispose(self) -> None:
        """Dispose cache.

        If the cached plugin implements LifecycleAware, its finalize() is invoked.
        """
        self._dispose_plugins(self._fm_plugins)
        self._dispose_plugins(self._oob_plugins)

    def _dispose_plugins(self, plugins: dict[str, FMPluginBase] | dict[str, OOBPluginBase]) -> None:
        for manager_id, plugin in plugins.items():
            if isinstance(plugin, ext.LifecycleAware):
                try:
                    plugin.finalize()
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    logger.warning("Failed to finalize plugin `%s`: %s", manager_id, str(exc), exc_info=exc)
        plugins.clear()


_PLUGIN_LOADER_HOLDER: contextvars.ContextVar[PluginLoader | None] = contextvars.ContextVar(
    "plugin_loader", default=None
)


def enable_plugin_lifecycle(fn):
    """Enable plugin lifecycle management in the decorated function.

    Args:
        fn: function to decorate
    Returns:
        decorated function
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        """Enable plugin lifecycle management."""
        if _PLUGIN_LOADER_HOLDER.get():
            raise RuntimeError("@enable_plugin_lifecycle can not be nested.")
        loader = PluginLoader()
        token = _PLUGIN_LOADER_HOLDER.set(loader)
        try:
            return fn(*args, **kwargs)
        finally:
            loader.dispose()
            _PLUGIN_LOADER_HOLDER.reset(token)

    return wrapper


def get_fm(manager_id: str) -> FMPluginBase:
    """Get FM plugin by Manager ID.

    If this function is invoked in the functions decorated by @enable_plugin_lifecycle,
    the plugins are cached and the methods declared in LifecycleAware are invoked.

    Args:
        manager_id: Manager ID (prefix of the plugin configuration file)
    Returns:
        FM plugin
    """
    if loader := _PLUGIN_LOADER_HOLDER.get():
        return loader.get_fm(manager_id)
    return plugin_manager.get_fm_plugin(manager_id)


def get_oob(manager_id: str) -> OOBPluginBase:
    """Get OOB plugin by Manager ID.

    If this function is invoked in the functions decorated by @enable_plugin_lifecycle,
    the plugins are cached and the methods declared in LifecycleAware are invoked.

    Args:
        manager_id: Manager ID (prefix of the plugin configuration file)
    Returns:
        OOB plugin
    """
    if loader := _PLUGIN_LOADER_HOLDER.get():
        return loader.get_oob(manager_id)
    return plugin_manager.get_oob_plugin(manager_id)

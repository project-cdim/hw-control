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

"""Plugin extensions.

This module defines interfaces to extend the functionality of plugins.
"""

from abc import ABC, abstractmethod


class LifecycleAware(ABC):
    """Interface of the plugin managing its lifecycle."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize plugin.

        This method is invoked just after the plugin is created.
        Typically allocate the resources that will be released by finalize().
        """

    @abstractmethod
    def finalize(self) -> None:
        """Finalize plugin.

        This method is invoked just before the plugin is destroyed.
        Typically release the resources allocated by initialize().
        """

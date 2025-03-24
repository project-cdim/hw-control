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

"""HW control API - load mapping table

Loads the mapping table file data used when generating a response
for the information acquisition API into memory.
"""

from fastapi import APIRouter
from app.core.info.info_utils import load_mapping_table
from app.common import constants

router = APIRouter(prefix=f"{constants.BASE_URL}/v1")


def startup_load_mapping():
    """Startup load mapping table

    Read the mapping table file at FastAPI startup event.
    """

    # Reads the mapping table file used in the information acquisition process (response generation).
    load_mapping_table()


router.add_event_handler("startup", startup_load_mapping)

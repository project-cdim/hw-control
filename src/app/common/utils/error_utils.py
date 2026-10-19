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

"""HW control - Error Utilities.

Some utilities widely used in HW control.

"""


def remove_duplicates(errors: list) -> list:
    """Remove duplicates error information.

    Remove error information for duplicate error

    Args:
        errors (list): error information list

    Returns:
            list: error information list
    """
    # If the error information is not valid (None, [], etc.), it is returned as is.
    if not errors:
        return errors

    # Initialize the error list to be stored.
    # (To speed up the existence determination, set() is used to store only the error separately.)
    err_list = set()
    # Initialize the error information array to be returned.
    rtn_errors = []

    for error_item in errors:
        error_identifier = frozenset(error_item.items())
        # If it does not yet exist, add it to the return list.
        if error_identifier not in err_list:
            # Add error information to the error information array to be returned.
            rtn_errors.append(error_item)
            # Store the error in the error list.
            err_list.add(error_identifier)

    return rtn_errors

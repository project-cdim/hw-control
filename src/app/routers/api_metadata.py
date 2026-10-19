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

"""This module defines API metadata and provides factory functions for generating API metadata.

- OpenAPI tag definitions:
    This module contains OpenAPI tag definitions used for FastAPI documentation.
    The tags defined here are set to the openapi_tags argument when instantiating
    the FastAPI class and are loaded into the application.
    To avoid duplicate tag names, all tags are managed collectively in this module.

    The tags defined in this module are also set for each endpoint and are used to
    group endpoints in the API documentation.

- Factory Function for Error Response Specification:
    Provides functions to generate error response specification dictionaries for use in FastAPI endpoints.

    For each endpoint, the error case response specification can be defined for each HTTP status code.
    For details, see: https://fastapi.tiangolo.com/advanced/additional-responses/

    If there is only one error case for a status code, use `error_case_spec_factory`.
    Set the error case description in the `case_description` argument.

    If there are multiple error cases for a status code, use `error_cases_spec_factory`.
    Set the simplified description for the status code in the `case_description` argument.
    Set the concrete description for each error case in the `sub_case_descriptions` argument.

    - Factory Function Usage Example in endpoint declarator:

        from src.app.routers import api_metadata
        @router.put(
            path="/path/to/endpoint",
            # ...omitted for brevity...
            responses = {
                422: api_metadata.validation_error_case_spec_factory("The request parameter is invalid or missing."),
                500: api_metadata.error_cases_spec_factory(
                    "An internal server error occurred.",
                    [
                        "The Fabric Manager failed to control the link state.",
                        "The application configuration is invalid or missing.",
                    ]
                ),
            }
"""

from pydantic import BaseModel, Field

from app.routers import response_models

# Define the openapi_tags for FastAPI documentation.
DEVICE_CONTROL_API = "Device Control API"
DEVICE_CONTROL_API_TAG = {
    "name": DEVICE_CONTROL_API,
    "description": (
        "This API provides endpoints for changing the configuration of a node by controlling the link state "
        "between the upstream side device and the downstream side device. "
        "It also controls the power state of each device."
    ),
}

DEVICE_INFO_API = "Device Information API"
DEVICE_INFO_API_TAG = {
    "name": DEVICE_INFO_API,
    "description": (
        "This API provides endpoints for retrieving information about devices within a node, "
        "such as memory, storage, network devices, and CPUs. "
        "It allows clients to obtain device lists, detailed device specifications, resource information, "
        "and metric data for each device. "
    ),
}

# Define the Introduction of API specifications
HW_CONTROL_API_DESCRIPTION = """
## Introduction of hw-control API specifications

### What is hw-control?

hw-control is one of the API services that make up CDIM.
It abstracts hardware-specific interactions and enables unified management of Composable Disaggregated Infrastructure
(CDI) hardware resources and the fabric-related devices that interconnect them, regardless of vendor implementation.

hw-control provides the following main APIs:

- **Device Control API**
- **Device Information API**

please refer to each API's section for more details.

### Device ID

In hw-control, each device is uniquely identified by a **Device ID** (UUID4).
Most APIs require you to specify this Device ID to select the target device for operations.

### Error Code

In error cases, hw-control APIs return a response with the following schema:

```json
{
    "code": "< An error code will be provided here >",
    "message": "< A detailed error message will be provided here >"
}
```

The "code" field represents the error code, which follows the error code system described below.
This code allows clients to identify the type and category of the error that occurred.
The "message" field contains a human-readable error message describing the error in detail.

For HTTP status code 422 (request parameter validation error), the response additionally includes
a "detail" field containing structured information about which request parameters failed validation
and why:

```json
{
    "code": "< An error code will be provided here >",
    "message": "< A detailed error message will be provided here >",
    "detail": [
        {
            "type": "< The type of the validation error will be provided here >",
            "loc": ["< The location of the invalid request parameter will be provided here >"],
            "msg": "< A message describing the validation error will be provided here >",
            "input": "< The invalid input value will be provided here >"
        }
    ]
}
```

Each error code consists of 11 characters, with the following structure:
- **1st character:** Error flag (`E`: error, `C`: critical error)
- **2nd character:** Recoverable flag (`R`: can be retried, `F`: cannot be retried)
- **3rd-5th characters:** Error category code (identifies the type of error)
- **6th-8th characters:** Plugin code (`BAS`: main application, others: plugin)
- **9th-11th characters:** Detailed error code (identifies the specific error)

Example: `EF013BAS000`

#### Error Category Code

The error category code (characters 3 to 5 in the error code) identifies the type of error that occurred.
Below are the main error category codes used in hw-control:

Error category codes:

- `003`: **Bad request**
    - Returned when the request is invalid or malformed.
- `004`: **Control Object error**
    - Returned when an error occurs during operate Control Object
      (e.g., CDI hardware resources management module, fabric-related management module).
- `005`: **Resource busy**
    - Returned when the target resource is busy.
- `007`: **Configuration error**
    - Returned when there is a system or parameter configuration error.
- `010`: **Internal error**
    - Returned when an unexpected internal server error occurs.
- `011`: **Request conflict**
    - Returned when the request conflicts with the current resource state.
- `012`: **Dependency service error**
    - Returned when a failure occurs in an external dependency (e.g., Secret API or Authorization Server).
- `013`: **Resource not found**
    - Returned when the specified resource cannot be found.

Example:
- `EF003BAS000` → Bad request
- `EF013BAS000` → Resource not found

"""

# Dictionary type used as an example of the response body schema for error cases.
# The values are written abstractly and omitted for brevity.
ERROR_EXAMPLE = {
    "code": "< An error code will be provided here >",
    "message": "< A detailed error message will be provided here >",
}

# Dictionary type used as an example of the response body schema for the request parameter
# validation error case (HTTP 422). The values are written abstractly and omitted for brevity.
VALIDATION_ERROR_EXAMPLE = {
    "code": "< An error code will be provided here >",
    "message": "< A detailed error message will be provided here >",
    "detail": [
        {
            "type": "< The type of the validation error will be provided here >",
            "loc": ["< The location of the invalid request parameter will be provided here >"],
            "msg": "< A message describing the validation error will be provided here >",
            "input": "< The invalid input value will be provided here >",
        },
    ],
}


class ErrorResponseSpec(BaseModel):
    """Data model for representing the error response specification used in FastAPI's responses argument.

    This model defines the structure of error response metadata for API documentation.
    It includes a description of the error case, the response model class representing the error response body,
    and the content dictionary containing example data in JSON format.

    Attributes:
        description (str): A short description of the error case, suitable for API documentation.
        model (Type[BaseModel]): The response model class representing the error response body.
        content (dict): A dictionary containing the error response example in JSON format.
    """

    description: str = Field(
        description="A short description of the error case, suitable for API documentation.",
    )
    model: type[BaseModel] = response_models.ErrorResponseModel
    content: dict = Field(description="A dictionary containing the error response example in JSON format.")


def error_case_spec_factory(case_description: str) -> dict:
    """Generate a response specification for a single error case for one HTTP status code for API documentation.

    This function creates a dictionary representing the error response specification
    for a single error case associated with a specific HTTP status code, suitable for constructing
    the value for a FastAPI responses entry. The generated dictionary is intended to be used for
    documenting error cases in the automatically generated API documentation.

    Args:
        case_description (str): Description text for the specific error case.
            This will be used as the response's description in the API documentation.

    Returns:
        dict: A dictionary representing the error response specification for a single error case
            corresponding to one HTTP status code.

    Example usage:
        from src.app.routers import api_metadata

        @router.put(
            path="/path/to/endpoint",
            ...
            responses = {
                422: api_metadata.error_case_spec_factory(
                    case_description="The request parameter is invalid or missing."
                ),
        }
    """
    # Set single example
    error_content_example = {"application/json": {"example": ERROR_EXAMPLE}}

    response = ErrorResponseSpec(description=case_description, content=error_content_example).model_dump()
    return response


def validation_error_case_spec_factory(case_description: str) -> dict:
    """Generate a response specification for a request parameter validation error case (HTTP 422).

    Unlike `error_case_spec_factory`, this includes the `detail` field showing structured
    validation error information, since HTTP 422 responses are always generated by
    `custom_validation_exception_handler`, which returns `ValidationErrorResponseModel`.

    Args:
        case_description (str): Description text for the specific error case.
            This will be used as the response's description in the API documentation.

    Returns:
        dict: A dictionary representing the error response specification for the 422 error case.

    Example usage:
        from src.app.routers import api_metadata

        @router.put(
            path="/path/to/endpoint",
            ...
            responses = {
                422: api_metadata.validation_error_case_spec_factory(
                    case_description="The request parameter validation error."
                ),
        }
    """
    # Set single example
    error_content_example = {"application/json": {"example": VALIDATION_ERROR_EXAMPLE}}

    response = ErrorResponseSpec(
        description=case_description,
        model=response_models.ValidationErrorResponseModel,
        content=error_content_example,
    ).model_dump()
    return response


def error_cases_spec_factory(case_description: str, sub_case_descriptions: list[str]) -> dict:
    """Generate a response specification for multiple error cases for one HTTP status code for API documentation.

    This function creates a dictionary representing the error response specification
    for multiple error cases associated with a specific HTTP status code, suitable for constructing
    the value for a FastAPI responses entry. The generated dictionary is intended to be used for
    documenting error cases in the automatically generated API documentation.

    Args:
        case_description (str): Simplified description for the error cases corresponding to the HTTP status code.
        sub_case_descriptions (list[str]): List of concrete description for each specific error case,
            used as summaries in the API documentation.

    Returns:
        dict: A dictionary representing the error response specification for multiple error cases.

    Example usage:
        from src.app.routers import api_metadata

        @router.put(
            path="/path/to/endpoint",
            ...
            responses = {
                500: api_metadata.error_cases_spec_factory(
                    "An internal server error occurred.",
                    [
                        "The Fabric Manager failed to control the link state.",
                        "The application configuration is invalid or missing.",
                    ]
                ),
            }
    """
    # Build examples dictionary for sub case
    examples_dict = {
        f"error case{str(index)}": {
            "summary": description,
            "value": ERROR_EXAMPLE,
        }
        for index, description in enumerate(sub_case_descriptions)
    }

    # Build the content dictionary using the model structure
    error_content_examples = {"application/json": {"examples": examples_dict}}

    # Use the ErrorResponseSpec model to construct the error cases specification
    error_response_specification = ErrorResponseSpec(
        description=case_description, content=error_content_examples
    ).model_dump()
    return error_response_specification

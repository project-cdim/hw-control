# hw-control

hw-control - Pluggable Hardware Controller

## Requirements

- Python 3.13 and later
- [pdm](https://pdm-project.org/en/latest/)
- Docker (required for running integration tests)

## How to install dependencies

```bash
pdm sync
```

## How to start API server

```bash
pdm run start
```

### Environment Variables

- `HW_CONTROL_LOGGING_RAISE_EXCEPTIONS`
  - This variable set [`logging.raiseExceptions`](https://docs.python.org/3.13/library/logging.html#logging.raiseExceptions).
  - Default to `False`.

- `HW_CONTROL_AUTHORIZATION_SERVER_TOKEN_ENDPOINT`
  - This variable specifies the access token endpoint url of the Authorization Server.
  - e.g. `https://authorization-server.example.com/path/to/access_token_endpoint`

- `HW_CONTROL_AUTHORIZATION_SERVER_TIMEOUT`
  - This variable specifies the timeout value for sending access token requests to the Authorization Server's access token endpoint.
  - Please specify in seconds.
  - Default to `3`.

- `HW_CONTROL_SECRET_API_HOST`
  - This variable specifies the Secret API host.
  - Default to `localhost`.

- `HW_CONTROL_SECRET_API_PORT`
  - This variable specifies the Secret API port.
  - Default to `3500`.

- `HW_CONTROL_SECRET_API_PATH`
  - This variable specifies the Secret API base path.
  - Default to `/v1.0/secrets/`.

- `HW_CONTROL_SECRET_API_TIMEOUT`
  - This variable specifies the timeout value for sending secret requests to the Secret API.
  - Please specify in seconds.
  - Default to `3`.

- `HW_CONTROL_CONFIG_FILE_DIR`
  - This variable specifies the base directory relative to which the configuration files are located.
  - Default to `/opt/cdim/hw-control/config/`.

- `HW_CONTROL_DATA_FILE_DIR`
  - This variable specifies the base directory relative to which the data files are located.
  - Default to `/opt/cdim/hw-control/data/`.

- `HW_CONTROL_PLUGIN_FILE_DIR`
  - This variable specifies the base directory relative to which the plugin configuration files are located.
  - Default to `/opt/cdim/hw-control/data/plugins`.

- `HW_CONTROL_DEVICE_MANAGER_DB_URL`
  - This variable specifies the connection URL for the device management database.
  - The URL must follow the [SQLAlchemy database URL format](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls).
  - This variable is required.

- `HW_CONTROL_DEVICE_MANAGER_DB_POOL_SIZE`
  - This variable specifies the base number of connections maintained in the device management database connection pool.
  - Default to `5`.

- `HW_CONTROL_DEVICE_MANAGER_DB_MAX_OVERFLOW`
  - This variable specifies the maximum number of temporary connections allowed beyond the device management database connection pool size.
  - Default to `10`.

- `HW_CONTROL_DEVICE_MANAGER_DB_POOL_TIMEOUT`
  - This variable specifies the timeout value in seconds for acquiring a connection from the device management database connection pool.
  - Please specify in seconds.
  - Default to `30`.

- `HW_CONTROL_DEVICE_MANAGER_DB_POOL_RECYCLE`
  - This variable specifies the time in seconds after which device management database connections are recycled.
  - Please specify in seconds.
  - Default to `1800`.

- `HW_CONTROL_DEVICE_MANAGER_DB_ECHO`
  - This variable controls whether SQLAlchemy logs all SQL statements executed against the device management database.
  - Set to `true` to enable SQL logging. Not recommended for production use.
  - Default to `false`.

- `HW_CONTROL_PLUGIN_MAX_RESPONSE_SIZE`
  - This variable specifies the maximum allowed size of a response received from a remote plugin.
  - Please specify in bytes.
  - Default to `1048576` (1 MiB).

### Configuration files

The configuration files is located within the directory specified by the environment variable HW_CONTROL_CONFIG_FILE_DIR.  
If the environment variable is not set, it defaults to /opt/cdim/hw-control/config/.  
You need to create a directory to place the configuration files.  

#### Configuration files list

<!-- markdownlint-disable MD033 -->
| No  | File Name                                                | File Summary                             |
| --- | -------------------------------------------------------- | ---------------------------------------- |
| 1   | invalid_serial_number.json                               | Invalid Serial Number Configuration File |
| 2   | device_attribute_setting.yaml                            | Device attribute setting file            |
| 3   | logging_config.yaml                                      | logging system configuration file        |
<!-- markdownlint-enable MD033 -->

#### 1. invalid_serial_number.json

This configuration file manages invalid serial numbers.  
It is used to mark serial numbers as invalid, such as when they are set to zero or duplicated across multiple devices, and to identify devices using other information.  
Invalid serial numbers are listed in this file.  
However, if you do not need to manage invalid serial numbers, you don't need to create this file.  

##### 1.1. Configuration items of invalid_serial_number.json

| Item                   | Description                                                       |
| ---------------------- | ----------------------------------------------------------------- |
| oobDeviceID            | OOB Device ID. Identifier to identify a device in the OOB plugin. |
| PCIeVendorId           | PCIe vendor ID of the device connected to the DSP(*1).            |
| PCIeDeviceId           | PCIe device ID of the device connected to the DSP(*1).            |
| PCIeDeviceSerialNumber | PCIe device serial number of the device connected to the DSP(*1). |
| CPUSerialNumber        | Serial number of the CPU device (host) connected to the USP(*2).  |
| CPUManufacturer        | Manufacturer of the CPU device (host) connected to the USP(*2).   |
| CPUModel               | Model number of the CPU device (host) connected to the USP(*1).   |

  *1  Downstream Switch Port. Refers to the switch port type to which the device is connected.  
  *2  Upstream Switch Port. Refers to the switch port type to which the host (CPU device) is connected.  

If invalid serial numbers are not defined, an empty list (`[]`) should be set within the file or the file itself should not be deployed.

##### 1.2. Example of invalid_serial_number.json

1. With invalid serial number settings:

    ``` json
    [
        {
            "PCIeVendorId": null,
            "PCIeDeviceId": null,
            "PCIeDeviceSerialNumber": null,
            "CPUSerialNumber": "987654321",
            "CPUManufacturer": "AMD",
            "CPUModel": "ABCDEF",
            "switchSerialNumber": null,
            "switchManufacturer": null,
            "switchModel": null
        },
        {
            "PCIeVendorId": "1af4",
            "PCIeDeviceId": "1042",
            "PCIeDeviceSerialNumber": null,
            "CPUSerialNumber": null,
            "CPUManufacturer": null,
            "CPUModel": null,
            "switchSerialNumber": null,
            "switchManufacturer": null,
            "switchModel": null
        },
    ]
    ```

    Null values are ignored for serial number information, and devices matching the manufacturer and model information are targeted.  
    If serial number values are not null, all serial number, manufacturer, and model information must match.  

1. Without invalid serial number settings:

    ```json
    []
    ```

#### 2. device_attribute_setting.yaml

Currently, there is no need to change the settings in this file, but the file itself needs to exist.  
Therefore, this file need to be created.  
You can use the file registered in the config directory of the repository.  

##### 2.1. Example of file settings

1. Please write the following content to device_attribute_setting.yaml.  
   There is no need to change each setting value.  

    ```yaml
    ---
    DEFAULT:
      agent:
        url: http://0.0.0.0:8100
        timeout: 600
      specific_data:
        diskID: 00000000000000000000
        macAddress: 00:00:00:00:00:00
    ...
    ```

#### 3. logging_config.yaml

This configuration file defines the default logging system used by hw-control.
Specify the path to this file in the `--log-config` argument when starting hw-control with uvicorn.
This will automatically configure the logging system when the uvicorn server starts.
See [Uvicorn documentation](https://www.uvicorn.org/settings/#logging) for further details.

If you want to customize the logging system, copy and edit this file, then specify the path in the startup argument.

### Data files

The data files is located within the directory specified by the environment variable HW_CONTROL_DATA_FILE_DIR.  
If the environment variable is not set, it defaults to /opt/cdim/hw-control/data/.  
You need to create a directory to place the data files.  

#### Data files list

| No  | File Name               | File Summary                            |
| --- | ----------------------- | --------------------------------------- |
| 1   | device_id_info.json     | Device ID Management File               |
| 2   | device_id_info.json.tmp | Temporary files for device_id_info.json |
| 3   | device_attribute.yaml   | Device attribute file                   |

##### 1. device_id_info.json

A management file that stores device information.  
Only the Device ID Management feature has access to this file. The user does not need to edit it.  
This file is generated automatically.  

##### 2. device_id_info.json.tmp

This file will be temporarily created when updating the device_id_info.json file and will be deleted after the update is complete.

##### 3. device_attribute.yaml

This file is automatically generated based on the `device_attribute_setting.yaml` configuration file.  
Users do not need to edit this file directly.  

## How to read API specification

1. Start API server
1. Access <http://localhost:8000/redoc>

## How to run lint

```bash
pdm run lint
```

## How to run unittest

```bash
pdm run test
```

## How to run integration tests

```bash
pdm run test-it
```

## Directories

- plugins directory
  - ./src/plugins
- log output directory
  - /var/log/cdim

## License

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)

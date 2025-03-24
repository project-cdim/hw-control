# hw-control

hw-control - Pluggable Hardware Controller

## Requirements

- Python 3.12 and later
- [pdm](https://pdm-project.org/en/latest/)

## How to install dependencies

```bash
pdm sync
```

## How to start API server

```bash
pdm run start
```

### Environment Variables

- `HW_CONTROL_LOG_DIR`
  - This variable specifies the log directory path.
  - Default to `/var/log/cdim`.

- `HW_CONTROL_LOG_FILE`
  - This variable specifies the log file name.
  - Default to `app_hw_control.log`.

- `HW_CONTROL_LOGGING_LEVEL`
  - This variable specifies the logging level.(DEBUG/INFO/WARN/ERROR/CRITICAL)
  - Default to `INFO`.

- `HW_CONTROL_LOG_ROTATION_SIZE`
  - This variable specifies the maximum size of the log.
  - Default to `1000000`.

- `HW_CONTROL_LOG_BACKUP_FILES`
  - This variable specifies the number of log histories.
  - Default to `3`.

- `HW_CONTROL_LOG_STDOUT`
  - This variable specifies whether to output information to the standard output.(True/False)
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
  - Specify that the end of the path should end with a slash "/".
  - Default to `/opt/cdim/hw-control/config/`.

- `HW_CONTROL_DATA_FILE_DIR`
  - This variable specifies the base directory relative to which the data files are located.
  - Specify that the end of the path should end with a slash "/".
  - Default to `/opt/cdim/hw-control/data/`.

### Configuration files

The configuration files is located within the directory specified by the environment variable HW_CONTROL_CONFIG_FILE_DIR.  
If the environment variable is not set, it defaults to /opt/cdim/hw-control/config/.  
You need to create a directory to place the configuration files.  

#### Configuration files list

<!-- markdownlint-disable MD033 -->
| No | File Name | File Summary |
| -- | -- | -- |
| 1 | invalid_serial_number.json | Invalid Serial Number Configuration File |
| 2 | device_attribute_setting.yaml <br> device_attribute.yaml | device attribute setting file |
<!-- markdownlint-enable MD033 -->

#### 1. invalid_serial_number.json

This configuration file manages invalid serial numbers.  
It is used to mark serial numbers as invalid, such as when they are set to zero or duplicated across multiple devices, and to identify devices using other information.  
Invalid serial numbers are listed in this file.  
However, if you do not need to manage invalid serial numbers, you don't need to create this file.  

##### 1.1. Configuration items of invalid_serial_number.json

| Item | Description |
| -- | -- |
| oobDeviceID | OOB Device ID. Identifier to identify a device in the OOB plugin. |
| PCIeVendorId | PCIe vendor ID of the device connected to the DSP(*1). |
| PCIeDeviceId | PCIe device ID of the device connected to the DSP(*1). |
| PCIeDeviceSerialNumber | PCIe device serial number of the device connected to the DSP(*1). |
| CPUSerialNumber | Serial number of the CPU device (host) connected to the USP(*2). |
| CPUManufacturer | Manufacturer of the CPU device (host) connected to the USP(*2). |
| CPUModel | Model number of the CPU device (host) connected to the USP(*1). |

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

##### 2. device_attribute_setting.yaml and device_attribute.yaml

Currently, there is no need to change the settings in this file, but the file itself needs to exist.  
Therefore, these files need to be created.  
You can use the files registered in the config directory of the repository.  

###### 2.1. Example of file settings

1. Please write the following content to device_attribute_setting.yaml.  
   There is no need to change each setting value.  

    ```yaml
    ---
    DEFAULT:
        agent:
            url: http://0.0.0.0:8100
            timeout: 600
        specific_data:
            disk_id: 00000000000000000000
            macaddress: 00:00:00:00:00:00
    ...
    ```

1. Please write the following content to device_attribute.yaml.  
   There is no need to change each setting value.  

    ```yaml
    ---
    ...
    ```

### Data files

The data files is located within the directory specified by the environment variable HW_CONTROL_DATA_FILE_DIR.  
If the environment variable is not set, it defaults to /opt/cdim/hw-control/data/.  
You need to create a directory to place the data files.  

#### Data files list

| No | File Name | File Summary |
| -- | -- | -- |
| 1 | device_id_info.json | Device ID management File |
| 2 | device_id_info.json.tmp | Temporary files for device_id_info.json |

##### 1. device_id_info.json

A management file that stores device information.  
Only the device ID management feature has access to this file. The user does not need to edit it.  
This file is generated automatically.  

##### 2. device_id_info.json.tmp

This file will be temporarily created when updating the device_id_info.json file and will be deleted after the update is complete.

## How to read API specification

1. Start API server
1. Access <http://localhost:8000/docs>

## How to run lint

```bash
pdm run lint
```

## How to run unittest

```bash
pdm run test
```

## Directories

- plugins directory
  - ./src/plugins
- log output directory
  - /var/log/cdim

## License

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)

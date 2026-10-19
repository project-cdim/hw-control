# Changelog 0.2

## [0.2.1](https://github.com/project-cdim/hw-control/compare/v0.2.0...v0.2.1) - 2026-10-19

The changes from v0.2.0 are as follows:

### Features

- Added a new database-backed Device Manager for managing device information. Note that migration from the legacy Device ID Manager to Device Manager is planned for a future release.
- Added support for communicating with plugins deployed as separate services over HTTP, in preparation for the future migration from the existing Python module-based plugins. Note that the service plugin interface is planned for a future release.
- Added a property (`SecureEraseCapability`) that indicates whether secure erasure of storage is possible.
- Enabled handling of devices of unknown type.

### Breaking Changes

- Changed validation-error (422) `message` field to a fixed generic string to prevent leaking internal file paths.
- Added a new `detail` field to validation-error (422) responses to return structured validation error details.
- Removed the built-in device-exclusive lock module; busy-device handling is now delegated to plugins.

### Other Changes

- Fixed a security issue where the OAuth client secret could be exposed in plaintext logs.
- Migrated from pylint and Black to Ruff.
- Various internal test infrastructure improvements (integration test suites for Device Manager, authorization, and API layers).
- Added pip-audit as a dependency checking tool and addressed several security vulnerabilities.
- Added deptry for dependency consistency checking.

## [0.2.0](https://github.com/project-cdim/hw-control/compare/v0.1.1...v0.2.0) - 2026-03-18

The changes from v0.1.1 are as follows:

### Features

- Added support for devices controlled by multiple Fabric Managers. Note that this implementation will be refactored to improve maintainability in a future release.
- Added support for devices controlled by multiple Out-of-band Managers.
- Added new device type. (sourceFabricAdapter, destinationFabricAdapter)

### Bug Fixes

- Updated control-object error messages to reflect device-to-device aggregation.
- Fixed a bug where response trace logs were not output in the fallback error handler.
- Fixed logging config tests to be environment-independent by using temporary log files.
- Correct mistake in the property names displayed in the API documentation.

### Breaking Changes

- Removed deprecated legacy Aggregation Control endpoint.
- We will change it so that the socketNum included in the CPU information always returns 1.
- Delete device_attribute.yaml from the config directory.

### Other Changes

- Updated to Python 3.13, refreshed dependencies, updated tests, and reformatted with latest Black.
- Updated uvicorn dependency to version 0.40.0 with standard extras.
- Updated `pyproject.toml` to comply with PEP 639 license specification.
- Migrated correlation ID management to asgi-correlation-id library.
- Fixed code smells in logging config file.
- Removed unused logger instantiation from log settings module.
- Moved the data mapping loading process at startup from service startup to FastAPI's recommended LifeSpan.

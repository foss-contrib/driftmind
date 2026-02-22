# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Releasing a New Version

1. Update version in `pyproject.toml`
2. Update fallback version in `src/driftmind/constants.py` (for editable installs)
3. Update this CHANGELOG with release date and changes
4. Commit changes: `git commit -am "Release v0.X.0"`
5. Create git tag: `git tag v0.X.0`
6. Push: `git push && git push --tags`

---

## [0.5.0] - 2026-02-19

### Added
- `use_api_native_format` option on `DriftMindClient`: when enabled, the client accepts camelCase input dictionaries and returns camelCase output keys, matching the raw API format. Provides backwards compatibility for users migrating from pre-v0.3 clients. The existing `accept_java_date_format` option remains independent.
- `docs/API_NATIVE.md` documenting the `use_api_native_format` option with usage examples and migration guidance for pre-v0.3 users.
- GitHub Actions workflow for automated PyPI publishing on version tags (`publish.yml`) with Trusted Publishing and tag-version verification.
- Expanded test suite from 74 to 117 tests (92% coverage, up from 88%). New coverage includes `health_check`, retry logic (5xx/429/Timeout), error paths (401/403/404/417/500), model edge cases, and date conversion roundtrip.
- Native format test suite (`TestNativeFormatClient`) with camelCase input fixtures covering all endpoints.

### Fixed
- Corrected `timeStampIntervalInSeconds` API misspelling: users now see `timestampIntervalInSeconds` (camelCase) or `timestamp_interval_in_seconds` (snake_case). The client handles the API's misspelling transparently.
- Added `plotly` to `examples` optional dependency.
- Fixed notebook install instructions in README.md to use `uv sync --extra examples`.
- Restored Python 3.9 compatibility (broken by the v0.4.1 minimum-version bump): added `from __future__ import annotations` to `exceptions.py`; added `eval-type-backport` as a dependency so Pydantic v2 can evaluate `X | None` annotations at runtime on Python 3.9; added `__init__.py` to `driftmind/data` so `importlib.resources.files()` resolves correctly on Python 3.9.

### Changed
- Renamed `utils/helpers.py` → `utils/core.py` and `utils/generator.py` → `utils/demo.py` for clearer module naming.
- Renamed back `examples/demo.ipynb` → `examples/cold_start_demo.ipynb` for better understanding of its purpose.
- Moved `numpy`, `pandas`, `matplotlib` from core dependencies to `[examples]` optional extra, lightening the default install.
- Moved plotting functions (`plot_actual_vs_predicted`, `plot_time_series`) from `utils/core` to `utils/demo` with lazy imports.
- Updated CI test workflow: upgraded `astral-sh/setup-uv` from v4 to v5, pinned Python 3.9, consolidated lint and format into a single step, simplified test command.
- Added Python 3.13 classifier to `pyproject.toml`.
- Pytest config: coverage runs by default (`--cov=driftmind`), added explicit test discovery patterns, switched `addopts` to list format.
- Added `[tool.coverage.run]` configuration with `source = ["src"]` and excluded non-essential modules (`__init__.py`, `exceptions.py`, `utils/demo.py`) from coverage reporting.

---

## [0.4.2] - 2026-02-17

### Added
- `accept_java_date_format` option on `DriftMindClient` to work with Java SimpleDateFormat patterns directly, bypassing automatic Python↔Java conversion.
- Bundled OpenAPI spec (`openapi.yaml`) as package resource data for contract testing and spec-driven mocking.
- Added `jsonschema`, `openapi-core`, and `openapi-spec-validator` as dev dependencies for contract testing.

### Fixed
- Corrected project keywords in `pyproject.toml`.
- Fixed broken links and inaccuracies in `README.md`.

### Changed
- Migrated test mocking from static fixture files to spec-driven examples via `get_openapi_response_example`, ensuring mocked responses always reflect the current OpenAPI spec.
- Flattened `fixtures/responses/` directory structure (removed `success/` and `errors/` subdirectories).

### Removed
- Removed 20 unused JSON fixture files superseded by spec-driven mocking.
- Removed `record_api_responses.py` references from testing documentation.

---

## [0.4.1] - 2026-02-01

### Added
- GitHub Actions CI/CD pipeline for automated testing and linting
- Universal resolution support in `uv.lock` for seamless cross-OS syncing (Windows/Linux)

### Changed
- **BREAKING**: Minimum Python version raised from 3.8 to 3.9
- Migrated build backend from `setuptools` to `hatchling` for better `uv` integration
- Improved documentation structure and consistency
- Updated pre-commit config to exclude untracked files
- Refined Ruff linting rules to include `PYI` and `TID` for better type-hinting and import management

### Fixed
- Minor corrections in documentation
- Fixed self-referencing `all` extra in `pyproject.toml`

### Removed
- Unused notebook files and obsolete code

---

## [0.4.0] - 2026-01-31

### Added
- Comprehensive test suite: 65 tests with 85% coverage
- Complete API documentation in `docs/API.md`
- Utils package refactoring (`utils/helpers.py`, `utils/generator.py`)
- Quickstart example (`examples/quickstart.py`)
- Testing documentation (`tests/TESTING.md`)
- Environment template (`.env.example`)
- Pre-commit hooks with ruff for code quality

### Changed
- Enhanced error handling with retry logic and exponential backoff
- Connection pooling for better performance
- Sensitive data protection in logs
- Bulk operations with partial success handling
- Pydantic v2 models with automatic snake_case ↔ camelCase conversion
- Improved README

### Fixed
- Bulk operations field handling (`results` vs `details`)
- Import paths after utils refactoring
- Notebook imports to use public API

---

## [0.3.0] - 2026-02-01

### Changed
- Implemented snake_case to camelCase translation for all client inputs and outputs.
- Replaced manual key patching with Pydantic aliases for automated schema-driven validation.

### Fixed
- Applied `ruff format` and `ruff check` across the codebase for PEP 8 compliance.
- Renamed `readme.md` to `README.md` for standard documentation discovery.

### Removed
- Deleted unused and redundant test files to streamline the repository.

---

## [0.1.1] - 2025-01-07

### Added
- Initial release with basic DriftMind API client
- Core operations: create, delete, feed data, get predictions
- Credential loading from environment variables
- Plotting utilities for time series visualization
- Date format conversion utilities
- Test data generator for sin/cos/tan with drifts

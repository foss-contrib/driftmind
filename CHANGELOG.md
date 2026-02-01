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

## [0.3.0] - 2026-02-01

### Changed
- Implemented snake_case to camelCase translation for all client inputs and outputs.
- Replaced manual key patching with Pydantic aliases for automated schema-driven validation.

### Fixed
- Applied `ruff format` and `ruff check` across the codebase for PEP 8 compliance.
- Renamed `readme.md` to `README.md` for standard documentation discovery.

### Removed
- Deleted unused and redundant test files to streamline the repository.

## [0.1.1] - 2025-01-07

### Added
- Initial release with basic DriftMind API client
- Core operations: create, delete, feed data, get predictions
- Credential loading from environment variables
- Plotting utilities for time series visualization
- Date format conversion utilities
- Test data generator for sin/cos/tan with drifts

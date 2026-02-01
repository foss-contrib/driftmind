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

## [0.4.1] - 2026-02-01

### Added
- GitHub Actions CI/CD pipeline for automated testing and linting

### Changed
- **BREAKING**: Minimum Python version raised from 3.8 to 3.9
- Improved documentation structure and consistency
- Updated pre-commit config to exclude untracked files

### Fixed
- Minor corrections in documentation

### Removed
- Unused notebook files and obsolete code

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

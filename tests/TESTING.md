# Testing Guide

## Overview

The DriftMind client uses **pytest** with the **responses** library to mock HTTP requests. All tests use recorded fixtures from real API interactions, ensuring tests match actual API behavior.

**Test Framework:**
- **pytest** - Test runner and fixture management
- **responses** - HTTP mocking library
- **pytest-cov** - Coverage reporting

**Test Strategy:**
1. **Client-side validation** - Pydantic model validation (no mocking)
2. **API interactions** - Mocked with real API response fixtures
3. **Error handling** - Both client and API errors
4. **Retry logic** - Transient failure handling

---

## Test Results

✅ **All 65 tests passing** (execution time: ~6.9 seconds)

```
============================= test session starts ==============================
tests/test_client.py (30 tests) PASSED                                   [ 46%]
tests/test_client_edge_cases.py (10 tests) PASSED                       [ 61%]
tests/test_data.py (9 tests) PASSED                                      [ 75%]
tests/test_utils.py (15 tests) PASSED                                    [100%]

============================== 65 passed in 6.90s ===============================
```

## Test Coverage

| Module          | Coverage | Status                 |
|-----------------|----------|------------------------|
| `__init__.py`   | 100%     | ✅ Complete             |
| `exceptions.py` | 100%     | ✅ Complete             |
| `utils.py`      | 96%      | ✅ Excellent            |
| `models.py`     | 94%      | ✅ Excellent            |
| `constants.py`  | 93%      | ✅ Excellent            |
| `client.py`     | 82%      | ✅ Excellent            |
| **Overall**     | **85%**  | ✅ **Production Ready** |

**Conclusion:** Comprehensive test coverage across all critical modules. Client library is production-ready.

---

## Test Distribution

### test_client.py (30 tests)
**Client Validation (7 tests)** - Empty/whitespace forecaster_id, missing fields, invalid constraints, duplicate features, inconsistent data

**Success Cases (8 tests)** - Create, feed, forecast, get details, get data (empty/with data), list, delete

**Error Cases (5 tests)** - Wrong features (400), insufficient data (422), not found (404), empty payload, wrong format, auth error (401)

**Bulk Operations (6 tests)** - Bulk feed (200/206/417/REDIS), delete all (success/failures)

**Infrastructure (2 tests)** - Retry logic, context manager

### test_client_edge_cases.py (10 tests)
**Logging Protection (2 tests)** - API key redaction, protection disabled

**Error Handling (8 tests)** - Empty/whitespace API key/URL, trailing slash handling, non-JSON responses, connection errors, custom session, session cleanup

### test_data.py (9 tests)
- Request/response serialization (snake_case ↔ camelCase)
- Required field validation
- Cross-field validation
- Date format conversion

### test_utils.py (15 tests)
**Credential Loading (5 tests)** - Load from env, missing key/URL errors, dotenv not installed, explicit .env path

**Plotting Functions (5 tests)** - Plot actual vs predicted (with data/empty/missing column), plot time series (with data/empty)

**Date Conversion (5 tests)** - Smart date parsing (string/non-string/invalid), Python↔Java format conversion

## Coverage Recommendations

**Current state:** Production-ready with 85% coverage

**Remaining uncovered areas:**
- `utils/generator.py` (16%) - Data generation utilities, not critical for client functionality
- Minor edge cases in client error handling

**No urgent action needed** - All critical paths are well tested.

## Test Infrastructure

### conftest.py - Shared Fixtures

Provides reusable fixtures for all tests:

**Client fixtures:**
- `api_key` - Test API key
- `base_url` - API endpoint URL  
- `client` - Fresh DriftMindClient instance per test

**Data fixtures:**
- `minimal_spec_input` - Minimal forecaster configuration
- `full_spec_input` - Full forecaster configuration
- `api_creation_response` - Successful creation response
- `api_validation_error` - Validation error response

**Helper function:**
- `load_fixture(filename)` - Loads JSON fixtures from requests/responses directories

### Directory Structure

```
tests/
├── fixtures/
│   ├── requests/              # Request payloads (snake_case, as users provide)
│   │   ├── bulk_feed_data_*.json
│   │   ├── create_forecaster_minimal.json
│   │   ├── feed_data_*.json
│   │   ├── full_spec_input.json
│   │   └── minimal_spec_input.json
│   └── responses/
│       ├── success/           # 2xx responses
│       │   ├── bulk_feed_data_*.json
│       │   ├── create_forecaster_201.json
│       │   ├── delete_forecaster_200.json
│       │   ├── feed_data_200.json
│       │   ├── forecast_200.json
│       │   ├── get_forecaster_data_*.json
│       │   ├── get_forecaster_details_200.json
│       │   └── list_forecasters_200.json
│       └── errors/            # 4xx/5xx responses
│           ├── bulk_feed_data_417*.json
│           ├── create_forecaster_401_token_rejected.json
│           ├── feed_data_400_*.json
│           ├── forecast_422_insufficient_data.json
│           └── get_forecaster_details_404_not_found.json
├── conftest.py                # Shared fixtures and helpers
├── test_client.py             # Client API tests (30 tests)
├── test_client_edge_cases.py  # Edge cases & logging (10 tests)
├── test_data.py               # Model validation tests (9 tests)
├── test_utils.py              # Utils & plotting tests (15 tests)
└── record_api_responses.py    # Script to capture real API responses
```

### Test Files

**test_client.py (30 tests)** - Main API interaction tests using mocked responses

**test_client_edge_cases.py (10 tests)** - Edge cases, logging protection, error handling

**test_data.py (9 tests)** - Pydantic model validation and serialization

**test_utils.py (15 tests)** - Utility functions (credentials, plotting, date conversion)

---

## Recording New Fixtures

To capture real API responses for new test scenarios:

```bash
# Run the recorder script
uv run python tests/record_api_responses.py
```

**What it does:**
1. Connects to the real DriftMind API using credentials from `.env`
2. Executes API calls for various scenarios (success and error cases)
3. Saves request payloads to `fixtures/requests/` (snake_case format)
4. Saves responses to:
   - `fixtures/responses/success/` for 2xx responses
   - `fixtures/responses/errors/` for 4xx/5xx responses

**Adding new scenarios:**
1. Edit `tests/record_api_responses.py`
2. Add your scenario to the `main()` function
3. Run the script to capture fixtures
4. Write tests using the new fixtures

## Running Tests

```bash
# All tests
uv run pytest tests/

# With coverage
uv run pytest tests/ --cov=driftmind --cov-report=term-missing

# Verbose output
uv run pytest tests/ -v

# Specific test file
uv run pytest tests/test_client.py -v

# Specific test class
uv run pytest tests/test_client.py::TestCreateForecaster -v
```

## Adding New Tests

1. **Capture fixtures** (if needed):
   - Add scenario to `record_api_responses.py`
   - Run recorder to capture real responses

2. **Write test**:
   ```python
   @responses.activate
   def test_new_scenario(self, client, base_url):
       request = load_request("endpoint_scenario.json")
       response = load_response("endpoint_200_scenario.json")
       
       responses.add(
           responses.METHOD,
           f"{base_url}/path",
           json=response["body"],
           status=response["status_code"],
       )
       
       result = client.method(request)
       assert ...
   ```

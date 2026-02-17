# Testing Guide

## Overview

The DriftMind client uses **pytest** with the **responses** library to mock HTTP requests. Tests use a combination of JSON request fixtures and examples extracted at runtime from the bundled OpenAPI spec (`src/driftmind/data/openapi.yaml`), ensuring mocked responses always match the contract.

**Test Framework:**
- **pytest** - Test runner and fixture management
- **responses** - HTTP mocking library
- **pytest-cov** - Coverage reporting
- **jsonschema** / **openapi-core** - Contract validation against the OpenAPI spec

**Test Strategy:**
1. **Client-side validation** - Pydantic model validation (no mocking needed)
2. **Spec-driven mocking** - API responses are extracted from OpenAPI examples via `get_openapi_response_example`, not hardcoded
3. **Contract testing** - Request/response validated against the OpenAPI spec via `validate_contract`
4. **Error handling** - Both client-side and API errors
5. **Retry logic** - Transient failure handling

---

## Running Tests

```bash
# All tests (use python -m pytest for src layout)
uv run python -m pytest tests/

# With coverage
uv run python -m pytest tests/ --cov=driftmind --cov-report=term-missing

# Verbose output
uv run python -m pytest tests/ -v

# Specific test file
uv run python -m pytest tests/test_client.py -v

# Specific test class
uv run python -m pytest tests/test_client.py::TestCreateForecaster -v

# Specific test
uv run python -m pytest tests/test_client.py::TestClientValidation::test_rejects_duplicate_features -v
```

---

## Test Distribution

### test_client.py (29 tests)

**TestClientValidation (9 tests)** - Client-side validation without API calls:
- `test_rejects_invalid_forecaster_id` (3 parametrized: empty, whitespace, None)
- `test_rejects_missing_required_fields`
- `test_rejects_invalid_window_sizes` (2 parametrized: output > input)
- `test_rejects_duplicate_features`
- `test_rejects_inconsistent_data_lengths`
- `test_rejects_non_numeric_data`

**TestCreateForecaster (2 tests)** - Create endpoint with contract validation:
- `test_create_minimal_success` (201)
- `test_create_auth_error` (401)

**TestFeedData (4 tests)** - Feed data endpoint:
- `test_feed_single_point_success` (200)
- `test_feed_wrong_features_error` (400)
- `test_feed_empty_payload_error` (client-side)
- `test_feed_wrong_format_error` (client-side)

**TestForecast (2 tests)** - Forecast endpoint:
- `test_forecast_success` (200)
- `test_forecast_insufficient_data_error` (422)

**TestGetForecasterDetails (2 tests)** - Details endpoint:
- `test_get_details_success` (200)
- `test_get_details_not_found_error` (404)

**TestGetForecasterData (2 tests)** - Observations endpoint:
- `test_get_data_success` (200)
- `test_get_data_empty_success` (200, empty data)

**TestDeleteForecaster (2 tests)** - Delete endpoint:
- `test_delete_forecaster_success` (200)
- `test_delete_forecaster_not_found` (404)

**TestContextManager (2 tests)** - Resource cleanup:
- `test_context_manager_closes_session_verified`
- `test_manual_close`

**TestJavaDateFormatClient (1 test)** - `accept_java_date_format` end-to-end:
- `test_create_with_java_date_format` (201, Java date pattern passthrough)

**TestBulkOperations (3 tests)** - Multi-forecaster operations:
- `test_bulk_feed_data_all_success` (200)
- `test_bulk_feed_data_partial_success` (206)
- `test_delete_all_forecasters_success` (list + delete chain)

### test_client_edge_cases.py (7 tests)

**TestLoggingProtection (1 test)** - API key redaction in DEBUG logs

**TestClientEdgeCases (4 tests)** - Constructor and connection edge cases:
- `test_empty_api_key_error`
- `test_base_url_trailing_slash_stripped`
- `test_non_json_response_error` (502 HTML response)
- `test_connection_error_retry` (DNS failure, max retries)

**TestContractExtremeCases (2 tests)** - Client resilience against malformed server responses:
- `test_server_returns_wrong_data_type` (string where int expected)
- `test_server_missing_required_field` (missing objectId)

### test_data.py (15 tests)

**TestForecasterCreationSchema (9 tests)** - Pydantic model validation and serialization:
- `test_request_serialization_mapping` (2 parametrized: minimal + full spec)
- `test_response_parsing_coercion` (camelCase API response → snake_case model)
- `test_request_validation_required_fields` (4 parametrized: each required field)
- `test_response_error_handling_schema`
- `test_request_logic_constraints` (output_size vs input_size)

**TestJavaDateFormatOption (6 tests)** - `accept_java_date_format` context flag:
- `test_spec_accepts_java_date_format` (Java pattern accepted with flag)
- `test_spec_converts_python_to_java_without_flag` (default stores Python format)
- `test_spec_serialization_passthrough_java` (API serialization keeps Java as-is)
- `test_spec_serialization_converts_without_flag` (default converts Python→Java)
- `test_config_keeps_java_format_with_flag` (response parsing keeps Java)
- `test_config_converts_java_to_python_without_flag` (response converts Java→Python)

### test_utils.py (15 tests)

**TestLoadCredentials (5 tests)** - Credential loading from env / .env file:
- `test_load_from_env_success`, `test_missing_api_key_error`, `test_missing_api_url_error`, `test_dotenv_not_installed_error`, `test_load_with_dotenv_path`

**TestPlotting (5 tests)** - Plot functions:
- `test_plot_actual_vs_predicted`, `test_plot_actual_vs_predicted_empty`, `test_plot_actual_vs_predicted_missing_column`, `test_plot_time_series`, `test_plot_time_series_empty`

**TestDateConversion (5 tests)** - Date parsing and format conversion:
- `test_smart_parse_date_string`, `test_smart_parse_date_non_string`, `test_smart_parse_date_invalid`, `test_convert_strftime_to_java`, `test_convert_java_to_strftime`

---

## Test Infrastructure

### conftest.py - Shared Fixtures

**Client fixtures:**
- `api_key` - Test API key (`"test-api-key"`)
- `root_url` - API root (`"https://api.thingbook.io/access/api"`)
- `base_url` - Full versioned URL (`root_url + "/driftmind/v1"`)
- `client` - Fresh `DriftMindClient` instance per test

**OpenAPI / Contract fixtures (session-scoped):**
- `spec_dict` - Raw OpenAPI dictionary loaded from `driftmind.data/openapi.yaml`
- `openapi_spec` - `openapi-core` Spec object

**Validation fixtures:**
- `validate_contract(response_call, path_pattern)` - Validates both request and response bodies against the OpenAPI spec using jsonschema
- `get_openapi_response_example(path, method, status_code, example_name)` - Extracts response examples from the OpenAPI spec at runtime, resolving `$ref` and array schemas. This is used to build mock responses for `responses.add()` so that mocked API responses always reflect the current spec rather than stale fixture files.

**Data fixtures:**
- `load_json_fixture(filename)` - Loads JSON fixtures.

### Fixture Directory

```
tests/fixtures/
    ├── bulk_feed_data_multiple.json
    ├── bulk_feed_data_partial.json
    ├── create_forecaster_minimal.json
    ├── feed_data_single_point.json
    ├── feed_data_wrong_features.json
    ├── full_spec_input.json
    ├── full_spec_input_java.json
    └── minimal_spec_input.json
```

---

## Adding New Tests

Most tests use OpenAPI spec examples via `get_openapi_response_example` and validate with `validate_contract`:

```python
@responses.activate
def test_new_scenario(self, client, base_url, get_openapi_response_example, validate_contract):
    SPEC_PATH = "/driftmind/v1/forecasters/{forecasterId}/predictions"
    forecaster_id = "test-id"

    mock_response = copy.deepcopy(get_openapi_response_example(SPEC_PATH, "GET", 200))

    responses.add(
        responses.GET,
        f"{base_url}/forecasters/{forecaster_id}/predictions",
        json=mock_response,
        status=200,
    )

    result = client.forecast(forecaster_id)
    assert "anomaly_score" in result

    validate_contract(responses.calls[0], path_pattern=SPEC_PATH)
```

For tests that need specific request payloads (e.g., testing client-side validation of user input), add a JSON file to `fixtures/` and load it with `load_json_fixture()`.

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
4. **Error handling** - Both client-side and API errors (400, 401, 403, 404, 417, 422, 500)
5. **Retry logic** - Transient failure handling (5xx, 429, Timeout, ConnectionError)
6. **Model validation** - Pydantic schema tests for all request/response models

---

## Running Tests

```bash
# All tests (coverage is enabled by default via pyproject.toml)
uv run python -m pytest tests/

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

## Coverage

Coverage is collected automatically on every test run (configured in `pyproject.toml` via `--cov=driftmind`). Reports are printed to the terminal and written as HTML to `htmlcov/`. No minimum threshold is enforced.

| Module | Coverage |
|---|---|
| `client.py` | 89% |
| `constants.py` | 93% |
| `models.py` | 96% |
| `utils/core.py` | 96% |
| **Total** | **92%** |

Excluded from coverage: `__init__.py` (re-exports only), `exceptions.py` (simple hierarchy), `utils/demo.py` (plotting utilities for examples).

---

## Test Distribution

### test_client.py (58 tests)

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

**TestCreateForecasterExtended (4 tests)** - Extended create scenarios:
- `test_create_full_spec_success` (201, all optional fields)
- `test_create_location_header_id_extraction` (201, Location header)
- `test_create_400_validation_error` (400, VALIDATION_FAILED)
- `test_create_misspelling_fix_timestamp_interval` (timeStampIntervalInSeconds)

**TestFeedData (4 tests)** - Feed data endpoint:
- `test_feed_single_point_success` (200)
- `test_feed_wrong_features_error` (400)
- `test_feed_empty_payload_error` (client-side)
- `test_feed_wrong_format_error` (client-side)

**TestFeedDataExtended (2 tests)** - Extended feed scenarios:
- `test_feed_data_404_not_found` (404)
- `test_feed_data_alias_delegates_to_feed_point` (feed_data → feed_point)

**TestForecast (2 tests)** - Forecast endpoint:
- `test_forecast_success` (200)
- `test_forecast_insufficient_data_error` (422)

**TestForecastExtended (1 test)** - Extended forecast scenarios:
- `test_forecast_404_not_found` (404)

**TestGetForecasterDetails (2 tests)** - Details endpoint:
- `test_get_details_success` (200)
- `test_get_details_not_found_error` (404)

**TestGetForecasterDetailsExtended (1 test)** - Extended details scenarios:
- `test_get_details_403_forbidden` (403)

**TestGetForecasterData (2 tests)** - Observations endpoint:
- `test_get_data_success` (200)
- `test_get_data_empty_success` (200, empty data)

**TestGetForecasterDataExtended (1 test)** - Extended observations scenarios:
- `test_get_data_404_not_found` (404)

**TestDeleteForecaster (2 tests)** - Delete endpoint:
- `test_delete_forecaster_success` (200)
- `test_delete_forecaster_not_found` (404)

**TestDeleteForecasterExtended (1 test)** - Extended delete scenarios:
- `test_delete_forecaster_401_auth_error` (401)

**TestContextManager (2 tests)** - Resource cleanup:
- `test_context_manager_closes_session_verified`
- `test_manual_close`

**TestJavaDateFormatClient (1 test)** - `accept_java_date_format` end-to-end:
- `test_create_with_java_date_format` (201, Java date pattern passthrough)

**TestNativeFormatClient (8 tests)** - `use_api_native_format` end-to-end (camelCase I/O):
- `test_create_with_camel_case_input` (201, camelCase input and output)
- `test_create_with_full_spec_native_input` (201, full spec + Java dates + camelCase)
- `test_get_details_returns_camel_case` (200)
- `test_forecast_returns_camel_case` (200)
- `test_list_forecasters_returns_camel_case` (200)
- `test_delete_returns_camel_case` (200)
- `test_bulk_feed_with_camel_case_input` (200)
- `test_delete_all_with_native_format` (list + delete chain)

**TestBulkOperations (7 tests)** - Multi-forecaster operations:
- `test_bulk_feed_data_all_success` (200)
- `test_bulk_feed_data_partial_success` (206)
- `test_delete_all_forecasters_success` (list + delete chain)
- `test_bulk_feed_data_all_failed` (417)
- `test_bulk_feed_data_unexpected_error` (500)
- `test_delete_all_forecasters_empty_list` (empty list → no deletes)
- `test_delete_all_forecasters_partial_failure` (some deletes fail)

**TestHealthCheck (2 tests)** - Health check endpoint:
- `test_health_check_success` (list_forecasters succeeds → True)
- `test_health_check_reraises_api_error` (401 re-raised)

**TestListForecasters (2 tests)** - List endpoint edge cases:
- `test_list_forecasters_401_auth_error` (401)
- `test_list_forecasters_empty_list` (200, empty array)

### test_client_edge_cases.py (15 tests)

**TestLoggingProtection (1 test)** - API key redaction in DEBUG logs

**TestLoggingProtectionExtended (2 tests)** - Extended logging protection:
- `test_multiple_sensitive_headers_redacted` (authorization, x-api-key)
- `test_logging_protection_disabled` (enable_logging_protection=False)

**TestClientEdgeCases (8 tests)** - Constructor and connection edge cases:
- `test_empty_api_key_error`
- `test_base_url_trailing_slash_stripped`
- `test_non_json_response_error` (502 HTML response)
- `test_whitespace_api_key_error` (whitespace-only key)
- `test_empty_base_url_error` (empty string)
- `test_custom_session_injection` (external Session, _owns_session=False)
- `test_custom_timeout_and_retry_params` (custom values stored)
- `test_connection_error_retry` (DNS failure, max retries)

**TestContractExtremeCases (2 tests)** - Client resilience against malformed server responses:
- `test_server_returns_wrong_data_type` (string where int expected)
- `test_server_missing_required_field` (missing objectId)

**TestRetryLogic (4 tests)** - Retry behaviour for transient errors:
- `test_5xx_triggers_retry_then_succeeds` (500 → 200 on 2nd attempt)
- `test_429_triggers_retry` (429 rate limit → 200 on 2nd attempt)
- `test_timeout_retries_then_raises` (Timeout after max retries)
- `test_non_retryable_exception_raises_immediately` (InvalidURL, 1 call only)

### test_data.py (26 tests)

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

**TestForecasterSpecExtended (4 tests)** - Extended ForecasterSpec validation:
- `test_blank_feature_name_rejected` (blank string in features)
- `test_date_format_required_when_custom_flag_set` (use_custom_date_format=True, no format)
- `test_initialization_date_required_when_flag_set` (use_initialization_date=True, no date)
- `test_similarity_threshold_out_of_range` (< 0.6 and > 1.0)

**TestDataFeedPayloadSchema (3 tests)** - DataFeedPayload validation:
- `test_empty_dict_rejected` (empty dict)
- `test_empty_lists_rejected` (empty value lists)
- `test_inconsistent_lengths_rejected` (mismatched list lengths)

**TestFeaturePredictionSchema (1 test)** - FeaturePrediction validation:
- `test_array_length_mismatch_rejected` (predictions vs timestamps)

**TestForecasterDeletionResponseSchema (3 tests)** - ForecasterDeletionResponse:
- `test_valid_deletion_response` (FORECASTER_DELETED accepted)
- `test_unexpected_message_rejected` (Literal constraint)
- `test_extra_fields_rejected` (extra="forbid")

**TestBulkDataFeedPayloadSchema (1 test)** - BulkDataFeedPayload:
- `test_empty_payloads_list_rejected` (min_length=1)

### test_utils.py (18 tests)

**TestLoadCredentials (5 tests)** - Credential loading from env / .env file:
- `test_load_from_env_success`, `test_missing_api_key_error`, `test_missing_api_url_error`, `test_dotenv_not_installed_error`, `test_load_with_dotenv_path`

**TestPlotting (5 tests)** - Plot functions:
- `test_plot_actual_vs_predicted`, `test_plot_actual_vs_predicted_empty`, `test_plot_actual_vs_predicted_missing_column`, `test_plot_time_series`, `test_plot_time_series_empty`

**TestDateConversion (8 tests)** - Date parsing and format conversion:
- `test_smart_parse_date_string`, `test_smart_parse_date_non_string`, `test_smart_parse_date_invalid`, `test_convert_strftime_to_java`, `test_convert_java_to_strftime`, `test_roundtrip_conversion` (Python→Java→Python), `test_unmapped_tokens_passthrough` (non-mapped chars kept), `test_smart_parse_date_datetime_passthrough` (datetime object returned as-is)

---

## Test Infrastructure

### conftest.py - Shared Fixtures

**Client fixtures:**
- `api_key` - Test API key (`"test-api-key"`)
- `root_url` - API root (`"https://api.thingbook.io/access/api"`)
- `base_url` - Full versioned URL (`root_url + "/driftmind/v1"`)
- `client` - Fresh `DriftMindClient` instance per test
- `native_client` - `DriftMindClient` with `use_api_native_format=True` for camelCase I/O tests

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
    ├── full_spec_input_dateformat_java.json
    ├── minimal_spec_input.json
    ├── create_forecaster_minimal_native.json
    ├── full_spec_input_native.json
    └── bulk_feed_data_multiple_native.json
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

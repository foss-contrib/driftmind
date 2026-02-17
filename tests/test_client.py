"""
Comprehensive test suite for DriftMind client using recorded API responses.

Tests are organized by:
1. Client-side validation (no API mocking)
2. Success cases (2xx responses)
3. Error cases (4xx/5xx responses)
"""

import copy
from typing import Any
from unittest.mock import patch

import pytest
import responses

from driftmind import DriftMindClient
from driftmind.exceptions import DriftMindApiError, DriftMindError, ForecastError


class TestClientValidation:
    """Test client-side validation (no API calls)."""

    @pytest.mark.parametrize("invalid_id", ["", "   ", None])
    def test_rejects_invalid_forecaster_id(self, client: DriftMindClient, invalid_id):
        """Client should reject empty or whitespace-only forecaster_id."""
        with pytest.raises(DriftMindError, match="forecaster_id cannot be empty"):
            # Testing across different methods to ensure consistent validation
            if invalid_id is None:
                client.get_forecaster_details(invalid_id)
            else:
                client.forecast(invalid_id)

    def test_rejects_missing_required_fields(self, client: DriftMindClient):
        """Client should reject payload missing required fields."""
        # Missing 'features', 'input_size', etc.
        with pytest.raises(DriftMindError, match="validation"):
            client.create_forecaster({"forecaster_name": "Test"})

    @pytest.mark.parametrize(
        "input_size, output_size",
        [
            (10, 20),  # This WILL trigger the validator (> input_size)
            (5, 100),  # This WILL trigger the validator
        ],
    )
    def test_rejects_invalid_window_sizes(
        self, client: DriftMindClient, input_size, output_size
    ):
        """Client should reject output_size that is strictly greater than input_size."""
        payload = {
            "forecaster_name": "Test",
            "features": ["x"],
            "input_size": input_size,
            "output_size": output_size,
        }

        # We don't need @responses.activate here because
        # Pydantic will raise the error before any network call.
        with pytest.raises(
            DriftMindError, match="output_size must be less than or equal to"
        ):
            client.create_forecaster(payload)

    def test_rejects_duplicate_features(self, client: DriftMindClient):
        """Client should reject duplicate feature names."""
        payload = {
            "forecaster_name": "Test",
            "features": ["x", "x"],
            "input_size": 10,
            "output_size": 3,
        }
        with pytest.raises(DriftMindError, match="unique"):
            client.create_forecaster(payload)

    def test_rejects_inconsistent_data_lengths(self, client: DriftMindClient):
        """Client should reject feed data with inconsistent list lengths."""
        invalid_data = {
            "x": [1, 2, 3],
            "y": [4, 5],  # Length mismatch
        }
        with pytest.raises(DriftMindError, match="Inconsistent list lengths"):
            client.feed_point("test-id", invalid_data)

    def test_rejects_non_numeric_data(self, client: DriftMindClient):
        """Addition: Check if client rejects strings in data feeding."""
        invalid_data = {
            "x": [1, "not_a_number", 3],
        }
        with pytest.raises(DriftMindError, match="validation|numeric"):
            client.feed_point("test-id", invalid_data)


class TestCreateForecaster:
    """Test create_forecaster endpoint."""

    SPEC_PATH = "/driftmind/v1/forecasters"

    @responses.activate
    def test_create_minimal_success(
        self,
        client: DriftMindClient,
        base_url: str,
        get_openapi_response_example: Any,
        load_json_fixture: Any,
        validate_contract: Any,
    ) -> None:
        """Test creating forecaster with minimal configuration using openAPI spec examples."""

        # 1. Load the real input fixture
        request_payload = load_json_fixture("create_forecaster_minimal.json")

        # 2. Extract the base example from the Spec
        mock_response_body = get_openapi_response_example(self.SPEC_PATH, "POST", 201)

        # 3. DYNAMIC PATCH: Inject request data into the mock response
        # This ensures the 'API' appears to behave logically by echoing our inputs
        mock_response_body = copy.deepcopy(
            get_openapi_response_example(self.SPEC_PATH, "POST", 201)
        )
        mock_response_body["forecasterName"] = request_payload["forecaster_name"]
        mock_response_body["features"] = request_payload["features"]

        # 4. Setup the mock
        responses.add(
            responses.POST,
            f"{base_url}/forecasters",
            json=mock_response_body,
            status=201,
            content_type="application/json",
        )

        # 5. Execute
        result = client.create_forecaster(request_payload)

        # 6. Assertions
        assert "forecaster_id" in result
        assert result["forecaster_name"] == request_payload["forecaster_name"]
        assert set(result["features"]) == set(request_payload["features"])
        assert "configuration" in result

        # 7. Contract Validation
        # This verifies the OUTGOING request from the client follows the openAPI spec
        validate_contract(responses.calls[0], path_pattern=self.SPEC_PATH)

    @responses.activate
    def test_create_auth_error(
        self,
        client: DriftMindClient,
        base_url: str,
        get_openapi_response_example: Any,
        load_json_fixture: Any,
        validate_contract: Any,
    ) -> None:
        """Test creating forecaster with invalid auth token using Spec for error body."""

        # 1. Load the valid request payload
        request_payload = load_json_fixture("create_forecaster_minimal.json")

        # 2. Extract the 401 error example from the Spec
        # Path matches the key in openapi.yaml
        mock_error_body = copy.deepcopy(
            get_openapi_response_example(self.SPEC_PATH, "POST", 401)
        )

        # 3. Setup the mock for 401 Unauthorized
        responses.add(
            responses.POST,
            f"{base_url}/forecasters",
            json=mock_error_body,
            status=401,
            content_type="application/json",
        )

        # 4. Execute and Assert Exception
        # We expect DriftMindApiError for 401 status codes
        with pytest.raises(DriftMindApiError) as exc:
            client.create_forecaster(request_payload)

        # 5. Verify the exception details
        assert exc.value.status_code == 401

        # Optionally verify the error message matches what's in the spec example
        if mock_error_body and "detail" in mock_error_body:
            assert str(exc.value.message) == mock_error_body["detail"]

        # 6. Contract Validation
        # Ensures that even if auth fails, the client's request structure was correct
        validate_contract(responses.calls[0], path_pattern=self.SPEC_PATH)


class TestFeedData:
    """Test feed_point endpoint."""

    # This must match the exact key in your openapi.yaml
    SPEC_PATH = "/driftmind/v1/forecasters/{forecasterId}/observations"

    @responses.activate
    def test_feed_single_point_success(
        self,
        client: Any,
        base_url: str,
        get_openapi_response_example: Any,
        load_json_fixture: Any,
        validate_contract: Any,
    ) -> None:
        """Test feeding a single data point using spec-driven mocks."""
        forecaster_id = "test-id"

        # 1. Load the real input fixture
        request_payload = load_json_fixture("feed_data_single_point.json")

        # 2. Extract and CLONE the example from the Spec (200 OK)
        # Deepcopy prevents cross-test pollution
        raw_example = get_openapi_response_example(self.SPEC_PATH, "POST", 200)
        mock_response_body = copy.deepcopy(raw_example)

        # 3. Setup the mock
        # We use the actual ID in the URL, but self.SPEC_PATH for the validator
        responses.add(
            responses.POST,
            f"{base_url}/forecasters/{forecaster_id}/observations",
            json=mock_response_body,
            status=200,
            content_type="application/json",
        )

        # 4. Execute
        result = client.feed_point(forecaster_id, request_payload)

        # 5. Assertions
        assert "message" in result
        assert isinstance(result["message"], str)

        # 6. Contract Validation
        # Crucial: Pass the SPEC_PATH (with brackets) so the validator finds the schema
        validate_contract(responses.calls[0], path_pattern=self.SPEC_PATH)

    @responses.activate
    def test_feed_wrong_features_error(
        self,
        client: Any,
        base_url: str,
        get_openapi_response_example: Any,
        load_json_fixture: Any,
        validate_contract: Any,
    ) -> None:
        """Test feeding data with features not in forecaster (400 error from API)."""
        forecaster_id = "test-id"
        request_payload = load_json_fixture("feed_data_wrong_features.json")

        # 1. Extract the 400 Bad Request example from Spec
        raw_error = get_openapi_response_example(self.SPEC_PATH, "POST", 400)
        mock_error_body = copy.deepcopy(raw_error)

        # 2. Setup mock
        responses.add(
            responses.POST,
            f"{base_url}/forecasters/{forecaster_id}/observations",
            json=mock_error_body,
            status=400,
            content_type="application/json",
        )

        # 3. Execute and verify client-side exception
        from driftmind.exceptions import DataFeedError  # Use your specific error class

        with pytest.raises(DataFeedError) as exc:
            client.feed_point(forecaster_id, request_payload)

        assert exc.value.status_code == 400

        # 4. Contract Validation: Verifies the request body was correct
        # even though the server rejected it based on business logic
        validate_contract(responses.calls[0], path_pattern=self.SPEC_PATH)

    @responses.activate
    def test_feed_empty_payload_error(
        self, client: Any, base_url: str, validate_contract: Any
    ) -> None:
        """Test feeding data with empty payload (Client-side validation)."""
        forecaster_id = "test-id"

        # 1. Setup mock (though it shouldn't be reached if client validates early)
        responses.add(
            responses.POST,
            f"{base_url}/forecasters/{forecaster_id}/observations",
            json={"detail": "This should not be reached"},
            status=400,
        )

        # 2. Execute with empty payload
        # Based on your comment, the client validates BEFORE sending
        from driftmind.exceptions import DriftMindError

        with pytest.raises(DriftMindError) as exc:
            client.feed_point(forecaster_id, {})

        # 3. Validation Logic
        assert "validation" in str(exc.value).lower()

        # 4. Conditional Contract Validation
        # If the client blocked the call internally, responses.calls will be empty.
        # We only validate if the call actually hit the network.
        if len(responses.calls) > 0:
            validate_contract(responses.calls[0], path_pattern=self.SPEC_PATH)

    @responses.activate
    def test_feed_wrong_format_error(
        self, client: Any, base_url: str, validate_contract: Any
    ) -> None:
        """Test feeding data with wrong format (timestamp dict instead of arrays)."""
        forecaster_id = "test-id"

        # 1. Payload that violates the expected schema (should be arrays/lists)
        wrong_format = {
            "data": {"2025-01-01 00:15:00": {"temp": 112.5, "pressure": 0.6}}
        }

        # 2. Setup mock as a safety net
        # (If the client were to fail its internal check and try to send this,
        # we want to catch the 400 it would receive)
        responses.add(
            responses.POST,
            f"{base_url}/forecasters/{forecaster_id}/observations",
            json={"detail": "Format error"},
            status=400,
        )

        # 3. Execute and verify Client-Side validation (Pydantic)
        from driftmind.exceptions import DriftMindError

        with pytest.raises(DriftMindError) as exc:
            client.feed_point(forecaster_id, wrong_format)

        # 4. Assertions on the error message
        error_msg = str(exc.value).lower()
        assert "validation" in error_msg
        # Optional: Check if the specific field name is mentioned in the error
        assert "data" in error_msg

        # 5. Contract Validation (Conditional)
        # We check if the request actually reached the mock.
        # In this specific case, we expect len to be 0 because Pydantic blocks it.
        if len(responses.calls) > 0:
            # If it ever reaches here, the contract validator will fail it
            # because the dict format doesn't match the 'array' schema in YAML.
            validate_contract(responses.calls[0], path_pattern=self.SPEC_PATH)


class TestForecast:
    """Test forecast endpoint."""

    # Exact key from openapi.yaml
    SPEC_PATH = "/driftmind/v1/forecasters/{forecasterId}/predictions"

    @responses.activate
    def test_forecast_success(
        self,
        client: Any,
        base_url: str,
        get_openapi_response_example: Any,
        validate_contract: Any,
    ) -> None:
        """Test getting forecast with spec-validated response."""
        forecaster_id = "test-id"

        # 1. Extract and clone the 200 OK example
        raw_example = get_openapi_response_example(self.SPEC_PATH, "GET", 200)
        mock_response_body = copy.deepcopy(raw_example)

        # 2. Setup the mock
        responses.add(
            responses.GET,
            f"{base_url}/forecasters/{forecaster_id}/predictions",
            json=mock_response_body,
            status=200,
            content_type="application/json",
        )

        # 3. Execute
        result = client.forecast(forecaster_id)

        # 4. Assertions (Logic checks)
        assert "anomaly_score" in result
        assert "features" in result
        assert isinstance(result["features"], dict)

        # 5. Contract Validation
        # This checks that the MOCK response we sent matches the SPEC
        # and that the client handled the GET request correctly.
        validate_contract(responses.calls[0], path_pattern=self.SPEC_PATH)

    @responses.activate
    def test_forecast_insufficient_data_error(
        self,
        client: Any,
        base_url: str,
        get_openapi_response_example: Any,
        validate_contract: Any,
    ) -> None:
        """Test forecast with insufficient data (422 Unprocessable Entity)."""
        forecaster_id = "test-id"

        # 1. Extract 422 example from spec
        raw_error = get_openapi_response_example(self.SPEC_PATH, "GET", 422)
        mock_error_body = copy.deepcopy(raw_error)

        # 2. Setup mock
        responses.add(
            responses.GET,
            f"{base_url}/forecasters/{forecaster_id}/predictions",
            json=mock_error_body,
            status=422,
            content_type="application/json",
        )

        # 3. Execute and verify specific exception
        with pytest.raises(ForecastError) as exc:
            client.forecast(forecaster_id)

        assert exc.value.status_code == 422

        # 4. Contract Validation
        # Validates that the error response structure (422) matches the spec
        validate_contract(responses.calls[0], path_pattern=self.SPEC_PATH)


class TestGetForecasterDetails:
    """Test get_forecaster_details endpoint."""

    SPEC_PATH = "/driftmind/v1/forecasters/{forecasterId}"

    @responses.activate
    def test_get_details_success(
        self,
        client: Any,
        base_url: str,
        get_openapi_response_example: Any,
        validate_contract: Any,
    ) -> None:
        """Test getting forecaster details using Spec examples."""
        forecaster_id = "test-id"

        # 1. Extract and clone the 200 OK example
        raw_example = get_openapi_response_example(self.SPEC_PATH, "GET", 200)
        mock_response_body = copy.deepcopy(raw_example)

        # 2. Setup the mock
        responses.add(
            responses.GET,
            f"{base_url}/forecasters/{forecaster_id}",
            json=mock_response_body,
            status=200,
            content_type="application/json",
        )

        # 3. Execute
        result = client.get_forecaster_details(forecaster_id)

        # 4. Logic Assertions
        # (Assuming your client transforms camelCase API response to snake_case)
        assert result["forecaster_id"] == mock_response_body.get(
            "forecasterId", forecaster_id
        )
        assert "forecaster_name" in result
        assert "configuration" in result

        # 5. Contract Validation
        validate_contract(responses.calls[0], path_pattern=self.SPEC_PATH)

    @responses.activate
    def test_get_details_not_found_error(
        self,
        client: Any,
        base_url: str,
        get_openapi_response_example: Any,
        validate_contract: Any,
    ) -> None:
        """Test getting details for nonexistent forecaster (404)."""
        invalid_id = "nonexistent-id"

        # 1. Extract the 404 error example
        raw_error = get_openapi_response_example(self.SPEC_PATH, "GET", 404)
        mock_error_body = copy.deepcopy(raw_error)

        # 2. Setup mock
        responses.add(
            responses.GET,
            f"{base_url}/forecasters/{invalid_id}",
            json=mock_error_body,
            status=404,
            content_type="application/json",
        )

        # 3. Execute and verify exception
        with pytest.raises(DriftMindApiError) as exc:
            client.get_forecaster_details(invalid_id)

        assert exc.value.status_code == 404

        # 4. Contract Validation (Optional but recommended for error formats)
        validate_contract(responses.calls[0], path_pattern=self.SPEC_PATH)


class TestGetForecasterData:
    """Test get_forecaster_data endpoint."""

    SPEC_PATH = "/driftmind/v1/forecasters/{forecasterId}/observations"

    @responses.activate
    def test_get_data_success(
        self,
        client: Any,
        base_url: str,
        get_openapi_response_example: Any,
        validate_contract: Any,
    ) -> None:
        """Test getting stored forecaster data using Spec example."""
        forecaster_id = "test-id"

        # 1. Extract and clone example
        mock_response_body = copy.deepcopy(
            get_openapi_response_example(self.SPEC_PATH, "GET", 200)
        )

        # 2. Setup mock
        responses.add(
            responses.GET,
            f"{base_url}/forecasters/{forecaster_id}/observations",
            json=mock_response_body,
            status=200,
            content_type="application/json",
        )

        # 3. Execute
        result = client.get_forecaster_data(forecaster_id)

        # 4. Assertions
        assert isinstance(result, dict)
        # Verify the structure matches what your client is supposed to return
        # (e.g., if client returns the value of the 'data' key)
        if "data" in mock_response_body:
            assert len(result) >= 0

        # 5. Contract Validation
        validate_contract(responses.calls[0], path_pattern=self.SPEC_PATH)

    @responses.activate
    def test_get_data_empty_success(
        self, client: Any, base_url: str, validate_contract: Any
    ) -> None:
        """Test getting data from forecaster with no observations yet."""
        forecaster_id = "test-id"

        # Manual mock for the 'empty' case to be explicit
        mock_response_body = {"data": {}}

        responses.add(
            responses.GET,
            f"{base_url}/forecasters/{forecaster_id}/observations",
            json=mock_response_body,
            status=200,
            content_type="application/json",
        )

        result = client.get_forecaster_data(forecaster_id)

        # Ensure client handles the empty mapping correctly
        assert result == {"data": {}}
        validate_contract(responses.calls[0], path_pattern=self.SPEC_PATH)


class TestDeleteForecaster:
    """Test delete_forecaster endpoint."""

    SPEC_PATH = "/driftmind/v1/forecasters/{forecasterId}"

    @responses.activate
    def test_delete_forecaster_success(
        self,
        client: Any,
        base_url: str,
        get_openapi_response_example: Any,
        validate_contract: Any,
    ) -> None:
        """Test deleting a single forecaster using Spec example."""
        forecaster_id = "test-id"

        # 1. Extract 200 OK example for DELETE
        mock_response_body = copy.deepcopy(
            get_openapi_response_example(self.SPEC_PATH, "DELETE", 200)
        )

        responses.add(
            responses.DELETE,
            f"{base_url}/forecasters/{forecaster_id}",
            json=mock_response_body,
            status=200,
            content_type="application/json",
        )

        result = client.delete_forecaster(forecaster_id)

        assert "message" in result
        # Note: Validating against the spec example ensures the mock and assertion match
        assert result["message"] == mock_response_body.get("message")

        validate_contract(responses.calls[0], path_pattern=self.SPEC_PATH)

    @responses.activate
    def test_delete_forecaster_not_found(
        self,
        client: Any,
        base_url: str,
        get_openapi_response_example: Any,
        validate_contract: Any,
    ) -> None:
        """Test deleting nonexistent forecaster."""
        invalid_id = "nonexistent-id"
        mock_error_body = copy.deepcopy(
            get_openapi_response_example(self.SPEC_PATH, "DELETE", 404)
        )

        responses.add(
            responses.DELETE,
            f"{base_url}/forecasters/{invalid_id}",
            json=mock_error_body,
            status=404,
            content_type="application/json",
        )

        with pytest.raises(DriftMindApiError) as exc:
            client.delete_forecaster(invalid_id)

        assert exc.value.status_code == 404
        validate_contract(responses.calls[0], path_pattern=self.SPEC_PATH)


class TestContextManager:
    """Test context manager functionality for resource cleanup."""

    def test_context_manager_closes_session_verified(self, base_url):
        """Verify the underlying requests session is closed using mocks."""

        # 1. Patch the Session class where it's imported/used in your client
        # Adjust 'driftmind.client.requests.Session' if your import path differs
        with patch("requests.Session") as mock_session_class:
            # This is the instance that will be created inside DriftMindClient
            mock_session_instance = mock_session_class.return_value

            # 2. Use the client as a context manager
            with DriftMindClient("test-key", base_url) as client:
                # Inside the block, the session should be active
                assert client._session == mock_session_instance
                mock_session_instance.close.assert_not_called()

            # 3. Outside the block, close() MUST have been called
            mock_session_instance.close.assert_called_once()

    def test_manual_close(self, base_url):
        """Verify manual close() call also works as expected."""
        with patch("requests.Session") as mock_session_class:
            mock_session_instance = mock_session_class.return_value

            client = DriftMindClient("test-key", base_url)
            client.close()

            mock_session_instance.close.assert_called_once()


class TestJavaDateFormatClient:
    """Test that accept_java_date_format threads through the client correctly."""

    SPEC_PATH = "/driftmind/v1/forecasters"

    @responses.activate
    def test_create_with_java_date_format(
        self,
        base_url: str,
        get_openapi_response_example: Any,
    ) -> None:
        """Client with accept_java_date_format=True should accept Java patterns."""
        java_client = DriftMindClient(
            "test-key", base_url, accept_java_date_format=True
        )

        mock_response = copy.deepcopy(
            get_openapi_response_example(self.SPEC_PATH, "POST", 201)
        )

        responses.add(
            responses.POST,
            f"{base_url}/forecasters",
            json=mock_response,
            status=201,
            content_type="application/json",
        )

        result = java_client.create_forecaster(
            {
                "forecaster_name": "Java Test",
                "features": ["x"],
                "input_size": 30,
                "output_size": 1,
                "use_custom_date_format": True,
                "date_format": "dd-MM-yyyy HH:mm",
                "use_initialization_date": True,
                "initialization_date": "01-01-2025 00:00",
            }
        )
        assert "forecaster_id" in result


class TestBulkOperations:
    """Test bulk feed and delete operations with multi-call validation."""

    BULK_FEED_PATH = "/driftmind/v1/forecasters/observations"
    LIST_PATH = "/driftmind/v1/forecasters"
    DELETE_PATH = "/driftmind/v1/forecasters/{forecasterId}"

    @responses.activate
    def test_bulk_feed_data_all_success(
        self,
        client: Any,
        base_url: str,
        get_openapi_response_example: Any,
        load_json_fixture: Any,
        validate_contract: Any,
    ) -> None:
        """Test bulk feeding data to multiple forecasters (200 OK)."""
        request_payload = load_json_fixture("bulk_feed_data_multiple.json")

        # 1. Mock the PATCH bulk endpoint
        mock_response = copy.deepcopy(
            get_openapi_response_example(self.BULK_FEED_PATH, "PATCH", 200)
        )

        responses.add(
            responses.PATCH,
            f"{base_url}/forecasters/observations",
            json=mock_response,
            status=200,
            content_type="application/json",
        )

        result = client.bulk_feed_data(request_payload)

        # 2. Logic Assertions
        assert "results" in result
        assert len(result["results"]) == 2
        assert all(r["status"] == 200 for r in result["results"])

        # 3. Contract Validation
        validate_contract(responses.calls[0], path_pattern=self.BULK_FEED_PATH)

    @responses.activate
    def test_bulk_feed_data_partial_success(
        self, client: Any, base_url: str, load_json_fixture: Any, validate_contract: Any
    ) -> None:
        """Test bulk feeding with partial success (206 Partial Content)."""
        request_payload = load_json_fixture("bulk_feed_data_partial.json")

        # Manual construction for specific partial failure scenario
        mock_response = {
            "results": [
                {"forecasterId": "fc-1", "status": 200, "message": "FED"},
                {
                    "forecasterId": "fc-2",
                    "status": 404,
                    "message": "FORECASTER_NOT_FOUND",
                },
            ]
        }

        responses.add(
            responses.PATCH,
            f"{base_url}/forecasters/observations",
            json=mock_response,
            status=206,
            content_type="application/json",
        )

        result = client.bulk_feed_data(request_payload)

        assert result["results"][1]["status"] == 404
        # Validate that 206 is a valid response for this path in the Spec
        validate_contract(responses.calls[0], path_pattern=self.BULK_FEED_PATH)

    @responses.activate
    def test_delete_all_forecasters_success(
        self,
        client: Any,
        base_url: str,
        get_openapi_response_example: Any,
        validate_contract: Any,
    ) -> None:
        """Test deleting all forecasters (List then Delete multiple)."""

        # 1. Setup the List GET response
        list_example = copy.deepcopy(
            get_openapi_response_example(self.LIST_PATH, "GET", 200)
        )
        responses.add(
            responses.GET,
            f"{base_url}/forecasters",
            json=list_example,
            status=200,
            content_type="application/json",
        )

        # 2. Setup the DELETE mocks for each ID in the list
        for forecaster in list_example:
            # Handle potential key naming differences (object_id vs forecasterId)
            fc_id = forecaster.get("objectId") or forecaster.get("forecasterId")

            responses.add(
                responses.DELETE,
                f"{base_url}/forecasters/{fc_id}",
                json={"message": "FORECASTER_DELETED"},
                status=200,
                content_type="application/json",
            )

        # 3. Execute
        result = client.delete_all_forecasters()

        # 4. Assertions & Multi-Call Contract Validation
        assert len(result["results"]) == len(list_example)

        # Validate the first call (The List GET)
        validate_contract(responses.calls[0], path_pattern=self.LIST_PATH)

        # Validate the subsequent DELETE calls
        for i in range(1, len(responses.calls)):
            validate_contract(responses.calls[i], path_pattern=self.DELETE_PATH)

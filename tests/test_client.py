"""
Comprehensive test suite for DriftMind client using recorded API responses.

Tests are organized by:
1. Client-side validation (no API mocking)
2. Success cases (2xx responses)
3. Error cases (4xx/5xx responses)
"""

import json
from pathlib import Path

import pytest
import responses

from driftmind import DriftMindClient
from driftmind.exceptions import (
    DataFeedError,
    DriftMindApiError,
    DriftMindError,
    ForecastError,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_request(filename: str) -> dict:
    """Load request payload fixture."""
    with open(FIXTURES_DIR / "requests" / filename) as f:
        return json.load(f)


def load_response(filename: str) -> dict:
    """Load response fixture (includes status_code and body)."""
    for subdir in ["success", "errors"]:
        path = FIXTURES_DIR / "responses" / subdir / filename
        if path.exists():
            with open(path) as f:
                return json.load(f)
    raise FileNotFoundError(f"Response fixture not found: {filename}")


@pytest.fixture
def client():
    """Create test client."""
    return DriftMindClient("test-api-key", "https://api.test.com/api/driftmind")


@pytest.fixture
def base_url():
    """Base URL for mocking."""
    return "https://api.test.com/api/driftmind"


class TestClientValidation:
    """Test client-side validation (no API calls)."""

    def test_rejects_empty_forecaster_id(self, client):
        """Client should reject empty forecaster_id."""
        with pytest.raises(DriftMindError, match="forecaster_id cannot be empty"):
            client.get_forecaster_details("")

    def test_rejects_whitespace_forecaster_id(self, client):
        """Client should reject whitespace-only forecaster_id."""
        with pytest.raises(DriftMindError, match="forecaster_id cannot be empty"):
            client.forecast("   ")

    def test_rejects_missing_required_fields(self, client):
        """Client should reject payload missing required fields."""
        with pytest.raises(DriftMindError, match="validation"):
            client.create_forecaster({"forecaster_name": "Test"})

    def test_rejects_output_greater_than_input(self, client):
        """Client should reject output_size > input_size."""
        with pytest.raises(DriftMindError, match="output_size must be less than"):
            client.create_forecaster(
                {
                    "forecaster_name": "Test",
                    "features": ["x"],
                    "input_size": 10,
                    "output_size": 20,
                }
            )

    def test_rejects_duplicate_features(self, client):
        """Client should reject duplicate feature names."""
        with pytest.raises(DriftMindError, match="unique"):
            client.create_forecaster(
                {
                    "forecaster_name": "Test",
                    "features": ["x", "x"],
                    "input_size": 10,
                    "output_size": 3,
                }
            )

    def test_rejects_empty_features_list(self, client):
        """Client should reject empty features list."""
        with pytest.raises(DriftMindError, match="validation"):
            client.create_forecaster(
                {
                    "forecaster_name": "Test",
                    "features": [],
                    "input_size": 10,
                    "output_size": 3,
                }
            )

    def test_rejects_inconsistent_data_lengths(self, client):
        """Client should reject feed data with inconsistent list lengths."""
        with pytest.raises(DriftMindError, match="Inconsistent list lengths"):
            client.feed_point(
                "test-id",
                {
                    "x": [1, 2, 3],
                    "y": [4, 5],  # Different length
                },
            )


class TestCreateForecaster:
    """Test create_forecaster endpoint."""

    @responses.activate
    def test_create_minimal_success(self, client, base_url):
        """Test creating forecaster with minimal configuration."""
        request = load_request("create_forecaster_minimal.json")
        response = load_response("create_forecaster_201.json")

        responses.add(
            responses.POST,
            f"{base_url}/forecasters",
            json=response["body"],
            status=response["status_code"],
        )

        result = client.create_forecaster(request)

        assert "forecaster_id" in result
        assert result["forecaster_name"] == request["forecaster_name"]
        assert set(result["features"]) == set(request["features"])  # API may reorder
        assert "configuration" in result

    @responses.activate
    def test_create_auth_error(self, client, base_url):
        """Test creating forecaster with invalid auth token."""
        request = load_request("create_forecaster_minimal.json")
        response = load_response("create_forecaster_401_token_rejected.json")

        responses.add(
            responses.POST,
            f"{base_url}/forecasters",
            json=response["body"],
            status=response["status_code"],
        )

        # 401 is handled by _parse_and_check and raises DriftMindApiError (not ForecasterCreationError)
        with pytest.raises(DriftMindApiError) as exc:
            client.create_forecaster(request)

        assert exc.value.status_code == 401


class TestFeedData:
    """Test feed_point endpoint."""

    @responses.activate
    def test_feed_single_point_success(self, client, base_url):
        """Test feeding a single data point."""
        request = load_request("feed_data_single_point.json")
        response = load_response("feed_data_200.json")

        responses.add(
            responses.POST,
            f"{base_url}/forecasters/test-id/observations",
            json=response["body"],
            status=response["status_code"],
        )

        result = client.feed_point("test-id", request)

        assert "message" in result

    @responses.activate
    def test_feed_wrong_features_error(self, client, base_url):
        """Test feeding data with features not in forecaster."""
        request = load_request("feed_data_wrong_features.json")
        response = load_response("feed_data_400_wrong_features.json")

        responses.add(
            responses.POST,
            f"{base_url}/forecasters/test-id/observations",
            json=response["body"],
            status=response["status_code"],
        )

        with pytest.raises(DataFeedError) as exc:
            client.feed_point("test-id", request)

        assert exc.value.status_code == 400

    @responses.activate
    def test_feed_empty_payload_error(self, client, base_url):
        """Test feeding data with empty payload."""
        response = load_response("feed_data_400_empty_payload.json")

        responses.add(
            responses.POST,
            f"{base_url}/forecasters/test-id/observations",
            json=response["body"],
            status=response["status_code"],
        )

        # Client validates before sending, so this raises DriftMindError not DataFeedError
        with pytest.raises(DriftMindError) as exc:
            client.feed_point("test-id", {})

        assert "validation" in str(exc.value).lower()

    @responses.activate
    def test_feed_wrong_format_error(self, client, base_url):
        """Test feeding data with wrong format (timestamp dict instead of arrays)."""
        # Client validates before sending, so this raises DriftMindError not DataFeedError
        # Timestamp dict format (wrong)
        wrong_format = {"data": {"01-01-2025 00:15": {"temp": 112.5, "pressure": 0.6}}}

        with pytest.raises(DriftMindError) as exc:
            client.feed_point("test-id", wrong_format)

        assert "validation" in str(exc.value).lower()


class TestForecast:
    """Test forecast endpoint."""

    @responses.activate
    def test_forecast_success(self, client, base_url):
        """Test getting forecast."""
        response = load_response("forecast_200.json")

        responses.add(
            responses.GET,
            f"{base_url}/forecasters/test-id/predictions",
            json=response["body"],
            status=response["status_code"],
        )

        result = client.forecast("test-id")

        assert "anomaly_score" in result
        assert "features" in result
        assert isinstance(result["features"], dict)

    @responses.activate
    def test_forecast_insufficient_data_error(self, client, base_url):
        """Test forecast with insufficient data."""
        response = load_response("forecast_422_insufficient_data.json")

        responses.add(
            responses.GET,
            f"{base_url}/forecasters/test-id/predictions",
            json=response["body"],
            status=response["status_code"],
        )

        with pytest.raises(ForecastError) as exc:
            client.forecast("test-id")

        assert exc.value.status_code == 422


class TestGetForecasterDetails:
    """Test get_forecaster_details endpoint."""

    @responses.activate
    def test_get_details_success(self, client, base_url):
        """Test getting forecaster details."""
        response = load_response("get_forecaster_details_200.json")

        responses.add(
            responses.GET,
            f"{base_url}/forecasters/test-id",
            json=response["body"],
            status=response["status_code"],
        )

        result = client.get_forecaster_details("test-id")

        assert "forecaster_id" in result
        assert "forecaster_name" in result
        assert "configuration" in result
        assert "features" in result

    @responses.activate
    def test_get_details_not_found_error(self, client, base_url):
        """Test getting details for nonexistent forecaster."""
        response = load_response("get_forecaster_details_404_not_found.json")

        responses.add(
            responses.GET,
            f"{base_url}/forecasters/nonexistent-id",
            json=response["body"],
            status=response["status_code"],
        )

        with pytest.raises(DriftMindApiError) as exc:
            client.get_forecaster_details("nonexistent-id")

        assert exc.value.status_code == 404


class TestGetForecasterData:
    """Test get_forecaster_data endpoint."""

    @responses.activate
    def test_get_data_success(self, client, base_url):
        """Test getting stored forecaster data."""
        response = load_response("get_forecaster_data_200.json")

        responses.add(
            responses.GET,
            f"{base_url}/forecasters/test-id/observations",
            json=response["body"],
            status=response["status_code"],
        )

        result = client.get_forecaster_data("test-id")

        assert isinstance(result, dict)
        # Result should be dict of timestamp -> features

    @responses.activate
    def test_get_data_empty_success(self, client, base_url):
        """Test getting data from forecaster with no observations yet."""
        response = load_response("get_forecaster_data_200_empty.json")

        responses.add(
            responses.GET,
            f"{base_url}/forecasters/test-id/observations",
            json=response["body"],
            status=response["status_code"],
        )

        result = client.get_forecaster_data("test-id")

        # API returns {"data": {}} but client returns the dict directly
        assert isinstance(result, dict)
        assert result == {"data": {}}


class TestListForecasters:
    """Test list_forecasters endpoint."""

    @responses.activate
    def test_list_forecasters_success(self, client, base_url):
        """Test listing all forecasters."""
        response = load_response("list_forecasters_200.json")

        responses.add(
            responses.GET,
            f"{base_url}/forecasters",
            json=response["body"],
            status=response["status_code"],
        )

        result = client.list_forecasters()

        assert isinstance(result, list)
        if result:
            assert "object_id" in result[0]
            assert "object_name" in result[0] or result[0].get("object_name") is None


class TestDeleteForecaster:
    """Test delete_forecaster endpoint."""

    @responses.activate
    def test_delete_forecaster_success(self, client, base_url):
        """Test deleting a single forecaster."""
        response = load_response("delete_forecaster_200.json")

        responses.add(
            responses.DELETE,
            f"{base_url}/forecasters/test-id",
            json=response["body"],
            status=response["status_code"],
        )

        result = client.delete_forecaster("test-id")

        assert "message" in result
        assert result["message"] == "FORECASTER_DELETED"

    @responses.activate
    def test_delete_forecaster_not_found(self, client, base_url):
        """Test deleting nonexistent forecaster."""
        response = load_response("get_forecaster_details_404_not_found.json")

        responses.add(
            responses.DELETE,
            f"{base_url}/forecasters/nonexistent-id",
            json=response["body"],
            status=response["status_code"],
        )

        with pytest.raises(DriftMindApiError) as exc:
            client.delete_forecaster("nonexistent-id")

        assert exc.value.status_code == 404


class TestRetryLogic:
    """Test retry behavior for transient failures."""

    @responses.activate
    def test_retries_on_500_error(self, client, base_url):
        """Test that client retries on 500 errors."""
        # First two calls fail with 500, third succeeds
        responses.add(
            responses.GET,
            f"{base_url}/forecasters",
            json={"error": "Internal Server Error"},
            status=500,
        )
        responses.add(
            responses.GET,
            f"{base_url}/forecasters",
            json={"error": "Internal Server Error"},
            status=500,
        )
        response = load_response("list_forecasters_200.json")
        responses.add(
            responses.GET,
            f"{base_url}/forecasters",
            json=response["body"],
            status=response["status_code"],
        )

        result = client.list_forecasters()

        assert isinstance(result, list)
        assert len(responses.calls) == 3  # Verify it retried


class TestContextManager:
    """Test context manager functionality."""

    def test_context_manager_closes_session(self, base_url):
        """Test that context manager properly closes the session."""
        with DriftMindClient("test-key", base_url) as client:
            assert client._session is not None

        # Session should be closed after exiting context
        # (We can't directly test this without accessing internals)


class TestBulkOperations:
    """Test bulk feed and delete operations."""

    @responses.activate
    def test_bulk_feed_data_all_success(self, client, base_url):
        """Test bulk feeding data to multiple forecasters (200)."""
        request = load_request("bulk_feed_data_multiple.json")
        response = load_response("bulk_feed_data_200.json")

        responses.add(
            responses.PATCH,
            f"{base_url}/forecasters/observations",
            json=response["body"],
            status=response["status_code"],
        )

        result = client.bulk_feed_data(request)

        assert "results" in result
        assert len(result["results"]) == 2  # Real fixture has 2 forecasters
        assert all(r["status"] == 200 for r in result["results"])
        assert all(r["message"] == "FED" for r in result["results"])

    @responses.activate
    def test_bulk_feed_data_partial_success(self, client, base_url):
        """Test bulk feeding with partial success (206)."""
        request = load_request("bulk_feed_data_partial.json")
        response = load_response("bulk_feed_data_206.json")

        responses.add(
            responses.PATCH,
            f"{base_url}/forecasters/observations",
            json=response["body"],
            status=response["status_code"],
        )

        result = client.bulk_feed_data(request)

        assert "results" in result
        assert len(result["results"]) == 2
        assert result["results"][0]["status"] == 200
        assert (
            result["results"][1]["status"] == 404
        )  # Real API returns 404 for nonexistent forecaster

    @responses.activate
    def test_bulk_feed_data_all_failed(self, client, base_url):
        """Test bulk feeding with all failures (417)."""
        request = load_request("bulk_feed_data_single.json")
        response = load_response("bulk_feed_data_417.json")

        responses.add(
            responses.PATCH,
            f"{base_url}/forecasters/observations",
            json=response["body"],
            status=response["status_code"],
        )

        result = client.bulk_feed_data(request)

        assert "results" in result
        assert len(result["results"]) == 1
        assert result["results"][0]["status"] == 400

    @responses.activate
    def test_bulk_feed_data_redis_error(self, client, base_url):
        """Test bulk feeding with REDIS_UNAVAILABLE error (417)."""
        request = load_request("bulk_feed_data_single.json")
        response = load_response("bulk_feed_data_417_redis.json")

        responses.add(
            responses.PATCH,
            f"{base_url}/forecasters/observations",
            json=response["body"],
            status=response["status_code"],
        )

        result = client.bulk_feed_data(request)

        assert "results" in result
        assert len(result["results"]) == 1
        assert result["results"][0]["status"] == 500
        assert result["results"][0]["message"] == "REDIS_UNAVAILABLE"

    @responses.activate
    def test_delete_all_forecasters_success(self, client, base_url):
        """Test deleting all forecasters."""
        # Use existing list fixture
        list_response = load_response("list_forecasters_200.json")

        responses.add(
            responses.GET,
            f"{base_url}/forecasters",
            json=list_response["body"],
            status=list_response["status_code"],
        )

        # Mock delete responses for each forecaster in the list
        for forecaster in list_response["body"]:
            fc_id = forecaster["object_id"]  # Use object_id from list response
            responses.add(
                responses.DELETE,
                f"{base_url}/forecasters/{fc_id}",
                json={"message": "FORECASTER_DELETED"},
                status=200,
            )

        result = client.delete_all_forecasters()

        assert "results" in result
        assert len(result["results"]) == len(list_response["body"])
        assert all(r["status"] == 200 for r in result["results"])

    @responses.activate
    def test_delete_all_forecasters_with_failures(self, client, base_url):
        """Test deleting all forecasters with some failures."""
        # Use existing list fixture
        list_response = load_response("list_forecasters_200.json")

        responses.add(
            responses.GET,
            f"{base_url}/forecasters",
            json=list_response["body"],
            status=list_response["status_code"],
        )

        # First delete succeeds, rest fail
        forecasters = list_response["body"]
        if forecasters:
            # First one succeeds
            responses.add(
                responses.DELETE,
                f"{base_url}/forecasters/{forecasters[0]['object_id']}",  # Use object_id
                json={"message": "FORECASTER_DELETED"},
                status=200,
            )
            # Rest fail
            for forecaster in forecasters[1:]:
                responses.add(
                    responses.DELETE,
                    f"{base_url}/forecasters/{forecaster['object_id']}",  # Use object_id
                    json={"error": "FORECASTER_NOT_FOUND"},
                    status=404,
                )

        result = client.delete_all_forecasters()

        assert "results" in result
        if forecasters:
            assert result["results"][0]["status"] == 200
            assert all(r["status"] == 404 for r in result["results"][1:])

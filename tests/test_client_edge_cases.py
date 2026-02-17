import copy
import logging
from typing import Any
from unittest.mock import patch

import pytest
import responses

from driftmind import DriftMindClient
from driftmind.exceptions import DriftMindError


class TestLoggingProtection:
    """Test sensitive data filtering in logs."""

    def test_api_key_redacted_in_logs(self, caplog, base_url):
        """Test that API keys are redacted from logs even in DEBUG mode."""
        with caplog.at_level(logging.DEBUG):
            # Create a transient client for this test
            _ = DriftMindClient(
                "secret-key-123", base_url, enable_logging_protection=True
            )

            logger = logging.getLogger("urllib3")
            logger.debug("Auth: secret-key-123")

            # Check for redaction
            assert "secret-key-123" not in caplog.text or "[REDACTED]" in caplog.text


class TestClientEdgeCases:
    """Test local validation and connection edge cases."""

    # Note: We don't use the 'client' fixture for many of these
    # because we are testing the CONSTRUCTOR behavior itself.

    def test_empty_api_key_error(self, base_url):
        with pytest.raises(DriftMindError, match="api_key cannot be empty"):
            DriftMindClient("", base_url)

    def test_base_url_trailing_slash_stripped(self):
        client = DriftMindClient("test-key", "https://test.com/api/")
        assert client.base_url == "https://test.com/api"

    @responses.activate
    def test_non_json_response_error(self, client, base_url):
        """Test error handling when server returns HTML instead of JSON (e.g. Proxy error)."""
        responses.add(
            responses.GET,
            f"{base_url}/forecasters",
            body="<html><head><title>502 Bad Gateway</title></head></html>",
            status=502,
            content_type="text/html",
        )

        with pytest.raises(DriftMindError, match="invalid JSON"):
            client.list_forecasters()

    def test_connection_error_retry(self, client):
        """Test that the client gives up and raises DriftMindError after max retries."""
        from requests.exceptions import ConnectionError

        with patch.object(
            client._session, "request", side_effect=ConnectionError("DNS failure")
        ):
            with pytest.raises(DriftMindError, match="failed after"):
                client.list_forecasters()


class TestContractExtremeCases:
    """
    EXTREME CASES: Testing client resilience against 'Dishonest' Servers.
    These tests verify that our validate_contract fixture catches
    OpenAPI violations that would normally cause silent bugs.
    """

    SPEC_PATH = "/driftmind/v1/forecasters"

    @responses.activate
    def test_server_returns_wrong_data_type(
        self,
        client: Any,
        base_url: str,
        get_openapi_response_example: Any,
        validate_contract: Any,
    ) -> None:
        """Extreme Case: Server returns a STRING where an INTEGER is expected."""
        mock_data = copy.deepcopy(
            get_openapi_response_example(self.SPEC_PATH, "GET", 200)
        )

        # Corrupt the data: Change a numeric field to a non-numeric string
        if mock_data:
            mock_data[0]["requestsProcessed"] = "MANY_REQUESTS"

        responses.add(
            responses.GET, f"{base_url}/forecasters", json=mock_data, status=200
        )

        # Update the match to handle Pydantic's multi-line error message
        # 'int_parsing' is the specific error code Pydantic 2.x uses for this failure
        with pytest.raises(Exception, match=r"(?s)requestsProcessed.*int_parsing"):
            client.list_forecasters()
            # If the code reaches here, Pydantic failed to catch it,
            # so we let the contract validator have a go.
            validate_contract(responses.calls[0], path_pattern=self.SPEC_PATH)

    @responses.activate
    def test_server_missing_required_field(
        self,
        client: Any,
        base_url: str,
        get_openapi_response_example: Any,
        validate_contract: Any,
    ) -> None:
        """Extreme Case: Server omits a mandatory field like 'objectId'."""
        mock_data = copy.deepcopy(
            get_openapi_response_example(self.SPEC_PATH, "GET", 200)
        )

        if mock_data:
            del mock_data[0]["objectId"]

        responses.add(
            responses.GET, f"{base_url}/forecasters", json=mock_data, status=200
        )

        # The (?s) flag allows the dot to match across newlines \n
        with pytest.raises(Exception, match=r"(?s)objectId.*Field required"):
            client.list_forecasters()

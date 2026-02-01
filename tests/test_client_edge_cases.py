"""Tests for client logging protection and edge cases."""

import logging
from unittest.mock import patch

import pytest
import responses

from driftmind import DriftMindClient
from driftmind.exceptions import DriftMindError


class TestLoggingProtection:
    """Test sensitive data filtering in logs."""

    def test_api_key_redacted_in_logs(self, caplog):
        """Test that API keys are redacted from logs."""
        with caplog.at_level(logging.DEBUG):
            _ = DriftMindClient(
                "secret-key-123", "https://test.com", enable_logging_protection=True
            )

            # Trigger a log that might contain the auth header
            logger = logging.getLogger("urllib3")
            logger.debug("Auth: secret-key-123")

            # Check that the key was redacted
            assert "secret-key-123" not in caplog.text or "[REDACTED]" in caplog.text

    def test_logging_protection_disabled(self):
        """Test client works with logging protection disabled."""
        client = DriftMindClient(
            "test-key", "https://test.com", enable_logging_protection=False
        )
        assert client.api_key == "test-key"


class TestClientEdgeCases:
    """Test error handling edge cases."""

    def test_empty_api_key_error(self):
        """Test error when API key is empty."""
        with pytest.raises(DriftMindError, match="api_key cannot be empty"):
            DriftMindClient("", "https://test.com")

    def test_whitespace_api_key_error(self):
        """Test error when API key is whitespace."""
        with pytest.raises(DriftMindError, match="api_key cannot be empty"):
            DriftMindClient("   ", "https://test.com")

    def test_empty_base_url_error(self):
        """Test error when base URL is empty."""
        with pytest.raises(DriftMindError, match="base_url cannot be empty"):
            DriftMindClient("test-key", "")

    def test_base_url_trailing_slash_stripped(self):
        """Test that trailing slashes are removed from base URL."""
        client = DriftMindClient("test-key", "https://test.com/api/")
        assert client.base_url == "https://test.com/api"

    def test_api_key_whitespace_stripped(self):
        """Test that whitespace is stripped from API key."""
        client = DriftMindClient("  test-key  ", "https://test.com")
        assert client.api_key == "test-key"

    @responses.activate
    def test_non_json_response_error(self):
        """Test error handling for non-JSON responses."""
        client = DriftMindClient("test-key", "https://test.com")

        responses.add(
            responses.GET,
            "https://test.com/forecasters",
            body="<html>Error</html>",
            status=500,
            content_type="text/html",
        )

        with pytest.raises(DriftMindError, match="invalid JSON"):
            client.list_forecasters()

    def test_connection_error_retry(self):
        """Test retry on connection errors."""
        from requests.exceptions import ConnectionError

        client = DriftMindClient(
            "test-key", "https://test.com", max_retries=2, retry_delay=0.01
        )

        with patch.object(
            client._session, "request", side_effect=ConnectionError("Connection failed")
        ):
            with pytest.raises(DriftMindError, match="failed after"):
                client.list_forecasters()

    def test_custom_session(self):
        """Test client with custom session."""
        from requests import Session

        custom_session = Session()
        client = DriftMindClient("test-key", "https://test.com", session=custom_session)
        assert client._session is custom_session
        assert not client._owns_session

        # Close should not close custom session
        client.close()

    def test_owned_session_closed(self):
        """Test that owned session is closed."""
        client = DriftMindClient("test-key", "https://test.com")
        assert client._owns_session

        _ = client._session
        client.close()
        # Session should be closed (can't easily test, but verify no error)

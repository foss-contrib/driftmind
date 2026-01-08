import pytest

from driftmind.client import DriftMindClient


@pytest.fixture
def api_key():
    return "test-api-key-123"


@pytest.fixture
def base_url():
    return "https://api.thingbook.io/access/api/driftmind"


@pytest.fixture
def client(api_key, base_url):
    """Provides a fresh client for every test."""
    return DriftMindClient(api_key=api_key, base_url=base_url)

import json
from pathlib import Path

import pytest

from driftmind.client import DriftMindClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(filename: str) -> dict:
    """Load JSON fixture from fixtures directory.

    Searches in new structure (requests/, responses/) first,
    then falls back to root for backward compatibility.
    """
    # Try new structure
    for subdir in ["requests", "responses/success", "responses/errors"]:
        path = FIXTURES_DIR / subdir / filename
        if path.exists():
            with open(path) as f:
                return json.load(f)

    # Fallback to old location
    path = FIXTURES_DIR / filename
    if path.exists():
        with open(path) as f:
            return json.load(f)

    raise FileNotFoundError(f"Fixture not found: {filename}")


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


@pytest.fixture
def minimal_spec_input():
    """Only mandatory fields."""
    return load_fixture("minimal_spec_input.json")


@pytest.fixture
def full_spec_input():
    """All optional fields included with string dates."""
    return load_fixture("full_spec_input.json")


@pytest.fixture
def api_creation_response():
    """API response for successful forecaster creation."""
    return load_fixture("api_creation_response.json")


@pytest.fixture
def api_validation_error():
    """API error response for validation failures."""
    return load_fixture("api_validation_error.json")

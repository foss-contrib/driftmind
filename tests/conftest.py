import json
import random
from importlib import resources
from pathlib import Path
from typing import Any, Callable, Optional

import jsonschema
import pytest
import yaml
from openapi_core import Spec

from driftmind import DriftMindClient

# Type aliases for clarity
ExampleExtractor = Callable[[str, str, int, Optional[str]], Any]

FIXTURES_DIR: Path = Path(__file__).parent / "fixtures"

## --- Spec Fixtures ---


@pytest.fixture(scope="session")
def spec_dict() -> dict[str, Any]:
    """Loads the raw OpenAPI dictionary from package data."""
    spec_path = resources.files("driftmind.data").joinpath("openapi.yaml")
    with spec_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def openapi_spec(spec_dict: dict[str, Any]) -> Spec:
    """Provides an openapi-core Spec object if needed for other utilities."""
    return Spec.from_dict(spec_dict)


## --- Validation & Contract Testing ---


@pytest.fixture
def validate_contract(spec_dict):
    """
    Validates the request and response of a call against the OpenAPI spec.
    """

    def _validate(response_call, path_pattern="/driftmind/v1/forecasters"):
        # We set a default path_pattern so your existing tests don't break!
        method = response_call.request.method.lower()

        try:
            # 1. Use the spec_dict directly from the parent fixture
            operation = spec_dict["paths"][path_pattern][method]

            # 2. Initialize validator with full spec for $ref support
            ValidatorClass = jsonschema.validators.validator_for(spec_dict)
            base_validator = ValidatorClass(spec_dict)

            # --- Request Validation ---
            request_content = operation.get("requestBody", {}).get("content", {})
            req_schema = request_content.get("application/json", {}).get("schema", {})

            if req_schema:
                body_bytes = response_call.request.body or b"{}"
                # Ensure we handle both strings and bytes safely
                if isinstance(body_bytes, str):
                    body_bytes = body_bytes.encode("utf-8")

                request_data = json.loads(body_bytes.decode("utf-8"))
                base_validator.evolve(schema=req_schema).validate(request_data)

            # --- Response Validation ---
            status_code = str(response_call.response.status_code)
            response_spec = operation.get("responses", {}).get(status_code)

            if response_spec and "content" in response_spec:
                res_schema = (
                    response_spec["content"]
                    .get("application/json", {})
                    .get("schema", {})
                )
                if res_schema:
                    res_data = response_call.response.json()
                    base_validator.evolve(schema=res_schema).validate(res_data)

        except jsonschema.exceptions.ValidationError as e:
            pytest.fail(f"Contract Violation: {e.message} at {list(e.path)}")
        except KeyError as e:
            pytest.fail(
                f"Spec mismatch: Key {e} not found for {method.upper()} {path_pattern}"
            )
        except Exception as e:
            pytest.fail(f"Validation internal error: {type(e).__name__}: {e}")

    return _validate


## --- Client & Mocking Fixtures ---


@pytest.fixture
def api_key() -> str:
    return "test-api-key"


@pytest.fixture
def root_url() -> str:
    return "https://api.thingbook.io/access/api"


@pytest.fixture
def base_url(root_url: str) -> str:
    return f"{root_url}/driftmind/v1"


@pytest.fixture
def client(api_key: str, base_url: str) -> DriftMindClient:
    return DriftMindClient(api_key, base_url)


@pytest.fixture
def load_json_fixture():
    """Returns a function that loads JSON fixtures from the fixtures directory."""

    def _loader(filename: str) -> dict:
        path = FIXTURES_DIR / filename
        if path.exists():
            with open(path) as f:
                return json.load(f)

        raise FileNotFoundError(f"Fixture not found: {filename}")

    return _loader


## --- Example Extraction Utilities ---


@pytest.fixture
def get_openapi_response_example(spec_dict: dict[str, Any]) -> ExampleExtractor:
    """Extracts response examples or schema fallbacks from the spec."""

    def _resolve_schema_example(schema: dict[str, Any], spec: dict[str, Any]) -> Any:
        """Helper to resolve $ref and extract examples from components."""
        # Handle $ref pointers
        if "$ref" in schema:
            ref_path = schema["$ref"].lstrip("#/").split("/")
            ref_obj = spec
            for part in ref_path:
                ref_obj = ref_obj.get(part, {})
            return ref_obj.get("example")

        # Handle Arrays (List of objects)
        if schema.get("type") == "array":
            items = schema.get("items", {})
            item_example = _resolve_schema_example(items, spec)
            # Wrap the single item example in a list
            return [item_example] if item_example is not None else []

        return schema.get("example")

    def _extract(
        path: str, method: str, status_code: int, example_name: Optional[str] = None
    ) -> Any:
        method, status = method.lower(), str(status_code)

        # Safe navigation to the response content
        path_item = spec_dict.get("paths", {}).get(path, {})
        operation = path_item.get(method, {})
        response = operation.get("responses", {}).get(status, {})
        content = response.get("content", {}).get("application/json", {})

        if not content:
            return None  # Return None so tests can handle missing specs explicitly

        # 1. Check for explicit examples in the response block
        if "examples" in content:
            exs = content["examples"]
            if example_name and example_name in exs:
                return exs[example_name].get("value")
            # Using random.choice is clever for variety, but we'll stick to your pattern
            return random.choice(list(exs.values())).get("value")

        if "example" in content:
            return content["example"]

        # 2. Fallback to Schema-level examples (handles $ref)
        schema = content.get("schema", {})
        return _resolve_schema_example(schema, spec_dict)

    return _extract


def _resolve_schema_example(schema: dict[str, Any], spec: dict[str, Any]) -> Any:
    """Recursively resolves $ref to find example values in the spec components."""
    if "$ref" in schema:
        parts = schema["$ref"].split("/")
        target = spec
        for p in parts[1:]:
            target = target.get(p, {})
        return target.get("example")
    return schema.get("example")

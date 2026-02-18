from typing import Any

import pytest
from pydantic import ValidationError

from driftmind.models import (
    ApiErrorResponse,
    ForecasterConfig,
    ForecasterCreationResponse,
    ForecasterSpec,
)


class TestForecasterCreationSchema:
    """
    Validates transformations for the create_forecaster workflow:
    - Request: Python Spec -> API JSON (Snake to Camel)
    - Response: API JSON -> Python Object (Camel to Snake)
    """

    SPEC_PATH = "/driftmind/v1/forecasters"

    # 1. Successful Outbound (Python -> API)
    @pytest.mark.parametrize(
        "fixture_file", ["minimal_spec_input.json", "full_spec_input.json"]
    )
    def test_request_serialization_mapping(self, fixture_file: str, load_json_fixture: Any):
        """
        Tests that Python objects (minimal or full) convert correctly
        to API-ready camelCase JSON with Java date formats.
        """
        # FIX: Call the factory fixture directly with the filename string
        data = load_json_fixture(fixture_file)
        spec = ForecasterSpec(**data)

        # Serialize for API
        payload = spec.model_dump(
            mode="json", by_alias=True, exclude_none=True, context={"target": "api"}
        )

        # Assert Keys are CamelCase
        assert "forecasterName" in payload
        assert "forecaster_name" not in payload

        # Assert Date Conversion (only if custom format was used)
        if data.get("use_custom_date_format"):
            assert payload["dateFormat"] == "dd-MM-yyyy HH:mm"
            assert payload["initializationDate"] == data["initialization_date"]
            assert isinstance(payload["initializationDate"], str)

    # 2. Successful Inbound (API -> Python)
    def test_response_parsing_coercion(
        self,
        get_openapi_response_example: Any,
        load_json_fixture: Any,
    ):
        """Tests that API response (camelCase/Strings) parses into Pythonic model."""
        api_creation_response = get_openapi_response_example(
            self.SPEC_PATH, "POST", 201
        )
        model = ForecasterCreationResponse.model_validate(api_creation_response)

        assert model.forecaster_id == "f4e2a5bb-9360-4802-8f6c-2211e97473b7"
        assert model.configuration.input_size == 30  # Coerced from string
        assert model.configuration.date_format == "%d-%m-%Y %H:%M:%S"

    # 3. Schema Failure (Missing keys)
    @pytest.mark.parametrize(
        "missing_field", ["forecaster_name", "features", "input_size", "output_size"]
    )
    def test_request_validation_required_fields(
        self,
        load_json_fixture: Any,
        missing_field: str,
    ):
        """
        Verify that omitting any mandatory key raises a ValidationError.
        We check Pydantic's error 'loc' to see if it caught the right field.
        """
        full_spec_input = load_json_fixture("full_spec_input.json")
        invalid_data = full_spec_input.copy()
        del invalid_data[missing_field]

        with pytest.raises(ValidationError) as exc_info:
            ForecasterSpec(**invalid_data)

        # 1. Get structured errors from Pydantic
        errors = exc_info.value.errors()

        # 2. Extract all 'loc' (location) entries.
        # Pydantic returns tuples like ('outputSize',) or ('output_size',)
        flat_locs = [str(item).lower() for err in errors for item in err["loc"]]

        # 3. Check if either the snake_case name or camelCase alias is in the error locations
        # We normalize to lowercase and remove underscores to be safe
        normalized_field = missing_field.replace("_", "").lower()

        assert any(normalized_field in loc.replace("_", "") for loc in flat_locs), (
            f"Expected error for field '{missing_field}', but got locs: {flat_locs}"
        )

    # 4. API Error Handling (parsing the 400/500 JSON)
    def test_response_error_handling_schema(
        self,
        get_openapi_response_example: Any,
        load_json_fixture: Any,
    ):
        """Test API Error JSON -> Python Error Model."""
        api_validation_error = get_openapi_response_example(
            self.SPEC_PATH, "POST", 400, "Invalid Window Sizes"
        )
        err = ApiErrorResponse.model_validate(api_validation_error)
        assert err.error == "VALIDATION_FAILED"
        assert len(err.details) == 2

    # 5. Business Logic (Cross-field validation)
    def test_request_logic_constraints(self):
        """Test Internal validation (e.g., output_size vs input_size)."""
        with pytest.raises(ValueError, match="output_size must be less than"):
            ForecasterSpec(
                forecaster_name="Bad Model",
                features=["f1"],
                input_size=10,
                output_size=20,  # Invalid: output > input
            )


class TestJavaDateFormatOption:
    """
    Tests the accept_java_date_format context flag at the model level.
    When True, Java SimpleDateFormat patterns (e.g., "dd-MM-yyyy HH:mm")
    are accepted as-is without conversion to/from Python strftime.
    """

    JAVA_FMT = "dd-MM-yyyy HH:mm"
    PYTHON_FMT = "%d-%m-%Y %H:%M"
    JAVA_CONTEXT = {"accept_java_date_format": True}
    API_JAVA_CONTEXT = {"target": "api", "accept_java_date_format": True}

    # --- ForecasterSpec (outbound / request) ---

    def test_spec_accepts_java_date_format(self, load_json_fixture: Any):
        """Java pattern should be accepted when context flag is set."""
        data = load_json_fixture("full_spec_input_dateformat_java.json")
        spec = ForecasterSpec.model_validate(data, context=self.JAVA_CONTEXT)
        assert spec.date_format == self.JAVA_FMT

    def test_spec_converts_python_to_java_without_flag(self, load_json_fixture: Any):
        """Without flag, Python strftime format is stored as-is internally."""
        data = load_json_fixture("full_spec_input.json")
        spec = ForecasterSpec(**data)
        assert spec.date_format == self.PYTHON_FMT

    def test_spec_serialization_passthrough_java(self, load_json_fixture: Any):
        """With flag set, serialization for API should pass Java format through."""
        data = load_json_fixture("full_spec_input_dateformat_java.json")
        spec = ForecasterSpec.model_validate(data, context=self.JAVA_CONTEXT)
        payload = spec.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
            context=self.API_JAVA_CONTEXT,
        )
        # Java format should pass through unchanged (no double-conversion)
        assert payload["dateFormat"] == self.JAVA_FMT
        # initialization_date should still serialize correctly
        assert payload["initializationDate"] == data["initialization_date"]

    def test_spec_serialization_converts_without_flag(self, load_json_fixture: Any):
        """Without flag, serialization for API should convert Python→Java."""
        data = load_json_fixture("full_spec_input.json")
        spec = ForecasterSpec(**data)
        payload = spec.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
            context={"target": "api"},
        )
        assert payload["dateFormat"] == self.JAVA_FMT

    # --- ForecasterConfig (inbound / response) ---

    def test_config_keeps_java_format_with_flag(self):
        """Response parsing should keep Java format when flag is set."""
        config = ForecasterConfig.model_validate(
            {
                "inputSize": "30",
                "outputSize": "1",
                "dateFormat": self.JAVA_FMT,
            },
            context=self.JAVA_CONTEXT,
        )
        assert config.date_format == self.JAVA_FMT

    def test_config_converts_java_to_python_without_flag(self):
        """Response parsing should convert Java→Python without the flag."""
        config = ForecasterConfig.model_validate(
            {
                "inputSize": "30",
                "outputSize": "1",
                "dateFormat": self.JAVA_FMT,
            },
        )
        assert config.date_format == self.PYTHON_FMT

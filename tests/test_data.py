import pytest
from pydantic import ValidationError

from driftmind.models import (
    ApiErrorResponse,
    ForecasterCreationResponse,
    ForecasterSpec,
)


class TestForecasterCreationSchema:
    """
    Validates transformations for the create_forecaster workflow:
    - Request: Python Spec -> API JSON (Snake to Camel)
    - Response: API JSON -> Python Object (Camel to Snake)
    """

    # 1. Successful Outbound (Python -> API)
    @pytest.mark.parametrize("fixture_name", ["minimal_spec_input", "full_spec_input"])
    def test_request_serialization_mapping(self, fixture_name, request):
        """
        Tests that Python objects (minimal or full) convert correctly
        to API-ready camelCase JSON with Java date formats.
        """
        data = request.getfixturevalue(fixture_name)
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
    def test_response_parsing_coercion(self, api_creation_response):
        """Tests that API response (camelCase/Strings) parses into Pythonic model."""
        model = ForecasterCreationResponse.model_validate(api_creation_response)

        assert model.forecaster_id == "fc-123"
        assert model.configuration.input_size == 30  # Coerced from string
        assert model.configuration.date_format == "%d-%m-%Y %H:%M"

    # 3. Schema Failure (Missing keys)
    @pytest.mark.parametrize(
        "missing_field", ["forecaster_name", "features", "input_size", "output_size"]
    )
    def test_request_validation_required_fields(self, full_spec_input, missing_field):
        """
        Verify that omitting any mandatory key raises a ValidationError.
        We check Pydantic's error 'loc' to see if it caught the right field.
        """
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

        assert any(
            normalized_field in loc.replace("_", "") for loc in flat_locs
        ), f"Expected error for field '{missing_field}', but got locs: {flat_locs}"

    # 4. API Error Handling (parsing the 400/500 JSON)
    def test_response_error_handling_schema(self, api_validation_error):
        """Test API Error JSON -> Python Error Model."""
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

from __future__ import annotations

from datetime import datetime
from typing import Any

from dateutil import parser as date_parser
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_serializer,
    field_validator,
    model_validator,
)

from .utils import (
    is_java_date_format,
    java_to_python_date_format,
    python_to_java_date_format,
    to_camel,
    to_snake,
)


class ObjectInformation(BaseModel):
    """Represents a tracked object in the DriftMind system."""

    object_id: str = Field(
        ...,
        alias="objectId",
        description="Unique identifier of the object.",
        examples=["object-7e4b1a21"],
    )
    object_name: str = Field(
        ...,
        alias="objectName",
        description="Human-readable name assigned to the object.",
        examples=["Web Traffic Forecaster"],
    )
    created_at: str = Field(
        ...,
        alias="createdAt",
        description="Date when the object was created, in format YYYY-MM-DD.",
        examples=["2025-09-14"],
    )
    created_by: str = Field(
        ...,
        alias="createdBy",
        description="Developer token that created the object.",
        examples=["VfYZ3hLQk6FohdPTkKXB0lC30DworzI5Mz...."],
    )
    object_type: str = Field(
        ...,
        alias="objectType",
        description="Type or category of the object (e.g., 'FORECASTER', 'OFFLINE DETECTOR', 'DATASET', etc).",
        examples=["FORECASTER"],
    )
    data_processed: float = Field(
        ...,
        alias="dataProcessed",
        description="Amount of data processed by the object expressed in MB (human-readable).",
        examples=[14120.0],
    )
    requests_processed: int = Field(
        ...,
        alias="requestsProcessed",
        description="Number of API or internal requests handled by this object.",
        examples=[328],
    )

    @field_validator("data_processed", mode="before")
    @classmethod
    def parse_float_string(cls, v: Any) -> float:
        if isinstance(v, str):
            # Remove commas and convert
            return float(v.replace(",", ""))
        return v

    @field_validator("requests_processed", mode="before")
    @classmethod
    def parse_int_string(cls, v: Any) -> int:
        if isinstance(v, str):
            # Remove commas and convert
            # We convert to float first in case string is "328.0", then to int
            return int(float(v.replace(",", "")))
        return v


class ObjectInformationList(RootModel[list[ObjectInformation]]):
    """List response of tracked objects."""

    root: list[ObjectInformation]


class ForecasterConfigBase(BaseModel):
    """Base configuration payload for creating DriftMind forecasters."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",
        alias_generator=to_camel,
    )

    input_size: int = Field(
        ...,
        description="Number of past time steps (input window size) to use for forecasting.",
        examples=[30],
        gt=0,
    )

    output_size: int = Field(
        ...,
        description=(
            "Number of future time steps (forecast horizon) to predict. "
            "Must be less than inputSize."
        ),
        examples=[1],
        gt=0,
    )

    max_clusters_allowed: int = Field(
        default=100,
        description=(
            "Maximum number of clusters allowed. Affects memory footprint "
            "and model complexity."
        ),
        examples=[50],
        gt=0,
    )

    similarity_threshold: float = Field(
        default=0.8,
        description=(
            "Clustering similarity threshold in [0.6, 1.0]. Controls how "
            "similar time series must be to be clustered together."
        ),
        ge=0.6,
        le=1.0,
        examples=[0.8],
    )

    timestamp_interval_in_seconds: int = Field(
        default=60,
        description=(
            "Time interval (in seconds) between consecutive data points. "
            "Used to validate time-based assumptions."
        ),
        examples=[86400],
        gt=0,
    )

    fit_rate: int = Field(
        default=1,
        description=(
            "Number of data point insertions required to trigger a model fit operation."
        ),
        examples=[1],
        gt=0,
    )

    date_format: str = Field(
        default="dd-MM-yyyy HH:mm",
        description=(
            "Java date format used for parsing timestamps."
            "Will be converted to Python format for the client"
        ),
        examples=["dd-MM-yyyy HH:mm"],
    )

    initialization_date: str | None = Field(
        default=None,
        description=(
            "Initialization date/time used when use_initialization_date is True. "
            "Format must match date_format."
        ),
        examples=["01-01-2025 00:00"],
    )

    @field_validator("date_format", mode="before")
    @classmethod
    def deserialize_date_format(cls, v: Any) -> Any:
        if isinstance(v, str):
            # Only convert if it actually looks like Java and NOT Python
            if is_java_date_format(v):
                return java_to_python_date_format(v)
        return v

    @model_validator(mode="before")
    @classmethod
    def convert_extra_camel_to_snake(cls, data: Any) -> Any:
        """
        Intercepts raw input data to convert camelCase keys to snake_case.
        This ensures that 'extra' fields are stored in a Pythonic format.
        """
        if isinstance(data, dict):
            return {to_snake(k): v for k, v in data.items()}
        return data

    @model_validator(mode="after")
    def validate_constraints(self) -> ForecasterConfigBase:
        if self.output_size >= self.input_size:
            raise ValueError("output_size must be less than input_size")

        return self


class ForecasterConfig(ForecasterConfigBase):
    """Configuration payload for creating a DriftMind forecaster."""

    forecaster_name: str = Field(
        ...,
        description="Unique name for the forecaster to be created.",
        examples=["Daily_revenue_predictor"],
    )

    features: list[str] = Field(
        ...,
        description="list of input features (column names) to be used for forecasting.",
        examples=[["Product Category A", "Product Category B", "Product Category C"]],
        min_length=1,
    )

    use_custom_date_format: bool = Field(
        default=False,
        description=(
            "If true, input data contains timestamps in a custom format, "
            "parsed using date_format."
        ),
        examples=[True],
    )

    date_format: str = Field(
        default="%d-%m-%Y %H:%M:%S",
        description=(
            "Python strptime/strftime format used for parsing timestamps when "
            "use_custom_date_format is True."
            "Will be converted to Java format for the API"
        ),
        examples=["%d-%m-%Y %H:%M"],
    )

    use_initialization_date: bool = Field(
        default=False,
        description=(
            "If true, training is assumed to start at initialization_date; "
            "otherwise current system time is used."
        ),
        examples=[True],
    )

    @field_validator("date_format")
    @classmethod
    def validate_python_format_string(cls, v: str) -> str:
        """Verify the string is a valid Python strftime format."""
        try:
            # Attempt to format a dummy date to see if it's a valid pattern
            datetime.now().strftime(v)
        except Exception as exc:
            raise ValueError(f"Invalid Python date format string: {v}") from exc
        return v

    @field_serializer("date_format", when_used="json")
    def serialize_date_format(self, v: str) -> str:
        """Converts Python strftime format to Java/Unicode format for the API."""
        return python_to_java_date_format(v)

    @model_validator(mode="after")
    def validate_constraints(self) -> ForecasterConfig:
        super().validate_constraints()

        if self.use_initialization_date:
            if not self.initialization_date:
                raise ValueError(
                    "initialization_date must be provided when use_initialization_date is True."
                )

            # 3. Validate format against date_format
            try:
                # Internally we still use the Python % format to validate the input string
                datetime.strptime(self.initialization_date, self.date_format)
            except ValueError as exc:
                raise ValueError(
                    f"initialization_date='{self.initialization_date}' "
                    f"does not match date_format='{self.date_format}'"
                ) from exc

        return self


class ForecasterSpec(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=to_camel,
    )

    forecaster_id: str = Field(
        ...,
        alias="forecasterId",
        description="Unique id for the forecaster created.",
    )

    features: list[str] = Field(
        ...,
        description="list of input features (column names) to be used for forecasting.",
        examples=[["Product Category A", "Product Category B", "Product Category C"]],
        min_length=1,
    )

    forecaster_name: str = Field(
        ...,
        description="Unique name for the forecaster to be created.",
        examples=["Daily_revenue_predictor"],
    )

    properties: ForecasterConfigBase = Field(
        ...,
        description="Effective configuration properties applied to the forecaster after defaults and normalization.",
    )


class TimeSeriesSegment(RootModel[dict[str, list[float]]]):
    """Mapping from feature name to a list of floats with equal length."""

    @model_validator(mode="after")
    def validate_segment_integrity(self) -> TimeSeriesSegment:
        # Check if the dictionary itself is empty
        if not self.root:
            raise ValueError("TimeSeriesSegment must contain at least one feature.")

        # Get lengths of all lists
        lengths = {key: len(values) for key, values in self.root.items()}

        # Check if any list is empty (e.g., {"a": []})
        if any(length == 0 for length in lengths.values()):
            raise ValueError("Feature lists cannot be empty.")

        # Check for alignment (equal length)
        unique_lengths = set(lengths.values())
        if len(unique_lengths) > 1:
            length_summary = ", ".join([f"{k}({v})" for k, v in lengths.items()])
            raise ValueError(
                f"All feature lists must have the same length. Got: {length_summary}"
            )

        return self


class TimeSeriesSnapshot(RootModel[dict[str, dict[str, float]]]):
    """Mapping from timestamp string to a mapping of feature → float.

    Example input::

        {
          "data": {
            "01/05/2024 00:05:00": {"temperature": 42.5, "humidity": 77.1},
            "01/05/2024 00:06:00": {"temperature": 38.2, "humidity": 75.0}
          }
        }

    The model validates that:
    - Each timestamp maps to a dict[str, float]
    - All inner dicts have the same set of feature keys
    """

    @model_validator(mode="after")
    def validate_consistent_features(self) -> TimeSeriesSnapshot:
        if not self.root:
            return self

        # Use an iterator to get the first set of keys
        data_iter = iter(self.root.items())
        first_ts, first_features = next(data_iter)
        expected_keys = set(first_features.keys())

        # Only need to check the remaining items
        for ts, features in data_iter:
            if set(features.keys()) != expected_keys:
                raise ValueError(
                    f"Feature mismatch at timestamp '{ts}'. "
                    f"Expected {sorted(expected_keys)}, but found {sorted(features.keys())}."
                )

        return self


class TimeSeriesData(BaseModel):
    """Container for time-indexed feature values, mapping each timestamp to a consistent set of float features."""

    data: TimeSeriesSnapshot


class ForecastResultPerFeature(BaseModel):
    time_stamps: list[str] = Field(..., alias="timeStamps")
    predictions: list[float]
    upper_confidence: list[float] = Field(..., alias="upperConfidence")
    lower_confidence: list[float] = Field(..., alias="lowerConfidence")
    anomaly_score: float = Field(..., alias="anomalyScore")
    forecasting_method: str = Field(..., alias="forecastingMethod")
    number_of_clusters: int = Field(..., alias="numberOfClusters")

    @field_validator("time_stamps")
    @classmethod
    def validate_time_stamps(cls, v: list[str]) -> list[str]:
        for ts in v:
            date_parser.parse(ts)
        return v

    @model_validator(mode="after")
    def validate_internal_lengths(self) -> ForecastResultPerFeature:
        """Ensure all arrays within this feature result match."""
        expected = len(self.time_stamps)
        actuals = {
            "predictions": len(self.predictions),
            "upper_confidence": len(self.upper_confidence),
            "lower_confidence": len(self.lower_confidence),
        }
        for field, length in actuals.items():
            if length != expected:
                raise ValueError(
                    f"Length mismatch: {field} has {length} items, but time_stamps has {expected}"
                )
        return self


class ForecastResponse(BaseModel):
    """Forecast response with global metrics and per-feature results."""

    anomaly_score: float = Field(..., alias="anomalyScore")
    number_of_clusters: int = Field(..., alias="numberOfClusters")
    features_map: dict[str, ForecastResultPerFeature] = Field(..., alias="FeaturesMap")

    @model_validator(mode="after")
    def validate_cross_feature_consistency(self) -> ForecastResponse:
        if not self.features_map:
            return self

        # Get the length from the first feature in the map
        iterator = iter(self.features_map.values())
        first_feature = next(iterator)
        expected_length = len(first_feature.time_stamps)

        for name, feature in iterator:
            actual_length = len(feature.time_stamps)
            if actual_length != expected_length:
                raise ValueError(
                    f"Feature consistency error: '{name}' has {actual_length} points, "
                    f"but first feature had {expected_length} points."
                )
        return self

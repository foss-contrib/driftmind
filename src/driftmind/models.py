from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    AliasChoices,
    AliasGenerator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    RootModel,
    SerializationInfo,
    ValidationInfo,
    field_serializer,
    field_validator,
    model_validator,
)
from pydantic.alias_generators import to_camel

from .utils import convert_java_to_strftime, convert_strftime_to_java, smart_parse_date

# Reusable type for date fields
SmartDateTime = Annotated[datetime, BeforeValidator(smart_parse_date)]


# Common config to handle snake_case <-> camelCase conversion
common_config = ConfigDict(
    alias_generator=AliasGenerator(
        validation_alias=to_camel,
        serialization_alias=to_camel,
    ),
    populate_by_name=True,
)


class DriftMindObjectInformation(BaseModel):
    """
    Represents a tracked object in the DriftMind system, including metadata and statistics.
    """

    model_config = common_config

    object_id: str = Field(
        ...,
        description="Unique identifier of the object.",
        examples=["object-7e4b1a21"],
    )
    object_name: str | None = Field(
        None,
        description="Human-readable name assigned to the object.",
        examples=["Web Traffic Forecaster"],
    )
    created_at: str = Field(
        ...,
        description="Date when the object was created, in format YYYY-MM-DD.",
        examples=["2025-09-14"],
    )
    created_by: str = Field(
        ...,
        description="Developer token that created the object.",
        examples=["VfYZ3hLQk6FohdPTkKXB0lC30DworzI5Mz...."],
    )
    object_type: str = Field(
        ...,
        description="Type or category of the object (e.g., 'FORECASTER', 'OFFLINE DETECTOR', 'DATASET', etc).",
        examples=["FORECASTER"],
    )
    data_processed: float = Field(
        ...,
        description="Amount of data processed by the object expressed in MB (human-readable).",
        examples=[14120.0],
    )
    requests_processed: int = Field(
        description="Number of API or internal requests handled by this object.",
        examples=[328],
    )


class DriftMindObjectInformationList(RootModel):
    """
    List response of DriftMindObjectInformation objects as returned by the retrieval endpoint.
    """

    root: list[DriftMindObjectInformation]


class ForecasterSettingsBase(BaseModel):
    """
    Common settings shared between creation requests and API responses.
    """

    model_config = common_config

    # Mandatory Fields
    input_size: int = Field(
        ...,
        description="Number of past time steps (input window size) to use for forecasting.",
        examples=[30],
        ge=1,
    )
    output_size: int = Field(
        ...,
        description=(
            "Number of future time steps (forecast horizon) to predict. "
            "Must be less than inputSize."
        ),
        examples=[1],
        ge=1,
    )

    # Optional Fields with Constraints
    max_clusters_allowed: int | None = Field(
        None,
        description=(
            "Maximum number of clusters allowed. Affects memory footprint "
            "and model complexity."
        ),
        examples=[50],
        ge=1,
    )
    similarity_threshold: float | None = Field(
        None,
        description=(
            "Clustering similarity threshold in [0.6, 1.0]. Controls how "
            "similar time series must be to be clustered together."
        ),
        ge=0.6,
        le=1.0,
        examples=[0.8],
    )
    timestamp_interval_in_seconds: int | None = Field(
        None,
        description=(
            "Time interval (in seconds) between consecutive data points. "
            "Used to validate time-based assumptions."
        ),
        alias="timeStampIntervalInSeconds",
        examples=[86400],
        ge=1,
    )
    fit_rate: int | None = Field(
        None,
        description=(
            "Number of data point insertions required to trigger a model fit operation."
        ),
        examples=[1],
        ge=1,
    )
    use_custom_date_format: bool | None = Field(
        None,
        description=(
            "If true, input data contains timestamps in a custom format, "
            "parsed using date_format."
        ),
        examples=[True],
    )
    date_format: str | None = Field(
        None,
        description=(
            "Python strptime/strftime format used for parsing timestamps when "
            "use_custom_date_format is True."
            "Will be converted to Java format for the API"
        ),
        examples=["%d-%m-%Y %H:%M"],
    )
    use_initialization_date: bool | None = Field(
        None,
        description=(
            "If true, training is assumed to start at initialization_date; "
            "otherwise current system time is used."
        ),
        examples=[True],
    )
    initialization_date: SmartDateTime | None = Field(
        None,
        description=(
            "Initialization date/time used when use_initialization_date is True. "
            "Format must match date_format."
        ),
    )

    @field_validator("date_format")
    @classmethod
    def validate_python_format_string(
        cls, v: str | None, info: ValidationInfo
    ) -> str | None:
        if v is None:
            return v

        # Skip Python validation if we are in 'accept_java' mode
        if info.context and info.context.get("accept_java_date_format"):
            return v

        try:
            datetime.now().strftime(v)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid Python date format string: {v}") from exc
        return v

    @model_validator(mode="after")
    def validate_logic_constraints(self) -> ForecasterSettingsBase:
        """Cross-field validation for output_size and date configurations."""
        # 1. outputSize <= inputSize constraint
        if self.output_size > self.input_size:
            raise ValueError("output_size must be less than or equal to input_size.")

        # 2. Date format requirement
        if self.use_custom_date_format and not self.date_format:
            raise ValueError(
                "date_format must be provided if use_custom_date_format is True."
            )

        # 3. Initialization date requirement
        if self.use_initialization_date and not self.initialization_date:
            raise ValueError(
                "initialization_date must be provided if use_initialization_date is True."
            )

        return self

    @field_serializer("date_format", when_used="json")
    def serialize_date_format(
        self, date_format: str | None, info: SerializationInfo
    ) -> str | None:
        """
        Only converts to Java if the context explicitly asks for 'api' target.
        Otherwise, keeps the Python format.
        """
        context = info.context or {}

        if date_format is None:
            return None

        # Skip conversion if user wants to talk Java directly
        if context.get("accept_java_date_format"):
            return date_format

        if context.get("target") == "api":
            return convert_strftime_to_java(date_format)
        return date_format

    @field_serializer("initialization_date", when_used="json")
    def serialize_initialization_date(
        self, v: datetime | None, info: SerializationInfo
    ) -> str | None:
        if v is None:
            return None

        # Use date_format from the model instance
        fmt = self.date_format if self.date_format else "%Y-%m-%d %H:%M:%S"
        context = info.context or {}
        if context.get("accept_java_date_format"):
            fmt = convert_java_to_strftime(fmt)
        return v.strftime(fmt)


class ForecasterSpec(ForecasterSettingsBase):
    """
    Configuration parameters required to create a new DriftMind forecaster.
    """

    model_config = common_config

    forecaster_name: str = Field(..., description="Unique name for the forecaster.")
    features: list[str] = Field(
        ...,
        description="list of input features (column names) to be used for forecasting.",
        examples=[["Product Category A", "Product Category B", "Product Category C"]],
        min_length=1,
    )

    @field_validator("features")
    @classmethod
    def validate_features(cls, v: list[str]) -> list[str]:
        """Ensures features list is unique and strings are not blank."""
        if len(v) != len(set(v)):
            raise ValueError("Feature names must be unique.")
        if any(not s.strip() for s in v):
            raise ValueError("Feature names cannot be blank strings.")
        return v


class ForecasterConfig(ForecasterSettingsBase):
    """
    Extends the Spec to handle the API's 'all-strings' response quirk.
    Pydantic will automatically coerce strings like "30" to int 30.
    """

    @field_validator("date_format", mode="before")
    @classmethod
    def handle_java_date_conversion(
        cls, v: str | None, info: ValidationInfo
    ) -> str | None:
        # If user wants Java, don't attempt to convert it to Python
        if info.context and info.context.get("accept_java_date_format"):
            return v

        if isinstance(v, str) and "%" not in v:
            return convert_java_to_strftime(v)
        return v


class ForecasterCreationResponse(BaseModel):
    """
    The full object returned by the GET/Retrieval endpoint.
    """

    model_config = common_config

    forecaster_id: str = Field(..., description="Unique ID of the forecaster.")
    forecaster_name: str = Field(..., description="Name of the forecaster.")
    features: list[str] = Field(..., description="list of feature names.")

    # Nested configuration dictionary from the API
    configuration: ForecasterConfig = Field(
        ..., description="The internal settings of the forecaster."
    )


class FeatureStats(BaseModel):
    """
    Detailed statistics for an individual feature within a forecaster.
    """

    model_config = common_config

    anomaly_score: float
    active_clusters: int
    total_created_clusters: int
    total_deleted_clusters: int
    total_observations: int
    total_time_series_processed: int
    last_addition: str = Field(
        ...,
        validation_alias=AliasChoices("lastAddtion", "lastAddition"),
        serialization_alias="lastAddition",
        description="Timestamp of the last data addition.",
    )


class ForecasterDetails(BaseModel):
    """
    Complete description of a forecaster, including its identity,
    operational configuration, and current feature statistics.
    """

    model_config = common_config

    forecaster_id: str
    forecaster_name: str

    # Reusing the model that handles string-coercion and Java-to-Python date conversion
    configuration: ForecasterConfig

    # Dynamic dictionary where keys are feature names and values are FeatureStats
    features: dict[str, FeatureStats]


class DataFeedPayload(RootModel):
    """
    Represents a columnar dataset where keys are feature names and values are lists of numeric values.
    """

    root: dict[str, list[int | float]] = Field(
        ...,
        description="A dictionary mapping feature names to their respective numerical time-series data.",
    )

    @model_validator(mode="after")
    def validate_matrix_shape(self) -> DataFeedPayload:
        if not self.root:
            raise ValueError("Data dictionary cannot be empty.")

        lengths = {key: len(val) for key, val in self.root.items()}
        unique_lengths = set(lengths.values())

        if 0 in unique_lengths:
            raise ValueError("Lists cannot be empty.")

        if len(unique_lengths) > 1:
            raise ValueError(f"Inconsistent list lengths: {lengths}")

        return self


class ForecasterDataFeedEntry(BaseModel):
    """
    Payload used to feed a multivariate time series into a forecaster.
    """

    model_config = common_config

    forecaster_id: str = Field(
        ..., description="The unique identifier for the forecaster instance."
    )
    data: DataFeedPayload = Field(
        ...,
        description="A mapping of feature names to their aligned numeric time series.",
    )


class BulkDataFeedPayload(BaseModel):
    """
    Payload for bulk uploading multiple forecaster datasets in a single request.
    """

    model_config = common_config

    payloads_list: list[ForecasterDataFeedEntry] = Field(
        ...,
        description="A list of forecaster entries to be processed in bulk.",
        min_length=1,
    )


class StoredDataResponse(RootModel):
    """
    Response model for retrieving historical data.
    Returns dict with timestamp keys mapping to feature dicts.
    """

    root: dict[str, dict[str, float]]


class FeaturePrediction(BaseModel):
    """
    Detailed prediction results for an individual feature.
    Automatically parses timestamps and ensures parallel array consistency.
    """

    model_config = common_config

    # Using our custom type: Pydantic handles the parsing loop for us
    timestamps: list[SmartDateTime] = Field(
        ..., description="List of timestamps for the predicted points."
    )
    predictions: list[float] = Field(
        ..., description="The predicted values for the feature."
    )
    upper_confidence: list[float] = Field(
        ..., description="The upper bound of the prediction confidence interval."
    )
    lower_confidence: list[float] = Field(
        ..., description="The lower bound of the prediction confidence interval."
    )

    anomaly_score: float = Field(..., description="Calculated anomaly score.")
    forecasting_method: str = Field(..., description="Algorithm used.")
    number_of_clusters: int = Field(..., description="Clusters identified.")

    @model_validator(mode="after")
    def validate_array_consistency(self) -> FeaturePrediction:
        """Ensures all data arrays match the number of timestamps provided."""
        expected_len = len(self.timestamps)

        # We group the arrays to check their lengths in one pass
        parallel_arrays = {
            "predictions": self.predictions,
            "upper_confidence": self.upper_confidence,
            "lower_confidence": self.lower_confidence,
        }

        for name, array in parallel_arrays.items():
            if len(array) != expected_len:
                raise ValueError(
                    f"Array '{name}' length ({len(array)}) must match "
                    f"timestamps length ({expected_len})."
                )
        return self


class PredictionResponse(BaseModel):
    """
    Top-level response for prediction requests, aggregating global scores and feature-specific results.
    """

    model_config = common_config

    anomaly_score: float = Field(
        ..., description="The global anomaly score across all features."
    )
    number_of_clusters: int = Field(
        ..., description="Total number of clusters found in the global dataset."
    )
    features: dict[str, FeaturePrediction] = Field(
        ...,
        description="A mapping of feature names to their respective prediction details.",
    )


class ApiErrorResponse(BaseModel):
    """Internal model to parse standard API error bodies."""

    error: str = Field(
        ...,
        description="Error code provided by the API endpoint",
        examples=["VALIDATION_FAILED"],
    )
    details: list[str] = Field(default_factory=list)


class ForecasterDeletionResponse(BaseModel):
    """Response from deleting a forecaster."""

    message: Literal["FORECASTER_DELETED"]

    model_config = ConfigDict(
        extra="forbid",
    )


class ForecasterOperationResult(BaseModel):
    """Result of a single forecaster operation (deletion, feed, etc.)."""

    forecaster_id: str = Field(alias="forecasterId")
    status: int
    message: str

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )


class BulkOperationResponse(BaseModel):
    """Response from a bulk operation on multiple forecasters."""

    results: list[ForecasterOperationResult]

    model_config = ConfigDict(extra="forbid")

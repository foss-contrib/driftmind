from typing import Any


class DriftMindError(Exception):
    """Base exception for DriftMind client errors."""


class DriftMindConfigError(DriftMindError):
    """Configuration error related to DriftMind credentials or settings."""


class DriftMindApiError(DriftMindError):
    """Error returned by the DriftMind API."""

    def __init__(
        self,
        status_code: int,
        message: str,
        details: Any | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(f"[{status_code}] {message}")


class ForecasterCreationError(DriftMindApiError):
    """Error returned by the DriftMind forecaster-creation endpoint."""


class DataFeedError(DriftMindApiError):
    """Error returned by the DriftMind data-feed endpoint."""


class ForecastError(DriftMindApiError):
    """Error returned by the DriftMind forecast endpoint."""


class ListObjectsError(DriftMindApiError):
    """Error returned by the DriftMind list objects endpoint."""


class GetObjectDetailsError(DriftMindApiError):
    """Error returned by the DriftMind get object details endpoint."""

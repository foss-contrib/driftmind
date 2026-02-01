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
        error_code: str | None = None,
        details: list[str] | None = None,
    ) -> None:
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        self.details = details or []

        # Construct a readable error message
        prefix = f"[{status_code} {error_code}]" if error_code else f"[{status_code}]"
        # If we have specific details (like validation issues), append them
        full_msg = message
        if self.details:
            full_msg += f" | Details: {'; '.join(self.details)}"

        super().__init__(f"{prefix} {full_msg}")


class ForecasterCreationError(DriftMindApiError):
    """Error returned by the DriftMind forecaster-creation endpoint."""


class DataFeedError(DriftMindApiError):
    """Error returned by the DriftMind data-feed endpoint."""


class ForecastError(DriftMindApiError):
    """Error returned by the DriftMind forecast endpoint."""


class ListObjectsError(DriftMindApiError):
    """Error returned by the DriftMind list objects endpoint."""


class GetForecasterDetailsError(DriftMindApiError):
    """Error returned by the DriftMind get forecaster details endpoint."""


class ForecasterDeletionError(DriftMindApiError):
    """Error returned by the DriftMind delete forecaster endpoint"""

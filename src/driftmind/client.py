from __future__ import annotations

import functools
import logging
import time
from typing import Any, Callable

import requests
from pydantic import ValidationError
from requests import Response, Session
from requests.adapters import HTTPAdapter
from typing_extensions import Self

from driftmind.constants import (
    BULK_OPERATION_TIMEOUT,
    DEFAULT_MAX_RETRIES,
    DEFAULT_POOL_CONNECTIONS,
    DEFAULT_POOL_MAXSIZE,
    DEFAULT_RETRY_DELAY,
    DEFAULT_TIMEOUT,
    FORECASTER_OBSERVATIONS_PATH,
    FORECASTER_PATH,
    FORECASTER_PREDICTIONS_PATH,
    FORECASTERS_OBSERVATIONS_PATH,
    FORECASTERS_PATH,
    HTTP_EXPECTATION_FAILED,
    HTTP_FORBIDDEN,
    HTTP_NOT_FOUND,
    HTTP_OK,
    HTTP_PARTIAL_CONTENT,
    HTTP_SERVER_ERROR,
    HTTP_TOO_MANY_REQUESTS,
    HTTP_UNAUTHORIZED,
    SENSITIVE_HEADERS,
    USER_AGENT,
)
from driftmind.exceptions import (
    DataFeedError,
    DriftMindApiError,
    DriftMindError,
    ForecasterCreationError,
    ForecasterDeletionError,
    ForecastError,
    GetForecasterDetailsError,
    ListObjectsError,
)
from driftmind.models import (
    ApiErrorResponse,
    BulkDataFeedPayload,
    BulkOperationResponse,
    DataFeedPayload,
    DriftMindObjectInformationList,
    ForecasterCreationResponse,
    ForecasterDataFeedEntry,
    ForecasterDeletionResponse,
    ForecasterDetails,
    ForecasterSpec,
    PredictionResponse,
)


class _SensitiveDataFilter(logging.Filter):
    """Filter to redact sensitive data from logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "msg") and isinstance(record.msg, str):
            msg_lower = record.msg.lower()
            for header in SENSITIVE_HEADERS:
                if header in msg_lower:
                    # Use regex to replace only the header value, not everything after
                    import re

                    record.msg = re.sub(
                        rf"{re.escape(header)}:\s*\S+",
                        f"{header}: [REDACTED]",
                        record.msg,
                        flags=re.IGNORECASE,
                    )
        return True


def _validate_forecaster_id(func: Callable) -> Callable:
    """Decorator to validate forecaster_id parameter.

    Raises:
        DriftMindError: If forecaster_id is empty or contains only whitespace.
    """

    @functools.wraps(func)
    def wrapper(self, forecaster_id: str, *args, **kwargs):
        if not forecaster_id or not forecaster_id.strip():
            raise DriftMindError("forecaster_id cannot be empty or whitespace")
        return func(self, forecaster_id, *args, **kwargs)

    return wrapper


class DriftMindClient:
    """Client for the DriftMind forecasting API.

    This client provides a thin wrapper around the HTTP API, handling
    authentication, timeouts, and basic error handling.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        *,
        session: Session | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        enable_logging_protection: bool = True,
        pool_connections: int = DEFAULT_POOL_CONNECTIONS,
        pool_maxsize: int = DEFAULT_POOL_MAXSIZE,
        accept_java_date_format: bool = False,
        use_api_native_format: bool = False,
    ) -> None:
        """Initialize the DriftMindClient.

        Args:
            api_key: API key or token used for authentication.
            base_url: Base URL of the DriftMind API
                (for example, ``https://api.driftmind.ai/v1``).
            session: Optional existing ``requests.Session`` instance to use.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retry attempts for transient failures.
            retry_delay: Initial delay between retries in seconds (exponential backoff).
            enable_logging_protection: If True, installs a filter to redact API keys from logs.
            pool_connections: Number of connection pools to cache (per host).
            pool_maxsize: Maximum number of connections to save in the pool.
            accept_java_date_format: If True, date format strings are kept in Java
                style (e.g. ``dd-MM-yyyy``) instead of being converted to Python
                strftime format.
            use_api_native_format: If True, return dictionaries with camelCase keys
                matching the raw API format, instead of converting to snake_case.

        """
        self.api_key = api_key.strip()
        if not self.api_key:
            raise DriftMindError("api_key cannot be empty or whitespace")
        self.base_url = base_url.rstrip("/")
        if not self.base_url:
            raise DriftMindError("base_url cannot be empty")
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self.accept_java_date_format = accept_java_date_format
        self.use_api_native_format = use_api_native_format

        # Configure session with connection pooling
        if session is None:
            self._session = requests.Session()
            adapter = HTTPAdapter(
                pool_connections=pool_connections,
                pool_maxsize=pool_maxsize,
            )
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)
            self._owns_session = True
        else:
            self._session = session
            self._owns_session = False

        # Install logging protection
        if enable_logging_protection:
            for logger_name in ["urllib3", "requests"]:
                logger = logging.getLogger(logger_name)
                logger.addFilter(_SensitiveDataFilter())

    def _get_context(self, target: str = "internal") -> dict:
        """Helper method to generate context"""
        return {
            "target": target,
            "accept_java_date_format": self.accept_java_date_format,
            "use_api_native_format": self.use_api_native_format,
        }

    def _headers(self) -> dict[str, str]:
        """Build default HTTP headers for API requests.

        Returns:
            A dictionary containing HTTP headers for authentication and
            content negotiation.

        """
        return {
            "accept": "application/json",
            "Auth": self.api_key,
            "User-Agent": USER_AGENT,
        }

    def _request(
        self,
        method: str,
        path: str = "",
        *,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> Response:
        """Perform an HTTP request against the DriftMind API using requests.Session.

        Args:
            method: HTTP method to use (for example, ``GET`` or ``POST``).
            path: URL path to append to the base URL.
            json: Optional JSON-serializable payload to send as the request body.
            headers: Optional additional headers to merge with default headers.
            timeout: Request timeout in seconds. If None, uses the default timeout.

        Returns:
            The underlying ``requests.Response`` object.

        Raises:
            DriftMindError: If the request fails due to a network error or a non-success HTTP status code.

        """
        url = f"{self.base_url}{path}"
        request_timeout = timeout if timeout is not None else self._timeout

        # Merge default headers with per-request headers
        request_headers = self._headers()
        if headers:
            request_headers.update(headers)

        for attempt in range(self._max_retries):
            try:
                resp = self._session.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    json=json,
                    timeout=request_timeout,
                )
                # Retry on 5xx errors or 429 (rate limit)
                if (
                    resp.status_code >= HTTP_SERVER_ERROR
                    or resp.status_code == HTTP_TOO_MANY_REQUESTS
                ):
                    if attempt < self._max_retries - 1:
                        delay = self._retry_delay * (2**attempt)
                        time.sleep(delay)
                        continue
                return resp
            except (requests.Timeout, requests.ConnectionError) as err:
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay * (2**attempt)
                    time.sleep(delay)
                    continue
                raise DriftMindError(
                    f"Request to {url} failed after {self._max_retries} retries: {err}"
                ) from err
            except requests.RequestException as err:
                raise DriftMindError(f"Request to {url} failed: {err}") from err

    def _parse_and_check(
        self,
        response: requests.Response,
        error_class: type[DriftMindApiError] = DriftMindApiError,
    ) -> Any:
        """Parses the API response and performs centralized error handling.

        This method validates that the response is valid JSON and checks the HTTP
        status code. If the status indicates an error (>= 400), it attempts to
        parse the structured error body into an `ApiErrorResponse` and raises
        a granular exception.

        Args:
            response: The raw response object from the requests library.
            error_class: The specific DriftMindApiError subclass to raise if
                the response indicates a failure. Defaults to DriftMindApiError.

        Returns:
            The parsed JSON data from the response body.

        Raises:
            DriftMindApiError: Raised for global issues like 401 (Unauthorized),
                403 (Forbidden), 404 (Not Found), or if the server returns
                non-JSON content.
            error_class: The specific exception passed in the arguments, raised
                for client-side errors (400) or unprocessable entities (422),
                enriched with the API's machine-readable error code and details.
        """
        try:
            data = response.json() if response.content else {}
        except ValueError:
            raise DriftMindApiError(
                status_code=response.status_code,
                message="Server returned an invalid JSON response (not JSON).",
            ) from None

        if response.ok:
            return data

        # 1. Initialize defaults
        error_msg = "An unexpected error occurred."
        error_code = None
        details = []

        # 2. Extract structured data from the API response
        if isinstance(data, dict):
            try:
                # Validate against the ApiErrorResponse model
                error_info = ApiErrorResponse.model_validate(data)

                # In your model, 'error' is the machine-readable code (e.g. "VALIDATION_FAILED")
                error_code = error_info.error
                details = error_info.details

                # Create a human-readable message from the code or the first detail
                error_msg = details[0] if details else f"API Error: {error_code}"

            except ValidationError:
                # Fallback if the error body is just a simple {'message': '...'} or {'error': '...'}
                error_msg = data.get("message", data.get("error", error_msg))
                error_code = data.get("error")

        # 3. Handle specific global status codes
        if response.status_code == HTTP_UNAUTHORIZED:
            raise DriftMindApiError(
                HTTP_UNAUTHORIZED,
                "Unauthorized: Invalid or expired API Key.",
                "AUTH_FAILED",
            )

        if response.status_code == HTTP_FORBIDDEN:
            raise DriftMindApiError(
                HTTP_FORBIDDEN,
                "Forbidden: You do not have permission to access this resource.",
                "FORBIDDEN",
            )

        if response.status_code == HTTP_NOT_FOUND:
            raise DriftMindApiError(
                HTTP_NOT_FOUND, f"Not Found: {response.url}", "NOT_FOUND"
            )

        # 4. Raise the specific endpoint error with the correctly mapped error_code
        raise error_class(
            status_code=response.status_code,
            message=error_msg,
            error_code=error_code,  # Now properly passed!
            details=details,
        )

    def create_forecaster(
        self, payload: ForecasterSpec | dict[str, Any]
    ) -> dict[str, Any]:
        # 1. Outgoing Validation: Use context to allow Java strings if configured
        try:
            forecast_config = ForecasterSpec.model_validate(
                payload, context=self._get_context()
            )
        except ValidationError as err:
            raise DriftMindError(f"Invalid forecaster configuration: {err}") from err

        # 2. API Preparation: Target 'api' triggers conversion to Java patterns
        path = FORECASTERS_PATH
        api_payload = forecast_config.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
            context=self._get_context(target="api"),
        )
        # Fix API-specific misspelling: the API expects "timeStampIntervalInSeconds"
        if "timestampIntervalInSeconds" in api_payload:
            api_payload["timeStampIntervalInSeconds"] = api_payload.pop(
                "timestampIntervalInSeconds"
            )
        resp = self._request("POST", path, json=api_payload)

        data = self._parse_and_check(resp, error_class=ForecasterCreationError)

        # 3. Incoming Validation: Respect flag when reading back the config
        try:
            forecaster_creation_response = ForecasterCreationResponse.model_validate(
                data,
                context=self._get_context(),
            )
            # IMPORTANT: Use default context (target="internal") so the user
            # gets the format they expect (Python or Java) in the return dict.
            validated_data = forecaster_creation_response.model_dump(
                mode="json",
                by_alias=self.use_api_native_format,
                exclude_none=True,
                context=self._get_context(),
            )
        except ValidationError as err:
            raise DriftMindApiError(
                resp.status_code, "Malformed API response", details=[str(err)]
            ) from err

        # 4. Forecaster ID Extraction
        location = resp.headers.get("Location")
        header_id = location.rstrip("/").split("/")[-1] if location else None
        id_key = "forecasterId" if self.use_api_native_format else "forecaster_id"
        final_id = header_id or validated_data.get(id_key)

        if not final_id:
            raise DriftMindApiError(
                resp.status_code, "No forecaster_id found in response.", details=[data]
            )

        # 5. Success State
        validated_data[id_key] = final_id

        return validated_data

    @_validate_forecaster_id
    def get_forecaster_details(self, forecaster_id: str) -> dict[str, Any]:
        """Fetch configuration details for a specific forecaster.

        Args:
            forecaster_id: Forecaster identifier.

        Returns:
            A dictionary containing the forecaster configuration as
            returned by the API.

        Raises:
            DriftMindError: If forecaster_id is empty/whitespace, the request fails,
                or the response body cannot be parsed as JSON.
            GetForecasterDetailsError: If the API reports a 4xx/5xx error.

        """
        path = FORECASTER_PATH.format(forecaster_id=forecaster_id)
        resp = self._request("GET", path)
        data = self._parse_and_check(resp, error_class=GetForecasterDetailsError)

        try:
            # 1. Validation: Tunnels context to ForecasterConfig to handle date conversion
            forecaster_details_response = ForecasterDetails.model_validate(
                data, context=self._get_context()
            )

            # 2. Dump: Context ensures the serializer respects the user's date format preference
            validated_data = forecaster_details_response.model_dump(
                mode="json",
                by_alias=self.use_api_native_format,
                exclude_none=True,
                context=self._get_context(),
            )
        except ValidationError as err:
            raise DriftMindApiError(
                resp.status_code, "Malformed API response", details=[str(err)]
            ) from err

        return validated_data

    @_validate_forecaster_id
    def get_forecaster_data(self, forecaster_id: str) -> dict[str, Any]:
        """Fetch the data currently held by a forecaster.

        Args:
            forecaster_id: Forecaster identifier.

        Returns:
            A dictionary where keys are timestamps and values are
            dictionaries of feature values.

        Raises:
            DriftMindError: If forecaster_id is empty/whitespace or a network error occurs.
            GetForecasterDetailsError: If the API reports a 4xx/5xx error.
        """
        path = FORECASTER_OBSERVATIONS_PATH.format(forecaster_id=forecaster_id)
        resp = self._request("GET", path)
        data = self._parse_and_check(resp, error_class=GetForecasterDetailsError)

        # API returns dict directly without wrapper
        if not isinstance(data, dict):
            raise DriftMindApiError(
                resp.status_code,
                "Unexpected response format from get_forecaster_data",
                details=[str(data)],
            )

        return data

    @_validate_forecaster_id
    def feed_point(
        self,
        forecaster_id: str,
        data_point: DataFeedPayload | dict[str, list[int | float]],
    ) -> dict[str, Any]:
        """Feed time-series data to a forecaster.

        Args:
            forecaster_id: Identifier of the forecaster to feed.
            data_point: Time-series data as a dictionary mapping feature names
                to lists of numeric values. All lists must have the same length.
                Example: {"temperature": [20.5, 21.0], "humidity": [65.0, 66.5]}

        Returns:
            A dictionary containing the API response on success (HTTP 200),
            typically including a ``"message"`` field.

        Raises:
            DriftMindError: If forecaster_id is empty/whitespace, data payload fails
                validation, or a network error occurs.
            DataFeedError: If the API reports a 4xx/5xx error during the feed
                operation.
        """
        try:
            feed_payload = DataFeedPayload.model_validate(data_point)
        except ValidationError as err:
            raise DriftMindError(f"Invalid data point specification: {err}") from err

        path = FORECASTER_OBSERVATIONS_PATH.format(forecaster_id=forecaster_id)
        payload = feed_payload.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        )
        resp = self._request("POST", path, json=payload)

        data = self._parse_and_check(resp, error_class=DataFeedError)

        # For this endpoint, API returns a simple dict with "message" key
        if not isinstance(data, dict):
            raise DriftMindApiError(
                resp.status_code,
                "Unexpected response format from data feed operation",
                details=data,
            )

        return data

    def feed_data(
        self, forecaster_id: str, data: ForecasterDataFeedEntry | dict[str, Any]
    ) -> dict[str, Any]:
        """Alias for :meth:`feed_point` for backwards compatibility.

        All validation, error handling, and behavior match ``feed_point``
        exactly. See its documentation for details.

        Args:
            forecaster_id: Forecaster identifier.
            data: Time-series data, either as a ``ForecasterDataFeedEntry``
                object or a JSON-serializable dictionary.

        Returns:
            A dictionary containing the API response on success (HTTP 200),
            typically including a ``"message"`` field.

        Raises:
            DriftMindError: If the data payload fails validation.
            DataFeedError: If the API reports a 4xx/5xx error during the feed
                operation.
        """
        return self.feed_point(forecaster_id, data)

    @_validate_forecaster_id
    def forecast(self, forecaster_id: str) -> dict[str, Any]:
        """Request a forecast from a forecaster.

        Args:
            forecaster_id: Forecaster identifier.

        Returns:
            A dictionary containing the forecast data.

        Raises:
            DriftMindError: If forecaster_id is empty/whitespace or a network error occurs.
            ForecastError: If the API reports a 4xx/5xx error.
            DriftMindApiError: If the response cannot be validated.
        """
        path = FORECASTER_PREDICTIONS_PATH.format(forecaster_id=forecaster_id)
        resp = self._request("GET", path)

        data = self._parse_and_check(resp, error_class=ForecastError)

        try:
            # 1. Validation: Use context to handle potential Java patterns in metadata
            forecast_response = PredictionResponse.model_validate(
                data, context=self._get_context()
            )

            # 2. Dump: Ensure serialized output respects accept_java_date_format
            validated_data = forecast_response.model_dump(
                mode="json",
                by_alias=self.use_api_native_format,
                exclude_none=True,
                context=self._get_context(),  # Crucial for serializer consistency
            )
        except ValidationError as err:
            raise DriftMindApiError(
                resp.status_code, "Malformed API response", details=[str(err)]
            ) from err

        return validated_data

    def list_forecasters(self) -> dict[str, Any]:
        """List all forecasters available in the system.

        Returns:
            A dictionary containing the list of forecasters.

        Raises:
            ListObjectsError: If the API reports a 4xx/5xx error while listing
                objects.
            DriftMindApiError: If the response cannot be validated.
        """
        resp = self._request("GET", FORECASTERS_PATH)

        data = self._parse_and_check(resp, error_class=ListObjectsError)

        try:
            objects = DriftMindObjectInformationList.model_validate(data)
            validated_data = objects.model_dump(
                mode="json",
                by_alias=self.use_api_native_format,
                exclude_none=True,
            )
        except ValidationError as err:
            raise DriftMindApiError(
                resp.status_code, "Malformed API response", details=[str(err)]
            ) from err

        return validated_data

    def health_check(self) -> bool:
        """Check if the API is reachable and credentials are valid.

        This method performs a lightweight API call to verify connectivity
        and authentication. It's useful for validating setup before performing
        actual operations.

        Returns:
            True if the API is accessible and credentials are valid.

        Raises:
            DriftMindApiError: If the API is unreachable, credentials are invalid,
                or any other API error occurs.
            DriftMindError: If a network-level error occurs.

        Example:
            >>> with DriftMindClient(api_key=key, base_url=url) as client:
            ...     if client.health_check():
            ...         print("✓ Connected to DriftMind API")
        """
        try:
            self.list_forecasters()
            return True
        except DriftMindApiError:
            raise

    @_validate_forecaster_id
    def delete_forecaster(self, forecaster_id: str) -> dict[str, Any]:
        """Delete a forecaster from the library.

        Args:
            forecaster_id: Identifier of the forecaster to delete.

        Returns:
            A dictionary containing the API response on success (HTTP 200),
            with a ``"message"`` field.

        Raises:
            DriftMindError: If forecaster_id is empty/whitespace or a network error occurs.
            ForecasterDeletionError: If the API reports a 4xx/5xx error during
                the deletion operation (for example, the forecaster does not exist
                or an authorization error occurs).
            DriftMindApiError: If the response cannot be validated.
        """
        path = FORECASTER_PATH.format(forecaster_id=forecaster_id)
        resp = self._request("DELETE", path)

        data = self._parse_and_check(resp, error_class=ForecasterDeletionError)

        try:
            deletion_response = ForecasterDeletionResponse.model_validate(data)
            validated_data = deletion_response.model_dump(
                by_alias=self.use_api_native_format
            )
        except ValidationError as err:
            raise DriftMindApiError(
                resp.status_code, "Malformed API response", details=[str(err)]
            ) from err

        return validated_data

    def delete_all_forecasters(self) -> dict[str, Any]:
        """Delete all forecasters owned by the authenticated customer.

        Note: This method deletes forecasters sequentially as the API does not
        provide a bulk deletion endpoint. For large numbers of forecasters,
        this operation may take some time.

        This method fetches all forecasters and attempts to delete them one by one.
        It always succeeds at the method level, returning detailed results for each
        forecaster deletion attempt.

        Returns:
            A dictionary with a "results" key containing a list of deletion results.
            Each result includes:
                - "forecaster_id": The forecaster identifier
                - "status": HTTP status code (200 for success, 404/500/etc. for errors)
                - "message": "FORECASTER_DELETED" on success, or error code on failure

        Raises:
            ListObjectsError: If listing forecasters fails.
            DriftMindApiError: If the list response cannot be validated.
        """
        # 1. Get all forecasters
        forecasters_data = self.list_forecasters()

        # list_forecasters returns a list directly (RootModel)
        forecasters = forecasters_data if isinstance(forecasters_data, list) else []
        id_key = "objectId" if self.use_api_native_format else "object_id"
        forecaster_ids = [f[id_key] for f in forecasters]

        if not forecaster_ids:
            return {"results": []}

        # 2. Delete each forecaster and collect results
        results = []

        for forecaster_id in forecaster_ids:
            try:
                self.delete_forecaster(forecaster_id)
                # Success case
                results.append(
                    {
                        "forecaster_id": forecaster_id,
                        "status": 200,
                        "message": "FORECASTER_DELETED",
                    }
                )
            except ForecasterDeletionError as err:
                # API returned an error - extract status and error code
                results.append(
                    {
                        "forecaster_id": forecaster_id,
                        "status": err.status_code,
                        "message": err.error_code or err.message,
                    }
                )
            except DriftMindApiError as err:
                # Unexpected API error (malformed response, etc.)
                results.append(
                    {
                        "forecaster_id": forecaster_id,
                        "status": err.status_code,
                        "message": err.error_code or err.message,
                    }
                )
            except DriftMindError as err:
                # Network-level error
                results.append(
                    {
                        "forecaster_id": forecaster_id,
                        "status": 0,
                        "message": str(err),
                    }
                )

        # 3. Validate and return
        try:
            bulk_response = BulkOperationResponse(results=results)
            return bulk_response.model_dump(by_alias=self.use_api_native_format)
        except ValidationError as err:
            # This should not happen, but handle it just in case
            raise DriftMindError(
                f"Failed to construct deletion response: {err}"
            ) from err

    def close(self) -> None:
        """Close the underlying HTTP session if owned by this client."""
        if self._owns_session:
            self._session.close()

    def __enter__(self) -> Self:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - closes the session."""
        self.close()

    def bulk_feed_data(
        self, payload: BulkDataFeedPayload | dict[str, Any]
    ) -> dict[str, Any]:
        """Feed observations to multiple forecasters at once.

        Args:
            payload: Bulk feed payload containing data for multiple forecasters,
                either as a ``BulkDataFeedPayload`` object or a JSON-serializable
                dictionary.

        Returns:
            A dictionary with a "results" key containing a list of feed results.
            Each result includes:
                - "forecaster_id": The forecaster identifier
                - "status": HTTP status code (200 for success, 400/500/etc. for errors)
                - "message": Status message (e.g., "FED", "MISSING_COLUMN_sin", etc.)

        The method succeeds at the API level regardless of individual forecaster
        feed results. Check the status codes in the results to determine which
        forecasters were successfully fed.

        Raises:
            DriftMindError: If the payload fails validation.
            DriftMindApiError: If the response cannot be parsed or validated.
        """
        # 1. Validate input
        try:
            bulk_payload = BulkDataFeedPayload.model_validate(payload)
        except ValidationError as err:
            raise DriftMindError(f"Invalid bulk feed payload: {err}") from err

        # 2. Prepare request
        path = FORECASTERS_OBSERVATIONS_PATH
        request_payload = bulk_payload.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        )
        # Use longer timeout for bulk operations
        resp = self._request(
            "PATCH", path, json=request_payload, timeout=BULK_OPERATION_TIMEOUT
        )

        # 3. Handle response - 200, 206, and 417 are all valid responses
        status = resp.status_code

        # Parse JSON
        try:
            data = resp.json()
        except ValueError as err:
            raise DriftMindApiError(
                status,
                "Unexpected non-JSON response from bulk feed operation",
                details=[resp.text],
            ) from err

        # 4. Check if status is one of the expected codes
        if status not in (HTTP_OK, HTTP_PARTIAL_CONTENT, HTTP_EXPECTATION_FAILED):
            # Unexpected status - try to parse as error
            try:
                parsed_error = ApiErrorResponse.model_validate(data)
                raise DataFeedError(
                    status_code=status,
                    message=f"API Error: {parsed_error.error}",
                    error_code=parsed_error.error,
                    details=parsed_error.details,
                )
            except ValidationError as err:
                raise DriftMindApiError(
                    status,
                    "Unexpected response from bulk feed operation",
                    details=[str(data)],
                ) from err

        # 5. Extract results from the response (API uses 'results' for success, 'details' for errors)
        if not isinstance(data, dict):
            raise DriftMindApiError(
                status,
                "Malformed bulk feed response: expected dict",
                details=[str(data)],
            )

        results = data.get("results") or data.get("details", [])
        if not results:
            raise DriftMindApiError(
                status,
                "Malformed bulk feed response: missing 'results' or 'details' field",
                details=[str(data)],
            )

        # 6. Validate and structure the response
        try:
            bulk_response = BulkOperationResponse(results=results)
            return bulk_response.model_dump(by_alias=self.use_api_native_format)
        except ValidationError as err:
            raise DriftMindApiError(
                status, "Malformed API response", details=[str(err)]
            ) from err

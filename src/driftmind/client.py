import logging
logger = logging.getLogger("Driftmind API Client")
from __future__ import annotations

from http import HTTPStatus
from typing import Any

import requests
from pydantic import ValidationError
from requests import Response, Session

from .exceptions import (
    DataFeedError,
    DriftMindApiError,
    DriftMindError,
    ForecasterCreationError,
    ForecastError,
    GetObjectDetailsError,
    ListObjectsError,
)
from .models import (
    ForecasterConfig,
    ForecasterSpec,
    ForecastResponse,
    ObjectInformationList,
    TimeSeriesSegment,
)


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
        timeout: float = 10.0,
    ) -> None:
        """Initialize the DriftMindClient.

        Args:
            api_key: API key or token used for authentication.
            base_url: Base URL of the DriftMind API
                (for example, ``https://api.driftmind.ai/v1``).
            session: Optional existing ``requests.Session`` instance to use.
            timeout: Request timeout in seconds.

        """
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self._session = session or requests.Session()
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        """Build default HTTP headers for API requests.

        Returns:
            A dictionary containing HTTP headers for authentication and
            content negotiation.

        """
        return {
            "accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Auth": self.api_key,
        }

    def _request(
        self,
        method: str,
        path: str = "",
        *,
        json: dict[str, Any] | None = None,
    ) -> Response:
        """Perform an HTTP request against the DriftMind API using requests.Session.

        Args:
            method: HTTP method to use (for example, ``GET`` or ``POST``).
            path: URL path to append to the base URL.
            json: Optional JSON-serializable payload to send as the request body.

        Returns:
            The underlying ``requests.Response`` object.

        Raises:
            DriftMindError: If the request fails due to a network error or a non-success HTTP status code.

        """
        if path:
            url = f"{self.base_url}/{path.lstrip('/')}"
        else:
            url = self.base_url
        
        logger.debug(f"Requesting: {method} {url}")
 
        try:
            resp = self._session.request(
                method=method,
                url=url,
                headers=self._headers(),
                json=json,
                timeout=self._timeout,
            )
        except requests.RequestException as err:
            raise DriftMindError(f"Request to {url} failed: {err}") from err
        return resp

    def _parse_and_check(
        self, resp: Response, error_class: type[DriftMindApiError] = DriftMindApiError
    ) -> Any:
        """Helper to parse JSON and raise specific API errors automatically."""
        try:
            data = resp.json()
        except ValueError as err:
            # If not JSON, we check if it was an error status
            if not resp.ok:
                raise DriftMindApiError(
                    resp.status_code, "API error with non-JSON body", details=resp.text
                ) from err
            # If it was a 200/201 but not JSON, that's also an error
            raise DriftMindApiError(
                resp.status_code,
                "Expected JSON response but received text",
                details=resp.text,
            ) from err

        if not resp.ok:
            status = resp.status_code
            message = "API Error"

            # Specific logic for your 400 Bad Request list of strings
            if status == HTTPStatus.BAD_REQUEST:
                if isinstance(data, list) and all(isinstance(x, str) for x in data):
                    message = f"Bad Request: {'; '.join(data)}"
                elif isinstance(data, dict):
                    message = data.get("error", data.get("message", "Bad Request"))
            else:
                # Generic message extraction for 401, 404, 500, etc.
                if isinstance(data, dict):
                    message = data.get("error", data.get("message", f"Error {status}"))

            raise error_class(status, message, details=data)

        return data

    def create_forecaster(
        self, payload: ForecasterConfig | dict[str, Any]
    ) -> dict[str, Any]:
        """Create a new forecaster on the DriftMind API."""
        
        # 1. Outgoing Validation
        try:
            forecast_config = ForecasterConfig.model_validate(payload)
        except ValidationError as err:
            raise DriftMindError(f"Invalid forecaster configuration: {err}") from err

        # 2. FIXED: Force CamelCase for Java API Compliance
        # We dump the model to a dict, but we MUST ensure keys match the Java DTOs.
        # If ForecasterConfig is not aliased correctly, we patch it here manually.
        raw_dump = forecast_config.model_dump(mode="json", exclude_none=True)
        
        api_payload = {
            "forecasterName": raw_dump.get("forecaster_name") or raw_dump.get("forecasterName"),
            "features": raw_dump.get("features"),
            "inputSize": raw_dump.get("input_size") or raw_dump.get("inputSize"),
            "outputSize": raw_dump.get("output_size") or raw_dump.get("outputSize"),
            # Map other optional fields similarly
            "timeStampIntervalInSeconds": raw_dump.get("time_stamp_interval_in_seconds"),
            "maxClustersAllowed": raw_dump.get("max_clusters_allowed")
        }
        
        # Clean up None values from the manual map
        api_payload = {k: v for k, v in api_payload.items() if v is not None}

    
        # 3. FIXED: Correct Endpoint URL
        # The API documentation specifies POST /driftmind/v1/forecasters
        resp = self._request("POST", "forecasters", json=api_payload)
        
        # ... (Rest of your error handling logic remains valid) ...

        # This will raise ForecasterCreationError if status is 4xx/5xx
        data = self._parse_and_check(resp, error_class=ForecasterCreationError)

        # 4. Identity Extraction & Response Mapping
        # Java API returns "forecasterId" (camelCase). Python likely expects "forecaster_id".
        # We handle both to be safe.
        location = resp.headers.get("Location")
        header_id = location.rstrip("/").split("/")[-1] if location else None
        
        returned_id = data.get("forecasterId") or data.get("forecaster_id")
        final_id = header_id or returned_id

        if not final_id:
            raise DriftMindApiError(
                resp.status_code, "No forecaster_id found in response.", details=data
            )

        # 5. Success State
        # Ensure we return snake_case to the Python user, even if API gave camelCase
        data["forecaster_id"] = final_id
        
        return data

    def feed_point(
        self,
        forecaster_id: str,
        data_point: TimeSeriesSegment | dict[str, Any],
    ) -> dict[str, Any]:
        """Feed time-series data to a forecaster.

        Args:
            forecaster_id: Identifier of the forecaster to feed.
            data_point: Time-series data, either as a ``TimeSeriesSegment``
                object or a JSON-serializable dictionary matching the same
                structure (feature name → list of floats).

        Returns:
            A dictionary containing the API response on success (HTTP 200),
            typically including a ``"message"`` field.

        Raises:
            DriftMindError: If the forecaster ID is unknown, or the data payload
                fails validation.
            DriftMindApiError: If the HTTP request fails, the response body cannot
                be parsed as JSON, the API returns an unexpected payload shape,
                or an unexpected status code.
            DataFeedError: If the API reports a 4xx/5xx error during the feed
                operation (for example, the forecaster does not exist or an
                authorization error occurs).
        """
        try:
            segment = TimeSeriesSegment.model_validate(data_point)
        except ValidationError as err:
            raise DriftMindError(f"Invalid data point specification: {err}") from err

        payload = segment.model_dump(mode="json", exclude_none=True)

        resp = self._request("POST", "forecasters/"+forecaster_id+"/observations", json=payload)
        data = self._parse_and_check(resp)
        status = resp.status_code

        if status == HTTPStatus.OK:
            if not isinstance(data, dict) or "message" not in data:
                raise DriftMindApiError(
                    resp.status_code,
                    "Unexpected success payload from data feed operation",
                    details=resp.text,
                )
            return data
        elif status == HTTPStatus.NOT_FOUND:
            if isinstance(data, dict) and isinstance(data.get("error"), str):
                raise DataFeedError(status, data["error"], details=data)
            raise DataFeedError(status, "Forecaster not found", details=data)
        elif status in (
            HTTPStatus.UNAUTHORIZED,
            HTTPStatus.PAYMENT_REQUIRED,
            HTTPStatus.FORBIDDEN,
            HTTPStatus.INTERNAL_SERVER_ERROR,
        ):
            if isinstance(data, dict) and isinstance(data.get("error"), str):
                raise DataFeedError(status, data["error"], details=data)
            raise DataFeedError(status, "API error", details=data)
        else:
            raise DriftMindApiError(
                status, "Unexpected response from API", details=data
            )

    def feed_data(
        self, forecaster_id: str, data: TimeSeriesSegment | dict[str, Any]
    ) -> dict[str, Any]:
        """Alias for :meth:`feed_point` for backwards compatibility.

        All validation, error handling, and behavior match ``feed_point``
        exactly. See its documentation for details.

        Args:
            forecaster_id: Forecaster identifier.
            data: Time-series data, either as a ``TimeSeriesSegment``
                object or a JSON-serializable dictionary matching the same
                structure (feature name → list of floats).

        Returns:
            A dictionary containing the API response on success (HTTP 200),
            typically including a ``"message"`` field.

        Raises:
            DriftMindError: If the forecaster ID is unknown, the data payload
                fails validation, or the feature names do not match the
                forecaster specification.
            DriftMindApiError: If the HTTP request fails, the response body cannot
                be parsed as JSON, the API returns an unexpected payload shape,
                or an unexpected status code.
            DataFeedError: If the API reports a 4xx/5xx error during the feed
                operation (for example, the forecaster does not exist).
        """
        return self.feed_point(forecaster_id, data)

    def forecast(self, forecaster_id: str) -> ForecastResponse:
        """Request a forecast from a forecaster.

        Args:
            forecaster_id: Forecaster identifier.

        Returns:
            A ``ForecastResponse`` object containing the forecast (HTTP 200).

        Raises:
            DriftMindApiError: If the HTTP request fails, the response body cannot
                be parsed as JSON, the API returns an unexpected payload shape,
                or an unexpected status code.
            ForecastError: If the API reports a 4xx/5xx error (for example,
                the forecaster does not exist or an authorization error occurs).
        """
        path = f"/forecasters/{forecaster_id}/predictions"
        resp = self._request("GET", path)
        data = self._parse_and_check(resp)
        status = resp.status_code

        if status == HTTPStatus.OK:
            try:
                print(f"Data Returned:\n{data}")
                forecast = ForecastResponse.model_validate(data)
            except ValidationError as err:
                # Print the ACTUAL validation error so we can see what field is wrong
                print(f"❌ PYDANTIC VALIDATION ERROR:\n{err}")
                raise DriftMindApiError(
                    resp.status_code, "Unexpected forecast payload", details=resp.text
                ) from err
            return forecast.model_dump(mode="json", by_alias=True, exclude_none=True)
        elif status == HTTPStatus.NOT_FOUND:
            raise ForecastError(status, "Forecaster not found", details=data)
        elif status in (
            HTTPStatus.UNAUTHORIZED,
            HTTPStatus.PAYMENT_REQUIRED,
            HTTPStatus.FORBIDDEN,
            HTTPStatus.INTERNAL_SERVER_ERROR,
        ):
            if isinstance(data, dict) and isinstance(data.get("error"), str):
                raise ForecastError(status, data["error"], details=data)
            raise ForecastError(status, "API error", details=data)
        else:
            raise DriftMindApiError(
                status, "Unexpected response from API", details=data
            )

    def get_forecaster_data(self, forecaster_id: str) -> dict[str, Any]:
        """Fetch the data currently held by a forecaster.

        Args:
            forecaster_id: Forecaster identifier.

        Returns:
            A dictionary where keys are timestamps and values are
            dictionaries of feature values, as returned by the API.

        Raises:
            DriftMindError: If the request fails or the response body
                cannot be parsed as JSON.

        """
        path = f"/forecasters/{forecaster_id}/observations"
        resp = self._request("GET", path)
        data = self._parse_and_check(resp)

        return data

    def list_forecasters(self) -> ObjectInformationList:
        """List all forecasters available in the system.

        Returns:
            An ``ObjectInformationList`` containing one entry per forecaster.

        Raises:
            DriftMindApiError: If the response body cannot be parsed as JSON.
            ListObjectsError: If the API reports a 4xx/5xx error while listing
                objects and no specific error message is provided.
        """
        resp = self._request("GET", "")
        data = self._parse_and_check(resp, error_class=ListObjectsError)

        try:
            objects = ObjectInformationList.model_validate(data)
            validated_data = objects.model_dump(
                mode="json", by_alias=False, exclude_none=True
            )
        except ValidationError as err:
            raise DriftMindApiError(
                resp.status_code, "Malformed API response", details=err
            ) from err

        return validated_data

    def get_forecaster_details(
        self, forecaster_id: str, cached: bool = True
    ) -> dict[str, Any]:
        """Fetch configuration details for a specific forecaster.
        
        Returns the raw JSON response from the API without local validation.
        """
        # Correct Path based on your OpenAPI spec
        path = f"forecasters/{forecaster_id}"
        
        # 1. Get the raw response
        resp = self._request("GET", path)
        
        # 2. Check for HTTP errors (4xx/5xx) and parse JSON
        # This function already handles raising DriftMindApiError if the status is bad
        data = self._parse_and_check(resp, error_class=GetObjectDetailsError)

        # 3. Return the raw data.
        # No Pydantic validation here. we pass it through to the user instead of crashing.
        
        return data

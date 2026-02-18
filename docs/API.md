# DriftMind Client API Reference

Complete reference for all DriftMind client operations with input/output formats and examples.

**[← Back to README](../README.md)**

All API responses are automatically validated using Pydantic v2 models, ensuring type safety and data integrity. You work with standard Python dictionaries—validation happens transparently.

---

## Table of Contents

- [Client Initialization](#client-initialization)
- [Forecaster Management](#forecaster-management)
  - [create_forecaster](#create_forecaster)
  - [list_forecasters](#list_forecasters)
  - [get_forecaster_details](#get_forecaster_details)
  - [delete_forecaster](#delete_forecaster)
  - [delete_all_forecasters](#delete_all_forecasters)
- [Data Operations](#data-operations)
  - [feed_point](#feed_point)
  - [get_forecaster_data](#get_forecaster_data)
  - [bulk_feed_data](#bulk_feed_data)
- [Forecasting](#forecasting)
  - [forecast](#forecast)
- [Utilities](#utilities)
  - [health_check](#health_check)

---

## Client Initialization

Initialize the client with API credentials.

**Parameters:**

| Name                        | Type    | Required | Description                                          |
|-----------------------------|---------|----------|------------------------------------------------------|
| `api_key`                   | str     | Yes      | API authentication key                               |
| `base_url`                  | str     | Yes      | API base URL                                         |
| `session`                   | Session | No       | Custom requests.Session (for advanced use)           |
| `timeout`                   | float   | No       | Request timeout in seconds (default: 10.0)           |
| `max_retries`               | int     | No       | Maximum retry attempts (default: 3)                  |
| `retry_delay`               | float   | No       | Initial retry delay in seconds (default: 1.0)        |
| `enable_logging_protection` | bool    | No       | Redact API keys from logs (default: True)            |
| `pool_connections`          | int     | No       | Number of connection pools to cache (default: 10)    |
| `pool_maxsize`              | int     | No       | Maximum connections to save in pool (default: 10)    |
| `accept_java_date_format`   | bool    | No       | Accept Java SimpleDateFormat patterns (default: False)|
| `use_api_native_format`     | bool    | No       | Use camelCase keys for input/output (default: False)  |

**Example:**

```python
from driftmind import DriftMindClient
from driftmind.utils import load_credentials

creds = load_credentials()

# Recommended: Use context manager
with DriftMindClient(
    api_key=creds["DRIFTMIND_API_KEY"],
    base_url=creds["DRIFTMIND_API_URL"]
) as client:
    # Your code here
    pass

# Alternative: Manual cleanup
client = DriftMindClient(
    api_key=creds["DRIFTMIND_API_KEY"],
    base_url=creds["DRIFTMIND_API_URL"],
    timeout=15.0,
    max_retries=5
)
try:
    # Your code here
    pass
finally:
    client.close()
```

> **Note:** This reference documents the default Pythonic interface (`snake_case` keys). If you need `camelCase` keys for backwards compatibility with pre-v0.3 clients, see [API_NATIVE.md](API_NATIVE.md).

---

## Forecaster Management

### create_forecaster

Create a new forecaster with specified configuration.

**Pydantic Models:** Input validated by `ForecasterSpec`, output validated by `ForecasterCreationResponse`

**Input:**

```python
{
    "forecaster_name": str,           # Required: Human-readable name
    "features": list[str],            # Required: Feature names
    "input_size": int,                # Required: Input window size
    "output_size": int,               # Required: Output forecast size
    "max_clusters_allowed": int,      # Optional: Max clusters (default: 200)
    "similarity_threshold": float,    # Optional: Cluster threshold 0-1 (default: 0.8)
    "timestamp_interval_in_seconds": int,  # Optional: Time between points (default: 60)
    "fit_rate": int,                  # Optional: Update frequency (default: 1)
    "use_custom_date_format": bool,   # Optional: Use custom date format (default: False)
    "date_format": str,               # Optional: Python strftime format (default: "%d-%m-%Y %H:%M:%S")
    "use_initialization_date": bool,  # Optional: Use explicit start date (default: False)
    "initialization_date": str        # Optional: Start date (default: current time)
}
```

**Output:**

```python
{
    "forecaster_id": str,             # Unique forecaster identifier
    "forecaster_name": str,           # Name provided
    "features": list[str],            # Feature names
    "configuration": {
        "input_size": int,
        "output_size": int,
        "max_clusters_allowed": int,
        "similarity_threshold": float,
        "timestamp_interval_in_seconds": int,
        "fit_rate": int,
        "date_format": str,
        "initialization_date": str
    }
}
```

**Example:**

```python
# Minimal configuration
forecaster = client.create_forecaster({
    "forecaster_name": "Temperature Monitor",
    "features": ["temp", "humidity"],
    "input_size": 30,
    "output_size": 5
})
forecaster_id = forecaster["forecaster_id"]

# Full configuration
forecaster = client.create_forecaster({
    "forecaster_name": "Industrial Sensor",
    "features": ["vibration", "temp", "pressure"],
    "input_size": 60,
    "output_size": 10,
    "max_clusters_allowed": 100,
    "similarity_threshold": 0.85,
    "timestamp_interval_in_seconds": 30,
    "fit_rate": 1,
    "use_custom_date_format": True,
    "date_format": "%Y-%m-%d %H:%M:%S",
    "use_initialization_date": True,
    "initialization_date": "2026-01-01 00:00:00"
})
```

**Raises:**

- `DriftMindError`: Invalid configuration or validation failure
- `ForecasterCreationError`: API error during creation

---

### list_forecasters

List all forecasters owned by the authenticated user.

**Pydantic Models:** Output validated by `DriftMindObjectInformationList`

**Input:** None

**Output:**

```python
[
    {
        "object_id": str,              # Forecaster ID
        "object_name": str,            # Forecaster name
        "created_at": str,             # Creation date (YYYY-MM-DD)
        "created_by": str,             # User identifier
        "object_type": str,            # Always "FORECASTER"
        "data_processed": float,       # Data processed in MB
        "requests_processed": int      # Number of requests
    },
    ...
]
```

**Example:**

```python
forecasters = client.list_forecasters()

for f in forecasters:
    print(f"{f['object_name']} (ID: {f['object_id']})")
    print(f"  Data processed: {f['data_processed']} MB")
    print(f"  Requests: {f['requests_processed']}")
```

**Raises:**

- `ListObjectsError`: API error during listing

---

### get_forecaster_details

Get detailed information about a specific forecaster.

**Pydantic Models:** Output validated by `ForecasterDetails`

**Input:**

```python
forecaster_id: str  # Forecaster identifier
```

**Output:**

```python
{
    "forecaster_id": str,
    "forecaster_name": str,
    "features": {
        "feature_name": {
            "anomaly_score": float,
            "active_clusters": int,
            "total_created_clusters": int,
            "total_deleted_clusters": int,
            "total_observations": int,
            "total_time_series_processed": int,
            "last_addition": str       # Timestamp of last data point
        },
        ...
    },
    "configuration": {
        "input_size": int,
        "output_size": int,
        "max_clusters_allowed": int,
        "similarity_threshold": float,
        "timestamp_interval_in_seconds": int,
        "fit_rate": int,
        "date_format": str,
        "initialization_date": str
    }
}
```

**Example:**

```python
details = client.get_forecaster_details(forecaster_id)

print(f"Forecaster: {details['forecaster_name']}")
print(f"Input size: {details['configuration']['input_size']}")

for feature, stats in details["features"].items():
    print(f"\n{feature}:")
    print(f"  Active clusters: {stats['active_clusters']}")
    print(f"  Anomaly score: {stats['anomaly_score']}")
    print(f"  Observations: {stats['total_observations']}")
```

**Raises:**

- `DriftMindError`: Empty or invalid forecaster_id
- `GetForecasterDetailsError`: API error (e.g., forecaster not found)

---

### delete_forecaster

Delete a specific forecaster.

**Pydantic Models:** Output validated by `ForecasterDeletionResponse`

**Input:**

```python
forecaster_id: str  # Forecaster identifier
```

**Output:**

```python
{
    "message": "FORECASTER_DELETED"
}
```

**Example:**

```python
result = client.delete_forecaster(forecaster_id)
print(result["message"])  # "FORECASTER_DELETED"
```

**Raises:**

- `DriftMindError`: Empty or invalid forecaster_id
- `ForecasterDeletionError`: API error (e.g., forecaster not found)

---

### delete_all_forecasters

Delete all forecasters owned by the authenticated user.

**Input:** None

**Output:**

```python
{
    "results": [
        {
            "forecaster_id": str,
            "status": int,             # HTTP status code (200 = success)
            "message": str             # "FORECASTER_DELETED" or error message
        },
        ...
    ]
}
```

**Example:**

```python
results = client.delete_all_forecasters()

for result in results["results"]:
    if result["status"] == 200:
        print(f"✓ Deleted {result['forecaster_id']}")
    else:
        print(f"✗ Failed to delete {result['forecaster_id']}: {result['message']}")
```

**Note:** Deletes forecasters sequentially as the API doesn't provide bulk deletion.

**Raises:**

- `ListObjectsError`: Error listing forecasters

---

## Data Operations

### feed_point

Feed time-series data to a forecaster.

**Pydantic Models:** Output validated by `ForecasterDeletionResponse` (reuses same response format)

**Input:**

```python
forecaster_id: str  # Forecaster identifier
data_point: dict[str, list[float]]  # Feature name -> list of values
```

All feature lists must have the same length. Data points are processed in order.

**Output:**

```python
{
    "message": "FORECASTER_FED"
}
```

**Example:**

```python
# Feed single point
data = {
    "temp": [25.5],
    "humidity": [65.0]
}
client.feed_point(forecaster_id, data)

# Feed multiple points
data = {
    "temp": [25.5, 26.0, 25.8],
    "humidity": [65.0, 64.5, 65.2]
}
client.feed_point(forecaster_id, data)
```

**Raises:**

- `DriftMindError`: Empty forecaster_id, invalid data format, or inconsistent list lengths
- `DataFeedError`: API error (e.g., wrong features, missing columns)

---

### get_forecaster_data

Retrieve historical observations stored in the forecaster.

**Pydantic Models:** Output validated by `StoredDataResponse`

**Input:**

```python
forecaster_id: str  # Forecaster identifier
```

**Output:**

```python
{
    "timestamp": {
        "feature1": float,
        "feature2": float,
        ...
    },
    ...
}
```

**Example:**

```python
history = client.get_forecaster_data(forecaster_id)

for timestamp, features in history.items():
    print(f"{timestamp}: {features}")
```

**Raises:**

- `DriftMindError`: Empty or invalid forecaster_id
- `GetForecasterDetailsError`: API error

---

### bulk_feed_data

Feed data to multiple forecasters in a single request.

**Pydantic Models:** Output validated by `BulkOperationResponse`

**Input:**

```python
{
    "payloads_list": [
        {
            "forecaster_id": str,
            "data": dict[str, list[float]]  # Feature name -> values
        },
        ...
    ]
}
```

**Output:**

```python
{
    "results": [
        {
            "forecaster_id": str,
            "status": int,             # HTTP status code
            "message": str             # "FED" or error message
        },
        ...
    ]
}
```

**Status Codes:**

- `200`: All forecasters fed successfully
- `206`: Partial success (some forecasters failed)
- `417`: All forecasters failed

**Example:**

```python
payload = {
    "payloads_list": [
        {
            "forecaster_id": forecaster_id_1,
            "data": {
                "temp": [25.5, 26.0],
                "humidity": [65.0, 64.5]
            }
        },
        {
            "forecaster_id": forecaster_id_2,
            "data": {
                "pressure": [1013.2, 1013.5],
                "wind": [5.2, 5.5]
            }
        }
    ]
}

results = client.bulk_feed_data(payload)

for result in results["results"]:
    if result["status"] == 200:
        print(f"✓ Fed {result['forecaster_id']}")
    else:
        print(f"✗ Failed {result['forecaster_id']}: {result['message']}")
```

**Raises:**

- `DriftMindError`: Invalid payload format
- `DriftMindApiError`: Unexpected API response

---

## Forecasting

### forecast

Request predictions from a forecaster.

**Pydantic Models:** Output validated by `PredictionResponse`

**Input:**

```python
forecaster_id: str  # Forecaster identifier
```

**Requirements:**

- Minimum data points: `input_size + output_size`
- Example: If input_size=30 and output_size=5, need at least 35 points

**Output:**

```python
{
    "anomaly_score": float,           # Global anomaly score (0-1)
    "number_of_clusters": int,        # Total active clusters
    "features": {
        "feature_name": {
            "timestamps": list[str],   # Forecast timestamps
            "predictions": list[float],  # Predicted values
            "upper_confidence": list[float],  # Upper confidence bound
            "lower_confidence": list[float],  # Lower confidence bound
            "anomaly_score": float,    # Feature-specific anomaly score
            "forecasting_method": str,  # "Clustering" or "Time Series Extension"
            "number_of_clusters": int  # Clusters for this feature
        },
        ...
    }
}
```

**Example:**

```python
result = client.forecast(forecaster_id)

print(f"Global anomaly score: {result['anomaly_score']:.4f}")
print(f"Active clusters: {result['number_of_clusters']}")

for feature, pred in result["features"].items():
    print(f"\n{feature}:")
    print(f"  Method: {pred['forecasting_method']}")
    print(f"  Next value: {pred['predictions'][0]:.4f}")
    print(f"  Confidence: [{pred['lower_confidence'][0]:.4f}, {pred['upper_confidence'][0]:.4f}]")
    print(f"  Anomaly score: {pred['anomaly_score']:.4f}")
```

**Raises:**

- `DriftMindError`: Empty or invalid forecaster_id
- `ForecastError`: API error (e.g., insufficient data - 422 status)

---

## Utilities

### health_check

Verify API connectivity and credentials.

**Input:** None

**Output:**

```python
bool  # True if API is accessible
```

**Example:**

```python
try:
    if client.health_check():
        print("✓ API is accessible")
except DriftMindApiError as e:
    if e.status_code == 401:
        print("✗ Invalid credentials")
    else:
        print(f"✗ API error: {e.message}")
except DriftMindError as e:
    print(f"✗ Network error: {e}")
```

**Raises:**

- `DriftMindApiError`: API error (e.g., invalid credentials)
- `DriftMindError`: Network error

---

## Error Handling

All methods may raise the following exceptions:

### DriftMindError

Base exception for all client errors.

**Common causes:**

- Empty or whitespace forecaster_id
- Invalid data format
- Validation failures
- Network errors

**Example:**

```python
from driftmind.exceptions import DriftMindError

try:
    client.forecast("")
except DriftMindError as e:
    print(f"Error: {e}")  # "forecaster_id cannot be empty or whitespace"
```

### DriftMindApiError

API-level errors (authentication, not found, etc.).

**Attributes:**

- `status_code`: HTTP status code
- `message`: Error message
- `error_code`: Machine-readable error code
- `details`: Additional error details

**Example:**

```python
from driftmind.exceptions import DriftMindApiError

try:
    client.get_forecaster_details("nonexistent-id")
except DriftMindApiError as e:
    print(f"Status: {e.status_code}")  # 404
    print(f"Error: {e.error_code}")    # "NOT_FOUND"
    print(f"Message: {e.message}")
```

### Specific Exceptions

- `ForecasterCreationError`: Error creating forecaster
- `ForecasterDeletionError`: Error deleting forecaster
- `DataFeedError`: Error feeding data
- `ForecastError`: Error generating forecast
- `GetForecasterDetailsError`: Error retrieving details
- `ListObjectsError`: Error listing forecasters
- `DriftMindConfigError`: Configuration error (e.g., missing credentials)

---

## Complete Example

```python
from driftmind import DriftMindClient
from driftmind.utils import load_credentials
from driftmind.exceptions import DriftMindError, ForecastError
import math

# Load credentials
creds = load_credentials()

with DriftMindClient(
    api_key=creds["DRIFTMIND_API_KEY"],
    base_url=creds["DRIFTMIND_API_URL"]
) as client:
    # Verify connectivity
    if client.health_check():
        print("✓ Connected to API")
    
    # Create forecaster
    forecaster = client.create_forecaster({
        "forecaster_name": "Demo Forecaster",
        "features": ["sin", "cos"],
        "input_size": 10,
        "output_size": 3
    })
    forecaster_id = forecaster["forecaster_id"]
    print(f"✓ Created forecaster: {forecaster_id}")
    
    # Feed data (minimum: input_size + output_size = 13 points)
    for i in range(20):
        angle = i * 0.1
        data = {
            "sin": [math.sin(angle)],
            "cos": [math.cos(angle)]
        }
        client.feed_point(forecaster_id, data)
    print("✓ Fed 20 data points")
    
    # Get forecast
    try:
        result = client.forecast(forecaster_id)
        print(f"\n✓ Forecast generated:")
        print(f"  Anomaly score: {result['anomaly_score']:.4f}")
        
        for feature, pred in result["features"].items():
            print(f"\n  {feature}:")
            print(f"    Next 3 values: {pred['predictions'][:3]}")
            print(f"    Method: {pred['forecasting_method']}")
    except ForecastError as e:
        print(f"✗ Forecast error: {e.message}")
    
    # Get details
    details = client.get_forecaster_details(forecaster_id)
    print(f"\n✓ Forecaster details:")
    for feature, stats in details["features"].items():
        print(f"  {feature}: {stats['total_observations']} observations")
    
    # Clean up
    client.delete_forecaster(forecaster_id)
    print(f"\n✓ Deleted forecaster")
```

---

## See Also

- [README.md](../README.md) - Getting started guide
- [examples/quickstart.py](../examples/quickstart.py) - Runnable example
- [examples/demo.ipynb](../examples/demo.ipynb) - Interactive demo
- [tests/TESTING.md](../tests/TESTING.md) - Testing documentation

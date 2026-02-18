# DriftMind Client API Reference (Native Format)

API reference for the native (camelCase) format mode. Enable it with `use_api_native_format=True`.

**[Default (snake_case) API Reference](API.md)** | **[Back to README](../README.md)**

This document mirrors the main [API.md](API.md) but shows the camelCase key names used when `use_api_native_format=True`. All method signatures, error handling, and behavior remain identical.

---

## Client Initialization

```python
from driftmind import DriftMindClient

client = DriftMindClient(
    api_key="your-api-key",
    base_url="https://api.thingbook.io/access/api/driftmind",
    use_api_native_format=True,          # camelCase keys in and out
    accept_java_date_format=True,        # optional: keep Java date patterns
)
```

---

## Forecaster Management

### create_forecaster

**Input:**

```python
{
    "forecasterName": str,                    # Required
    "features": list[str],                    # Required
    "inputSize": int,                         # Required
    "outputSize": int,                        # Required
    "maxClustersAllowed": int,                # Optional
    "similarityThreshold": float,             # Optional
    "timestampIntervalInSeconds": int,        # Optional
    "fitRate": int,                           # Optional
    "useCustomDateFormat": bool,              # Optional
    "dateFormat": str,                        # Optional (Java format with accept_java_date_format)
    "useInitializationDate": bool,            # Optional
    "initializationDate": str                 # Optional
}
```

**Output:**

```python
{
    "forecasterId": str,
    "forecasterName": str,
    "features": list[str],
    "configuration": {
        "inputSize": int,
        "outputSize": int,
        "maxClustersAllowed": int,
        "similarityThreshold": float,
        "timestampIntervalInSeconds": int,
        "fitRate": int,
        "dateFormat": str,
        "initializationDate": str
    }
}
```

**Example:**

```python
forecaster = client.create_forecaster({
    "forecasterName": "Temperature Monitor",
    "features": ["temp", "humidity"],
    "inputSize": 30,
    "outputSize": 5
})
forecaster_id = forecaster["forecasterId"]
```

---

### list_forecasters

**Output:**

```python
[
    {
        "objectId": str,
        "objectName": str,
        "createdAt": str,
        "createdBy": str,
        "objectType": str,
        "dataProcessed": float,
        "requestsProcessed": int
    },
    ...
]
```

**Example:**

```python
forecasters = client.list_forecasters()

for f in forecasters:
    print(f"{f['objectName']} (ID: {f['objectId']})")
```

---

### get_forecaster_details

**Output:**

```python
{
    "forecasterId": str,
    "forecasterName": str,
    "features": {
        "feature_name": {
            "anomalyScore": float,
            "activeClusters": int,
            "totalCreatedClusters": int,
            "totalDeletedClusters": int,
            "totalObservations": int,
            "totalTimeSeriesProcessed": int,
            "lastAddition": str
        },
        ...
    },
    "configuration": {
        "inputSize": int,
        "outputSize": int,
        "maxClustersAllowed": int,
        "similarityThreshold": float,
        "timestampIntervalInSeconds": int,
        "fitRate": int,
        "dateFormat": str,
        "initializationDate": str
    }
}
```

**Example:**

```python
details = client.get_forecaster_details(forecaster_id)

print(f"Forecaster: {details['forecasterName']}")
print(f"Input size: {details['configuration']['inputSize']}")

for feature, stats in details["features"].items():
    print(f"{feature}: {stats['activeClusters']} active clusters")
```

---

### delete_forecaster

**Output:**

```python
{
    "message": "FORECASTER_DELETED"
}
```

---

### delete_all_forecasters

**Output:**

```python
{
    "results": [
        {
            "forecasterId": str,
            "status": int,
            "message": str
        },
        ...
    ]
}
```

---

## Data Operations

### feed_point

Input format is unchanged (feature names are user-defined, not converted):

```python
data = {
    "temp": [25.5, 26.0],
    "humidity": [65.0, 64.5]
}
client.feed_point(forecaster_id, data)
```

---

### bulk_feed_data

**Input:**

```python
{
    "payloadsList": [
        {
            "forecasterId": str,
            "data": {
                "temp": [25.5, 26.0],
                "humidity": [65.0, 64.5]
            }
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
            "forecasterId": str,
            "status": int,
            "message": str
        },
        ...
    ]
}
```

---

## Forecasting

### forecast

**Output:**

```python
{
    "anomalyScore": float,
    "numberOfClusters": int,
    "features": {
        "feature_name": {
            "timestamps": list[str],
            "predictions": list[float],
            "upperConfidence": list[float],
            "lowerConfidence": list[float],
            "anomalyScore": float,
            "forecastingMethod": str,
            "numberOfClusters": int
        },
        ...
    }
}
```

**Example:**

```python
result = client.forecast(forecaster_id)

print(f"Global anomaly score: {result['anomalyScore']:.4f}")

for feature, pred in result["features"].items():
    print(f"{feature}: next value = {pred['predictions'][0]:.4f}")
    print(f"  Method: {pred['forecastingMethod']}")
    print(f"  Confidence: [{pred['lowerConfidence'][0]:.4f}, {pred['upperConfidence'][0]:.4f}]")
```

---

## Key Differences from Default Mode

| Default (snake_case) | Native (camelCase) |
|---|---|
| `result["forecaster_id"]` | `result["forecasterId"]` |
| `result["anomaly_score"]` | `result["anomalyScore"]` |
| `result["forecasting_method"]` | `result["forecastingMethod"]` |
| `result["upper_confidence"]` | `result["upperConfidence"]` |
| `result["object_id"]` | `result["objectId"]` |
| `result["timestamp_interval_in_seconds"]` | `result["timestampIntervalInSeconds"]` |
| `"payloads_list"` | `"payloadsList"` |
| `"forecaster_name"` | `"forecasterName"` |

Error handling, method signatures, and exceptions are identical in both modes.

---

## See Also

- [API.md](API.md) - Default (snake_case) API reference
- [README.md](../README.md) - Getting started guide
- [CHANGELOG.md](../CHANGELOG.md) - Version history

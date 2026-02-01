# DriftMind Client

DriftMind is an **adaptive forecasting and anomaly detection engine** designed for **fast, real-time data environments**. Unlike traditional forecasting systems that require long offline training phases, DriftMind uses an **online training approach**: it learns continuously from incoming data streams and can start generating forecasts as soon as enough points are fed.

---

## ✨ Why DriftMind?

DriftMind is particularly well-suited for:

- 🌐 **Streaming data scenarios** such as telecom, IoT, or finance.
- ⚡ **Cold-start forecasting**: predictions available immediately without long historical training.
- 🔍 **On-the-fly anomaly detection**: dynamically compares current behaviors against learned patterns to spot unusual sequences immediately.
- 📈 **Scalable deployments** where thousands of forecasters can be created, queried, and updated in real time.

---

## 🔬 Core Concepts

At its core, DriftMind blends:

- **Online clustering** to adapt quickly to new patterns as they emerge.
- **Geometric Extension forecasting** as a fallback when no cluster is available.
- **Continuous learning** without explicit retraining steps.

## 📚 Research & Publications

DriftMind is built on novel research in adaptive signal processing and online clustering. For a deeper dive into the architecture and theoretical foundations, please refer to:

* **📄 The Paper:** [DriftMind: A Self-Adaptive, Cold-Start Framework for Time Series Forecasting and Anomaly Detection](https://www.researchgate.net/publication/398142288_DriftMind_A_Self-Adaptive_Cold-Start_Framework_for_Time_Series_Forecasting_and_Anomaly_Detection_in_Fast_Data_Streams) – *ResearchGate (Preprint), Dec 2025*
* **🧠 The Article:** [Reflexive Memory: A CPU-Only Alternative to Transformers for Streaming Forecasting](https://medium.com/towards-artificial-intelligence/reflexive-memory-a-cpu-only-alternative-to-transformers-for-streaming-forecasting-45efc12e383c) – *Towards AI, Dec 2025*

These resources detail the **single-pass clustering mechanism** and **temporal transition graphs** that allow DriftMind to outperform deep learning models (like OneNet) in real-time environments without GPUs.

## 🎯 The DriftMind Client

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The **DriftMind Client** is a lightweight Python package that encapsulates the [DriftMind API](https://api.thingbook.io/access/swagger/index.html). It makes it easy to:

- Create and manage forecasters at scale.
- Integarte DriftMind capabilities into existing Python pipelines.
- Stream time-series data point-by-point or in batches.
- Request forecasts, anomaly scores, and cluster insights at any time.
- Visualize actual vs. predicted values, anomaly scores, and cluster evolution.

## 🛠 Prerequisites

Before using the DriftMind Client, make sure you have the following:

- **Python environment**: The DriftMind Client requires Python 3.8 or higher.

- **DriftMind backend service**: The client communicates with the **DriftMind API service**. You will need either:
  - Access to a **Thingbook.io hosted DriftMind endpoint**, or
  - A **local deployment** of the DriftMind backend (Kubernetes) for on-premise environments.

  *Note: Without a running DriftMind API, the client cannot create forecasters or request forecasts.*

- **API credentials**: 
  - An **API key**: Register at <https://thingbook.io/> and choose the free Demo tier to obtain a key.
  - **Base URL**: The DriftMind API endpoint (e.g., `https://api.thingbook.io/access/api/driftmind`).

  Pass these as environment variables (or via a `.env` file): `DRIFTMIND_API_KEY` and `DRIFTMIND_API_URL`.

## 🚀 Installation

While `uv` is recommended, standard `pip` commands also work.

```bash
# Clone the repository
git clone https://github.com/thngbk/driftmind.git
cd driftmind-client

# Create and activate virtual environment
uv venv
source .venv/bin/activate

# Install package in editable mode
uv pip install -e .
```

## ⚙️ Configuration

Create a file named `.env` (e.g., in your project root or `env/` folder) to store your credentials securely.

### File Content:
```
DRIFTMIND_API_KEY=<your_api_key>
DRIFTMIND_API_URL=https://api.thingbook.io/access/api/driftmind/v1/
```

## 📖 Usage

### 1. Import and initialize the client

```python
from driftmind import DriftMindClient
from driftmind.utils import load_credentials

creds = load_credentials()
client = DriftMindClient(
    api_key=creds["DRIFTMIND_API_KEY"], 
    base_url=creds["DRIFTMIND_API_URL"]
)

```

### 2. Create a Forecaster

A **forecaster** is the core unit in DriftMind: it maintains state, learns continuously from fed data, and produces forecasts, anomaly scores, and cluster insights.

#### 🟢 Minimum configuration

At minimum, you only need to specify:

- **`forecaster_name`**: A unique, human-friendly identifier.
- **`features`**: A list of feature names (columns in your dataset).
- **`input_size`**: Number of past points used as input window.
- **`output_size`**: Number of future points to forecast.

Example:

```python
columns = ["sin", "cos", "tan"]
forecaster_payload = {
    "forecaster_name": "Cold Start Demo",
    "features": columns,
    "input_size": 15,
    "output_size": 1,
}

forecaster_info = client.create_forecaster(forecaster_payload)
forecaster_id = forecaster_info.get("forecaster_id")
```

If only these parameters are provided, DriftMind applies sensible defaults for the rest.

#### ⚙️ Extended configuration

You can fine-tune behavior by overriding the default parameters.

**Full example:**

```python
forecaster_info = client.create_forecaster({
  "forecaster_name": "Machine Health Forecaster",
  "features": ["vibration_g", "motor_temp_c", "power_kw"],
  "input_size": 30,
  "output_size": 1,
  "max_clusters_allowed": 50,
  "similarity_threshold": 0.8,
  "timestamp_interval_in_seconds": 30,
  "fit_rate": 1,
  "use_custom_date_format": True,
  "date_format": "%d-%m-%Y %H:%M",
  "use_initialization_date": True,
  "initialization_date": "01-01-2025 00:00"
})

forecaster_id = forecaster_info.get("forecaster_id")
```

#### 📋 Parameter Reference

| Parameter                       | Type   | Required | Default                            | Description                                                                     |
|---------------------------------|--------|----------|------------------------------------|---------------------------------------------------------------------------------|
| `forecaster_name`               | string | ✅ Yes   | –                                  | Human-readable name for the forecaster.                                         |
| `features`                      | list   | ✅ Yes   | –                                  | List of feature names (columns in your dataset).                                |
| `input_size`                    | int    | ✅ Yes   | –                                  | Number of past points used as input.                                            |
| `output_size`                   | int    | ✅ Yes   | –                                  | Number of future points to forecast.                                            |
| `max_clusters_allowed`          | int    | No       | 200                                | Maximum number of clusters maintained.                                          |
| `similarity_threshold`          | float  | No       | 0.8                                | Similarity threshold (0–1) for assigning points to clusters.                    |
| `timestamp_interval_in_seconds` | int    | No       | 60                                 | Expected interval between points expressed in seconds.                          |
| `fit_rate`                      | int    | No       | 1                                  | Frequency of model updates (lower = faster adaptation).                         |
| `use_custom_date_format`        | bool   | No       | False                              | Whether to parse timestamps with a custom format.                               |
| `date_format`                   | string | No       | `%d-%m-%Y %H:%M:%S`                | Python strptime/strftime format when `use_custom_date_format` is set to `True`. |
| `use_initialization_date`       | bool   | No       | False                              | Whether to align forecasts relative to a given start date.                      |
| `initialization_date`           | string | No       | System time at forecaster creation | Explicit start date. Otherwise, current time is assigned as start date.         |

With this flexibility, you can start with **minimal setup for quick prototyping**, and later move to **fine-grained configurations** for production scenarios like industrial IoT, telecom, or financial forecasting.

---

### 3. Feed data

Data must be passed as lists of floats (received by the server as `double[]`).

```python
# Single point
data_point = {
    "sin": [0.12],
    "cos": [0.34],
    "tan": [0.56]
}
client.feed_data(forecaster_id, data_point)

# Batch of points
data_batch = {
    "sin": [0.12, 0.13, 0.14],
    "cos": [0.34, 0.35, 0.36],
    "tan": [0.56, 0.57, 0.58]
}
client.feed_data(forecaster_id, data_batch)
```

Data points are processed in the order they are fed. The first point is assigned the `initialization_date`, while subsequent points are automatically assigned timestamps based on their order and the `timestamp_interval_in_seconds` parameter.

---

### 4. Forecast

One of the key characteristics of **DriftMind** is its **online training approach**. This means there is no need for an explicit training phase before requesting forecasts; the model begins learning as soon as data starts flowing in. The only requirement for generating a forecast is that a **minimum number of points** have been fed into the system. This number is simply the sum of the **input length** and the **output length**.

For example, if the forecaster is configured with an input length of 20 and an output length of 5, the system must first receive **25 points** before it can produce a valid forecast. Once this threshold is reached, DriftMind can start delivering predictions in real time while continuously updating its internal models as new data arrives.

```
Minimum required points = Input length + Output length

    |<---------------------------- Input (20 points) ------------------------->|<Output (5 points)>|
---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●
                                                                                                   ^ Forecast starts here
```


```python
# Forecaster features
columns = ["sin", "cos", "tan"]

# Request forecasting data
result = client.forecast(forecaster_id)

# Visualize results
for var in columns:
    df_var = pd.DataFrame(results["features_map"][var])
    utils.plot_actual_vs_predicted(df_var, var)
```
![Actual vs. Predicted](images/image.png)

#### 📦 Response Format

A successful forecast request returns a JSON object with both global metrics and per-feature results.

**Example response:**

```json
{
  "anomaly_score": 0.03,
  "number_of_clusters": 24,
  "features_map": {
    "tan": {
      "timestamps": ["23-09-2025 01:33:37"],
      "predictions": [-0.3633],
      "upper_confidence": [-0.1078],
      "lower_confidence": [-1.8216],
      "anomaly_score": 0,
      "forecasting_method": "Clustering",
      "number_of_clusters": 8
    },
    "cos": {
      "timestamps": ["23-09-2025 01:33:37"],
      "predictions": [1.5515],
      "upper_confidence": [1.7922],
      "lower_confidence": [1.3251],
      "anomaly_score": 0.07,
      "forecasting_method": "Clustering",
      "number_of_clusters": 8
    },
    "sin": {
      "timestamps": ["23-09-2025 01:33:37"],
      "predictions": [-0.0016],
      "upper_confidence": [0.2502],
      "lower_confidence": [-0.2372],
      "anomaly_score": 0.01,
      "forecasting_method": "Clustering",
      "number_of_clusters": 8
    }
  }
}
```

#### 🔑 Field Descriptions

* **`anomaly_score` (float)**: Global anomaly score across all features.
* **`number_of_clusters` (int)**: Total number of clusters currently maintained by the system.
* **`features_map` (object)**: Per-feature forecast results. Each feature (e.g. `sin`, `cos`, `tan`) contains:
  * **`timestamps` (list\[str])**: Timestamps of forecasted points.
  * **`predictions` (list\[float])**: Forecasted values.
  * **`upper_confidence` / `lower_confidence` (list\[float])**: Confidence interval bounds.
  * **`anomaly_score` (float)**: Anomaly score specific to this feature.
  * **`forecasting_method` (str)**: Forecasting approach used (e.g. `Clustering`, `Extension`, `Naive`).
  * **`number_of_clusters` (int)**: Number of clusters active in the system for this Forecaster. the clusters model the recent and past behaviour with minimum footprint.

#### 🔍 Example: Working with Forecasts

```python
# Access global anomaly score
print(f"Global anomaly score: {result['anomaly_score']}")

# Iterate over feature forecasts
for feature, details in result["allResults"].items():
    print(f"\nFeature: {feature}")
    print(f"Predicted: {details['predictions'][0]}")
    print(f"Confidence interval: ({details['lower_confidence'][0]}, {details['upper_confidence'][0]})")
    print(f"Feature anomaly score: {details['anomaly_score']}")
```

---

### 5. Recover forecaster data

At any time, you can inspect the **data currently held by a forecaster**. This is useful for debugging, validation, or verifying that data points are being stored correctly.

```python
data_snapshot = client.get_forecaster_data(forecaster_id)

if data_snapshot:
    for ts, values in data_snapshot["data"].items():
        print(f"{ts} → {values}")
```

Example response. Each key in the data object is a timestamp, and its value is a dictionary containing the last known values for each feature.

```json
{
  "data": {
    "23-09-2025 18:54:20": { "tan": -0.8335, "sin": -0.6755, "cos": 0.3708 },
    "23-09-2025 18:55:20": { "tan": -0.7879, "sin": -0.6472, "cos": 0 },
    "23-09-2025 18:56:20": { "tan": -0.7458, "sin": -0.6164, "cos": -0.3708 },
    "23-09-2025 18:57:20": { "tan": -0.7067, "sin": -0.5832, "cos": -0.7053 },
    "23-09-2025 18:58:20": { "tan": -0.6703, "sin": -0.5476, "cos": -0.9708 }
  }
}

```

### 6. List all forecasters

You can query the system to get a list of all available forecasters. Each entry contains metadata such as the forecaster’s ID, name, creation date, and usage stats.

```python
import json 

all_forecasters = client.list_forecasters()

print(json.dumps(all_forecasters, indent=2))
```

Example response: 

```json
[
  {
    "object_id": "a82bdf13-becf-4a06-9c97-c7b106a8fbac",
    "object_name": "Cold Start Demo",
    "created_at": "2025-09-22",
    "created_by": "VfYZ3hLQk6FohdPTkKXB0lC30DworzI5Mz0M2NTk1MDY3MjE4MDE4NDwE3MTA3OTA1NDUzMDc4Njg5NjA0Nw",
    "object_type": "FORECASTER",
    "data_processed": -0.67,
    "requests_processed": 601
  },
  {
    "object_id": "c339beb7-ae9b-4f3e-bb73-e4d4245cb507",
    "object_name": "Basic Forecaster Creation",
    "created_at": "2025-09-22",
    "created_by": "VfYZ3hLQk6FohdPTkKXB0lC30DworzI5Mz0M2NTk1MDY3MjE4MDE4NDwE3MTA3OTA1NDUzMDc4Njg5NjA0Nw",
    "object_type": "FORECASTER",
    "data_processed": -3.19,
    "requests_processed": 1202
  }
]
```

In other approach:

```python
for f in all_forecasters:
    print(f"ID={f['object_id']}, Name={f['object_name']}, Created={f['created_at']}, Requests={f['requests_processed']}")
```

The response would be:

```txt
ID=a82bdf13-becf-4a06-9c97-c7b106a8fbac, Name=Cold Start Demo, Created=2025-09-22, Requests=601
ID=c339beb7-ae9b-4f3e-bb73-e4d4245cb507, Name=Basic Forecaster Creation, Created=2025-09-22, Requests=1202
```

Each element in the list includes:

* **object_id**: Unique ID of the object.
* **object_name**: Human-readable name.
* **created_at**: Date of creation.
* **created_by**: API key used to create the object.
* **object_type**: `FORECASTER` (at the moment, forecasters are the only objects supported).
* **data_processed**: Amount of data processed (aggregate value) in MB. This value will be always negative.
* **requests_processed**: Number of requests served by the forecaster.

---

### 7. Get forecaster details

You can inspect the **configuration and properties of a specific forecaster** using its ID. This is useful for verifying feature setup, parameters, and metadata.

```python
forecaster_id = "529cd364-67b2-4f04-8c07-c42b5740b3aa"
details = client.get_forecaster_details(forecaster_id)

if details:
    print(f"Forecaster Name: {details['forecaster_name']}")
    print(f"Features: {details['features']}")
    print(f"Input Size: {details['properities']['input_size']}")
    print(f"Output Size: {details['properities']['output_size']}")
```

Example response:

```json
{
  "forecaster_id": "529cd364-67b2-4f04-8c07-c42b5740b3aa",
  "forecaster_name": "Cold Start Demo",
  "features": ["tan", "sin", "cos"],
  "properties": {
    "fit_rate": "1",
    "initialization_date": "23-09-2025 09:37:13",
    "max_clusters_allowed": "100",
    "date_format": "dd-MM-yyyy HH:mm:ss",
    "similarity_threshold": "0.8",
    "timestamp_interval_in_seconds": "60",
    "output_size": "1",
    "input_size": "15"
  }
}
```

---

### 8. Example: Cold-Start Demo

A demo notebook is included in `notebooks/cold_start_demo.ipynb` which:

* Creates a forecaster
* Generates synthetic `sin/cos/tan` data with drifts
* Feeds data point by point
* Requests forecasts in the loop
* Plots Actual vs Predicted values for all three features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📮 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/thngbk/driftmind/issues).

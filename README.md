# DriftMind Client

DriftMind is an **adaptive forecasting and anomaly detection engine** designed for **fast, real-time data environments**. Unlike traditional forecasting systems that require long offline training phases, DriftMind uses an **online training approach**: it learns continuously from incoming data streams and can start generating forecasts as soon as enough points are fed.

---

## ✨ Why DriftMind?

DriftMind is particularly well-suited for:

- 🌐 **Streaming data scenarios** such as telecom, IoT, or finance.
- ⚡ **Cold-start forecasting**: predictions available immediately without long historical training.
- 🔍 **On-the-fly anomaly detection** using dynamic clustering.
- 📈 **Scalable deployments** where thousands of forecasters can be created, queried, and updated in real time.
## 🔬 Core Concepts

At its core, DriftMind blends:

- **Online clustering** to adapt quickly to new patterns.
- **Geometric forecasting** as a fallback when no cluster is available.
- **Continuous learning** without explicit retraining steps.

## 📚 Research & Publications

DriftMind is built on novel research in adaptive signal processing and online clustering. For a deeper dive into the architecture and theoretical foundations, please refer to:

* **📄 The Paper:** [DriftMind: A Self-Adaptive, Cold-Start Framework for Time Series Forecasting and Anomaly Detection](https://www.researchgate.net/publication/398142288_DriftMind_A_Self-Adaptive_Cold-Start_Framework_for_Time_Series_Forecasting_and_Anomaly_Detection_in_Fast_Data_Streams) – *ResearchGate (Preprint), Dec 2025*
* **🧠 The Article:** [Reflexive Memory: A CPU-Only Alternative to Transformers for Streaming Forecasting](https://medium.com/towards-artificial-intelligence/reflexive-memory-a-cpu-only-alternative-to-transformers-for-streaming-forecasting-45efc12e383c) – *Towards AI, Dec 2025*

These resources detail the **single-pass clustering mechanism** and **temporal transition graphs** that allow DriftMind to outperform deep learning models (like OneNet) in real-time environments without GPUs.

---

## 🎯 The DriftMind Client

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/thngbk/driftmind/actions/workflows/test.yml/badge.svg)](https://github.com/thngbk/driftmind/actions/workflows/test.yml)
[![Test Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen.svg)](tests/TESTING.md)

The **DriftMind Client** is a lightweight Python package that encapsulates the [DriftMind API](https://api.thingbook.io/access/swagger/index.html). It makes it easy to:

- Create and manage forecasters at scale.
- Stream time-series data point-by-point or in batches.
- Request forecasts, anomaly scores, and cluster insights at any time.
- Visualize actual vs. predicted values, anomaly scores, and cluster evolution.

**Key Features:**

- 🔄 Automatic retry with exponential backoff.
- 🔒 Built-in credential protection in logs.
- ✅ Comprehensive error handling with specific exceptions.
- 📊 Pydantic v2 models with automatic validation.
- 🧪 85% test coverage with 65 tests.

---

## 🛠 Prerequisites & Installation

### 1. System Requirements
- **Python**: 3.9 or higher.
- **Windows Users**: You must have the **Visual Studio Build Tools** installed to compile dependencies like `numpy`. 
    - [Download here](https://visualstudio.microsoft.com/visual-cpp-build-tools/) and select the **"Desktop development with C++"** workload.

### 2. Backend Access
You will need:
  - An **API key**: Register at <https://thingbook.io/> and choose the free Demo tier to obtain a key.
  - **Base URL**: The DriftMind API endpoint (e.g., `https://api.thingbook.io/access/api/driftmind`).

These should be stored in a `.env` file (see [Configuration](#-configuration)).

### 3. Quick Start Installation

We recommend using [uv](https://docs.astral.sh/uv/) for the fastest and most reliable setup. It automatically handles the virtual environment and lockfile synchronization.

```bash
# Clone the repository
git clone https://github.com/thngbk/driftmind.git
cd driftmind

# Synchronize the environment (creates .venv and installs everything)
uv sync
```

**For development (editable mode with all tools):**

```bash
# For development (includes testing tools, linter, and examples):
uv sync --dev --extra examples
```

---

## ⚠️ Migration from 0.2.x (Breaking Changes)

Version **0.4.1** introduces a major change to provide a more idiomatic Python experience: **API response keys are now automatically converted from `camelCase` to `snake_case`.**

| Old Behavior (v0.2.0)         | New Behavior (v0.4.1)          |
| ----------------------------- | ------------------------------ |
| `result["anomalyScore"]`      | `result["anomaly_score"]`      |
| `result["forecastingMethod"]` | `result["forecasting_method"]` |

### How to use the Legacy Version

If your existing codebase depends on the `camelCase` keys and you are not ready to upgrade, you can install the legacy version using the `v0.2.0` tag:

```bash
# Using uv
uv pip install git+[https://github.com/thngbk/driftmind.git@v0.2.0](https://github.com/thngbk/driftmind.git@v0.2.0)

# Using pip
pip install git+[https://github.com/thngbk/driftmind.git@v0.2.0](https://github.com/thngbk/driftmind.git@v0.2.0)
```

---

## ⚙️ Configuration

Copy the example environment file and add your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```text
DRIFTMIND_API_KEY=<your_api_key>
DRIFTMIND_API_URL=[https://api.thingbook.io/access/api/driftmind](https://api.thingbook.io/access/api/driftmind)
```

---

## 🧪 Development & Testing

### 🛠️ Environment Setup

To ensure all development tools and hooks are correctly configured, run the following:

```bash
# 1. Sync the environment (installs dev tools and optional examples)
uv sync --dev --extra examples

# 2. Install the git pre-commit hooks
uv run pre-commit install
```

### 🧪 Testing

The DriftMind client includes a comprehensive test suite with **65 tests** achieving **85% code coverage**:

- **Client API tests** (30 tests) - All endpoints, success/error cases, bulk operations
- **Edge cases & logging** (10 tests) - Error handling, logging protection, session management  
- **Model validation** (9 tests) - Pydantic serialization, field validation
- **Utils & plotting** (15 tests) - Credential loading, date conversion, plotting functions

```bash
# Run all tests using uv (recommended for src layout)
uv run python -m pytest tests/

# Run with coverage report
uv run python -m pytest tests/ --cov=driftmind --cov-report=term-missing
```

See [tests/TESTING.md](tests/TESTING.md) for detailed testing documentation.

### ✨ Code Quality (Pre-commit)

This project uses [pre-commit](https://pre-commit.com/) with [ruff](https://docs.astral.sh/ruff/) to automate code quality. Hooks run automatically before each commit; if issues are found, the commit is blocked until fixed.

**Manual execution:**

```bash
# Run hooks manually on all files
uv run pre-commit run --all-files
```

**What gets checked:**

- **ruff check** (`--fix`): Lints and auto-fixes code issues
  - `E`, `W`: PEP 8 errors and warnings
  - `F`: Pyflakes (unused imports, undefined names)
  - `I`: Import sorting (isort-compatible)
  - `B`: Bugbear (common bugs and design problems)
  - `UP`: pyupgrade (modern Python syntax)
- **ruff format**: Ensures consistent code formatting (Black-compatible)

### 🚀 Continuous Integration (CI)

All pushes and pull requests are automatically tested via **GitHub Actions** on both **Windows and Ubuntu** to ensure cross-platform compatibility and maintain code integrity.

---

## 📖 Usage

> **📘 For complete API reference with detailed input/output formats, see [docs/API.md](docs/API.md)**

All API responses are automatically validated using Pydantic v2 models, ensuring type safety and data integrity. You work with standard Python dictionaries—validation happens transparently in the background.

### 1. Import and Initialize

The client handles authentication and session management automatically. Use the context manager for automatic resource cleanup.

```python
from driftmind import DriftMindClient
from driftmind.utils import load_credentials

creds = load_credentials()

# Recommended: Use context manager for automatic resource cleanup
with DriftMindClient(
    api_key=creds["DRIFTMIND_API_KEY"], 
    base_url=creds["DRIFTMIND_API_URL"]
) as client:
    # Verify connectivity (optional)
    if client.health_check():
        print("✓ Connected to DriftMind API")
    
    # Your code here
    pass

# Alternative: Manual cleanup
client = DriftMindClient(
    api_key=creds["DRIFTMIND_API_KEY"], 
    base_url=creds["DRIFTMIND_API_URL"]
)
try:
    # Your code here
    pass
finally:
    client.close()
```

#### Advanced Configuration

Customize client behavior with additional parameters:

```python
from driftmind import DriftMindClient

with DriftMindClient(
    api_key=creds["DRIFTMIND_API_KEY"],
    base_url=creds["DRIFTMIND_API_URL"],
    timeout=15.0,
    max_retries=5,
    retry_delay=2.0,
    enable_logging_protection=True
) as client:
    pass
```

**Configuration Parameters:**

| Parameter                   | Type    | Required | Default | Description                                                                  |
|-----------------------------|---------|----------|---------|------------------------------------------------------------------------------|
| `api_key`                   | str     | ✅ Yes    | –       | API authentication key                                                       |
| `base_url`                  | str     | ✅ Yes    | –       | DriftMind API endpoint URL                                                   |
| `session`                   | Session | No       | None    | Custom requests.Session (for advanced use)                                   |
| `timeout`                   | float   | No       | 10.0    | Request timeout in seconds                                                   |
| `max_retries`               | int     | No       | 3       | Maximum retry attempts for 5xx errors, 429 rate limits, and network failures |
| `retry_delay`               | float   | No       | 1.0     | Initial delay between retries (exponential backoff: 1s, 2s, 4s, ...)         |
| `enable_logging_protection` | bool    | No       | True    | Automatically redact API keys from debug logs                                |
| `pool_connections`          | int     | No       | 10      | Number of connection pools to cache per host                                 |
| `pool_maxsize`              | int     | No       | 10      | Maximum number of connections to save in the pool                            |

---

### 2. Create a Forecaster

> **📘 See [docs/API.md#create_forecaster](docs/API.md#create_forecaster) for complete parameter reference**

A **forecaster** is the core unit in DriftMind: it maintains state, learns continuously from fed data, and produces forecasts, anomaly scores, and cluster insights.

#### 🟢 Minimum configuration

At minimum, you only need to specify:

- **`forecaster_name`**: A unique, human-friendly identifier.
- **`features`**: A list of feature names (columns in your dataset).
- **`input_size`**: Number of past points used as input window.
- **`output_size`**: Number of future points to forecast.

Example:

```python
with DriftMindClient(
    api_key=creds["DRIFTMIND_API_KEY"], 
    base_url=creds["DRIFTMIND_API_URL"]
) as client:
    forecaster_payload = {
        "forecaster_name": "Cold Start Demo",
        "features": ["sin", "cos", "tan"],
        "input_size": 15,
        "output_size": 1,
    }

    forecaster_info = client.create_forecaster(forecaster_payload)
    forecaster_id = forecaster_info["forecaster_id"]
```

If only these parameters are provided, DriftMind applies sensible defaults for the rest.

#### ⚙️ Extended configuration

Fine-tune the online learning engine using `ForecasterSettingsBase` parameters.

**Full example:**

```python
with DriftMindClient(
    api_key=creds["DRIFTMIND_API_KEY"], 
    base_url=creds["DRIFTMIND_API_URL"]
) as client:
    forecaster_info = client.create_forecaster({
        "forecaster_name": "Industrial Sensor Model",
        "features": ["vibration", "temp"],
        "input_size": 60,
        "output_size": 5,
        "max_clusters_allowed": 100,
        "similarity_threshold": 0.85,
        "timestamp_interval_in_seconds": 60,
        "use_custom_date_format": True,
        "date_format": "%d-%m-%Y %H:%M",  # Uses Python format; client converts to Java for API
        "use_initialization_date": True,
        "initialization_date": "2026-01-16 08:00:00"
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

### 3. Feed Data

> **📘 See [docs/API.md#feed_point](docs/API.md#feed_point) for detailed examples and bulk operations**

Feeding data trains the forecaster using **online learning**—the model updates continuously as new data arrives, with no separate training phase needed.

Data must be in **columnar format**: a dictionary where keys are feature names and values are lists of numeric observations.

```python
with DriftMindClient(
    api_key=creds["DRIFTMIND_API_KEY"], 
    base_url=creds["DRIFTMIND_API_URL"]
) as client:
    # Feed single or multiple points
    data = {
        "sin": [0.12, 0.24, 0.36],
        "cos": [0.34, 0.45, 0.56]
    }
    client.feed_point(forecaster_id, data)
```

**Bulk feeding multiple forecasters:**

```python
with DriftMindClient(
    api_key=creds["DRIFTMIND_API_KEY"], 
    base_url=creds["DRIFTMIND_API_URL"]
) as client:
    payloads = [
        {
            "forecaster_id": forecaster_id_1,
            "data": {
                "motor_temp_c": [18.0, 19.5, 20.1, 20.7],
                "power_kw": [0.62, 0.60, 0.58, 0.59],
                "vibration_g": [1012.2, 1012.5, 1012.1, 1011.9]
            }
        },
        {
            "forecaster_id": forecaster_id_2,
            "data": {
                "temperature": [22.5, 23.1, 23.8],
                "humidity": [0.65, 0.63, 0.61]
            }
        }
    ]
    
    result = client.bulk_feed_data(payloads)
    print(f"Status: {result['message']}")
```

**Timestamp assignment:**

- First point → `initialization_date`
- Subsequent points → auto-incremented by `timestamp_interval_in_seconds`
- Example: `initialization_date="2025-01-01 00:00"`, `interval=60` → timestamps: 00:00, 00:01, 00:02...

---

### 4. Inspect Forecaster Data

> **📘 See [docs/API.md#get_forecaster_data](docs/API.md#get_forecaster_data) for details**

Retrieve the historical observations currently stored in the forecaster's memory.

```python
with DriftMindClient(
    api_key=creds["DRIFTMIND_API_KEY"], 
    base_url=creds["DRIFTMIND_API_URL"]
) as client:
    history = client.get_forecaster_data(forecaster_id)

    for timestamp, features in history.items():
        print(f"Time: {timestamp} | Data: {features}")
```

---

### 5. Get Predictions

> **📘 See [docs/API.md#forecast](docs/API.md#forecast) for complete output format and examples**

Once enough data is fed, you can request forecasts. The minimum required is:

**Minimum Points = input_size + output_size**

For example, with `input_size=20` and `output_size=5`, you need 25 points before forecasting is available.

```
    |<---------------------------- Input (20 points) ------------------------->|<Output (5 points)>|
---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●---●
                                                                                                   ^ Forecast starts here
```

```python
with DriftMindClient(
    api_key=creds["DRIFTMIND_API_KEY"], 
    base_url=creds["DRIFTMIND_API_URL"]
) as client:
    result = client.forecast(forecaster_id)

    print(f"Global Anomaly Score: {result['anomaly_score']}")

    for feature_name, pred in result["features"].items():
        print(f"--- {feature_name} ---")
        print(f"Method: {pred['forecasting_method']}")
        print(f"Next Value: {pred['predictions'][0]}")
        print(f"Confidence: [{pred['lower_confidence'][0]}, {pred['upper_confidence'][0]}]")
```

---

### 6. Management & Monitoring

> **📘 See [docs/API.md#forecaster-management](docs/API.md#forecaster-management) for complete management operations**

#### List All Objects

Get a high-level overview of all tracked objects.

```python
with DriftMindClient(
    api_key=creds["DRIFTMIND_API_KEY"], 
    base_url=creds["DRIFTMIND_API_URL"]
) as client:
    forecasters = client.list_forecasters()
    for f in forecasters:
        print(f"{f['object_name']} (ID: {f['object_id']}) - Processed: {f['data_processed']} MB")
```

#### Get Detailed Stats

Retrieve configuration and live feature statistics (like cluster counts and anomaly scores).

```python
with DriftMindClient(
    api_key=creds["DRIFTMIND_API_KEY"], 
    base_url=creds["DRIFTMIND_API_URL"]
) as client:
    details = client.get_forecaster_details(forecaster_id)

    # Configuration is under the 'configuration' key
    print(f"Input Size: {details['configuration']['input_size']}")

    # Per-feature stats
    for name, stats in details["features"].items():
        print(f"Feature {name} has {stats['active_clusters']} active clusters.")
```

---

### 7. Clean Up

> **📘 See [docs/API.md#delete_forecaster](docs/API.md#delete_forecaster) and [docs/API.md#delete_all_forecasters](docs/API.md#delete_all_forecasters) for details**

Delete a specific forecaster or perform a bulk wipe.

```python
with DriftMindClient(
    api_key=creds["DRIFTMIND_API_KEY"], 
    base_url=creds["DRIFTMIND_API_URL"]
) as client:
    # Delete one
    client.delete_forecaster(forecaster_id)

    # Delete all (Bulk Operation)
    # Note: Deletes sequentially as API doesn't provide bulk deletion
    results = client.delete_all_forecasters()
    
    # Check results
    for result in results["results"]:
        if result["status"] == 200:
            print(f"✓ Deleted {result['forecaster_id']}")
        else:
            print(f"✗ Failed to delete {result['forecaster_id']}: {result['message']}")
```

---

### 8. Example: Complete Quickstart

Two complete examples are available:

**1. Python Script** ([`examples/quickstart.py`](examples/quickstart.py)) - Complete runnable example:

```python
import math
from driftmind import DriftMindClient
from driftmind.exceptions import DriftMindError
from driftmind.utils import load_credentials

creds = load_credentials()

with DriftMindClient(
    api_key=creds["DRIFTMIND_API_KEY"],
    base_url=creds["DRIFTMIND_API_URL"]
) as client:
    # Verify connectivity
    if client.health_check():
        print("✓ Connected to DriftMind API")
    
    # Create forecaster
    forecaster_info = client.create_forecaster({
        "forecaster_name": "Quickstart Demo",
        "features": ["sin", "cos"],
        "input_size": 10,
        "output_size": 3,
    })
    forecaster_id = forecaster_info["forecaster_id"]
    
    # Feed data (minimum: input_size + output_size = 13 points)
    for i in range(18):
        angle = i * 0.1
        data = {
            "sin": [math.sin(angle)],
            "cos": [math.cos(angle)]
        }
        client.feed_point(forecaster_id, data)
    
    # Get predictions
    result = client.forecast(forecaster_id)
    print(f"Anomaly Score: {result['anomaly_score']:.4f}")
    
    for feature_name, pred in result["features"].items():
        print(f"{feature_name}: {pred['predictions'][:3]}")
    
    # Inspect stored data
    history = client.get_forecaster_data(forecaster_id)
    print(f"Stored {len(history)} data points")
    
    # Clean up
    client.delete_forecaster(forecaster_id)
```

Run it with: `uv run python examples/quickstart.py`

**2. Jupyter Notebook** ([`examples/cold_start_demo.ipynb`](examples/cold_start_demo.ipynb)) - Interactive demo with:

- Synthetic data generation with drifts
- Online learning loop (600 iterations)
- Visualization of actual vs predicted values
- Anomaly score and cluster evolution plots

To run the notebook, install JupyterLab:
```bash
uv pip install -e ".[examples]"
jupyter lab examples/cold_start_demo.ipynb
```

---

## ⚠️ Common Errors

> **📘 For complete error handling guide, see [docs/API.md#error-handling**](https://www.google.com/search?q=docs/API.md%23error-handling)

### 🪟 Windows: C++ Build Tools Missing

If you see an error like `error: Microsoft Visual C++ 14.0 or greater is required` during installation, it means the `numpy` build failed because your system lacks a C++ compiler.

**The Fix:**

1. Download the [Visual Studio Build Tools](https://www.google.com/search?q=https://visualstudio.microsoft.com/visual-cpp-build-tools/).
2. Run the installer and select **"Desktop development with C++"**.
3. Restart your terminal and run `uv sync` again.

### 🔍 Verifying API Connectivity

Before performing complex operations, use `health_check()` to verify connectivity and credentials:

```python
with DriftMindClient(
    api_key=creds["DRIFTMIND_API_KEY"],
    base_url=creds["DRIFTMIND_API_URL"]
) as client:
    try:
        if client.health_check():
            print("✓ API is accessible")
    except DriftMindApiError as e:
        if e.status_code == 401:
            print("❌ Invalid API credentials")
        else:
            print(f"❌ API error: {e.message}")
    except DriftMindError as e:
        print(f"❌ Network error: {e}")
```

### 🆔 Empty or Invalid forecaster_id

The client validates `forecaster_id` locally to save unnecessary API calls. It must not be empty or whitespace.

```python
# ❌ These will raise DriftMindError
client.forecast("")           # Empty string
client.forecast("   ")        # Whitespace only

# ✅ Valid usage
forecaster_id = forecaster_info.get("forecaster_id")
client.forecast(forecaster_id)
```

**Error message:**

```text
DriftMindError: forecaster_id cannot be empty or whitespace
```

---

## 📚 Documentation

- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes
- **[docs/API.md](docs/API.md)** - Complete API reference with input/output formats
- **[examples/quickstart.py](examples/quickstart.py)** - Runnable Python example
- **[examples/cold_start_demo.ipynb](examples/cold_start_demo.ipynb)** - Interactive Jupyter notebook
- **[tests/TESTING.md](tests/TESTING.md)** - Testing documentation

---

## ⚡ Async Support

The client currently uses synchronous I/O with the `requests` library. For most forecasting workloads, this is sufficient and keeps the implementation simple and reliable.

If you need async support for high-concurrency scenarios (e.g., managing 1000+ forecasters concurrently), please open an issue to discuss your requirements. We can consider adding an `AsyncDriftMindClient` based on `httpx` if there's sufficient demand.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📮 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/thngbk/driftmind/issues).

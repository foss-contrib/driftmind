"""Constants for the DriftMind client."""

import platform
import sys
from importlib.metadata import PackageNotFoundError, version

# Version - read from package metadata
try:
    VERSION = version("driftmind")
except PackageNotFoundError:
    # Fallback for development/editable installs
    VERSION = "0.5.0"

# User Agent
PYTHON_VERSION = (
    f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
)
USER_AGENT = f"DriftMind-Python/{VERSION} Python/{PYTHON_VERSION} {platform.system()}/{platform.release()}"

# API Endpoints
FORECASTERS_PATH = "/forecasters"
FORECASTERS_OBSERVATIONS_PATH = f"{FORECASTERS_PATH}/observations"
FORECASTER_PATH = f"{FORECASTERS_PATH}/{{forecaster_id}}"
FORECASTER_PREDICTIONS_PATH = f"{FORECASTERS_PATH}/{{forecaster_id}}/predictions"
FORECASTER_OBSERVATIONS_PATH = f"{FORECASTERS_PATH}/{{forecaster_id}}/observations"

# Timeout Configuration (seconds)
DEFAULT_TIMEOUT = 10.0
BULK_OPERATION_TIMEOUT = 30.0

# Retry Configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0

# Connection Pool Configuration
DEFAULT_POOL_CONNECTIONS = 10
DEFAULT_POOL_MAXSIZE = 10

# HTTP Status Codes
HTTP_OK = 200
HTTP_PARTIAL_CONTENT = 206
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_EXPECTATION_FAILED = 417
HTTP_TOO_MANY_REQUESTS = 429
HTTP_SERVER_ERROR = 500

# Logging
SENSITIVE_HEADERS = {"auth", "authorization", "api-key", "x-api-key"}

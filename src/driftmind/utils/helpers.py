from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Sequence

import matplotlib.pyplot as plt

from .exceptions import DriftMindConfigError

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


def load_credentials(
    *,
    use_dotenv: bool = True,
    dotenv_path: Path | None = None,
) -> dict[str, str]:
    """Load DriftMind API credentials from env/.env.

    Args:
        use_dotenv: Whether to attempt loading variables from a ``.env`` file.
        dotenv_path: Optional explicit path to the ``.env`` file.

    Returns:
        A dict with ``DRIFTMIND_API_KEY`` and ``DRIFTMIND_API_URL``.

    Raises:
        DriftMindConfigError: If required variables are missing, or dotenv
            is requested but unavailable.
    """
    if use_dotenv:
        if load_dotenv is None:
            raise DriftMindConfigError(
                "python-dotenv is not installed but use_dotenv=True. "
                "Install it with `pip install python-dotenv` or set "
                "DRIFTMIND_API_KEY and DRIFTMIND_API_URL in the environment."
            )

        if dotenv_path is not None:
            load_dotenv(dotenv_path)
        else:
            load_dotenv()

    api_key = os.getenv("DRIFTMIND_API_KEY")
    base_url = os.getenv("DRIFTMIND_API_URL")

    if not api_key or not base_url:
        raise DriftMindConfigError(
            "Missing DRIFTMIND_API_KEY or DRIFTMIND_API_URL environment variables. "
            "Set them in your environment or in a .env file."
        )

    return {
        "DRIFTMIND_API_KEY": api_key,
        "DRIFTMIND_API_URL": base_url,
    }


def plot_actual_vs_predicted(
    df,
    variable_name: str,
    *,
    timestamp_col: str = "timestamp",
    actual_col: str = "expected",
    predicted_col: str = "predicted",
) -> None:
    """Plot actual vs. predicted values over time.

    Args:
        df: A pandas DataFrame containing timestamp, actual, and predicted
            columns.
        variable_name: Label used in the plot title.
        timestamp_col: Name of the timestamp column in ``df``.
        actual_col: Name of the column containing actual values.
        predicted_col: Name of the column containing predicted values.

    Returns:
        None. The function creates and shows a matplotlib figure.

    Raises:
        KeyError: If any of the required columns are missing from ``df``.

    """
    if df.empty:
        # No-op on empty data; not considered an error.
        return

    for col in (timestamp_col, actual_col, predicted_col):
        if col not in df.columns:
            raise KeyError(f"Required column '{col}' not found in DataFrame.")

    plt.figure(figsize=(15, 4))
    plt.plot(df[timestamp_col], df[actual_col], label="Actual", linewidth=2)
    plt.plot(
        df[timestamp_col],
        df[predicted_col],
        label="Predicted",
        linestyle="--",
    )
    plt.title(f"{variable_name}: Actual vs Predicted")
    plt.xlabel("Time")
    plt.ylabel("Value")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_time_series(
    timestamps: Sequence[Any],
    values: Sequence[float],
    title: str,
    xlabel: str,
    ylabel: str,
) -> None:
    """Plot a simple time series.

    Args:
        timestamps: Sequence of timestamp-like values for the x-axis.
        values: Sequence of numeric values for the y-axis.
        title: Plot title.
        xlabel: X-axis label.
        ylabel: Y-axis label.

    Returns:
        None. The function creates and shows a matplotlib figure.

    """
    if not timestamps or not values:
        return

    plt.figure(figsize=(15, 3))
    plt.plot(timestamps, values, color="red", linewidth=2)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def to_snake(string: str) -> str:
    """Convert camelCase or PascalCase to snake_case."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", string).lower()


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def python_to_java_date_format(python_format: str) -> str:
    """
    Converts a Python strftime format string to a Java/Unicode LDML format string.
    Example: '%d-%m-%Y %H:%M' -> 'dd-MM-yyyy HH:mm'
    """
    mapping = {
        "%d": "dd",
        "%m": "MM",
        "%Y": "yyyy",
        "%y": "yy",
        "%H": "HH",
        "%M": "mm",
        "%S": "ss",
    }

    # Create a regex pattern from the mapping keys
    pattern = re.compile("|".join(re.escape(k) for k in mapping.keys()))

    # Replace each match using the dictionary
    return pattern.sub(lambda m: mapping[m.group(0)], python_format)


def is_java_date_format(format_str: str) -> bool:
    """
    Returns True if the string looks like a Java/LDML date format.
    Returns False if it contains Python tokens or no recognizable tokens.
    """
    # 1. If it contains '%', it is definitely a Python/C format
    if "%" in format_str:
        return False

    # 2. Look for common Java/Unicode tokens: y, M, d, H, m, s
    # We use a regex that looks for these letters while ignoring
    # text wrapped in single quotes (which Java uses for escaping)
    java_token_pattern = re.compile(r"[yMdhHmsS]")

    return bool(java_token_pattern.search(format_str))


def java_to_python_date_format(java_format: str) -> str:
    """
    Converts a Java/Unicode LDML date format string to a Python strftime string.
    Example: 'dd-MM-yyyy HH:mm' -> '%d-%m-%Y %H:%M'
    """
    # Reverse mapping
    mapping = {
        "yyyy": "%Y",
        "yy": "%y",
        "MM": "%m",
        "dd": "%d",
        "HH": "%H",
        "mm": "%M",
        "ss": "%S",
    }

    # Sort keys by length descending (match 'yyyy' before 'yy')
    pattern = re.compile(
        "|".join(re.escape(k) for k in sorted(mapping.keys(), key=len, reverse=True))
    )

    # Remove Java's single quotes used for escaping text (e.g., 'T' -> T)
    clean_format = java_format.replace("'", "")

    return pattern.sub(lambda m: mapping[m.group(0)], clean_format)

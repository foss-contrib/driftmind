from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from dateutil import parser as date_parser

from ..exceptions import DriftMindConfigError

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


def smart_parse_date(v: any) -> any:
    """Parses ambiguous date strings using dateutil, favoring Day-First."""
    if isinstance(v, str):
        try:
            # dayfirst=True handles the dd-mm-yyyy format correctly
            return date_parser.parse(v, dayfirst=True)
        except (ValueError, OverflowError):
            return v
    return v


def convert_strftime_to_java(fmt: str) -> str:
    """
    Maps common Python strftime tokens to Java SimpleDateFormat tokens.
    """
    mapping = {
        "%d": "dd",
        "%m": "MM",
        "%Y": "yyyy",
        "%y": "yy",
        "%H": "HH",
        "%M": "mm",
        "%S": "ss",
        "%f": "SSS",  # Python microseconds to Java milliseconds (approx)
        "%z": "Z",
    }
    for py_token, java_token in mapping.items():
        fmt = fmt.replace(py_token, java_token)
    return fmt


def convert_java_to_strftime(fmt: str) -> str:
    """
    Maps Java SimpleDateFormat tokens back to Python strftime tokens.
    """
    # Note: Order matters here (yyyy before yy) to avoid partial replacement issues
    mapping = {
        "yyyy": "%Y",
        "yy": "%y",
        "MM": "%m",
        "dd": "%d",
        "HH": "%H",
        "mm": "%M",
        "ss": "%S",
        "SSS": "%f",
        "Z": "%z",
    }
    for java_token, py_token in mapping.items():
        fmt = fmt.replace(java_token, py_token)
    return fmt

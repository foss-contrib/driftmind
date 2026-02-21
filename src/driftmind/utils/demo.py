from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Final

_INSTALL_HINT = "Install with: pip install driftmind[examples]"


def generate_sin_cos_tan_with_drifts(
    n: int = 600,
    noise_std: float = 0.0,
    seed: int = 42,
):
    """Generate a synthetic time series with piecewise sinusoidal drifts.

    The sequence is split into three segments, each with different
    amplitudes and frequencies for sine, cosine, and tangent components.
    Optional Gaussian noise can be added to each component.

    Args:
        n: Number of time steps to generate. Must be a positive integer.
        noise_std: Standard deviation of additive Gaussian noise applied
            independently to each component. Must be non-negative.
        seed: Seed for the NumPy random number generator.

    Returns:
        A pandas DataFrame with columns:
        - ``sequence``: Integer time index from 0 to n-1.
        - ``sin``: Sine component with drifts.
        - ``cos``: Cosine component with drifts.
        - ``tan``: Clipped tangent component with drifts.

    Raises:
        ValueError: If ``n`` is not positive or ``noise_std`` is negative.
        ImportError: If numpy or pandas are not installed.

    """
    try:
        import numpy as np
    except ImportError as exc:
        raise ImportError(f"numpy is required. {_INSTALL_HINT}") from exc

    try:
        import pandas as pd
    except ImportError as exc:
        raise ImportError(f"pandas is required. {_INSTALL_HINT}") from exc

    if n <= 0:
        raise ValueError(f"n must be positive, got {n}.")
    if noise_std < 0:
        raise ValueError(f"noise_std must be non-negative, got {noise_std}.")

    rng = np.random.default_rng(seed)
    t = np.arange(n)

    first_break: Final[int] = n // 3
    second_break: Final[int] = 2 * n // 3

    # Create segment masks
    mask_0 = t < first_break
    mask_1 = (t >= first_break) & (t < second_break)
    mask_2 = t >= second_break

    # Initialize arrays
    sin_vals = np.zeros(n)
    cos_vals = np.zeros(n)
    tan_vals = np.zeros(n)

    # Segment parameters
    segments: list[dict[str, float]] = [
        {
            "sin_amp": 1.0,
            "sin_freq": 0.020,
            "cos_amp": 0.6,
            "cos_freq": 0.030,
            "tan_amp": 0.2,
            "tan_freq": 0.006,
        },
        {
            "sin_amp": 1.8,
            "sin_freq": 0.045,
            "cos_amp": 0.3,
            "cos_freq": 0.015,
            "tan_amp": 0.35,
            "tan_freq": 0.012,
        },
        {
            "sin_amp": 0.8,
            "sin_freq": 0.010,
            "cos_amp": 1.2,
            "cos_freq": 0.050,
            "tan_amp": 0.5,
            "tan_freq": 0.004,
        },
    ]

    # Apply segment-specific computations using vectorization
    for _idx, (mask, cfg) in enumerate(
        [(mask_0, segments[0]), (mask_1, segments[1]), (mask_2, segments[2])]
    ):
        t_seg = t[mask]

        sin_vals[mask] = cfg["sin_amp"] * np.sin(2 * np.pi * cfg["sin_freq"] * t_seg)
        cos_vals[mask] = cfg["cos_amp"] * np.cos(2 * np.pi * cfg["cos_freq"] * t_seg)

        tan_arg = 2 * np.pi * cfg["tan_freq"] * t_seg
        tan_vals[mask] = np.clip(cfg["tan_amp"] * np.tan(tan_arg), -3.0, 3.0)

    # Add noise if specified
    if noise_std > 0.0:
        noise = rng.normal(0.0, noise_std, (n, 3))
        sin_vals += noise[:, 0]
        cos_vals += noise[:, 1]
        tan_vals += noise[:, 2]

    df = pd.DataFrame(
        {
            "sequence": t,
            "sin": sin_vals,
            "cos": cos_vals,
            "tan": tan_vals,
        }
    )
    return df


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
        ImportError: If matplotlib is not installed.

    """
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(f"matplotlib is required. {_INSTALL_HINT}") from exc

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

    Raises:
        ImportError: If matplotlib is not installed.

    """
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise ImportError(f"matplotlib is required. {_INSTALL_HINT}") from exc

    if len(timestamps) == 0 or len(values) == 0:
        return

    plt.figure(figsize=(15, 3))
    plt.plot(timestamps, values, color="red", linewidth=2)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.tight_layout()
    plt.show()

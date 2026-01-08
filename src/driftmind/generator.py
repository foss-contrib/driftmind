from __future__ import annotations

from typing import Final

import numpy as np
import pandas as pd


def generate_sin_cos_tan_with_drifts(
    n: int = 600,
    noise_std: float = 0.0,
    seed: int = 42,
) -> pd.DataFrame:
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

    """
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}.")
    if noise_std < 0:
        raise ValueError(f"noise_std must be non-negative, got {noise_std}.")

    rng = np.random.default_rng(seed)
    t = np.arange(n)

    first_break: Final[int] = n // 3
    second_break: Final[int] = 2 * n // 3

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

    def segment_index(idx: int) -> int:
        if idx < first_break:
            return 0
        if idx < second_break:
            return 1
        return 2

    sin_vals: list[float] = []
    cos_vals: list[float] = []
    tan_vals: list[float] = []

    for i in range(n):
        cfg = segments[segment_index(i)]

        sin_val = cfg["sin_amp"] * np.sin(2 * np.pi * cfg["sin_freq"] * i)
        cos_val = cfg["cos_amp"] * np.cos(2 * np.pi * cfg["cos_freq"] * i)

        tan_arg = 2 * np.pi * cfg["tan_freq"] * i
        tan_raw = cfg["tan_amp"] * np.tan(tan_arg)
        tan_val = float(np.clip(tan_raw, -3.0, 3.0))

        if noise_std > 0.0:
            sin_val += float(rng.normal(0.0, noise_std))
            cos_val += float(rng.normal(0.0, noise_std))
            tan_val += float(rng.normal(0.0, noise_std))

        sin_vals.append(float(sin_val))
        cos_vals.append(float(cos_val))
        tan_vals.append(float(tan_val))

    df = pd.DataFrame(
        {
            "sequence": t,
            "sin": sin_vals,
            "cos": cos_vals,
            "tan": tan_vals,
        }
    )
    return df

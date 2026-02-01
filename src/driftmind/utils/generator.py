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
        sin_vals += rng.normal(0.0, noise_std, n)
        cos_vals += rng.normal(0.0, noise_std, n)
        tan_vals += rng.normal(0.0, noise_std, n)

    df = pd.DataFrame(
        {
            "sequence": t,
            "sin": sin_vals,
            "cos": cos_vals,
            "tan": tan_vals,
        }
    )
    return df

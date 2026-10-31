"""Performance metrics (paper §IV; definitions approved under Q14/Q15).

* positioning error, 3D (primary, Q14)  delta = ||p - p'||, metres
* positioning error, 2D (Eq. 17 literal) delta = sqrt((x-x')^2 + (y-y')^2), metres, stored for transparency
* normalised positioning error (Q15)    mean(delta) / R
* per-node relative error (Q15)         delta / R          (Fig. 9b analogue)
"positioning accuracy (%)" is NOT computed: the paper gives no definition (Q15).
"""

from __future__ import annotations

import numpy as np


def error_3d(estimates: np.ndarray, truth: np.ndarray) -> np.ndarray:
    return np.linalg.norm(np.asarray(estimates) - np.asarray(truth), axis=-1)


def error_2d_eq17(estimates: np.ndarray, truth: np.ndarray) -> np.ndarray:
    """Eq. (17) exactly as printed (x and y only)."""
    diff = np.asarray(estimates)[..., :2] - np.asarray(truth)[..., :2]
    return np.linalg.norm(diff, axis=-1)


def relative_error(errors: np.ndarray, comm_radius: float) -> np.ndarray:
    return np.asarray(errors) / comm_radius


def normalized_error(errors: np.ndarray, comm_radius: float) -> float:
    errors = np.asarray(errors)
    if errors.size == 0:
        return float("nan")
    return float(errors.mean() / comm_radius)


def mean_ci95(values: np.ndarray) -> tuple[float, float, float]:
    """Mean, sample std and 95 % CI half-width (normal approximation) ignoring NaN."""
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return float("nan"), float("nan"), float("nan")
    std = float(values.std(ddof=1)) if values.size > 1 else 0.0
    return float(values.mean()), std, 1.96 * std / np.sqrt(values.size)

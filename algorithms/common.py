"""Calculations shared by traditional DV-HOP and HCMCDV-HOP.

* Eq. (3)      - 3D average hop distance (AHD) of each anchor          (§III-A, p.85528)
* nearest AN   - hop distance a UN adopts (Eq. 2 text, p.85527; Q6)
* Eqs. (5)-(6) - linearised multilateration the paper calls "MLE"      (p.85528)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from config import MIN_ANCHORS_MLE


@dataclass
class LocalizationResult:
    """Output of one algorithm on one network. Arrays are indexed like ``network.unknown_idx``."""

    name: str
    estimates: np.ndarray  # (n_u, 3), NaN where not localised
    localized: np.ndarray  # (n_u,) bool
    hops: np.ndarray  # (n_a, n) hop counts anchor -> node
    hopsize: np.ndarray  # (n_a,) AHD per anchor, m/hop
    est_dist: np.ndarray  # (n_u, n_a) estimated UN -> AN distances, NaN if unused
    diagnostics: dict = field(default_factory=dict)
    runtime_s: float = float("nan")


def anchor_hopsize_eq3(anchor_positions: np.ndarray, anchor_hops: np.ndarray) -> np.ndarray:
    """Eq. (3): Hopsize'_i = sum_j ||a_i - a_j|| / sum_j h_ij over anchors j != i reachable from i.

    anchor_hops : (n_a, n_a) hop counts between anchors (np.inf = unreachable).
    Returns (n_a,) m/hop; NaN for an anchor that reaches no other anchor.
    """
    n_a = anchor_positions.shape[0]
    dist = np.linalg.norm(anchor_positions[:, None, :] - anchor_positions[None, :, :], axis=2)
    usable = np.isfinite(anchor_hops) & ~np.eye(n_a, dtype=bool)
    sum_dist = np.where(usable, dist, 0.0).sum(axis=1)
    sum_hops = np.where(usable, anchor_hops, 0.0).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        hopsize = sum_dist / sum_hops
    hopsize[~usable.any(axis=1)] = np.nan
    return hopsize


def nearest_anchor(hops_to_unknowns: np.ndarray) -> np.ndarray:
    """Index of the anchor with the fewest hops to each UN (ties -> lowest index, Q6).

    hops_to_unknowns : (n_a, n_u). Returns (n_u,) int, -1 if no anchor is reachable.
    """
    nearest = np.argmin(hops_to_unknowns, axis=0)  # argmin returns the first (lowest) index
    unreachable = ~np.isfinite(hops_to_unknowns).any(axis=0)
    nearest[unreachable] = -1
    return nearest


def mle_position(anchor_positions: np.ndarray, distances: np.ndarray) -> np.ndarray | None:
    """Eqs. (5)-(6): X = (A^T A)^-1 A^T b with the last anchor as reference.

    Returns the (3,) estimate, or None when fewer than 4 anchors are given or A^T A is
    singular (Q11: the node is then not localised; the paper names this MLE weakness).
    """
    anchor_positions = np.asarray(anchor_positions, dtype=float)
    distances = np.asarray(distances, dtype=float)
    if anchor_positions.shape[0] < MIN_ANCHORS_MLE:
        return None
    ref, ref_d = anchor_positions[-1], distances[-1]
    others, others_d = anchor_positions[:-1], distances[:-1]
    # Row k of A: 2(x_k - x_n), 2(y_k - y_n), 2(z_k - z_n)
    a_matrix = 2.0 * (others - ref)
    # Row k of b: x_k^2 - x_n^2 + y_k^2 - y_n^2 + z_k^2 - z_n^2 + d_n^2 - d_k^2
    b_vector = np.sum(others**2, axis=1) - np.sum(ref**2) + ref_d**2 - others_d**2
    if np.linalg.matrix_rank(a_matrix) < 3:
        return None  # A^T A not invertible
    ata = a_matrix.T @ a_matrix
    try:
        return np.linalg.solve(ata, a_matrix.T @ b_vector)
    except np.linalg.LinAlgError:
        return None


def mle_localize_all(
    anchor_positions: np.ndarray, est_dist: np.ndarray
) -> tuple[np.ndarray, np.ndarray, int]:
    """Apply Eqs. (5)-(6) to every UN using its anchors with finite estimated distance.

    Returns estimates (n_u, 3), localized mask (n_u,), number of singular-matrix failures.
    """
    n_u = est_dist.shape[0]
    estimates = np.full((n_u, 3), np.nan)
    localized = np.zeros(n_u, dtype=bool)
    singular = 0
    for u in range(n_u):
        used = np.isfinite(est_dist[u])
        if used.sum() < MIN_ANCHORS_MLE:
            continue
        position = mle_position(anchor_positions[used], est_dist[u, used])
        if position is None:
            singular += 1
            continue
        estimates[u] = position
        localized[u] = True
    return estimates, localized, singular

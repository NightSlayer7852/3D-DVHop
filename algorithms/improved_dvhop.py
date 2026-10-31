"""Improved 3D DV-HOP: HCMCDV-HOP and HCMSPSO-DV-HOP (paper §III-B, Eqs. 7-16, Figs. 5-7).

This module contains ONLY the authors' improvements; shared math lives in algorithms/common.py.

Improvement 1  MCR fractional hop counts (radii R/3, 2R/3, R -> 1/3, 2/3, 1 hop), p.85530.
Improvement 2  hop-count threshold t_i, Eq. (7), discards anchors with large error.
Improvement 3  weighted AHD, Eqs. (8)-(10).
Improvement 4  UN->AN distance from the mean ("median") of two hop distances, Eq. (11).
Improvement 5  LDW-PSO (Eqs. 12-16) replaces "MLE" (Eqs. 5-6).

estimator="mle" -> HCMCDV-HOP (improvements 1-4; plotted in paper Fig. 12)
estimator="pso" -> HCMSPSO-DV-HOP (improvements 1-5; the proposed algorithm)
"""

from __future__ import annotations

import itertools

import numpy as np

from algorithms.common import LocalizationResult, mle_localize_all, nearest_anchor
from algorithms.pso import ldw_pso
from config import ImprovedConfig, PSOConfig
from simulation.network import Network, min_plus_shortest_paths

NAME_MLE = "HCMCDV-HOP"
NAME_PSO = "HCMSPSO-DV-HOP"


# --- Improvement 1: multiple communication radii --------------------------------------------
def mcr_hop_value(dist: np.ndarray, comm_radius: float) -> np.ndarray:
    """Fractional hop value of a direct link (p.85530): d<=R/3 -> 1/3, d<=2R/3 -> 2/3, d<=R -> 1."""
    dist = np.asarray(dist, dtype=float)
    value = np.full(dist.shape, np.inf)
    value[dist <= comm_radius] = 1.0
    value[dist <= 2.0 * comm_radius / 3.0] = 2.0 / 3.0
    value[dist <= comm_radius / 3.0] = 1.0 / 3.0
    return value


def mcr_hop_counts(network: Network, mode: str = "anchor_only") -> np.ndarray:
    """Minimum MCR hop counts from every anchor to every node, shape (n_a, n).

    anchor_only (Q1, approved): the anchor broadcasts at three radii, so its direct link is
        1/3, 2/3 or 1 hop; relays forward at radius R adding 1 hop each.
    all_links (sensitivity check): every link is weighted 1/3, 2/3 or 1 by its length.
    """
    anchors = network.anchor_idx
    n = network.positions.shape[0]
    fractional = mcr_hop_value(network.dist, network.comm_radius)
    np.fill_diagonal(fractional, np.inf)
    if mode == "anchor_only":
        initial = fractional[anchors].copy()
        initial[np.arange(len(anchors)), anchors] = 0.0
        link = np.where(network.adjacency, 1.0, np.inf)
    elif mode == "all_links":
        initial = np.full((len(anchors), n), np.inf)
        initial[np.arange(len(anchors)), anchors] = 0.0
        link = fractional
    else:
        raise ValueError(f"unknown MCR mode {mode!r}")
    return min_plus_shortest_paths(initial, link)


# --- Improvement 2: hop-count threshold, Eq. (7) ----------------------------------------------
def region_endpoints(side_length: float) -> np.ndarray:
    """The M = 8 vertices of the cubic deployment region (Q2)."""
    return np.array(list(itertools.product((0.0, side_length), repeat=3)))


def hop_thresholds(anchor_positions: np.ndarray, side_length: float, comm_radius: float) -> np.ndarray:
    """Eq. (7): t_i = max_m d_im / R over the region endpoints m. Returns (n_a,) hops."""
    endpoints = region_endpoints(side_length)
    d = np.linalg.norm(anchor_positions[:, None, :] - endpoints[None, :, :], axis=2)
    return d.max(axis=1) / comm_radius


# --- Improvement 3: weighted AHD, Eqs. (8)-(10) -----------------------------------------------
def weighted_hopsize(
    anchor_positions: np.ndarray,
    anchor_hops: np.ndarray,
    thresholds: np.ndarray,
    comm_radius: float,
    zero_tol: float = 1e-12,
) -> tuple[np.ndarray, dict]:
    """Weighted AHD of each anchor.

    Eq. (8)  c_ij = 1 / (d_ij / R - hops_ij)
    Eq. (9)  w_ij = c_ij / sum_{l in S_i} c_il          (Q4: index typo corrected)
    Eq. (10) Hopsize_i = sum_{j in S_i} w_ij d_ij / hops_ij
    S_i = anchors j != i, reachable, with hops_ij <= t_i (Eq. 7).
    Q3: if S_i is empty, the threshold is skipped for anchor i (all reachable anchors used).
    Q5: pairs with |d_ij/R - hops_ij| < zero_tol are excluded (would divide by zero).

    Since hops_ij >= d_ij / R, every c_ij <= 0; Eq. (9) normalises same-sign values, so the
    weights are positive and favour anchors whose path is close to straight.
    """
    n_a = anchor_positions.shape[0]
    true_dist = np.linalg.norm(anchor_positions[:, None, :] - anchor_positions[None, :, :], axis=2)
    hopsize = np.full(n_a, np.nan)
    stats = {"threshold_fallback": 0, "zero_denominator": 0, "anchors_discarded": 0}
    for i in range(n_a):
        reachable = np.isfinite(anchor_hops[i]) & (np.arange(n_a) != i)
        retained = reachable & (anchor_hops[i] <= thresholds[i])
        stats["anchors_discarded"] += int(reachable.sum() - retained.sum())
        if reachable.any() and not retained.any():
            retained = reachable
            stats["threshold_fallback"] += 1
        if not retained.any():
            continue
        d = true_dist[i, retained]
        h = anchor_hops[i, retained]
        denominator = d / comm_radius - h
        valid = np.abs(denominator) >= zero_tol
        stats["zero_denominator"] += int((~valid).sum())
        if not valid.any():
            continue
        c = 1.0 / denominator[valid]  # Eq. (8)
        w = c / c.sum()  # Eq. (9)
        hopsize[i] = np.sum(w * d[valid] / h[valid])  # Eq. (10)
    return hopsize, stats


# --- Improvement 4: UN -> AN distance, Eq. (11) -----------------------------------------------
def estimate_distances_eq11(hopsize: np.ndarray, hops_au: np.ndarray) -> np.ndarray:
    """Eq. (11): d_uj = 1/2 (Hopsize_{a*(u)} + Hopsize_j) * h_uj (Q6: a* = nearest anchor).

    hops_au : (n_a, n_u). Returns (n_u, n_a), NaN where unavailable.
    """
    nearest = nearest_anchor(hops_au)
    n_u = hops_au.shape[1]
    est = np.full((n_u, hops_au.shape[0]), np.nan)
    for u in range(n_u):
        if nearest[u] < 0 or not np.isfinite(hopsize[nearest[u]]):
            continue
        usable = np.isfinite(hops_au[:, u]) & np.isfinite(hopsize)
        est[u, usable] = 0.5 * (hopsize[nearest[u]] + hopsize[usable]) * hops_au[usable, u]
    return est


# --- Full pipeline ---------------------------------------------------------------------------
def localize(
    network: Network,
    estimator: str = "pso",
    improved_config: ImprovedConfig | None = None,
    pso_config: PSOConfig | None = None,
    rng: np.random.Generator | None = None,
    keep_pso_history: bool = False,
) -> LocalizationResult:
    improved_config = improved_config or ImprovedConfig()
    anchors, unknowns = network.anchor_idx, network.unknown_idx
    anchor_pos = network.anchor_positions

    hops = mcr_hop_counts(network, improved_config.mcr_mode)  # Improvement 1
    thresholds = hop_thresholds(anchor_pos, network.side_length, network.comm_radius)  # Eq. (7)
    hopsize, stats = weighted_hopsize(  # Eqs. (8)-(10)
        anchor_pos, hops[:, anchors], thresholds, network.comm_radius,
        improved_config.zero_denominator_tol,
    )
    est_dist = estimate_distances_eq11(hopsize, hops[:, unknowns])  # Eq. (11)

    diagnostics = dict(stats)
    if estimator == "mle":
        estimates, localized, singular = mle_localize_all(anchor_pos, est_dist)
        diagnostics["singular_matrix"] = singular
        name = NAME_MLE
    elif estimator == "pso":
        if rng is None:
            raise ValueError("PSO estimator requires an explicit rng for reproducibility")
        pso_config = pso_config or PSOConfig()
        mask = np.isfinite(est_dist)
        # Fig. 7: an orphan UN (no anchor information) is not localised.
        solvable = mask.any(axis=1)
        estimates = np.full((len(unknowns), 3), np.nan)
        if solvable.any():
            result = ldw_pso(
                anchor_pos, est_dist[solvable], mask[solvable],
                (0.0, network.side_length), pso_config, rng,
            )
            estimates[solvable] = result.best_positions
            if keep_pso_history:
                diagnostics["pso_history"] = result.history
        localized = solvable
        name = NAME_PSO
    else:
        raise ValueError("estimator must be 'mle' or 'pso'")

    return LocalizationResult(
        name=name, estimates=estimates, localized=localized, hops=hops,
        hopsize=hopsize, est_dist=est_dist, diagnostics=diagnostics,
    )

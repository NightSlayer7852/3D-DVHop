"""Traditional 3D DV-HOP (paper §III-A, Eqs. 2, 3, 5, 6; Fig. 4).

Stage 1  anchors flood the network; each node keeps the minimum integer hop count.
Stage 2  each anchor computes its AHD with Eq. (3).
Stage 3  each UN adopts the AHD of its nearest (fewest-hop) anchor and estimates
         d_ij = Hopsize * h_ij (Eq. 2).
Stage 4  coordinates from the linearised system, Eqs. (5)-(6) ("MLE").
"""

from __future__ import annotations

import numpy as np

from algorithms.common import (
    LocalizationResult,
    anchor_hopsize_eq3,
    mle_localize_all,
    nearest_anchor,
)
from simulation.network import Network, integer_hop_counts

NAME = "DV-HOP"


def estimate_distances_eq2(hopsize: np.ndarray, hops_au: np.ndarray) -> np.ndarray:
    """Eq. (2): d_uj = Hopsize_{a*(u)} * h_uj, a*(u) = nearest anchor of UN u.

    hops_au : (n_a, n_u). Returns (n_u, n_a); NaN where no estimate is possible.
    """
    nearest = nearest_anchor(hops_au)
    n_u = hops_au.shape[1]
    est = np.full((n_u, hops_au.shape[0]), np.nan)
    for u in range(n_u):
        if nearest[u] < 0 or not np.isfinite(hopsize[nearest[u]]):
            continue
        reachable = np.isfinite(hops_au[:, u])
        est[u, reachable] = hopsize[nearest[u]] * hops_au[reachable, u]
    return est


def localize(network: Network) -> LocalizationResult:
    anchors = network.anchor_idx
    unknowns = network.unknown_idx

    hops = integer_hop_counts(network.adjacency, anchors)  # Stage 1
    hopsize = anchor_hopsize_eq3(network.anchor_positions, hops[:, anchors])  # Stage 2, Eq. (3)
    est_dist = estimate_distances_eq2(hopsize, hops[:, unknowns])  # Stage 3, Eq. (2)
    estimates, localized, singular = mle_localize_all(network.anchor_positions, est_dist)  # Stage 4

    return LocalizationResult(
        name=NAME,
        estimates=estimates,
        localized=localized,
        hops=hops,
        hopsize=hopsize,
        est_dist=est_dist,
        diagnostics={"singular_matrix": singular},
    )

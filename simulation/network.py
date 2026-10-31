"""Network connectivity and hop-count computation.

Radio model: ideal sphere of radius R (a node within R is a one-hop neighbour). The paper
implies but does not name this model (PAPER_ANALYSIS.md §7).

All hop counts are computed with one min-plus (Bellman-Ford) relaxation routine:
    hop[s, v] = min over paths s -> v of (initial[s, first node] + sum of link weights)
which covers
    * integer DV-HOP flooding           : initial = 0 at source, unit link weights;
    * anchor-only MCR (Q1, approved)    : initial = fractional first hop, unit link weights;
    * all-links MCR (Q1, sensitivity)   : initial = 0 at source, fractional link weights.
This is equivalent to the paper's "keep the minimum hop value" flooding (Fig. 4).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


def pairwise_distances(positions: np.ndarray) -> np.ndarray:
    """Euclidean distance matrix (n, n) in metres."""
    positions = np.asarray(positions, dtype=float)
    if positions.ndim != 2 or positions.shape[1] != 3:
        raise ValueError("positions must have shape (n, 3)")
    diff = positions[:, None, :] - positions[None, :, :]
    return np.sqrt(np.einsum("ijk,ijk->ij", diff, diff))


def adjacency_matrix(dist: np.ndarray, comm_radius: float) -> np.ndarray:
    """One-hop neighbours: distance <= R, no self loops."""
    if comm_radius <= 0:
        raise ValueError("comm_radius must be positive")
    adj = dist <= comm_radius
    np.fill_diagonal(adj, False)
    return adj


def min_plus_shortest_paths(
    initial: np.ndarray, link_weights: np.ndarray, chunk_size: int = 32
) -> np.ndarray:
    """Shortest path values by repeated min-plus relaxation.

    Parameters
    ----------
    initial : (S, n) array. initial[s, v] = cost of reaching v directly from source s
              (np.inf where not directly reachable).
    link_weights : (n, n) array. Cost of a relay hop u -> v (np.inf where not adjacent).

    Returns (S, n) array of minimum costs (np.inf = unreachable).
    """
    initial = np.asarray(initial, dtype=float)
    weights = np.asarray(link_weights, dtype=float)
    result = np.empty_like(initial)
    for start in range(0, initial.shape[0], chunk_size):
        cost = initial[start : start + chunk_size].copy()
        while True:
            # relaxed[s, v] = min_u cost[s, u] + w[u, v]
            relaxed = np.min(cost[:, :, None] + weights[None, :, :], axis=1)
            updated = np.minimum(cost, relaxed)
            if np.array_equal(updated, cost):
                break
            cost = updated
        result[start : start + chunk_size] = cost
    return result


def integer_hop_counts(adjacency: np.ndarray, sources: np.ndarray) -> np.ndarray:
    """Traditional DV-HOP flooding (§III-A): minimum integer hops from each source."""
    n = adjacency.shape[0]
    sources = np.asarray(sources, dtype=int)
    initial = np.full((len(sources), n), np.inf)
    initial[np.arange(len(sources)), sources] = 0.0
    unit = np.where(adjacency, 1.0, np.inf)
    return min_plus_shortest_paths(initial, unit)


@dataclass
class Network:
    """A deployed network. Distances/adjacency are the physical layer shared by all algorithms."""

    positions: np.ndarray
    is_anchor: np.ndarray
    comm_radius: float
    side_length: float
    dist: np.ndarray = field(init=False, repr=False)
    adjacency: np.ndarray = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.positions = np.asarray(self.positions, dtype=float)
        self.is_anchor = np.asarray(self.is_anchor, dtype=bool)
        if self.positions.shape[0] != self.is_anchor.shape[0]:
            raise ValueError("positions and is_anchor length mismatch")
        if not self.is_anchor.any():
            raise ValueError("network needs at least one anchor")
        self.dist = pairwise_distances(self.positions)
        self.adjacency = adjacency_matrix(self.dist, self.comm_radius)

    @property
    def anchor_idx(self) -> np.ndarray:
        return np.flatnonzero(self.is_anchor)

    @property
    def unknown_idx(self) -> np.ndarray:
        return np.flatnonzero(~self.is_anchor)

    @property
    def anchor_positions(self) -> np.ndarray:
        return self.positions[self.is_anchor]

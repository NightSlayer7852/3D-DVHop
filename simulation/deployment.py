"""Random 3D node deployment (paper §IV, p.85531).

Paper: nodes are "randomly distributed" in a 100 m cube. The distribution law is not
given; uniform placement with a random anchor subset is ASSUMPTION Q16.
"""

from __future__ import annotations

import numpy as np

from config import NetworkConfig


def deploy_nodes(config: NetworkConfig, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Place ``config.n_total`` nodes uniformly in [0, L]^3 and pick anchors at random.

    Returns
    -------
    positions : (n, 3) float array, metres
    is_anchor : (n,) bool array
    """
    n_anchors = config.n_anchors
    if n_anchors < 1 or n_anchors >= config.n_total:
        raise ValueError(
            f"anchor_ratio={config.anchor_ratio} with n_total={config.n_total} gives "
            f"{n_anchors} anchors; need 1 <= anchors < n_total"
        )
    positions = rng.uniform(0.0, config.side_length, size=(config.n_total, 3))
    is_anchor = np.zeros(config.n_total, dtype=bool)
    is_anchor[rng.choice(config.n_total, size=n_anchors, replace=False)] = True
    return positions, is_anchor

"""Linear-decreasing-inertia-weight PSO used by HCMSPSO-DV-HOP (paper §III-B, Eqs. 12-16, Fig. 6).

Paper-given parts
    Eq. (12) personal best, Eq. (13) global best, Eq. (14) initialisation,
    Eq. (15) inertia weight with w_s = 0.9, w_e = 0.4, Eq. (16) RMS objective.
Approved resolutions (IMPLEMENTATION_PLAN.md §10)
    Q7  velocity/position update not printed in the paper; the standard inertia-weight form
        v <- w v + c1 r1 (P_i - x) + c2 r2 (P_g - x),  x <- x + v   is used, c1 = c2 = 2.
    Q8  Eq. (15) printed as w = w_s - (w_s - w_e)(MaxIt/N) has no iteration term; implemented
        as w(t) = w_s - (w_s - w_e) t / MaxIt, t = 1..MaxIt.
    Q9  m = w (sum limit) = number of anchors with an estimated distance to the UN.
    Q10 N = 30, MaxIt = 300, v_max = 10 m, v_min = -v_max, search box = deployment region.

Many UNs are solved simultaneously: problem b has its own independent swarm; arrays are (B, P, 3).
The algorithm per UN is unchanged; only the order in which random numbers are drawn differs from a
per-UN loop (same distribution, bit-reproducible for a given seed).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from config import PSOConfig


def rms_objective(
    particles: np.ndarray, anchor_positions: np.ndarray, est_dist: np.ndarray, mask: np.ndarray
) -> np.ndarray:
    """Eq. (16): f(x,y,z) = sqrt( (1/m) * sum_i ( ||p - a_i|| - d_i )^2 ).

    particles        (B, P, 3)
    anchor_positions (n_a, 3)
    est_dist         (B, n_a) estimated distances d_i (ignored where mask is False)
    mask             (B, n_a) anchors used by each problem
    Returns (B, P).
    """
    diff = particles[:, :, None, :] - anchor_positions[None, None, :, :]
    geometric = np.sqrt(np.einsum("bpak,bpak->bpa", diff, diff))
    residual = np.where(mask[:, None, :], geometric - np.nan_to_num(est_dist)[:, None, :], 0.0)
    m = mask.sum(axis=1)[:, None]
    return np.sqrt(np.einsum("bpa,bpa->bp", residual, residual) / m)


def inertia_weight(t: int, config: PSOConfig) -> float:
    """Eq. (15) (Q8 corrected): linear decrease from w_s at t=0 to w_e at t=MaxIt."""
    if config.constant_inertia is not None:  # classic PSO, Q17 contrast only
        return config.constant_inertia
    return config.w_start - (config.w_start - config.w_end) * t / config.max_iter


@dataclass
class PSOResult:
    best_positions: np.ndarray  # (B, 3) global best P_g
    best_fitness: np.ndarray  # (B,)
    history: np.ndarray  # (B, MaxIt + 1) global-best fitness after each iteration


def ldw_pso(
    anchor_positions: np.ndarray,
    est_dist: np.ndarray,
    mask: np.ndarray,
    bounds: tuple[float, float],
    config: PSOConfig,
    rng: np.random.Generator,
) -> PSOResult:
    """Minimise Eq. (16) for B problems at once."""
    mask = np.asarray(mask, dtype=bool)
    if mask.ndim != 2 or (mask.sum(axis=1) < 1).any():
        raise ValueError("every problem needs at least one anchor distance")
    x_min, x_max = bounds
    n_problems, n_particles = mask.shape[0], config.n_particles
    shape = (n_problems, n_particles, 3)

    # Eq. (14): x_ij(0) = rdft() (x_max - x_min) + x_min ;  v_ij(0) = rdft() v_max
    positions = rng.random(shape) * (x_max - x_min) + x_min
    velocities = rng.random(shape) * config.v_max

    fitness = rms_objective(positions, anchor_positions, est_dist, mask)
    personal_best, personal_fit = positions.copy(), fitness.copy()
    rows = np.arange(n_problems)
    g_idx = np.argmin(personal_fit, axis=1)  # Eq. (13)
    global_best, global_fit = personal_best[rows, g_idx], personal_fit[rows, g_idx]

    history = np.empty((n_problems, config.max_iter + 1))
    history[:, 0] = global_fit
    for t in range(1, config.max_iter + 1):
        w = inertia_weight(t, config)
        r1, r2 = rng.random(shape), rng.random(shape)
        velocities = (
            w * velocities
            + config.c1 * r1 * (personal_best - positions)
            + config.c2 * r2 * (global_best[:, None, :] - positions)
        )
        velocities = np.clip(velocities, -config.v_max, config.v_max)  # v in [v_min, v_max]
        positions = np.clip(positions + velocities, x_min, x_max)  # x in [x_min, x_max]

        fitness = rms_objective(positions, anchor_positions, est_dist, mask)
        improved = fitness <= personal_fit  # Eq. (12)
        personal_best[improved] = positions[improved]
        personal_fit[improved] = fitness[improved]
        g_idx = np.argmin(personal_fit, axis=1)  # Eq. (13)
        global_best, global_fit = personal_best[rows, g_idx], personal_fit[rows, g_idx]
        history[:, t] = global_fit

    return PSOResult(global_best.copy(), global_fit.copy(), history)

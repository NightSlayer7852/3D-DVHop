"""Central configuration for the 3D DV-HOP reproduction.

Every value is tagged with its provenance:
    PAPER      - stated explicitly in Wu et al., IEEE Access 2023 (DOI 10.1109/ACCESS.2023.3303569)
    ASSUMPTION - not given by the paper; chosen in IMPLEMENTATION_PLAN.md §10 (question number given)
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class NetworkConfig:
    """Physical network parameters."""

    side_length: float = 100.0  # PAPER §IV p.85531: 100 m x 100 m x 100 m region
    n_total: int = 200  # ASSUMPTION Q16 (paper sweeps 80-240, Fig. 12c)
    anchor_ratio: float = 0.2  # ASSUMPTION Q16 (paper sweeps 0.1-0.5, Fig. 12a)
    comm_radius: float = 40.0  # ASSUMPTION Q16 (paper sweeps 25-65, Fig. 12b), metres

    def __post_init__(self) -> None:
        if self.side_length <= 0:
            raise ValueError("side_length must be positive")
        if self.comm_radius <= 0:
            raise ValueError("comm_radius must be positive")
        if not 0.0 < self.anchor_ratio < 1.0:
            raise ValueError("anchor_ratio must lie strictly between 0 and 1")
        if self.n_total < 2:
            raise ValueError("n_total must be at least 2")

    @property
    def n_anchors(self) -> int:
        return int(round(self.anchor_ratio * self.n_total))


@dataclass(frozen=True)
class PSOConfig:
    """Linear-decreasing-inertia-weight PSO (paper Eqs. 12-16)."""

    n_particles: int = 30  # ASSUMPTION Q10
    max_iter: int = 300  # ASSUMPTION Q10 (Fig. 8 x-axis ends at 300)
    w_start: float = 0.9  # PAPER Eq. (15), p.85531
    w_end: float = 0.4  # PAPER Eq. (15), p.85531
    c1: float = 2.0  # ASSUMPTION Q7 (learning factor, not given)
    c2: float = 2.0  # ASSUMPTION Q7 (learning factor, not given)
    v_max: float = 10.0  # ASSUMPTION Q10 (10 % of region side), metres / iteration
    constant_inertia: float | None = None  # only for the Q17 contrast curve (classic PSO, w = 0.7)

    def __post_init__(self) -> None:
        if self.n_particles < 1 or self.max_iter < 1:
            raise ValueError("n_particles and max_iter must be >= 1")
        if self.v_max <= 0:
            raise ValueError("v_max must be positive")


@dataclass(frozen=True)
class ImprovedConfig:
    """Switches for the improved algorithm."""

    # Q1: "anchor_only" = only the anchor's first link is fractional (approved, literal reading);
    #     "all_links"   = every link weighted 1/3, 2/3, 1 (sensitivity check only).
    mcr_mode: str = "anchor_only"
    zero_denominator_tol: float = 1e-12  # Q5: exact-zero guard for Eq. (8)

    def __post_init__(self) -> None:
        if self.mcr_mode not in ("anchor_only", "all_links"):
            raise ValueError("mcr_mode must be 'anchor_only' or 'all_links'")


@dataclass(frozen=True)
class ExperimentConfig:
    n_trials: int = 50  # ASSUMPTION Q16 (Monte-Carlo trials per sweep point)
    master_seed: int = 2023  # ASSUMPTION Q16
    network: NetworkConfig = field(default_factory=NetworkConfig)
    pso: PSOConfig = field(default_factory=PSOConfig)
    improved: ImprovedConfig = field(default_factory=ImprovedConfig)


# Sweep grids (ranges PAPER Figs. 12a-c; step sizes ASSUMPTION Q16)
ANCHOR_RATIO_SWEEP = (0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50)
COMM_RADIUS_SWEEP = (25.0, 30.0, 35.0, 40.0, 45.0, 50.0, 55.0, 60.0, 65.0)
TOTAL_NODES_SWEEP = (80, 100, 120, 140, 160, 180, 200, 220, 240)

# Minimum anchors for the 3D linear system of Eqs. (5)-(6): n - 1 >= 3 rows.
MIN_ANCHORS_MLE = 4

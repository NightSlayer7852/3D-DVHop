"""True vs estimated positions with error lines (paper Fig. 11 analogue)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from simulation.simulation_engine import ALGORITHMS
from visualization.style import ANCHOR_COLOR, MUTED, SERIES, apply_style, save


def plot_projection_panels(nodes: dict, anchor_xyz: np.ndarray, side: float, path: Path) -> None:
    """x-y projection per algorithm (as in the paper's Fig. 11) plus the true layout.

    Each estimate is drawn as a marker joined to its true position by a line; line length is the
    planar (Eq. 17) error. Only UNs in the common evaluation set are drawn.
    """
    apply_style()
    fig, axes = plt.subplots(2, 2, figsize=(10, 9.4), sharex=True, sharey=True)
    for ax, alg in zip(axes.flat, ALGORITHMS):
        sel = (nodes["algorithm"] == alg) & nodes["in_common_set"]
        true = np.c_[nodes["x"][sel], nodes["y"][sel]]
        est = np.c_[nodes["x_est"][sel], nodes["y_est"][sel]]
        style = SERIES[alg]
        for t, e in zip(true, est):
            ax.plot([t[0], e[0]], [t[1], e[1]], color=style["color"], linewidth=0.8, alpha=0.7)
        ax.scatter(*est.T, s=14, color=style["color"], marker=style["marker"], label="Estimate", zorder=3)
        ax.scatter(*anchor_xyz[:, :2].T, s=18, color=ANCHOR_COLOR, marker="o", label="Anchor", zorder=4)
        ax.set_title(alg)
    ax = axes.flat[3]
    sel = nodes["algorithm"] == ALGORITHMS[0]
    ax.scatter(nodes["x"][sel], nodes["y"][sel], s=14, color=MUTED, marker="^", label="Unknown (true)")
    ax.scatter(*anchor_xyz[:, :2].T, s=18, color=ANCHOR_COLOR, marker="o", label="Anchor")
    ax.set_title("Real node distribution")
    handles = [plt.Line2D([], [], color=SERIES[a]["color"], marker=SERIES[a]["marker"], linewidth=0.8,
                          label=f"{a} estimate (line → true position)") for a in ALGORITHMS]
    handles += [plt.Line2D([], [], color=MUTED, marker="^", linestyle="", label="Unknown node (true)"),
                plt.Line2D([], [], color=ANCHOR_COLOR, marker="o", linestyle="", label="Anchor node")]
    fig.legend(handles=handles, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.04))
    fig.suptitle("Positioning results, x–y projection (Fig. 11 analogue)")
    for ax in axes.flat:
        ax.set_xlim(0, side)
        ax.set_ylim(0, side)
        ax.set_aspect("equal")
    for ax in axes[1]:
        ax.set_xlabel("x (m)")
    for ax in axes[:, 0]:
        ax.set_ylabel("y (m)")
    save(fig, path)


def plot_error_lines_3d(nodes: dict, anchor_xyz: np.ndarray, side: float, path: Path) -> None:
    """Full 3D view of estimate→truth error lines, one panel per algorithm."""
    apply_style()
    fig = plt.figure(figsize=(15, 5))
    for k, alg in enumerate(ALGORITHMS):
        ax = fig.add_subplot(1, 3, k + 1, projection="3d")
        sel = (nodes["algorithm"] == alg) & nodes["in_common_set"]
        true = np.c_[nodes["x"][sel], nodes["y"][sel], nodes["z"][sel]]
        est = np.c_[nodes["x_est"][sel], nodes["y_est"][sel], nodes["z_est"][sel]]
        style = SERIES[alg]
        for t, e in zip(true, est):
            ax.plot(*np.c_[t, e], color=style["color"], linewidth=0.7, alpha=0.7)
        ax.scatter(*est.T, s=8, color=style["color"], marker=style["marker"])
        ax.scatter(*anchor_xyz.T, s=12, color=ANCHOR_COLOR)
        for setter in (ax.set_xlim, ax.set_ylim, ax.set_zlim):
            setter(0, side)
        ax.set_title(f"{alg}\nmean 3D error {np.linalg.norm(true - est, axis=1).mean():.1f} m")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        ax.set_zlabel("z (m)")
    save(fig, path)

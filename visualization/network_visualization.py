"""3D deployment view (paper Fig. 9(a) analogue)."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from visualization.style import ANCHOR_COLOR, INK_2, MUTED, apply_style, save


def plot_network_3d(unknown_xyz: np.ndarray, anchor_xyz: np.ndarray, side: float, title: str,
                    path: Path) -> None:
    apply_style()
    fig = plt.figure(figsize=(6.4, 5.6))
    ax = fig.add_subplot(projection="3d")
    ax.scatter(*unknown_xyz.T, s=14, marker="^", color=MUTED, alpha=0.8, label=f"Unknown node ({len(unknown_xyz)})")
    ax.scatter(*anchor_xyz.T, s=30, marker="o", color=ANCHOR_COLOR, label=f"Anchor node ({len(anchor_xyz)})")
    for setter in (ax.set_xlim, ax.set_ylim, ax.set_zlim):
        setter(0, side)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("z (m)")
    ax.set_title(title, color=INK_2)
    ax.legend(loc="upper left")
    save(fig, path)

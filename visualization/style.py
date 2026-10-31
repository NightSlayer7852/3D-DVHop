"""Shared Matplotlib styling. Fixed series order -> fixed colour (never cycled).

Palette: validated categorical slots 1-3 (blue, orange, aqua) on a light surface. Aqua is below
3:1 contrast, so every series also has its own marker and line style and a legend (identity is
never carried by colour alone), and every figure has a numeric table in results/tables.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from simulation.simulation_engine import ALGORITHMS  # noqa: E402

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

SERIES = {
    ALGORITHMS[0]: {"color": "#2a78d6", "marker": "o", "linestyle": "-"},   # DV-HOP
    ALGORITHMS[1]: {"color": "#eb6834", "marker": "s", "linestyle": "--"},  # HCMCDV-HOP
    ALGORITHMS[2]: {"color": "#1baf7a", "marker": "^", "linestyle": "-."},  # HCMSPSO-DV-HOP
}
ANCHOR_COLOR = INK
TRUE_COLOR = MUTED


def apply_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": AXIS, "axes.labelcolor": INK, "axes.titlecolor": INK,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
        "xtick.color": INK_2, "ytick.color": INK_2, "xtick.labelcolor": INK_2, "ytick.labelcolor": INK_2,
        "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10, "legend.fontsize": 9,
        "legend.frameon": False, "lines.linewidth": 2.0, "lines.markersize": 6,
        "savefig.dpi": 200, "savefig.bbox": "tight",
    })


def save(fig, path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
